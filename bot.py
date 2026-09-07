import os
import asyncio
import re

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

# Falcon bot name
FALCON_NAME = "falcon"


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

    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print("🏴‍☠️ Bounty_Vault is ONLINE!")


# =========================
# PING
# =========================

@bot.command(name="ping")
async def ping(ctx):

    await ctx.send(
        "🏴‍☠️ **Bounty_Vault is ONLINE!** 🟢"
    )


# ============================================================
# ACCOUNT AGE CHECK
# ============================================================

async def check_account_age(ctx, target):

    # Ask Falcon
    await ctx.send(
        f"-accage {target.mention}"
    )

    print(
        f"📡 Requested Falcon account age for {target}"
    )

    # Wait for Falcon
    await asyncio.sleep(6)

    falcon_description = None

    # Search recent messages
    async for msg in ctx.channel.history(
        limit=20
    ):

        # Must be a bot
        if not msg.author.bot:
            continue

        # Must be Falcon
        if FALCON_NAME not in msg.author.name.lower():
            continue

        # Must contain an embed
        if not msg.embeds:
            continue

        embed = msg.embeds[0]

        # Need title
        if not embed.title:
            continue

        # Need Account Age in title
        if "account age" not in embed.title.lower():
            continue

        target_name = target.name.lower()

        title_text = embed.title.lower()

        footer_text = ""

        if embed.footer:
            footer_text = (
                embed.footer.text.lower()
            )

        # Make sure this is the target's result
        if (
            target_name not in title_text
            and target_name not in footer_text
        ):
            continue

        falcon_description = (
            embed.description
        )

        break

    # Falcon didn't respond
    if not falcon_description:

        return None, None

    # =========================
    # PARSE AGE
    # =========================

    text = falcon_description.lower()

    years_match = re.search(
        r"(\d+)\s*year",
        text
    )

    months_match = re.search(
        r"(\d+)\s*month",
        text
    )

    days_match = re.search(
        r"(\d+)\s*day",
        text
    )

    years = (
        int(years_match.group(1))
        if years_match
        else 0
    )

    months = (
        int(months_match.group(1))
        if months_match
        else 0
    )

    days = (
        int(days_match.group(1))
        if days_match
        else 0
    )

    total_months = (
        years * 12
        + months
    )

    return (
        falcon_description,
        total_months
    )


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
            "❌ Verification can only be used inside a server.",
            ephemeral=True
        )

        return

    # =========================
    # PROFILE PICTURE
    # =========================

    if target.avatar is None:

        await interaction.followup.send(
            "❌ **Verification Failed**\n\n"
            "🖼️ You need to have a profile picture "
            "set before you can pass verification.",
            ephemeral=True
        )

        return

    # Tell user we're checking
    await interaction.followup.send(
        "🔍 **Verification started!**\n\n"
        "🖼️ Profile picture: ✅\n"
        "📅 Checking account age with Falcon...\n\n"
        "⏳ Please wait...",
        ephemeral=True
    )

    # =========================
    # ACCOUNT AGE
    # =========================

    description, total_months = (
        await check_account_age(
            # We need a channel for Falcon
            interaction.channel,
            target
        )
    )

    # Falcon failed
    if description is None:

        await interaction.followup.send(
            "❌ **Verification Failed**\n\n"
            "I couldn't read Falcon's account-age response.\n\n"
            "Please try again in a few seconds.",
            ephemeral=True
        )

        return

    # =========================
    # ACCOUNT TOO YOUNG
    # =========================

    if total_months < MIN_ACCOUNT_MONTHS:

        await interaction.followup.send(
            "❌ **Not Eligible**\n\n"
            f"👤 User: {target.mention}\n"
            "🖼️ Profile Picture: ✅\n"
            f"📅 Account Age: **{description}**\n\n"
            f"🚫 Your account must be at least "
            f"**{MIN_ACCOUNT_MONTHS} months old**.",
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
            "⚠️ **Verification Passed, "
            "but I couldn't give the role.**\n\n"
            f"{role_message}",
            ephemeral=True
        )

        return

    # =========================
    # SUCCESS
    # =========================

    embed = discord.Embed(
        title="✅ Eligibility Verified!",
        description=(
            f"Congratulations {target.mention}! 🎉\n\n"
            "You passed all required checks."
        ),
        color=discord.Color.green()
    )

    embed.add_field(
        name="🖼️ Profile Picture",
        value="✅ Yes",
        inline=True
    )

    embed.add_field(
        name="📅 Account Age",
        value=description,
        inline=True
    )

    embed.add_field(
        name="🎟️ Role",
        value=f"**{ROLE_NAME}**",
        inline=True
    )

    embed.set_footer(
        text="🏴‍☠️ Bounty_Vault Verification"
    )

    await interaction.followup.send(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# VERIFY BUTTON
# ============================================================

class VerifyView(discord.ui.View):

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

        # Make the interaction acknowledged
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
                    "❌ Something went wrong "
                    "during verification.\n\n"
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
        title="🏴‍☠️ Bounty_Vault Verification",
        description=(
            "Click the button below to check "
            "your eligibility.\n\n"
            "🔎 **Checks:**\n"
            "• Profile picture\n"
            "• Account age\n"
            "• Eligibility status\n"
            "• Paid Joiner role\n\n"
            "✨ Verification is automatic."
        ),
        color=discord.Color.gold()
    )

    embed.set_footer(
        text="Bounty_Vault • Eligibility System"
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

    # Profile picture
    if target.avatar is None:

        await ctx.send(
            f"❌ {target.mention} does not have "
            "a profile picture set."
        )

        return

    await ctx.send(
        f"🔍 Checking {target.mention}..."
    )

    description, total_months = (
        await check_account_age(
            ctx,
            target
        )
    )

    if description is None:

        await ctx.send(
            "❌ Could not read Falcon's response. "
            "Please try again."
        )

        return

    if total_months < MIN_ACCOUNT_MONTHS:

        await ctx.send(
            f"❌ {target.mention}'s account is "
            f"under {MIN_ACCOUNT_MONTHS} months old.\n"
            f"Found: **{description}**"
        )

        return

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

    await ctx.send(
        f"✅ **Eligibility Verified!**\n\n"
        f"👤 User: {target.mention}\n"
        f"🖼️ Profile Picture: Yes\n"
        f"📅 Account Age: {description}\n"
        f"🎟️ {role_message}"
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