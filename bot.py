"""
Bot de Discord para roleplay de ER:LC (Emergency Response: Liberty County)
Hecho con discord.py

Antes de correrlo:
1. Instala las dependencias:  pip install -r requirements.txt
2. Crea un archivo .env (copia .env.example) y pon tu TOKEN ahí.
3. Corre el bot:  python bot.py
"""

import os
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ERLC_API_KEY = os.getenv("ERLC_API_KEY")  # opcional, para el comando /status

# ---------------------------------------------------------
# Configuración de intents (permisos que el bot necesita)
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Conectado como {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")


# ===========================================================
#                    COMANDOS DE MODERACIÓN
# ===========================================================

@bot.tree.command(name="kick", description="Expulsa a un miembro del servidor")
@app_commands.describe(miembro="Miembro a expulsar", razon="Razón de la expulsión")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, miembro: discord.Member, razon: str = "No especificada"):
    await miembro.kick(reason=razon)
    embed = discord.Embed(
        title="👢 Miembro expulsado",
        description=f"**{miembro}** fue expulsado.\n**Razón:** {razon}",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ban", description="Banea a un miembro del servidor")
@app_commands.describe(miembro="Miembro a banear", razon="Razón del baneo")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, miembro: discord.Member, razon: str = "No especificada"):
    await miembro.ban(reason=razon)
    embed = discord.Embed(
        title="🔨 Miembro baneado",
        description=f"**{miembro}** fue baneado.\n**Razón:** {razon}",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mute", description="Silencia a un miembro por X minutos")
@app_commands.describe(miembro="Miembro a silenciar", minutos="Duración en minutos")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, miembro: discord.Member, minutos: int):
    import datetime
    duracion = datetime.timedelta(minutes=minutos)
    await miembro.timeout(duracion)
    embed = discord.Embed(
        title="🔇 Miembro silenciado",
        description=f"**{miembro}** fue silenciado por **{minutos} minutos**.",
        color=discord.Color.dark_grey()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="clear", description="Borra una cantidad de mensajes del canal")
@app_commands.describe(cantidad="Número de mensajes a borrar (máx 100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, cantidad: app_commands.Range[int, 1, 100]):
    await interaction.response.defer(ephemeral=True)
    borrados = await interaction.channel.purge(limit=cantidad)
    await interaction.followup.send(f"🧹 Se borraron {len(borrados)} mensajes.", ephemeral=True)


# ===========================================================
#              SISTEMA DE SOLICITUDES (WHITELIST)
# ===========================================================

class SolicitudModal(discord.ui.Modal, title="Solicitud de Staff / Whitelist"):
    nombre_roblox = discord.ui.TextInput(label="Usuario de Roblox", placeholder="TuUsuario123")
    edad = discord.ui.TextInput(label="Edad", placeholder="Ej. 16")
    experiencia = discord.ui.TextInput(
        label="Experiencia previa en RP",
        style=discord.TextStyle.paragraph,
        placeholder="Cuéntanos tu experiencia en roleplay o staff..."
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Cambia este ID por el ID del canal donde quieres que lleguen las solicitudes
        canal_revision_id = int(os.getenv("CANAL_SOLICITUDES_ID", "0"))
        canal = interaction.guild.get_channel(canal_revision_id)

        embed = discord.Embed(title="📋 Nueva solicitud", color=discord.Color.blue())
        embed.add_field(name="Discord", value=interaction.user.mention, inline=False)
        embed.add_field(name="Usuario de Roblox", value=self.nombre_roblox.value, inline=True)
        embed.add_field(name="Edad", value=self.edad.value, inline=True)
        embed.add_field(name="Experiencia", value=self.experiencia.value, inline=False)

        if canal:
            await canal.send(embed=embed)

        await interaction.response.send_message(
            "✅ ¡Tu solicitud fue enviada! El staff la revisará pronto.", ephemeral=True
        )


@bot.tree.command(name="solicitar", description="Envía una solicitud para staff o whitelist")
async def solicitar(interaction: discord.Interaction):
    await interaction.response.send_modal(SolicitudModal())


# ===========================================================
#           ESTADO DEL SERVIDOR ER:LC (API oficial)
# ===========================================================

@bot.tree.command(name="status", description="Muestra el estado actual del servidor de ER:LC")
async def status(interaction: discord.Interaction):
    if not ERLC_API_KEY:
        await interaction.response.send_message(
            "⚠️ No hay una API key de ER:LC configurada. Consigue una con `:api` dentro de tu servidor privado y ponla en el archivo .env",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    headers = {"server-key": ERLC_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.policeroleplay.community/v1/server", headers=headers) as resp:
            if resp.status != 200:
                await interaction.followup.send("❌ No se pudo obtener el estado del servidor. Revisa la API key.")
                return
            data = await resp.json()

    embed = discord.Embed(title=f"🚓 {data.get('Name', 'Servidor ER:LC')}", color=discord.Color.green())
    embed.add_field(name="Jugadores", value=f"{data.get('CurrentPlayers', '?')}/{data.get('MaxPlayers', '?')}")
    embed.add_field(name="Código de unión", value=data.get("JoinKey", "N/A"))
    embed.add_field(name="En cola", value=str(data.get("QueueCount", 0)))
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="ping", description="Revisa si el bot está vivo")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Latencia: {round(bot.latency * 1000)}ms")


bot.run(TOKEN)
