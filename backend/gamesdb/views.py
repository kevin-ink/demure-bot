from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Wishlist
from .serializers import WishlistSerializer

class Wishlist(APIView):
    def get(self, request, username):
        try:
            wishlist = Wishlist.objects.get(username=username)
            serializer = WishlistSerializer(wishlist)
            return Response(serializer.data)
        except:
            return Response({"error": "User or wishlist not found"}, status=404)
    