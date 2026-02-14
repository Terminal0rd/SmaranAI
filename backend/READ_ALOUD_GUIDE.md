# Read Aloud Button - Quick Integration Guide

## ✅ Backend Ready

New endpoint created: **POST `/api/chat/read-aloud/{message_id}`**

Generates audio on-demand when user clicks button.

---

## Frontend Integration

### 1. Add the Button Component

Copy `ReadAloudButton.tsx` to your components folder.

### 2. Use in Chat Messages

```tsx
// In your chat message component (e.g., ChatMessage.tsx)
import { ReadAloudButton } from '@/components/ReadAloudButton';

function ChatMessage({ message }: { message: Message }) {
  return (
    <div className="message">
      {/* AI response content */}
      <div className="content">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>

      {/* Read Aloud button (only for assistant messages) */}
      {message.role === 'assistant' && (
        <div className="mt-2">
          <ReadAloudButton 
            messageId={message.id} 
            messageContent={message.content}  
          />
        </div>
      )}
    </div>
  );
}
```

---

## How It Works

1. **User clicks "Read Aloud" button**
2. Frontend calls: `POST /api/chat/read-aloud/{message_id}`
3. Backend generates audio using TTS (1-2 seconds)
4. Returns: `{ "audio_url": "/static/audio/response_123.mp3" }`
5. Frontend plays audio immediately
6. Button shows "Playing..." state
7. User can pause/resume by clicking again

---

## Features

✅ **On-demand generation** - Audio created only when requested
✅ **No auto-generate lag** - Chat responses stay fast
✅ **Play/Pause toggle** - Click button to pause/resume
✅ **Loading state** - Shows "Generating..." while creating audio
✅ **Error handling** - Shows alert if generation fails
✅ **Visual feedback** - Button changes color when playing

---

## Testing

1. **Backend**: Already running with Read Aloud endpoint
2. **Send a chat message**
3. **Click "Read Aloud" button** below AI response
4. **Audio generates** and plays automatically
5. **Click again** to pause
6. **Click again** to resume from pause

---

## No Config Needed!

This endpoint works **independently** of `ENABLE_VOICE_TUTOR` setting.

You can:
- Set `ENABLE_VOICE_TUTOR=False` (no auto-generation)
- Use Read Aloud button (on-demand generation)

Or:
- Set `ENABLE_VOICE_TUTOR=True` (auto-generate + button)
- Button will reuse existing audio if available

---

## API Response

```json
POST /api/chat/read-aloud/{message_id}

Response:
{
  "message_id": "abc123",
  "audio_url": "/static/audio/response_abc123.mp3",
  "status": "success"
}
```

---

**Status**: ✅ Ready to use! Just add the button component to your chat UI.
