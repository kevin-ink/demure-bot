from discord.ext import commands, tasks
import discord
import requests
import asyncio
from utils import logger, itad_auth, db_token

class IsThereAnyDeal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BASE_URL = "https://api.isthereanydeal.com"
        self.ERROR_MSG = "Service error. Try again later."
        self.BACKEND_URL = "http://127.0.0.1:8000/api/wishlist/"
        self.HEADER = {
            'Authorization ': f'Token {db_token}'
        }

    @commands.command()
    async def wishlist(self, ctx):
        """Display user's wishlist."""
        headers = {
            'Authorization': f'Token {db_token}'
        }
        url = f"{IsThereAnyDeal.BACKEND_URL}{ctx.author.id}/"
    
    async def create_wishlist(self, ctx):
        wishlist_data = {
            "userid": ctx.author.id,
            "username": ctx.author.name
        }
        create_wishlist_response = requests.post(self.BACKEND_URL, data=wishlist_data, headers=self.HEADER)
        if create_wishlist_response.status_code == 201:
            logger.info(f"Wishlist created for {ctx.author.name}.")
        else:
            logger.info(f"Bad Response: \n{create_wishlist_response.content}")
            logger.info("Error creating wishlist.")
        

    @commands.command()
    async def itad(self, ctx, *, name: str = None):
        """Find current best price of game by name."""

        if not name:
            # name argument not provided
            await ctx.send("```Usage: !itad [name]```")
            return
    
        embed = discord.Embed(description=f"Searching for {name} on IsThereAnyDeal...")
        embed_msg = await ctx.send(embed=embed)
        
        # fetch game details
        game_data = self.get_game_by_name(name, itad_auth)
        if not game_data or not game_data.get("found"):
            await self.send_error(ctx, "Game could not be identified. Double-check your spelling and try again.")
            await embed_msg.delete()
            return
        
        game = game_data.get("game")
        game_id = game.get("id")
        game_name = game.get("title")
        
        # fetch game price
        price_data = self.get_game_prices(game_id, itad_auth)
        if not price_data:
            await embed_msg.delete()
            await self.send_error(ctx, self.ERROR_MESSAGE)
            return

        prices = price_data.get("prices", [])
        current_price = prices[0].get("current", {}) if prices else None

        if not current_price:
            await embed_msg.delete()
            await self.send_error(ctx, "Unable to retrieve price information. Try again later.")
            return
        
        deal_price = current_price.get("price", {}).get("amount", "N/A")
        reg_price = current_price.get("regular", {}).get("amount", "N/A")
        shop_name = current_price.get("shop", {}).get("name", "Unknown")

        if deal_price < reg_price:
            msg = await embed_msg.edit(embed=discord.Embed(title=game_name, description=f"Current best price: ${deal_price} at {shop_name}.\n"
                                              f"React with 👀 to add the game to your wishlist."))
        else:
            msg = await embed_msg.edit(embed=discord.Embed(
                title=name, description=f"There are currently no deals on {name}.\n"
                                        f"Regular price: ${reg_price} from {shop_name}\n"
                                        f"React with 👀 to add the game to your wishlist."))

        await self.handle_reaction(ctx, msg, game_id, game_name)
    
    def get_game_by_name(self, name, api_key):
        """Fetch game details by name."""
        payload = {"title": name, "key": api_key}
        response = requests.get(f"{self.BASE_URL}/games/lookup/v1", params=payload)
        return response.json() if response.status_code == 200 else None
    
    def get_game_prices(self, game_id, api_key):
        """Fetch game prices by game ID."""
        params = {"key": api_key}
        body = [game_id]
        response = requests.post(f"{self.BASE_URL}/games/overview/v2", params=params, json=body)
        return response.json() if response.status_code == 200 else None

    async def handle_reaction(self, ctx, msg, game_id, name):
        # check for reaction
        def check(reaction, user):
            return user == ctx.author and (reaction.emoji) == '👀' and reaction.message.id == msg.id
        
        # if reaction meets criteria, add game to tracking
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            return
        
        await self.add_game_to_wishlist(ctx, name, user.id, user.name)
    
    async def send_error(self, ctx, message):
        """Send a standardized error message."""
        if message == self.ERROR_MSG:
            logger.info(f"Service error occurred from IsThereAnyDeal API.")
        await ctx.send(embed=discord.Embed(description=message))

    @commands.command()
    async def testdb(self, ctx):
        await self.add_game_to_wishlist(ctx, "Test Game", ctx.author.id, ctx.author.name)

    async def add_game_to_wishlist(self, ctx, game_name, user_id):
        headers = {
            'Authorization': f'Token {db_token}'
        }
        url = f"{self.BACKEND_URL}{user_id}/"

        async def add_game():
            add_game_url = f"{url}add_game/"
            add_game_data = {"name": game_name}
            add_game_response = requests.post(add_game_url, data=add_game_data, headers=headers)
            if add_game_response.status_code == 200:
                await ctx.send(embed=discord.Embed(description=f"{game_name} has been added to your wishlist and you will be notified whenever the game goes on sale anywhere."))
            else:
                logger.info(f"Error adding {game_name} to wishlist for {user_id}.")
                logger.info(f"Bad Response: \n{add_game_response.content}")
                await ctx.send(embed=discord.Embed(description=f"Unexpected error adding game to your wishlist.")) 

        try:
            response = requests.get(url, headers=headers)
            await self.create_wishlist(ctx)
            await add_game()
        except:
            logger.info(f"Error connecting to database.")
            await ctx.send(embed=discord.Embed(description="Unknown error occured when adding game to your wishlist."))
            return

        if response.status_code == 404:
            
                return
        elif response.status_code != 200:
            logger.info(f"Bad Response: \n{response.content}")
            return
        
        wishlist = response.json()
        games = wishlist.get('games', [])
        game_in_wishlist = any(game['name'] == game_name for game in games)
        
        if game_in_wishlist:
            await ctx.send(embed=discord.Embed(description=f"{game_name} is already being tracked for you. Use command !wishlist to see your currently tracked games."))
        else:
            await add_game()