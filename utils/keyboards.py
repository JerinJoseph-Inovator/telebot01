def add_back_button(keyboard, back_to="main"):
    if back_to == "main":
        keyboard.append(["🔙 Back to Main Menu"])
    elif back_to == "gift_cards":
        keyboard.append(["🔙 Back to Gift Cards", "🔙 Back to Main Menu"])
    else:
        keyboard.append([f"🔙 Back"])
    return keyboard
