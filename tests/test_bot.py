import os
import unittest

os.environ["BOT_TOKEN"] = "test-token"

from bot import feed_items, menu, topics_menu, search_navigation, TOPIC_NAMES


class DailyReportTests(unittest.TestCase):
    def test_feed_items_extracts_valid_items(self):
        xml = b"""<?xml version="1.0"?>
        <rss><channel>
          <item>
            <title>Example headline</title>
            <link>https://example.com/story</link>
            <source>Example</source>
          </item>
        </channel></rss>"""
        items = feed_items(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Example headline")
        self.assertEqual(items[0]["link"], "https://example.com/story")

    def test_menu_has_three_core_functions(self):
        keyboard = menu()
        labels = [
            button.text
            for row in keyboard.inline_keyboard
            for button in row
        ]
        self.assertEqual(
            labels,
            ["📰 Daily Brief", "📚 Topic Brief", "🔎 Search Headlines"],
        )

    def test_topics_cover_expected_categories(self):
        keyboard = topics_menu()
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
            if button.callback_data
        ]
        for topic in TOPIC_NAMES:
            self.assertIn(f"topic_{topic}", callbacks)

    def test_search_navigation_has_retry_path(self):
        callbacks = [
            button.callback_data
            for row in search_navigation().inline_keyboard
            for button in row
            if button.callback_data
        ]
        self.assertIn("search", callbacks)
        self.assertIn("home", callbacks)


if __name__ == "__main__":
    unittest.main()
