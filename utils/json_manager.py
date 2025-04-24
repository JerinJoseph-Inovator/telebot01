# utils/json_manager.py
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "..", "data.json")
STOCK_FILE = os.path.join(BASE_DIR, "..", "data", "stock.json")

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_stock():
    with open(STOCK_FILE, "r") as f:
        return json.load(f)

def save_stock(stock_data):
    with open(STOCK_FILE, "w") as f:
        json.dump(stock_data, f, indent=2)
