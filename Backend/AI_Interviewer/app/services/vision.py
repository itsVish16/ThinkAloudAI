import asyncio
import logging
import os
import base64
import io
from livekit import rtc
from openai import AsyncOpenAI
from PIL import Image

logger = logging.getLogger("vision_service")

_vlm_instance = None

def get_vlm_service():
    global _vlm_instance
    if _vlm_instance is None:
        logger.info("Initializing global LocalVLMService instance (now using Fireworks API)...")
        _vlm_instance = LocalVLMService()
    return _vlm_instance

class LocalVLMService:
    def __init__(self):
        """
        Initializes the VLM service to use Qwen via Fireworks API.
        """
        self.api_key = os.getenv("FIREWORKS_API_KEY")
        if not self.api_key:
            logger.warning("FIREWORKS_API_KEY is not set. Vision service will fail.")
            
        self.client = AsyncOpenAI(
            api_key=self.api_key or "dummy_key_not_set",
            base_url="https://api.fireworks.ai/inference/v1"
        )
        self.model = "accounts/fireworks/models/qwen3p7-plus"

    async def analyze_frame(self, frame: rtc.VideoFrame, is_whiteboard=False) -> str:
        """
        Analyzes a single video frame using Qwen on Fireworks and returns a textual description.
        """
        if not self.api_key:
            return "Visual Context: Vision API key not configured."

        try:
            # Convert LiveKit VideoFrame to a PIL Image
            argb_frame = frame.convert(rtc.VideoBufferType.ARGB)
            image = Image.frombytes(
                "RGBA", 
                (argb_frame.width, argb_frame.height), 
                argb_frame.data
            ).convert("RGB")
            
            # Downscale for performance and API limits
            image.thumbnail((512, 512))
            
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            prompt_text = "Analyze the candidate's facial expression, focus, body language, and overall behavior in detail. Describe exactly what they are doing."
            if is_whiteboard:
                prompt_text = "Analyze the content of the shared screen or whiteboard in detail. Extract all text, components, data flows, or code visible on the screen. Describe the visual layout and any diagrams."

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_str}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt_text
                            }
                        ]
                    }
                ],
                max_tokens=50,
                temperature=0.2
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error processing video frame via Fireworks API: {e}")
            return "Visual Context: Failed to process frame."
