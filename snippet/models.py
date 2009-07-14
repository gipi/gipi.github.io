from django.db import models
from django.contrib.auth.models import User

from tagging.fields import TagField

class Entry(models.Model):
    content = models.CharField(max_length=1000)
    user = models.ForeignKey(User)

class Blog(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=1000)
    creation_date = models.DateTimeField(auto_now_add=True)
    tags = TagField()
