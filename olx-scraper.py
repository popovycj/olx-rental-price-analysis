import time
import requests
import json
import random as r
# from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import csv
import multiprocessing
from seleniumwire import webdriver
import datetime


class OlxCrawler:
  CURRENT_TIME = datetime.datetime.now()
  CURRENT_INDEX = 0

  PROXIES = [
    None,
    'http://kGfpv0:QQajVu@46.3.145.14:8000',
    'http://kGfpv0:QQajVu@46.3.145.178:8000',
    'http://3jeg3M:wG0e86@91.218.51.251:9132',
  ]

  def __init__(self, proxy=None):
    # self.headers = { 'User-Agent': UserAgent().chrome }
    self.driver = self._set_up_driver(proxy)


  def _set_up_driver(self, proxy=None):
    service = Service(executable_path=ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument(f'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    # chrome_options.add_argument("--window-size=1920,1200")
    chrome_options.add_argument("--headless")

    if proxy:
      seleniumwire_options = {
          'proxy': {
              'http': proxy,
              'verify_ssl': False,
          },
      }
      return webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=seleniumwire_options)
    return webdriver.Chrome(service=service, options=chrome_options)



  @staticmethod
  def save_csv(options, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=options[0].keys())
        writer.writeheader()
        for option in options:
            writer.writerow(option)

  @staticmethod
  def read_csv(filename):
    with open(filename, newline='') as csvfile:
      reader = csv.DictReader(csvfile)
      data = [row for row in reader]
    return data


  def get_regions_data(self):
    regions = []

    for region_id in range(1, 26):
      region_shortcut = json.loads(requests.get(
        "https://www.olx.ua/api/v1/friendly-links/create-url/",
        params={ "region_id": region_id },
        headers=self.headers
      ).content)['data']['path'][-1]

      region_name = json.loads(requests.get(
        f'https://www.olx.ua/api/v1/geo-encoder/regions/{region_id}/',
        headers=self.headers
      ).content)['data']['name']

      regions.append({
        'id': region_id,
        'shortcut': region_shortcut,
        'name': region_name,
        'url': f"https://www.olx.ua/d/uk/nedvizhimost/kvartiry/dolgosrochnaya-arenda-kvartir/{region_shortcut}/"
      })

    return regions


  def get_houses_links(self, region):
    houses_links = set()
    url = region['url']
    page = 1

    while url:
      self.driver.get(url)
      time.sleep(r.randint(1, 2))
      soup = BeautifulSoup(self.driver.page_source, 'lxml')

      try:
        links = ['https://www.olx.ua' + tag.find('a')['href'] for tag in soup.find_all('div', {'data-cy': 'l-card'})]
        houses_links.update(links)
        print(f'{len(links)} links from "{region["name"]}" {page}th page')
        print('*' * 100)
      except Exception as e:
        print(e)
        print('*' * 100)

      try:
        url = 'https://www.olx.ua' + soup.find('a', {'data-testid': 'pagination-forward'})['href']
        page += 1
      except Exception as e:
        url = None
        print(e)
        print('*' * 100)

    return houses_links


  def get_house_data(self, region, url):
    self.driver.get(url)
    time.sleep(r.random())

    while "ERROR: The request could not be satisfied" in self.driver.page_source and "403 ERROR" in self.driver.page_source:
      print('ERROR')
      self.define_proxy()
      time.sleep(r.randint(30, 60))
      self.driver.refresh()
    else:
      print("No errors found.")

    soup = BeautifulSoup(self.driver.page_source, 'lxml')

    print('=' * 100)
    print('=' * 100)
    print(url)

    try:
      title = soup.find('h1', {'data-cy': 'ad_title'}).text
      # print(title)
      # print('*' * 100)
    except Exception as e:
      title = 'None'
      print('title ||' + str(e))
      print('*' * 100)

    try:
      price = soup.find('div', {'data-testid': 'ad-price-container'}).find('h3').text
      if 'грн.' in price:
        price = float(price.replace(' ', '').replace('грн.', ''))
        price_currency = 'UAH'
      elif '$' in price:
        price = float(price.replace(' ', '').replace('$', ''))
        price_currency = 'USD'
      elif '€' in price:
        price = float(price.replace(' ', '').replace('€', ''))
        price_currency = 'EUR'
      else:
        price = price.replace(' ', '')
      # print(f'{price} {price_currency}')
      # print('*' * 100)
    except Exception as e:
      price = 'None'
      price_currency = 'None'
      print('price ||' + str(e))
      print('*' * 100)

    try:
      description = soup.find('div', {'data-cy': 'ad_description'}).find('div').text
      # print(description)
      # print('*' * 100)
    except Exception as e:
      description = 'None'
      print('description ||' + str(e))
      print('*' * 100)

    try:
      views_count = int(soup.find('span', {'data-testid': 'page-view-text'}).text.split()[-1])
      # print(views_count)
      # print('*' * 100)
    except Exception as e:
      views_count = 'None'
      print('views_count ||' + str(e))
      print('*' * 100)

    try:
      created_at = soup.find('span', {'data-cy': 'ad-posted-at'}).text
      # print(created_at)
      # print('*' * 100)
    except Exception as e:
      created_at = 'None'
      print('created_at ||' + str(e))
      print('*' * 100)

    try:
      options = [li.find('p').text for li in soup.find('div',{'id': 'baxter-above-parameters'}).find_next('ul').find_all('li')]
      # print(options)
      # print('*' * 100)
    except Exception as e:
      options = 'None'
      print('options ||' + str(e))
      print('*' * 100)

    try:
      location = soup.find('p', text=region).find_previous('p').text.strip(', ')
      # print(location)
      # print('*' * 100)
    except Exception as e:
      location = 'None'
      print('location ||' + str(e))
      print('*' * 100)

    try:
      seller_link = soup.find('a', {'data-testid': 'user-profile-link'})['href']
      if seller_link.startswith('/d'):
        seller_link = 'https://www.olx.ua' + seller_link
      # print(seller_link)
      # print('*' * 100)
    except Exception as e:
      seller_link = 'None'
      print('seller_link ||' + str(e))
      print('*' * 100)

    try:
      seller_name = soup.find('a', {'data-testid': 'user-profile-link'}).find('h4').text.strip()
      # print(seller_name)
      # print('*' * 100)
    except Exception as e:
      seller_name = 'None'
      print('seller_name ||' + str(e))
      print('*' * 100)

    try:
      seller_registration_date = soup.find('a', {'data-testid': 'user-profile-link'}).find('b').text.strip()
      # print(seller_registration_date)
      # print('*' * 100)
    except Exception as e:
      seller_registration_date = 'None'
      print('seller_registration_date ||' + str(e))
      print('*' * 100)

    with open('data.csv', 'a', newline='') as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow([
        title, price, price_currency, description, views_count, created_at, str(options), location, region, seller_name, seller_registration_date, seller_link, url
      ])

  @classmethod
  def define_proxy(cls):
    if datetime.datetime.now() - cls.CURRENT_TIME > datetime.timedelta(seconds=15):
      cls.CURRENT_INDEX += 1
      if cls.CURRENT_INDEX >= len(cls.PROXIES):
        cls.CURRENT_INDEX = 0
    cls.CURRENT_TIME = datetime.datetime.now()
    print(f"NEW PROXY: {cls.PROXIES[cls.CURRENT_INDEX]}")
    return cls.PROXIES[cls.CURRENT_INDEX]


def process_house(index, house):
    try:
      proxy = OlxCrawler.define_proxy()
      olx = OlxCrawler(proxy)
      olx.get_house_data(house['Region name'], house['Announcement Link'])
    except Exception as e:
      print('GENERAL ERROR' + str(e))
    print(f'Processed {index}th house')


if __name__ == '__main__':
  # olx = OlxCrawler()
  # regions = olx.get_regions_data()
  # print(regions)
  # print('*' * 100)

  # houses_links = []
  # for region in regions:
  #   links = olx.get_houses_links(region)
  #   houses_links.extend([{'Region name': region['name'], 'Announcement Link': link} for link in links])
  #   print(f'Generally {len(links)} links from {region["name"]}')
  #   print('*' * 100)
  #   print('*' * 100)

  # print(houses_links)

  # olx.save_csv(houses_links, 'announcements_links.csv')

  data = OlxCrawler.read_csv('announcements_links.csv')

  # with open('data.csv', 'w', newline='') as csvfile:
  #     writer = csv.writer(csvfile)
  #     writer.writerow([
  #       'title', 'price', 'price_currency', 'description', 'views_count', 'created_at', 'options', 'location', 'region', 'seller_name', 'seller_registration_date', 'seller_link', 'announcement_link'
  #     ])

  # test_count = 20

  # while test_count > 0:
  #   house_data = data[r.randint(100, 10000)]
  #   olx.get_house_data(house_data['Region name'], house_data['Announcement Link'])
  #   test_count -= 1

# htmls = []

# for index, house in enumerate(data[2968:]):
#   try:
#     # olx.get_house_data(house['Region name'], house['Announcement Link'])
#     htmls.append(olx.get_html(house['Region name'], house['Announcement Link']))
#   except Exception as e:
#     print('GENERAL ERROR' + str(e))
#   print(f'Processed {index}th house')

  pool = multiprocessing.Pool(processes=4)
  results = [pool.apply_async(process_house, args=(index, house)) for index, house in enumerate(data[9464:], 9464)]
  pool.close()
  pool.join()

  # olx = OlxCrawler()
  # olx.driver.get('https://whatismyipaddress.com/')
  # time.sleep(60)

  # print(olx.get_html('', 'https://www.olx.ua/d/uk/obyavlenie/orenda-3-km-kvartiri-vul-b-hmelnitskogo-IDRyvVh.html'))

  # olx = OlxCrawler('http://F01j2r:ALKhMa@85.195.81.169:11791')
  # olx.driver.get('https://www.olx.ua/d/uk/obyavlenie/orenda-3-km-kvartiri-vul-b-hmelnitskogo-IDRyvVh.html')
  # time.sleep(60)
