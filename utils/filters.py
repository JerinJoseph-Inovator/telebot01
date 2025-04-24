# utils/filters.py
from telegram.ext import filters
from typing import Any
from telegram import Message
from utils.json_manager import load_stock

class InStockBrandFilter(filters.Filter):
    """
    Generic filter for checking message.text against a category in stock.json.
    Category should be one of "gift_cards" or "streaming_services".
    """
    def __init__(self, category: str):
        self.category = category

    def filter(self, message: Message) -> bool:
        text = message.text or ""
        stock = load_stock().get(self.category, {})
        return text in stock

# instantiate them for easy import
gift_brand_filter = InStockBrandFilter("gift_cards")
stream_brand_filter = InStockBrandFilter("streaming_services")
