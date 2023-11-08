import json
from django.shortcuts import render
from pymongo import MongoClient
import re
import numpy as np
from datetime import datetime
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
import plotly.figure_factory as ff  
from collections import Counter
import requests


client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

def format_price(price_str):
    # Clean the price by removing non-numeric characters and the peso sign (₱)
    cleaned_price_str = re.sub(r'[^\d.]', '', price_str)
    if cleaned_price_str:
        # Convert the cleaned price string to a float, preserving decimal points
        return float(cleaned_price_str)
    return 0.0

def calculate_price_per_product(price_str):
    # Calculate the price per product for prices in the format "X for Y.YY"
    match = re.match(r'(\d+)\s+for\s+(\d+\.\d+)', price_str)
    if match:
        return None
    return format_price(price_str)


def calculate_total_price_per_supermarket(data):
    # Create a dictionary to store the total prices for each supermarket
    total_prices_per_supermarket = {}

    for item in data:
        supermarket = item['supermarket']
        price = item['original_price']

        if supermarket not in total_prices_per_supermarket:
            total_prices_per_supermarket[supermarket] = price
        else:
            total_prices_per_supermarket[supermarket] += price

    return total_prices_per_supermarket

def calculate_price_stats(data):
    # Create a dictionary to store price statistics for each supermarket and category
    price_stats = {}

    for item in data:
        supermarket = item['supermarket']
        category = item['category']
        price = item['original_price']

        if supermarket not in price_stats:
            price_stats[supermarket] = {}

        if category not in price_stats[supermarket]:
            price_stats[supermarket][category] = []

        price_stats[supermarket][category].append(price)

    # Calculate summary statistics (min, max, median) for each supermarket and category
    for supermarket, categories in price_stats.items():
        for category, prices in categories.items():
            min_price = min(prices)
            max_price = max(prices)
            median_price = np.median(prices)

            price_stats[supermarket][category] = {
                'min_price': min_price,
                'max_price': max_price,
                'median_price': median_price,
            }
    return price_stats


def calculate_discounted_vs_regular_prices(data):
    discounted_vs_regular_prices = {}

    for item in data:
        supermarket = item['supermarket']
        category = item['category']
        original_price = item['original_price']
        discounted_price = item.get('discounted_price', 0.0)

        if supermarket not in discounted_vs_regular_prices:
            discounted_vs_regular_prices[supermarket] = {}

        if category not in discounted_vs_regular_prices[supermarket]:
            discounted_vs_regular_prices[supermarket][category] = {
                'regular_price_sum': 0.0,
                'discounted_price_sum': 0.0,
            }

        discounted_vs_regular_prices[supermarket][category]['regular_price_sum'] += original_price
        discounted_vs_regular_prices[supermarket][category]['discounted_price_sum'] += discounted_price

    return discounted_vs_regular_prices


def format_date(date_str):
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')
    # Format the datetime object as "month day, year"
    formatted_date = date_obj.strftime('%b %d, %Y')
    return formatted_date

def get_price_history(product_id):
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
    db = client['Product_Comparison_System']
    collection = db['Sept_Final']

    # Fetch the price history data for the given product_id
    product = collection.find_one({'id': product_id}, {'price_history': 1})

    if product and 'price_history' in product:
        # Extract dates and prices from the price history data and format the dates
        price_history = product['price_history']

        dates = []
        prices = []

        for entry in price_history:
            date = format_date(entry['date_scraped'])
            price = float(entry['price'].replace('₱', '').replace(',', ''))

            dates.append(date)
            prices.append(price)

        return dates, prices
    else:
        return None, None


def get_products_with_price_history():
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
    db = client['Product_Comparison_System']
    collection = db['Sept_FInal_Final']

    # Find products that have price history
    products_with_price_history = list(collection.find({'price_history': {'$exists': True}}, {'id': 1, 'price_history': 1}))

    return products_with_price_history

# -------------------------------------------------------------------------------------------------------------------------------------------

def chart1(request):
    # Fetch the data from MongoDB
    data = list(collection.find({}, {'supermarket': 1, 'category': 1, 'original_price': 1, 'discounted_price': 1, 'title': 1}))

    # Clean and format the 'original_price' field (remove the '₱' sign)
    for item in data:
        original_price = item['original_price']
        discounted_price = item.get('discounted_price', None)

        # Calculate price per product for prices in the format "X for Y.YY"
        price_per_product = calculate_price_per_product(original_price)
        price_per_product_discounted = calculate_price_per_product(discounted_price) if discounted_price else None

        if price_per_product is not None:
            # Use the calculated price per product
            item['original_price'] = price_per_product
        
        if price_per_product_discounted is not None:
            # Use the calculated price per product for discounted price
            item['discounted_price'] = price_per_product_discounted

