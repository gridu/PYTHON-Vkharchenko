import csv
import logging
from datetime import datetime
from scrapy.spiders import CrawlSpider
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s', )

file_handler = logging.FileHandler('gd_blog_parser.log')
logging.getLogger().addHandler(file_handler)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler.setFormatter(formatter)


class GDBlogCrawler(CrawlSpider):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        logging.getLogger('scrapy').setLevel(logging.WARNING)

    name = 'blog_scraper'
    allowed_domains = ['blog.griddynamics.com']
    start_urls = [
        'https://blog.griddynamics.com/all-authors/'
    ]
    output_articles = 'articles.csv'
    output_authors = 'authors.csv'
    first_row_articles = True
    first_row_authors = True
    author_counter = 1
    authors_len = None
    articles_len = 0

    def parse_author(self, response):
        logging.info('Parsing author page [{current}/{all}] -> {url}'.format(current=self.author_counter,
                                                                             all=self.authors_len,
                                                                             url=response.url))
        self.author_counter += 1
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
            with open(self.output_authors, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if self.first_row_authors:
                    writer.writerow(['full_name', 'job_title', 'linkedin', 'contact', 'articles_counter'])
                    self.first_row_authors = False
                if len(contacts) is not 0:
                    for contact in contacts:
                        if len(linkedin) is 0:
                            writer.writerow([full_name, job_title, '', contact, articles_counter])
                        else:
                            writer.writerow([full_name, job_title, linkedin, contact, articles_counter])
                else:
                    if len(linkedin) is 0:
                        writer.writerow([full_name, job_title, '', '', articles_counter])
                    else:
                        writer.writerow([full_name, job_title, linkedin, '', articles_counter])

            author_articles = response.css('div#author > div#authorbox > did.postlist > a::attr(href)').getall()
            for article_url in author_articles:
                yield response.follow(article_url, self.parse_article)

    def parse_article(self, response, write_to_csv=True):
        self.articles_len += 1
        logging.info('Parsing article page -> {url}'.format(url=response.url))
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
            if write_to_csv:
                with open(self.output_articles, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if self.first_row_articles:
                        writer.writerow(['title', 'url', 'text', 'publication_date', 'author', 'tag'])
                        self.first_row_articles = False
                    if len(tags) > len(authors):
                        for tag in tags:
                            for author in authors:
                                writer.writerow([title, url, text, publication_date, author, tag])
                    else:
                        for author in authors:
                            for tag in tags:
                                writer.writerow([title, url, text, publication_date, author, tag])
            else:
                return title, url, text, publication_date, authors, tags

    def parse(self, response):
        logging.info('Getting urls to authors pages -> {url}'.format(url=response.url))
        authors_list = response.css('div#wrap > div.blog.list.authorslist > div.inner > '
                                    'div.row > div.left > div.single')
        logging.info('Urls collected. Starting iteration process . . .')
        counter = 0
        for author in authors_list:
            author_url = author.css('a.authormore::attr(href)').get()
            counter += 1
            yield response.follow(author_url, self.parse_author)
        lost_authors = ('/author/ezra/',
                        '/author/anton/',
                        '/author/pavel-vasilyev/')
        for url in lost_authors:
            counter += 1
            yield response.follow(url, self.parse_author)
        self.authors_len = counter

    def close(self, reason):
        logging.info('Spider closed. '
                     '{authors_len} Author(s) extracted to {authors_file}, '
                     '{articles_len} Article(s) extracted to {articles_file}.'
                     .format(authors_len=self.authors_len,
                             authors_file=self.output_authors,
                             articles_len=self.articles_len,
                             articles_file=self.output_articles))
