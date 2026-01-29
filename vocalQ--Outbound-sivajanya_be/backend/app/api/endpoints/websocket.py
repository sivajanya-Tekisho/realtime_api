from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
import asyncio
import sys
import uuid
from datetime import datetime, timezone
from app.services.openai_realtime_service import OpenAIRealtimeService
from app.services.gemini_realtime_service import GeminiRealtimeService
from app.services.llm_service import LLMService
from app.services.vad_service import vad_service
from app.core.supabase_client import supabase
import base64

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("\n[TELEPHONY] --- NEW INBOUND WEBSOCKET CONNECTION (REALTIME API) ---")
    sys.stdout.flush()
    await websocket.accept()
    
    # Pre-initialize service to reduce latency
    async def send_to_twilio(text_data):
        try:
            await websocket.send_text(text_data)
        except Exception as e:
            logger.error(f"Failed to send to Twilio: {e}")

    # realtime_service = OpenAIRealtimeService(stream_sid=None, send_to_twilio_func=send_to_twilio)
    realtime_service = GeminiRealtimeService(stream_sid=None, send_to_twilio_func=send_to_twilio)
    init_task = asyncio.create_task(realtime_service.connect())

    call_id = str(uuid.uuid4())
    stream_sid = None
    vad_active = False  # Local VAD state

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event = data.get("event")

            if event == "connected":
                logger.info("Twilio connected")
                
            elif event == "start":
                start_data = data.get("start", {})
                stream_sid = start_data.get("streamSid")
                realtime_service.stream_sid = stream_sid # Set SID now

                custom_params = start_data.get("customParameters", {})
                queue_id = custom_params.get("queueId")
                caller_number = custom_params.get("callerNumber")
                attempt_str = custom_params.get("attemptCount", "1")
                try:
                    attempt_count = int(attempt_str)
                except:
                    attempt_count = 1
                
                logger.info(f"Stream started: {stream_sid}, QueueID: {queue_id}, Attempt: {attempt_count}")
                
                # Run Supabase logging in background to reduce latency
                def log_call_start_sync(cid, qid, sid, cnum, attempts):
                    try:
                        start_ts = datetime.now(timezone.utc).isoformat()
                        supabase.table("calls").insert({
                            "id": cid,
                            "call_queue_id": qid if qid else None,
                            "twilio_call_sid": sid,
                            "start_time": start_ts,
                            "call_status": "active",
                            "caller_number": cnum
                        }).execute()
                        
                        supabase.table("call_attempts").insert({
                            "call_id": cid,
                            "attempt_number": attempts,
                            "status": "initiated",
                            "started_at": start_ts
                        }).execute()
                    except Exception as e:
                        logger.error(f"Failed to insert call/attempt record: {e}")

                asyncio.get_running_loop().run_in_executor(
                    None, 
                    log_call_start_sync, 
                    call_id, queue_id, stream_sid, caller_number, attempt_count
                )

                # Wait for OpenAI to be ready (it might already be)
                logger.info("Waiting for OpenAI connection to complete...")
                await realtime_service.wait_for_connection()
                logger.info("OpenAI Ready. Sending Greeting.")
                await realtime_service.send_greeting()
                await realtime_service.enable_vad()
                
            elif event == "media":
                if realtime_service and realtime_service.is_connected:
                    payload = data['media']['payload']
                    
                    # --- Silero VAD Check ---
                    try:
                        chunk_bytes = base64.b64decode(payload)
                        speech_prob = vad_service.is_speech(chunk_bytes)
                        if speech_prob > 0.5:
                            if not vad_active:
                                vad_active = True
                                logger.info("Local VAD detected speech start")
                                await realtime_service.handle_interruption()
                        elif speech_prob < 0.3:
                            vad_active = False

                    except Exception as vad_err:
                        logger.error(f"VAD Error: {vad_err}")
                    # ------------------------

                    await realtime_service.send_audio(payload)
                    
            elif event == "stop":
                logger.info("Stream stopped")
                if realtime_service:
                    await realtime_service.close()
                break
                
            elif event == "close":
                logger.info("Stream closed")
                if realtime_service:
                    await realtime_service.close()
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Update Call Status and Process After-Call Work
        if call_id and realtime_service:
             try:
                # 1. Update 'calls' table
                end_time = datetime.now(timezone.utc)
                end_time_iso = end_time.isoformat()
                
                # Fetch start time to calculate duration
                # Assuming start time was close to when we created 'calls' record. 
                # For simplicity, we can fetch it or just rely on 'updated_at' mechanisms if we had them.
                # Ideally, we should have stored start_time in memory.
                # Let's read the call record to get start_time
                res = supabase.table("calls").select("start_time").eq("id", call_id).single().execute()
                duration = 0
                if res.data and res.data.get("start_time"):
                    start_time = datetime.fromisoformat(res.data["start_time"].replace("Z", "+00:00"))
                    duration = int((end_time - start_time).total_seconds())

                # Prepare Transcript
                transcript_list = realtime_service.transcript
                transcript_json = json.dumps(transcript_list)

                # Generate Summary
                summary_text = await LLMService.summarize_call(transcript_list)
                
                # Simple intent extraction (heuristic or separate LLM call)
                # For now, we will assume intent is part of summary or generic.
                intent = "General Inquiry" 

                # Update 'calls'
                supabase.table("calls").update({
                    "call_status": "completed",
                    "end_time": end_time_iso,
                    "call_duration": duration,
                    "transcript": transcript_list, # Supabase client should handle list -> jsonb
                    "summary": summary_text,
                    "intent": intent
                }).eq("id", call_id).execute()

                # 2. Insert into 'call_summaries'
                supabase.table("call_summaries").insert({
                    "call_id": call_id,
                    "summary_text": summary_text
                }).execute()

                # 3. Update 'call_attempts'
                supabase.table("call_attempts").update({
                    "status": "completed", 
                    "ended_at": end_time_iso
                }).eq("call_id", call_id).execute()

                logger.info(f"Call {call_id} updated successfully.")
                
             except Exception as e:
                 logger.error(f"Failed to update call record: {e}")

        if realtime_service:
            await realtime_service.close()
        try:
            await websocket.close()
        except:
            pass

