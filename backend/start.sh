#!/bin/bash

echo "🚀 Starting Risk Engine Backend..."
echo "📊 Python version: $(python --version)"
echo "📊 Current directory: $(pwd)"
echo "📊 Files in directory: $(ls -la)"

# Check if requirements are installed
echo "📦 Checking requirements..."
pip list

# Start the application
echo "🌐 Starting uvicorn server..."
uvicorn main:app --host 0.0.0.0 --port $PORT --log-level debug 