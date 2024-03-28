import json

import scrapy
from itemadapter import ItemAdapter
from scrapy import Item, Field
from scrapy.crawler import CrawlerProcess


class QuoteItem(Item):
    quote = Field()
    author = Field()
    tags = Field()


class AuthorItem(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    description = Field()


class DataPipeline:
    quotes = []
    authors = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'fullname' in adapter.keys():
            self.authors.append(dict(adapter))
        elif 'quote' in adapter.keys():
            self.quotes.append(dict(adapter))
        else:
            raise Exception('Something went wrong.')

    def close_spider(self, spider):
        with open('quotes.json', 'w', encoding='utf-8') as f:
            json.dump(self.quotes, f, ensure_ascii=False, indent=4)
        with open('authors.json', 'w', encoding='utf-8') as f:
            json.dump(self.authors, f, ensure_ascii=False, indent=4)


class GetQuotesSpider(scrapy.Spider):
    name = 'get_quotes'
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com"]
    custom_settings = {"ITEM_PIPELINES": {DataPipeline: 300}}

    def parse(self, response, **kwargs):
        for q in response.xpath("//div[@class='quote']"):
            quote = q.xpath("span[@class='text']/text()").get().strip()
            author = q.xpath("span/small[@class='author']/text()").get().strip()
            tags = q.xpath("div[@class='tags']/a/text()").extract()

            yield QuoteItem(quote=quote, author=author, tags=tags)
            author_page_link = q.xpath("span/a/@href").get()
            if author_page_link:
                yield response.follow(url=author_page_link, callback=self.parse_author)

        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield response.follow(url=next_link)

    @classmethod
    def parse_author(cls, response, **kwargs):
        a = response.xpath("/html//div[@class='author-details']")
        fullname = a.xpath("h3[@class='author-title']/text()").get().strip()
        born_date = a.xpath("p/span[@class='author-born-date']/text()").get().strip()
        born_location = a.xpath("p/span[@class='author-born-location']/text()").get().strip()
        description = a.xpath("div[@class='author-description']/text()").get().strip()

        yield AuthorItem(fullname=fullname, born_date=born_date, born_location=born_location, description=description)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(GetQuotesSpider)
    process.start()
