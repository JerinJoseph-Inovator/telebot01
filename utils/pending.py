import os
import json
from pathlib import Path

# Get the correct base directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
PENDING_FILE = DATA_DIR / 'pending_deposits.json'

# Create data directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_pending():
    """Load pending deposits from JSON file"""
    try:
        if PENDING_FILE.exists():
            with open(PENDING_FILE, "r") as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_pending(pending):
    """Save pending deposits to JSON file"""
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2)