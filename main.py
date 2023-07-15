import asyncio
from aiogram import types
from aiogram.utils import executor
from aiogram.types import message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import client
from create_bot import dp, bot
from client import main_kb, get_info

from datetime import datetime, timedelta

import requests

import json

client.register_handlers_client(dp)

def get_info(query):
    url = f"https://catalog-ads.wildberries.ru/api/v5/search?keyword={query}"
    response = requests.get(url=url)
    data = response.json()
    adverts = data['adverts']
    id = adverts[0]['id']

    url = f"https://wbx-content-v2.wbstatic.net/ru/{id}.json"
    category = requests.get(url=url).json()['subj_name']

    return category

async def sched():
    with open('output.txt', 'r', encoding='utf-8') as f:
        data = f.read()

    if data == "":
        pass
    else:
        text = ""
        try:
            with open('data.json', 'r') as f:
                old_data = json.load(f)
        except FileNotFoundError:
            old_data = {}

        new_data = {}
        for query in data.split("\n"):
            try:
                category = get_info(query)
                new_data[query.lstrip()] = category
                if query.lstrip() in old_data and old_data[query.lstrip()] == category:
                    text += f"{query.lstrip()} - Не изменилось\n"
                else:
                    text += f"{query.lstrip()} - {category}\n"
            except:
                pass

        with open('data.json', 'w') as f:
            json.dump(new_data, f)

        # await bot.send_message(650413050, text=f"Отчет:\n\n{text}")
        await bot.send_message(5440191358, text=f"Отчет:\n\n{text}")



async def on_startup(dp):
    print('Bot online...')
    await dp.bot.set_my_commands([types.BotCommand("start", "Запустить бота")])

    scheduler = AsyncIOScheduler()
    scheduler.add_job(sched, 'cron', hour='11', minute='12')
    scheduler.start()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
