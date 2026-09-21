import os
import discord
from discord import app_commands
from discord.ext import commands

# إعداد الصلاحيات والـ Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class ModBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # مزامنة أوامر السلاش تلقائياً
        await self.tree.sync()
        print("✅ تم مزامنة أوامر السلاش بنجاح!")

bot = ModBot()

# قائمة معرفات (IDs) المطورين المحميين
DEV_IDS = [1182602010651017298, 1078717086035103806]

def is_developer(user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم ضمن قائمة المطورين المحميين"""
    return user_id in DEV_IDS

@bot.event
async def on_ready():
    print(f"🚀 البوت جاهز ويعمل باسم: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="إدارة السيرفر | /"))

# --- معالجة أخطاء الأوامر لضمان الاستقرار ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        msg = "❌ ليس لديك الصلاحيات الكافية لاستخدام هذا الأمر."
    elif isinstance(error, app_commands.CommandOnCooldown):
        msg = f"⏳ يرجى الانتظار {error.retry_after:.1f} ثانية قبل إعادة الاستخدام."
    else:
        msg = "❌ حدث خطأ أثناء تنفيذ الأمر."
    
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)

# ---------------- الأوامر الإدارية ----------------

# 1. أمر مسح الرسائل المختصر (/c)
@bot.tree.command(name="c", description="مسح عدد من الرسائل من الشات")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.checks.cooldown(1, 3, key=lambda i: (i.guild_id, i.user.id))
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    if amount < 1 or amount > 100:
        await interaction.followup.send("⚠️ اختر عدداً بين 1 و 100.")
        return
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم مسح {len(deleted)} رسالة بنجاح.")

# 2. أمر الحظر المختصر (/b)
@bot.tree.command(name="b", description="حظر عضو من السيرفر")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    await interaction.response.defer()
    
    if is_developer(member.id):
        await interaction.followup.send("🛡️ لا يمكنك تطبيق الأوامر الإدارية على مطور البوت!")
        return

    await member.ban(reason=reason)
    await interaction.followup.send(f"🔨 تم حظر {member.mention} | السبب: {reason}")

# 3. أمر الطرد المختصر (/k)
@bot.tree.command(name="k", description="طرد عضو من السيرفر")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    await interaction.response.defer()

    if is_developer(member.id):
        await interaction.followup.send("🛡️ لا يمكنك تطبيق الأوامر الإدارية على مطور البوت!")
        return

    await member.kick(reason=reason)
    await interaction.followup.send(f"👞 تم طرد {member.mention} | السبب: {reason}")

# 4. أمر الإسكات المختصر بالدقائق (/t)
@bot.tree.command(name="t", description="إسكات عضو لعدد معين من الدقائق")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout_cmd(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "لم يتم تحديد سبب"):
    await interaction.response.defer()

    if is_developer(member.id):
        await interaction.followup.send("🛡️ لا يمكنك تطبيق الأوامر الإدارية على مطور البوت!")
        return

    duration = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.followup.send(f"🔇 تم إسكات {member.mention} لمدة {minutes} دقيقة | السبب: {reason}")

# 5. أمر فك الإسكات (/unt)
@bot.tree.command(name="unt", description="إلغاء الإسكات عن عضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def untimeout(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()
    await member.timeout(None)
    await interaction.followup.send(f"🔊 تم فك الإسكات عن {member.mention}.")

# 6. أمر الوضع البطئ (/sm)
@bot.tree.command(name="sm", description="تحديد زمن الانتظار بين الرسائل بالثواني (0 للإلغاء)")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.response.defer()
    await interaction.channel.edit(slowmode_delay=seconds)
    if seconds == 0:
        await interaction.followup.send("⚡ تم إيقاف الوضع البطئ في هذا الروم.")
    else:
        await interaction.followup.send(f"🐢 تم ضبط الوضع البطئ إلى {seconds} ثانية.")

# 7. أمر تغيير اللقب (/nick)
@bot.tree.command(name="nick", description="تغيير اسم عضو داخل السيرفر")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nickname(interaction: discord.Interaction, member: discord.Member, new_nick: str):
    await interaction.response.defer()

    if is_developer(member.id):
        await interaction.followup.send("🛡️ لا يمكنك تطبيق الأوامر الإدارية على مطور البوت!")
        return

    await member.edit(nick=new_nick)
    await interaction.followup.send(f"🏷️ تم تغيير لقب {member.mention} إلى: {new_nick}")

# تشغيل البوت عبر متغير البيئة
token = os.getenv("DISCORD_TOKEN")
bot.run(token)
