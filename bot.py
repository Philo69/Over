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
api_token = '8036013708:AAHw9l9gIHrZSi6NGhKK1vPibVuE4kZVdwc'
bot_owner_id = 7202072688  # Bot owner's Telegram user ID
bot = telebot.TeleBot(api_token)

# Initialize logging with console output for easier debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Check for API token initialization
if not api_token or api_token == "YOUR_TELEGRAM_BOT_API_TOKEN":
    logging.error("Telegram API token is not set or is incorrect.")
    exit("Please set the correct Telegram API token.")

# Define the developer footer to append to messages
developer_footer = "\n\n━━━━━━━━━━━━━━\n**Developer - [@TechPiro](https://t.me/TechPiro)**"

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
        logging.info("Data file not found, initializing empty data.")
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
        logging.info("Data saved successfully.")
    except Exception as e:
        logging.error("Error saving data: %s", str(e))

# Initialize data
registered_users, premium_users, redeem_codes, user_credits = load_data()

# Simple command to check if bot is responsive
@bot.message_handler(commands=['hello'])
def greet(message):
    bot.send_message(message.chat.id, f"Hello! The bot is active.{developer_footer}", parse_mode="Markdown")

# Welcome and registration message with /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    try:
        user_id = message.from_user.id
        welcome_message = (
            f"❖ **Welcome To Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ, {message.from_user.first_name}!**\n"
            "━━━━━━━━━━━━━━\n"
            "Please use **/register** to sign up for basic features.\n"
            "For a list of all commands, type **/cmds**."
            f"{developer_footer}"
        )
        bot.send_message(message.chat.id, welcome_message, parse_mode="Markdown")
        logging.info("/start command executed successfully for user %s", user_id)
    except Exception as e:
        logging.error("Error in /start command: %s", str(e))

# Command for registering the user
@bot.message_handler(commands=['register'])
def cmd_register(message):
    try:
        user_id = message.from_user.id
        if user_id not in registered_users:
            registered_users.add(user_id)
            user_credits[user_id] = user_credits.get(user_id, 100)  # Give 100 initial credits
            save_data()
            bot.send_message(message.chat.id, f"❖ **Registration Successful! You Have Been Given 100 Credits.**{developer_footer}", parse_mode="Markdown")
            logging.info("User %s registered successfully.", user_id)
        else:
            bot.send_message(message.chat.id, f"❖ **You Are Already Registered! Use /cmds To View Commands.**{developer_footer}", parse_mode="Markdown")
            logging.info("User %s attempted to register again.", user_id)
    except Exception as e:
        logging.error("Error in /register command: %s", str(e))

