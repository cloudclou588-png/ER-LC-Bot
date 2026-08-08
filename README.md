# Bot de Discord para ER:LC RP

## 1. Instalación local (para probar)

1. Instala [Python 3.10+](https://www.python.org/downloads/) si no lo tienes.
2. Abre una terminal en esta carpeta y corre:
   ```
   pip install -r requirements.txt
   ```
3. Copia `.env.example` y renómbralo a `.env`. Pon ahí tu token del bot (el que copiaste del Developer Portal).
4. Corre el bot:
   ```
   python bot.py
   ```
5. Si todo salió bien, verás en la consola: `✅ Conectado como ...`

## 2. Comandos incluidos

- `/kick` `/ban` `/mute` `/clear` — moderación básica
- `/solicitar` — formulario para solicitudes de staff/whitelist
- `/status` — muestra jugadores conectados en tu servidor de ER:LC (necesita API key, ver abajo)
- `/ping` — prueba que el bot esté vivo
- `/canal-bienvenida` — configura en qué canal se saluda a los miembros nuevos
- `/mensaje-bienvenida` — personaliza el texto de bienvenida (usa `{miembro}` y `{servidor}`)
- `/probar-bienvenida` — muestra cómo se vería el mensaje sin esperar a que alguien entre
- `/canal-solicitudes` — configura a qué canal llegan las solicitudes enviadas con `/solicitar`

### Cómo activar la bienvenida
1. Usa `/canal-bienvenida` y selecciona el canal donde quieres que aparezca el saludo.
2. (Opcional) Usa `/mensaje-bienvenida` para cambiar el texto, ej:
   `¡Bienvenido {miembro} a {servidor}! Ve a #reglas antes de jugar.`
3. Cada vez que alguien nuevo entre al servidor, el bot lo saludará automáticamente.

> Nota: la configuración se guarda en un archivo `config.json` que el bot crea solo. En Railway esto persiste mientras no borres el proyecto, pero si vuelves a subir el código desde cero (redeploy completo) puede reiniciarse — en ese caso solo vuelve a correr `/canal-bienvenida`.

### Cómo conseguir la API key de ER:LC
Dentro de tu servidor privado de ER:LC, escribe el comando `:api` en el chat del juego (debes ser dueño o co-owner del servidor). Te dará una key — ponla en `ERLC_API_KEY` dentro del `.env`.

## 3. Cómo alojarlo GRATIS (para que esté prendido 24/7)

Tu PC apagada = bot apagado, así que necesitas un servidor gratuito. Recomendado:

### Opción A: Railway (más fácil)
1. Crea cuenta en [railway.app](https://railway.app) con GitHub.
2. Sube esta carpeta a un repositorio de GitHub (puede ser privado).
3. En Railway: "New Project" → "Deploy from GitHub repo" → selecciona tu repo.
4. En la pestaña "Variables" agrega `DISCORD_TOKEN`, `ERLC_API_KEY` y `CANAL_SOLICITUDES_ID` con tus valores.
5. Railway detecta que es Python y lo corre solo. Da algunas horas gratis al mes.

### Opción B: Render.com
Similar a Railway, tiene un plan gratuito para "Background Workers" (ideal para bots, no se duerme como los Web Services gratuitos).

### Opción C: Replit + UptimeRobot
Más manual, útil si Railway/Render no te dejan (piden tarjeta a veces). Requiere un pequeño servidor web extra para mantenerlo despierto con UptimeRobot.

## 4. Siguientes pasos sugeridos
- Agregar comandos específicos de tu servidor (turnos de staff, formularios de facción policía/EMS/fuego, etc.)
- Sistema de tickets para soporte
- Logs de moderación en un canal
