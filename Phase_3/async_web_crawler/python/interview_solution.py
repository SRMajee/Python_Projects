"""
Async Web Crawler - Interview Solution (Python)

1. Primary Capabilities:
   - BFS crawl with asyncio.Queue + semaphore-bounded concurrency
   - Depth-limited traversal, URL deduplication
   - HTML link extraction via regex, title parsing
   - Concurrency Extension: asyncio.Semaphore controls max parallel fetches

2. Error Handling:
   - Per-URL try/except, errors stored in CrawlResult.error
   - Graceful worker cancellation on completion

3. Out Of Scope:
   - robots.txt parsing, JavaScript rendering, polite crawl delay,
     persistent storage, sitemap support, cookie/session handling
"""
import asyncio, re
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, field

@dataclass
class CrawlResult:
    url: str; status: int; title: str = ""; links: list = field(default_factory=list); error: str = ""

class Crawler:
    def __init__(self, max_depth=2, max_conc=5, fetch_fn=None):
        self.max_depth, self.max_conc, self._fetch = max_depth, max_conc, fetch_fn
        self._visited, self._results = set(), []

    async def crawl(self, seeds):
        sem = asyncio.Semaphore(self.max_conc)
        q = asyncio.Queue()
        for u in seeds:
            self._visited.add(u); await q.put((u, 0))
        async def worker():
            while True:
                url, d = await q.get()
                try:
                    async with sem:
                        st, html = await self._fetch(url)
                    title = (m.group(1) if (m := re.search(r'<title>(.*?)</title>', html)) else "")
                    links = [urljoin(url, m.group(1)) for m in re.finditer(r'href=["\']([^"\']+)', html)]
                    r = CrawlResult(url, st, title, links)
                    self._results.append(r)
                    if d < self.max_depth:
                        for lnk in links:
                            if lnk not in self._visited:
                                self._visited.add(lnk); await q.put((lnk, d + 1))
                except Exception as e:
                    self._results.append(CrawlResult(url, 0, error=str(e)))
                finally:
                    q.task_done()
        workers = [asyncio.create_task(worker()) for _ in range(self.max_conc)]
        await q.join()
        for w in workers: w.cancel()
        return self._results

if __name__ == "__main__":
    pages = {"https://a.com": (200, "<title>A</title><a href='/b'>B</a>"), "https://a.com/b": (200, "<title>B</title>")}
    async def fetch(u): return pages.get(u, (404, ""))
    r = asyncio.run(Crawler(1, 2, fetch).crawl(["https://a.com"]))
    assert len(r) == 2 and r[0].title == "A"
    print("Interview Crawler passed!")
