import os
import threading
from datetime import datetime, timezone

from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
from dotenv import load_dotenv


# =========================
# LOAD .ENV
# =========================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "❌ DISCORD_TOKEN is missing from your .env file!"
    )


# =========================
# CONFIG
# =========================

ROLE_NAME = "Paid Joiner"
MIN_ACCOUNT_MONTHS = 4


# =========================
# RENDER HEALTH SERVER
# =========================

PORT = int(os.getenv("PORT", "10000"))


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain"
        )
        self.end_headers()

        self.wfile.write(
            b"Bounty_Vault is online!"
        )

    def log_message(self, format, *args):
        # Keep Render logs clean
        return


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"🌐 Health server listening on port {PORT}"
    )

    server.serve_forever()


# Start health server
health_thread = threading.Thread(
    target=start_health_server,
    daemon=True
)

health_thread.start()


# =========================
# DISCORD INTENTS
# =========================

intents = discord.Intents.default()

intents.members = True
intents.message_content = True


# =========================
# BOT
# =========================

bot = commands.Bot(
    command_prefix="-",
    intents=intents
)


# =========================
# BOT STARTUP
# =========================

@bot.event
async def on_ready():

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(
            name="Bounty Vault"
        )
    )

    print(
        f"✅ Logged in as {bot.user}"
    )

    print(
        f"🆔 Bot ID: {bot.user.id}"
    )

    print(
        "🏴‍☠️ Bounty_Vault is ONLINE!"
    )


# =========================
# PING
# =========================

@bot.command(name="ping")
async def ping(ctx):

    await ctx.send(
        "🏴‍☠️ **Bounty_Vault is ONLINE!** 🟢"
    )


# ============================================================
# CALCULATE DISCORD ACCOUNT AGE
# ============================================================

def calculate_account_age(user):

    created_at = user.created_at

    now = datetime.now(timezone.utc)

    # Calculate total days
    total_days = (
        now - created_at
    ).days

    # Approximate months
    total_months = total_days // 30

    years = total_months // 12
    months = total_months % 12

    remaining_days = (
        total_days
        - (total_months * 30)
    )

    # =========================
    # FORMAT AGE
    # =========================

    parts = []

    if years > 0:

        parts.append(
            f"{years} year"
            + ("s" if years != 1 else "")
        )

    if months > 0:

        parts.append(
            f"{months} month"
            + ("s" if months != 1 else "")
        )

    if remaining_days > 0:

        parts.append(
            f"{remaining_days} day"
            + ("s" if remaining_days != 1 else "")
        )

    if not parts:

        parts.append("Less than 1 month")

    age_text = ", ".join(parts)

    return age_text, total_months


# ============================================================
# GIVE PAID JOINER ROLE
# ============================================================

async def give_paid_joiner_role(
    guild,
    target
):

    role = discord.utils.get(
        guild.roles,
        name=ROLE_NAME
    )

    # Role doesn't exist
    if role is None:

        return False, (
            f"⚠️ The role `{ROLE_NAME}` "
            f"does not exist."
        )

    # Already has role
    if role in target.roles:

        return True, (
            f"ℹ️ {target.mention} already has "
            f"the **{ROLE_NAME}** role."
        )

    # Check bot hierarchy
    if role >= guild.me.top_role:

        return False, (
            f"❌ I can't give the `{ROLE_NAME}` role.\n\n"
            f"Move my bot role **above** "
            f"`{ROLE_NAME}` in Server Settings → Roles."
        )

    # Give role
    try:

        await target.add_roles(
            role,
            reason=(
                "Passed Bounty_Vault "
                "eligibility check"
            )
        )

    except discord.Forbidden:

        return False, (
            "❌ Discord denied the role assignment.\n\n"
            "Make sure I have **Manage Roles** "
            "and my bot role is above `Paid Joiner`."
        )

    except discord.HTTPException:

        return False, (
            "❌ Discord rejected the role assignment. "
            "Please try again."
        )

    return True, (
        f"🎟️ Granted the **{ROLE_NAME}** role!"
    )


# ============================================================
# REAL VERIFICATION
# ============================================================

