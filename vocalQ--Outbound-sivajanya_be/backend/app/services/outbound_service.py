import asyncio
import logging
from typing import List, Optional
from twilio.rest import Client
from app.core.config import settings
from app.core.supabase_client import supabase

logger = logging.getLogger(__name__)

class OutboundService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.queue = asyncio.Queue()
        self.is_running = False
        self.current_call_sid = None

    async def add_to_queue(self, phone_numbers: List[str]):
        """Add a list of phone numbers to the outbound queue (DB backed)."""
        from datetime import datetime, timezone
        
        for number in phone_numbers:
            # 1. Check/Insert Contact
            try:
                res = supabase.table("contacts").select("id").eq("phone_number", number).execute()
                if res.data:
                    contact_id = res.data[0]['id']
                else:
                    # Create new contact
                    new_contact = {"phone_number": number, "name": "Unknown"} # Default name
                    res = supabase.table("contacts").insert(new_contact).execute()
                    if res.data:
                        contact_id = res.data[0]['id']
                    else:
                        logger.error(f"Failed to create contact for {number}")
                        continue
                
                # 2. Insert into Call Queue
                queue_item = {
                    "contact_id": contact_id,
                    "scheduled_time": datetime.now(timezone.utc).isoformat(),
                    "status": "pending",
                    "attempt_count": 0
                }
                supabase.table("call_queue").insert(queue_item).execute()
                logger.info(f"Added {number} (Contact: {contact_id}) to DB call_queue.")
                
            except Exception as e:
                logger.error(f"Error adding {number} to queue: {e}")
        
        if not self.is_running:
            asyncio.create_task(self.process_queue())

    async def check_eligibility(self, phone_number: str) -> bool:
        """Performed before calling a number."""
        # TODO: Implement real eligibility logic (e.g., check Supabase)
        logger.info(f"Checking eligibility for {phone_number}...")
        return True

    async def get_ngrok_url(self):
        """Try to fetch the active ngrok tunnel URL from local API."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://127.0.0.1:4040/api/tunnels")
                if response.status_code == 200:
                    data = response.json()
                    tunnels = data.get("tunnels", [])
                    for tunnel in tunnels:
                        if tunnel.get("proto") == "https":
                            return tunnel.get("public_url")
        except Exception as e:
            logger.warning(f"Could not fetch ngrok URL: {e}")
        return None

    async def process_queue(self):
        """DB-backed processing of the phone number queue."""
        self.is_running = True
        logger.info(f"--- OUTBOUND QUEUE PROCESSOR STARTED (DB Mode) ---")
        
        from datetime import datetime, timezone, timedelta
        
        while True: # Infinite loop to poll DB
            try:
                # 0. Validate Env
                if not settings.TWILIO_PHONE_NUMBER:
                    logger.error("--- TWILIO_PHONE_NUMBER missing. Stopping processor. ---")
                    break

                # 1. Fetch pending items
                # status='pending' OR (status='retry_scheduled' AND next_retry_at <= now)
                # Supabase REST doesn't support complex OR easily in one query without raw SQL or multiple queries.
                # We'll fetch pending first.
                now_iso = datetime.now(timezone.utc).isoformat()
                
                # Fetch one pending item
                prospect = None
                
                # Try pending
                res = supabase.table("call_queue").select("*, contacts(phone_number)").eq("status", "pending").limit(1).execute()
                if res.data:
                    prospect = res.data[0]
                else:
                    # Try retry_scheduled
                    res = supabase.table("call_queue").select("*, contacts(phone_number)").eq("status", "retry_scheduled").lte("next_retry_at", now_iso).limit(1).execute()
                    if res.data:
                        prospect = res.data[0]
                
                if not prospect:
                    # No work, sleep and continue
                    # logger.debug("No pending calls. Waiting...") 
                    await asyncio.sleep(5)
                    continue
                
                # We have a prospect
                queue_id = prospect['id']
                contact = prospect.get('contacts')
                phone_number = contact.get('phone_number') if contact else None
                
                if not phone_number:
                    logger.error(f"Queue item {queue_id} has no valid contact phone number.")
                    supabase.table("call_queue").update({"status": "failed_final", "error_reason": "No phone number"}).eq("id", queue_id).execute()
                    continue

                logger.info(f"--- [OUTBOUND] Processing Queue ID: {queue_id} (Number: {phone_number}) ---")
                
                # Mark as calling
                supabase.table("call_queue").update({"status": "calling", "last_call_at": datetime.now(timezone.utc).isoformat()}).eq("id", queue_id).execute()
                
                # Detect ngrok
                public_url = await self.get_ngrok_url()
                if not public_url:
                     logger.error("--- [OUTBOUND] No public URL (ngrok). Rescheduling... ---")
                     # Logic to reschedule or sleep?
                     await asyncio.sleep(10)
                     continue

                attempt_count = prospect.get("attempt_count", 0)
                webhook_url = f"{public_url}{settings.API_V1_STR}/calls/twilio?queue_id={queue_id}&attempt_count={attempt_count}"
                
                # Trigger Call
                try:
                    logger.info(f"--- [OUTBOUND] Calling {phone_number}... ---")
                    call = self.client.calls.create(
                        to=phone_number,
                        from_=settings.TWILIO_PHONE_NUMBER,
                        url=webhook_url
                    )
                    
                    # Update DB with Call SID
                    supabase.table("call_queue").update({"call_sid": call.sid}).eq("id", queue_id).execute()
                    self.current_call_sid = call.sid # For status report (only tracks last one now)

                    # Monitor Call
                    final_status = await self.wait_for_call_completion(call.sid)
                    
                    # Handle Result
                    if final_status == 'completed':
                        supabase.table("call_queue").update({"status": "answered"}).eq("id", queue_id).execute()
                    else:
                        # Retry Logic
                        current_attempts = prospect.get("attempt_count", 0) + 1
                        max_attempts = prospect.get("max_attempts", 3)
                        
                        if current_attempts >= max_attempts:
                            supabase.table("call_queue").update({
                                "status": "failed_final", 
                                "attempt_count": current_attempts,
                                "error_reason": final_status
                            }).eq("id", queue_id).execute()
                        else:
                            # Schedule retry (e.g., 5 mins later)
                            next_retry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
                            supabase.table("call_queue").update({
                                "status": "retry_scheduled", 
                                "attempt_count": current_attempts,
                                "next_retry_at": next_retry,
                                "error_reason": final_status
                            }).eq("id", queue_id).execute()
                            logger.info(f"--- [OUTBOUND] Call {final_status}. Rescheduled for {next_retry} ---")

                except Exception as e:
                    logger.error(f"Twilio Call Error: {e}")
                    supabase.table("call_queue").update({"status": "failed_final", "error_reason": str(e)[:200]}).eq("id", queue_id).execute()
                    
                logger.info(f"--- [OUTBOUND] Finished processing {queue_id}. Waiting 10s... ---")
                await asyncio.sleep(10)

            except Exception as outer_e:
                logger.error(f"Queue Processor Critical Error: {outer_e}")
                await asyncio.sleep(5)

    async def wait_for_call_completion(self, call_sid: str):
        """Poll Twilio for call status until it is completed."""
        final_status = "unknown"
        while True:
            try:
                call = self.client.calls(call_sid).fetch()
                if call.status in ['completed', 'busy', 'failed', 'no-answer', 'canceled']:
                    logger.info(f"Call {call_sid} ended with status: {call.status}")
                    final_status = call.status
                    break
            except Exception as e:
                logger.warning(f"Error checking call status: {e}")
                break # Break to avoid infinite loop on valid error
                
            await asyncio.sleep(3)
        return final_status
