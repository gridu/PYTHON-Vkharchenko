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
    """This spider is used when some data already exists"""
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        logging.getLogger('scrapy').propagate = False  # disable default scrapy logger

    name = 'blog_check'
    allowed_domains = ['blog.griddynamics.com']
    start_urls = ['http://blog.griddynamics.com/explore/']
    blog_posts_dates = []
    new_articles_len = 0  # for console output of parsing process, e.g. 'parsing [1/2] articles'
    new_article_counter = 1  # same as above
    new_authors_len = 0  # same as above
    new_author_counter = 1  # same as above

    def get_last_publication_date_from_csv(self, csv_path=None):
        """Function to get last publication date from provided csv file"""
        if csv_path is None:
            data_articles = pd.read_csv('articles.csv')
        else:
            data_articles = pd.read_csv(csv_path)
        last_article_date_csv_as_str = data_articles.sort_values(
            'publication_date', ascending=False).head(1).iloc[0][3]  # e.g. 2020-02-28;
        '''iloc[m][n]: m - number of row, n - number of column'''
        last_article_date_csv = datetime.strptime(last_article_date_csv_as_str, '%Y-%m-%d').date()  # str to datetime
        return last_article_date_csv_as_str, last_article_date_csv

    def parse(self, response):
        """Function to get new blog-posts"""
        last_article_date_csv_as_str, last_article_date_csv = self.get_last_publication_date_from_csv()
        logging.info('Most recent blog-post date is {}'.format(last_article_date_csv_as_str))
        logging.info('Looking for a new blog-posts . . .')
        article_info = response.css('div.cntt')
        new_articles_urls = []
        for element in article_info:
            try:  # we are looking for date
                date_str = element.css('div.viewauthor > div.authwrp > span::text').get()
                current_article_date = \
                    datetime.strptime(date_str, '%b %d, %Y').date()  # trying to convert value to datetime
                if current_article_date > last_article_date_csv:
                    new_articles_urls.append(element.css('h4 > a::attr(href)').get())
            except ValueError:  # value is not convertable to datetime -> drop it
                pass

        logging.info('There is {counter} blog-posts were published since {last_date}'
                     .format(counter=len(new_articles_urls), last_date=last_article_date_csv_as_str))
        if len(new_articles_urls) is 0:
            self.close(self, reason='There is no new blog-posts')
        self.new_articles_len = len(new_articles_urls)
        for article_url in new_articles_urls:
            yield response.follow(article_url, self.parse_article)  # parsing each new article

    def parse_author(self, response):
        """Function to parse new author page and extract data to .csv file"""
        logging.info('Parsing author page [{current}/{all}] -> {url}'.format(current=self.new_author_counter,
                                                                             all=self.new_authors_len,
                                                                             url=response.url))
        self.new_author_counter += 1
        author_info = response.css('div#wrap > div#author > div#authorbox')
        for field in author_info:
            full_name = field.css('div.nomobile > div.right > h1::text').get()
            job_title = field.css('div.nomobile > div.right > h2::text').get()
            articles_counter = len(field.css('did.postlist > a::text').getall())
            all_urls = field.css('div.mobile > div.right > div.authorsocial > a::attr(href)').getall()
            linkedin = []
            contacts = []
            for url in all_urls:
                if 'linkedin' in url:
                    linkedin = url
                else:
                    contacts.append(url)
            with open(GDBlogCrawler.output_authors, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if len(contacts) is not 0:
                    for contact in contacts:
                        if len(linkedin) is 0:
                            writer.writerow([full_name, job_title, '', contact, articles_counter])
                            # if cell is empty default value is NaN. replacing NaN with empty symbol here and below
                        else:
                            writer.writerow([full_name, job_title, linkedin, contact, articles_counter])
                else:
                    if len(linkedin) is 0:
                        writer.writerow([full_name, job_title, '', '', articles_counter])
                    else:
                        writer.writerow([full_name, job_title, linkedin, '', articles_counter])

    def parse_article(self, response):
        """Function to parse new article page and extract data to .csv file"""
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
                if len(text) > 160:  # according to task text must be truncated to 160 symbols
                    text = text[:161].replace('\r', '').replace('\n', ' ')
            publication_date_as_str = article.css('div#postcontent > div.no-mobile > '
                                                  'div.posttag.right.nomobile > span::text').get()
            publication_date = datetime.strptime(publication_date_as_str, '%b %d, %Y').date()
            authors = article.css('div#postcontent > div.no-mobile > '
                                  'div.postauthor.left > span > a.goauthor > span::text').getall()
            tags = response.css('ul#mainmenu > li.current > a::text').getall()
            author_url = article.css('div#postcontent > div.no-mobile > '
                                     'div.postauthor.left > span > a::attr(href)').getall()
            authors_with_urls = dict(zip(authors, author_url))
            with open(GDBlogCrawler.output_articles, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if len(tags) > len(authors_with_urls.keys()):
                    for tag in tags:
                        for author in authors_with_urls.keys():
                            writer.writerow([title, url, text, publication_date, author, tag])
                else:
                    for author in authors_with_urls.keys():
                        for tag in tags:
                            writer.writerow([title, url, text, publication_date, author, tag])

            with open(GDBlogCrawler.output_authors, 'r') as f:
                reader = csv.reader(f)
                authors_csv = list(reader)

            with open(GDBlogCrawler.output_authors, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                looking_for = list(authors_with_urls.keys())
                author_index = 0
                for author in authors_csv:
                    for target_author in looking_for:
                        if author[0] == target_author:
                            del authors_with_urls[target_author]
                            author[4] = int(author[4]) + 1  # author[4] - 'articles_counter' field in csv
                        author_index += 1
                if len(looking_for) is not 0:  # new author(s) is present
                    self.new_authors_len = len(looking_for)
                    for new_author_url in authors_with_urls.values():
                        yield response.follow(new_author_url, self.parse_author)
                writer.writerows(authors_csv)
