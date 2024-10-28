from telethon import TelegramClient, events
import re
import json
import os

# Credentials for the Telegram Bot
API_ID = '29400566'
API_HASH = '8fd30dc496aea7c14cf675f59b74ec6f'
BOT_TOKEN = '8036013708:AAFS9hs6s2vmfNZsMMVLLeh0HPnoqqaGa3o'
BOT_OWNER_ID = 7202072688  # Replace with the Telegram ID of the bot owner

# Initialize the Telegram Client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Paths to store registered and authorized users
REGISTERED_USERS_FILE = "registered_users.json"
AUTHORIZED_USERS_FILE = "authorized_users.json"

# Regular expression to match card details in the format `number|exp_month|exp_year|cvc`
card_pattern = re.compile(r"\b(\d{16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})\b")

def luhn_check(card_number):
    """Uses the Luhn algorithm to validate a card number."""
    total = 0
    reverse_digits = card_number[::-1]
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n = n * 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

def load_users(file_path):
    """Loads users from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_user(user_id, file_path):
    """Adds a new user to a specified user list file."""
    users = load_users(file_path)
    if user_id not in users:
        users.append(user_id)
        with open(file_path, 'w') as f:
            json.dump(users, f)

def is_user_registered(user_id):
    """Checks if a user is registered."""
    return user_id in load_users(REGISTERED_USERS_FILE)

def is_user_authorized(user_id):
    """Checks if a user is authorized to bypass the card limit."""
    return user_id in load_users(AUTHORIZED_USERS_FILE)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Sends a welcome message and registration prompt."""
    user_id = event.sender_id
    if is_user_registered(user_id):
        await event.reply("❖ Welcome back to Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ ❖\n\nType /help to check card details using the Luhn algorithm.")
    else:
        await event.reply("❖ Welcome to Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ ❖\n\n❖ You need to register to use this bot.\nType /register to get started.")

@client.on(events.NewMessage(pattern='/register'))
async def register(event):
    """Registers the user if they are not already registered."""
    user_id = event.sender_id
    if is_user_registered(user_id):
        await event.reply("❖ You are already registered! ✓")
    else:
        save_user(user_id, REGISTERED_USERS_FILE)
        await event.reply("❖ Registration successful! ✓\nYou can now use the bot.\nType /help for instructions.")

@client.on(events.NewMessage(pattern='/auth'))
async def authorize_user(event):
    """Allows the bot owner to authorize a user to bypass the card limit."""
    user_id = event.sender_id
    if user_id != BOT_OWNER_ID:
        await event.reply("❖ You are not authorized to use this command. ✖")
        return

    try:
        target_user_id = int(event.message.message.split()[1])
        save_user(target_user_id, AUTHORIZED_USERS_FILE)
        await event.reply(f"❖ User {target_user_id} has been authorized to send more than 30 cards. ✓")
    except (IndexError, ValueError):
        await event.reply("❖ Please provide a valid user ID. Usage: /auth <user_id>")

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    """Provides instructions for using the bot."""
    user_id = event.sender_id
    if is_user_registered(user_id):
        await event.reply("❖ Send your card details, one per line, in this format:\n\n`card_number|exp_month|exp_year|cvc`\n\nThe bot will automatically check each card using the Luhn algorithm. ✦ You can send up to 30 cards unless authorized by the bot owner.")
    else:
        await event.reply("❖ You need to register to use this bot. Type /register to get started.")

@client.on(events.NewMessage)
async def card_check_handler(event):
    """Automatically processes card details sent by the user using the Luhn algorithm if they are registered."""
    user_id = event.sender_id
    if not is_user_registered(user_id):
        await event.reply("❖ You need to register to use this bot. Type /register to get started.")
        return

    text = event.raw_text.strip()
    lines = text.splitlines()

    # Check if user is authorized to bypass the limit
    if len(lines) > 30 and not is_user_authorized(user_id):
        await event.reply("❖ You are limited to 30 cards at a time. ✖\nPlease reduce the number of cards or request authorization.")
        return

    results = []
    for line in lines:
        card_data = line.strip()
        if "|" in card_data:
            try:
                card_number, exp_month, exp_year, cvc = card_data.split('|')
                if luhn_check(card_number):
                    results.append(f"❖ Approved ✓ - Card: {card_number}|{exp_month}|{exp_year}|{cvc}")
                else:
                    results.append(f"❖ Declined ✖ - Card: {card_number}|{exp_month}|{exp_year}|{cvc}")
            except ValueError:
                results.append("❖ Invalid format for line: " + line)
        else:
            results.append("❖ Invalid format for line: " + line)

    # Send the results back to the user
    await event.reply("\n".join(results))

# Start the bot
client.start()
client.run_until_disconnected()
