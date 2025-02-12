from rest_framework import serializers
from .models import Game, Wishlist

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'name']
    
class WishlistSerializer(serializers.ModelSerializer):
    games = GameSerializer(many=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'games']