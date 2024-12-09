import requests
import os
from dotenv import load_dotenv
load_dotenv()

def send_message_to_telegram_group(bot_token, group_id, message):
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": group_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print("Error sending message to telegram group", e)


bot_token = os.getenv("BOT_TOKEN")
group_id = os.getenv("TEST_GROUP_ID")


def create_error_logger(logger):
    original_error = logger.error
    
    def enhanced_error(message, *args, **kwargs):
        try:            
            # Add debug prints
            print(f"Bot token: {bot_token}")
            print(f"Group ID: {group_id}")
            
            # Call original error method
            original_error(message, *args, **kwargs)
            
            # Add debug print before sending
            print("Attempting to send Telegram message...")
            send_message_to_telegram_group(bot_token, group_id, message)
            print("Telegram message sent")
            
        except Exception as e:
            original_error(f"Logging enhancement failed: {e}")
            original_error(message, *args, **kwargs)
    
    return enhanced_error