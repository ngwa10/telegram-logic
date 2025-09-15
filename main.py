import asyncio
import os
import re
import json
from datetime import datetime, timedelta
from pyrogram import Client, filters
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
CHANNEL_ID = os.getenv("CHANNEL_ID") # Renamed for clarity

# Initialize the Pyrogram client
app = Client(
    "my_account",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER
)

# Define regex patterns for different signal formats
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

def parse_signal(message_text):
    """Parses a message and extracts signal data using regex."""
    for signal_type, pattern in patterns.items():
        match = pattern.search(message_text)
        if match:
            # Handle different signal formats
            if signal_type == "anna_signal":
                currency_pair, expiration, entry_time_str, direction = match.groups()
                expiration_int = int(expiration.replace('M', ''))
                direction = direction.strip().upper()
                
                # Calculate martingale levels for Anna signals
                entry_time = datetime.strptime(entry_time_str, "%H:%M:%S").time()
                martingale_1_time = (datetime.combine(datetime.today(), entry_time) + timedelta(minutes=expiration_int)).time()
                martingale_2_time = (datetime.combine(datetime.today(), martingale_1_time) + timedelta(minutes=expiration_int)).time()

                return {
                    "source": "Anna Signals",
                    "currency_pair": currency_pair.replace("-OTC", "").strip(),
                    "expiration": f"{expiration_int}M",
                    "entry_time": entry_time.strftime("%H:%M"),
                    "direction": direction,
                    "martingale_levels": {
                        "level_1": martingale_1_time.strftime("%H:%M"),
                        "level_2": martingale_2_time.strftime("%H:%M")
                    }
                }
            
            elif signal_type == "pocket_option_otc":
                currency_pair, expiration, entry_time, direction = match.groups()
                expiration_int = int(re.search(r'\d+', expiration).group())
                direction = direction.strip().upper()

                martingale_times = re.findall(r"Level \d — At (\d{2}:\d{2})", message_text)
                martingale_levels = {f"level_{i+1}": t for i, t in enumerate(martingale_times)}

                return {
                    "source": "Pocket Option OTC",
                    "currency_pair": currency_pair.replace("-OTC", "").strip(),
                    "expiration": f"{expiration_int}M",
                    "entry_time": entry_time,
                    "direction": direction,
                    "martingale_levels": martingale_levels
                }

            elif signal_type == "confirmed_entry":
                asset, entry_time, expiration, direction = match.groups()
                expiration_int = int(re.search(r'\d+', expiration).group())
                # Handle PUT/CALL signals by converting to BUY/SELL
                direction = "BUY" if direction.strip().upper() == "CALL" else "SELL"
                
                martingale_times = re.findall(r"Martingale \d at (\d{2}:\d{2})", message_text)
                martingale_levels = {f"level_{i+1}": t for i, t in enumerate(martingale_times)}

                return {
                    "source": "Confirmed Entry",
                    "currency_pair": asset.strip(),
                    "expiration": f"{expiration_int}M",
                    "entry_time": entry_time,
                    "direction": direction,
                    "martingale_levels": martingale_levels
                }
            
            elif signal_type == "currency_flags":
                currency_pair, expiration, entry_time, direction = match.groups()
                expiration_int = int(expiration.replace('M', ''))
                direction = "BUY" if "🟩 BUY" in direction else "SELL"
                
                martingale_times = re.findall(r"level at (\d{2}:\d{2})", message_text)
                martingale_levels = {f"level_{i+1}": t for i, t in enumerate(martingale_times)}

                return {
                    "source": "Currency Flags",
                    "currency_pair": currency_pair.replace("-OTC", "").strip(),
                    "expiration": f"{expiration_int}M",
                    "entry_time": entry_time,
                    "direction": direction,
                    "martingale_levels": martingale_levels
                }

    return None

def save_signal_for_processing(signal_data):
    """Saves the extracted signal data to a JSON file."""
    output_dir = "signals"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = os.path.join(output_dir, f"signal_{timestamp}.json")
    
    with open(file_path, "w") as f:
        json.dump(signal_data, f, indent=4)
    print(f"Signal saved to {file_path}")

@app.on_message(filters.chat(CHANNEL_ID) & filters.text)
async def handle_message(client, message):
    """Listens for new messages in the specified channel and processes them."""
    if message.text:
        print(f"New message from channel: {message.text}\n---")
        signal_data = parse_signal(message.text)
        
        if signal_data:
            print("Detected a signal:")
            for key, value in signal_data.items():
                print(f"  {key}: {value}")
            print("\n---")
            save_signal_for_processing(signal_data)

async def main():
    """Starts the client and runs the listener."""
    await app.start()
    print("Listener started. Waiting for messages...")
    await asyncio.Future()  # Wait forever until stopped

if __name__ == "__main__":
    asyncio.run(main())
