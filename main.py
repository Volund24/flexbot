import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from shared.database import init_db

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")

intents = discord.Intents.default()
intents.message_content = True # Required for some commands if using prefix, but we are likely using slash commands
intents.members = True

class CoreFlexbot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Load Cogs
        await self.load_extension("cogs.wallet")
        await self.load_extension("cogs.flex")
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.help")
        
        # Sync commands
        # We sync globally so commands are available in all guilds the bot joins.
        # This can take up to 1 hour to propagate, but ensures multi-guild support.
        # If immediate testing is needed in a specific guild, uncomment the guild sync block below temporarily.
        
        # if GUILD_ID and GUILD_ID.isdigit():
        #     guild = discord.Object(id=int(GUILD_ID))
        #     self.tree.copy_global_to(guild=guild)
        #     await self.tree.sync(guild=guild)
        #     print(f"Commands synced to guild {GUILD_ID}")
        # else:
        print("Syncing commands globally (this may take up to 1 hour to propagate)...")
        await self.tree.sync()
            
        print("Bot is ready and commands synced.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        try:
            init_db()
            print("Database initialized.")
        except Exception as e:
            print(f"Database initialization failed: {e}")

bot = CoreFlexbot()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in .env")
    else:
        bot.run(TOKEN)
