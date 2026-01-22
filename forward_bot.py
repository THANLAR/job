import os
import json
import asyncio
import logging
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# --- PARSE SOURCE CHANNELS (Updated Logic) ---
# Supports comma-separated list like "@channel1,@channel2"
source_env = os.getenv("SOURCE_CHANNEL")
if source_env:
    SOURCE_CHANNELS = []
    for x in source_env.split(','):
        x = x.strip()
        if x:
            SOURCE_CHANNELS.append(x)
else:
    logger.error("No SOURCE_CHANNEL found in environment variables!")
    exit(1)

# --- PARSE DESTINATION CHANNELS ---
dest_env = os.getenv("DESTINATION_CHANNELS")
if dest_env:
    DESTINATION_CHANNELS = []
    for x in dest_env.split(','):
        x = x.strip()
        if x:
            try:
                DESTINATION_CHANNELS.append(int(x))
            except ValueError:
                DESTINATION_CHANNELS.append(x)
else:
    logger.error("No DESTINATION_CHANNELS found in environment variables!")
    exit(1)

# State file is now a JSON to track multiple channels
STATE_FILE = "channel_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_state(state_data):
    with open(STATE_FILE, "w") as f:
        json.dump(state_data, f, indent=4)

async def main():
    async with TelegramClient('my_session', API_ID, API_HASH) as client:
        
        # Load the saved IDs for all channels
        state = load_state()
        
        logger.info(f"Targeting {len(SOURCE_CHANNELS)} Source Channels -> {len(DESTINATION_CHANNELS)} Destination Channels")

        # --- OUTER LOOP: Process each Source Channel one by one ---
        for source_channel in SOURCE_CHANNELS:
            try:
                logger.info(f"--- Checking Source: {source_channel} ---")
                
                # Get the last ID for THIS specific channel
                # Using the channel name/link as the key
                last_id = state.get(source_channel, 0)
                logger.info(f"Resuming {source_channel} from Message ID: {last_id}")

                # Loop through messages for this specific source
                async for message in client.iter_messages(source_channel, min_id=last_id, reverse=True, limit=50):
                    
                    # Filter: Must be Audio/Video File & Duration > 1 Hour (3600s)
                    is_valid_media = False
                    if message.file and message.file.duration:
                        if message.file.duration > 3600:
                            is_valid_media = True

                    if is_valid_media:
                        logger.info(f"[{source_channel}] Found media! ID: {message.id} ({message.file.duration}s)")
                        
                        # Loop through EACH destination channel
                        for dest_id in DESTINATION_CHANNELS:
                            try:
                                await client.forward_messages(dest_id, message)
                                logger.info(f"--> Forwarded to {dest_id}")
                                await asyncio.sleep(2) # Safety delay
                            except FloodWaitError as e:
                                logger.warning(f"FloodWait! Sleeping {e.seconds}s")
                                await asyncio.sleep(e.seconds + 5)
                                await client.forward_messages(dest_id, message)
                            except Exception as e:
                                logger.error(f"Failed to forward to {dest_id}: {e}")

                        # Update State for THIS channel immediately
                        state[source_channel] = message.id
                        save_state(state)
                        
                        await asyncio.sleep(10) # Anti-spam delay
                    else:
                        # Even if skipped, update ID so we don't check again
                        state[source_channel] = message.id
                        save_state(state)

            except Exception as e:
                logger.error(f"Error processing source channel {source_channel}: {e}")
                continue # Skip to next source channel if one fails

            # Pause briefly before switching to the next source channel
            await asyncio.sleep(2)

        logger.info("Batch processing for all channels complete.")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())