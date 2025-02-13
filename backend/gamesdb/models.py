from django.db import models

class Game(models.Model):
    name = models.CharField(primary_key=True, max_length=255, unique=True)

    def __str__(self):
        return self.name

class Wishlist(models.Model):
    userid = models.BigIntegerField(primary_key=True, unique=True)
    username = models.CharField(max_length=150)
    games = models.ManyToManyField(Game, related_name='wishlists', blank=True)

    def __str__(self):
        return f"{self.username}'s wishlist"
    
    def game_count(self):
        return self.games.count()