#--------------------------------------------------------------------------------------------------------------------------------------------

    # Create a dictionary to store total prices for each category in each supermarket
    category_prices = {}

    for item in data:
        supermarket = item['supermarket']
        category = item['category']
        price = item['original_price']
        if supermarket not in category_prices:
            category_prices[supermarket] = {}
        if category not in category_prices[supermarket]:
            category_prices[supermarket][category] = 0.0
        category_prices[supermarket][category] += price

    # Get a list of unique supermarkets
    supermarkets = list(category_prices.keys())

#--------------------------------------------------------------------------------------------------------------------------------------------
    bar_chart_data = {}

    # Add a special case for "all" to include total prices across all supermarkets
    all_categories = list(set(category for supermarket_data in category_prices.values() for category in supermarket_data.keys()))
    all_total_prices = [sum(supermarket_data[category] for supermarket_data in category_prices.values() if category in supermarket_data) for category in all_categories]
    bar_chart_data['all'] = {
        'categories': all_categories,
        'total_prices': all_total_prices,
    }

    for supermarket in supermarkets:
        categories = list(category_prices[supermarket].keys())
        total_prices = list(category_prices[supermarket].values())

        bar_chart_data[supermarket] = {
            'categories': categories,
            'total_prices': total_prices,
        }
    bar_chart_data_json = json.dumps(bar_chart_data)
    total_prices_per_supermarket = calculate_total_price_per_supermarket(data)
    total_prices_json = json.dumps(total_prices_per_supermarket)


#--------------------------------------------------------------------------------------------------------------------------------------------
    doughnut_chart_data = {}
    # Add a special case for "all" to include the total number of products across all supermarkets
    all_category_counts = [len(data)]
    doughnut_chart_data['all'] = {
        'categories': ['All Products'],
        'category_counts': all_category_counts,
    }

    for supermarket in supermarkets:
        categories = list(category_prices[supermarket].keys())
        category_counts = [len([item for item in data if item['supermarket'] == supermarket and item['category'] == category]) for category in categories]

        doughnut_chart_data[supermarket] = {
            'categories': categories,
            'category_counts': category_counts,
        }


#--------------------------------------------------------------------------------------------------------------------------------------------
    category_counts = {}

    for item in data:
        supermarket = item['supermarket']
        category = item['category']

        if supermarket not in category_counts:
            category_counts[supermarket] = {}

        if category not in category_counts[supermarket]:
            category_counts[supermarket][category] = 0

        category_counts[supermarket][category] += 1

    # Get a list of unique supermarkets
    supermarkets = list(category_counts.keys())
#--------------------------------------------------------------------------------------------------------------------------------------------
    doughnut_chart_data = {}

    # Add a special case for "all" to include the total number of products across all supermarkets
    all_category_counts = [sum(counts.values()) for counts in category_counts.values()]
    doughnut_chart_data['all'] = {
        'categories': supermarkets,
        'category_counts': all_category_counts,
    }

    for supermarket in supermarkets:
        categories = list(category_counts[supermarket].keys())
        category_counts_list = [category_counts[supermarket][category] for category in categories]

        doughnut_chart_data[supermarket] = {
            'categories': categories,
            'category_counts': category_counts_list,
        }

    doughnut_chart_data_json = json.dumps(doughnut_chart_data)
    doughnut_chart_data_json = json.dumps(doughnut_chart_data)

#3 HORIZONTAL CHART---------------------------------------------------------------------------------------------------------------------------

# Create a dictionary to store the count of products with discounts for each category in each supermarket
    category_discount_counts = {}

    for item in data:
        supermarket = item['supermarket']
        category = item['category']
        has_discount = 'discounted_price' in item and item['discounted_price'] is not None

        if supermarket not in category_discount_counts:
            category_discount_counts[supermarket] = {}

        if category not in category_discount_counts[supermarket]:
            category_discount_counts[supermarket][category] = 0

        if has_discount:
            category_discount_counts[supermarket][category] += 1

    # Get a list of unique supermarkets
    supermarkets = list(category_discount_counts.keys())

