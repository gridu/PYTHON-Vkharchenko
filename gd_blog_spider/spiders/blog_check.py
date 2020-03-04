import logging
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from scrapy.spiders import CrawlSpider
import pandas as pd

from gd_blog_spider.spiders.blog_parse import GDBlogCrawler

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s', )


class BlogCheckSpider(CrawlSpider):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        logging.getLogger('scrapy').propagate = False

    name = 'blog_check'
    allowed_domains = ['blog.griddynamics.com']
    start_urls = ['http://blog.griddynamics.com/explore/']
    blog_posts_dates = []
    new_articles_len = 0
    new_article_counter = 1

    def parse(self, response):
        data_articles = pd.read_csv('articles.csv')
        last_article_date_csv_as_str = data_articles.sort_values(
            'publication_date', ascending=False).head(1).iloc[0][3]  # 2020-02-28
        last_article_date_csv = datetime.strptime(last_article_date_csv_as_str, '%Y-%m-%d').date()
        logging.info('Most recent blog-post date is {}'.format(last_article_date_csv_as_str))
        logging.info('Looking for a new blog-posts . . .')
        article_info = response.css('div.cntt')
        new_articles_urls = []
        for element in article_info:
            try:
                date_str = element.css('div.viewauthor > div.authwrp > span::text').get()
                current_article_date = datetime.strptime(date_str, '%b %d, %Y').date()
                if current_article_date > last_article_date_csv:
                    new_articles_urls.append(element.css('h4 > a::attr(href)').get())
            except ValueError:
                pass

        logging.info('There is {counter} blog-posts were published since {last_date}'
                     .format(counter=len(new_articles_urls), last_date=last_article_date_csv_as_str))
        if len(new_articles_urls) is 0:
            self.close(self, reason='There is no new blog-posts')
        self.new_articles_len = len(new_articles_urls)
        for article_url in new_articles_urls:
            yield response.follow(article_url, self.parse_article)

    def parse_article(self, response):
        logging.info('Parsing article page [{current}/{all}] -> {url}'.format(current=self.new_article_counter,
                                                                              all=self.new_articles_len,
                                                                              url=response.url))
        self.new_article_counter += 1
        search_results = response.css('body > div#wrap')
        for article in search_results:
            title = str(article.css('div#postcontent > h1::text').get()).replace('\r', '').replace('\n', ' ')
            url = response.url
            text_raw_with_tags = article.css('div#postcontent > div#mypost').getall()
            text = ''
            for row in text_raw_with_tags:
                soup_raw = BeautifulSoup(row, features='lxml')
                text += soup_raw.get_text().strip()  # getting rid of html tags
                if len(text) > 160:
                    text = text[:161].replace('\r', '').replace('\n', ' ')
            publication_date_as_str = article.css('div#postcontent > div.no-mobile > '
                                                  'div.posttag.right.nomobile > span::text').get()
            publication_date = datetime.strptime(publication_date_as_str, '%b %d, %Y').date()
            authors = article.css('div#postcontent > div.no-mobile > '
                                  'div.postauthor.left > span > a.goauthor > span::text').getall()
            tags = response.css('ul#mainmenu > li.current > a::text').getall()

            with open(GDBlogCrawler.output_articles, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if len(tags) > len(authors):
                    for tag in tags:
                        for author in authors:
                            writer.writerow([title, url, text, publication_date, author, tag])
                else:
                    for author in authors:
                        for tag in tags:
                            writer.writerow([title, url, text, publication_date, author, tag])

            with open(GDBlogCrawler.output_authors, 'r') as f:
                reader = csv.reader(f)
                authors_csv = list(reader)

            with open(GDBlogCrawler.output_authors, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                looking_for = authors
                for author in authors_csv:
                    for target_author in looking_for:
                        if author[0] == target_author:
                            looking_for.remove(target_author)
                            author[4] = int(author[4]) + 1  # author[4] - 'articles_counter' field in csv
                if len(looking_for) is not 0:  # new author is present
                    for new_author in looking_for:
                        authors_csv.append([new_author, '', '', '', 1])
                writer.writerows(authors_csv)
