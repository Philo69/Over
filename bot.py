import telebot
import requests
import re
import random
import string
import json
import logging
from datetime import datetime, timedelta

# Replace with your actual Telegram Bot API token
api_token = '8036013708:AAGDNShcujmXUHSOyPqtmXXkHmhPVVx6DZw'
bot_owner_id = 7202072688  # Bot owner's Telegram user ID
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

# Define a developer footer
developer_footer = "\n\n━━━━━━━━━━━━━━\n**Developer - [@TechPiro](https://t.me/TechPiro)**"

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

# Persistent data management
def load_data():
    try:
        with open("bot_data.json", "r") as f:
            data = json.load(f)
            return data.get("registered_users", {}), data.get("redeem_codes", {}), data.get("user_credits", {})
    except FileNotFoundError:
        return {}, {}, {}

def save_data(registered_users, redeem_codes, user_credits):
    with open("bot_data.json", "w") as f:
        json.dump({
            "registered_users": registered_users,
            "redeem_codes": redeem_codes,
            "user_credits": user_credits
        }, f)

registered_users, redeem_codes, user_credits = load_data()

# Function to generate a redeem code in the format "OVER-XXXX-XXXX"
def generate_code():
    return f"OVER-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

# Command to generate 10 redeem codes (Owner only)
@bot.message_handler(commands=['generate'])
def cmd_generate(message):
    if message.from_user.id != bot_owner_id:
        bot.send_message(message.chat.id, f"❖ **You are not authorized to generate codes.**{developer_footer}", parse_mode="Markdown")
        return

    try:
        _, credit_amount, days_valid = message.text.split()
        credit_amount = int(credit_amount)
        days_valid = int(days_valid)

        generated_codes = []
        for _ in range(10):
            code = generate_code()
            redeem_codes[code] = {
                "credits": credit_amount,
                "expiry": datetime.now() + timedelta(days=days_valid),
                "uses": 1
            }
            generated_codes.append(code)

        save_data(registered_users, redeem_codes, user_credits)

        codes_message = "\n".join(f"🔹 `{code}`" for code in generated_codes)
        response_message = (
            f"❖ **10 Redeem Codes Generated**\n"
            f"❖ **Credits per Code:** {credit_amount} credits\n"
            f"❖ **Valid for:** {days_valid} days\n\n"
            f"{codes_message}{developer_footer}"
        )
        bot.send_message(message.chat.id, response_message, parse_mode="Markdown")

    except ValueError:
        bot.send_message(message.chat.id, f"❖ **Invalid format. Usage: /generate <credits> <days>**{developer_footer}", parse_mode="Markdown")

# Additional commands and URL analysis code remain unchanged from previous versions

bot.polling()