#--------------------------------------------------------------------------------------------------------------------------------------------
    horizontal_bar_chart_data = {}

    # Add a special case for "all" to include total counts of products with discounts across all supermarkets
    all_category_discount_counts = [sum(counts.values()) for counts in category_discount_counts.values()]
    horizontal_bar_chart_data['all'] = {
        'categories': supermarkets,
        'category_discount_counts': all_category_discount_counts,
    }

    for supermarket in supermarkets:
        categories = list(category_discount_counts[supermarket].keys())
        category_discount_counts_list = [category_discount_counts[supermarket][category] for category in categories]

        horizontal_bar_chart_data[supermarket] = {
            'categories': categories,
            'category_discount_counts': category_discount_counts_list,
        }

    horizontal_bar_chart_data_json = json.dumps(horizontal_bar_chart_data)

#4 PRICE FLUCTUATION CHART--------------------------------------------------------------------------------------------

    price_distribution_data = {}

    # Add a special case for "all" to include the Price Distribution Histogram for all supermarkets
    all_prices = [item['original_price'] for item in data]
    price_ranges = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]  # Define your desired price ranges
    frequency = [len([price for price in all_prices if price_range <= price < price_range + 100]) for price_range in price_ranges]

    price_distribution_data['all'] = {
        'price_ranges': price_ranges,
        'frequency': frequency,
    }

    for supermarket in supermarkets:
        supermarket_prices = [item['original_price'] for item in data if item['supermarket'] == supermarket]
        frequency = [len([price for price in supermarket_prices if price_range <= price < price_range + 100]) for price_range in price_ranges]

        price_distribution_data[supermarket] = {
            'price_ranges': price_ranges,
            'frequency': frequency,
        }

    price_distribution_data_json = json.dumps(price_distribution_data)
    price_stats = calculate_price_stats(data)
    price_stats_json = json.dumps(price_stats)
#5 ORIGINAL VS DISCOUNTED PRICE----------------------------------------------------------------------------------------------------------------------------------------------

    # # Add a special case for "all" to include the total discount and regular prices across all supermarkets
    all_categories = list(set(category for item in data))
    all_total_discounted_prices = [sum(item.get('discounted_price', 0.0) for item in data if item['category'] == category) for category in all_categories]
    all_total_regular_prices = [sum(item['original_price'] for item in data if item['category'] == category) for category in all_categories]

    price_distribution_data['all'] = {
        'categories': all_categories,
        'total_discounted_prices': all_total_discounted_prices,
        'total_regular_prices': all_total_regular_prices,
    }

    for supermarket in supermarkets:
        categories = list(category_prices[supermarket].keys())
        total_discounted_prices = [sum(item.get('discounted_price', 0.0) for item in data if item['supermarket'] == supermarket and item['category'] == category) for category in categories]
        total_regular_prices = [sum(item['original_price'] for item in data if item['supermarket'] == supermarket and item['category'] == category) for category in categories]

        price_distribution_data[supermarket] = {
            'categories': categories,
            'total_discounted_prices': total_discounted_prices,
            'total_regular_prices': total_regular_prices,
        }

    discounted_vs_regular_prices_data = calculate_discounted_vs_regular_prices(data)
    discounted_vs_regular_prices_json = json.dumps(discounted_vs_regular_prices_data)

#--------------------------------------------------------------------------------------------------------------------------------------------

    # scatter_data = [{'x': item['original_price'], 'y': item.get('discounted_price', 0.0)} for item in data]
    # Extract product titles to be used in tooltips
    # product_titles = [{'title': item['title'],} for item in data]

    # Convert the scatter plot data and product titles to JSON format for JavaScript
    # scatter_data_json = json.dumps(scatter_data)
    # product_titles_json = json.dumps(product_titles)

    # Get all products that have price history
    #  # Get all products that have price history
    # products_with_price_history = list(collection.find({}, { 'id': 1, 'price_history': 1 }))
    # # Prepare data to pass to the template
    # product_data = []


    # for product in products_with_price_history:
    #     product_id = str(product['id'])
    #     price_history = product.get('price_history', [])

    #     title = collection.find_one({'id': product_id}, {'title': 1})
    #     product_title = title.get('title', 'Unknown Title')
    #     dates = []
    #     prices = []

            
    #     for entry in price_history:
    #         # assuming date_scraped is in '2023-09-24T00:00:00.000Z' format
    #         date_scraped = entry.get('date_scraped')
    #         if date_scraped:
    #             # split date and time, format it to 'Sep 24, 2023'
    #             date = datetime.strptime(date_scraped.split("T")[0], "%Y-%m-%d").strftime("%b %d, %Y")
    #             dates.append(date)
            
    #         price = entry.get('price')
    #         if price:
    #             # assuming price is in '₱1,116.00' format
    #             price = float(price.replace('₱', '').replace(',', ''))
    #             prices.append(price)
                
    #     if dates and prices:
    #         # Convert the data to JSON format for JavaScript
    #         dates_json = json.dumps(dates)
    #         prices_json = json.dumps(prices)
    #         product_data.append({
    #             'product_id': product_id,
    #             'dates_json': dates_json,
    #             'prices_json': prices_json,
    #             'title': product_title,  # Include the title in the data

    #         })


