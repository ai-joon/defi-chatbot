# DeFi Chatbot

A conversational interface for decentralized finance operations.

## Features
- [Briefly list main features]

## Prerequisites
- Python 3.8+
- pip package manager

## Project Structure
```
.
├── venv/               # Virtual environment (excluded from version control)
├── src/
│   └── main.py        # Main application entry point
├── requirements.txt   # Production dependencies (auto-generated)
├── requirements.dev.txt # Development dependencies (auto-generated)
└── ...                # Other project files
```

## Installation & Setup

### 1. Create Virtual Environment
Best practice: Use separate environments per project [4]
```shell
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 2. Install Dependency Management Tools
```shell
pip install pip-tools  # Enables precise dependency control [3]
```

### 3. Install Dependencies
First create/edit these files:
- `requirements.in` (main dependencies)
- `requirements.dev.in` (development dependencies)

Then compile and sync:
```shell
pip-compile requirements.in  # Generates requirements.txt
pip-compile requirements.dev.in  # Generates requirements.dev.txt
pip-sync requirements.txt requirements.dev.txt
```

## Development Tools
Consider including these common tools [3]:
```python
# requirements.dev.in
black      # Code formatting
ruff       # Linting
pytest     # Testing
python-dotenv  # Environment management
```

## Usage
```shell
python src/main.py
```
