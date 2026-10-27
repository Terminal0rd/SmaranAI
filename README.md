# SmaranAI - Adaptive Learning Platform

> **AI-Powered Tutor with MindMap-First Learning, Whiteboard Sessions, and Adaptive Quiz Engine**

![License](https://img.shields.io/badge/license-Educational-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **MindMap-First Learning** | Visualize concepts as interactive node graphs |
| 📝 **Whiteboard Sessions** | AI explains topics with structured, slide-based notes |
| 🎯 **Adaptive Quizzes** | Auto-generated from sessions, tracks weak topics |
| 📚 **RAG Knowledge Base** | Upload PDFs to enhance AI answers |
| 📊 **Progress Analytics** | Charts, scores, and learning insights |
| 📥 **Export PDF/PPT** | Download sessions as documents |

## ✨ Contributors

| Name | Github |
|---------|-------------|
| Ayush Hande | https://github.com/Terminal0rd |
| Suraj Raykar | https://github.com/ssuraj2504 |
| Himanshu Kapure | https://github.com/Himanshu25kapure |
| 📚 **RAG Knowledge Base** | Upload PDFs to enhance AI answers |
| 📊 **Progress Analytics** | Charts, scores, and learning insights |
| 📥 **Export PDF/PPT** | Download sessions as documents |

## 🛠️ Tech Stack

**Backend:** FastAPI, SQLAlchemy (async), JWT Auth, SentenceTransformers, Qwen 2.5 LLM via Ollama

**Frontend:** Next.js 14, TailwindCSS, Framer Motion, ReactFlow, Recharts

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama with Qwen 2.5 model

### 1. Start LLM Server
```bash
# Pull the model (one-time setup)
ollama pull qwen2.5:7b-instruct

# Start Ollama (it runs as a service, or use:)
ollama serve
ollama run phi3local
```

### 2. Start Backend
```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Start Frontend
```bash
cd frontend
npm install && npm run dev
```

**Visit:** http://localhost:3000

## 📖 Documentation

See [SETUP.md](./SETUP.md) for:
- Complete directory tree
- Detailed setup instructions
- Environment variables
- Testing checklist
- API reference
- Troubleshooting

## 📁 Project Structure

```
SmaranAI/
├── backend/           # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── models/    # 8 database models
│   │   ├── routes/    # 9 API routers
│   │   ├── services/  # 8 service modules
│   │   └── utils/     # Security, PDF, chunking
│   └── storage/       # Uploads + vector store
│
├── frontend/          # Next.js 14
│   └── src/
│       ├── app/       # 10 pages
│       ├── components/# UI components
│       └── lib/       # API client + stores
│
└── SETUP.md           # Full documentation
```

## 🔌 API Endpoints

| Category | Endpoints |
|----------|-----------|
| **Auth** | register, login, me, profile |
| **Subjects** | CRUD, recommendations |
| **Sessions** | Create, resume, messages |
| **Chat** | RAG-powered AI responses |
| **MindMap** | Nodes, edges, mastery |
| **Quiz** | Generate, submit, history |
| **Progress** | Dashboard, analytics |
| **Documents** | Upload PDF, status |
| **Export** | PDF, PowerPoint |

## 📝 License

Educational project - All rights reserved

---

Built with ❤️ using FastAPI + Next.js + Qwen 2.5 (Ollama)
