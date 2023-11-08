from django.shortcuts import render
from pymongo import MongoClient
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import re
from collections import defaultdict  # Import defaultdict for category counts
from collections import Counter




# Connect to MongoDB
client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Graph']





def supermarket_page(request, supermarket_name):
    # Retrieve products from the selected supermarket
    # products = collection.find({'supermarket': supermarket_name})
    all_products =list(collection.find({'supermarket': supermarket_name}))

    # Define banner image URLs for each supermarket (adjust these URLs as needed)
    supermarket_banners = {
        'WalterMart': '/static/imgs/banner/waltermart.png',
        'Puregold': '/static/imgs/banner/puregold.png',
        'ShopMetro': '/static/imgs/banner/shopmetro2.png',
    }
    # Get the banner image URL for the selected supermarket
    banner_image_url = supermarket_banners.get(supermarket_name)

    # Calculate category counts for the selected supermarket
    category_counts = Counter(product['category'].replace(' ', '_') for product in all_products)
    
    # Calculate the total number of products for the selected supermarket
    total_products = len(all_products)

    # Create a Paginator object with 20 products per page
    paginator = Paginator(all_products, 20)
   
    # Get the requested page number from the URL query parameters
    page = request.GET.get('page')

    try:
        # Try to get the products for the requested page
        product_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to page 1
        product_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., page 9999), deliver the last page of results
        product_page = paginator.page(paginator.num_pages)
    
   
    context = {
        'supermarket_name': supermarket_name,
        'all_products': all_products,
        'product_page': product_page,  # Pass the paginated products to the template
        'total_products': total_products,  # Pass the total number of products for the selected category
        'category_counts': category_counts,
        'banner_image_url': banner_image_url,
        # 'product_by_category': product_by_category,
    }

    return render(request, 'supermarket/supermarket_page.html', context)




def get_similar_products(product, supermarket_name):
    # Define similarity criteria, e.g., based on product name
    similarity_criteria = {
        'product_name': product['product_name'],
        'supermarket': {'$ne': supermarket_name},  # Exclude the current supermarket
    }
    
    # Query the database to find similar products
    similar_products = list(collection.find(similarity_criteria))

    return get_similar_products

def compare_modal(request, supermarket_name, product_id):
    # Retrieve the selected product
    selected_product = collection.find_one({'supermarket': supermarket_name, 'id': product_id})

    # Get similar products from other supermarkets
    similar_products = get_similar_products(selected_product, supermarket_name)

    context = {
        'selected_product': selected_product,
        'similar_products': similar_products,
    }

    return render(request, 'supermarket/supermarket_page.html', context)









def supermarket_category(request, supermarket_name, category_name):
    categories = collection.distinct('category', {'supermarket': supermarket_name})
    
    # Create a dictionary to store product by category
    product_by_category = {}

    # Retrieve products for each category
    for category in categories:
        products = collection.find({'supermarket': supermarket_name, 'category': category_name})
        product_by_category[category] = list(products)


    products = list(collection.find({'supermarket': supermarket_name, 'category': category_name}))
    
    # Calculate the total number of products for the selected category
    total_products = len(products)

    # # Calculate category counts for the selected supermarket
    category_counts = Counter(product['category'].replace(' ', '_') for product in products)

    # Create a Paginator object with 20 products per page
    paginator = Paginator(products, 20)
   
    # Get the requested page number from the URL query parameters
    page = request.GET.get('page')

    try:
        # Try to get the products for the requested page
        product_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, default to page 1
        product_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., page 9999), deliver the last page of results
        product_page = paginator.page(paginator.num_pages)
    

    context = {
        'supermarket': supermarket_name,
        'category': category_name,
        'categories': categories,
        'products': products,
        'product_by_category' : product_by_category,

        'product_page': product_page,  # Pass the paginated products to the template
        'total_products': total_products,
        'category_counts': category_counts,


    }

    return render(request, 'supermarket/supermarket_category.html', context)


def hot_deals(request):
    
    return render(request, 'supermarket/hot_deals.html')



# Add more view functions as needed for other pages related to the supermarket