#--------------------------------------------------------------------------------------------------------------------------------------------

    products_with_price_history = list(collection.find({}, { 'id': 1, 'price_history': 1 }))
    # Prepare data to pass to the template
    product_data = []

    for product in products_with_price_history:
        product_id = str(product['id'])
        price_history = product.get('price_history', [])
        dates = []
        prices = []
        for entry in price_history:
            # assuming date_scraped is in '2023-09-24T00:00:00.000Z' format
            date_scraped = entry.get('date_scraped')
            if date_scraped:
                # split date and time, format it to 'Sep 24, 2023'
                date = datetime.strptime(date_scraped.split("T")[0], "%Y-%m-%d").strftime("%b %d, %Y")
                dates.append(date)
            
            price = entry.get('price')
            if price:
                # assuming price is in '₱1,116.00' format
                price = float(price.replace('₱', '').replace(',', ''))
                prices.append(price)
                
        if dates and prices:
            # Convert the data to JSON format for JavaScript
            dates_json = json.dumps(dates)
            prices_json = json.dumps(prices)
            product_data.append({
                'product_id': product_id,
                'dates_json': dates_json,
                'prices_json': prices_json,
            })
    #---------------------------------------------------------USER USER USER------------------------------------------


    user_collection = db['Users']
    user_data = list(user_collection.find({}, {"age": 1, "gender": 1, "birthday": 1, "purpose": 1}))

    dislike_like_collection = db['ProductLikesDislikes']
    dislike_like_data = list(dislike_like_collection.find({}, {"user_id": 1, "product_id": 1, "action": 1, "_id": 0}))

    # Extract age and gender information
    ages = [user.get("age", 0) for user in user_data]
    genders = [user.get("gender", "Unknown") for user in user_data]

    # Create bins for age groups (e.g., 10-20, 20-30, etc.)
    age_bins = range(0, 101, 10)  # Adjust the range and bin size as needed

    # Calculate the histogram data
    male_age_counts, _ = np.histogram([ages[i] for i in range(len(ages)) if genders[i] == "male"], bins=age_bins)
    female_age_counts, _ = np.histogram([ages[i] for i in range(len(ages)) if genders[i] == "female"], bins=age_bins)

    # Convert the histogram data to a format that can be easily passed to JavaScript
    age_labels = [f"{bin_start}-{bin_end}" for bin_start, bin_end in zip(age_bins[:-1], age_bins[1:])]
    histogram_data = {
        "age_labels": age_labels,
        "male_age_counts": male_age_counts.tolist(),
        "female_age_counts": female_age_counts.tolist(),
    }

     # Extract ages
    ages = []
    for user in user_data:
        birthday = user.get("birthday")
        if birthday:
            # Parse the date string into a datetime object
            birth_date = datetime.strptime(birthday, "%Y-%m-%d")
            # Append the datetime object to the list of ages
            ages.append(birth_date)

    # Create a birthday distribution histogram
    fig1 = px.histogram(ages, title="Birthday Distribution")
    fig1.update_xaxes(title="Birthdate")
    fig1.update_yaxes(title="Count")

    birthday_chart_json = fig1.to_json()
    histogram_data_json = json.dumps(histogram_data)

#--------------------------------------------------------------------------------------------------------------------------------------------
    
    purposes = [user.get("purpose", "") for user in user_data]

    # Count the occurrences of each purpose
    purpose_counts = Counter(purposes)

    # Find the purpose with the highest count
    most_common_purpose, most_common_count = purpose_counts.most_common(1)[0]

    # Convert the counts to a JSON format for JavaScript
    purpose_counts_json = json.dumps(purpose_counts)

