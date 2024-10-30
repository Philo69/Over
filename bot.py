import telebot
import requests
import re
import random
import string
import json
import logging
import time
from datetime import datetime, timedelta

# Replace with your actual Telegram Bot API token and the bot owner's user ID
api_token = '8036013708:AAHeC-NzIZUDUi7cJ2cI4FMaK9zHhJsjWI0'
bot_owner_id = 7202072688  # Bot owner's Telegram user ID
bot = telebot.TeleBot(api_token)

# Initialize logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load persistent data from JSON file
def load_data():
    try:
        with open("bot_data.json", "r") as f:
            data = json.load(f)
            return set(data.get("registered_users", [])), set(data.get("premium_users", [])), data.get("redeem_codes", {})
    except FileNotFoundError:
        return set(), set(), {}

# Save data to JSON file
def save_data():
    try:
        with open("bot_data.json", "w") as f:
            json.dump({
                "registered_users": list(registered_users),
                "premium_users": list(premium_users),
                "redeem_codes": redeem_codes
            }, f)
    except Exception as e:
        logging.error("Error saving data: %s", str(e))

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

# Analyze URL and send response
def analyze_url(url, chat_id):
    try:
        # Assuming `check_url()` is implemented as in the original code
        detected_gateways, status_code, captcha, cloudflare, payment_security_type, cvv_cvc_status, inbuilt_status = check_url(url)

        gateways_str = ', '.join(detected_gateways) if detected_gateways else "None"
        response_message = (
            f"❖ **Gateways Fetched Successfully ✅**\n"
            f"━━━━━━━━━━━━━━\n"
            f"❖ **URL:** {url}\n"
            f"❖ **Payment Gateways:** {gateways_str}\n"
            f"❖ **Captcha Detected:** {captcha}\n"
            f"❖ **Cloudflare Detected:** {cloudflare}\n"
            f"❖ **Payment Security Type:** {payment_security_type}\n"
            f"❖ **CVV/CVC Requirement:** {cvv_cvc_status}\n"
            f"❖ **Inbuilt Payment System:** {inbuilt_status}\n"
            f"❖ **Status Code:** {status_code}\n"
            f"❖ **Bot Developer: [TechPiro](https://t.me/TechPiro)**"
        )
        bot.send_message(chat_id, response_message, parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in analyzing URL: %s", str(e))
        bot.send_message(chat_id, "❖ **An Error Occurred While Processing The URL. Please Try Again.**", parse_mode="Markdown")

# Handler for /generate command for bot owner to generate redeem codes
@bot.message_handler(commands=['generate'])
def cmd_generate(message):
    if message.from_user.id != bot_owner_id:
        bot.send_message(message.chat.id, "❖ **You Are Not Authorized To Generate Redeem Codes.**", parse_mode="Markdown")
        return

    try:
        # Example usage: /generate <uses> <expiry in hours/days>
        _, uses, expiry = message.text.split()
        uses = int(uses)

        # Check if expiry is in days or hours
        if expiry.lower().endswith("d"):
            expiry_days = int(expiry[:-1])  # Get number of days
            expiry_time = datetime.now() + timedelta(days=expiry_days)
            time_unit = f"{expiry_days} Day(s)"
        elif expiry.lower().endswith("h"):
            expiry_hours = int(expiry[:-1])  # Get number of hours
            expiry_time = datetime.now() + timedelta(hours=expiry_hours)
            time_unit = f"{expiry_hours} Hour(s)"
        else:
            bot.send_message(message.chat.id, "❖ **Invalid Format. Usage: /generate <uses> <expiry in hours or days (e.g., 48h or 2d)>**", parse_mode="Markdown")
            return

        # Generate the redeem code
        code = f"OVERSTRIPE-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        
        # Save redeem code with expiry
        redeem_codes[code] = {'uses': uses, 'expiry': expiry_time}
        save_data()
        bot.send_message(
            message.chat.id, 
            f"❖ **Redeem Code Generated: `{code}`**\n"
            f"❖ **Valid For: {uses} Use(s)**\n"
            f"❖ **Expires In: {time_unit}**",
            parse_mode="Markdown"
        )
    except ValueError:
        bot.send_message(message.chat.id, "❖ **Invalid Format. Usage: /generate <uses> <expiry in hours or days (e.g., 48h or 2d)>**", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in /generate command: %s", str(e))

# Handler for /cmds command to list all available commands
@bot.message_handler(commands=['cmds'])
def cmd_cmds(message):
    help_message = (
        "❖ **Available Commands** ❖\n\n"
        "❖ **/start** - Start The Bot And Receive A Welcome Message.\n"
        "❖ **/register** - Register Yourself To Use The Bot’s Basic Features.\n"
        "❖ **/redeem <code>** - Redeem A Premium Code For Advanced Features.\n"
        "❖ **/generate <uses> <expiry in hours/days>** - *Bot Owner Only:* Generate A Redeem Code With A Set Number Of Uses And Expiration Time.\n\n"
        "❖ **How To Use:**\n"
        "   - Send A URL Directly To Analyze It.\n"
        "❖ **For Any Questions, Contact The Developer: [TechPiro](https://t.me/TechPiro)**"
    )
    bot.send_message(message.chat.id, help_message, parse_mode="Markdown")

# Handler for direct text input for URL analysis
@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        user_id = message.from_user.id
        if user_id not in registered_users:
            bot.send_message(message.chat.id, "❖ **Please Register First By Sending /register.**", parse_mode="Markdown")
            return

        url = message.text.strip()
        if is_valid_url(url):
            bot.send_message(message.chat.id, "❖ **Auto-Detect: Processing URL...**", parse_mode="Markdown")
            analyze_url(url, message.chat.id)
        else:
            bot.send_message(message.chat.id, "❖ **Invalid Input. Please Send A Valid URL Or Use A Command.**", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in handling text message: %s", str(e))

# Use a loop to ensure continuous polling
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error("Polling error: %s", str(e))
        time.sleep(5)  # Wait a bit before restarting polling
                  
