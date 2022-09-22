import os
import asyncio
import objects
import sqlite3
import _thread
from time import sleep
from telethon.sync import TelegramClient, events
from datetime import datetime, timezone, timedelta
from telethon.tl.functions.messages import SetBotCallbackAnswerRequest
from telethon.tl.types import KeyboardButtonRow, KeyboardButtonUrl, ReplyInlineMarkup, KeyboardButtonCallback
stamp1 = objects.time_now()


class SQL:
    def __init__(self, _database):
        def dict_factory(cursor, row):
            dictionary = {}
            for idx, col in enumerate(cursor.description):
                dictionary[col[0]] = row[idx]
            return dictionary
        self.connection = sqlite3.connect(_database, timeout=100, check_same_thread=False)
        self.connection.execute('PRAGMA journal_mode = WAL;')
        self.connection.execute('PRAGMA synchronous = OFF;')
        self.connection.row_factory = dict_factory
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def request(self, sql, fetchone=None):
        with self.connection:
            self.cursor.execute(sql)
        result = self.cursor.fetchone() if fetchone else self.cursor.fetchall()
        return dict(result) if result and fetchone else result


def set_inline_markup(event_id: int, markup: ReplyInlineMarkup = None):
    rows, counter = [], 0
    if markup is not None:
        for row in markup.rows:
            temp_row = []
            for button in row.buttons:
                if type(button) == KeyboardButtonCallback:
                    temp_row.append(KeyboardButtonCallback(
                        button.text, f'{counter}_{event_id}'.encode('utf-8')))
                    counter += 1
                elif type(button) == KeyboardButtonUrl:
                    temp_row.append(KeyboardButtonUrl(button.text, button.url))
                    counter += 1
            rows.append(KeyboardButtonRow(temp_row))
    return ReplyInlineMarkup(rows) if rows else None


database = SQL('edit.db')
objects.environmental_files()
users = eval(os.environ['users'])
Auth = objects.AuthCentre(ID_DEV=-1001312302092, TOKEN=os.environ['TOKEN'])
database.request(f'CREATE TABLE IF NOT EXISTS edited (original BIGINT UNIQUE, control BIGINT, user_id BIGINT)')
database.close()
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
            holder.append(event.peer_id.user_id)
            await client.send_message(user['main_bot'], event.message.message, formatting_entities=event.entities)

    @bot.on(events.CallbackQuery(chats=user['admins']))
    async def bot_queries_handler(event):
        holder.append(event.query.user_id)
        data = [int(i) for i in event.query.data.decode('utf-8').split('_')]
        message = await client.get_messages(user['main_bot'], ids=[data[1]])
        await message[0].click(data[0])
        try:
            await bot(SetBotCallbackAnswerRequest(event.query.query_id, 0))
        except IndexError and Exception:
            pass

    with client:
        @client.on(events.MessageEdited(chats=user['main_bot']))
        async def edited_handler(event):
            db = SQL('edit.db')
            record = db.request(f'SELECT * FROM edited WHERE original = {event.message.id}', fetchone=True)
            if record:
                chat = await client.get_entity(record['user_id'])
                markup = set_inline_markup(event.message.id, event.reply_markup)
                await bot.edit_message(chat, record['control'], event.message.message,
                                       buttons=markup, formatting_entities=event.entities, link_preview=False)
            db.close()

        @client.on(events.NewMessage(from_users=user['main_bot']))
        async def response_handler(event):
            if holder and event.message.message:
                db, markup, chat_id = SQL('edit.db'), event.reply_markup, holder.pop(0)
                if type(markup) == ReplyInlineMarkup:
                    markup = set_inline_markup(event.id, markup)
                    db.request(f'INSERT INTO edited (original, control, user_id) VALUES ({event.id}, NULL, {chat_id})')
                response = await bot.send_message(chat_id, event.message.message, buttons=markup,
                                                  formatting_entities=event.entities, link_preview=False)
                if type(markup) == ReplyInlineMarkup:
                    db.request(f'UPDATE edited SET control = {response.id} WHERE original = {event.id}')
                db.close()
            await client.forward_messages(user['f_chat_id'], event.message)
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
