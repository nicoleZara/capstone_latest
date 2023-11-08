from typing import Any
from django.shortcuts import render, redirect
import random
from pymongo import MongoClient
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import re
import json
import logging
from django.http import HttpResponse
from datetime import datetime  

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from fuzzywuzzy import fuzz  

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from auth_system.views import like_dislike_collection as likes_dislikes_collection
from django.http import HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_POST

from django.http import JsonResponse
from fuzzywuzzy import fuzz
import uuid


from auth_system.models import MongoDBUser
from bson.objectid import ObjectId
from pymongo import UpdateOne





# Connect to MongoDB
# client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
# db = client['Product_Comparison_System']
# collection = db['Sept_FInal_Final']

client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['TryGraph']
comments_collection = db['Comments']
user_collection = db['Users']
favorites_collection = db['Favorites']



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




# Initialize NLTK stopwords
nltk.download("stopwords")
from nltk.corpus import stopwords
stop_words = set(stopwords.words("english"))

# Preprocess text: remove stopwords, punctuation, and extra spaces
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = " ".join([word for word in text.split() if word not in stop_words])  # Remove stopwords
    return text

# Calculate similarity using TF-IDF and Cosine Similarity
def calculate_similarity(input_title, product_titles):
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform([input_title] + product_titles)
    cosine_similarities = linear_kernel(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    return cosine_similarities


# Find similar products based on similarity scores within a threshold range
def find_similar_products(title):
    product_titles = [p.get('title', '') for p in collection.find()]

    # Split the input title into product name and weight/grams
    input_title_parts = re.split(r'\s+\|\s+', title)
    input_name = input_title_parts[0]
    input_weight = input_title_parts[-1]

    # Preprocess input title parts
    input_name = preprocess_text(input_name)
    input_weight = preprocess_text(input_weight)

    title_parts_list = [re.split(r'\s+\|\s+', product_title) for product_title in product_titles]
    product_names = [preprocess_text(parts[0]) for parts in title_parts_list]
    product_weights = [preprocess_text(parts[-1]) for parts in title_parts_list]

    similarity_scores = calculate_similarity(input_name, product_names)

    similar_products = []
    for i, score in enumerate(similarity_scores):
        if 0.65 <= score <= 0.9:  # Adjust the threshold range as needed
            # Check if the weight/grams are similar
            if fuzz.ratio(input_weight, product_weights[i]) >= 80:  # Adjust the similarity threshold as needed
                product_doc = collection.find()[i]  # Get the MongoDB document
                similar_products.append({
                    'title': product_titles[i],
                    'supermarket': product_doc.get('supermarket', ''),  # Fetch the 'supermarket' field
                    'original_price': product_doc.get('original_price', ''),  # Fetch the 'original_price' field
                    'url': product_doc.get('url', ''),  # Fetch the 'url' field
                    'similarity_score': score,
                })

    similar_products.sort(key=lambda x: x['similarity_score'], reverse=True)

    return similar_products


# Modify the product_detail view to find similar products
def product_detail(request, product_id):

    product = collection.find_one({'id': product_id})
    comments = comments_collection.find({'product_id': product_id})

      # Get the current user
    user = request.user

    # Check if the user has already liked or disliked this product
    user_interaction = likes_dislikes_collection.find_one({'user_id': user.id, 'product_id': product_id})

    # Check if the user has already commented on this product
    user_has_commented = comments_collection.find_one({'user_id': user.id, 'product_id': product_id})

    # Count the number of comments for the product
    comment_count = comments_collection.count_documents({'product_id': product_id})
    print("Comment Count:", comment_count)

    
    # Calculate the like and dislike counts for the product
    like_count = likes_dislikes_collection.count_documents({'product_id': product_id, 'action': 'like'})
    dislike_count = likes_dislikes_collection.count_documents({'product_id': product_id, 'action': 'dislike'})
    



    # Get the product title
    product_title = product.get('title', '')

    # Use the find_similar_products function to find similar products
    similar_products = find_similar_products(product_title)

    # Get the historical price data for the product
    price_history = product.get('price_history', [])


    # Calculate the like and dislike counts for the product
    # like_count = likes_dislikes_collection.count_documents({'product_id': product_id, 'action': 'like'})
    # dislike_count = likes_dislikes_collection.count_documents({'product_id': product_id, 'action': 'dislike'})

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
        'similar_products': similar_products,  # Pass the list of similar products to the template
        'formatted_price_history_json': formatted_price_history_json,
        'has_price_history': bool(formatted_price_history),  # Check if price history exists

        'user_interaction': user_interaction,
        'like_count': like_count,
        'dislike_count': dislike_count,
        'comment_count': comment_count,
        'comments': comments,
        'user_has_commented': user_has_commented is not None,
    }
    return render(request, 'product_detail.html', context)


