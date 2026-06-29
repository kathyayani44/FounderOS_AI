# FounderOS AI

FounderOS AI is an AI-powered fundraising assistant that helps founders discover investors, manage meetings, store memories, and receive intelligent recommendations.

## Project Structure

```
FounderOS_ai/
│
├── backend/
│   ├── api/
│   ├── database/
│   ├── models/
│   ├── services/
│   ├── tools/
│   ├── requirements.txt
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
└── README.md
```

---

# Prerequisites

Install the following software before starting.

- Python 3.12+
- Node.js 22 LTS (Recommended)
- npm
- Git

Verify installation

```bash
python --version
node -v
npm -v
git --version
```

---

# Clone Repository

```bash
git clone <repository-url>
cd FounderOS_ai
```

---

# Backend Setup

## Step 1: Go to backend

```bash
cd backend
```

## Step 2: Create virtual environment (Recommended)

Windows

```bash
python -m venv venv
```

Activate

Command Prompt

```bash
venv\Scripts\activate
```

PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

---

## Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

If pip is outdated

```bash
python -m pip install --upgrade pip
```

---

## Step 4: Configure Environment Variables

Create a `.env` file inside the backend folder.

Example

```env
DATABASE_URL=
SUPABASE_URL=
SUPABASE_KEY=
QDRANT_URL=
QDRANT_API_KEY=
GOOGLE_API_KEY=
OPENAI_API_KEY=
```

Fill these values with your credentials.

---

## Step 5: Start Backend

Return to project root

```bash
cd ..
```

Run

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Backend will be available at

```
http://127.0.0.1:8000
```

Swagger Documentation

```
http://127.0.0.1:8000/docs
```

---

# Frontend Setup

Open another terminal.

Go to frontend

```bash
cd frontend
```

Install packages

```bash
npm install
```

Create a `.env.local`

Example

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Run frontend

```bash
npm run dev
```

Frontend will be available at

```
http://localhost:3000
```

---

# Running the Application

Terminal 1

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Terminal 2

```bash
cd frontend
npm run dev
```

Open

```
http://localhost:3000
```

---

# API Documentation

Swagger UI

```
http://127.0.0.1:8000/docs
```

OpenAPI JSON

```
http://127.0.0.1:8000/openapi.json
```

---

# Common Issues

## ModuleNotFoundError: No module named 'backend'

Run Uvicorn from the project root instead of the backend folder.

Correct

```bash
cd FounderOS_ai
python -m uvicorn backend.main:app --reload --port 8000
```

---

# Tech Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Axios

## Backend

- FastAPI
- SQLAlchemy
- Supabase PostgreSQL
- Qdrant Vector Database
- Sentence Transformers
- Google Gemini
- Uvicorn

---

# Development Workflow

1. Pull latest changes

```bash
git pull
```

2. Start backend

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

3. Start frontend

```bash
cd frontend
npm run dev
```

4. Open

```
http://localhost:3000
```

---

