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
api_token = '8036013708:AAF-L0gANinIJRfrKWcZw4Pn5rMmLabxEq4'
bot_owner_id = 7202072688  # Bot owner's Telegram user ID
bot = telebot.TeleBot(api_token)

# Initialize logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load persistent data from JSON file
def load_data():
    try:
        with open("bot_data.json", "r") as f:
            data = json.load(f)
            return (
                set(data.get("registered_users", [])), 
                set(data.get("premium_users", [])), 
                data.get("redeem_codes", {}),
                data.get("user_credits", {})
            )
    except FileNotFoundError:
        return set(), set(), {}, {}

# Save data to JSON file
def save_data():
    try:
        with open("bot_data.json", "w") as f:
            json.dump({
                "registered_users": list(registered_users),
                "premium_users": list(premium_users),
                "redeem_codes": redeem_codes,
                "user_credits": user_credits
            }, f)
    except Exception as e:
        logging.error("Error saving data: %s", str(e))

# Initialize data
registered_users, premium_users, redeem_codes, user_credits = load_data()

# Generate redeem code with 100 credits and 3 days Premium access
@bot.message_handler(commands=['generate'])
def cmd_generate(message):
    if message.from_user.id != bot_owner_id:
        bot.send_message(message.chat.id, "❖ **You Are Not Authorized To Generate Redeem Codes.**", parse_mode="Markdown")
        return

    try:
        # Generate the redeem code in format OVER-XXXX-XXXX
        code = f"OVER-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        
        # Set redeem code details: 100 credits and 3 days of Premium access
        redeem_codes[code] = {
            'credits': 100,
            'premium_days': 3,
            'expiry': datetime.now() + timedelta(days=3),  # Code expires in 3 days
            'uses': 1
        }
        save_data()
        
        bot.send_message(
            message.chat.id, 
            f"❖ **Redeem Code Generated: `{code}`**\n"
            f"❖ **Includes: 100 Credits and 3 Days of Premium Access**\n"
            f"❖ **Expires In: 3 Days**",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error("Error in /generate command: %s", str(e))

# Redeem code for credits and premium access
@bot.message_handler(commands=['redeem'])
def cmd_redeem(message):
    try:
        user_id = message.from_user.id
        if user_id in premium_users:
            bot.send_message(message.chat.id, "❖ **You Already Have Premium Access!**", parse_mode="Markdown")
            return

        try:
            code = message.text.split()[1]
        except IndexError:
            bot.send_message(message.chat.id, "❖ **Please Provide A Redeem Code. Usage: /redeem <code>**", parse_mode="Markdown")
            return

        if code in redeem_codes:
            redeem_info = redeem_codes[code]
            if redeem_info['expiry'] < datetime.now():
                bot.send_message(message.chat.id, "❖ **This Redeem Code Has Expired.**", parse_mode="Markdown")
                del redeem_codes[code]
                save_data()
            elif redeem_info['uses'] > 0:
                # Add credits and premium access
                user_credits[user_id] = user_credits.get(user_id, 0) + redeem_info['credits']
                premium_users.add(user_id)
                save_data()
                
                # Update usage and premium expiry
                redeem_info['uses'] -= 1
                if redeem_info['uses'] == 0:
                    del redeem_codes[code]  # Delete code after uses are exhausted
                premium_expiry = datetime.now() + timedelta(days=redeem_info['premium_days'])
                
                bot.send_message(
                    message.chat.id,
                    f"❖ **Redeem Successful! You Now Have 100 Credits and Premium Access for 3 Days (Until {premium_expiry.strftime('%Y-%m-%d %H:%M:%S')}).**",
                    parse_mode="Markdown"
                )
            else:
                # Message for already redeemed code
                bot.send_message(
                    message.chat.id,
                    "🚫 **Oops! This Redeem Code Has Already Been Used By Someone Else!**\n\n"
                    "🔄 **Try Another Code Or Contact Support If You Need Assistance.**\n\n"
                    "✨ **Thank You For Your Interest!**",
                    parse_mode="Markdown"
                )
        else:
            bot.send_message(message.chat.id, "❖ **Invalid Redeem Code.**", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in /redeem command: %s", str(e))

# Other command handlers (such as /start, /register, /check, /cmds, /balance, and /add_credits) remain the same

# Ignore other text inputs
@bot.message_handler(content_types=['text'])
def handle_text(message):
    pass  # Ignore all non-command messages

# Use a loop to ensure continuous polling
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error("Polling error: %s", str(e))
        time.sleep(5)  # Wait a bit before restarting polling
