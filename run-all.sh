#!/bin/bash

echo "🚀 Starting ClauseCraft"
echo "======================="

# Check if virtual environment exists for backend
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend virtual environment not found."
    echo "Please run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend node_modules exist
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed."
    echo "Please run: cd frontend && npm install"
    exit 1
fi

# Start backend in background
echo "🔥 Starting FastAPI backend on port 8000..."
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "⚡ Starting Next.js frontend on port 3000..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ ClauseCraft is running!"
echo "========================="
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend API: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping ClauseCraft..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

trap cleanup INT TERM

# Wait for processes
wait
