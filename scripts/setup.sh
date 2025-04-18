#!/bin/bash

echo "Setting up Project Management System..."

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check OS and install system dependencies first (before pip requirements)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Installing macOS system dependencies..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew first:"
        echo "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install system dependencies
    brew install portaudio
    brew install ffmpeg
    brew install libsndfile
    brew install postgresql@14
    
    # Special handling for Python 3.13
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ "$PYTHON_VERSION" == "3.13" ]]; then
        echo "Detected Python 3.13 - Installing dependencies with special handling..."
        pip install --upgrade pip setuptools wheel

        # Install base requirements first
        pip install Django==4.2.11
        pip install djangorestframework==3.16.0
        pip install djangorestframework-simplejwt==5.3.1
        
        # Install PostgreSQL dependencies
        export LDFLAGS="-L$(brew --prefix postgresql@14)/lib"
        export CPPFLAGS="-I$(brew --prefix postgresql@14)/include"
        pip install "psycopg[binary]>=3.2.6"
        
        pip install django-cors-headers==4.7.0
        pip install django-filter==24.1
        
        # Install audio dependencies
        export LDFLAGS="-L$(brew --prefix portaudio)/lib"
        export CPPFLAGS="-I$(brew --prefix portaudio)/include"
        pip install --no-binary :all: pyaudioop
        pip install --no-binary :all: audioop
        
        # Now install the rest of the requirements
        pip install -r requirements.txt
        
        echo "Dependencies installation completed for Python 3.13"
    else
        # Install pip requirements normally for other Python versions
        pip install -r requirements.txt
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Installing Linux system dependencies..."
    sudo apt-get update
    sudo apt-get install -y python3-dev portaudio19-dev python3-pyaudio ffmpeg libsndfile1 postgresql postgresql-contrib libpq-dev
    pip install -r requirements.txt
fi

echo "Setup complete! You can now run the development server." 