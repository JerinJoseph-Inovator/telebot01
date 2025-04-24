# handlers/gift_cards.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.json_manager import load_stock
from utils.keyboards import add_back_button
from utils.user_manager import deduct_balance
from config import ADMIN_ID
import logging


async def gift_cards_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available gift card brands"""
    stock = load_stock()
    brands = list(stock.get("gift_cards", {}).keys())
    keyboard = [[brand] for brand in brands]
    keyboard = add_back_button(keyboard, back_to="main")
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a Gift Card brand:", reply_markup=reply_markup)

async def gift_card_offer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show in-stock gift card offers for selected brand"""
    selected = update.message.text
    stock = load_stock()
    offers_dict = stock.get("gift_cards", {}).get(selected, {})
    
    # Only show offers that are in stock
    offers = [offer for offer, available in offers_dict.items() if available]

    if not offers:
        await update.message.reply_text("❌ No available stock. Please check later.")
        return

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

        # Parse "$50 for $25" → card_value=50, price=25
        try:
            parts = offer_text.split(' for $')
            card_value = float(parts[0].replace('$', ''))
            price = float(parts[1])
        except (IndexError, ValueError):
            await update.message.reply_text("Invalid format. Please choose a valid offer.")
            return

        success = deduct_balance(
            user_id=user_id,
            amount=price,
            service="gift_card",
            brand=brand,
            card_value=card_value
        )

        if success:
            await update.message.reply_text(
                f"✅ Order confirmed! Your {brand} gift card for ${card_value} "
                f"will be delivered within 24 hours.\n\n"
                f"💳 ${price} has been deducted from your balance."
            )

            admin_msg = (
                f"🎁 New Gift Card Purchase\n\n"
                f"👤 User: @{update.effective_user.username or update.effective_user.full_name}\n"
                f"🛒 {brand} ${card_value} Gift Card\n"
                f"💰 Price: ${price}\n"
                f"📝 Deliver within 24 hours"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
        else:
            await update.message.reply_text(
                "❌ Insufficient balance. Please top up your account."
            )

    except Exception as e:
        logging.error(f"Gift card purchase error: {e}", exc_info=True)
        await update.message.reply_text("⚠️ An error occurred during purchase. Try again.")
