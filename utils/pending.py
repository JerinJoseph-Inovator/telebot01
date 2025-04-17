import json
import os

PENDING_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "pending_deposits.json")

def load_pending():
    if not os.path.exists(PENDING_FILE):
        return []
    with open(PENDING_FILE, "r") as f:
        return json.load(f)

def save_pending(data):
    with open(PENDING_FILE, "w") as f:
        json.dump(data, f, indent=2)
