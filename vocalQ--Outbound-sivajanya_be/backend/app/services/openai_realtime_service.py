import json
import logging
import asyncio
import websockets
from datetime import datetime
from app.core.config import settings
from app.services.qdrant_service import QdrantService
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class OpenAIRealtimeService:
    def __init__(self, stream_sid: str | None, send_to_twilio_func: Callable[[str], Awaitable[None]]):
        self.stream_sid = stream_sid
        self.send_to_twilio = send_to_twilio_func
        self.ws = None
        self.qdrant = QdrantService()
        self.is_connected = False
        self.session_id = None
        self.pending_func_calls = {} # call_id -> function_name
        self.transcript = []
        self._connection_event = asyncio.Event() 

        
        # System instructions
        self.instructions = """
You are VocalQ.ai’s professional AI phone assistant.

ROLE & TONE:
- You are polite, confident, calm, and helpful.
- Sound natural and human, not robotic.
- Use short, clear sentences suitable for phone calls.
- Be empathetic when users sound confused or frustrated.

CALL OPENING (VERY IMPORTANT):
- Always greet immediately when the call connects.
- Use this neutral greeting:
  "Hello, thank you for calling VocalQ support. How can I help you today?"
- Do NOT wait for the user to speak before greeting.

MULTILINGUAL BEHAVIOR (DYNAMIC SWITCHING):
- You are a polyglot assistant. You MUST detect the language of EVERY user turn independently.
- DO NOT stick to a previous language if the user switches.
- IF user speaks Telugu -> You respond in Telugu.
- IF user THEN speaks Hindi -> You IMMEDIATEY switch to Hindi.
- IF user THEN speaks English -> You IMMEDIATEY switch to English.
- Always match the language of the *most recent* user input.
- If the user speaks a mix (Hinglish/Tanglish), respond in the same mixed style or the dominant language.
- NEVER force English or the previous language.

TURN-TAKING & INTERRUPTS (CRITICAL):
- Speak ONLY when it is your turn.
- STOP speaking immediately if the caller starts talking.
- If interrupted or the caller says “stop”, “wait”, or “hold on”:
  - Stop instantly.
  - Respond with:
    "Okay, I’m listening."

RESPONSE LENGTH:
- Use 1–2 short sentences only.
- NEVER exceed 2 sentences.
- If more detail is needed:
  - Ask permission first:
    "Would you like a brief explanation?"

KNOWLEDGE HANDLING & IDENTITY:
- You are "VocalQ Support Assistant".
- You CAN answer questions about your identity, capabilities, and current status (e.g., "what is your name", "what do you do", "how are you", "are you real") directly and naturally without tools.
- For business queries (company info, policies, services, prices, etc.):
  - ALWAYS call `query_knowledge_base` first.
  - If the tool result says "No information found", say:
    "I’m sorry, I don’t have that specific information."
- NEVER guess about company policies or data.

OUT-OF-SCOPE QUESTIONS:
- For general knowledge questions unrelated to VocalQ or your identity (e.g., "Who is the president?", "What is the weather?"):
  - Apologize briefly: "I’m sorry, I can only help with VocalQ support queries."

ACKNOWLEDGEMENTS:
- Acknowledge before answering:
  - "I understand."
  - "Got it."
  - "Thanks for explaining."

THANK-YOU RESPONSES:
- Respond politely with variety:
  - "You're welcome."
  - "Happy to help."
  - "Glad I could assist."

ERROR HANDLING:
- If a tool fails:
  "Sorry about that. I’m having trouble accessing that information."

CALL ENDING:
- Close politely:
  "Is there anything else I can help you with today?"
  "Thank you for calling VocalQ. Have a great day."

-------------------------
STRICT DOs & DON’Ts:

DO:
- Stop speaking immediately when interrupted.
- End responses immediately after stating lack of information.
- Ask permission before giving longer explanations.
- Remain silent when unsure.

DO NOT:
- Do NOT hallucinate or invent answers.
- Do NOT continue talking after an out-of-scope response.
- Do NOT explain general knowledge.
- Do NOT speak over the caller.
- Do NOT exceed 2 sentences.
- Do NOT repeat the same sentence structure.
- Do NOT ask the caller to select a language.



"""

    async def connect(self):
        """Connect to OpenAI Realtime API."""
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview-2024-12-17"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        }
        
        try:
            logger.info(f"Connecting to OpenAI Realtime at {url}...")
            self.ws = await websockets.connect(url, additional_headers=headers)
            self.is_connected = True
            self._connection_event.set()
            logger.info("--- Connected to OpenAI Realtime API ---")
            
            # Initiate Session
            await self.update_session()
            
            # NOTE: Removed automatic send_greeting() and enable_vad() from here.
            # They should be called explicitly by the caller when ready.
            
            # Start the receive loop
            asyncio.create_task(self.receive_loop())
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI Realtime: {e}")
            raise e

    async def wait_for_connection(self):
        """Waits until the WebSocket is connected."""
        await self._connection_event.wait()

    async def update_session(self):
        """Configure the session with tools and instructions."""
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": "alloy",
                "instructions": self.instructions,
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "tools": [
                     {
                        "type": "function",
                        "name": "query_knowledge_base",
                        "description": "Search the knowledge base for answer to user questions about the company, services, or policies.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query based on user's question."
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ],
                "turn_detection": None
            }
        }
        await self.ws.send(json.dumps(session_config))
        # Small delay to ensure session update is processed
        # await asyncio.sleep(0.5) 

    async def enable_vad(self):
        logger.info("Enabling Server VAD...")
        await self.ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }))
        
    async def send_greeting(self):
        # Trigger response creation with instructions to greet
        await self.ws.send(json.dumps({
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
                "instructions": "Hello, thank you for calling VocalQ support. How can I help you today?"
            }
        }))

    async def send_audio(self, audio_b64: str):
        """Appends audio to the input buffer."""
        if not self.is_connected:
            return
            
        msg = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }
        await self.ws.send(json.dumps(msg))

    async def close(self):
        """Close connection."""
        self.is_connected = False
        if self.ws:
            await self.ws.close()

    async def receive_loop(self):
        """Handle incoming messages from OpenAI."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                event_type = data.get("type")
                
                if event_type == "input_audio_buffer.speech_started":
                    logger.info("Interrupt: User started speaking.")
                    await self.send_to_twilio(json.dumps({
                        "event": "clear",
                        "streamSid": self.stream_sid
                    }))
                    await self.ws.send(json.dumps({
                         "type": "response.cancel"
                    }))

                elif event_type == "session.created":
                    self.session_id = data.get("session", {}).get("id")
                    logger.info(f"OpenAI Session Created: {self.session_id}")

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = data.get("transcript")
                    if transcript:
                        item = {"role": "user", "content": transcript, "timestamp": datetime.now().isoformat()}
                        self.transcript.append(item)
                        logger.info(f"User transcript: {transcript}")

                elif event_type == "response.audio_transcript.done":
                    transcript = data.get("transcript")
                    if transcript:
                        item = {"role": "assistant", "content": transcript, "timestamp": datetime.now().isoformat()}
                        self.transcript.append(item)
                        logger.info(f"Assistant transcript: {transcript}")
                
                elif event_type == "response.output_item.added":
                     item = data.get("item", {})
                     if item.get("type") == "function_call":
                         self.pending_func_calls[item["call_id"]] = item["name"]

                elif event_type == "response.audio.delta":
                    # Stream audio back to Twilio
                    audio_payload = data.get("delta")
                    if audio_payload and self.stream_sid:
                        media_message = {
                            "event": "media",
                            "streamSid": self.stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await self.send_to_twilio(json.dumps(media_message))
                        
                elif event_type == "response.function_call_arguments.done":
                     call_id = data.get("call_id")
                     name = self.pending_func_calls.get(call_id)
                     if name == "query_knowledge_base":
                         await self.handle_function_call(call_id, data.get("arguments"))

                elif event_type == "error":
                    logger.error(f"OpenAI Error: {data}")

        except Exception as e:
            logger.error(f"Error in OpenAI receive loop: {e}")
        finally:
            self.is_connected = False

    async def handle_function_call(self, call_id, arguments_str):
        """Execute the function and return the output."""
        try:
            args = json.loads(arguments_str)
            logger.info(f"Tool Call: query_knowledge_base Args: {args}")
            
            query = args.get("query")
            results = await self.qdrant.search(query, limit=3)
            result_text = "\n".join(results) if results else "No information found in knowledge base."
            
            logger.info(f"Tool Result: {result_text[:50]}...")
            
            # Send Output
            output_item = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": result_text
                }
            }
            await self.ws.send(json.dumps(output_item))
            
            # Trigger Response
            await self.ws.send(json.dumps({"type": "response.create"}))
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")

    async def handle_interruption(self):
        """Handle interruption from local VAD."""
        if not self.is_connected:
            return
        logger.info("Local VAD Interrupt: User started speaking.")
        await self.send_to_twilio(json.dumps({
            "event": "clear",
            "streamSid": self.stream_sid
        }))
        await self.ws.send(json.dumps({
             "type": "response.cancel"
        }))
