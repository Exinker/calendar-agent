import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from config import settings
from models import ParsedEvent
from llm_parser import parse_events
from calendar_clients.yandex import YandexCalendarClient
from calendar_clients.icloud import ICloudCalendarClient
from time_utils import get_current_datetime_str


logger.add("bot.log", rotation="1 day", level=settings.log_level)

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=MemoryStorage())

yandex_client = YandexCalendarClient()
icloud_client = ICloudCalendarClient()

user_calendars = {}


def get_active_calendar(user_id: int) -> str:
    active = user_calendars.get(user_id, settings.default_calendar)
    if active == "yandex" and not settings.yandex_enabled:
        return "icloud" if settings.icloud_enabled else None
    if active == "icloud" and not settings.icloud_enabled:
        return "yandex" if settings.yandex_enabled else None
    return active


def get_calendar_client(calendar_type: str):
    if calendar_type == "yandex":
        return yandex_client
    return icloud_client


class ClarificationState(StatesGroup):
    waiting_for_answer = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_calendars[message.from_user.id] = settings.default_calendar
    await message.answer(
        f"Привет! Я бот для добавления событий в календарь.\n"
        f"Текущий календарь: {settings.default_calendar}\n"
        f"Отправьте сообщение с описанием события, и я добавлю его в календарь.\n\n"
        f"Команды:\n"
        f"/calendar - показать текущий календарь\n"
        f"/set_calendar <yandex|icloud> - сменить календарь\n"
        f"/calendars - список доступных календарей"
    )


@dp.message(Command("calendar"))
async def cmd_calendar(message: types.Message):
    active = get_active_calendar(message.from_user.id)
    await message.answer(f"Текущий календарь: {active}")


@dp.message(Command("set_calendar"))
async def cmd_set_calendar(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or args[1] not in ("yandex", "icloud"):
        await message.answer("Использование: /set_calendar <yandex|icloud>")
        return

    calendar_type = args[1]
    if calendar_type == "yandex" and not settings.yandex_enabled:
        await message.answer("Yandex Calendar отключен")
        return
    if calendar_type == "icloud" and not settings.icloud_enabled:
        await message.answer("iCloud Calendar отключен")
        return

    user_calendars[message.from_user.id] = calendar_type
    await message.answer(f"Активный календарь: {calendar_type}")


@dp.message(Command("calendars"))
async def cmd_calendars(message: types.Message):
    available = []
    if settings.yandex_enabled:
        available.append("yandex")
    if settings.icloud_enabled:
        available.append("icloud")

    active = get_active_calendar(message.from_user.id)
    text = "Доступные календари:\n" + "\n".join(f"{'• ' if c == active else '  '}{c}" for c in available)
    await message.answer(text)


@dp.message(Command("now"))
async def cmd_now(message: types.Message):
    await message.answer(f"Текущее время: {get_current_datetime_str()}")


@dp.message(ClarificationState.waiting_for_answer)
async def handle_clarification(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await process_message(message, state, override_title=message.text)


async def process_message(message: types.Message, state: FSMContext = None, override_title: str = None):
    try:
        await message.answer("Обрабатываю сообщение...")

        events_list = await parse_events(message.text)

        if not events_list.events:
            await message.answer("Не удалось найти события в сообщении. Попробуйте ещё раз.")
            return

        calendar_type = get_active_calendar(message.from_user.id)
        if not calendar_type:
            await message.answer("Нет доступных календарей. Включите хотя бы один в настройках.")
            return
        client = get_calendar_client(calendar_type)

        created = []
        for event in events_list.events:
            if event.needs_clarification:
                await state.set_state(ClarificationState.waiting_for_answer)
                await state.update_data(events=events_list.events)
                await message.answer(event.clarification_question or "Уточните детали события:")
                return

            if override_title:
                event.title = override_title

            client.create_event(event)
            created.append(event)

        if len(created) == 1:
            result = (
                f"Событие добавлено в {calendar_type}:\n\n"
                f"Название: {created[0].title}\n"
                f"Дата: {created[0].start_date} {created[0].start_time}\n"
            )
            if created[0].description:
                result += f"Описание: {created[0].description}\n"
        else:
            result = f"Добавлено {len(created)} событий в {calendar_type}:\n\n"
            for i, event in enumerate(created, 1):
                result += f"{i}. {event.title} — {event.start_date} {event.start_time}"
                if event.description:
                    result += f" ({event.description})"
                result += "\n"

        await message.answer(result)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.answer(f"Ошибка: {str(e)}")


@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    await process_message(message, state)


async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
