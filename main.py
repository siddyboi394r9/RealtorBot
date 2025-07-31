import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import requests
import nest_asyncio
import asyncio

# ---- Configuration ----
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"  # Replace with your bot token
COMMAND_PREFIX = "!"

# ---- Initialize Bot ----
intents = discord.Intents.default()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
nest_asyncio.apply()

# ---- Real Listings Fetcher ----
def get_real_listings(city, max_price, min_bedrooms):
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    payload = {
        "CultureId": 1,
        "ApplicationId": 1,
        "PropertySearchTypeId": 1,
        "TransactionTypeId": 2,
        "RecordsPerPage": 3,
        "MaximumResults": 3,
        "Query": city,
        "PriceMax": max_price,
        "BedRange": f"{min_bedrooms}-0",
    }

    try:
        res = requests.post("https://api2.realtor.ca/Listing.svc/PropertySearch_Post", headers=headers, json=payload)
        results = res.json()
        return [
            {
                "title": l.get("Property", {}).get("Address", {}).get("Text", "No title"),
                "price": l.get("Property", {}).get("Price", "N/A"),
                "bedrooms": l.get("Building", {}).get("BedroomsTotal", "N/A"),
                "url": f"https://www.realtor.ca/real-estate/{l.get('Id')}",
                "image": l.get("Property", {}).get("Photo", {}).get("HighResPath")
                         or l.get("Property", {}).get("Photo", {}).get("MedResPath")
                         or "https://via.placeholder.com/400x200.png?text=No+Image"
            } for l in results.get("Results", [])
        ]
    except Exception as e:
        print(f"Error fetching real listings: {e}")
        return []

# ---- Interactive Filters View ----
class FilterView(View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.city = None
        self.max_price = None
        self.min_bedrooms = None
        self.add_item(CityDropdown(self))
        self.add_item(PriceDropdown(self))
        self.add_item(BedroomDropdown(self))
        self.add_item(SearchButton(self))

class CityDropdown(Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=city) for city in ["Toronto", "Mississauga", "Vancouver", "Ottawa", "Calgary"]]
        super().__init__(placeholder="Select a city", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.city = self.values[0]
        await interaction.response.send_message(f"✅ City set to **{self.values[0]}**", ephemeral=True)

class PriceDropdown(Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="$500,000"), discord.SelectOption(label="$750,000"),
            discord.SelectOption(label="$1,000,000"), discord.SelectOption(label="$1,500,000")
        ]
        super().__init__(placeholder="Select max price", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.max_price = int(self.values[0].replace("$", "").replace(",", ""))
        await interaction.response.send_message(f"✅ Max price set to **{self.values[0]}**", ephemeral=True)

class BedroomDropdown(Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=str(i)) for i in range(1, 6)]
        super().__init__(placeholder="Select min bedrooms", options=options, row=2)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.min_bedrooms = int(self.values[0])
        await interaction.response.send_message(f"✅ Min bedrooms set to **{self.values[0]}**", ephemeral=True)

class SearchButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="🔍 Search Homes", style=discord.ButtonStyle.success, row=3)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        city = self.parent_view.city
        price = self.parent_view.max_price
        beds = self.parent_view.min_bedrooms

        if not all([city, price, beds]):
            await interaction.response.send_message("⚠️ Please select all filters before searching.", ephemeral=True)
            return

        listings = get_real_listings(city, price, beds)
        await interaction.response.send_message(f"🏠 Showing listings for **{city}** under **${price:,}** with at least **{beds}** bedrooms:", ephemeral=False)

        if not listings:
            await interaction.followup.send("No results found.")
            return

        for listing in listings:
            embed = discord.Embed(title=listing["title"], url=listing["url"], description=listing["price"])
            embed.add_field(name="Bedrooms", value=listing["bedrooms"])
            embed.set_image(url=listing["image"])
            await interaction.followup.send(embed=embed)

# ---- Bot Command ----
@bot.command(name="findhome")
async def find_home(ctx):
    view = FilterView(ctx)
    await ctx.send("Let’s find you a home! Choose your filters below:", view=view)

# ---- Run Bot in Jupyter Notebook ----
async def start_bot():
    await bot.start(DISCORD_TOKEN)

await start_bot()

