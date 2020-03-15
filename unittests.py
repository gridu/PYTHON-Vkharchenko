import unittest
import datetime
from scrapy.http import HtmlResponse
from gd_blog_spider.spiders.blog_check import BlogCheckSpider
from gd_blog_spider.spiders.blog_parse import GDBlogCrawler
from report import get_top5_articles_df


class SpiderTest(unittest.TestCase):

    def test_parse_article(self):
        """to emulate response from url with offline htm file we must pass all code of the page to response object"""
        with open(r'unittests_files/article_sample.htm') as f:
            body = f.read()  # reading htm file to get all html+css code
        response = HtmlResponse(
            url='https://blog.griddynamics.com/tiered-machine-learning-ranking-improves-relevance-for-the-retail-search/',
            body=body, encoding='utf-8')
        crawler = GDBlogCrawler()
        expected = ('Tiered machine learned ranking improves relevance for the retail search',
                    'https://blog.griddynamics.com/tiered-machine-learning-ranking-improves-relevance-for-the-retail-search/',
                    'Online retailers operating large catalogs are always looking to improve the quality of their product discovery functionality. Keyword search and category browse ',
                    datetime.date(2020, 3, 3),
                    ['Aleksandr Vasilev', 'Eugene Steinberg'],
                    ['Search', 'ML & AI', 'E-commerce'])
        self.assertEqual(crawler.parse_article(response, write_to_csv=False), expected)

    def test_get_last_publication_date(self):
        spider = BlogCheckSpider()
        self.assertEqual(spider.get_last_publication_date_from_csv(csv_path='unittests_files/articles_sample.csv'),
                         ('2020-03-03', datetime.date(2020, 3, 3)))  # function returns values as str and as datetime

    def test_get_top5_articles_df(self):
        df = get_top5_articles_df(csv_path='unittests_files/articles_sample.csv')
        expected = ['2020-03-03', '2020-02-28', '2020-02-22', '2020-02-18', '2020-02-11']
        self.assertEqual(df.publication_date.tolist(),
                         expected)


if __name__ == '__main__':
    unittest.main()


