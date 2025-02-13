import discord
from discord.ext import commands
from utils import logger, bot_token

# SETUP INTENTS
intents = discord.Intents.default()
intents.message_content = True

# SETUP BOT
bot = commands.Bot(command_prefix='!',intents=intents, help_command=commands.DefaultHelpCommand(
    sort_commands = True,
    show_parameter_descriptions = False,
))

# BOT EVENTS
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    from itad import IsThereAnyDeal
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
    logger.info(f"Bot shutting down from shutdown command.")
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

# RUN BOT
bot.run(bot_token)