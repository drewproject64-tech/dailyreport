import asyncio
import html
import logging
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required.")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("dailyreport")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

RSS_FEEDS = {
    "technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "sports": "https://feeds.bbci.co.uk/sport/rss.xml",
    "world": "https://feeds.bbci.co.uk/news/world/rss.xml",
}

TOPIC_NAMES = {
    "technology": "Technology",
    "business": "Business",
    "science": "Science",
    "sports": "Sports",
    "world": "World",
}

awaiting_search: set[int] = set()


def menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📰 Daily Brief", callback_data="daily")],
            [InlineKeyboardButton(text="📚 Topic Brief", callback_data="topics")],
            [InlineKeyboardButton(text="🔎 Search Headlines", callback_data="search")],
        ]
    )


def navigation() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="home")]]
    )


def topics_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Technology", callback_data="topic_technology"),
                InlineKeyboardButton(text="Business", callback_data="topic_business"),
            ],
            [
                InlineKeyboardButton(text="Science", callback_data="topic_science"),
                InlineKeyboardButton(text="Sports", callback_data="topic_sports"),
            ],
            [InlineKeyboardButton(text="World", callback_data="topic_world")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="home")],
        ]
    )


def search_navigation() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Search Again", callback_data="search")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="home")],
        ]
    )


def feed_items(xml_data: bytes, limit: int = 5) -> list[dict[str, str]]:
    root = ET.fromstring(xml_data)
    items: list[dict[str, str]] = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        source = (item.findtext("source") or "BBC").strip()
        if title and link:
            items.append(
                {"title": html.unescape(title), "source": source}
            )
    return items


async def fetch_feed(url: str, limit: int = 5) -> list[dict[str, str]]:
    def load() -> list[dict[str, str]]:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "DailyReportBot/1.0"},
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            return feed_items(response.read(), limit)

    return await asyncio.to_thread(load)


async def fetch_topic(topic: str, limit: int = 5) -> list[dict[str, str]]:
    url = RSS_FEEDS.get(topic)
    if not url:
        return []
    try:
        return await fetch_feed(url, limit)
    except (OSError, ET.ParseError, ValueError) as exc:
        logger.warning("Feed fetch failed for %s: %s", topic, exc)
        return []


def content_navigation() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📰 Daily Brief", callback_data="daily")],
            [InlineKeyboardButton(text="📚 Topics", callback_data="topics")],
            [InlineKeyboardButton(text="🔎 Search", callback_data="search")],
        ]
    )


def format_items(items: list[dict[str, str]]) -> str:
    lines = []
    for index, item in enumerate(items, 1):
        lines.append(f"{index}. {item['title']}\n   {item['source']}")
    return "\n\n".join(lines)


async def daily_brief() -> tuple[str, InlineKeyboardMarkup]:
    date_text = datetime.now(timezone.utc).strftime("%d %B %Y")
    selected = ["technology", "business", "science", "sports", "world"]
    all_items: list[tuple[str, dict[str, str]]] = []

    results = await asyncio.gather(
        *(fetch_topic(topic, 2) for topic in selected),
        return_exceptions=True,
    )
    for topic, result in zip(selected, results):
        if isinstance(result, list):
            all_items.extend((topic, item) for item in result)

    if not all_items:
        return (
            f"📰 Daily Brief — {date_text}\n\n"
            "The latest reports are temporarily unavailable. Please try again.",
            InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Try Again", callback_data="daily")],
                    [InlineKeyboardButton(text="🏠 Main Menu", callback_data="home")],
                ]
            ),
        )

    lines = [f"📰 Daily Brief — {date_text}", ""]
    for topic, item in all_items[:10]:
        lines.append(f"• {TOPIC_NAMES[topic]}: {item['title']}")
    lines.extend(["", "All report content is displayed directly inside Telegram."])
    return "\n".join(lines), content_navigation()


async def show_topic(topic: str) -> tuple[str, InlineKeyboardMarkup]:
    name = TOPIC_NAMES.get(topic)
    if not name:
        return "That topic is not available.", topics_menu()

    items = await fetch_topic(topic, 7)
    if not items:
        return (
            f"📚 {name} Brief\n\n"
            "This report is temporarily unavailable. Please try again.",
            InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Try Again", callback_data=f"topic_{topic}")],
                    [InlineKeyboardButton(text="📚 Topics", callback_data="topics")],
                    [InlineKeyboardButton(text="🏠 Main Menu", callback_data="home")],
                ]
            ),
        )

    text = f"📚 {name} Brief\n\n{format_items(items)}"
    return text, content_navigation()