#-----------------------------------------------------------------------------------------------------------------------------------------
    dislike_like_collection = db['ProductLikesDislikes']
    user_action_data = list(dislike_like_collection.find({}, {"user_id": 1, "product_id": 1, "action": 1, "_id": 0}))

    # Create a DataFrame from the user action data
    df = pd.DataFrame(user_action_data)
    # Function to convert 'like' to 1 and 'dislike' to 0
    def action_to_numeric(x):
        if x == 'like':
            return 1
        if x == 'dislike':
            return 0
        return None

    # Apply this function to the 'action' column
    df['action'] = df['action'].apply(action_to_numeric)

    # Now you can create your interaction_matrix with mean function as it's now numeric
    interaction_matrix = df.pivot_table(index='user_id', columns='product_id', values='action', fill_value=0)

    # Convert the interaction matrix to a list of lists for Plotly heatmap
    interaction_matrix_list = interaction_matrix.values.tolist()
    product_titles = {}
    # Get all documents in the collection
    products = collection.find({}, {'id': 1, 'title': 1})
    # Fill the dictionary with id -> title mappings
    for product in products:
        product_titles[product['id']] = product['title']

    # Define the x-axis (product_id) and y-axis (user_id) labels
    x_labels = [product_titles.get(id, '') for id in interaction_matrix.columns.tolist()]
    y_labels = interaction_matrix.index.tolist()

    # Create the heatmap
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=interaction_matrix_list,
        x=x_labels,
        y=y_labels,
        colorscale='RdYlGn',  # Customize the colorscale
        hoverongaps=False,
    ))

    # Customize the layout of the heatmap
    heatmap_fig.update_layout(
        title="User-Product Interaction",
        xaxis_title="Product ID",
        yaxis_title="User ID",
    )
    import plotly.io as pio

    heatmap_fig_json = pio.to_json(heatmap_fig)

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
    most_liked_title, most_liked_original_price, most_liked_image, most_liked_description, most_liked_total_count = get_most_liked_disliked_product('like')
    most_disliked_title, most_disliked_original_price, most_disliked_image, most_disliked_description, most_disliked_total_count = get_most_liked_disliked_product('dislike')

    # Convert the data for the horizontal stacked bar chart to JSON format for JavaScript
    context = {
        'bar_chart_data_json': bar_chart_data_json,
        'total_prices_json': total_prices_json,
        'doughnut_chart_data_json': doughnut_chart_data_json,  # Add doughnut chart data to the context
        'supermarkets': supermarkets,
        'horizontal_bar_chart_data_json':horizontal_bar_chart_data_json,
        'price_distribution_data_json': price_distribution_data_json,  # Add Price Distribution Histogram data to the context
        'price_stats_json': price_stats_json,  # Add price statistics data to the context
        'discounted_vs_regular_prices_json': discounted_vs_regular_prices_json,  # Add the new chart data to the context
        # 'scatter_data_json': scatter_data_json,
        # 'product_titles_json': product_titles_json,
        #---------------USERR------------------
        'histogram_data_json': histogram_data_json,
        'product_data': json.dumps(product_data),
        'birthday_chart_json':birthday_chart_json, 
        'dislike_like_data': json.dumps(dislike_like_data),
        "heatmap_fig_json": heatmap_fig_json,
        'most_liked_title': most_liked_title,
        'most_liked_original_price': most_liked_original_price,
        'most_liked_image': most_liked_image,
        'most_liked_description': most_liked_description,
        'most_disliked_title': most_disliked_title,
        'most_disliked_original_price': most_disliked_original_price,
        'most_disliked_image': most_disliked_image,
        'most_disliked_description': most_disliked_description,
        'most_liked_total_count': most_liked_total_count,  # Add total count of likes
        'most_disliked_total_count': most_disliked_total_count,  
        'most_common_purpose': most_common_purpose,  # Add the most common purpose to the context
        'most_common_count': most_common_count,
        'purpose_counts_json':purpose_counts_json
        

 # Convert the product data to JSON for JavaScript


    }

    return render(request, 'charts/chart1.html', context)

def get_most_liked_disliked_product(action):
    # Create a pipeline to group and count likes and dislikes
    product_likes_dislikes_collection = db['ProductLikesDislikes']
    sept_final_final_collection = db['Sept_FInal_Final']
    pipeline = [
        {
            '$match': {'action': action}
        },
        {
            '$group': {
                '_id': '$product_id',
                'count': {'$sum': 1}
            }
        },
        {
            '$sort': {'count': -1},
        },
        {
            '$limit': 1
        }
    ]

    # Execute the aggregation pipeline to get the product with the most likes or dislikes
    product_with_most_action = product_likes_dislikes_collection.aggregate(pipeline)

    # Extract the product_id with the most likes or dislikes
    product_id = None
    total_count = 0  # Initialize the total count

    for result in product_with_most_action:
        product_id = result['_id']
        total_count = result['count']  # Extract the total count

    if product_id:
        # Fetch the product details from Sept_FInal_Final collection
        product_details = sept_final_final_collection.find_one({'id': product_id})

        # Extract the desired fields from the product document
        title = product_details['title']
        original_price = product_details['original_price']
        image = product_details['image']
        description = product_details['description']

        return title, original_price, image, description, total_count  # Return the total count

    return None, 0  # Handle the case where there are no likes or dislikes

