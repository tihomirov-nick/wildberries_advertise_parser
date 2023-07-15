import requests
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import callback_query

import re

from create_bot import bot

import json


main_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text="Загрузить запросы", callback_data="Загрузить запросы")).add(
    InlineKeyboardButton(text="Получить отчет", callback_data="Получить отчет")).add(
    InlineKeyboardButton(text="Проверить группу запросов", callback_data="Проверить группу запросов")).add(
    InlineKeyboardButton(text="Очистить файл", callback_data="Очистить файл"))


def get_info(query):
    url = f"https://catalog-ads.wildberries.ru/api/v5/search?keyword={query}"
    response = requests.get(url=url)
    data = response.json()
    adverts = data['adverts']
    id = adverts[0]['id']

    url = f"https://wbx-content-v2.wbstatic.net/ru/{id}.json"
    category = requests.get(url=url).json()['subj_name']

    return category


async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id,
                           text="Добро пожаловать! Этот Бот позволяет отслеживать приоритетные предметы по запросам в рекламе.",
                           reply_markup=main_kb)


async def new_command_start(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.edit_text(text="Главное меню", reply_markup=main_kb)


class TextState(StatesGroup):
    waiting_for_message = State()


async def get_requests(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(text="Загрузка запросов начата. Пожалуйста, отправьте запросы.", reply_markup=main_kb)
    await TextState.first()
    

async def get_text(message: types.Message, state: FSMContext):
    text = message.text
    split_text = re.split(r'[,\n;]+', text)

    with open('output.txt', 'a', encoding='utf-8') as f:
        for item in split_text:
            f.write(f"{item}\n")

    await message.answer(text="Запросы успешно загружены в файл", reply_markup=main_kb)
    await state.finish()


async def get_report(callback_query: types.CallbackQuery):
    with open('output.txt', 'r', encoding='utf-8') as f:
        data = f.read()

    if data == "":
        await callback_query.message.edit_text(text=f"База пуста", reply_markup=main_kb)
    else:
        await callback_query.message.edit_text(text="Загрузка отчета начата. Пожалуйста, ожидайте...")
        text = ""
        for query in data.split("\n"):
            try:
                text += f"{query.lstrip()} - {get_info(query)}\n"
            except:
                pass
        await callback_query.message.edit_text(text=f"Отчет:\n\n{text}", reply_markup=main_kb)


async def clear_data(callback_query: types.CallbackQuery):
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write("")
    await callback_query.message.edit_text(text="Файл очищен", reply_markup=main_kb)


class TextStateNow(StatesGroup):
    waiting_for_message = State()


async def get_text_now(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(text="Пожалуйста, отправьте запросы.", reply_markup=main_kb)
    await TextStateNow.first()


async def get_report_now(message: types.Message, state: FSMContext):
    await message.answer(text=f"Загрузка запросов начата...")
    text = message.text
    split_text = re.split(r'[,\n;]+', text)
    
    report_text = ""
    for query in split_text:
        try:
            report_text += f"{query.lstrip()} - {get_info(query)}\n"
        except:
            pass

    await message.answer(text=f"Отчет:\n\n{report_text}", reply_markup=main_kb)
    await state.finish()


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'])
    dp.register_callback_query_handler(new_command_start, lambda c: c.data == "Главное меню", state="*")

    dp.register_callback_query_handler(get_requests, lambda c: c.data == "Загрузить запросы", state="*")
    dp.register_message_handler(get_text, state=TextState.waiting_for_message)

    dp.register_callback_query_handler(get_report, lambda c: c.data == "Получить отчет", state="*")

    dp.register_callback_query_handler(clear_data, lambda c: c.data == "Очистить файл", state="*")

    dp.register_callback_query_handler(get_text_now, lambda c: c.data == "Проверить группу запросов", state="*")
    dp.register_message_handler(get_report_now, state=TextStateNow.waiting_for_message)
