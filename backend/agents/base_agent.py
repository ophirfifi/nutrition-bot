import logging

from anthropic import AsyncAnthropic

from config import settings

logger = logging.getLogger(__name__)

MODEL = "claude-opus-4-6"


class BaseAgent:
    """
    Base class for all agents.
    Handles Claude API calls with prompt caching on system prompts.
    """

    def __init__(self) -> None:
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = MODEL

    async def call_claude(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 2048,
    ) -> str:
        """
        Call Claude Opus 4.6 with prompt caching on the system prompt.
        Raises on API error (caller must handle).
        """
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=[
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=messages,
            )
            return response.content[0].text
        except Exception as exc:
            logger.error("Claude API error in %s: %s", self.__class__.__name__, exc, exc_info=True)
            raise

    async def call_claude_vision(
        self,
        system: str,
        photo_base64: str,
        media_type: str,
        text_prompt: str,
        max_tokens: int = 2048,
    ) -> str:
        """Call Claude with an image + text prompt (Vision API)."""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": photo_base64,
                        },
                    },
                    {"type": "text", "text": text_prompt},
                ],
            }
        ]
        return await self.call_claude(system=system, messages=messages, max_tokens=max_tokens)
