"""
Audio transcription for voice-based fact-checking

Supports multiple transcription services:
- OpenAI Whisper API (primary)
- Google Speech-to-Text (fallback)
- AssemblyAI (alternative)
"""

import os
import logging
import tempfile
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


async def transcribe_audio_whisper(audio_data: bytes, language: str = "en") -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_data: Audio file bytes (mp3, wav, webm, etc.)
        language: Language code (default: en)
    
    Returns:
        Dict with 'text', 'language', 'confidence'
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    
    try:
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        # Call Whisper API
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(temp_path, "rb") as audio_file:
                files = {"file": ("audio.webm", audio_file, "audio/webm")}
                data = {
                    "model": "whisper-1",
                    "language": language,
                    "response_format": "verbose_json"
                }
                headers = {"Authorization": f"Bearer {api_key}"}
                
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    files=files,
                    data=data,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
        
        # Cleanup temp file
        os.unlink(temp_path)
        
        return {
            "text": result.get("text", ""),
            "language": result.get("language", language),
            "confidence": 0.95,  # Whisper doesn't provide confidence
            "duration": result.get("duration", 0),
            "service": "whisper"
        }
    
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        # Cleanup temp file on error
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise


async def transcribe_audio_google(audio_data: bytes, language: str = "en") -> Dict[str, Any]:
    """
    Transcribe audio using Google Speech-to-Text API
    
    Args:
        audio_data: Audio file bytes
        language: Language code (default: en-US)
    
    Returns:
        Dict with 'text', 'language', 'confidence'
    """
    try:
        from google.cloud import speech
        
        client = speech.SpeechClient()
        
        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code=f"{language}-US" if language == "en" else language,
            enable_automatic_punctuation=True,
            model="latest_long"
        )
        
        response = client.recognize(config=config, audio=audio)
        
        if not response.results:
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "service": "google"
            }
        
        # Get best result
        result = response.results[0]
        alternative = result.alternatives[0]
        
        return {
            "text": alternative.transcript,
            "language": language,
            "confidence": alternative.confidence,
            "service": "google"
        }
    
    except Exception as e:
        logger.error(f"Google transcription failed: {e}")
        raise


async def transcribe_audio_assemblyai(audio_data: bytes) -> Dict[str, Any]:
    """
    Transcribe audio using AssemblyAI API
    
    Args:
        audio_data: Audio file bytes
    
    Returns:
        Dict with 'text', 'language', 'confidence'
    """
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise ValueError("ASSEMBLYAI_API_KEY not configured")
    
    try:
        headers = {"authorization": api_key}
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Upload audio
            upload_response = await client.post(
                "https://api.assemblyai.com/v2/upload",
                headers=headers,
                content=audio_data
            )
            upload_response.raise_for_status()
            audio_url = upload_response.json()["upload_url"]
            
            # Request transcription
            transcript_request = {
                "audio_url": audio_url,
                "language_detection": True,
                "punctuate": True,
                "format_text": True
            }
            
            transcript_response = await client.post(
                "https://api.assemblyai.com/v2/transcript",
                headers=headers,
                json=transcript_request
            )
            transcript_response.raise_for_status()
            transcript_id = transcript_response.json()["id"]
            
            # Poll for completion
            import asyncio
            while True:
                status_response = await client.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers=headers
                )
                status_response.raise_for_status()
                result = status_response.json()
                
                if result["status"] == "completed":
                    return {
                        "text": result["text"],
                        "language": result.get("language_code", "en"),
                        "confidence": result.get("confidence", 0.9),
                        "service": "assemblyai"
                    }
                elif result["status"] == "error":
                    raise Exception(f"Transcription failed: {result.get('error')}")
                
                await asyncio.sleep(2)
    
    except Exception as e:
        logger.error(f"AssemblyAI transcription failed: {e}")
        raise


async def transcribe_audio(
    audio_data: bytes,
    language: str = "en",
    service: str = "auto"
) -> Dict[str, Any]:
    """
    Transcribe audio using available service
    
    Args:
        audio_data: Audio file bytes
        language: Language code
        service: Preferred service (auto, whisper, google, assemblyai)
    
    Returns:
        Dict with transcription result
    """
    # Try services in order of preference
    services = []
    
    if service == "whisper" or service == "auto":
        if os.getenv("OPENAI_API_KEY"):
            services.append(("whisper", transcribe_audio_whisper))
    
    if service == "google" or service == "auto":
        try:
            from google.cloud import speech
            services.append(("google", transcribe_audio_google))
        except ImportError:
            pass
    
    if service == "assemblyai" or service == "auto":
        if os.getenv("ASSEMBLYAI_API_KEY"):
            services.append(("assemblyai", transcribe_audio_assemblyai))
    
    if not services:
        raise ValueError("No transcription service configured")
    
    # Try each service
    last_error = None
    for service_name, transcribe_func in services:
        try:
            logger.info(f"Attempting transcription with {service_name}")
            result = await transcribe_func(audio_data, language)
            logger.info(f"Transcription successful with {service_name}")
            return result
        except Exception as e:
            logger.warning(f"{service_name} transcription failed: {e}")
            last_error = e
            continue
    
    # All services failed
    raise Exception(f"All transcription services failed. Last error: {last_error}")


def validate_audio_file(audio_data: bytes, max_size_mb: int = 25) -> bool:
    """
    Validate audio file size and format
    
    Args:
        audio_data: Audio file bytes
        max_size_mb: Maximum file size in MB
    
    Returns:
        True if valid
    
    Raises:
        ValueError if invalid
    """
    # Check size
    size_mb = len(audio_data) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"Audio file too large: {size_mb:.1f}MB (max {max_size_mb}MB)")
    
    # Check minimum size (at least 1KB)
    if len(audio_data) < 1024:
        raise ValueError("Audio file too small (minimum 1KB)")
    
    return True
