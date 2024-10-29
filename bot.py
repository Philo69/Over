import telebot
import requests
import re
import random
import string
from datetime import datetime, timedelta

# Replace with your actual Telegram Bot API token and the bot owner's user ID
api_token = '8036013708:AAHSZQQh7dnW5pT7_oBsPqCO1Z7NvO0WGiI'
bot_owner_id = 123456789  # Replace with the bot owner's Telegram user ID
bot = telebot.TeleBot(api_token)

# Store registered and premium users
registered_users = set()
premium_users = set()
redeem_codes = {}  # Structure: {'CODE': {'uses': 1, 'expiry': datetime}}

# Expanded list of payment gateways
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

def is_valid_url(url):
    """Check if the URL is valid."""
    regex = re.compile(
        r'^(?:http|ftp)s?://'  
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  
        r'localhost|'  
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  
        r'(?::\d+)?'  
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

@bot.message_handler(commands=['start'])
def cmd_start(message):
    """Welcome message with registration prompt."""
    user_id = message.from_user.id
    if user_id in registered_users:
        bot.send_message(message.chat.id, "メ Welcome back! You are already registered. Send a URL to analyze.")
    else:
        bot.send_message(
            message.chat.id,
            f"メ Welcome To Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ, {message.from_user.first_name}! 👋\n\n"
            "Please register to start using the bot by sending /register.\n"
            "For premium features, use a redeem code if you have one with /redeem <code>."
        )

@bot.message_handler(commands=['register'])
def cmd_register(message):
    """Register the user to allow access."""
    user_id = message.from_user.id
    if user_id not in registered_users:
        registered_users.add(user_id)
        bot.send_message(message.chat.id, "♁ Registration successful! You can now send a URL to analyze.")
    else:
        bot.send_message(message.chat.id, "You are already registered! Send a URL to analyze.")

@bot.message_handler(commands=['redeem'])
def cmd_redeem(message):
    """Redeem a code for premium access."""
    user_id = message.from_user.id
    if user_id in premium_users:
        bot.send_message(message.chat.id, "You already have premium access!")
        return
    
    try:
        code = message.text.split()[1]
        if code in redeem_codes:
            redeem_info = redeem_codes[code]
            # Check if the code is expired
            if redeem_info['expiry'] < datetime.now():
                bot.send_message(message.chat.id, "This redeem code has expired.")
                del redeem_codes[code]  # Remove expired code
            elif redeem_info['uses'] > 0:
                redeem_info['uses'] -= 1
                premium_users.add(user_id)
                bot.send_message(message.chat.id, "♁ Redeem successful! You now have premium access.")
                if redeem_info['uses'] == 0:
                    del redeem_codes[code]  # Remove code if no uses are left
            else:
                bot.send_message(message.chat.id, "This redeem code has no remaining uses.")
        else:
            bot.send_message(message.chat.id, "Invalid redeem code.")
    except IndexError:
        bot.send_message(message.chat.id, "Please provide a redeem code. Usage: /redeem <code>")

@bot.message_handler(commands=['generate_redeem_code'])
def cmd_generate_redeem_code(message):
    """Generate a redeem code with expiry for premium access (Owner only)."""
    if message.from_user.id != bot_owner_id:
        bot.send_message(message.chat.id, "You are not authorized to generate redeem codes.")
        return
    
    try:
        # Example usage: /generate_redeem_code <uses> <expiry in hours>
        _, uses, expiry_hours = message.text.split()
        uses = int(uses)
        expiry_hours = int(expiry_hours)
        # Generate a code in the format OVERSTRIPE-XXXX-XXXX
        code = f"OVERSTRIPE-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        expiry_time = datetime.now() + timedelta(hours=expiry_hours)

        redeem_codes[code] = {'uses': uses, 'expiry': expiry_time}
        bot.send_message(
            message.chat.id, 
            f"♁ Redeem Code Generated: {code}\n"
            f"Valid for: {uses} use(s)\n"
            f"Expires in: {expiry_hours} hour(s)"
        )
    except ValueError:
        bot.send_message(message.chat.id, "Invalid format. Usage: /generate_redeem_code <uses> <expiry in hours>")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Handle text messages and check if user is registered or has premium access."""
    user_id = message.from_user.id
    if user_id not in registered_users:
        bot.send_message(message.chat.id, "Please register first by sending /register.")
        return

    if user_id in premium_users:
        # Provide premium analysis, such as advanced data if desired
        bot.send_message(message.chat.id, "♁ Premium analysis activated for this URL.")
    
    url = message.text.strip()
    if not is_valid_url(url):
        bot.send_message(message.chat.id, "Please provide a valid URL.")
        return
    
    # Call `check_url` function here to analyze the URL...
    # Assuming `check_url` is implemented as in the original code

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
