from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    room_name = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
