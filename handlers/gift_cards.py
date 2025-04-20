# handlers/gift_cards.py
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.json_manager import load_data
from utils.keyboards import add_back_button
from utils.user_manager import deduct_balance
from config import ADMIN_ID
import logging


async def gift_cards_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available gift card brands"""
    data = load_data()
    keyboard = [[brand] for brand in data["gift_cards"].keys()]
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a Gift Card brand:", reply_markup=reply_markup)

async def gift_card_offer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show gift card options and handle selection"""
    selected = update.message.text
    data = load_data()
    offers = data["gift_cards"].get(selected, [])
    
    if not offers:
        await update.message.reply_text("No offers found. Please try again.")
        return
    
    # Store brand in context for purchase handling
    context.user_data['selected_brand'] = selected
    
    keyboard = [[offer] for offer in offers]
    keyboard = add_back_button(keyboard, back_to="gift_cards")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"{selected} Offers:", reply_markup=reply_markup)

async def handle_gift_card_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process gift card purchase and deduct balance"""
    try:
        user_id = update.effective_user.id
        offer_text = update.message.text
        brand = context.user_data.get('selected_brand')
        
        if not brand:
            await update.message.reply_text("Please select a brand first.")
            return
        
        # Parse the amount from offer text (e.g., "$50 for $25")
        try:
            parts = offer_text.split(' for $')
            card_value = float(parts[0].replace('$', ''))
            price = float(parts[1])
        except (IndexError, ValueError):
            await update.message.reply_text("Invalid offer format. Please try again.")
            return
        
        # Deduct from user balance
        success = deduct_balance(
            user_id=user_id,
            amount=price,
            service="gift_card",
            brand=brand,
            card_value=card_value
        )
        
        if success:
            # Notify user
            await update.message.reply_text(
                f"✅ Order confirmed! Your {brand} gift card for ${card_value} "
                f"will be delivered within 24 hours.\n\n"
                f"💳 ${price} has been deducted from your balance."
            )
            
            # Notify admin
            user = update.effective_user
            admin_message = (
                f"🎁 New Gift Card Purchase\n\n"
                f"👤 User: @{user.username or user.full_name} (ID: {user_id})\n"
                f"🛒 Item: {brand} ${card_value} Gift Card\n"
                f"💰 Price: ${price}\n"
                f"📝 Please deliver within 24 hours"
            )
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message
            )
        else:
            await update.message.reply_text(
                "❌ Insufficient balance for this purchase. "
                "Please top up your account."
            )
            
    except Exception as e:
        logging.error(f"Gift card purchase error: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ An error occurred during purchase. Please try again."
        )