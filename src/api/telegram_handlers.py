"""Telegram bot handlers."""
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.config import settings
from src.models.domain import ParsedEvent
from src.services.llm_service import parse_events_with_llm
from src.managers.whitelist_manager import WhitelistManager
from src.managers.calendar_manager import CalendarManager
from src.managers.event_logger import EventLogger
from src.dao.database import AsyncSessionLocal


# Initialize bot and dispatcher
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=MemoryStorage())


class ClarificationState(StatesGroup):
    """State for waiting clarification from user."""
    waiting_for_answer = State()


async def get_db_session() -> AsyncSession:
    """Get database session for handlers."""
    async with AsyncSessionLocal() as session:
        return session


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command - check whitelist."""
    user_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        whitelist_mgr = WhitelistManager(session)
        
        if not await whitelist_mgr.is_user_whitelisted(user_id):
            await message.answer(
                "Доступ запрещен. Обратитесь к администратору для добавления в whitelist."
            )
            return
        
        # Update last activity
        await whitelist_mgr.update_last_activity(user_id)
        
        user = await whitelist_mgr.get_user(user_id)
        role_text = "администратор" if user.role == "admin" else "пользователь"
        
        await message.answer(
            f"Привет! Вы {role_text} календарного бота.\n\n"
            f"Отправьте сообщение с описанием события, и я добавлю его в календарь.\n\n"
            f"Команды:\n"
            f"/stats - показать статистику\n"
        )
        
        if user.role == "admin":
            await message.answer(
                "Админские команды:\n"
                "/add_user <telegram_id> - добавить пользователя\n"
                "/remove_user <telegram_id> - удалить пользователя\n"
                "/list_users - список пользователей"
            )


@dp.message(Command("add_user"))
async def cmd_add_user(message: types.Message):
    """Add user to whitelist (admin only)."""
    admin_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        whitelist_mgr = WhitelistManager(session)
        
        # Check if user is admin
        if not await whitelist_mgr.is_admin(admin_id):
            await message.answer("У вас нет прав для выполнения этой команды.")
            return
        
        # Parse command arguments
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Использование: /add_user <telegram_id>")
            return
        
        try:
            new_user_id = int(args[1])
        except ValueError:
            await message.answer("Telegram ID должен быть числом.")
            return
        
        # Add user to whitelist
        try:
            user = await whitelist_mgr.add_user(
                telegram_id=new_user_id,
                added_by=admin_id
            )
            await message.answer(f"Пользователь {new_user_id} добавлен в whitelist.")
            logger.info(f"Admin {admin_id} added user {new_user_id}")
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            await message.answer(f"Ошибка при добавлении пользователя: {e}")


@dp.message(Command("remove_user"))
async def cmd_remove_user(message: types.Message):
    """Remove user from whitelist (admin only)."""
    admin_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        whitelist_mgr = WhitelistManager(session)
        
        # Check if user is admin
        if not await whitelist_mgr.is_admin(admin_id):
            await message.answer("У вас нет прав для выполнения этой команды.")
            return
        
        # Parse command arguments
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Использование: /remove_user <telegram_id>")
            return
        
        try:
            user_id = int(args[1])
        except ValueError:
            await message.answer("Telegram ID должен быть числом.")
            return
        
        # Prevent removing yourself
        if user_id == admin_id:
            await message.answer("Вы не можете удалить самого себя.")
            return
        
        # Remove user
        try:
            success = await whitelist_mgr.remove_user(user_id)
            if success:
                await message.answer(f"Пользователь {user_id} удален из whitelist.")
                logger.info(f"Admin {admin_id} removed user {user_id}")
            else:
                await message.answer(f"Пользователь {user_id} не найден.")
        except Exception as e:
            logger.error(f"Failed to remove user: {e}")
            await message.answer(f"Ошибка при удалении пользователя: {e}")


@dp.message(Command("list_users"))
async def cmd_list_users(message: types.Message):
    """List all whitelist users (admin only)."""
    admin_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        whitelist_mgr = WhitelistManager(session)
        
        # Check if user is admin
        if not await whitelist_mgr.is_admin(admin_id):
            await message.answer("У вас нет прав для выполнения этой команды.")
            return
        
        try:
            users = await whitelist_mgr.get_all_users(only_active=True)
            if not users:
                await message.answer("Список пользователей пуст.")
                return
            
            text = "Пользователи в whitelist:\n\n"
            for user in users:
                role_emoji = "👑" if user.role == "admin" else "👤"
                text += f"{role_emoji} ID: {user.telegram_id}"
                if user.username:
                    text += f" (@{user.username})"
                text += f" - {user.role}\n"
            
            await message.answer(text)
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            await message.answer(f"Ошибка при получении списка: {e}")


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Show user statistics."""
    user_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        event_logger = EventLogger(session)
        
        try:
            stats = await event_logger.get_user_stats(user_id)
            if stats:
                await message.answer(
                    f"Ваша статистика:\n\n"
                    f"Событий создано: {stats.events_created}\n"
                    f"Первое событие: {stats.first_event_at.strftime('%Y-%m-%d')}\n"
                    f"Последнее событие: {stats.last_event_at.strftime('%Y-%m-%d') if stats.last_event_at else 'N/A'}"
                )
            else:
                await message.answer("У вас пока нет созданных событий.")
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            await message.answer(f"Ошибка при получении статистики: {e}")


