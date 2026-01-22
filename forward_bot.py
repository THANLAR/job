import os
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
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")

# Parse multiple channels from string (e.g., "-100111,-100222") to list of integers
dest_env = os.getenv("DESTINATION_CHANNELS")
if dest_env:
    DESTINATION_CHANNELS = [int(x.strip()) for x in dest_env.split(',') if x.strip()]
else:
    logger.error("No DESTINATION_CHANNELS found in environment variables!")
    exit(1)

STATE_FILE = "last_processed_id.txt"

def get_last_id():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0

def save_last_id(message_id):
    with open(STATE_FILE, "w") as f:
        f.write(str(message_id))

async def main():
    async with TelegramClient('my_session', API_ID, API_HASH) as client:
        last_id = get_last_id()
        logger.info(f"Starting check from Message ID: {last_id}")
        logger.info(f"Targeting {len(DESTINATION_CHANNELS)} destination channels.")

        # Loop through messages from Source
        async for message in client.iter_messages(SOURCE_CHANNEL, min_id=last_id, reverse=True, limit=50):
            
            # Filter: Must be Audio/Video File & Duration > 1 Hour (3600s)
            is_valid_media = False
            if message.file and message.file.duration:
                 if message.file.duration > 3600:
                     is_valid_media = True

            if is_valid_media:
                logger.info(f"Found suitable media! ID: {message.id} (Duration: {message.file.duration}s)")
                
                # Loop through EACH destination channel
                for dest_id in DESTINATION_CHANNELS:
                    try:
                        await client.forward_messages(dest_id, message)
                        logger.info(f"--> Forwarded to {dest_id}")
                        
                        # Small delay between channels to be safe
                        await asyncio.sleep(2) 
                        
                    except FloodWaitError as e:
                        logger.warning(f"FloodWait hit! Sleeping for {e.seconds} seconds")
                        await asyncio.sleep(e.seconds + 5)
                        # Retry forwarding to this channel after sleep
                        try:
                            await client.forward_messages(dest_id, message)
                        except Exception as retry_e:
                            logger.error(f"Failed to forward to {dest_id} after retry: {retry_e}")

                    except Exception as e:
                        logger.error(f"Failed to forward to {dest_id}: {e}")
                
                # Save ID only after attempting all forwards
                save_last_id(message.id)
                
                # Sleep between messages to prevent spamming
                await asyncio.sleep(10)
                
            else:
                # Update ID even if skipped, so we don't check it again
                save_last_id(message.id)

        logger.info("Batch processing complete.")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())