import os
import asyncio
import objects
import _thread
from time import sleep
from telethon.sync import TelegramClient, events
from datetime import datetime, timezone, timedelta
from telethon.tl.types import KeyboardButtonRow, KeyboardButtonUrl, ReplyInlineMarkup, KeyboardButtonCallback
stamp1 = objects.time_now()
objects.environmental_files()
users = eval(os.environ['users'])
Auth = objects.AuthCentre(ID_DEV=-1001312302092, TOKEN=os.environ['TOKEN'])

if os.environ.get('local') is None:
    drive_client, session_files = objects.GoogleDrive('google.json'), [f'{key}.session' for key in users]
    for file in drive_client.files():
        if file['name'] in session_files:
            drive_client.download_file(file['id'], file['name'])
# =================================================================================================================


def client_init(name, user):
    holder = []
    asyncio.set_event_loop(asyncio.new_event_loop())
    client = TelegramClient(name, int(user['api_id']), user['api_hash']).start()
    bot = TelegramClient(f'bot-{name}', int(user['api_id']), user['api_hash']).start(bot_token=user['control_token'])

    @bot.on(events.NewMessage(from_users=user['admins']))
    async def bot_messages_handler(event):
        if event.message.message:
            message = await client.send_message(
                user['main_bot'], event.message.message, formatting_entities=event.entities)
            holder.append(message.from_id.user_id)

    @bot.on(events.CallbackQuery(chats=user['admins']))
    async def bot_queries_handler(event):
        data = [int(i) for i in event.query.data.decode('utf-8').split('_')]
        message = await client.get_messages(user['main_bot'], ids=[data[1]])
        await message[0].click(data[0])
        holder.append(event.query.user_id)

    with client:
        @client.on(events.NewMessage(from_users=user['main_bot']))
        async def response_handler(event):
            if holder and event.message.message:
                rows, markup, chat_id, counter = [], event.reply_markup, holder.pop(0), 0
                if type(markup) == ReplyInlineMarkup:
                    for row in markup.rows:
                        temp_row = []
                        for button in row.buttons:
                            if type(button) == KeyboardButtonCallback:
                                temp_row.append(KeyboardButtonCallback(
                                    button.text, f'{counter}_{event.id}'.encode('utf-8')))
                                counter += 1
                            elif type(button) == KeyboardButtonUrl:
                                temp_row.append(KeyboardButtonUrl(button.text, button.url))
                                counter += 1
                        rows.append(KeyboardButtonRow(temp_row))
                    markup = ReplyInlineMarkup(rows)
                await bot.send_message(chat_id, event.message.message, buttons=markup,
                                       formatting_entities=event.entities, link_preview=False)
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
