from rest_framework import serializers
from .models import Game, Wishlist
from rest_framework.decorators import action

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['name']
    
class WishlistSerializer(serializers.ModelSerializer):
    games = GameSerializer(many=True, required=False)

    class Meta:
        model = Wishlist
        fields = ['userid', 'username', 'games', 'game_count']