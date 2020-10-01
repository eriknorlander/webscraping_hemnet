FROM python:3.7

WORKDIR /app

RUN pip install pandas beautifulsoup4 requests

ADD scrape_hemnet.py scrape_hemnet.py

CMD [ "python", "scrape_hemnet.py", "-d", "'test.csv'", "-p", "5"]