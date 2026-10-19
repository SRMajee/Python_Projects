"""Tests for Async Web Crawler."""
import asyncio
import unittest
from crawler import AsyncWebCrawler, CrawlerConfig

# Simulated web graph
PAGES = {
    "https://example.com": (200, "<html><title>Home</title><a href='/about'>About</a><a href='/blog'>Blog</a></html>"),
    "https://example.com/about": (200, "<html><title>About</title><a href='/'>Home</a></html>"),
    "https://example.com/blog": (200, "<html><title>Blog</title><a href='/blog/post1'>Post1</a></html>"),
    "https://example.com/blog/post1": (200, "<html><title>Post1</title></html>"),
}

async def mock_fetch(url: str) -> tuple[int, str]:
    if url in PAGES:
        return PAGES[url]
    return (404, "<html><title>Not Found</title></html>")


class TestAsyncWebCrawler(unittest.TestCase):
    def _run(self, coro):
        return asyncio.run(coro)

    def test_basic_crawl(self):
        config = CrawlerConfig(max_depth=1, max_concurrency=2, allowed_domains={"example.com"})
        crawler = AsyncWebCrawler(config=config, fetch_fn=mock_fetch)
        results = self._run(crawler.crawl(["https://example.com"]))
        urls = {r.url for r in results}
        self.assertIn("https://example.com", urls)
        self.assertIn("https://example.com/about", urls)
        self.assertIn("https://example.com/blog", urls)
        # depth=1 so post1 should NOT be crawled
        self.assertNotIn("https://example.com/blog/post1", urls)

    def test_depth_2(self):
        config = CrawlerConfig(max_depth=2, max_concurrency=3, allowed_domains={"example.com"})
        crawler = AsyncWebCrawler(config=config, fetch_fn=mock_fetch)
        results = self._run(crawler.crawl(["https://example.com"]))
        urls = {r.url for r in results}
        self.assertIn("https://example.com/blog/post1", urls)

    def test_deduplication(self):
        config = CrawlerConfig(max_depth=3, max_concurrency=2, allowed_domains={"example.com"})
        crawler = AsyncWebCrawler(config=config, fetch_fn=mock_fetch)
        results = self._run(crawler.crawl(["https://example.com"]))
        url_list = [r.url for r in results]
        self.assertEqual(len(url_list), len(set(url_list)))  # no duplicates

    def test_title_extraction(self):
        config = CrawlerConfig(max_depth=0, max_concurrency=1)
        crawler = AsyncWebCrawler(config=config, fetch_fn=mock_fetch)
        results = self._run(crawler.crawl(["https://example.com"]))
        self.assertEqual(results[0].title, "Home")

    def test_error_handling(self):
        async def failing_fetch(url):
            raise ConnectionError("timeout")
        config = CrawlerConfig(max_depth=0, max_concurrency=1)
        crawler = AsyncWebCrawler(config=config, fetch_fn=failing_fetch)
        results = self._run(crawler.crawl(["https://bad.com"]))
        self.assertEqual(results[0].status, 0)
        self.assertIn("timeout", results[0].error)

    def test_concurrency_limit(self):
        call_count = 0
        max_concurrent = 0
        current = 0
        lock = asyncio.Lock()

        async def counting_fetch(url):
            nonlocal call_count, max_concurrent, current
            async with lock:
                current += 1
                call_count += 1
                if current > max_concurrent:
                    max_concurrent = current
            await asyncio.sleep(0.05)
            async with lock:
                current -= 1
            return PAGES.get(url, (404, "<html></html>"))

        config = CrawlerConfig(max_depth=1, max_concurrency=2, allowed_domains={"example.com"})
        crawler = AsyncWebCrawler(config=config, fetch_fn=counting_fetch)
        self._run(crawler.crawl(["https://example.com"]))
        self.assertLessEqual(max_concurrent, 2)


if __name__ == "__main__":
    unittest.main()
