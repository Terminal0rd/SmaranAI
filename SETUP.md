# SmaranAI - Complete Project Documentation

## Final Directory Tree

```
SmaranAI/
├── .gitignore
├── README.md
├── SETUP.md
│
├── backend/
│   ├── .env                          # Environment configuration
│   ├── .env.example                  # Template
│   ├── requirements.txt              # Python dependencies
│   ├── storage/
│   │   ├── .gitkeep
│   │   ├── uploads/                  # PDF uploads
│   │   │   └── .gitkeep
│   │   └── vectors.pkl               # GLOBAL vector store (auto-created)
│   │
│   └── app/
│       ├── __init__.py
│       ├── config.py                 # Pydantic settings
│       ├── database.py               # Async SQLAlchemy setup
│       ├── main.py                   # FastAPI app entry point
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py               # User model (JWT auth)
│       │   ├── subject.py            # Subject/topic model
│       │   ├── session.py            # Session, Message, SessionConcept
│       │   ├── mindmap.py            # MindMapNode, MindMapEdge
│       │   ├── quiz.py               # QuizAttempt, QuizQuestion
│       │   ├── progress.py           # Progress tracking
│       │   └── document.py           # Document, DocumentChunk
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── user.py               # Auth schemas
│       │   ├── subject.py
│       │   ├── session.py
│       │   ├── chat.py
│       │   ├── mindmap.py
│       │   ├── quiz.py
│       │   ├── progress.py
│       │   └── document.py
│       │
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py               # /api/auth/*
│       │   ├── subjects.py           # /api/subjects/*
│       │   ├── sessions.py           # /api/sessions/*
│       │   ├── chat.py               # /api/chat/*
│       │   ├── mindmap.py            # /api/mindmap/*
│       │   ├── quiz.py               # /api/quiz/*
│       │   ├── progress.py           # /api/progress/*
│       │   ├── documents.py          # /api/documents/*
│       │   └── export.py             # /api/export/* (PDF/PPT)
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth_service.py       # User CRUD, password hashing
│       │   ├── llm_service.py        # Phi-3 via /v1/chat/completions
│       │   ├── embedding_service.py  # SentenceTransformers + .pkl
│       │   ├── rag_service.py        # RAG retrieval + generation
│       │   ├── quiz_service.py       # Quiz generation + scoring
│       │   ├── mindmap_service.py    # Concept graph management
│       │   ├── progress_service.py   # Analytics aggregation
│       │   └── export_service.py     # PDF/PPT generation
│       │
│       └── utils/
│           ├── __init__.py
│           ├── security.py           # JWT, bcrypt, OAuth2
│           ├── pdf_parser.py         # PyMuPDF text extraction
│           └── text_chunker.py       # Chunk text for RAG
│
└── frontend/
    ├── .env.local                    # Frontend environment
    ├── .env.local.example
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    │
    └── src/
        ├── app/
        │   ├── globals.css           # Tailwind + custom styles
        │   ├── layout.tsx            # Root layout
        │   ├── page.tsx              # Landing page (/)
        │   │
        │   ├── login/
        │   │   └── page.tsx          # Login page
        │   │
        │   ├── register/
        │   │   └── page.tsx          # Multi-step register
        │   │
        │   └── (protected)/          # Auth-required routes
        │       ├── layout.tsx        # Auth guard wrapper
        │       │
        │       ├── dashboard/
        │       │   └── page.tsx      # Main dashboard
        │       │
        │       ├── learn/
        │       │   ├── page.tsx      # Subject/session selection
        │       │   └── [sessionId]/
        │       │       └── page.tsx  # Whiteboard chat + export
        │       │
        │       ├── quiz/
        │       │   └── [sessionId]/
        │       │       └── page.tsx  # Quiz interface + results
        │       │
        │       ├── mindmap/
        │       │   └── [subjectId]/
        │       │       └── page.tsx  # ReactFlow visualization
        │       │
        │       ├── progress/
        │       │   └── page.tsx      # Progress dashboard
        │       │
        │       └── upload/
        │           └── page.tsx      # PDF upload for RAG
        │
        ├── components/
        │   ├── Providers.tsx         # React Query + Toast
        │   ├── layout/
        │   │   └── Navbar.tsx
        │   └── ui/
        │       ├── index.ts
        │       ├── Button.tsx
        │       ├── Input.tsx
        │       └── Card.tsx
        │
        └── lib/
            ├── api.ts                # Axios client + all endpoints
            ├── auth-store.ts         # Zustand auth state
            ├── session-store.ts      # Session state
            └── utils.ts              # Helpers
```

---

## Setup Instructions (Windows)

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ installed
- llama-server running with Phi-3 model

### Step 1: Start LLM Server

```bash
# Navigate to llama directory
cd D:\llama

# Start llama-server with Phi-3 (OpenAI-compatible API)
llama-server.exe -m models\Phi-3-mini-4k-instruct-gguf\Phi-3-mini-4k-instruct-q4.gguf --port 8080
```

