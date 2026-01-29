import logging
import json
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    _greeting = "Hello, thank you for calling VocalQ.ai support. How can I help you today?"

    @classmethod
    def get_greeting(cls):
        return cls._greeting
                                                 
    @classmethod
    def set_greeting(cls, text: str):
        cls._greeting = text
        logger.info(f"AI Greeting updated to: {text}")

    @classmethod
    async def summarize_call(cls, transcript: list) -> str:
        """
        Generates a summary of the call transcript using Gemini 2.0 Flash.
        Transcript is expected to be a list of dicts: [{"role": "user/assistant", "content": "..."}]
        """
        if not transcript:
            return "No transcript available."

        try:
            # Format transcript for prompt
            conversation_text = ""
            for turn in transcript:
                role = turn.get("role", "unknown")
                content = turn.get("content", "")
                conversation_text += f"{role.upper()}: {content}\n"
            
            system_instruction = (
                "You are an expert AI call analyst. Summarize the following phone conversation concisely. "
                "Identify the main topic, the user's intent, and the outcome."
            )
            
            prompt = f"{system_instruction}\n\nHere is the transcript:\n\n{conversation_text}"
            
            # Gemini Check
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                # Extract text
                # Structure: candidates[0].content.parts[0].text
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            
            return "Summary unavailable (No content returned)."

        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {e}")
            return "Summary generation failed."
