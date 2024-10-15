import json
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from web3 import Web3
from web3.exceptions import Web3ValueError

from models import Account, QueryData, Status
from monitoring import alive, send_error
from settings import BOT_NAME, BOT_TOKEN, API_HASH, API_ID, PROXY, ADMIN_IDS
from utils import unpack_list, unpack_dict, create_buttons

client = Client(name=BOT_NAME, bot_token=BOT_TOKEN, api_hash=API_HASH, api_id=API_ID, proxy=PROXY)
chatId_account = dict()
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
home_key = InlineKeyboardMarkup([
    [InlineKeyboardButton('decode', QueryData.Decode), InlineKeyboardButton('abi', QueryData.Abi)],
    # [InlineKeyboardButton('add', QueryData.Add), InlineKeyboardButton('del', QueryData.Del)],
])
if not os.path.exists('abis'):
    os.mkdir('abis')


@client.on_callback_query()
def handle_callback_query(bot: Client, query: CallbackQuery):  # noqa
    chat_id = query.message.chat.id
    msg_id = query.message.id
    chat_acc: Account = chatId_account.setdefault(chat_id, Account())
    chat_acc.status = query.data
    if chat_acc.status == QueryData.Abi:
        abis = [f'`{abi}`' for abi in os.listdir('abis')]
        if abis:
            bot.edit_message_text(chat_id, msg_id, '📜 Available ABIs:\n' + '\n'.join(abis), reply_markup=home_key)
        else:
            bot.edit_message_text(chat_id, msg_id, '❌ Nothing available.', reply_markup=home_key)
    elif chat_acc.status == QueryData.Decode:
        abi_buttons = create_buttons(os.listdir('abis'), InlineKeyboardButton)
        if abi_buttons:
            bot.edit_message_text(chat_id, msg_id, '📝 Choose abi:', reply_markup=InlineKeyboardMarkup(abi_buttons))
        else:
            bot.edit_message_text(chat_id, msg_id, '❌ Nothing available.', reply_markup=home_key)
    elif chat_acc.status == QueryData.Add:
        pass
    elif chat_acc.status == QueryData.Del:
        pass
    else:
        bot.edit_message_text(chat_id, msg_id, '✏️ Enter bytecode:')
        chat_acc.abi = query.data
        chat_acc.status = Status.Decode


@client.on_message()
@send_error(client)
def handle_message(bot: Client, message: Message):  # noqa
    chat_id = message.chat.id
    chat_acc: Account = chatId_account.setdefault(chat_id, Account())
    if message.text:
        msg = message.text
        if msg.startswith('/start'):
            bot.send_message(chat_id, '🚀 Bot started!\n' + about, reply_markup=home_key)
        elif msg.startswith('/abi'):
            abis = [f'`{abi}`' for abi in os.listdir('abis')]
            if abis:
                bot.send_message(chat_id, '📜 Available ABIs:\n' + '\n'.join(abis), reply_markup=home_key)
            else:
                bot.send_message(chat_id, '❌ Nothing available.', reply_markup=home_key)
        elif msg.startswith('/decode') or chat_acc.status == Status.Decode:
            if msg.startswith('/decode'):
                *abi_name, bytecode = msg.split()[1:]
                abi_name = " ".join(abi_name)
            else:
                bytecode = msg
                abi_name = chat_acc.abi
            if os.path.exists(f'abis/{abi_name}'):
                with open(f'abis/{abi_name}', 'r') as fp:
                    abi = json.load(fp)
                contract = w3.eth.contract(abi=abi)
                try:
                    function, call_data = contract.decode_function_input(bytecode)
                except Web3ValueError:
                    bot.send_message(chat_id, "⚠️ Could not find any function 🔍", reply_markup=home_key)
                    return
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
                bot.send_message(chat_id, f"```json\n{data}```", reply_markup=home_key)
            else:
                bot.send_message(chat_id, "❌ File doesn't exist", reply_markup=home_key)
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
