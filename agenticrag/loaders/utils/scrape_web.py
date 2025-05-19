import nest_asyncio
nest_asyncio.apply()

import sys
if "twisted.internet.reactor" in sys.modules:
    del sys.modules["twisted.internet.reactor"]




def scrape_web(url: str) -> str:
    """Scrape and return Markdown content from a website"""
    try:
        from scrapy.crawler import CrawlerProcess
        from scrapy.spiders import Spider
        from scrapy.http import Response
        from markdownify import markdownify
    except ImportError:
        raise ImportError("Scrapy and markdownify are required to scrape web pages, install it via `pip install Scrapy markdownify`")

    results = {"markdown": ""}

    class TextExtractionSpider(Spider):
        name = "text_extraction_spider"
        start_urls = [url]

        def parse(self, response: Response):
            title = response.xpath("//title/text()").get()
            site_name = title or url.split("//")[1].split("/")[0]
            results["site_name"] = site_name

            html_body = self._extract_html_body(response)
            markdown_content = markdownify(html_body)
            results["markdown"] = f"# {title}\n\n{markdown_content}" if title else markdown_content

        def _extract_html_body(self, response: Response) -> str:
            return response.xpath("//body").get() or ""

    process = CrawlerProcess(settings={
        "LOG_LEVEL": "ERROR",
        "USER_AGENT": "Mozilla/5.0 (compatible; TextScraper/1.0)",
        "ROBOTSTXT_OBEY": True,
    })

    process.crawl(TextExtractionSpider)
    process.start()

    return results if results["markdown"] else None