@login_required
def toggle_like_dislike(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')  # 'like' or 'dislike'

        # Get the current user
        user = request.user

        # Check if the user has already liked or disliked this product
        user_interaction = likes_dislikes_collection.find_one({'user_id': user.id, 'product_id': product_id})

        # Prepare an update query to update the MongoDB collection
        update_query = {
            'user_id': user.id,
            'product_id': product_id,
        }

        if user_interaction:
            if user_interaction['action'] == action:
                # User clicked the same button again, remove the interaction
                likes_dislikes_collection.delete_one(update_query)
                result = 'removed'
            else:
                # User changed their action, update the interaction
                likes_dislikes_collection.update_one(update_query, {'$set': {'action': action}})
                result = 'updated'
        else:
            # User is interacting with this product for the first time, create a new interaction
            update_query['action'] = action
            likes_dislikes_collection.insert_one(update_query)
            result = 'added'

        # Now, update the MongoDB collection for likes and dislikes based on user interactions
        # You should implement the logic to update MongoDB based on user interactions here

        return JsonResponse({'result': result})



@login_required
def add_comment(request, product_id):
    if request.method == 'POST':
        user = request.user
        comment_text = request.POST.get('comment_text')

        user_id = user.id
        user_data = user_collection.find_one({'user_id': user_id})

        if user_data:
            user_name = user_data['username']
        else:
            user_name = 'Anonymous'

        # Check if the user has already commented on this product
        existing_comment = comments_collection.find_one({'user_id': user_id, 'product_id': product_id})

        if existing_comment:
            # You can choose to handle this case differently, e.g., show an error message
            return HttpResponseForbidden("You have already commented on this product.")

        comment_data = {
            'user_id': user_id,
            'user_name': user_name,
            'product_id': product_id,
            'text': comment_text,
            'timestamp': datetime.now(),
        }

        comments_collection.insert_one(comment_data)

        return redirect('home:product_detail', product_id=product_id)
    else:
        # Render the comment form or a template where users can add comments
        return render(request, 'product_detail.html')




# DISPLAY ALL WITH PROMOS IN DISCOUNT.HTML
def discounts(request):
    # Fetch all products with a discounted price from MongoDB
    discounted_products = list(collection.find({'discounted_price': {'$exists': True}}))

    # Get the selected supermarket from the URL query parameters
    selected_supermarket = request.GET.get('supermarket')

    # Filter products based on the selected supermarket (if provided)
    if selected_supermarket and selected_supermarket != 'None':
        discounted_products = [product for product in discounted_products if product['supermarket'] == selected_supermarket]


    # Create a Paginator object with 15 products per page
    paginator = Paginator(discounted_products, 15)

    # Get the requested page number from the URL query parameters
    page = request.GET.get('page')

    try:
        # Try to get the products for the requested page
        product_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to page 1
        product_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver the last page of results
        product_page = paginator.page(paginator.num_pages)

    context = {
        'discounted_products': product_page,
        'selected_supermarket': selected_supermarket,
    }

    return render(request, 'discounts.html', context)



@login_required
def add_to_favorites(request, product_id):
    # Retrieve the product from the original collection
    product = collection.find_one({'id': product_id})

    if not product:
        return HttpResponse("Product not found.", status=404)

    # Get the current user
    user = request.user

    # Check if the product is already in the favorites collection
    existing_favorite = favorites_collection.find_one({'user_id': user.id, 'id': product_id})

    if existing_favorite:
        return HttpResponse("Product is already in your favorites.")
    # Check if the user is logged in
    # if not request.user.is_authenticated:
    #     # messages.error(request, "Please log in to add a product to your favorites.")
    #     return HttpResponse("Please log in to add a product to your favorites.")  # Redirect to the login page

    # If the product is not in favorites, add it to the favorites collection with a unique batch identifier
    batch_identifier = str(uuid.uuid4())  # Generate a unique batch identifier
    product['batch_identifier'] = batch_identifier  # Add the batch identifier to the product
    product['user_id'] = user.id
    favorites_collection.insert_one(product)

    # Use the find_similar_products function to find similar products
    similar_products = find_similar_products(product.get('title', ''), product.get('weight', ''), product.get('brand', ''), product.get('supermarket', ''), collection)
    
    # Collect all similar products that are not already in favorites
    new_similar_products = [similar_product for similar_product in similar_products if not favorites_collection.find_one({'id': similar_product['id'], 'user_id': user.id})]

    # Iterate through the new similar products and add them to the favorites collection with the same batch identifier
    for similar_product in new_similar_products:
        similar_product['batch_identifier'] = batch_identifier  # Add the same batch identifier
        similar_product['user_id'] = user.id
        favorites_collection.insert_one(similar_product)

    return HttpResponse("Product added to favorites successfully.")
