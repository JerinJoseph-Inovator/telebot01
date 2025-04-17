import json, os

USER_DIR = os.path.join(os.path.dirname(__file__), "..", "user")
TRANSACTION_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "transactions")

os.makedirs(USER_DIR, exist_ok=True)
os.makedirs(TRANSACTION_LOG_DIR, exist_ok=True)

def get_user_path(user_id):
    return os.path.join(USER_DIR, f"{user_id}.json")

def load_user(user_id):
    path = get_user_path(user_id)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"balance": 0.0, "transactions": []}

def save_user(user_id, data):
    path = get_user_path(user_id)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def log_transaction(txid, data):
    with open(os.path.join(TRANSACTION_LOG_DIR, f"{txid}.json"), "w") as f:
        json.dump(data, f, indent=2)
