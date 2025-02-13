from django.contrib import admin
from .models import Wishlist, Game

class WishlistAdmin(admin.ModelAdmin):
    list_display = ['userid', 'username', 'game_count']
    filter_horizontal = ['games']

admin.site.register(Game)
admin.site.register(Wishlist, WishlistAdmin)