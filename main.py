import json
import os

from pyrogram import Client
from pyrogram.types import Message
from web3 import Web3

from settings import BOT_NAME, BOT_TOKEN, API_HASH, API_ID, PROXY, ADMIN_ID

client = Client(name=BOT_NAME, bot_token=BOT_TOKEN, api_hash=API_HASH, api_id=API_ID, proxy=PROXY)
w3 = Web3()

about = '''
Commands:
🚀 /start: Bot start
🔍 `/decode [abi_file_name bytecode]`: Decode a bytecode
📂 /abi: Show name of all ABI files
➕ `/add (Attach abi_file_name)` : Add a abi file
➖ `/del [abi_file_name]`: Delete a abi file
'''
if not os.path.exists('abis'):
    os.mkdir('abis')


@client.on_message()
def handle_message(bot: Client, message: Message):
    chat_id = message.chat.id
    if message.text:
        msg = message.text
        if msg.startswith('/start'):
            bot.send_message(chat_id, 'Bot start\n' + about)
        elif msg.startswith('/abi'):
            abis = os.listdir('abis')
            bot.send_message(chat_id, '\n'.join(abis))
        elif msg.startswith('/decode'):
            *abi_name, bytecode = msg.split()[1:]
            abi_name = " ".join(abi_name)
            if os.path.exists(f'abis/{abi_name}'):
                with open(f'abis/{abi_name}', 'r') as fp:
                    abi = json.load(fp)
                contract = w3.eth.contract(abi=abi)
                call_data = contract.decode_function_input(bytecode)
                data = [f'Function: {str(call_data[0]).split()[1][:-1]}\n']
                for k, v in call_data[1].items():
                    data.append(f'{k}: {v}')
                data = '\n'.join(data)
                bot.send_message(chat_id, f"```json\n{data}```")
            else:
                bot.send_message(chat_id, "File doesn't exist")
        elif msg.startswith('/del'):
            if not ADMIN_ID or message.from_user.id == ADMIN_ID:
                abi_name = " ".join(msg.split()[1:])
                if os.path.exists(f'abis/{abi_name}'):
                    os.remove(f'abis/{abi_name}')
                    bot.send_message(chat_id, 'File deleted')
                else:
                    bot.send_message(chat_id, "File doesn't exist")
            else:
                bot.send_message(chat_id, "You haven't access")
    elif message.document and message.caption:
        msg = message.caption
        if msg.startswith('/add'):
            if not ADMIN_ID or message.from_user.id == ADMIN_ID:
                bot.download_media(message, 'abis/')
                bot.send_message(chat_id, f'{message.document.file_name} added')
            else:
                bot.send_message(chat_id, "You haven't access")


client.run()
