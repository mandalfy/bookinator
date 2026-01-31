#!/bin/bash

# Bookinator v2 Run Script
# -------------------------

VENV_DIR="venv"

# Find Python
find_python() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo "none"
    fi
}

PYTHON_CMD=$(find_python)

if [ "$PYTHON_CMD" == "none" ]; then
    echo "❌ Error: Python 3 not found. Please install Python."
    exit 1
fi

echo "ℹ️  Using Python: $PYTHON_CMD"

# Create venv if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR
    if [ ! -d "$VENV_DIR" ]; then
         echo "❌ Failed to create venv."
         exit 1 
    fi
fi

# Activate venv
echo "🔓 Activating virtual environment..."
if [ -f "$VENV_DIR/Scripts/activate" ]; then
    source $VENV_DIR/Scripts/activate
elif [ -f "$VENV_DIR/bin/activate" ]; then
    source $VENV_DIR/bin/activate
else
    echo "⚠️  Could not find activate script. Trying global python..."
fi

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies from requirements.txt..."
    pip install --quiet -r requirements.txt
else
    echo "⚠️ requirements.txt not found! Installing manually..."
    pip install --quiet flask requests ddgs
fi

# Run the app
echo ""
echo "🚀 Starting Bookinator v2..."
echo "   Open: http://127.0.0.1:5000"
echo ""
python app.py
