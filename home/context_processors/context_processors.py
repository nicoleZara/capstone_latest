from collections import defaultdict
from pymongo import MongoClient  # Import the MongoClient
import re

client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System']
collection = db['Sept_FInal_Final']

def category_counts(request):
    # Connect to MongoDB
    # Retrieve all products from the MongoDB collection
    all_products = list(collection.find())

    # Calculate the category counts for all categories
    category_counts = defaultdict(int)
    for product in all_products:
        category = product['category'].replace(' ', '_')  # Replace space with underscore
        category_counts[category] += 1

    return {'category_counts': dict(category_counts)}
