import asyncio
import discord
import logging
import requests
from discord.ext import commands, tasks
import datetime
import json

try:
    import keys
except ModuleNotFoundError:
    print('Error: keys.py not found. Bot requires the authentication present in keys.py in order to work.')

# INITIALIZE TOKENS
token = keys.bot_token
itadauth = keys.itad_token # IsThereAnyDeal

# SETUP INTENTS
intents = discord.Intents.default()
intents.message_content = True

# SETUP LOGGING
logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# SETUP TIME
time = datetime.time(hour=20)

# SETUP BOT
bot = commands.Bot(command_prefix='!',intents=intents, help_command=commands.DefaultHelpCommand(
    sort_commands = True,
    show_parameter_descriptions = False,
))

# BOT EVENTS
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    await bot.add_cog(IsThereAnyDeal(bot))
    logger.info(f"Registered ITAD cog to bot.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)
    
# PEACEFUL SHUTDOWN
@bot.command(hidden=True)
async def shutdown(ctx):
    '''Shuts down bot after saving data to disc (admin only command)'''
    if not ctx.author.guild_permissions.administrator:
        return
    itad_cog = bot.get_cog("IsThereAnyDeal")
    itad_cog.save()
    await bot.close()

# COMMAND NOT FOUND ERRORS
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"```Invalid command. !help for a list of valid commands.```")
        return
    raise error
    
class IsThereAnyDeal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracking = self.load()

    def load(self):
        '''Load's tracking dict from disc'''
        try:
            with open("data.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        
    def save(self):
        '''Saves tracking dict to disc'''
        with open("data.json", "w") as f:
            json.dump(self.tracking, f)
    
    @tasks.loop(time=time)
    async def checkDeals(self):
        '''IMPLEMENTATION IN PROGRESS'''
        return
    
    @commands.command(hidden=True)
    async def cwl(self, ctx, *, name = None):
        '''Clears entire wishlist or the first arg of command from wishlist (admin only command).'''
        if not ctx.author.guild_permissions.administrator:
            return
        logger.info(f"A clear wishlist command was executed.")

        if not name:
            self.tracking.clear()
            return

        for key, value in self.tracking.items():
            if name == value:
                self.tracking.pop(key)
                return
            
        logger.info(f"{name} does not exist in wishlist.")
    
    @commands.command()
    async def wishlist(self, ctx):
        '''Displays currently tracked games.'''
        result = []
        i = 1
        for name in self.tracking.values():
            result.append(f"1. {name}")
            i += 1

        if result:
            await ctx.send(embed = discord.Embed(title="Currently tracked games:", description=f"\n".join(result)))
        else:
            await ctx.send(embed = discord.Embed(description=f"Bot is currently not tracking any games."))

    @commands.command()
    async def itad(self, ctx, *, name: str = None):
        """Find current best price of game by name."""

        if not name:
            # name argument not provided
            await ctx.send("```Usage: !itad [name]```")
            return
        
        # send request to get game id from title
        payload = {"title": name, "key": itadauth}
        r = requests.get("https://api.isthereanydeal.com/games/lookup/v1", params=payload)
        if r.status_code != 200:
            # api error
            await ctx.send(embed=discord.Embed(description="Service error. Try again later."))
            return
        data = r.json()
        if not data.get("found"):
            # game not found from title
            await ctx.send(embed=discord.Embed(description="Game could not be identified from provided name. Double check your spelling \
                                               and try again."))
            return
        game = data.get("game")
        game_id = game.get("id")
        name = game.get("title")
        
        # request game's lowest price using game id
        params = {"key": itadauth}
        body = [game_id]
        response = requests.post("https://api.isthereanydeal.com/games/overview/v2", params=params, json=body)
        if response.status_code != 200:
            # api error
            await ctx.send(embed=discord.Embed(description="Service error. Try again later."))
            return
        data = response.json()
        prices = data.get("prices", [])
        curr = prices[0].get("current", {})
        if not curr:
            # curr is None
            await ctx.send(embed=discord.Embed(description="Unknown error. Try again later."))
            return
        deal_price = curr.get("price", {}).get("amount")
        reg_price = curr.get("regular", {}).get("amount")
        shop_name = curr.get("shop", {}).get("name")
        if deal_price < reg_price:
            await ctx.send(embed=discord.Embed(title=name, description=f"Current best price: ${deal_price} {shop_name}"))
            return
        
        msg = await ctx.send(embed=discord.Embed(title=name, description=f"There are currently no deals on {name}.\nRegular price: ${reg_price} {shop_name}\n \
                                               React to this message with 👀 if you want to be reminded when this game goes on sale anywhere."))
        
        # check for reaction
        def check(reaction, user):
            return user == ctx.author and (reaction.emoji) == '👀' and reaction.message.id == msg.id
        
        # if reaction meets criteria, add game to tracking
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            return
        else:
            if game_id not in self.tracking:
                self.tracking[game_id] = name
                await ctx.send(embed=discord.Embed(description=f"This text channel will be notified whenever {name} goes on sale anywhere."))
            else:
                await ctx.send(embed=discord.Embed(description=f"{name} is already being tracked for deals."))

bot.run(token)
