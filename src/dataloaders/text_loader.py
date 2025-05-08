from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from scrapy.http import Response
from markdownify import markdownify

from .base import BaseDataLoader
from ..datastores.vectorstores.textstore import TextStore
from ..datastores.sqlstores.metastore import MetaStore
from ..types.core import TextData, MetaData
from .utils.text_to_desc import text_to_desc
from ..utils.logging_config import setup_logger


logger = setup_logger(__name__)

class TextLoader(BaseDataLoader):
    """
    This is data loading class that loads text content and store them into elastic search.
    """
    @property
    def data_store(self):
        return TextStore()

    def load_text(self, text:str, name:str, description:str = None, source:str = None) -> str:
        if description is None:
            description = text_to_desc(text=text)
        data = TextData(name=name, description=description, text=text, source=source)
        self.data_store.store(data=data)
        metadata = MetaData(type=self.data_store.source_data_type, name=name, description=description)
        self.meta_store.store(metadata)


    def load_web(self, url: str, name: str = None, description: str = None) -> str:
        web_data = self._scrape_web(url)
        if name is None:
            name = web_data['site_name']
        logger.debug(f"url {url} scrape successful with name: {name}")
        self.load_text(text=web_data['markdown'], name=web_data['site_name'], description=description, source=url)        



    @staticmethod
    def _scrape_web(url:str)->str:
        """Scrape and return Markdown content from a website"""
        results = {"markdown": ""}

        class TextExtractionSpider(Spider):
            name = "text_extraction_spider"
            start_urls = [url]

            def parse(self, response: Response) -> None:
                title = response.xpath("//title/text()").get()
                site_name = title or url.split("//")[1].split("/")[0]
                results["site_name"] = site_name

                html_body = self._extract_html_body(response)
                markdown_content = markdownify(html_body)
                results["markdown"] = f"# {title}\n\n{markdown_content}" if title else markdown_content

            def _extract_html_body(self, response: Response) -> str:
                """Extract the main body content as HTML"""
                body_content = response.xpath("//body").get()
                return body_content or ""

        process = CrawlerProcess(settings={
            "LOG_LEVEL": "ERROR",
            "USER_AGENT": "Mozilla/5.0 (compatible; TextScraper/1.0)",
            "ROBOTSTXT_OBEY": True
        })
        
        process.crawl(TextExtractionSpider)
        process.start()

        if results["markdown"]:
            return results
        else:
            return None
    

