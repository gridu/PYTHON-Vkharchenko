import unittest
import datetime
from scrapy.http import HtmlResponse
from gd_blog_spider.spiders.blog_check import BlogCheckSpider
from gd_blog_spider.spiders.blog_parse import GDBlogCrawler


class SpiderTest(unittest.TestCase):

    def test_parse_article(self):
        with open(r'unittests_files/article_sample.htm') as f:
            body = f.read()
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
                         ('2020-03-03', datetime.date(2020, 3, 3)))

    def test_get_top5_articles(self):
        pass


if __name__ == '__main__':
    unittest.main()


