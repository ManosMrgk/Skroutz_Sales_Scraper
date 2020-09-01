from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import json
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')


def price_to_num(price_str):
    if len(price_str.split('.')) > 1:
        split_thousands = price_str.split('.')
        split_thousands[1] = (split_thousands[1].split(',')[0] + '.' + split_thousands[1].split(',')[1]).split()[0]
        return float(split_thousands[0] + split_thousands[1])
    else:
        return float((price_str.split(',')[0] + '.' + price_str.split(',')[1]).split()[0])

def sale_to_num(sale_str):
    return float(sale_str.split('-')[1].split('%')[0] + '.')


def starting_price(sale_percentage, discount_price):
    decimal = (100.0 - sale_percentage) / 100.0
    return round(discount_price / decimal, 2)


PATH = "C:\Program Files (x86)\chromedriver.exe"
driver = webdriver.Chrome(PATH,options=options)
url = "https://www.skroutz.gr/"
driver.get(url)
search = driver.find_element_by_id("search-bar-input")
search_terms = str(input("What are you looking for?\n"))
if input("Want to set the max number of result pages to search? [yes/no]:") == "yes":
    max_pages = int(input("Max number of pages to search:"))
else:
    max_pages = 2
#max_pages = 10
if input("Want to set lowest price? [yes/no]:") == "yes":
    lowest_price = int(input("Enter lowest price:"))
else:
    lowest_price = 0
search.send_keys(search_terms)
search.send_keys(Keys.RETURN)

try:
    main = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.TAG_NAME, "main"))
    )
    content_type = main.get_attribute("class")
except NoSuchElementException:
    driver.quit()

if content_type == "content":
    ul_list = driver.find_elements_by_tag_name("ul")[2]
    category_list = ul_list.find_elements_by_tag_name("li")

    for num, category in enumerate(category_list):
        print(num, "-", category.text)
    wanted_category = int(input('Choose a category from 0 to ' + str(len(category_list) - 1) + ':'))
    # wanted_category = 1
    category_list[wanted_category].click()

    try:
        main = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.TAG_NAME, "main"))
        )
    except NoSuchElementException:
        driver.quit()
    # driver.quit()

current_url = driver.current_url
biggest_discount = 0
before_discount = 0
after_discount = 0
discount_name = ""
discount_url = ""
cheapest = ""
cheapest_url = ""
cheapest_price = -1
page = 1
while page <= max_pages:
    try:
        search_results = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.ID, "sku-list"))
        )
    except NoSuchElementException:
        driver.quit()

    items_list = search_results.find_elements_by_tag_name("li")
    for item in items_list:
        if item.get_attribute("class") != "cf card with-skus-slider" and item.get_attribute("class") != "cf card" and item.get_attribute("class") != "card":
            continue
        if item.get_attribute("class") == "card":
            header = item.find_element_by_css_selector(".pic")
            specs = item.find_element_by_css_selector(".specs")
            price = item.find_element_by_css_selector(".product-link")
        else:
            header = item.find_element_by_css_selector(".js-sku-link")
            price = item.find_element_by_css_selector(".js-sku-link.sku-link")
        if (cheapest_price == -1 or cheapest_price > price_to_num(price.text)) and price_to_num(price.text) > lowest_price:
            cheapest_price = price_to_num(price.text)
            cheapest = header.get_attribute("title")
            cheapest_url = header.get_attribute("href")
        sale = item.find_elements_by_css_selector(".pricedrop.low")
        print(header.get_attribute("title"))
        if item.get_attribute("class") == "card":
            print(specs.text)
        if sale:
            print("SALE:", sale_to_num(sale[0].text), '%', "Was:", starting_price(sale_to_num(sale[0].text), price_to_num(price.text)), "€")
            if starting_price(sale_to_num(sale[0].text), price_to_num(price.text)) - price_to_num(price.text) > biggest_discount and price_to_num(price.text) > lowest_price:
                before_discount = starting_price(sale_to_num(sale[0].text), price_to_num(price.text))
                after_discount = price_to_num(price.text)
                biggest_discount = starting_price(sale_to_num(sale[0].text), price_to_num(price.text)) - price_to_num(price.text)
                discount_name = header.get_attribute("title")
                discount_url = item.find_element_by_css_selector(".js-sku-link").get_attribute("href")
        print(price_to_num(price.text), "€")
    driver.get(current_url + "&page=" + str(page))
    page += 1
with open('products.json', 'r') as json_file:
    data = json.load(json_file)
    products = []
    for p in data['Products']:
        products.append(p)
if cheapest != "":
    print("Cheapest item:", cheapest, cheapest_price, "€")
    print(cheapest_url)
    cheapest_item = {
            "name" : cheapest,
            "price" : cheapest_price,
            "prev_price" : "-",
            "link" : cheapest_url
        }
    if cheapest_item not in products:
        products.append(cheapest_item)
else:
    print("Could not find an item with those filters")
if discount_name != "":
    print("Most discounted item:", discount_name)
    print(discount_url)
    driver = webdriver.Chrome(PATH)
    driver.get(discount_url)
    most_discounted_item = {
            "name": discount_name,
            "price": after_discount,
            "prev_price": before_discount,
            "link": discount_url
        }
    if most_discounted_item not in products:
        products.append(most_discounted_item)
with open('products.json', 'w') as json_file:
    data = {}
    data["Products"] = []
    data["Products"] = products
    json.dump(data, json_file, sort_keys=True, indent=4)
