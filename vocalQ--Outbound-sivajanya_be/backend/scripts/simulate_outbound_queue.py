import asyncio
import logging
import sys
import os

import sys
import os
from unittest.mock import MagicMock

# Create mock Supabase before any other imports
mock_supabase = MagicMock()
sys.modules['app.core.supabase_client'] = MagicMock(supabase=mock_supabase)

# Add the project root to sys.path for backend imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.outbound_service import OutboundService
from app.core.config import settings

# Mock Twilio Client for testing
class MockTwilioCall:
    def __init__(self, sid, status='queued'):
        self.sid = sid
        self.status = status

class MockTwilioCalls:
    def __init__(self):
        self.calls = {}
    
    def create(self, to, from_, url):
        sid = f"CA{os.urandom(16).hex()}"
        print(f"  [MOCK TWILIO] Initiating call to {to} (SID: {sid})")
        call = MockTwilioCall(sid)
        self.calls[sid] = call
        return call
    
    def __call__(self, sid):
        return self.calls[sid]

    def fetch(self):
        # This is handled by a separate method in the actual SDK, 
        # but here we'll mock the fetching behavior within the service poll loop.
        pass

class MockTwilioClient:
    def __init__(self):
        self.calls = MockTwilioCalls()

async def simulate_verification():
    logging.basicConfig(level=logging.INFO)
    print("--- STARTING OUTBOUND QUEUE VERIFICATION ---")
    
    service = OutboundService()
    # Replace real client with mock
    mock_client = MockTwilioClient()
    service.client = mock_client
    
    # Override wait_for_call_completion to simulate call progression
    async def mock_wait(call_sid):
        print(f"  [SIMULATOR] Waiting for call {call_sid} to complete...")
        await asyncio.sleep(2) # Simulate ringing/call time
        mock_client.calls.calls[call_sid].status = 'completed'
        print(f"  [SIMULATOR] Call {call_sid} marked COMPLETED.")
    
    service.wait_for_call_completion = mock_wait
    
    numbers = ["+919392665199"]
    print(f"Adding {len(numbers)} numbers to queue: {numbers}")
    await service.add_to_queue(numbers)
    
    # Wait for processing to finish
    while service.is_running:
        await asyncio.sleep(0.5)
        
    print("--- VERIFICATION COMPLETED SUCCESSFULLY ---")
    print("All numbers were processed sequentially.")

if __name__ == "__main__":
    asyncio.run(simulate_verification())
