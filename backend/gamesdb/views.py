from rest_framework import viewsets
from .models import Wishlist, Game
from .serializers import WishlistSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer

    @action(detail=True, methods=['post'], url_path='add_game')
    def add_game(self, request, pk=None):
        wishlist = self.get_object()

        # Get the game data from the request
        game_name = request.data.get('name', None)
        
        if not game_name:
            raise ValidationError("Game data must include a 'name' field.")
        
        # Find or create the game based on the name
        game, created = Game.objects.get_or_create(name=game_name)
        
        # Add the game to the wishlist
        wishlist.games.add(game)

        # Return the updated wishlist
        return Response(self.get_serializer(wishlist).data)
    
    @action(detail=True, methods=['delete'], url_path='remove_game')
    def remove_game(self, request, pk=None):
        wishlist = self.get_object()

        # Get the game data from the request
        game_name = request.data.get('name', None)
        
        if not game_name:
            raise ValidationError("Game data must include a 'name' field.")
        
        # Find the game based on the name
        try:
            game = Game.objects.get(name=game_name)
        except Game.DoesNotExist:
            raise ValidationError("Game not found.")
        
        # Remove the game from the wishlist
        wishlist.games.remove(game)

        # Return the updated wishlist
        return Response(self.get_serializer(wishlist).data)