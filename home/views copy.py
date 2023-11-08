from typing import Any
from django.shortcuts import render
import random
from pymongo import MongoClient
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import re
import json
import logging


# Connect to MongoDB
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Graph']



def home(request):
    product_details_list = {}
     # Fetch data from MongoDB
    categories = collection.distinct('category')
    for category in categories:
        products = collection.find({'category': category})
        product_details_list[category] = list(products)

    # Create a list to store the randomly selected products
    random_shopmetro = []
    random_waltermart = []
    random_puregold = []
    # Loop through the categories and select a random product from each category
    for category, products in product_details_list.items():
        if products:
            random_products = random.sample(products, 5)  # Select 4 random products
            for product in random_products:
                if product['supermarket'] == 'ShopMetro':
                    random_shopmetro.append(product)
                elif product['supermarket'] == 'WalterMart':
                    random_waltermart.append(product)
                elif product['supermarket'] == 'Puregold':
                    random_puregold.append(product)

    # Shuffle the lists to randomize their order
    random.shuffle(random_shopmetro)
    random.shuffle(random_waltermart)
    random.shuffle(random_puregold)
 
    random_discount = []
    random.shuffle(random_discount)
    random_discount = random_discount[:7]

    for category, products in product_details_list.items():
        discounted_products = [product for product in products if product.get('discounted_price')]
        if discounted_products:
            random_product = random.choice(discounted_products)
            random_discount.append(random_product)

     # Sorting based on the 'sort' query parameter
    sort_option = request.GET.get('sort')
    for category, products in product_details_list.items():
        product_details_list[category] = sort_products(products, sort_option)

    context = {
        'product_details_list': product_details_list,
        'random_shopmetro': random_shopmetro,
        'random_waltermart': random_waltermart,
        'random_puregold': random_puregold,        
        'random_discount': random_discount,  # Add the new random products with discounted prices
    }
    return render(request, 'index.html', context)

def category(request, category_name):
    # Retrieve products for the specified category from MongoDB
    products = list(collection.find({'category': category_name}))  # Convert cursor to list

    # Get the selected sorting option from the URL query parameters
    sort_option = request.GET.get('sort')

    # Get the selected price range from the URL query parameters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Get the selected supermarket from the URL query parameters
    selected_supermarket = request.GET.get('supermarket')

    # Filter products based on the selected price range
    if min_price is not None and max_price is not None:
        min_price = float(min_price)
        max_price = float(max_price)
        products = [product for product in products if min_price <= get_price(product) <= max_price]

    # Filter products based on the selected supermarket (if provided)
    if selected_supermarket and selected_supermarket != 'None':
        products = [product for product in products if product['supermarket'] == selected_supermarket]

    # Determine the sorting key based on the selected option
    if sort_option == 'price_low_to_high':
        sorting_key = 'discounted_price'  # Sort by discounted price ascending
    elif sort_option == 'price_high_to_low':
        sorting_key = '-discounted_price'  # Sort by discounted price descending
    else:
        sorting_key = None  # Default: No sorting

    if sorting_key:
        # Sort the entire list of products based on the sorting key
        products = sort_products(products, sort_option)

    # Calculate the total number of products for the selected category
    total_products = len(products)

    # Create a Paginator object with 20 products per page
    paginator = Paginator(products, 20)

    # Get the requested page number from the URL query parameters~
    page = request.GET.get('page')

    try:
        # Try to get the products for the requested page
        product_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to page 1~
        product_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., page 9999), deliver the last page of results
        product_page = paginator.page(paginator.num_pages)

    # Implement sorting and price filtering as needed (similar to your current code)

    context = {
        'product_page': product_page,  # Pass the paginated products to the template
        'total_products': total_products,  # Pass the total number of products for the selected category
        'sort_option': sort_option,  # Pass the selected sorting option to the template
        'category_name': category_name,
        'min_price': min_price,  # Pass the selected min price to the template
        'max_price': max_price,
        'selected_supermarket': selected_supermarket,  # Pass the selected supermarket to the template
    }

    return render(request, 'category.html', context)

def get_price(product):
    # Try to get the discounted price, then the original price, and default to None if both are missing
    price_str = product.get('discounted_price') or product.get('original_price')

    if price_str:
        # Remove non-numeric characters and spaces from the price string
        cleaned_price_str = re.sub(r'[^\d.]', '', price_str)

        if cleaned_price_str:
            # Try to convert the cleaned price string to a float
            return float(cleaned_price_str)

    # Return None if price information is missing or cannot be converted
    return None

def sort_products(products, sort_option):
    # Filter out products with None prices before sorting
    products = [product for product in products if get_price(product) is not None]

    if sort_option == 'price_low_to_high':
        sorted_products = sorted(products, key=lambda x: get_price(x))
    elif sort_option == 'price_high_to_low':
        sorted_products = sorted(products, key=lambda x: get_price(x), reverse=True)
    else:
        sorted_products = products  # Default: no sorting

    return sorted_products
import json
import logging
from datetime import datetime  # Import the datetime module

def product_detail(request, product_id):
    product = collection.find_one({'id': product_id})

    # Get the historical price data for the product
    price_history = product.get('price_history', [])

    # Format the date in the price history data
    formatted_price_history = []
    for entry in price_history:
        date_scraped = entry.get('date_scraped')
        if date_scraped:
            # Parse the date from ISO format
            date_object = datetime.fromisoformat(date_scraped)

            # Format the date as "Month Year"
            formatted_date = date_object.strftime('%B %Y')

            # Create a new entry with the formatted date
            formatted_entry = {
                'price': entry.get('price', ''),
                'date_scraped': formatted_date,
            }

            formatted_price_history.append(formatted_entry)

    # Serialize the formatted price history data to JSON
    formatted_price_history_json = json.dumps(formatted_price_history)

    # Log the price data to the console for debugging
    logging.debug(f'Product ID: {product_id}, Price History: {formatted_price_history}')

    context = {
        'product': product,
        'formatted_price_history_json': formatted_price_history_json,
        'has_price_history': bool(formatted_price_history),  # Check if price history exists
    }
    return render(request, 'product_detail.html', context)
