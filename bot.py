"""
Bot de Discord para roleplay de ER:LC (Emergency Response: Liberty County)
Hecho con discord.py

Antes de correrlo:
1. Instala las dependencias:  pip install -r requirements.txt
2. Crea un archivo .env (copia .env.example) y pon tu TOKEN ahí.
3. Corre el bot:  python bot.py
"""

import os
import json
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ERLC_API_KEY = os.getenv("ERLC_API_KEY")  # opcional, para el comando /status

# ---------------------------------------------------------
# Configuración de bienvenida (se guarda en config.json para
# que sobreviva a reinicios del bot sin tener que tocar código)
# ---------------------------------------------------------
CONFIG_FILE = "config.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


config = load_config()

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
        guild_config = config.get(str(interaction.guild.id), {})
        canal_id = guild_config.get("canal_solicitudes")
        canal = interaction.guild.get_channel(canal_id) if canal_id else None

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


@bot.tree.command(name="canal-solicitudes", description="Configura a qué canal llegan las solicitudes de staff/whitelist")
@app_commands.describe(canal="Canal donde llegarán las solicitudes")
@app_commands.checks.has_permissions(manage_guild=True)
async def canal_solicitudes(interaction: discord.Interaction, canal: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    config.setdefault(guild_id, {})["canal_solicitudes"] = canal.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ Canal de solicitudes configurado en {canal.mention}", ephemeral=True
    )


# ===========================================================
#              BIENVENIDA A NUEVOS MIEMBROS
# ===========================================================
# Usa {miembro} para mencionar al nuevo usuario y {servidor} para el nombre del servidor.
MENSAJE_POR_DEFECTO = "¡Bienvenido/a {miembro} a **{servidor}**! 🚓 Lee las reglas y disfruta tu estadía."


@bot.event
async def on_member_join(member: discord.Member):
    guild_config = config.get(str(member.guild.id), {})
    canal_id = guild_config.get("canal_bienvenida")
    if not canal_id:
        return  # no se ha configurado ningún canal en este servidor

    canal = member.guild.get_channel(canal_id)
    if not canal:
        return

    mensaje = guild_config.get("mensaje_bienvenida", MENSAJE_POR_DEFECTO)
    texto = mensaje.format(miembro=member.mention, servidor=member.guild.name)

    embed = discord.Embed(description=texto, color=discord.Color.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Ahora somos {member.guild.member_count} miembros")

    await canal.send(embed=embed)


@bot.tree.command(name="canal-bienvenida", description="Configura el canal donde se enviará el mensaje de bienvenida")
@app_commands.describe(canal="Canal donde se enviarán los mensajes de bienvenida")
@app_commands.checks.has_permissions(manage_guild=True)
async def canal_bienvenida(interaction: discord.Interaction, canal: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    config.setdefault(guild_id, {})["canal_bienvenida"] = canal.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ Canal de bienvenida configurado en {canal.mention}", ephemeral=True
    )


@bot.tree.command(name="mensaje-bienvenida", description="Personaliza el texto del mensaje de bienvenida")
@app_commands.describe(mensaje="Usa {miembro} para mencionar al usuario y {servidor} para el nombre del servidor")
@app_commands.checks.has_permissions(manage_guild=True)
async def mensaje_bienvenida(interaction: discord.Interaction, mensaje: str):
    guild_id = str(interaction.guild.id)
    config.setdefault(guild_id, {})["mensaje_bienvenida"] = mensaje
    save_config(config)
    await interaction.response.send_message("✅ Mensaje de bienvenida actualizado.", ephemeral=True)


@bot.tree.command(name="probar-bienvenida", description="Muestra una vista previa del mensaje de bienvenida")
@app_commands.checks.has_permissions(manage_guild=True)
async def probar_bienvenida(interaction: discord.Interaction):
    guild_config = config.get(str(interaction.guild.id), {})
    mensaje = guild_config.get("mensaje_bienvenida", MENSAJE_POR_DEFECTO)
    texto = mensaje.format(miembro=interaction.user.mention, servidor=interaction.guild.name)

    embed = discord.Embed(description=texto, color=discord.Color.blue())
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text=f"Ahora somos {interaction.guild.member_count} miembros")

    await interaction.response.send_message(embed=embed)


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
