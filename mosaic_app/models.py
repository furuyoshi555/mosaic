from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
# Create your models here.

class UserProfileInfo(models.Model):

    user = models.OneToOneField(User,on_delete=models.CASCADE, related_name="profile")


class MainImageInfo(models.Model):

    user_id = models.IntegerField()
    main_image = models.ImageField(upload_to ="main_images",blank=True)
    data = models.DateTimeField(default=datetime.now)


class MosaicArtInfo(models.Model):

    user_id = models.IntegerField()
    mosaic_art = models.ImageField(upload_to="mosaic_arts")
    data = models.DateTimeField(default=datetime.now)