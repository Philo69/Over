import telebot
import requests
import re
import logging
import time
import random
import string
from datetime import datetime, timedelta

# Replace with your actual Telegram Bot API token and bot owner ID
api_token = '8036013708:AAGHTboIBF91IZRL4VTfLuOzEP7s0nmuSgM'
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

def find_payment_gateways(response_text):
    detected_gateways = []
    for gateway in payment_gateways:
        if gateway in response_text.lower():
            detected_gateways.append(gateway.capitalize())
    return detected_gateways

def check_captcha(response_text):
    captcha_keywords = ['captcha', 'robot', 'verification', 'prove you are not a robot', 'challenge']
    return any(keyword in response_text.lower() for keyword in captcha_keywords)

def check_cloudflare(response_text):
    cloudflare_keywords = ['cf-', 'cloudflare', 'access denied', 'please wait', 'checking your browser']
    return any(keyword in response_text.lower() for keyword in cloudflare_keywords)

def check_3d_secure(response_text):
    secure_keywords = [
        "3dsecure", "3d secure", "secure3d", "secure checkout", "verified by visa",
        "mastercard securecode", "secure verification", "3d-authentication", "3d-auth"
    ]
    return any(keyword in response_text.lower() for keyword in secure_keywords)

def check_otp_required(response_text):
    otp_keywords = [
        "otp", "one-time password", "verification code", "enter the code", 
        "authentication code", "sms code", "mobile verification"
    ]
    return any(keyword in response_text.lower() for keyword in otp_keywords)

def check_cvv_required(response_text):
    response_text = response_text.lower()
    cvv_required = "cvv" in response_text
    cvc_required = "cvc" in response_text
    if cvv_required and cvc_required:
        return "Both CVV and CVC Required"
    elif cvv_required:
        return "CVV Required"
    elif cvc_required:
        return "CVC Required"
    else:
        return "None"

def check_inbuilt_payment_system(response_text):
    inbuilt_keywords = ["native payment", "integrated payment", "built-in checkout", "secure payment on this site", "on-site payment", "internal payment gateway"]
    response_text = response_text.lower()
    return any(keyword in response_text for keyword in inbuilt_keywords)

def check_url(url):
    """Check the provided URL for payment gateways, security features, and IP info."""
    if not is_valid_url(url):
        return None, False, False, False, "Invalid URL", "N/A", ["N/A"] * 5, "N/A"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        detected_gateways = find_payment_gateways(response.text)
        captcha_detected = check_captcha(response.text)
        cloudflare_detected = check_cloudflare(response.text)
        is_3d_secure = check_3d_secure(response.text)
        is_otp_required = check_otp_required(response.text)
        cvv_cvc_status = check_cvv_required(response.text)
        inbuilt_payment = check_inbuilt_payment_system(response.text)

        payment_security_type = (
            "Both 3D Secure and OTP Required" if is_3d_secure and is_otp_required else
            "3D Secure" if is_3d_secure else
            "OTP Required" if is_otp_required else
            "2D (No extra security)"
        )
        if captcha_detected:
            payment_security_type += " | Captcha Detected"
        if cloudflare_detected:
            payment_security_type += " | Protected by Cloudflare"

        inbuilt_status = "Yes" if inbuilt_payment else "No"

        return detected_gateways, response.status_code, captcha_detected, cloudflare_detected, payment_security_type, cvv_cvc_status, inbuilt_status

    except requests.exceptions.RequestException as e:
        logging.error("Error while checking URL: %s", str(e))
        return [f"Error: {str(e)}"], 500, False, False, "N/A", "N/A", "N/A"

@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.send_message(message.chat.id, f"Hey {message.from_user.first_name}! Welcome to **Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ**! Use /register to start and check URLs.")

@bot.message_handler(commands=['register'])
def cmd_register(message):
    user_id = str(message.from_user.id)
    if user_id not in registered_users:
        registered_users[user_id] = {"credits": 100, "premium": False, "premium_expiry": None}
        bot.send_message(message.chat.id, f"❖ **Registration Successful! You now have 100 credits.**{developer_footer}", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❖ **You are already registered!**{developer_footer}", parse_mode="Markdown")

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
    detected_gateways, status_code, captcha, cloudflare, payment_security_type, cvv_cvc_status, inbuilt_status = check_url(url)

    gateways_str = ', '.join(detected_gateways) if detected_gateways else "None"
    response_message = (
        f"🔍 **Gateways Fetched Successfully ✅**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🔹 **URL:** {url}\n"
        f"🔹 **Payment Gateways:** {gateways_str}\n"
        f"🔹 **Captcha Detected:** {captcha}\n"
        f"🔹 **Cloudflare Detected:** {cloudflare}\n"
        f"🔹 **Payment Security Type:** {payment_security_type}\n"
        f"🔹 **CVV/CVC Requirement:** {cvv_cvc_status}\n"
        f"🔹 **Inbuilt Payment System:** {inbuilt_status}\n"
        f"🔹 **Status Code:** {status_code}\n"
        f"{developer_footer}"
    )
    
    bot.send_message(message.chat.id, response_message, parse_mode="Markdown")

# Auto-restart polling loop
while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logging.error("Polling error: %s", str(e))
        time.sleep(5)  # Wait a bit before restarting