async def search_headlines(query: str) -> tuple[str, InlineKeyboardMarkup]:
    clean = " ".join(query.split()).strip()
    if not clean or len(clean) > 80:
        return (
            "Please enter a search term between 1 and 80 characters.",
            search_navigation(),
        )

    encoded = urllib.parse.quote_plus(clean)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en&gl=US&ceid=US:en"
    try:
        items = await fetch_feed(url, 7)
    except (OSError, ET.ParseError, ValueError) as exc:
        logger.warning("Search failed: %s", exc)
        items = []

    if not items:
        return (
            f"🔎 Search Headlines\n\nNo recent headlines were found for “{clean}”.\n"
            "Try a broader search term.",
            search_navigation(),
        )

    return (
        f"🔎 Search Headlines\n\nResults for “{clean}”:\n\n{format_items(items)}",
        headline_keyboard(items),
    )


def welcome_text() -> str:
    return (
        "Welcome to Daily Report.\n\n"
        "Get current news and updates directly inside Telegram:\n"
        "• Daily Brief — a quick overview across topics.\n"
        "• Topic Brief — focused headlines by category.\n"
        "• Search Headlines — find recent headlines by keyword.\n\n"
        "Choose an option below."
    )


async def safe_edit(
    callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup
) -> None:
    if not callback.message:
        return
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    awaiting_search.discard(message.from_user.id)
    await message.answer(welcome_text(), reply_markup=menu())


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    awaiting_search.discard(message.from_user.id)
    await message.answer(
        "Daily Report provides current headlines through three functions:\n\n"
        "1. Daily Brief — overview across several topics.\n"
        "2. Topic Brief — headlines for a selected category.\n"
        "3. Search Headlines — search recent headlines by keyword.\n\n"
        "Use the buttons to navigate. /start returns to the main menu.",
        reply_markup=menu(),
    )


@dp.callback_query(F.data == "home")
async def home_handler(callback: CallbackQuery) -> None:
    awaiting_search.discard(callback.from_user.id)
    await safe_edit(callback, welcome_text(), menu())
    await callback.answer()


@dp.callback_query(F.data == "daily")
async def daily_handler(callback: CallbackQuery) -> None:
    await callback.answer("Loading the latest brief…")
    text, markup = await daily_brief()
    await safe_edit(callback, text, markup)


@dp.callback_query(F.data == "topics")
async def topics_handler(callback: CallbackQuery) -> None:
    await safe_edit(callback, "📚 Choose a topic:", topics_menu())
    await callback.answer()


@dp.callback_query(F.data.startswith("topic_"))
async def topic_handler(callback: CallbackQuery) -> None:
    topic = callback.data.removeprefix("topic_")
    await callback.answer("Loading headlines…")
    text, markup = await show_topic(topic)
    await safe_edit(callback, text, markup)


@dp.callback_query(F.data == "search")
async def search_handler(callback: CallbackQuery) -> None:
    awaiting_search.add(callback.from_user.id)
    await safe_edit(
        callback,
        "🔎 Search Headlines\n\nSend one keyword or short phrase, for example:\n\n"
        "AI\nspace exploration\ntechnology",
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Cancel", callback_data="home")]
            ]
        ),
    )
    await callback.answer()


@dp.message(F.text)
async def text_handler(message: Message) -> None:
    user_id = message.from_user.id
    if user_id not in awaiting_search:
        await message.answer(
            "Please choose one of the three functions below.",
            reply_markup=menu(),
        )
        return

    awaiting_search.discard(user_id)
    await message.answer("Searching recent headlines…")
    text, markup = await search_headlines(message.text)
    await message.answer(text, reply_markup=markup)


@dp.message()
async def unsupported_message_handler(message: Message) -> None:
    await message.answer(
        "I can only process text searches here. Choose a function below.",
        reply_markup=menu(),
    )


@dp.errors()
async def error_handler(event: Any) -> bool:
    logger.exception("Unhandled bot error: %s", event.exception)
    return True


async def main() -> None:
    logger.info("Starting Daily Report bot")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
