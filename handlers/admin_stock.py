# handlers/admin_stock.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from utils.json_manager import load_stock, save_stock
import re

# === Helpers ===
def escape_markdown(text):
    return re.sub(r'([_\*\[\]()~`>#+=|{}.!\\-])', r'\\\1', text)


def build_main_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Gift Card", callback_data="admin:add_gift_card")],
        [InlineKeyboardButton("➕ Add Streaming Service", callback_data="admin:add_streaming")],
        [InlineKeyboardButton("📦 Manage Stock", callback_data="admin:manage_stock")],
        [InlineKeyboardButton("📥 View Pending TXs", callback_data="admin:pending_txs")],
        [InlineKeyboardButton("📨 Pending Deliveries", callback_data="admin:pending_delivery")],
    ])


def build_stock_toggle_keyboard(category, brand):
    stock = load_stock()
    items = stock.get(category, {}).get(brand, {})
    keyboard = []
    for item, available in items.items():
        toggle_text = "✅" if available else "❌"
        callback_data = f"admin:toggle:{category}:{brand}:{item}"
        escaped_item = escape_markdown(item)
        keyboard.append([InlineKeyboardButton(f"{toggle_text} {escaped_item}", callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin:manage_stock")])
    return InlineKeyboardMarkup(keyboard)


# === Entry Point ===
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to access this panel.")
        return

    await update.message.reply_text("⚙️ Admin Panel:", reply_markup=build_main_admin_keyboard())


# === Callback Handler ===
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin:add_gift_card":
        context.user_data["admin_state"] = "add_gift_card"
        await query.edit_message_text("✏️ Send the gift card brand name:")

    elif data == "admin:add_streaming":
        context.user_data["admin_state"] = "add_streaming"
        await query.edit_message_text("✏️ Send the streaming service name:")

    elif data == "admin:manage_stock":
        stock = load_stock()
        keyboard = []
        for category in stock:
            for brand in stock[category]:
                callback_data = f"admin:brand:{category}:{brand}"
                escaped_label = escape_markdown(f"{brand} ({category})")
                keyboard.append([InlineKeyboardButton(escaped_label, callback_data=callback_data)])
        await query.edit_message_text(
            "📦 Select brand to manage:",
            parse_mode='MarkdownV2',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("admin:brand:"):
        _, _, category, brand = data.split(":", 3)
        escaped_brand = escape_markdown(brand)
        escaped_category = escape_markdown(category)
        await query.edit_message_text(
            f"🛠 Managing *{escaped_brand}* \\({escaped_category}\\)",
            parse_mode='MarkdownV2',
            reply_markup=build_stock_toggle_keyboard(category, brand)
        )

    elif data.startswith("admin:toggle:"):
        _, _, category, brand, offer = data.split(":", 4)
        stock = load_stock()
        current = stock[category][brand].get(offer)
        if current is not None:
            stock[category][brand][offer] = not current
            save_stock(stock)
            await query.edit_message_reply_markup(reply_markup=build_stock_toggle_keyboard(category, brand))

    elif data == "admin:pending_txs":
        await query.edit_message_text("📥 This would show pending TXs (free feature).")

    elif data == "admin:pending_delivery":
        await query.edit_message_text("📨 This would show pending deliveries (free feature).")


# === Stock Input Handler ===
async def handle_admin_stock_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    state = context.user_data.get("admin_state")
    if not state:
        return

    stock = load_stock()
    text = update.message.text.strip()

    # Step 1: Add or select gift card brand
    if state == "add_gift_card":
        exists = text in stock.get("gift_cards", {})
        if not exists:
            stock.setdefault("gift_cards", {})[text] = {}
            save_stock(stock)
            await update.message.reply_text(
                f"✅ Gift card brand '{text}' added.\n"
                f"Please send gift card offers for '{text}', one per line, in format:\n"
                f"$50 for $25,true\n$100 for $50,false"
            )
        else:
            await update.message.reply_text(
                f"🔄 Brand '{text}' already exists.\n"
                f"Now send new offers to append to '{text}', one per line, in format:\n"
                f"$75 for $37,true"
            )
        context.user_data["admin_state"] = f"add_gift_card_offers:{text}"
        return

    # Step 2: Handle gift card offers input
    if state.startswith("add_gift_card_offers:"):
        brand = state.split(":", 1)[1]
        lines = [l for l in text.splitlines() if "," in l]
        added = []
        for line in lines:
            try:
                offer_text, avail = line.split(",", 1)
                avail_bool = avail.strip().lower() == "true"
                stock.setdefault("gift_cards", {}).setdefault(brand, {})[offer_text.strip()] = avail_bool
                added.append(offer_text.strip())
            except:
                continue
        save_stock(stock)
        context.user_data["admin_state"] = None
        await update.message.reply_text(
            f"✅ Added offers to '{brand}': {', '.join(added)}"
        )
        return

    # Step 3: Add or select streaming service
    if state == "add_streaming":
        exists = text in stock.get("streaming_services", {})
        if not exists:
            stock.setdefault("streaming_services", {})[text] = {}
            save_stock(stock)
            await update.message.reply_text(
                f"✅ Streaming service '{text}' added.\n"
                f"Please send streaming plans for '{text}', one per line, in format:\n"
                f"1 Month - $5,true\n3 Months - $12,false"
            )
        else:
            await update.message.reply_text(
                f"🔄 Service '{text}' already exists.\n"
                f"Now send new plans to append to '{text}', one per line, in format:\n"
                f"6 Months - $25,true"
            )
        context.user_data["admin_state"] = f"add_streaming_offers:{text}"
        return

    # Step 4: Handle streaming plans input
    if state.startswith("add_streaming_offers:"):
        service = state.split(":", 1)[1]
        lines = [l for l in text.splitlines() if "," in l]
        added = []
        for line in lines:
            try:
                plan_text, avail = line.split(",", 1)
                avail_bool = avail.strip().lower() == "true"
                stock.setdefault("streaming_services", {}).setdefault(service, {})[plan_text.strip()] = avail_bool
                added.append(plan_text.strip())
            except:
                continue
        save_stock(stock)
        context.user_data["admin_state"] = None
        await update.message.reply_text(
            f"✅ Added plans to '{service}': {', '.join(added)}"
        )
        return
