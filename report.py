import shlex  # Lexical analysis of shell-style syntaxes
import subprocess
import os
import logging
import pandas as pd
from matplotlib import pyplot as plt

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s', )

file_handler = logging.FileHandler('gd_blog_parser.log')
logging.getLogger().addHandler(file_handler)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler.setFormatter(formatter)


def run_command(command):
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:  # poll() reads a line from the stdout (None if still running)
            break
        if output:
            print(output.strip())
    rc = process.poll()  # returns 'return code' cuz process is completed
    return rc


def get_data():
    logging.info('Getting data for the report . . .')
    articles = pd.read_csv('articles.csv')

    big_data = len(articles[articles.tag == 'Big Data'].drop_duplicates('title'))
    data_science = len(articles[articles.tag == 'Data Science'].drop_duplicates('title'))
    devops = len(articles[articles.tag == 'DevOps'].drop_duplicates('title'))
    e_commerce = len(articles[articles.tag == 'E-commerce'].drop_duplicates('url'))
    ml_ai = len(articles[articles.tag == 'ML & AI'].drop_duplicates('title'))
    mobile = len(articles[articles.tag == 'Mobile'].drop_duplicates('title'))
    qa = len(articles[articles.tag == 'QA'].drop_duplicates('title'))
    search = len(articles[articles.tag == 'Search'].drop_duplicates('title'))
    ui = len(articles[articles.tag == 'UI'].drop_duplicates('title'))
    tag_len_all = {'Big Data': big_data, 'Data Science': data_science, 'DevOps': devops, 'E-commerce': e_commerce,
                   'ML & AI': ml_ai, 'Mobile': mobile, 'QA': qa, 'Search': search, 'UI': ui}
    tag_len_all = {k: v for k, v in sorted(tag_len_all.items(), key=lambda item: item[1], reverse=True)}
    tag_len_top7 = dict(list(tag_len_all.items())[:7])

    x = range(7)
    plt.figure(figsize=(9, 5))
    rects = plt.bar(x, tag_len_top7.values())
    plt.xticks(x, tag_len_top7.values(), rotation='horizontal')
    plt.yticks([], [])
    plt.title('Tags')
    plt.xlabel('Articles counter')

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its title."""
        for rect, key in zip(rects, tag_len_top7.keys()):
            height = rect.get_height()
            plt.annotate('{}'.format(key),
                         xy=(rect.get_x() + rect.get_width() / 2, height),
                         xytext=(0, 3),  # 3 points vertical offset
                         textcoords="offset points",
                         ha='center', va='bottom')

    autolabel(rects)
    plt.tight_layout()
    authors = pd.read_csv('authors.csv')
    pd.set_option("display.max_colwidth", 10000)
    top5_authors = authors.sort_values('articles_counter', ascending=False).drop_duplicates('full_name').head(5)
    top5_authors_file = top5_authors.to_string(index=False, na_rep='')

    top5_articles = articles.sort_values('publication_date', ascending=False).drop_duplicates('url').head(5)
    top5_articles_file = top5_articles.to_string(index=False, na_rep='')
    pd.set_option("display.max_colwidth", 30)
    top5_authors_console = '\n\n' + top5_authors.to_string(index=False, na_rep='') + '\n'
    top5_articles_console = '\n\n' + top5_articles.to_string(index=False, na_rep='') + '\n'
    return plt, top5_articles_console, top5_authors_console, top5_articles_file, top5_authors_file


def generate_report(plt, art_cons, auth_cons, art_file, auth_file):
    logging.info('Generating the report . . .')
    plt.savefig('top7tags.png', dpi=100)
    logging.info('To continue close pop-up window')
    plt.show()
    logging.info('Top-5 Authors (based on articles counter)')
    logging.info(auth_cons)
    logging.info('Top-5 New Articles (based on publish data)')
    logging.info(art_cons)
    logging.info('Short-form reports displayed above in the console.\n'
                 '\t\t\t\tLong-form reports saved to the current directory:\n'
                 '\t\t\t\t\t\t-> top5articles.txt\n'
                 '\t\t\t\t\t\t-> top5authors.txt\n'
                 '\t\t\t\t\t\t-> top7tags.png\n')

    with open('top5authors.txt', mode='w', newline='', encoding='utf-8') as f:
        f.writelines(auth_file)

    with open('top5articles.txt', mode='w', newline='', encoding='utf-8') as f:
        f.writelines(art_file)


if __name__ == "__main__":
    logging.info('Script started')
    logging.info('Checking if file with data already exists . . .')
    if os.path.isfile('authors.csv') and os.path.isfile('articles.csv'):  # data exists
        logging.info('Data exists. Getting most recent blog-post date . . .')
        return_code = run_command('scrapy crawl blog_check --nolog')
    else:
        logging.info('Data does not exists. Starting spider . . .')
        return_code = run_command('scrapy crawl blog_scraper --nolog')
    if return_code is 0:
        plt, art_cons, auth_cons, art_file, auth_file = get_data()
        generate_report(plt, art_cons, auth_cons, art_file, auth_file)
    else:
        logging.fatal('Script execution has been stopped because of error')