Verify it's running: http://127.0.0.1:8080/v1/models

### Step 2: Setup Backend

```bash
# Navigate to backend
cd D:\Projects\SmaranAI\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (already exists, verify settings)
# Edit .env if needed:
#   LLM_SERVER_URL=http://127.0.0.1:8080
#   DATABASE_URL=sqlite+aiosqlite:///./smaranai.db

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Step 3: Setup Frontend

```bash
# Open NEW terminal
cd D:\Projects\SmaranAI\frontend

# Install dependencies
npm install

# Verify .env.local exists with:
#   NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Frontend available at: http://localhost:3000

---

## Environment Variables

### Backend (.env)
```ini
DATABASE_URL=sqlite+aiosqlite:///./smaranai.db
SECRET_KEY=your-production-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LLM_SERVER_URL=http://127.0.0.1:8080
LLM_MAX_TOKENS=1024
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=storage/uploads
VECTOR_STORE_PATH=storage/vectors.pkl
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env.local)
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=SmaranAI
```

---

## Testing Checklist

### 1. Landing Page
- [ ] Visit http://localhost:3000
- [ ] Verify hero section loads with animations
- [ ] Click "Get Started" → goes to /register

### 2. Registration
- [ ] Fill in name, email, password → click Continue
- [ ] Fill in age, class, branch, learning goal → Create Account
- [ ] Should redirect to /dashboard

### 3. Login
- [ ] Logout, visit /login
- [ ] Enter email/password → Sign In
- [ ] Should redirect to /dashboard

### 4. Dashboard
- [ ] Stats cards show (Sessions, Quizzes, Score, Time)
- [ ] Quick actions visible
- [ ] Subjects list visible

### 5. Subject Selection & Session
- [ ] Click "Learn" in navbar
- [ ] Select a subject (e.g., Mathematics)
- [ ] Click "Start New Session"
- [ ] Should go to whiteboard chat

### 6. Whiteboard Chat (RAG)
- [ ] Type a question: "Explain quadratic equations"
- [ ] Wait for AI response
- [ ] Verify markdown formatting
- [ ] Slide appears in left timeline

### 7. Export
- [ ] Click PDF button → downloads PDF
- [ ] Click PPT button → downloads PowerPoint
- [ ] Open files to verify content

### 8. Quiz
- [ ] Click "Take Quiz" in session
- [ ] Answer 5 questions
- [ ] Submit → see results with score
- [ ] Weak topics highlighted

### 9. Mind Map
- [ ] Click "Mind Map" in navbar
- [ ] Select a subject
- [ ] Interactive nodes visible
- [ ] Click node → details panel shows
- [ ] Drag nodes to reposition

### 10. Progress Dashboard
- [ ] Click "Progress" in navbar
- [ ] Line chart shows quiz history
- [ ] Subject progress cards visible
- [ ] Weak topics listed

### 11. PDF Upload (RAG)
- [ ] Click "Upload" in navbar
- [ ] Select a subject
- [ ] Drag & drop a PDF
- [ ] Wait for processing
- [ ] Return to chat → answers now include PDF content

### 12. Session Resume
- [ ] Create a session, ask questions
- [ ] Navigate away
- [ ] Return to /learn → click same session
- [ ] Previous messages restored

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login, get JWT |
| GET | /api/auth/me | Get current user |
| GET | /api/subjects | List all subjects |
| POST | /api/subjects | Create subject |
| GET | /api/sessions | List user sessions |
| POST | /api/sessions | Create session |
| GET | /api/sessions/{id} | Get session with messages |
| POST | /api/chat | Send message, get AI response |
| GET | /api/mindmap/{subject_id} | Get mindmap nodes/edges |
| POST | /api/quiz/generate | Generate quiz |
| POST | /api/quiz/submit | Submit answers |
| GET | /api/progress/dashboard | Dashboard data |
| POST | /api/documents/upload | Upload PDF |
| GET | /api/export/{session_id}/pdf | Export PDF |
| GET | /api/export/{session_id}/pptx | Export PowerPoint |
| GET | /health | Health check |
| GET | /api/llm/status | LLM connection status |

---

## Troubleshooting

### "LLM connection failed"
1. Ensure llama-server is running: `curl http://127.0.0.1:8080/v1/models`
2. Check LLM_SERVER_URL in backend/.env

### "Module not found"
1. Activate venv: `venv\Scripts\activate`
2. Reinstall: `pip install -r requirements.txt`

### "401 Unauthorized"
1. JWT expired - login again
2. Check localStorage has token

### Database reset
```bash
del backend\smaranai.db
# Restart backend - tables auto-created
```

### Vector store reset
```bash
del backend\storage\vectors.pkl
# Re-upload PDFs
```
