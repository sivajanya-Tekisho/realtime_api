from typing import List, Optional
import sys
import logging
from fastapi import APIRouter, Response, Request
from app.core.supabase_client import supabase
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

def map_call(c):
    # Map from New Schema (public.calls) to Frontend Model
    
    timestamp = c.get("call_start_time") or c.get("created_at")
    if timestamp and isinstance(timestamp, str):
        timestamp = timestamp.replace(' ', 'T')
        if 'Z' not in timestamp and '+' not in timestamp[10:]:
            timestamp += 'Z'

    return {
        "id": c.get("id") or "Unknown",
        "caller": c.get("caller_number") or "Unknown", # Column might be missing in new schema, will be None
        "timestamp": timestamp,
        "duration": c.get("call_duration") or 0,
        "status": c.get("call_status") or "active",
        "intent": "N/A", # Not in new schema
        "summary": "", # Not in new schema
        "transcript": [], # Fetched separately if needed
        "language": "en-US"
    }

@router.get("/")
def read_calls(skip: int = 0, limit: int = 100, status: Optional[str] = None):
    # Select from 'calls' table matching the new schema
    # Columns: id, call_start_time, call_status, etc. (No summary, no transcript column)
    query = supabase.table("calls").select("*").order("call_start_time", desc=True).order("created_at", desc=True).range(skip, skip + limit - 1)
    
    if status:
        query = query.eq("call_status", status)
    
    try:
        response = query.execute()
    except Exception as e:
        logger.error(f"Error fetching calls: {e}")
        return []
        
    data = response.data or []
    return [map_call(c) for c in data]

@router.get("/active")
def read_active_calls():
    response = supabase.table("calls").select("*").eq("call_status", "active").execute()
    data = response.data or []
    return [map_call(c) for c in data]

@router.get("/analytics")
def get_analytics():
    try:
        # Fetch all calls for analytics
        response = supabase.table("calls").select("*").execute()
        calls = response.data or []
        
        total_calls = len(calls)
        completed_calls = len([c for c in calls if c.get("call_status") == "completed"])
        missed_calls = len([c for c in calls if c.get("call_status") in ["missed", "dropped", "no-answer"]])
        
        durations = [c.get("call_duration") or 0 for c in calls if c.get("call_duration")]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        # Intent not available anymore
        intent_counts = {"N/A": total_calls}

        # Calculate calls by hour for "Peak Window"
        from datetime import datetime
        from collections import defaultdict
        import dateutil.parser

        calls_by_hour = defaultdict(int)
        for c in calls:
            start_time_str = c.get("call_start_time") or c.get("created_at")
            if start_time_str:
                try:
                     dt = dateutil.parser.parse(start_time_str)
                     hour_label = dt.strftime("%I%p").lstrip('0').lower() # e.g. 2pm
                     calls_by_hour[hour_label] += 1
                except:
                    pass

        hour_wise_data = [{"name": k, "value": v} for k, v in calls_by_hour.items()]
        
        return {
            "total_calls": total_calls,
            "completed_calls": completed_calls,
            "missed_calls": missed_calls,
            "avg_duration": avg_duration,
            "intent_distribution": intent_counts,
            "calls_by_hour": hour_wise_data
        }
    except Exception as e:
        print(f"Analytics error: {e}")
        return {
            "total_calls": 0,
            "completed_calls": 0,
            "missed_calls": 0,
            "avg_duration": 0,
            "intent_distribution": {},
            "calls_by_hour": []
        }

@router.post("/twilio")
async def twilio_webhook(request: Request):
    """
    TwiML webhook for Twilio to handle incoming calls.
    Captures params like queue_id if passed in URL query params.
    """
    # Capture URL query params (e.g. queue_id from outbound service)
    query_params = request.query_params
    queue_id = query_params.get("queue_id")
    attempt_count = query_params.get("attempt_count")
    
    # Capture caller info from Twilio POST body
    form_data = await request.form()
    caller_number = form_data.get("From", "Unknown")
    
    # Legacy Stream Handling
    host = request.headers.get("host")
    is_secure = request.headers.get("x-forwarded-proto") == "https" or \
                ".ngrok" in host or \
                ".loca.lt" in host or \
                "serveo" in host
    protocol = "wss" if is_secure else "ws"
    ws_url = f"{protocol}://{host}/api/v1/stream"
    
    print(f"--- TWILIO WEBHOOK: LEGACY STREAM (Queue ID: {queue_id}) ---")
    sys.stdout.flush()
    
    # Pass queue_id in a custom parameter block
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="callerNumber" value="{caller_number}" />
            <Parameter name="queueId" value="{queue_id if queue_id else ''}" />
            <Parameter name="attemptCount" value="{attempt_count if attempt_count else '1'}" />
        </Stream>
    </Connect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")

@router.get("/{call_id}")
def read_call(call_id: str):
    # Fetch call details from 'calls' table
    call_response = supabase.table("calls").select("*").eq("id", call_id).single().execute()
    if not call_response.data:
        return None
        
    call_data = call_response.data
    
    # Manually fetch transcripts
    transcript_response = supabase.table("call_transcripts").select("*").eq("call_id", call_id).order("timestamp", desc=False).execute()
    transcript_rows = transcript_response.data or []
    
    # Format transcripts to match frontend expectation (optional depending on frontend)
    # Assuming frontend expects [{"speaker": "ai", "text": "..."}]
    formatted_transcript = []
    for r in transcript_rows:
        formatted_transcript.append({
            "speaker": r.get("speaker"),
            "text": r.get("text"),
            "timestamp": r.get("timestamp")
        })
    
    mapped = map_call(call_data)
    mapped["transcript"] = formatted_transcript
    
    return mapped
