from pyrogram import Client
from pyrogram.types import Message

from settings import BOT_NAME, BOT_TOKEN, API_HASH, API_ID, PROXY

client = Client(name=BOT_NAME, bot_token=BOT_TOKEN, api_hash=API_HASH, api_id=API_ID, proxy=PROXY)


@client.on_message()
def handle_message(bot: Client, message: Message):
    chat_id = message.chat.id
    msg = message.text
    if msg:
        if msg.startswith('/start'):
            bot.send_message(chat_id, 'bot start')


client.run()
