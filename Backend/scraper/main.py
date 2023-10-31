import asyncio
import json
import os
import pickle
import time
import sys
from utils import *

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException

from webdriver_manager.chrome import ChromeDriverManager

SHOPEE = "https://shopee.vn/"
AMAZON = "https://www.amazon.com/"

URLS = {
    SHOPEE: {
        "search_field_query": 'input.shopee-searchbar-input__input',
        "search_button_query": 'button.shopee-searchbar__search-button',
        "product_selector": 'div.shopee-search-item-result__item'
    },
    AMAZON: {
        "search_field_query": 'input[name="field-keywords"]',
        "search_button_query": 'input[value="Go"]',
        "product_selector": "div.s-card-container"
    }
}

available_urls = URLS.keys()

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def load_auth():
    options = Options()
    # options.add_argument("start-maximized")
    # options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def search(metadata, page, search_text):
    print("Searching for {search_text} on {page}")
    search_field_query = metadata.get("search_field_query")
    search_button_query = metadata.get("search_button_query")
    
    if search_field_query and search_button_query:
        print("Filling input field")
        WebDriverWait(driver, 50).until(EC.visibility_of_element_located((By.CSS_SELECTOR, search_field_query)))
        WebDriverWait(driver, 50).until(EC.visibility_of_element_located((By.CSS_SELECTOR, search_button_query)))
        
        driver.execute_script('''document.querySelector("div.home-page").remove();''')
        
        search_box = driver.find_element(By.CSS_SELECTOR, search_field_query)
        search_box.send_keys(search_text)
        
        print("Pressing search button")
        button = driver.find_element(By.CSS_SELECTOR, search_button_query)
        button.click()
    else:
        raise Exception("Could not search")
    
    
def get_products(search_text, selector, get_product)    :
    print("Retrieving products..")
    valid_products = []
    words = search_text.split(" ")    
    WebDriverWait(driver, 50).until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
    product_divs = driver.find_elements(By.CSS_SELECTOR, selector)
    slow_scrolling()
    
    for div in product_divs:
        product = get_product(div)
        if product != {}:
            for word in words:
                if word.lower() in product['name'].lower():
                    valid_products.append(product)
                    break
    print(len(valid_products))
    return valid_products        
        
        
def get_product(div):
    try:
        info_element = div.find_element(By.CSS_SELECTOR, "div.KMyn8J")
        image_element = div.find_element(By.CSS_SELECTOR, "div.yvbeD6.KUUypF img")
        url = div.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
        
        info_child = info_element.find_elements(By.XPATH, "*")
        image_url = image_element.get_attribute("src")
        infos = []
        for c in info_child:
            infos.append(c.text)
        
        price = handle_price(infos[1])
        name = handle_name(infos[0])
        result = {"img": image_url, "name": name, "price_lower": float(price[0]), 'price_upper': float(price[-1]), "url": url}
        return result
    except NoSuchElementException:
        return {}
    
        
def save_cookies(page):
    driver.get(page)
    try:
        cookies = pickle.load(open(os.path.join(__location__, "cookies.pkl"), 'rb'))
        for cookie in cookies:
            print(cookie)
            driver.add_cookie(cookie)
    except IOError:
        input("Login to retrieve new cookie....")
        input("Press enter when done.")
        pickle.dump(driver.get_cookies(), open(os.path.join(__location__, "cookies.pkl"), 'wb'))
    
    driver.get(page)


def slow_scrolling():
    total_page_height = driver.execute_script("return document.body.scrollHeight")
    browser_window_height = driver.get_window_size(windowHandle='current')['height']
    current_position = driver.execute_script('return window.pageYOffset')
    while total_page_height - current_position - 1000 > browser_window_height:
        driver.execute_script(f"window.scrollTo({current_position}, {browser_window_height + current_position});")
        current_position = driver.execute_script('return window.pageYOffset')
        time.sleep(.1)  # It is necessary here to give it some time to load the content

        
def main(url, search_text, response_route, product_filter=" "):
    metadata = URLS.get(url)
    if not metadata:
        print("Invalid URL.")
        return
    print("Connecting to browser..")
    
    save_cookies(url)
    search(URLS.get(SHOPEE), SHOPEE, search_text)
    results = get_products(product_filter, metadata["product_selector"], get_product)
    
    print("Saving results...")
    post_results(results=results, endpoint=response_route, search_text=search_text, source=url)
    # save_results(results)
        
        
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: python -m package_name url search_text endpoint')
        # sys.exit(1)
        
        url = SHOPEE
        search_text = "keycap"
        endpoint = "test"
    else:
        url = sys.argv[1]
        search_text = sys.argv[2]
        endpoint = sys.argv[3]
        
    driver = load_auth()
    main(url, search_text, endpoint)