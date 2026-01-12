import logging
import json
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

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
        Generates a summary of the call transcript using an LLM.
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
            
            system_prompt = (
                "You are an expert AI call analyst. Summarize the following phone conversation concisely. "
                "Identify the main topic, the user's intent, and the outcome."
            )
            
            response = await aclient.chat.completions.create(
                model="gpt-4o-mini", # or gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the transcript:\n\n{conversation_text}"}
                ],
                max_tokens=150
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Summary generation failed."
