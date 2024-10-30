import telebot
import requests
import re
import logging
import time
import random
import string
from datetime import datetime, timedelta

# Replace with your actual Telegram Bot API token and bot owner ID
api_token = '8036013708:AAG9AVmMmS7sgX6w1ZOIRE62rqDaoEqnQ6Y'
bot_owner_id = 7202072688  # Replace with actual bot owner's Telegram user ID
bot = telebot.TeleBot(api_token)

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# In-memory storage for simplicity
registered_users = {}
redeem_codes = {}

# Developer footer
developer_footer = "\n\n━━━━━━━━━━━━━━\n**Developer - [@techPiro](https://t.me/techPiro)**"

# Payment gateways list
payment_gateways = [
    "paypal", "stripe", "braintree", "square", "cybersource", "authorize.net", "2checkout", "adyen",
    "worldpay", "sagepay", "checkout.com", "shopify", "razorpay", "bolt", "paytm", "venmo",
    "pay.google.com", "revolut", "eway", "woocommerce", "upi", "apple.com", "payflow", "payeezy",
    "paddle", "payoneer", "recurly", "klarna", "paysafe", "webmoney", "payeer", "payu", "skrill",
    "affirm", "afterpay", "dwolla", "global payments", "moneris", "nmi", "payment cloud",
    "paysimple", "paytrace", "stax", "alipay", "bluepay", "paymentcloud", "clover",
    "zelle", "google pay", "cashapp", "wechat pay", "transferwise", "stripe connect",
    "mollie", "sezzle", "afterpay", "payza", "gocardless", "bitpay", "sureship"
]

# URL check cost
URL_CHECK_COST = 5

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

def generate_redeem_codes(count=10, credits=100, days_premium=2):
    """Generates a specified number of redeem codes with credits and premium status."""
    codes = []
    for _ in range(count):
        code = f"OVER-{''.join(random.choices(string.ascii_uppercase + string.digits, k=3))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=3))}"
        redeem_codes[code] = {
            "credits": credits,
            "premium_expiry": datetime.now() + timedelta(days=days_premium)
        }
        codes.append(code)
    return codes

@bot.message_handler(commands=['start'])
def cmd_start(message):
    welcome_message = (
        f"Welcome to **Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ**!\n"
        f"Use **/register** to start and receive 100 credits.\n"
        f"Developer: **@techPiro**{developer_footer}"
    )
    bot.send_message(message.chat.id, welcome_message, parse_mode="Markdown")

@bot.message_handler(commands=['register'])
def cmd_register(message):
    user_id = str(message.from_user.id)
    if user_id not in registered_users:
        registered_users[user_id] = {"credits": 100, "premium": False, "premium_expiry": None}
        bot.send_message(message.chat.id, f"❖ **Registration Successful! You now have 100 credits.**\n{developer_footer}", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❖ **You are already registered!**{developer_footer}", parse_mode="Markdown")

@bot.message_handler(commands=['generate'])
def cmd_generate(message):
    if message.from_user.id != bot_owner_id:
        bot.send_message(message.chat.id, f"❖ **You are not authorized to generate codes.**{developer_footer}", parse_mode="Markdown")
        return

    codes = generate_redeem_codes()
    codes_message = "\n".join(f"🔹 `{code}`" for code in codes)
    bot.send_message(message.chat.id, f"❖ **10 Redeem Codes Generated**\n\n{codes_message}{developer_footer}", parse_mode="Markdown")

@bot.message_handler(commands=['redeem'])
def cmd_redeem(message):
    try:
        code = message.text.split()[1]
        user_id = str(message.from_user.id)
        
        if code in redeem_codes and redeem_codes[code]["premium_expiry"] > datetime.now():
            registered_users[user_id]["credits"] += redeem_codes[code]["credits"]
            registered_users[user_id]["premium"] = True
            registered_users[user_id]["premium_expiry"] = redeem_codes[code]["premium_expiry"]
            del redeem_codes[code]
            bot.send_message(message.chat.id, f"❖ **Redeem Successful! You've received 100 credits and 2 days premium.**{developer_footer}", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❖ **Invalid or expired redeem code.**{developer_footer}", parse_mode="Markdown")
    except IndexError:
        bot.send_message(message.chat.id, f"❖ **Usage: /redeem <code>**{developer_footer}", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    user_id = str(message.from_user.id)
    if user_id in registered_users:
        user_info = registered_users[user_id]
        credits = user_info["credits"]
        premium_status = "Active" if user_info["premium"] and (user_info["premium_expiry"] is None or user_info["premium_expiry"] > datetime.now()) else "Inactive"
        premium_expiry = user_info["premium_expiry"].strftime("%Y-%m-%d %H:%M:%S") if user_info["premium_expiry"] else "N/A"
        
        status_message = (
            f"❖ **User Status**\n"
            f"━━━━━━━━━━━━━━\n"
            f"🔹 **Credits:** {credits}\n"
            f"🔹 **Premium Status:** {premium_status}\n"
            f"🔹 **Premium Expiry:** {premium_expiry}{developer_footer}"
        )
        bot.send_message(message.chat.id, status_message, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❖ **Please register first using /register.**{developer_footer}", parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = str(message.from_user.id)
    
    if user_id not in registered_users:
        bot.send_message(message.chat.id, f"❖ **Please register first using /register.**{developer_footer}", parse_mode="Markdown")
        return
    
    if registered_users[user_id]["credits"] < URL_CHECK_COST:
        bot.send_message(message.chat.id, f"❖ **Insufficient credits. Each URL check costs {URL_CHECK_COST} credits.**{developer_footer}", parse_mode="Markdown")
        return

    # Deduct credits for URL check
    registered_users[user_id]["credits"] -= URL_CHECK_COST

    url = message.text.strip()
    if not is_valid_url(url):
        bot.send_message(message.chat.id, "❖ **Invalid URL. Please enter a valid URL to analyze.**", parse_mode="Markdown")
        return

    # Sample response message for URL analysis
    response_message = (
        f"🔍 **Analyzing URL:** {url}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🔹 Payment Gateways: Sample\n"
        f"🔹 Captcha Detected: No\n"
        f"🔹 Cloudflare Detected: Yes\n"
        f"🔹 Security Type: 3D Secure\n"
        f"🔹 CVV/CVC Requirement: CVV Required\n"
        f"🔹 Inbuilt Payment System: Yes\n"
        f"Developer: **@techPiro**{developer_footer}"
    )
    bot.send_message(message.chat.id, response_message, parse_mode="Markdown")

# Auto-restart polling loop
while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logging.error("Polling error: %s", str(e))
        time.sleep(5)  # Wait a bit before restarting
        
