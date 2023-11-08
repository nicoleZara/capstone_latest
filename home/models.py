from django.db import models

class User(models.Model):
    USER_TYPES = (
        ('guest', 'Guest'),
        ('user', 'User'),
        ('admin', 'Admin'),

        # Add other user types as needed
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    birthday = models.DateField()
    address = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)
    contact = models.CharField(max_length=15)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.username