async def run_verification(
    interaction
):

    target = interaction.user
    guild = interaction.guild

    if guild is None:

        await interaction.followup.send(
            "❌ **Verification Unavailable**\n\n"
            "This system can only be used inside a server.",
            ephemeral=True
        )

        return


    # =========================
    # PROFILE PICTURE CHECK
    # =========================

    if target.avatar is None:

        await interaction.followup.send(
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "   🦅 **FALCON • VERIFICATION**\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

            "👤 **Identity:** "
            f"`{target.name}`\n"
            "🖼️ **Profile:** ❌ Not detected\n\n"

            "🚫 **VERIFICATION DENIED**\n"
            "A profile picture is required "
            "to continue.",
            ephemeral=True
        )

        return


    # =========================
    # START MESSAGE
    # =========================

    await interaction.followup.send(
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "   🦅 **FALCON • VERIFICATION**\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        f"👤 **User:** `{target.name}`\n\n"

        "🔎 **Running security checks...**\n"
        "🖼️ Profile integrity ........ `✓`\n"
        "📡 Account intelligence ...... `ACTIVE`\n"
        "🛡️ Eligibility scan .......... `RUNNING`\n\n"

        "⏳ **Analyzing account data...**",
        ephemeral=True
    )


    # =========================
    # CALCULATE ACCOUNT AGE
    # =========================

    age_text, total_months = (
        calculate_account_age(target)
    )


    # =========================
    # TOO YOUNG
    # =========================

    if total_months < MIN_ACCOUNT_MONTHS:

        await interaction.followup.send(
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "   🦅 **FALCON • SCAN COMPLETE**\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

            f"👤 **Account:** `{target.name}`\n"
            "🖼️ **Profile:** `VERIFIED` ✓\n"
            f"📆 **Account Age:** `{age_text}`\n"
            "🛡️ **Eligibility:** `DENIED` ✕\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n"

            "🚫 **NOT ELIGIBLE**\n\n"

            f"Your account must be at least "
            f"**{MIN_ACCOUNT_MONTHS} months old**.\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏴‍☠️ `Bounty_Vault • Security Division`",
            ephemeral=True
        )

        return


    # =========================
    # GIVE ROLE
    # =========================

    success, role_message = (
        await give_paid_joiner_role(
            guild,
            target
        )
    )


    if not success:

        await interaction.followup.send(
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "   🦅 **FALCON • SCAN COMPLETE**\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

            f"👤 **Account:** `{target.name}`\n"
            "🖼️ **Profile:** `VERIFIED` ✓\n"
            f"📆 **Account Age:** `{age_text}`\n"
            "🛡️ **Eligibility:** `CLEARED` ✓\n\n"

            "⚠️ **ROLE ASSIGNMENT FAILED**\n\n"

            f"{role_message}",
            ephemeral=True
        )

        return


    # =========================
    # SUCCESS
    # =========================

    embed = discord.Embed(

        title="🦅 FALCON • VERIFICATION COMPLETE",

        description=(
            f"**Welcome to the vault, "
            f"{target.mention}!** 🏴‍☠️\n\n"

            "Your account has successfully "
            "passed the eligibility scan."
        ),

        color=discord.Color.green()
    )


    embed.add_field(
        name="👤 Account",
        value=f"`{target.name}`",
        inline=True
    )


    embed.add_field(
        name="🖼️ Profile",
        value="`VERIFIED` ✓",
        inline=True
    )


    embed.add_field(
        name="📆 Account Age",
        value=f"`{age_text}`",
        inline=True
    )


    embed.add_field(
        name="🛡️ Eligibility",
        value="`CLEARED` ✓",
        inline=True
    )


    embed.add_field(
        name="🎟️ Access",
        value=f"`{ROLE_NAME}` ✓",
        inline=True
    )


    embed.add_field(
        name="🔐 Status",
        value="`APPROVED`",
        inline=True
    )


    embed.set_footer(
        text="🏴‍☠️ Bounty_Vault • Security Division"
    )


    await interaction.followup.send(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# VERIFY BUTTON
# ============================================================

class VerifyView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    @discord.ui.button(
        label="Verify Eligibility",
        style=discord.ButtonStyle.green,
        emoji="🔎",
        custom_id="bounty_vault_verify"
    )

    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # Acknowledge button
        await interaction.response.defer(
            ephemeral=True
        )

        try:

            await run_verification(
                interaction
            )

        except Exception as error:

            print(
                f"❌ Verification error: "
                f"{repr(error)}"
            )

            try:

                await interaction.followup.send(
                    "❌ **Verification Error**\n\n"
                    "Something went wrong while "
                    "processing your verification.\n\n"
                    "Please try again.",
                    ephemeral=True
                )

            except discord.HTTPException:

                pass


# ============================================================
# /VERIFY
# ============================================================

@bot.tree.command(
    name="verify",
    description="Check your Bounty_Vault eligibility."
)

async def verify(
    interaction: discord.Interaction
):

    embed = discord.Embed(

        title="🏴‍☠️ Bounty_Vault • Eligibility",

        description=(
            "### 🦅 Falcon Intelligence System\n\n"

            "Press **Verify Eligibility** below "
            "to begin your automated account scan.\n\n"

            "🔎 **Security Checks**\n"
            "・🖼️ Profile verification\n"
            "・📆 Account age analysis\n"
            "・🛡️ Eligibility assessment\n"
            "・🎟️ Paid Joiner access\n\n"

            "⚡ **Automatic verification**\n"
            "Fast. Simple. Secure."
        ),

        color=discord.Color.gold()
    )


    embed.set_footer(
        text="Bounty_Vault • Security Division"
    )


    await interaction.response.send_message(
        embed=embed,
        view=VerifyView()
    )


# ============================================================
# OLD -CHECKELIGIBLE COMMAND
# ============================================================

@bot.command(
    name="checkeligible"
)

@commands.guild_only()

async def check_eligible(
    ctx,
    member: discord.Member = None
):

    target = member or ctx.author


    # =========================
    # PROFILE PICTURE
    # =========================

    if target.avatar is None:

        await ctx.send(
            f"❌ {target.mention} does not have "
            "a profile picture set."
        )

        return


    await ctx.send(
        f"🔎 Checking `{target.name}`..."
    )


    # =========================
    # CALCULATE AGE
    # =========================

    age_text, total_months = (
        calculate_account_age(target)
    )


    # =========================
    # TOO YOUNG
    # =========================

    if total_months < MIN_ACCOUNT_MONTHS:

        await ctx.send(
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "   🦅 **FALCON • SCAN COMPLETE**\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

            f"👤 **Account:** `{target.name}`\n"
            f"📆 **Account Age:** `{age_text}`\n"
            "🛡️ **Eligibility:** `DENIED` ✕\n\n"

            f"🚫 Account must be at least "
            f"**{MIN_ACCOUNT_MONTHS} months old**."
        )

        return


    # =========================
    # GIVE ROLE
    # =========================

    success, role_message = (
        await give_paid_joiner_role(
            ctx.guild,
            target
        )
    )


    if not success:

        await ctx.send(
            role_message
        )

        return


    # =========================
    # SUCCESS
    # =========================

    await ctx.send(
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "   🦅 **FALCON • VERIFIED**\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        f"👤 **Account:** `{target.name}`\n"
        "🖼️ **Profile:** `VERIFIED` ✓\n"
        f"📆 **Account Age:** `{age_text}`\n"
        "🛡️ **Eligibility:** `CLEARED` ✓\n"
        f"🎟️ **Access:** `{ROLE_NAME}` ✓\n\n"

        "🏴‍☠️ **ACCESS GRANTED**"
    )


# ============================================================
# ERROR HANDLER
# ============================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandNotFound
    ):

        return


    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You don't have permission "
            "to use this command."
        )

        return


    print(
        f"❌ Command error: {repr(error)}"
    )


    await ctx.send(
        f"❌ An error occurred:\n"
        f"`{type(error).__name__}`"
    )


# ============================================================
# SYNC SLASH COMMANDS + PERSISTENT BUTTON
# ============================================================

@bot.event
async def setup_hook():

    # Keep button working after restart
    bot.add_view(
        VerifyView()
    )


    # Sync slash commands
    synced = await bot.tree.sync()


    print(
        f"🔄 Synced {len(synced)} slash command(s)"
    )


# ============================================================
# START BOT
# ============================================================

bot.run(TOKEN)
