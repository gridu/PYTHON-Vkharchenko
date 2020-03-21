# Parse GridDynamics Blog with Scrapy and visualize it
This application is a Web Crawler for GridDynamics blog.
Main task is to obtain information and generate a report with:
* Top-5 Authors,
* Top-5 New Articles,
* Plot with articles counter of 7 most popular tags
# How to
*Important: all commands described below highly recommended to be executed from the root directory of the project (file that you're currently viewing placed right here)*
### Setup and configure crawler
* Run ```source install.sh``` to create virtualenv and install all dependencies. Virtualenv becomes active automatically.
### Start crawler and get report
* Run ```python3 report.py```
### Run unittests
* [Setup and configure parser](https://github.com/gridu/PYTHON-Vkharchenko#setup-and-configure-crawler)
* Run ```python3 unittests.py```
