import requests
from bs4 import BeautifulSoup
import pandas as pd
import argparse

def get_next_url(url):
    # returns the url of the next page in your search
    result = requests.get(url)
    src = result.content
    soup = BeautifulSoup(src, features="html.parser")
    next_url = soup.find('a', class_="next_page button button--primary")
    if next_url is not None:
        next_url = 'https://hemnet.se/' + next_url.attrs['href']
    return next_url

def get_search_urls(url):
    # returns the urls for all the objects in a search
    result = requests.get(url)
    src = result.content
    soup = BeautifulSoup(src, features="html.parser")

    urls = []
    for li_tag in soup.find_all('li'):
        for div_tag in li_tag.find_all('div'):
            a_tag = div_tag.find('a')
            if a_tag != None:
                urls.append(a_tag.attrs['href'])

    urls = [x for x in urls if x.startswith("https://www.hemnet.se/")]
    return urls

def scrape(urls):
    # scrapes a set of objects at locations passed through "urls"
    # returns all the data from a search page in a dictionary
    all_values = {url : {c : '' for c in columns} for url in urls}
    
    for url in urls:
    
        result = requests.get(url)
        src = result.content
        soup = BeautifulSoup(src, features="html.parser")
        
        for a in soup.find_all(['dt','dd']):
            if a.attrs['class'][0] == "sold-property__attribute":
                temp_key = a.contents[0]
                if temp_key == 'Prisutveckling':
                    continue
            elif a.attrs['class'][0] == "sold-property__attribute-value" and temp_key != 'Prisutveckling':
                all_values[url][temp_key] = a.contents[0].strip(' kr').strip(' kr/m²').strip(' rum')\
                                         .strip(' kr/mån').strip(' kr/å').strip('\n').replace(u"\xa0", "").replace(',', '.')
                
        # Gets the closing price 
        closing_price = soup.find_all('span', class_="sold-property__price-value")
        closing_price = closing_price[0].contents[0].strip(' kr').replace(u"\xa0", "")
        all_values[url]['Slutpris'] = closing_price
                
        # Gets the time of sale
        time = soup.find('time').contents[0].strip('\n').strip('\n    ')
        all_values[url]['Datum'] = time
        
        # Gets the location of object
        area = soup.find("p").find("span") \
            .next_sibling \
            .strip("- Såld den\n    ") \
            .strip("Bostadsrättslägenhet - \n\n") \
            .strip("Andel i bostadsförening -\n\n") \
            .strip(',')
        all_values[url]['Område'] = area
        
    return all_values

def execute(search, nbr_pages):
    # Loops through a set number of pages specified by users or until end
    # returns a dictionary of ALL scraped objects
    current_search_page = search
    i = 0
    first = True
    while get_next_url(current_search_page) is not None:
        
        if i > nbr_pages:
            break
        
        current_search_page = get_next_url(current_search_page)
        
        urls = get_search_urls(current_search_page)
        
        print("Scraping page: ", i)
        temp = scrape(urls)
        
        if first != False:
            hemnet = temp
            first = False
        else:
            hemnet.update(temp)

        i += 1
    return hemnet

parser = argparse.ArgumentParser()

#-d DESTINATION -s SEARCH-URL -p "NUMBER OF PAGES
parser.add_argument("-d", "--destination", help="Destination", type=str, default='hemnet.csv')
parser.add_argument("-s", "--search", help="Search-url", 
                    default='https://www.hemnet.se/salda/bostader?item_types%5B%5D=bostadsratt&location_ids%5B%5D=473362&location_ids%5B%5D=898472&location_ids%5B%5D=473448&location_ids%5B%5D=925970&location_ids%5B%5D=925969&location_ids%5B%5D=925968&page=1&sold_age=all',
                    type=str)
parser.add_argument("-p", "--pages", help="Number of pages", type=int, default=5)

args = parser.parse_args()

search = args.search 
dest = args.destination
nbr_pages = args.pages

columns = [
        'Datum',
        'Område',
        'Pris per kvadratmeter',
        'Begärt pris',
        'Antal rum',
        'Boarea',
        'Avgift/månad',
        'Driftskostnad',
        'Byggår',
        'Slutpris',
        'Biarea'
        ]

hemnet = execute(search, nbr_pages)

df = pd.DataFrame.from_dict(hemnet, orient='index', columns=columns).reset_index()
df.to_csv(dest)
print('Scraped to:', dest)

