import os
import asyncio
import objects
import _thread
from time import sleep
from telethon.sync import TelegramClient, events
from datetime import datetime, timezone, timedelta
stamp1 = objects.time_now()

allowed_forward_ids = []
objects.environmental_files()
users = eval(os.environ['users'])
main_chat_id = os.environ['main_chat_id']
Auth = objects.AuthCentre(ID_DEV=-1001312302092, TOKEN=os.environ['TOKEN'])

if os.environ.get('local') is None:
    drive_client = objects.GoogleDrive('google.json')
    session_files = [f'{key}.session' for key in users]
    for file in drive_client.files():
        if file['name'] in session_files:
            drive_client.download_file(file['id'], file['name'])
# =================================================================================================================


def client_init(name, user):
    global allowed_forward_ids
    asyncio.set_event_loop(asyncio.new_event_loop())
    client = TelegramClient(name, int(user['api_id']), user['api_hash']).start()
    with client:
        @client.on(events.NewMessage(pattern=user['pattern'], from_users=[*user['admins'], 'evolvestin']))
        async def handler(event):
            replied = await event.get_reply_message()
            if replied:
                message = await client.send_message(main_chat_id, replied.message)
                allowed_forward_ids.append(message.id+1)

        @client.on(events.NewMessage(from_users=main_chat_id))
        async def response_handler(response):
            if response.message.id in allowed_forward_ids:
                await client.forward_messages(user['f_chat_id'], response.message)
        client.run_until_disconnected()


def start(stamp):
    if os.environ.get('local'):
        Auth.dev.printer('Запуск скрипта локально')
    else:
        Auth.dev.start(stamp)
    for key in users:
        _thread.start_new_thread(client_init, (key, users[key],))
    while True:
        sleep(24 * 60 * 60)


def auto_reboot():
    reboot = None
    tz = timezone(timedelta(hours=3))
    while True:
        try:
            sleep(30)
            date = datetime.now(tz)
            if date.strftime('%H') == '01' and date.strftime('%M') == '59':
                reboot = True
                while date.strftime('%M') == '59':
                    sleep(1)
                    date = datetime.now(tz)
            if reboot:
                reboot = None
                text, _ = Auth.logs.reboot()
                Auth.dev.printer(text)
        except IndexError and Exception:
            Auth.dev.thread_except()


if __name__ == '__main__':
    _thread.start_new_thread(auto_reboot, ())
    start(stamp1)
