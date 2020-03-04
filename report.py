import shlex  # Lexical analysis of shell-style syntaxes
import subprocess
import os
import logging

logging.getLogger().addHandler(logging.FileHandler('gd_blog_parser.log'))
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s',)


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


def generate_report():
    pass


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
        pass
    else:
        logging.fatal('Script execution has been stopped because of error')

