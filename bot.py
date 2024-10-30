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
api_token = '8036013708:AAG6e45IUIZ1SIvr0oG2DmTYZGhACvi7C1I'
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

# Handler for /start command
@bot.message_handler(commands=['start'])
def cmd_start(message):
    try:
        user_id = message.from_user.id
        if user_id in registered_users:
            bot.send_message(message.chat.id, "**メ Welcome Back! You Are Already Registered. Send A URL To Analyze.**", parse_mode="Markdown")
        else:
            bot.send_message(
                message.chat.id,
                f"**メ Welcome To Over ❖ Stripe, {message.from_user.first_name}! 👋**\n\n"
                "**Please Register To Start Using The Bot By Sending /register.**\n"
                "**For Premium Features, Use A Redeem Code If You Have One With /redeem <code>.**\n"
                "**Type /help For More Information On Available Commands.**",
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error("Error in /start command: %s", str(e))

# Handler for /register command
@bot.message_handler(commands=['register'])
def cmd_register(message):
    try:
        user_id = message.from_user.id
        if user_id not in registered_users:
            registered_users.add(user_id)
            save_data()
            bot.send_message(message.chat.id, "**♁ Registration Successful! You Can Now Send A URL To Analyze.**", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "**You Are Already Registered! Send A URL To Analyze.**", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in /register command: %s", str(e))

# Handler for /redeem command
@bot.message_handler(commands=['redeem'])
def cmd_redeem(message):
    try:
        user_id = message.from_user.id
        if user_id in premium_users:
            bot.send_message(message.chat.id, "**You Already Have Premium Access!**", parse_mode="Markdown")
            return
        
        code = message.text.split()[1]
        if code in redeem_codes:
            redeem_info = redeem_codes[code]
            if redeem_info['expiry'] < datetime.now():
                bot.send_message(message.chat.id, "**This Redeem Code Has Expired.**", parse_mode="Markdown")
                del redeem_codes[code]
                save_data()
            elif redeem_info['uses'] > 0:
                redeem_info['uses'] -= 1
                premium_users.add(user_id)
                save_data()
                bot.send_message(message.chat.id, "**♁ Redeem Successful! You Now Have Premium Access.**", parse_mode="Markdown")
                if redeem_info['uses'] == 0:
                    del redeem_codes[code]
                    save_data()
            else:
                bot.send_message(message.chat.id, "**This Redeem Code Has No Remaining Uses.**", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "**Invalid Redeem Code.**", parse_mode="Markdown")
    except IndexError:
        bot.send_message(message.chat.id, "**Please Provide A Redeem Code. Usage: /redeem <code>**", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in /redeem command: %s", str(e))

# /help command
@bot.message_handler(commands=['help'])
def cmd_help(message):
    try:
        if message.from_user.id == bot_owner_id:
            help_message = (
                "**メ OverStripe Bot Help For Owner メ**\n\n"
                "**♁ /start** - Start The Bot And Receive A Welcome Message.\n"
                "**♁ /register** - Register Yourself To Use The Bot’s Basic Features.\n"
                "**♁ /redeem <code>** - Redeem A Premium Code For Advanced Features.\n"
                "**♁ /generate_redeem_code <uses> <expiry in hours>** - Generate A Redeem Code With A Set Number Of Uses And Expiration Time.\n\n"
                "**For Any Questions Or Issues, Please Check The Logs Or Contact Support.**"
            )
        else:
            help_message = (
                "**メ OverStripe Bot Help メ**\n\n"
                "**♁ /start** - Start The Bot And Receive A Welcome Message.\n"
                "**♁ /register** - Register Yourself To Use The Bot’s Basic Features.\n"
                "**♁ /redeem <code>** - Redeem A Premium Code For Advanced Features.\n\n"
                "**To Analyze A URL, Send The URL Directly After Registration.**\n\n"
                "**For Any Questions, Contact Support!**"
            )
        bot.send_message(message.chat.id, help_message, parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in /help command: %s", str(e))

# Handle text input for URL analysis
@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        user_id = message.from_user.id
        if user_id not in registered_users:
            bot.send_message(message.chat.id, "**Please Register First By Sending /register.**", parse_mode="Markdown")
            return

        if user_id in premium_users:
            bot.send_message(message.chat.id, "**♁ Premium Analysis Activated For This URL.**", parse_mode="Markdown")
        
        url = message.text.strip()
        if not is_valid_url(url):
            bot.send_message(message.chat.id, "**Please Provide A Valid URL.**", parse_mode="Markdown")
            return
        
        # Assuming `check_url()` is implemented as in the original code
        detected_gateways, status_code, captcha, cloudflare, payment_security_type, cvv_cvc_status, inbuilt_status = check_url(url)

        gateways_str = ', '.join(detected_gateways) if detected_gateways else "None"
        response_message = (
            f"**♁ Gateways Fetched Successfully ✅**\n"
            f"━━━━━━━━━━━━━━\n"
            f"**♁ URL:** {url}\n"
            f"**♁ Payment Gateways:** {gateways_str}\n"
            f"**♁ Captcha Detected:** {captcha}\n"
            f"**♁ Cloudflare Detected:** {cloudflare}\n"
            f"**♁ Payment Security Type:** {payment_security_type}\n"
            f"**♁ CVV/CVC Requirement:** {cvv_cvc_status}\n"
            f"**♁ Inbuilt Payment System:** {inbuilt_status}\n"
            f"**♁ Status Code:** {status_code}\n"
            f"**Bot By: Random**"
        )
        
        bot.send_message(message.chat.id, response_message, parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in handling text message: %s", str(e))

# Use a loop to ensure continuous polling
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error("Polling error: %s", str(e))
        time.sleep(5)  # Wait a bit before restarting polling
