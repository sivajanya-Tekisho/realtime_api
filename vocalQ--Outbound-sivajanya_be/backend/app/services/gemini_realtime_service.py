import json
import logging
import asyncio
import websockets
import base64
import audioop # Warning: Deprecated in 3.13, but efficient
from datetime import datetime
from app.core.config import settings
from app.services.qdrant_service import QdrantService
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class GeminiRealtimeService:
    def __init__(self, stream_sid: str | None, send_to_twilio_func: Callable[[str], Awaitable[None]]):
        self.stream_sid = stream_sid
        self.send_to_twilio = send_to_twilio_func
        self.ws = None
        self.qdrant = QdrantService()
        self.is_connected = False
        self.session_id = None
        self.transcript = []
        self._connection_event = asyncio.Event()
        
        # Audio processing state
        self.rate_cv_state = None

        # System instructions
        self.instructions = """
You are VocalQ.ai’s professional AI phone assistant.

ROLE & TONE:
- You are polite, confident, calm, and helpful.
- Sound natural and human, not robotic.
- Use short, clear sentences suitable for phone calls.
- Be empathetic when users sound confused or frustrated.

CALL OPENING:
- Say EXACTLY this immediately: "Hello, thank you for calling VocalQ support. How can I help you today?"
- Do not add anything else.

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
"""

    async def connect(self):
        """Connect to Gemini Live API."""
        # URI for Gemini 2.0 Flash (confirn model name if 2.5 is available, but currently 2.0 is the live one)
        # Using the standard websocket endpoint
        model = "models/gemini-2.0-flash-exp" 
        url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={settings.GEMINI_API_KEY}"
        
        try:
            logger.info(f"Connecting to Gemini Live API at {url.split('?')[0]}...")
            self.ws = await websockets.connect(url)
            self.is_connected = True
            self._connection_event.set()
            logger.info("--- Connected to Gemini Live API ---")
            
            # Send Setup Message
            await self.send_setup()
            
            # Start the receive loop
            asyncio.create_task(self.receive_loop())
            
        except Exception as e:
            logger.error(f"Failed to connect to Gemini Live: {e}")
            raise e

    async def wait_for_connection(self):
        """Waits until the WebSocket is connected."""
        await self._connection_event.wait()

    async def send_setup(self):
        """Configure the session with tools and instructions."""
        setup_msg = {
            "setup": {
                "model": "models/gemini-2.0-flash-exp",
                "generation_config": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "Puck" 
                            }
                        }
                    }
                },
                "system_instruction": {
                    "parts": [{"text": self.instructions}]
                },
                "tools": [
                    {
                        "function_declarations": [
                            {
                                "name": "query_knowledge_base",
                                "description": "Search the knowledge base for answer to user questions about the company, services, or policies.",
                                "parameters": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "query": {
                                            "type": "STRING",
                                            "description": "The search query based on user's question."
                                        }
                                    },
                                    "required": ["query"]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        await self.ws.send(json.dumps(setup_msg))

    async def send_greeting(self):
        # Trigger an initial response based on the system instructions
        # We send a "client_content" message acting as a system trigger
        # content_user acts as a trigger for the model to generate the greeting
        msg = {
            "client_content": {
                "turns": [{
                    "role": "user",
                    "parts": [{"text": "Answer the call."}]
                }],
                "turn_complete": True
            }
        }
        await self.ws.send(json.dumps(msg))

    async def enable_vad(self):
        # Gemini handles VAD automatically, but we can tweak generation config if needed
        # No explicit "enable_vad" message for Gemini usually, it's always listening in Bidi
        pass 

    async def send_audio(self, audio_b64: str):
        """Appends audio to the input buffer."""
        if not self.is_connected:
            return
            
        try:
            # Twilio sends base64 encoded mulaw (8000Hz)
            audio_bytes = base64.b64decode(audio_b64)
            
            # Convert mulaw to PCM 16-bit
            pcm_data = audioop.ulaw2lin(audio_bytes, 2)
            
            # Resample 8k -> 16k (Gemini standard)
            # audioop.ratecv(fragment, width, nchannels, inrate, outrate, state[, weightA[, weightB]])
            # width=2 (16-bit), nchannels=1
            pcm_16k, self.rate_cv_state = audioop.ratecv(pcm_data, 2, 1, 8000, 16000, self.rate_cv_state)
            
            # Encode back to base64 for JSON
            pcm_b64 = base64.b64encode(pcm_16k).decode('utf-8')
            
            msg = {
                "realtime_input": {
                    "media_chunks": [
                        {
                            "mime_type": "audio/pcm",
                            "data": pcm_b64
                        }
                    ]
                }
            }
            await self.ws.send(json.dumps(msg))
        except Exception as e:
            logger.error(f"Error sending audio to Gemini: {e}")

    async def close(self):
        """Close connection."""
        self.is_connected = False
        if self.ws:
            await self.ws.close()

    async def receive_loop(self):
        """Handle incoming messages from Gemini."""
        try:
            async for message in self.ws:
                # message can be str or bytes? specific helper for Bidi might return bytes sometimes
                # websockets.connect returns text frames by default for text messages
                data = json.loads(message)
                
                # Check for serverContent
                server_content = data.get("serverContent")
                if server_content:
                    model_turn = server_content.get("modelTurn")
                    if model_turn:
                        parts = model_turn.get("parts", [])
                        for part in parts:
                            
                            # Handle Audio
                            inline_data = part.get("inlineData")
                            if inline_data:
                                mime_type = inline_data.get("mimeType")
                                audio_data_b64 = inline_data.get("data")
                                
                                if mime_type.startswith("audio/"):
                                    # Gemini returns PCM 24kHz usually.
                                    # We need to convert it back to Twilio format (mulaw 8k)
                                    
                                    pcm_bytes = base64.b64decode(audio_data_b64)
                                    
                                    # Downsample 24k -> 8k
                                    # Depending on what Gemini sends (usually 24k)
                                    # Let's assume 24000 input
                                    
                                    # ratecv from 24000 to 8000
                                    pcm_8k, _ = audioop.ratecv(pcm_bytes, 2, 1, 24000, 8000, None)
                                    
                                    # Convert PCM to mulaw
                                    mulaw_bytes = audioop.lin2ulaw(pcm_8k, 2)
                                    mulaw_b64 = base64.b64encode(mulaw_bytes).decode('utf-8')
                                    
                                    if self.stream_sid:
                                        media_message = {
                                            "event": "media",
                                            "streamSid": self.stream_sid,
                                            "media": {
                                                "payload": mulaw_b64
                                            }
                                        }
                                        await self.send_to_twilio(json.dumps(media_message))
                                    
                            # Handle Text (Transcript)
                            text_data = part.get("text")
                            if text_data:
                                logger.info(f"Gemini: {text_data}")


                    turn_complete = server_content.get("turnComplete")
                    # if turn_complete:
                    #     logger.info("Turn complete")

                    interrupted = server_content.get("interrupted")
                    if interrupted:
                        logger.info("Gemini Interrupted")
                        await self.send_to_twilio(json.dumps({
                            "event": "clear",
                            "streamSid": self.stream_sid
                        }))
                
                # Handle Tool Calls
                tool_calls = data.get("toolCall")
                if tool_calls:
                     function_calls = tool_calls.get("functionCalls", [])
                     for fc in function_calls:
                         await self.handle_function_call(fc)

        except Exception as e:
            logger.error(f"Error in Gemini receive loop: {e}")
        finally:
            self.is_connected = False

    async def handle_function_call(self, function_call):
        """Execute the function and return the output."""
        try:
            fc_id = function_call.get("id")
            name = function_call.get("name")
            args = function_call.get("args", {})
            
            logger.info(f"Tool Call: {name} Args: {args}")
            
            result_text = ""
            if name == "query_knowledge_base":
                query = args.get("query")
                results = await self.qdrant.search(query, limit=3)
                result_text = "\n".join(results) if results else "No information found."
            
            # Send Output
            tool_response = {
                "tool_response": {
                    "function_responses": [
                        {
                            "id": fc_id,
                            "name": name,
                            "response": {
                                "result": {
                                    "object_value": result_text 
                                    # note: Gemini expects specific format depending on return type
                                    # or just a dict 
                                }
                            }
                        }
                    ]
                }
            }
            await self.ws.send(json.dumps(tool_response))
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
