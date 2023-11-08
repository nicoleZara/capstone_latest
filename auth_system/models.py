from django.db import models
from django.contrib.auth.models import User
from pymongo import MongoClient
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin



client = MongoClient('mongodb+srv://capstonesummer1:9Q8SkkzyUPhEKt8i@cluster0.5gsgvlz.mongodb.net/')
db = client['Product_Comparison_System'] 
user_collection = db['Users']
# user_collection = db['Account']


class UserProfile(models.Model):
# class UserProfile(AbstractBaseUser, PermissionsMixin):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    purpose = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default_profile.png')  # Add this field
    
    region = models.CharField(max_length=50, blank=True, null=True)  # Add this field
    city = models.CharField(max_length=50, blank=True, null=True)  # Add this field

    # for verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)

     # Add the field for password reset token
    password_reset_token = models.CharField(max_length=255, blank=True, null=True)


    # Add any other fields you need

    def __str__(self):
        return self.user.username

class MongoDBUser:
    def __init__(self, user_id, username, email, password, confirm_password, fname, lname, gender, birthday, region, city, age, purpose):
        self.user_id = user_id 
        self.username = username
        self.email = email
        self.password = password
        self.confirm_password = confirm_password
        self.fname = fname
        self.lname = lname
        self.gender = gender
        self.birthday = birthday
        self.region = region
        self.city = city
        self.age = age
        self.purpose = purpose


    def save(self):
        user_data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'confirm_password': self.confirm_password,
            'fname': self.fname,
            'lname': self.lname,
            'gender': self.gender,
            'birthday': self.birthday,
            'region': self.region,
            'city': self.city,
            'age': self.age,
            'purpose': self.purpose,
        }
        user_collection.insert_one(user_data)

    @classmethod
    def find_by_username(cls, username):
        return user_collection.find_one({'username': username})
    