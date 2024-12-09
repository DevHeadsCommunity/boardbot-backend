import os
 
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

token = os.getenv('BOT_TOKEN')
group_id = os.getenv('TEST_GROUP_ID')

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text("Welcome Here!! I am designed to send error messages to the groups that I am a member of. Please make sure that I am a member of the group that you want to send messages to and give me admin rights.")
    except Exception as e:
        print(f"Error: Failed to send message - {str(e)}")


def main() -> None:
    try:
        application = Application.builder().token(token).build()

        application.add_handler(CommandHandler("start", start))

        print("Bot started successfully!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Error: Failed to start bot - {str(e)}")


if __name__ == "__main__":
    main()