# 🧠 Domain Knowledge Co-Pilot

A production-ready RAG (Retrieval-Augmented Generation) application that lets you upload your own documents and ask natural-language questions about them. Every answer includes citations pointing back to the exact source passage.

---

## Project Overview

Knowledge Co-Pilot allows users to:
- Create isolated **corpora** (knowledge bases) — e.g. "Client A", "Thesis", "Personal Research"
- Upload **PDF, DOCX, TXT, and Markdown** files into any corpus
- Ask questions in natural language and receive **grounded answers with citations**
- Click any citation to view the original source passage in a modal
- Maintain **per-corpus conversation history** resumable across sessions

---

## Folder Structure

```
knowledge-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── database.py        # SQLite connection + table initialization
│   │   ├── auth.py            # JWT + bcrypt authentication utilities
│   │   ├── models.py          # Row-to-dict helpers
│   │   ├── schemas.py         # Pydantic request/response schemas
│   │   ├── routes/
│   │   │   ├── auth.py        # POST /signup, POST /login
│   │   │   ├── corpora.py     # POST /corpora, GET /corpora, DELETE /corpora/{id}
│   │   │   ├── upload.py      # POST /corpora/{id}/upload
│   │   │   └── query.py       # POST /corpora/{id}/query, GET/DELETE history
│   │   ├── rag/
│   │   │   ├── parser.py      # PDF / DOCX / TXT / MD parsers
│   │   │   ├── chunker.py     # Sliding-window text chunker with overlap
│   │   │   ├── embeddings.py  # OpenAI text-embedding-3-small
│   │   │   ├── chroma.py      # ChromaDB collection management + retrieval
│   │   │   └── generator.py   # OpenAI chat completion + citation extraction
│   │   └── utils/
│   ├── uploads/               # Stored original files (user/corpus sub-dirs)
│   ├── chroma_db/             # Persistent ChromaDB vector store
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── login.html
│   ├── signup.html
│   ├── corpus.html            # Corpus selection + management
│   ├── upload.html            # Document upload with drag-and-drop
│   ├── chat.html              # Chat interface with citations
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── api.js             # Fetch API client for all backend calls
│       └── utils.js           # Shared UI utility functions
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.12+
- Node.js (only needed for the setup guide DOCX generation, not the app itself)
- A modern web browser
- An OpenAI API key

---

### 1. Clone / Download the Project

```bash
# If using git
git clone <your-repo-url>
cd knowledge-copilot
```

---

### 2. Create a Virtual Environment

```bash
cd backend
python -m venv venv
```

Activate it:

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Create the `.env` File

```bash
cp .env.example .env
```

Open `.env` and set your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

All other defaults are ready to use for local development.

---

### 5. Run FastAPI

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive API docs: `http://localhost:8000/docs`

---

### 6. Serve the Frontend

The frontend is pure HTML/CSS/JS — no build step required.

**Option A — Python simple server (recommended for local dev):**

```bash
cd frontend
python -m http.server 3000
```

Open `http://localhost:3000/login.html` in your browser.

**Option B — Any static file server:**

```bash
# Using npx serve
cd frontend
npx serve -p 3000
```

---

## Usage

### Signing Up

1. Open `http://localhost:3000/signup.html`
2. Enter your email and a password (minimum 8 characters)
3. You will be redirected to the corpus selection page

### Creating a Corpus

1. Click **"+ New Corpus"** or the dashed card
2. Enter a name (e.g. "My Research", "Client A", "Thesis")
3. Optionally add a description
4. Click **Create Corpus**

### Uploading Documents

1. Select a corpus from the corpus page to set it as active
2. Navigate to **Upload Documents** (sidebar or button)
3. Drag and drop files or click to browse
4. Supported formats: **PDF, DOCX, TXT, Markdown**
5. Click **Upload All** — files are parsed, chunked, embedded, and indexed automatically

### Asking Questions

1. Navigate to **Chat** from the sidebar
2. Type your question in the input box
3. Press **Enter** to send (Shift+Enter for a new line)
4. The answer appears with numbered **citation tags** below it
5. Click any citation tag to open a modal showing the exact source passage

### Understanding Citations

Each citation shows:
- **Source filename** — which document the passage came from
- **Page number** — when available (PDFs with page structure)
- **Chunk text** — the exact passage used to generate the answer

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/signup` | No | Register new user |
| POST | `/api/login` | No | Authenticate user |
| POST | `/api/corpora` | Yes | Create corpus |
| GET | `/api/corpora` | Yes | List user's corpora |
| DELETE | `/api/corpora/{id}` | Yes | Delete corpus |
| POST | `/api/corpora/{id}/upload` | Yes | Upload document |
| POST | `/api/corpora/{id}/query` | Yes | Ask a question |
| GET | `/api/corpora/{id}/history` | Yes | Get chat history |
| DELETE | `/api/corpora/{id}/history` | Yes | Clear chat history |

Full interactive documentation available at `http://localhost:8000/docs` when the server is running.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | **Required.** Your OpenAI API key |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat completion model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `MAX_TOKENS` | `1500` | Max tokens for chat response |
| `JWT_SECRET_KEY` | (change this) | Secret for signing JWTs |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime (24 hours) |
| `DATABASE_URL` | `sqlite:///./knowledge_copilot.db` | SQLite path |
| `CHROMA_DB_PATH` | `chroma_db` | ChromaDB persistence directory |
| `UPLOADS_DIR` | `uploads` | Uploaded files directory |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload file size |
| `CHUNK_SIZE` | `800` | Characters per text chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between adjacent chunks |
| `TOP_K_RESULTS` | `5` | Number of chunks retrieved per query |

---

## Troubleshooting

### `OPENAI_API_KEY` not set
Ensure your `.env` file exists in the `backend/` directory and contains your real API key. The server reads it at startup.

### CORS errors in browser
Make sure FastAPI is running on port 8000 and the frontend is served from a different port (e.g. 3000). The backend allows all origins by default.

### `ModuleNotFoundError`
Ensure your virtual environment is activated before running `uvicorn`. Re-run `pip install -r requirements.txt` inside the activated venv.

### ChromaDB collection errors
If the `chroma_db/` directory becomes corrupted, delete it and restart the server. Re-upload your documents.

### PDF parsing returns no text
Some PDFs are scanned images. The app requires text-based PDFs. Try converting with an OCR tool first.

### Upload returns 422
The file type is not supported, or the file is empty. Check the extension is `.pdf`, `.docx`, `.txt`, or `.md`.

### "No relevant content found"
The corpus has no documents, or the uploaded documents contain no extractable text. Upload documents first, then query.

---

## Architecture Notes

- **One ChromaDB collection per corpus** — complete data isolation between corpora
- **Embeddings:** `text-embedding-3-small` via OpenAI API (1536-dimensional vectors)
- **Chunking:** Character-based sliding window (800 chars, 150 overlap) with boundary detection
- **Retrieval:** Cosine similarity top-5 from ChromaDB
- **Generation:** `gpt-4o-mini` with last 5 conversation turns in context
- **Storage:** SQLite for users/corpora/documents/messages, ChromaDB for vectors, disk for original files
