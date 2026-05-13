"""
Vision API uses the Gemini multimodal pipeline in `lankaguide.services.vision_service`.

The previous MobileNet placeholder has been retired in favour of `gemini-1.5-flash`
image understanding (PRD multimodal / literature gap).
"""

from lankaguide.services.vision_service import VisionService

__all__ = ["VisionService"]
