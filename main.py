import json
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client
from pyrogram.types import Message
from web3 import Web3

from monitoring import alive, send_error
from settings import BOT_NAME, BOT_TOKEN, API_HASH, API_ID, PROXY, ADMIN_IDS

client = Client(name=BOT_NAME, bot_token=BOT_TOKEN, api_hash=API_HASH, api_id=API_ID, proxy=PROXY)
w3 = Web3()
scheduler = BackgroundScheduler()

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


def unpack_list(lst):
    res = []
    for i in lst:
        if isinstance(i, bytes):
            res.append('0x' + ''.join(c[2:] for c in map(hex, list(i))))
        elif isinstance(i, list):
            res.append(unpack_list(i))
        elif isinstance(i, dict):
            res.append(unpack_dict(i))
        else:
            res.append(i)
    return res


def unpack_dict(d):
    res = dict()
    for k, v in d.items():
        if isinstance(v, bytes):
            res[k] = '0x' + ''.join(c[2:] for c in map(hex, list(v)))
        elif isinstance(v, list):
            res[k] = unpack_list(v)
        elif isinstance(v, dict):
            res[k] = unpack_dict(v)
        else:
            res[k] = v
    return res


@client.on_message()
@send_error(client)
def handle_message(bot: Client, message: Message):
    chat_id = message.chat.id
    if message.text:
        msg = message.text
        if msg.startswith('/start'):
            bot.send_message(chat_id, '🚀 Bot started!\n' + about)
        elif msg.startswith('/abi'):
            abis = os.listdir('abis')
            if abis:
                bot.send_message(chat_id, '📜 Available ABIs:\n' + '\n'.join(abis))
            else:
                bot.send_message(chat_id, '❌ Nothing available.')
        elif msg.startswith('/decode'):
            *abi_name, bytecode = msg.split()[1:]
            abi_name = " ".join(abi_name)
            if os.path.exists(f'abis/{abi_name}'):
                with open(f'abis/{abi_name}', 'r') as fp:
                    abi = json.load(fp)
                contract = w3.eth.contract(abi=abi)
                function, call_data = contract.decode_function_input(bytecode)
                data = [f'Function: {str(function).split()[1][:-1]}\n']
                for k, v in call_data.items():
                    if isinstance(v, bytes):
                        call_data[k] = '0x' + ''.join(c[2:] for c in map(hex, list(v)))
                    elif isinstance(v, list):
                        call_data[k] = unpack_list(v)
                    elif isinstance(v, dict):
                        call_data[k] = unpack_dict(v)
                data.append(json.dumps(call_data, indent=4))
                data = '\n'.join(data)
                bot.send_message(chat_id, f"```json\n{data}```")
            else:
                bot.send_message(chat_id, "❌ File doesn't exist")
        elif msg.startswith('/del'):
            if not ADMIN_IDS or message.from_user.id in ADMIN_IDS:
                abi_name = " ".join(msg.split()[1:])
                if os.path.exists(f'abis/{abi_name}'):
                    os.remove(f'abis/{abi_name}')
                    bot.send_message(chat_id, '✅ File deleted successfully!')
                else:
                    bot.send_message(chat_id, "❌ File doesn't exist.")
            else:
                bot.send_message(chat_id, "🚫 You don't have access.")
    elif message.document and message.caption:
        msg = message.caption
        if msg.startswith('/add'):
            if not ADMIN_IDS or message.from_user.id in ADMIN_IDS:
                bot.download_media(message, 'abis/')
                bot.send_message(chat_id, f'✅ {message.document.file_name} added successfully!')
            else:
                bot.send_message(chat_id, "🚫 You don't have access.")


scheduler.add_job(alive, trigger='interval', args=(client,), start_date=datetime.now().date(), hours=2)
scheduler.start()

client.run()