# Check command for analyzing a provided URL, deducts 1 credit per check
@bot.message_handler(commands=['check'])
def cmd_check(message):
    try:
        user_id = message.from_user.id
        if user_id not in registered_users:
            bot.send_message(message.chat.id, f"❖ **Please Register First By Sending /register.**{developer_footer}", parse_mode="Markdown")
            return

        if user_credits.get(user_id, 0) < 1:
            bot.send_message(message.chat.id, f"❖ **Insufficient Credits. Please Redeem or Contact Support.**{developer_footer}", parse_mode="Markdown")
            return

        try:
            url = message.text.split()[1]
        except IndexError:
            bot.send_message(message.chat.id, f"❖ **Please Provide A URL To Check. Usage: /check <URL>**{developer_footer}", parse_mode="Markdown")
            return

        if is_valid_url(url):
            user_credits[user_id] -= 1  # Deduct one credit per check
            save_data()
            bot.send_message(message.chat.id, f"❖ **Processing URL...**{developer_footer}", parse_mode="Markdown")
            analyze_url(url, message.chat.id)
        else:
            bot.send_message(message.chat.id, f"❖ **Invalid URL Format. Please Provide A Valid URL.**{developer_footer}", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in /check command: %s", str(e))

# Generate redeem code with 100 credits and 3 days Premium access
@bot.message_handler(commands=['generate'])
def cmd_generate(message):
    if message.from_user.id != bot_owner_id:
        bot.send_message(message.chat.id, f"❖ **You Are Not Authorized To Generate Redeem Codes.**{developer_footer}", parse_mode="Markdown")
        return

    try:
        code = f"OVER-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        
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
            f"❖ **Expires In: 3 Days**{developer_footer}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error("Error in /generate command: %s", str(e))

# Redeem code for credits and premium access
@bot.message_handler(commands=['redeem'])
def cmd_redeem(message):
    try:
        user_id = message.from_user.id

        try:
            code = message.text.split()[1]
        except IndexError:
            bot.send_message(message.chat.id, f"❖ **Please Provide A Redeem Code. Usage: /redeem <code>**{developer_footer}", parse_mode="Markdown")
            return

        if code in redeem_codes:
            redeem_info = redeem_codes[code]
            if redeem_info['expiry'] < datetime.now():
                bot.send_message(message.chat.id, f"❖ **This Redeem Code Has Expired.**{developer_footer}", parse_mode="Markdown")
                del redeem_codes[code]
                save_data()
            elif redeem_info['uses'] > 0:
                user_credits[user_id] = user_credits.get(user_id, 0) + redeem_info['credits']
                premium_users.add(user_id)
                save_data()
                
                redeem_info['uses'] -= 1
                if redeem_info['uses'] == 0:
                    del redeem_codes[code]
                premium_expiry = datetime.now() + timedelta(days=redeem_info['premium_days'])
                
                bot.send_message(
                    message.chat.id,
                    f"❖ **Redeem Successful! You Now Have 100 Credits and Premium Access for 3 Days (Until {premium_expiry.strftime('%Y-%m-%d %H:%M:%S')}).**{developer_footer}",
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(
                    message.chat.id,
                    f"🚫 **Oops! This Redeem Code Has Already Been Used By Someone Else!**\n\n"
                    "🔄 **Try Another Code Or Contact Support If You Need Assistance.**\n\n"
                    f"✨ **Thank You For Your Interest!**{developer_footer}",
                    parse_mode="Markdown"
                )
        else:
            bot.send_message(message.chat.id, f"❖ **Invalid Redeem Code.**{developer_footer}", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in /redeem command: %s", str(e))

# Command to display all commands available to the user
@bot.message_handler(commands=['cmds'])
def cmd_cmds(message):
    help_message = (
        "❖ **Available Commands** ❖\n\n"
        "❖ **/start** - Start the bot and receive a welcome message.\n"
        "❖ **/register** - Register to use the bot’s basic features and get 100 initial credits.\n"
        "❖ **.credits** - Check your current credit balance.\n"
        "❖ **/redeem <code>** - Redeem a code for credits.\n"
        "❖ **/check <URL>** - Analyze a URL (costs 1 credit).\n"
        "❖ **/generate** - *Bot Owner Only:* Generate a redeem code.\n"
        "❖ **/add_credits <user_id> <credits>** - *Bot Owner Only:* Add credits to a user."
        f"{developer_footer}"
    )
    bot.send_message(message.chat.id, help_message, parse_mode="Markdown")

# New command for users to check credits with .credits
@bot.message_handler(func=lambda message: message.text == '.credits')
def check_credits(message):
    user_id = message.from_user.id
    if user_id == bot_owner_id:
        bot.send_message(message.chat.id, f"💎 **Your Credit Balance: Legendary** 💎{developer_footer}", parse_mode="Markdown")
    else:
        credits = user_credits.get(user_id, 0)
        bot.send_message(message.chat.id, f"❖ **Your Current Credit Balance: {credits} Credits**{developer_footer}", parse_mode="Markdown")
    logging.info("User %s checked their credits.", user_id)

# Command to add credits (for bot owner)
@bot.message_handler(commands=['add_credits'])
def cmd_add_credits(message):
    if message.from_user.id != bot_owner_id:
        bot.send_message(message.chat.id, f"❖ **You Are Not Authorized To Use This Command.**{developer_footer}", parse_mode="Markdown")
        return

    try:
        _, user_id, credits = message.text.split()
        user_id = int(user_id)
        credits = int(credits)

        if user_id in registered_users:
            user_credits[user_id] = user_credits.get(user_id, 0) + credits
            save_data()
            bot.send_message(message.chat.id, f"❖ **{credits} Credits Added To User {user_id}.**{developer_footer}", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❖ **User {user_id} Is Not Registered.**{developer_footer}", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, f"❖ **Invalid Format. Usage: /add_credits <user_id> <credits>**{developer_footer}", parse_mode="Markdown")
    except Exception as e:
        logging.error("Error in /add_credits command: %s", str(e))

# Improved polling with timeout and error handling
while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logging.error("Polling error: %s", str(e))
        time.sleep(5)  # Wait a bit before restarting polling
