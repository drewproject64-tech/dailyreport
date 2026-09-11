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

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Daily Report", callback_data="report")],
            [InlineKeyboardButton(text="📊 Categories", callback_data="categories")],
            [InlineKeyboardButton(text="ℹ️ About", callback_data="about")],
        ]
    )


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Welcome to Daily Report.\n\n"
        "Get concise daily summaries and organized information across technology, "
        "business, science, sports, and world topics.\n\n"
        "Choose an option below to explore.",
        reply_markup=main_menu(),
    )


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Daily Report helps you browse concise topic summaries.\n\n"
        "Use /start to open the main menu."
    )


@dp.callback_query(F.data == "report")
async def report_handler(callback: CallbackQuery) -> None:
    date_text = datetime.now(timezone.utc).strftime("%d %B %Y")
    await callback.message.edit_text(
        f"📋 Daily Report — {date_text}\n\n"
        "Today's report hub is ready. Select a category to view a focused summary.\n\n"
        "Technology • Business • Science • Sports • World",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Categories", callback_data="categories")],
                [InlineKeyboardButton(text="⬅️ Back", callback_data="back")],
            ]
        ),
    )
    await callback.answer()


@dp.callback_query(F.data == "categories")
async def categories_handler(callback: CallbackQuery) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💻 Technology", callback_data="topic_technology")],
            [InlineKeyboardButton(text="💼 Business", callback_data="topic_business")],
            [InlineKeyboardButton(text="🔬 Science", callback_data="topic_science")],
            [InlineKeyboardButton(text="🏟 Sports", callback_data="topic_sports")],
            [InlineKeyboardButton(text="🌍 World", callback_data="topic_world")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back")],
        ]
    )
    await callback.message.edit_text("Choose a report category:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("topic_"))
async def topic_handler(callback: CallbackQuery) -> None:
    topics = {
        "topic_technology": ("💻 Technology", "Explore concise technology updates and topic summaries."),
        "topic_business": ("💼 Business", "Explore concise business developments and topic summaries."),
        "topic_science": ("🔬 Science", "Explore concise science developments and topic summaries."),
        "topic_sports": ("🏟 Sports", "Explore concise sports updates and topic summaries."),
        "topic_world": ("🌍 World", "Explore concise world developments and topic summaries."),
    }
    title, body = topics.get(callback.data, ("Daily Report", "Select a category to continue."))
    await callback.message.edit_text(
        f"{title}\n\n{body}\n\n"
        "This starter bot is prepared for connecting to your preferred content source or API.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 More Categories", callback_data="categories")],
                [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back")],
            ]
        ),
    )
    await callback.answer()


@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "ℹ️ About Daily Report\n\n"
        "Daily Report is an information bot for concise, organized summaries across "
        "multiple general-interest topics.\n\n"
        "It does not provide financial advice, betting predictions, or guaranteed outcomes.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back")]]
        ),
    )
    await callback.answer()


@dp.callback_query(F.data == "back")
async def back_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Welcome to Daily Report.\n\nChoose an option below to explore.",
        reply_markup=main_menu(),
    )
    await callback.answer()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
