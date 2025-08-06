#!/bin/bash

# Start the Python backend
echo "Starting Python backend..."
cd backend
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start the React frontend
echo "Starting React frontend..."
cd ..
npm run dev &
FRONTEND_PID=$!

echo "Both servers are starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait 