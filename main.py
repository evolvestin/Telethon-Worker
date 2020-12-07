import os
import objects
from GDrive import Drive
from telethon.sync import TelegramClient, events
stamp1 = objects.time_now()

allowed_forward_ids = []
account_user = 'evolvestin'
objects.environmental_files()
api_id = os.environ.get('api_id')
drive_client = Drive('google.json')
user_id = os.environ.get('user_id')
chat_id = os.environ.get('chat_id')
api_hash = os.environ.get('api_hash')
session_file = account_user + '.session'
Auth = objects.AuthCentre(os.environ['TOKEN'])

for file in drive_client.files():
    if file['name'] == session_file:
        drive_client.download_file(file['id'], session_file)

if api_id and api_hash and chat_id and user_id and os.path.isfile(session_file):
    client = TelegramClient(account_user, int(api_id), api_hash).start()
    Auth.start_message(stamp1)

    with client:
        @client.on(events.NewMessage(pattern='/e.*', from_users=user_id, chats=chat_id, blacklist_chats=True))
        async def handler(event):
            replied = await event.get_reply_message()
            if replied:
                message = await client.send_message(chat_id, event.message)
                allowed_forward_ids.append(message.id + 1)

        @client.on(events.NewMessage(from_users=chat_id))
        async def response_handler(response_event):
            if response_event.message.id in allowed_forward_ids:
                await client.forward_messages(-1001438204845, response_event.message)

        client.run_until_disconnected()
else:
    Auth.start_message(stamp1, '\nОшибка с переменными окружения.\n' + objects.bold('Бот выключен'))