@dp.message(ClarificationState.waiting_for_answer)
async def handle_clarification(message: types.Message, state: FSMContext):
    """Handle clarification answer from user."""
    await state.clear()
    await process_message(message, override_title=message.text)


async def process_message(
    message: types.Message, 
    state: FSMContext = None, 
    override_title: str = None
):
    """Process message and create calendar event."""
    user_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        # Check whitelist
        whitelist_mgr = WhitelistManager(session)
        if not await whitelist_mgr.is_user_whitelisted(user_id):
            # Ignore messages from non-whitelisted users
            return
        
        await message.answer("Обрабатываю сообщение...")
        
        try:
            # Parse events from message
            events_list = await parse_events_with_llm(message.text)
            
            if not events_list.events:
                await message.answer("Не удалось найти события в сообщении. Попробуйте ещё раз.")
                return
            
            # Get calendar manager
            calendar_mgr = CalendarManager(session)
            client = await calendar_mgr.get_calendar_client()
            
            if not client:
                await message.answer("Календарь не настроен. Обратитесь к администратору.")
                return
            
            # Create events
            created = []
            for event in events_list.events:
                if event.needs_clarification:
                    await state.set_state(ClarificationState.waiting_for_answer)
                    await state.update_data(events=events_list.events)
                    await message.answer(event.clarification_question or "Уточните детали события:")
                    return
                
                if override_title:
                    event.title = override_title
                
                # Create event in calendar
                client.create_event(event)
                created.append(event)
                
                # Log event
                event_logger = EventLogger(session)
                from datetime import datetime
                event_datetime = datetime.strptime(
                    f"{event.start_date} {event.start_time}", 
                    "%Y-%m-%d %H:%M"
                )
                await event_logger.log_event(
                    telegram_user_id=user_id,
                    event_title=event.title,
                    event_date=event_datetime,
                    calendar_type="yandex",  # TODO: Get from config
                    event_description=event.description
                )
            
            # Update user activity
            await whitelist_mgr.update_last_activity(user_id)
            
            # Send success message
            if len(created) == 1:
                result = (
                    f"✅ Событие добавлено:\n\n"
                    f"📌 {created[0].title}\n"
                    f"📅 {created[0].start_date} {created[0].start_time}\n"
                )
                if created[0].description:
                    result += f"📝 {created[0].description}\n"
            else:
                result = f"✅ Добавлено {len(created)} событий:\n\n"
                for i, event in enumerate(created, 1):
                    result += f"{i}. {event.title} — {event.start_date} {event.start_time}\n"
            
            await message.answer(result)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await message.answer(f"❌ Ошибка: {str(e)}")


@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    """Handle regular messages."""
    await process_message(message, state)


async def main():
    """Start the bot."""
    logger.info("Starting Telegram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())