import telebot
import requests
import re
import random
import string
import json
import logging
from datetime import datetime, timedelta

# Replace with your actual Telegram Bot API token and the bot owner's user ID
api_token = '8036013708:AAG6r88dmDDqrevOi93VaHjvY-lTg2qbXvw'
bot_owner_id = 7202072688  # Replace with the bot owner's Telegram user ID
bot = telebot.TeleBot(api_token)

# Initialize logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load persistent data from JSON file
def load_data():
    try:
        with open("bot_data.json", "r") as f:
            data = json.load(f)
            return data.get("registered_users", set()), data.get("premium_users", set()), data.get("redeem_codes", {})
    except FileNotFoundError:
        return set(), set(), {}

# Save data to JSON file
def save_data():
    with open("bot_data.json", "w") as f:
        json.dump({
            "registered_users": list(registered_users),
            "premium_users": list(premium_users),
            "redeem_codes": redeem_codes
        }, f)

# Initialize data
registered_users, premium_users, redeem_codes = load_data()

# Function to validate URL format
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  
        r'localhost|'  
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  
        r'(?::\d+)?'  
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# /start command with registration prompt
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    if user_id in registered_users:
        bot.send_message(message.chat.id, "メ Welcome back! You are already registered. Send a URL to analyze.")
    else:
        bot.send_message(
            message.chat.id,
            f"メ Welcome To Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ, {message.from_user.first_name}! 👋\n\n"
            "Please register to start using the bot by sending /register.\n"
            "For premium features, use a redeem code if you have one with /redeem <code>.\n"
            "Type /help for more information on available commands."
        )

# /register command for users
@bot.message_handler(commands=['register'])
def cmd_register(message):
    user_id = message.from_user.id
    if user_id not in registered_users:
        registered_users.add(user_id)
        save_data()  # Save registration to persistent storage
        bot.send_message(message.chat.id, "♁ Registration successful! You can now send a URL to analyze.")
    else:
        bot.send_message(message.chat.id, "You are already registered! Send a URL to analyze.")

# /redeem command for redeeming premium codes
@bot.message_handler(commands=['redeem'])
def cmd_redeem(message):
    user_id = message.from_user.id
    if user_id in premium_users:
        bot.send_message(message.chat.id, "You already have premium access!")
        return
    
    try:
        code = message.text.split()[1]
        if code in redeem_codes:
            redeem_info = redeem_codes[code]
            if redeem_info['expiry'] < datetime.now():
                bot.send_message(message.chat.id, "This redeem code has expired.")
                del redeem_codes[code]
                save_data()
            elif redeem_info['uses'] > 0:
                redeem_info['uses'] -= 1
                premium_users.add(user_id)
                save_data()
                bot.send_message(message.chat.id, "♁ Redeem successful! You now have premium access.")
                if redeem_info['uses'] == 0:
                    del redeem_codes[code]
                    save_data()
            else:
                bot.send_message(message.chat.id, "This redeem code has no remaining uses.")
        else:
            bot.send_message(message.chat.id, "Invalid redeem code.")
    except IndexError:
        bot.send_message(message.chat.id, "Please provide a redeem code. Usage: /redeem <code>")

# /generate_redeem_code command for bot owner
@bot.message_handler(commands=['generate_redeem_code'])
def cmd_generate_redeem_code(message):
    if message.from_user.id != bot_owner_id:
        bot.send_message(message.chat.id, "You are not authorized to generate redeem codes.")
        return
    
    try:
        _, uses, expiry_hours = message.text.split()
        uses = int(uses)
        expiry_hours = int(expiry_hours)
        code = f"OVERSTRIPE-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        expiry_time = datetime.now() + timedelta(hours=expiry_hours)

        redeem_codes[code] = {'uses': uses, 'expiry': expiry_time}
        save_data()  # Save new code to persistent storage
        bot.send_message(
            message.chat.id, 
            f"♁ Redeem Code Generated: {code}\n"
            f"Valid for: {uses} use(s)\n"
            f"Expires in: {expiry_hours} hour(s)"
        )
    except ValueError:
        bot.send_message(message.chat.id, "Invalid format. Usage: /generate_redeem_code <uses> <expiry in hours>")

# /help command for listing available commands
@bot.message_handler(commands=['help'])
def cmd_help(message):
    if message.from_user.id == bot_owner_id:
        help_message = (
            "メ **OverStripe Bot Help for Owner** メ\n\n"
            "♁ **/start** - Start the bot and receive a welcome message.\n"
            "♁ **/register** - Register yourself to use the bot’s basic features.\n"
            "♁ **/redeem <code>** - Redeem a premium code for advanced features.\n"
            "♁ **/generate_redeem_code <uses> <expiry in hours>** - Generate a redeem code with a set number of uses and expiration time.\n\n"
            "For any questions or issues, please check the logs or contact support."
        )
    else:
        help_message = (
            "メ **OverStripe Bot Help** メ\n\n"
            "♁ **/start** - Start the bot and receive a welcome message.\n"
            "♁ **/register** - Register yourself to use the bot’s basic features.\n"
            "♁ **/redeem <code>** - Redeem a premium code for advanced features.\n\n"
            "To analyze a URL, send the URL directly after registration.\n\n"
            "For any questions, contact support!"
        )
    bot.send_message(message.chat.id, help_message, parse_mode="Markdown")

# Handle text input for URL analysis
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    if user_id not in registered_users:
        bot.send_message(message.chat.id, "Please register first by sending /register.")
        return

    if user_id in premium_users:
        bot.send_message(message.chat.id, "♁ Premium analysis activated for this URL.")
    
    url = message.text.strip()
    if not is_valid_url(url):
        bot.send_message(message.chat.id, "Please provide a valid URL.")
        return
    
    # Call `check_url` function here to analyze the URL...

    # Example response after checking the URL
    detected_gateways, status_code, captcha, cloudflare, payment_security_type, cvv_cvc_status, inbuilt_status = check_url(url)

    gateways_str = ', '.join(detected_gateways) if detected_gateways else "None"
    response_message = (
        f"♁ Gateways Fetched Successfully ✅\n"
        f"━━━━━━━━━━━━━━\n"
        f"♁ URL: {url}\n"
        f"♁ Payment Gateways: {gateways_str}\n"
        f"♁ Captcha Detected: {captcha}\n"
        f"♁ Cloudflare Detected: {cloudflare}\n"
        f"♁ Payment Security Type: {payment_security_type}\n"
        f"♁ CVV/CVC Requirement: {cvv_cvc_status}\n"
        f"♁ Inbuilt Payment System: {inbuilt_status}\n"
        f"♁ Status Code: {status_code}\n"
        f"Bot by: Random"
    )
    
    bot.send_message(message.chat.id, response_message)

bot.polling()
