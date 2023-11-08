
from typing import Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime  # Import datetime module

# Your webdriver path and Chrome options
webdriver_path = r'C:\Users\jenne\Desktop\chromedriver_win32\chromedriver.exe'
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument(f"webdriver.chrome.driver={webdriver_path}")

# Connect to MongoDB
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Graph']

def scrape_product_price(url, product_id):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # Implement your scraping logic here to get the new price
    # For example, find the original and discounted price elements and extract the price values
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    original_price_element = soup.find('span', class_='price').find('bdi')
    original_price = original_price_element.text.strip() if original_price_element else ''

    # You can similarly scrape the discounted price if it's available on the page

    driver.quit()

    # Update the product in MongoDB with the new price and date scraped
    current_date = datetime.utcnow().isoformat()  # Get the current date in ISO format
    

    # Prepare the update data
    update_data = {
        "$set": {
            "original_price": original_price,
        },
        "$push": {
            "price_history": {
                "price": original_price,
                "date_scraped": current_date
            }
        }
    }

    # Update the product in MongoDB based on the product_id
    collection.update_one({"id": product_id}, update_data)

# URLs and corresponding product IDs
url_to_product_id = {
    'https://shopmetro.ph/marketmarket-supermarket/product/great-taste-white-twin-pack-50g/': '64e08a61536ea90428262b3d',
    'https://shopmetro.ph/marketmarket-supermarket/product/lucky-me-pancit-canton-kalamansi-80g/': '64e08ae2536ea90428262b8e',
    'https://shopmetro.ph/marketmarket-supermarket/product/gardenia-regular-slice-600g/': '64e08ca4536ea90428262cbc',
    'https://shopmetro.ph/marketmarket-supermarket/product/bear-brand-adult-plus-300g/': '64e089c6536ea90428262ad7',
    # Add more URLs and corresponding product IDs as needed
}

# Loop through the URLs and scrape/update the prices
for url, product_id in url_to_product_id.items():
    scrape_product_price(url, product_id)
