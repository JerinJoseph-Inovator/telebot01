import json
import os
from datetime import datetime
from pathlib import Path
import logging

# Configure paths using pathlib for better cross-platform compatibility
BASE_DIR = Path(__file__).resolve().parent.parent
USER_DIR = BASE_DIR / "user"
TRANSACTION_LOG_DIR = BASE_DIR / "transactions"

# Create directories if they don't exist
USER_DIR.mkdir(parents=True, exist_ok=True)
TRANSACTION_LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_user_path(user_id: int) -> Path:
    """Get path to user's JSON file"""
    return USER_DIR / f"{user_id}.json"

def load_user(user_id: int) -> dict:
    """Load user data from JSON file"""
    path = get_user_path(user_id)
    try:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return {"balance": 0.0, "transactions": []}
    except Exception as e:
        logging.error(f"Error loading user {user_id}: {e}")
        return {"balance": 0.0, "transactions": []}

def save_user(user_id: int, data: dict):
    """Save user data to JSON file"""
    path = get_user_path(user_id)
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving user {user_id}: {e}")

def log_transaction(txid: str, data: dict):
    """Log transaction details to separate file"""
    try:
        path = TRANSACTION_LOG_DIR / f"{txid}.json"
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Error logging transaction {txid}: {e}")

def add_deposit(user_id: int, amount: float, txid: str, service: str = "top_up") -> dict:
    """
    Add deposit to user's balance and record transaction
    Args:
        user_id: Telegram user ID
        amount: Deposit amount
        txid: Transaction ID
        service: Service type (top_up, gift_card, etc.)
    Returns:
        Updated user data
    """
    try:
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        user = load_user(user_id)
        user['balance'] = user.get('balance', 0.0) + amount
        
        transaction = {
            'txid': txid,
            'amount': amount,
            'service': service,
            'status': 'approved',
            'timestamp': datetime.now().isoformat()
        }
        
        user.setdefault('transactions', []).append(transaction)
        save_user(user_id, user)
        log_transaction(txid, transaction)
        
        return user
        
    except ValueError as e:
        logging.error(f"Invalid deposit amount: {e}")
        raise
    except Exception as e:
        logging.error(f"Error adding deposit: {e}")
        raise

def deduct_balance(user_id: int, amount: float, service: str, **kwargs) -> bool:
    """
    Deduct from user's balance for purchases
    Args:
        user_id: Telegram user ID
        amount: Amount to deduct
        service: Service type (gift_card, streaming, etc.)
        **kwargs: Additional transaction details
    Returns:
        bool: True if deduction was successful
    """
    try:
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        user = load_user(user_id)
        if user.get('balance', 0) < amount:
            return False
            
        user['balance'] -= amount
        
        transaction = {
            'amount': -amount,
            'service': service,
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        user.setdefault('transactions', []).append(transaction)
        save_user(user_id, user)
        log_transaction(f"{service}_{datetime.now().timestamp()}", transaction)
        
        return True
        
    except Exception as e:
        logging.error(f"Error deducting balance: {e}")
        return False

def get_user_balance(user_id: int) -> float:
    """Get current user balance"""
    return load_user(user_id).get('balance', 0.0)

def get_transaction_history(user_id: int, limit: int = 10) -> list:
    """Get user's transaction history"""
    user = load_user(user_id)
    return user.get('transactions', [])[-limit:]