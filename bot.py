import asyncio
import logging
import os
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

REPORTS = {
    "technology": (
        "Technology Report",
        "Technology is moving quickly across AI, software, cybersecurity, and digital services. "
        "Today's sample briefing highlights major technology themes in a concise format."
    ),
    "business": (
        "Business Report",
        "Today's business briefing covers general developments in companies, markets, entrepreneurship, "
        "and the digital economy. The information is presented for general awareness."
    ),
    "science": (
        "Science Report",
        "Today's science briefing highlights general developments in research, space, health science, "
        "and innovation, presented as an easy-to-read information summary."
    ),
    "sports": (
        "Sports Report",
        "Today's sports briefing provides a general overview of notable sporting activity, teams, "
        "competitions, and major developments."
    ),
    "world": (
        "World Report",
        "Today's world briefing provides a concise overview of major international developments and "
        "general-interest events."
    ),
}


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📰 Today's Report", callback_data="report")],
            [InlineKeyboardButton(text="📚 Categories", callback_data="categories")],
            [InlineKeyboardButton(text="ℹ️ About", callback_data="about")],
        ]
    )


def categories_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💻 Technology", callback_data="topic_technology"),
                InlineKeyboardButton(text="💼 Business", callback_data="topic_business"),
            ],
            [
                InlineKeyboardButton(text="🔬 Science", callback_data="topic_science"),
                InlineKeyboardButton(text="🏟 Sports", callback_data="topic_sports"),
            ],
            [InlineKeyboardButton(text="🌍 World", callback_data="topic_world")],
            [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back")],
        ]
    )


def report_text() -> str:
    date_text = datetime.now(timezone.utc).strftime("%d %B %Y")
    return (
        f"📰 Daily Report — {date_text}\n\n"
        "Here is today's information hub. Choose a category below for a focused summary.\n\n"
        "Technology • Business • Science • Sports • World"
    )


async def safe_edit(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Welcome to Daily Report.\n\n"
        "Browse concise information summaries by topic. "
        "Use Today's Report for the main report or Categories to choose a topic.",
        reply_markup=main_menu(),
    )


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "How to use Daily Report:\n\n"
        "• Tap Today's Report for the daily information hub.\n"
        "• Tap Categories to browse a topic.\n"
        "• Use /start at any time to return to the main menu.\n\n"
        "All content is provided for general information."
    )


@dp.callback_query(F.data == "report")
async def report_handler(callback: CallbackQuery) -> None:
    await safe_edit(callback, report_text(), categories_menu())
    await callback.answer()


@dp.callback_query(F.data == "categories")
async def categories_handler(callback: CallbackQuery) -> None:
    await safe_edit(callback, "📚 Choose a report category:", categories_menu())
    await callback.answer()


@dp.callback_query(F.data.startswith("topic_"))
async def topic_handler(callback: CallbackQuery) -> None:
    key = callback.data.removeprefix("topic_")
    title, body = REPORTS.get(key, ("Daily Report", "Select a category to continue."))
    await safe_edit(
        callback,
        f"📌 {title}\n\n{body}\n\n"
        "This section provides concise general-interest information.",
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📚 Categories", callback_data="categories")],
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back")],
            ]
        ),
    )
    await callback.answer()


@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "ℹ️ About Daily Report\n\n"
        "Daily Report is a simple information bot for browsing concise summaries "
        "across technology, business, science, sports, and world topics.\n\n"
        "The bot is designed for straightforward reading and navigation.",
        InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="back")]]
        ),
    )
    await callback.answer()


@dp.callback_query(F.data == "back")
async def back_handler(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Welcome to Daily Report.\n\nChoose an option below to explore.",
        main_menu(),
    )
    await callback.answer()


@dp.errors()
async def error_handler(event) -> None:
    logger.exception("Unhandled bot error: %s", event.exception)


async def main() -> None:
    logger.info("Starting Daily Report bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
