# Frontend Streaming Integration Guide

## Backend Streaming Endpoint

✅ **NEW:** `/api/chat/stream` (Server-Sent Events)

Sends tokens in real-time as they're generated.

## Frontend Changes Needed

### 1. Update Chat Component

```typescript
// In your chat component (e.g., app/session/[id]/page.tsx or components/Chat.tsx)

async function sendMessageWithStreaming(message: string, sessionId: string) {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: message
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  let fullResponse = '';
  let sources = [];
  let messageId = '';
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.type === 'start') {
          // Initialize with sources
          sources = data.sources;
        } else if (data.type === 'token') {
          // Append token to display
          fullResponse += data.content;
          // Update UI here - show fullResponse in real-time
          setCurrentResponse(fullResponse);
        } else if (data.type === 'done') {
          // Streaming complete
          messageId = data.message_id;
          // Final update with concepts
        } else if (data.type === 'error') {
          console.error('Streaming error:', data.message);
        }
      }
    }
  }
  
  return { fullResponse, sources, messageId };
}
```

### 2. Use EventSource (Alternative - Simpler)

```typescript
function sendMessageWithEventSource(message: string, sessionId: string) {
  const token = localStorage.getItem('token');
  
  const eventSource = new EventSource(
    `http://localhost:8000/api/chat/stream?` + 
    new URLSearchParams({
      session_id: sessionId,
      message: message,
      token: token
    })
  );
  
  let fullResponse = '';
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'token') {
      fullResponse += data.content;
      setCurrentResponse(fullResponse); // Update UI
    } else if (data.type === 'done') {
      eventSource.close();
    }
  };
  
  eventSource.onerror = (error) => {
    console.error('EventSource error:', error);
    eventSource.close();
  };
}
```

### 3. Update Chat State

```typescript
// Add streaming message state
const [streamingMessage, setStreamingMessage] = useState('');
const [isStreaming, setIsStreaming] = useState(false);

// In your send message function
const handleSendMessage = async (message: string) => {
  setIsStreaming(true);
  setStreamingMessage('');
  
  // Use streaming function
  await sendMessageWithStreaming(message, sessionId);
  
  setIsStreaming(false);
};

// In your JSX, show streaming message
{isStreaming && (
  <div className="streaming-message">
    <ReactMarkdown>{streamingMessage}</ReactMarkdown>
    <div className="typing-indicator">▊</div>
  </div>
)}
```

## Quick Test

**Test streaming endpoint manually:**
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"session_id": "SESSION_ID", "message": "What is a variable?"}' \
  --no-buffer
```

You should see tokens appearing in real-time!

## Fallback

The original `/api/chat` endpoint still works (non-streaming).
Use it as fallback if streaming fails.
