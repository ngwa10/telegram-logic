import asyncio
import os
import re
import json
from datetime import datetime, timedelta
from pyrogram import Client, filters
from dotenv import load_dotenv

# ----------------- Load environment -----------------
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # must be integer for numeric channel IDs

# ----------------- Initialize client -----------------
app = Client(
    "my_account",
    api_id=API_ID,
    api_hash=API_HASH
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
            print(f"🔍 Matched pattern: {signal_type}")
            # (parsing logic stays the same as before…)
            # return parsed signal dict here
            pass

    print("⚠️ No matching signal format found.")
    return None

# ----------------- Save signals -----------------
def save_signal_for_processing(signal_data):
    """Saves the extracted signal data to a JSON file."""
    output_dir = "signals"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = os.path.join(output_dir, f"signal_{timestamp}.json")

    with open(file_path, "w") as f:
        json.dump(signal_data, f, indent=4)

    print(f"💾 Signal saved to {file_path}")

# ----------------- Channel listener -----------------
@app.on_channel_post(filters.chat(CHANNEL_ID) & filters.text)
async def handle_channel_post(client, message):
    """Listens for new channel posts."""

    # log raw message
    print(f"\n📩 New channel post at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Channel: {message.chat.title if message.chat else CHANNEL_ID}")
    print(f"Message ID: {message.id}")

    # split words
    words = message.text.split()
    last_five = " ".join(words[-5:]) if len(words) >= 5 else message.text
    cleaned_text = " ".join(words[:-5]) if len(words) > 5 else message.text

    print(f"📝 Last 5 words (ignored): {last_five}")
    print(f"🔑 Cleaned text used for parsing:\n{cleaned_text}\n---")

    # send only cleaned_text to parser
    signal_data = parse_signal(cleaned_text)

    if signal_data:
        print("✅ Extracted signal data:")
        for key, value in signal_data.items():
            print(f"  {key}: {value}")
        print("---")
        save_signal_for_processing(signal_data)
    else:
        print("❌ Message ignored (no valid signal detected).")

# ----------------- Main -----------------
async def main():
    print("🚀 Starting Telegram client...")
    await app.start()
    me = await app.get_me()
    print(f"✅ Logged in as: {me.first_name} ({me.id})")
    print(f"👀 Listening for channel posts in: {CHANNEL_ID}")
    print("⚡ Listener started. Waiting for messages...\n")
    await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
