from discord.ext import commands, tasks
import discord
import asyncio
import aiohttp
from utils import logger, itad_auth, db_token

class IsThereAnyDeal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BASE_URL = "https://api.isthereanydeal.com"
        self.ERROR_MSG = "Service error. Try again later."
        self.BACKEND_URL = "http://127.0.0.1:8000/api/wishlist/"
        self.HEADER = {
            'Authorization': f'Token {db_token}'
        }

    async def fetch(self, session, url, method='GET', **kwargs):
        async with session.request(method, url, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.info(f"Bad Response: \n{await response.text()}")
                return None

    @commands.command()
    async def unwish(self, ctx, *, name: str = None):
        if not name:
            await ctx.send("```Usage: !unwish [game name]```")
            return
        
        embed = await ctx.send(embed=discord.Embed(description=f"Removing {name} from your wishlist..."))
        url = f"{self.BACKEND_URL}{ctx.author.id}/"
        async with aiohttp.ClientSession(header=self.HEADER) as session:
            wishlist = await self.fetch(session, url)
            if not wishlist:
                await embed.edit(embed=discord.Embed(description="Unexpected error retrieving your wishlist."))
                return
            
            games = wishlist.get('games', [])
            game_in_wishlist = next((game for game in games if game['name'] == name), None)
            if not game_in_wishlist:
                await embed.edit(embed=discord.Embed(description=f"{name} is not currently being tracked for you."))
                return
        
        response = await self.fetch(session, f"{url}remove_game/", method='DELETE', json={"name": name})
        if response:
            await embed.edit(embed=discord.Embed(description=f"{name} has been removed from your wishlist."))
        else:
            await embed.edit(embed=discord.Embed(description="Unexpected error removing game from your wishlist."))


    @commands.command()
    async def wishlist(self, ctx):
        """Display user's wishlist."""
        embed = await ctx.send(embed=discord.Embed(description="Retrieving your wishlist..."))

        url = f"{self.BACKEND_URL}{ctx.author.id}/"
        async with aiohttp.ClientSession(headers=self.HEADER) as session:
            wishlist = await self.fetch(session, url)
            if not wishlist:
                await embed.edit(embed=discord.Embed(description="Unexpected error retrieving your wishlist."))
                return
            
            games = wishlist.get('games', [])
            if not games:
                await embed.edit(embed=discord.Embed(description="Your wishlist is currently empty."))
                return
            
            game_list = "\n".join([game['name'] for game in games])
            await embed.edit(embed=discord.Embed(title=f"{ctx.author.name.replace('_', ' ')}'s Wishlist", description=game_list))
    
    async def create_wishlist(self, ctx):
        wishlist_data = {
            "userid": ctx.author.id,
            "username": ctx.author.name
        }
        async with aiohttp.ClientSession(headers=self.HEADER) as session:
            response = await self.fetch(session, self.BACKEND_URL, method='POST', json=wishlist_data)
            if response:
                logger.info(f"Wishlist created for {ctx.author.name}.")
            else:
                logger.info("Error creating wishlist.")

    @commands.command()
    async def itad(self, ctx, *, name: str = None):
        """Find current best price of game by name."""
        if not name:
            await ctx.send("```Usage: !itad [name]```")
            return
    
        embed = discord.Embed(description=f"Searching for {name} on IsThereAnyDeal...")
        embed_msg = await ctx.send(embed=embed)
        
        game_data = self.get_game_by_name(name, itad_auth)
        if not game_data or not game_data.get("found"):
            await self.send_error(ctx, "Game could not be identified. Double-check your spelling and try again.")
            await embed_msg.delete()
            return
        
        game = game_data.get("game")
        game_id = game.get("id")
        game_name = game.get("title")
        
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

        await self.handle_reaction(ctx, msg, game_name)
    
    async def get_game_by_name(self, name):
        """Fetch game details by name."""
        async with aiohttp.ClientSession() as session:
            payload = {"title": name, "key": itad_auth}
            return await self.fetch(session, f"{self.BASE_URL}/games/lookup/v1", params=payload)
    
    async def get_game_prices(self, game_id):
        """Fetch game prices by game ID."""
        async with aiohttp.ClientSession() as session:
            params = {"key": itad_auth}
            body = [game_id]
            return await self.fetch(session, f"{self.BASE_URL}/games/prices/", params=params, json=body)

    async def handle_reaction(self, ctx, msg, game_name):
        def check(reaction, user):
            return user == ctx.author and (reaction.emoji) == '👀' and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            return
        
        await self.add_game_to_wishlist(ctx, game_name, user.id)
    
    async def send_error(self, ctx, message):
        """Send a standardized error message."""
        if message == self.ERROR_MSG:
            logger.info(f"Service error occurred from IsThereAnyDeal API.")
        await ctx.send(embed=discord.Embed(description=message))

    async def add_game_to_wishlist(self, ctx, game_name, user_id):
        url = f"{self.BACKEND_URL}{user_id}/"
        async with aiohttp.ClientSession(headers=self.HEADER) as session:
            wishlist = await self.fetch(session, url)
            if not wishlist:
                await ctx.send(embed=discord.Embed(description="Unexpected error retrieving your wishlist."))
                return
            
            games = wishlist.get('games', [])
            if any(game['name'] == game_name for game in games):
                await ctx.send(embed=discord.Embed(description=f"{game_name} is already being tracked for you."))
                return
            
            response = await self.fetch(session, f"{url}add_game/", method='POST', json={"name": game_name})
            if response:
                await ctx.send(embed=discord.Embed(description=f"{game_name} has been added to your wishlist and you will be notified whenever the game goes on sale anywhere."))
            else:
                await ctx.send(embed=discord.Embed(description="Unexpected error adding game to your wishlist."))