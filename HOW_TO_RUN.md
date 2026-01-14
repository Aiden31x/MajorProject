# 🚀 ClauseCraft - How to Run

## Option 1: Quick Start (Recommended)

### Step 1: Setup Backend
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies (this may take 5-10 minutes)
pip install -r requirements.txt
```

### Step 2: Configure API Key
```bash
# Edit the .env file
nano .env
# OR use any text editor

# Add your Gemini API key:
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

Get your API key from: https://aistudio.google.com/app/apikey

### Step 3: Start Backend
```bash
# Make sure you're in backend directory with venv activated
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
🏢 ClauseCraft FastAPI Backend
📦 Initializing RAG system...
✅ RAG system initialized successfully!
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Start Frontend (New Terminal)
```bash
# Open a NEW terminal window
cd frontend

# Start the development server
npm run dev
```

You should see:
```
▲ Next.js 14.x.x
- Local:        http://localhost:3000
```

### Step 5: Access the App
- **ClauseCraft App**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Option 2: Using the Startup Script

After completing Step 1 and Step 2 above, you can use:

```bash
# From the project root directory
./run-all.sh
```

This will start both backend and frontend together!

---

## ⚡ Quick Commands Reference

### Backend Commands
```bash
# Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# View API docs
open http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health
```

### Frontend Commands
```bash
# Start frontend
cd frontend
npm run dev

# Build for production
npm run build
npm start
```

---

## 🔧 Troubleshooting

### Backend Issues

**"ModuleNotFoundError"**
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**"ChromaDB errors"**
- The `chroma_db` directory will be created automatically
- Make sure you have write permissions in the project directory

**"Model not found"**
- Check that `9epochs-90 (1)` directory exists in project root
- Update `MODEL_PATH` in `.env` if needed

**"API key error"**
- Make sure you added your Gemini API key to `backend/.env`
- The key should start with `AI...`

### Frontend Issues

**"Cannot connect to backend"**
- Make sure backend is running on port 8000
- Check `frontend/.env.local` has: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

**"npm run dev fails"**
- Try: `rm -rf .next` then `npm run dev` again
- Make sure Node.js 18+ is installed

---

## 📱 Using the App

### PDF Analysis
1. Go to http://localhost:3000
2. Drag and drop a PDF or click to browse
3. Enter your Gemini API key
4. Click "Analyze Lease Agreement"
5. View results in two columns

### Chat/RAG Queries
1. Click "Query Knowledge Base" button
2. Or navigate to http://localhost:3000/chat
3. Enter your Gemini API key
4. Type questions about your lease agreements
5. The AI will retrieve relevant clauses and answer

---

## 🛑 Stopping the App

### If using run-all.sh:
- Press `Ctrl+C` in the terminal

### If running separately:
- Press `Ctrl+C` in each terminal window (backend and frontend)

---

## 📊 Checking Everything Works

### Test Backend:
```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{"status":"healthy","service":"ClauseCraft API","kb_clauses":0}
```

### Test Frontend:
- Open http://localhost:3000
- You should see the ClauseCraft landing page

---

## 🎯 First Time Setup Checklist

- [ ] Backend venv created
- [ ] Backend dependencies installed
- [ ] Gemini API key added to backend/.env
- [ ] Backend starts without errors
- [ ] Frontend dependencies installed (already done)
- [ ] Frontend starts at localhost:3000
- [ ] Can upload PDF and analyze
- [ ] Chat interface loads

---

## 💡 Tips

- Keep backend running in one terminal, frontend in another
- Watch both terminal windows for errors
- The first analysis may take a bit longer as models load
- ChromaDB data persists between runs
- You can run the old Gradio app alongside this if needed

---

Need help? Check the full documentation in:
- `README.md` - Main project overview
- `backend/README.md` - Backend details
- `frontend/README.md` - Frontend details
- `MIGRATION_COMPLETE.md` - Implementation checklist
