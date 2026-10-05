import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
import random
import logging
import urllib.parse
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ====================== KEEP ALIVE ======================
from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "NSFW Bot is running 24/7 🔥"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

# ====================== CONFIG ======================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

# ==================== API KEYS ======================
# Gọi dữ liệu từ phần Secrets đã lưu
RULE34_USER_ID = os.environ['R34_ID']
RULE34_API_KEY = os.environ['R34_KEY']

GELBOORU_USER_ID = os.environ['GEL_ID']
GELBOORU_API_KEY = os.environ['GEL_KEY']


nsfw_cooldown = {}

BLACKLIST_TAGS = {
    "loli", "shota", "toddler", "child", "lolicon", "shotacon", "underage", "cub",
    "gore", "scat", "vore", "bestiality", "rape", "incest", "necrophilia",
}

# ====================== EVENTS ======================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot đã online: {bot.user} | Slash commands synced")
    logging.info(f"Bot khởi động thành công: {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="hentai 24/7 🔥"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    logging.error(f"[ERROR] {ctx.command} | {error}")
    await ctx.send("❌ Đã xảy ra lỗi.", delete_after=5)

# ====================== COG ======================
class NSFWBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==================== HELPER ====================
    async def is_nsfw(self, ctx_or_inter):
        channel = ctx_or_inter.channel if hasattr(ctx_or_inter, 'channel') else ctx_or_inter.channel
        if not channel.is_nsfw():
            msg = "❌ Lệnh này **chỉ dùng trong kênh 18+**!"
            if isinstance(ctx_or_inter, discord.Interaction):
                await ctx_or_inter.response.send_message(msg, ephemeral=True)
            else:
                await ctx_or_inter.send(msg, delete_after=8)
            return False
        return True

    async def nsfw_cooldown_check(self, user_id: int, seconds: int = 6):
        now = datetime.utcnow()
        if user_id in nsfw_cooldown and now - nsfw_cooldown[user_id] < timedelta(seconds=seconds):
            return False
        nsfw_cooldown[user_id] = now
        return True

    def contains_blacklist(self, tags: str) -> bool:
        tag_list = {t.lower().strip() for t in tags.split()}
        return bool(tag_list & BLACKLIST_TAGS)

    async def safe_delete(self, message: discord.Message, delay: int = 45):
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except:
            pass

    # ==================== DANBOORU FOR ACTIONS ====================
    async def fetch_danbooru(self, tag: str):
        tags = tag
        url = f"https://danbooru.donmai.us/posts.json?tags={tags}&limit=80"
        headers = {"User-Agent": "DiscordBot/1.0"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        files = [
                            p.get("file_url")
                            for p in data
                            if p.get("file_url") and p.get("file_url").lower().endswith(('.jpg', '.png', '.gif', '.mp4', '.webm'))
                        ]
                        return random.choice(files) if files else None
        except:
            return None

    async def nsfw_action(self, inter: discord.Interaction, user: discord.User, tag: str, text: str, emoji: str):
        if not await self.is_nsfw(inter):
            return
        if not await self.nsfw_cooldown_check(inter.user.id, 8):
            return await inter.followup.send("⏳ Đừng spam!", ephemeral=True)

        await inter.response.defer()
        media = await self.fetch_danbooru(tag)

        if not media:
            return await inter.followup.send(f"❌ Không tìm thấy media cho `{tag}`.")

        embed = discord.Embed(
            description=f"🔥 **{inter.user.display_name}** {text} **{user.display_name}** {emoji}",
            color=0xFF69B4
        )
        embed.set_image(url=media)
        await inter.followup.send(content=f"{user.mention}", embed=embed)

    # ==================== SLASH ACTION ====================
    @app_commands.command(name="fuck", description="💦 Chịch đối phương")
    async def fuck(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "sex", "đang chịch nát bím", "💦")

    @app_commands.command(name="bj", description="👄 Bú cu")
    async def bj(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "blowjob", "đang bú cu nhiệt tình cho", "🍆💦")

    @app_commands.command(name="anal", description="🍑 Địt lỗ hậu")
    async def anal(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "anal", "đang thông đít", "🍑🔥")

    @app_commands.command(name="kiss", description="💋 Hôn")
    async def kiss(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "kissing", "hôn muốn nát môi", "💋")

    @app_commands.command(name="lick", description="👅 Liếm")
    async def lick(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "licking", "đang liếm láp", "👅")

    @app_commands.command(name="spank", description="🍑 Vỗ mông")
    async def spank(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "spanking", "vỗ mông bành bạch", "🍑💥")

    @app_commands.command(name="finger", description="👆 Móc")
    async def finger(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "fingering", "đang móc cua", "👆💦")

    @app_commands.command(name="cum_on", description="💦 Xuất tinh lên")
    async def cum_on(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "cum", "bắn tinh xối xả lên", "🤤💦")

    @app_commands.command(name="cowgirl", description="🐴 Cowgirl")
    async def cowgirl(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "cowgirl", "đang cưỡi lên người", "🐴💦")

    @app_commands.command(name="boobs", description="🍈 Nghịch vú")
    async def boobs_action(self, inter: discord.Interaction, user: discord.User):
        await self.nsfw_action(inter, user, "breast_grab", "đang vò nát bộ loa của", "🍈")
    # ==================== SET NSFW ====================
    @app_commands.command(name="setnsfw", description="Bật/Tắt chế độ NSFW cho kênh")
    @app_commands.describe(mode="on hoặc off")
    @app_commands.default_permissions(manage_channels=True)
    async def setnsfw(self, interaction: discord.Interaction, mode: str):
        if mode.lower() not in ["on", "off"]:
            return await interaction.response.send_message("❌ Chỉ chấp nhận `on` hoặc `off`!", ephemeral=True)

        channel = interaction.channel
        try:
            if mode.lower() == "on":
                await channel.edit(nsfw=True)
                await interaction.response.send_message("✅ Đã **bật** chế độ NSFW cho kênh này! 🔥", ephemeral=False)
            else:
                await channel.edit(nsfw=False)
                await interaction.response.send_message("✅ Đã **tắt** chế độ NSFW cho kênh này.", ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot không có quyền chỉnh sửa kênh!", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Lỗi khi thay đổi cài đặt NSFW.", ephemeral=True)
    # ==================== CLEAR ====================
    @app_commands.command(name="clear", description="🧹 Xóa tin nhắn trong kênh")
    @app_commands.describe(amount="Số tin nhắn muốn xóa (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1:
            return await interaction.response.send_message("❌ Số lượng phải lớn hơn 0!", ephemeral=True)
        if amount > 100:
            amount = 100

        await interaction.response.defer(ephemeral=True)

        try:
            deleted = await interaction.channel.purge(limit=amount, bulk=True)
            await interaction.followup.send(
                f"✅ Đã xóa **{len(deleted)}** tin nhắn.", 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot không có quyền xóa tin nhắn!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send("❌ Lỗi khi xóa tin nhắn.", ephemeral=True)
            logging.error(f"Clear error: {e}")

    # ==================== R34 SLASH ====================
    @app_commands.command(name="r34", description="🔞 Tìm ảnh Rule34/Gelbooru")
    @app_commands.describe(tags="Nhập 1 đến 4 tag (cách nhau bởi khoảng trắng)", amount="Số lượng (1-8)")
    async def r34(self, interaction: discord.Interaction, tags: str, amount: int = 4):
        if not await self.is_nsfw(interaction) or self.contains_blacklist(tags):
            return
        await interaction.response.defer()
        amount = min(max(amount, 1), 8)

        boorus = [
            {"name": "rule34.xxx", "url": "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1",
             "params": {"tags": tags, "limit": 100, "user_id": RULE34_USER_ID, "api_key": RULE34_API_KEY}},
            {"name": "gelbooru", "url": "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1",
             "params": {"tags": tags, "limit": 100, "user_id": GELBOORU_USER_ID, "api_key": GELBOORU_API_KEY}},
        ]

        for booru in boorus:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(booru["url"], params=booru["params"], timeout=15) as resp:
                        if resp.status != 200: continue
                        data = await resp.json()
                        if isinstance(data, dict):
                            data = data.get("post") or data.get("posts") or []
                        if not data: continue

                        selected = random.sample(data, min(amount, len(data)))
                        for post in selected:
                            file_url = post.get("file_url") or post.get("sample_url") or post.get("image")
                            if file_url and file_url.startswith("//"):
                                file_url = "https:" + file_url
                            if file_url:
                                await interaction.followup.send(f"**{booru['name']}** | `{tags}`\n{file_url}")
                        return
            except:
                continue
        await interaction.followup.send(f"❌ Không tìm thấy cho `{tags}`")

    # Auto-complete hỗ trợ gợi ý khi nhập nhiều tag (1, 2, 3, 4 tags)
    @r34.autocomplete("tags")
    async def r34_tags_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current:
            return []

        # Tách danh sách các tag đã nhập
        tag_list = current.split(" ")
        # Lấy từ khóa cuối cùng đang gõ để gửi lên API gợi ý
        current_typing = tag_list[-1]
        # Các tag đã gõ xong trước đó
        previous_tags = " ".join(tag_list[:-1])

        if not current_typing:
            return []

        try:
            url = f"https://api.rule34.xxx/autocomplete.php?q={urllib.parse.quote(current_typing)}"
            headers = {"User-Agent": "DiscordBot/1.0"}

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        choices = []
                        for item in data:
                            tag_name = item.get("value") or item.get("label")
                            if tag_name:
                                # Ghép tag vừa chọn vào sau các tag đã gõ trước đó
                                full_tag_value = f"{previous_tags} {tag_name}".strip() if previous_tags else tag_name
                                choices.append(app_commands.Choice(name=full_tag_value[:100], value=full_tag_value))
                        return choices[:25]
        except Exception as e:
            logging.error(f"Rule34 autocomplete error: {e}")

        return []

    # ==================== SLASH /DAN ====================
    @app_commands.command(name="dan", description="🔞 Tìm ảnh/video từ Danbooru")
    @app_commands.describe(tags="Tag tìm kiếm (gõ để hiện gợi ý)", amount="Số lượng ảnh (1-8)")
    async def dan(self, interaction: discord.Interaction, tags: str, amount: int = 1):
        if not await self.is_nsfw(interaction) or self.contains_blacklist(tags):
            return

        await interaction.response.defer()
        amount = min(max(amount, 1), 8)

        formatted_tags = urllib.parse.quote("+".join(tags.strip().split()))
        url = f"https://danbooru.donmai.us/posts.json?tags={formatted_tags}&limit=100"
        headers = {"User-Agent": "DiscordBot/1.0"}

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        posts = await resp.json(content_type=None)

                        if isinstance(posts, list) and len(posts) > 0:
                            valid_posts = [p for p in posts if p.get("file_url") or p.get("large_file_url")]
                            if valid_posts:
                                selected = random.sample(valid_posts, min(amount, len(valid_posts)))
                                for post in selected:
                                    file_url = post.get("file_url") or post.get("large_file_url")
                                    if file_url.startswith("//"):
                                        file_url = "https:" + file_url
                                    await interaction.followup.send(f"**Danbooru** | `{tags}`\n{file_url}")
                                return
        except Exception as e:
            logging.error(f"Danbooru error: {e}")

        await interaction.followup.send(f"❌ Không tìm thấy kết quả nào cho tag `{tags}` trên Danbooru.")

    # Auto-complete gợi ý tag cho lệnh /dan
    @dan.autocomplete("tags")
    async def dan_tags_autocomplete(self, interaction: discord.Interaction, current: str):
        if not current:
            return []

        try:
            url = f"https://danbooru.donmai.us/autocomplete.json?search[query]={urllib.parse.quote(current)}&search[type]=tag&limit=15"
            headers = {"User-Agent": "DiscordBot/1.0"}

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        choices = []
                        for item in data:
                            tag_name = item.get("value") or item.get("label") or item.get("name")
                            if tag_name:
                                post_count = item.get("post_count") or item.get("category") or ""
                                name = f"{tag_name}"
                                if post_count:
                                    name = f"{tag_name} ({post_count})"
                                choices.append(app_commands.Choice(name=name[:100], value=tag_name))
                        return choices[:25]
        except Exception as e:
            logging.error(f"Danbooru autocomplete error: {e}")

        return []
    # ==================== DOUJIN ====================
    @app_commands.command(name="doujin", description="📚 Random doujin HentaiVNX")
    async def doujin(self, inter: discord.Interaction):
        if not await self.is_nsfw(inter): return
        await inter.response.defer()
        try:
            page = random.randint(1, 30)
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://www.hentaivnx.us/the-loai/truyen-tranh-hentai/page/{page}/") as r:
                    soup = BeautifulSoup(await r.text(), "html.parser")
                    items = soup.select(".page-item-detail")
                    item = random.choice(items)
                    title = item.select_one("h3").text.strip()
                    link = item.select_one("a")["href"]
                    thumb = item.select_one("img")["src"]

                    embed = discord.Embed(title=title, url=link, color=0xFF69B4)
                    embed.set_image(url=thumb)
                    embed.set_footer(text="Click tiêu đề để đọc")
                    await inter.followup.send(embed=embed)
        except:
            await inter.followup.send("❌ Lỗi khi lấy doujin.")
    # ==================== HENTAIZ RANDOM VIDEO (Đẹp) ====================
    @app_commands.command(name="hentaivideo", description="🎥 Random video hentai từ hentaiz.bot https://hentaivietsub.com/")
    async def hentaivideo(self, interaction: discord.Interaction):
        if not await self.is_nsfw(interaction):
            return
        if not await self.nsfw_cooldown_check(interaction.user.id, 8):
            return await interaction.response.send_message("⏳ Chờ chút bro!", ephemeral=True)

        await interaction.response.defer()

        try:
            page = random.randint(1, 50)
            url = f"https://hentaiz.bot/the-loai/video-hentai/page/{page}/"

            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
                async with session.get(url, timeout=12) as resp:
                    soup = BeautifulSoup(await resp.text(), "html.parser")

                    # Lấy các video
                    items = soup.select("div.item, article, .video-item")
                    if not items:
                        items = soup.find_all("a", href=re.compile(r'/video/'))

                    if items:
                        item = random.choice(items)
                        link_tag = item if item.name == "a" else item.find("a", href=re.compile(r'/video/'))
                        video_url = "https://hentaiz.bot" + link_tag['href']

                        # Lấy ảnh preview
                        img = item.find("img")
                        thumb = img['src'] if img and img.get('src') else None

                        title = link_tag.get('title') or "Random Hentai Video"

                        embed = discord.Embed(
                            title="🎥 Random Video Hentai",
                            description=title,
                            url=video_url,
                            color=0xFF1493
                        )
                        if thumb:
                            embed.set_image(url=thumb)
                        embed.set_footer(text="Nhấn vào tiêu đề để xem video")

                        await interaction.followup.send(embed=embed)
                        return
        except Exception as e:
            logging.error(f"Hentaiz error: {e}")

        # Fallback
        await interaction.followup.send("https://hentaiz.bot\n🎥 https://hentaivietsub.com/🎥 Vào đây chọn video random nè 🔥")
    # ==================== NEKOBOT ĐÃ SỬA ====================
    async def get_nsfw(self, ctx, media_type: str, title: str):
        if not await self.is_nsfw(ctx) or not await self.nsfw_cooldown_check(ctx.author.id, 5):
            return

        await ctx.channel.typing()

        sources = [
            f"https://nekobot.xyz/api/image?type={media_type}",
            "https://api.waifu.pics/nsfw/waifu",
        ]

        for url in sources:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()

                            image_url = data.get("message") or data.get("url")
                            if image_url and image_url.startswith("http"):
                                msg = await ctx.send(f"**{title}**:\n{image_url}")
                                #asyncio.create_task(self.safe_delete(msg, 45))
                                return
            except:
                continue

        # Fallback dùng Danbooru
        try:
            fallback_tags = {
                "hentai": "hentai",
                "hentai_gif": "hentai animated",
                "lewd": "lewd",
                "ass": "ass",
                "boobs": "breasts",
                "thighs": "thighs",
                "ahegao": "ahegao",
                "anal": "anal",
                "pussy": "pussy"
            }
            tag = fallback_tags.get(media_type, "hentai")
            media = await self.fetch_danbooru(tag.replace("_gif", ""))
            if media:
                msg = await ctx.send(f"**{title}** (fallback):\n{media}")
                #asyncio.create_task(self.safe_delete(msg, 45))
                return
        except:
            pass

        await ctx.send("❌ Không lấy được media từ mọi nguồn.", delete_after=8)

    # ==================== GỘP CÁC LỆNH ! THÀNH SLASH /neko ====================
    @app_commands.command(name="neko", description="🌸 Lấy ảnh NSFW theo thể loại (chọn từ danh sách hoặc tự nhập)")
    @app_commands.describe(type="Chọn thể loại hoặc tự nhập tên thể loại")
    @app_commands.choices(type=[
        app_commands.Choice(name="🌸 Hentai", value="hentai"),
        app_commands.Choice(name="🌸 Hentai GIF", value="hentai_gif"),
        app_commands.Choice(name="🍑 Ass", value="ass"),
        app_commands.Choice(name="🍒 Boobs", value="boobs"),
        app_commands.Choice(name="🦵 Thighs", value="thighs"),
        app_commands.Choice(name="🍑 Anal", value="anal"),
        app_commands.Choice(name="🌸 Pussy", value="pussy"),
        app_commands.Choice(name="👬 Yaoi / BL", value="yaoi"),
        app_commands.Choice(name="🎞️ Pussy GIF", value="pgif"),
        app_commands.Choice(name="🦶 Feet", value="feet"),
        app_commands.Choice(name="🍈 Paizuri", value="paizuri"),
        app_commands.Choice(name="🐱 Neko", value="neko"),
        app_commands.Choice(name="🎲 Random", value="random")
    ])
    async def slash_neko(self, interaction: discord.Interaction, type: str):
        if not await self.is_nsfw(interaction):
            return

        if not await self.nsfw_cooldown_check(interaction.user.id, 5):
            return await interaction.response.send_message("⏳ Chờ chút bro, đừng spam!", ephemeral=True)

        await interaction.response.defer()

        # Xử lý trường hợp chọn random
        if type.lower() == "random":
            types = ["hentai", "lewd", "ass", "boobs", "thighs", "ahegao", "anal", "pussy"]
            type = random.choice(types)

        # Lấy ảnh thông qua hàm helper sẵn có
        title = f"✨ {type.title()}"
        
        # Gọi nguồn API
        sources = [
            f"https://nekobot.xyz/api/image?type={type}",
            "https://api.waifu.pics/nsfw/waifu",
        ]

        image_url = None
        for url in sources:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            image_url = data.get("message") or data.get("url")
                            if image_url and image_url.startswith("http"):
                                break
            except:
                continue

        # Fallback qua Danbooru nếu API Nekobot lỗi
        if not image_url or not image_url.startswith("http"):
            fallback_tags = {
                "hentai": "hentai",
                "hentai_gif": "hentai animated",
                "lewd": "lewd",
                "ass": "ass",
                "boobs": "breasts",
                "thighs": "thighs",
                "ahegao": "ahegao",
                "anal": "anal",
                "pussy": "pussy"
            }
            tag = fallback_tags.get(type, type)
            image_url = await self.fetch_danbooru(tag.replace("_gif", ""))

        if image_url:
            await interaction.followup.send(f"**{title}**:\n{image_url}")
        else:
            await interaction.followup.send("❌ Không lấy được media từ mọi nguồn.")

    # ==================== PREFIX L.R34 & L.ZI ====================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if content.startswith(("l.r34 ", "l.zi ")):
            tag = message.content[6:].strip() if content.startswith("l.r34 ") else message.content[5:].strip()

            if not tag:
                return await message.reply("❌ Thiếu tag! Ví dụ: `L.r34 blue_hair thighs`")
            if self.contains_blacklist(tag):
                return await message.reply("❌ Tag bị blacklist.", delete_after=8)

            await message.channel.typing()

            boorus = [
                {"name": "rule34", "url": "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1",
                 "params": {"tags": tag, "limit": 30, "user_id": RULE34_USER_ID, "api_key": RULE34_API_KEY}},
                {"name": "gelbooru", "url": "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1",
                 "params": {"tags": tag, "limit": 30, "user_id": GELBOORU_USER_ID, "api_key": GELBOORU_API_KEY}},
            ]

            found = False
            for booru in boorus:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(booru["url"], params=booru["params"], timeout=12) as resp:
                            if resp.status != 200: continue
                            data = await resp.json()
                            if isinstance(data, dict):
                                data = data.get("post") or data.get("posts") or []
                            if not data: continue

                            post = random.choice(data)
                            file_url = post.get("file_url") or post.get("sample_url") or post.get("image")
                            if file_url and file_url.startswith("//"):
                                file_url = "https:" + file_url
                            if file_url:
                                msg = await message.reply(f"**{booru['name']}** | `{tag}`\n{file_url}")
                                #asyncio.create_task(self.safe_delete(msg, 40))
                                found = True
                                break
                except:
                    continue

            if not found:
                await message.reply(f"❌ Không tìm thấy cho `{tag}`", delete_after=10)

        await self.bot.process_commands(message)

    # ==================== HELP ====================
@bot.tree.command(name="help", description="Xem danh sách các lệnh của bot")
async def custom_help(ctx: discord.Interaction):
    embed = discord.Embed(title="🚀 SIÊU BOT NSFW v4.0", color=0xFF1493)
    embed.add_field(name="🔞 Action", value="`/fuck` `/bj` `/anal` `/kiss` `/lick` `/spank` `/finger` `/cum_on` `/cowgirl` `/boobs`", inline=False)
    embed.add_field(name="🔍 Search", value="`/r34 [tag] [số]`\n`/doujin`\n`L.r34 [tag]` hoặc `L.zi [tag]`", inline=False)
    embed.add_field(name="🌸 Nekobot", value="`!hentai` `!hentaigif` `!ass` `!boobs` `!thighs` `!anal` `!pussy` `!nsfwrandom` `!neko` `!feet` `!pgif` `!yaoi` `!paizuri`", inline=False)
                    
    await ctx.response.send_message(embed=embed, ephemeral=True)


# ==== LỆNH /START CHỈ CHO ADMIN ====
@bot.tree.command(name="start", description="📢 Giới thiệu bot (chỉ Admin dùng được)")
async def start(inter: discord.Interaction):
    if not inter.user.guild_permissions.administrator:
        await inter.response.send_message("⛔ Bạn không có quyền dùng lệnh này.", ephemeral=True)
        return

    await inter.response.send_message(
        "**👋 Chào mọi người đã đến với bot **`Lồn Mini`**!**\n\n"
        "🔞 Đây là bot giải trí NSFW siêu tốc dành cho server người lớn!\n\n"
        "**📌 Các chức năng chính:**\n"
        "• `/r34 [tag]` – Tìm ảnh/video từ Rule34\n"
        "• `L.zi [tag]` – Tìm nhanh ảnh Rule34 từ tin nhắn thường\n"
        "• `/fuck @user` – Làm tình với ai đó 😳\n"
        "• `/kiss @user` – Hôn người khác 💋\n"
        "• `/cum_on @user` – Xuất tinh lên người 🤤\n"
        "• `/anal @user` – Chơi lỗ hậu 😈\n"
        "• `/cowgirl @user` – Cưỡi ngựa với ai đó 🐎\n"
        "• `/bj @user` – Cho ai đó blowjob 🍆💦\n"
        "• `/lick @user` – Liếm người khác 😋\n"
        "• `/spank @user` – Đánh mông người khác 🔥\n"
        "• `/finger @user` – Móc lồn người khác 😳\n"
        "• `/boobs @user` – Show vú người khác 🍈\n"
        "• `/setnsfw [on/off]` – Bật/tắt chế độ NSFW cho kênh\n\n"
        "💡 Dùng lệnh `/setnsfw on` để bật các lệnh NSFW cho kênh!\n"
        "❗ Nếu bot không phản hồi lệnh, hãy kiểm tra xem kênh đã bật NSFW chưa dùng lệnh !help để xem các lệnh của nekobot🌸")

# ====================== RUN ======================
async def main():
    keep_alive()                   
    async with bot:
        await bot.add_cog(NSFWBot(bot))
        # Gọi token từ Secrets thay vì dán trực tiếp
        await bot.start(os.environ['DISCORD_TOKEN'])

if __name__ == "__main__":
    asyncio.run(main())
