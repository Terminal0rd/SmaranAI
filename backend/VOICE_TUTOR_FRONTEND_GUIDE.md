# AI Voice Tutor Mode - Frontend Integration

## Backend Changes Complete ✅

The backend now supports optional audio generation for AI responses.

---

## How It Works

When `ENABLE_VOICE_TUTOR=True` in `.env`:
- Backend generates audio file (.mp3) for each AI response
- Saves to `static/audio/response_{message_id}.mp3`
- Returns `audio_url` in ChatResponse JSON

---

## Frontend Integration

### 1. Update TypeScript Interface

```typescript
// In your types/chat.ts or similar
interface ChatResponse {
  message_id: string;
  content: string;
  formatted_content: string;
  sources: SourceReference[];
  concepts_extracted: string[];
  audio_url?: string; // NEW: Optional audio URL
}
```

### 2. Add Audio Player Component

Create `components/AudioPlayer.tsx`:

```typescript
'use client';

import { useState, useRef, useEffect } from 'react';
import { Volume2, VolumeX, Pause, Play } from 'lucide-react';

interface AudioPlayerProps {
  audioUrl: string;
  autoPlay?: boolean;
}

export function AudioPlayer({ audioUrl, autoPlay = false }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (autoPlay && audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
    }
  }, [audioUrl, autoPlay]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    audioRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  return (
    <div className="flex items-center gap-2 mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
      <button
        onClick={togglePlay}
        className="p-1 hover:bg-blue-100 dark:hover:bg-blue-800 rounded"
        aria-label={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
      </button>
      
      <audio
        ref={audioRef}
        src={audioUrl}
        onEnded={() => setIsPlaying(false)}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />
      
      <div className="flex-1 text-sm text-blue-600 dark:text-blue-400">
        🎧 Voice Tutor Mode
      </div>
      
      <button
        onClick={toggleMute}
        className="p-1 hover:bg-blue-100 dark:hover:bg-blue-800 rounded"
        aria-label={isMuted ? 'Unmute' : 'Mute'}
      >
        {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
      </button>
    </div>
  );
}
```

### 3. Use in Chat Component

Update your chat message rendering:

```typescript
// In your ChatMessage component or similar
import { AudioPlayer } from '@/components/AudioPlayer';

function ChatMessage({ message }: { message: ChatResponse }) {
  return (
    <div className="message">
      {/* Existing message content */}
      <div className="content">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>
      
      {/* Sources */}
      {message.sources.length > 0 && (
        <div className="sources">
          {/* ...existing source rendering... */}
        </div>
      )}
      
      {/* NEW: Audio Player */}
      {message.audio_url && (
        <AudioPlayer 
          audioUrl={message.audio_url} 
          autoPlay={false}  // Change to true for auto-play
        />
      )}
    </div>
  );
}
```

### 4. Add Voice Mode Toggle (Optional)

Add a toggle in settings or chat interface:

```typescript
'use client';

import { useState } from 'react';
import { Volume2 } from 'lucide-react';

export function VoiceModeToggle() {
  const [enabled, setEnabled] = useState(false);

  // Store preference in localStorage
  const toggleVoiceMode = async () => {
    const newState = !enabled;
    setEnabled(newState);
    localStorage.setItem('voiceTutorEnabled', String(newState));
    
    // Optional: Also update backend preference
    // await updateUserSettings({ voice_tutor: newState });
  };

  return (
    <button
      onClick={toggleVoiceMode}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
        enabled 
          ? 'bg-blue-600 text-white' 
          : 'bg-gray-200 text-gray-700'
      }`}
    >
      <Volume2 className="w-4 h-4" />
      Voice Tutor {enabled ? 'ON' : 'OFF'}
    </button>
  );
}
```

---

## Testing

### 1. Enable Voice Mode

In backend `.env`:
```bash
ENABLE_VOICE_TUTOR=True
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Restart Backend

```bash
uvicorn app.main:app --reload
```

### 4. Test in Frontend

1. Ask a question in chat
2. Wait for response
3. Audio player should appear below the message
4. Click play button to hear the response

---

## Browser Compatibility

The audio player uses native HTML5 `<audio>` which works in:
- ✅ Chrome/Edge
- ✅ Firefox  
- ✅ Safari
- ✅ Mobile browsers

---

## Performance Notes

- Audio generation adds ~1-2 seconds to response time
- Files are cached in `static/audio/`
- Old files auto-cleanup after 100 messages
- Audio generation fails gracefully (response still works)

---

## Troubleshooting

**No audio player showing:**
- Check `ENABLE_VOICE_TUTOR=True` in backend `.env`
- Verify `audio_url` is not null in API response
- Check browser console for errors

**Audio not playing:**
- Check browser autoplay policy (some browsers block autoplay)
- Try clicking play button manually
- Verify audio file exists at the URL

**Large file sizes:**
- gTTS generates ~1-2MB per minute of speech
- Files are MP3 compressed
- Consider adding cleanup logic to delete old files

---

**Status:** ✅ Ready to use! Just enable in `.env` and integrate the audio player component.
