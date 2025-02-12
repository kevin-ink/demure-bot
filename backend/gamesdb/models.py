from django.db import models

class Game(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Wishlist(models.Model):
    user = models.CharField(max_length=150)
    games = models.ManyToManyField(Game, related_name='wishlists')
    def __str__(self):
        return f"{self.user}'s Wishlist"