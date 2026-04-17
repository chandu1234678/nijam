# Voice Recording Feature - Setup Guide

## Overview
Production-ready voice recording and transcription feature for fact-checking audio claims.

## Features
- 🎤 High-quality audio recording with MediaRecorder API
- 🌊 Real-time waveform visualization
- ⏱️ Recording timer with auto-stop at 5 minutes
- 🌍 Multi-language support (English, Spanish, French, German, Hindi, Telugu)
- 🔄 Automatic transcription using OpenAI Whisper API
- ✅ Direct integration with fact-checking pipeline
- 📱 Mobile-friendly responsive design

## Backend Setup

### 1. Install Dependencies
```bash
cd backend
pip install openai>=1.0.0
```

### 2. Configure OpenAI API Key
Add to `backend/.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Restart Backend
```bash
cd backend
uvicorn app.main:app --reload
```

## API Endpoints

### POST /audio/transcribe
Transcribe audio file to text.

**Request:**
- `audio`: Audio file (multipart/form-data)
- `language`: Language code (default: "en")

**Response:**
```json
{
  "success": true,
  "text": "transcribed text",
  "language": "en",
  "confidence": 0.95,
  "service": "whisper",
  "duration": 12.5
}
```

### POST /audio/verify
Transcribe audio and verify the claim in one call.

**Request:**
- `audio`: Audio file (multipart/form-data)
- `language`: Language code (default: "en")

**Response:**
```json
{
  "verdict": "fake",
  "confidence": 0.87,
  "explanation": "...",
  "evidence_articles": [...],
  "transcription": {
    "text": "transcribed claim",
    "confidence": 0.95,
    "service": "whisper"
  }
}
```

## Extension Usage

### 1. Access Voice Recorder
- Open extension popup
- Click sidebar menu
- Select "Voice Check" (🎤 icon)

### 2. Record Audio
1. Click the microphone button
2. Allow microphone access (first time only)
3. Speak your claim clearly
4. Click again to stop recording

### 3. Review & Verify
1. Review the transcription
2. Click "Verify Claim" to fact-check
3. Or click "Record Again" to retry

## Technical Details

### Audio Format
- Primary: WebM (Opus codec)
- Fallback: MP4 (AAC codec)
- Max size: 25MB
- Max duration: 5 minutes

### Transcription Services
1. **OpenAI Whisper** (primary)
   - Best accuracy
   - Supports 50+ languages
   - Requires API key

2. **Google Speech-to-Text** (fallback)
   - Requires Google Cloud credentials
   - Optional

3. **AssemblyAI** (alternative)
   - Requires API key
   - Optional

### Browser Compatibility
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Requires HTTPS
- Mobile: Supported on Android Chrome

## File Structure

```
backend/app/
├── routes/
│   └── audio_routes.py          # API endpoints
├── analysis/
│   └── audio_transcription.py   # Transcription logic

extension/popup/
├── voice-recorder.html          # UI
├── voice-recorder.js            # Recording logic
└── shared.css                   # Styles
```

## Testing

### 1. Test Transcription
```bash
curl -X POST http://localhost:8000/audio/transcribe \
  -F "audio=@test.webm" \
  -F "language=en"
```

### 2. Test Verification
```bash
curl -X POST http://localhost:8000/audio/verify \
  -F "audio=@test.webm" \
  -F "language=en"
```

## Troubleshooting

### Microphone Access Denied
- Check browser permissions
- Ensure HTTPS (required for production)
- Try different browser

### Transcription Failed
- Verify OPENAI_API_KEY is set
- Check audio file size (<25MB)
- Ensure audio is not empty
- Check API quota/billing

### No Audio Recorded
- Check microphone is connected
- Test microphone in system settings
- Try different browser
- Check for browser extensions blocking access

## Cost Estimation

OpenAI Whisper API pricing:
- $0.006 per minute of audio
- Example: 100 recordings/day × 1 min avg = $18/month

## Security Notes

- Audio files are NOT stored on server
- Transcription happens in real-time
- Files are processed in memory only
- No audio data is logged
- HTTPS required for production

## Future Enhancements

- [ ] Offline transcription (browser-based)
- [ ] Audio file upload (in addition to recording)
- [ ] Speaker diarization (multiple speakers)
- [ ] Real-time streaming transcription
- [ ] Audio quality indicators
- [ ] Background noise reduction
- [ ] Transcript editing before verification
- [ ] Save audio recordings to history

## Support

For issues or questions:
1. Check browser console for errors
2. Verify API key is configured
3. Test with simple short recording first
4. Check network tab for API responses
