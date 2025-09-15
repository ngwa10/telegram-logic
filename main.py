import asyncio
import os
import re
import json
from datetime import datetime, timedelta
from pyrogram import Client, filters
from dotenv import load_dotenv

# ----------------- Load environment -----------------
load_dotenv()

# Check required env vars
required_vars = ["API_ID", "API_HASH", "PHONE_NUMBER", "CHANNEL_ID"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"{var} is missing in your .env file")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ----------------- Initialize client -----------------
app = Client(
    "my_account",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER
)

# ----------------- Regex patterns -----------------
patterns = {
    "anna_signal": re.compile(
        r"CURRENCY PAIR:\s*([\w\/]+-OTC)\s*.*EXPIRATION:\s*(\w+)\s*.*TIME \(UTC-03:00\):\s*(\d{2}:\d{2}:\d{2})\s*.*(call|put|buy|sell)",
        re.IGNORECASE | re.DOTALL
    ),
    "pocket_option_otc": re.compile(
        r"Pair:\s*([\w\/]+-OTC)\s*.*Expiration:\s*(\d+ Minute)\s*.*Entry Time:\s*(\d{2}:\d{2}).*Signal Direction:\s*(\w+)",
        re.IGNORECASE | re.DOTALL
    ),
    "confirmed_entry": re.compile(
        r"Asset:\s*([\w\s]+)\s*.*Time:\s*(\d{2}:\d{2}).*Expiration:\s*(\d+ minute).*Direction:\s*🔴 (\w+)",
        re.IGNORECASE | re.DOTALL
    ),
    "currency_flags": re.compile(
        r"([\w\/]+) .*Expiration (\d+M).*Entry at (\d{2}:\d{2}).*(🟩 BUY|🟥 SELL)",
        re.IGNORECASE | re.DOTALL
    ),
}

# ----------------- Signal parser -----------------
def parse_signal(message_text):
    """Parses a message and extracts signal data using regex."""
    for signal_type, pattern in patterns.items():
        match = pattern.search(message_text)
        if match:
            # parsing logic (same as before)
            return {"source": signal_type, "raw_match": match.groups()}
    return None

# ----------------- Save signals -----------------
def save_signal_for_processing(signal_data):
    output_dir = "signals"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = os.path.join(output_dir, f"signal_{timestamp}.json")
    with open(file_path, "w") as f:
        json.dump(signal_data, f, indent=4)
    print(f"💾 Signal saved to {file_path}")

# ----------------- Debug listener -----------------
@app.on_message()
async def debug_all_messages(client, message):
    """Logs every message the client receives, regardless of chat."""
    chat_id = message.chat.id if message.chat else "Unknown"
    chat_title = message.chat.title if hasattr(message.chat, "title") else "Private/Unknown"
    text = getattr(message, "text", "")
    print(f"\n📩 Message received!")
    print(f"Chat ID: {chat_id} | Chat title: {chat_title}")
    print(f"Message ID: {message.id}")
    print(f"Message type: {message.chat.type if hasattr(message.chat, 'type') else 'Unknown'}")
    print(f"Full text: {text}")

    # Only process text messages
    if text:
        words = text.split()
        last_five = " ".join(words[-5:]) if len(words) >= 5 else text
        cleaned_text = " ".join(words[:-5]) if len(words) > 5 else text
        print(f"🔎 Last 5 words (ignored for parsing): {last_five}")
        print(f"🧹 Cleaned text for parsing: {cleaned_text}")

        signal_data = parse_signal(cleaned_text)
        if signal_data:
            print("✅ Signal detected:")
            for key, value in signal_data.items():
                print(f"   {key}: {value}")
            save_signal_for_processing(signal_data)
        else:
            print("❌ No signal matched.")

# ----------------- Main -----------------
async def main():
    print("🚀 Starting Telegram client...")
    await app.start()
    me = await app.get_me()
    print(f"✅ Logged in as: {me.first_name} ({me.id})")
    print("⚡ Listener started. Waiting for messages...")
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
