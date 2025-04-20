# utils/keyboards.py
def add_back_button(keyboard, back_to="main"):
    """Add properly formatted back button based on destination"""
    back_buttons = {
        "main": ["🔙 Back to Main Menu"],
        "gift_cards": ["🔙 Back to Gift Cards"],
        "streaming_services": ["🔙 Back to Streaming Services"]
    }
    keyboard.append(back_buttons.get(back_to, ["🔙 Back"]))
    return keyboard