#!/usr/bin/env python3
"""
TELEGRAM UNIVERSAL PROFILE RESOLVER -  EDITION 💀
Uses MTProto (Telethon) - Can access MORE info than normal bots!
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputUser
from flask import Flask, request
import logging

# ========== CONFIG ==========
api_id = int(os.environ.get('API_ID', 0))  # my.telegram.org se lo
api_hash = os.environ.get('API_HASH', '')
bot_token = os.environ.get('BOT_TOKEN', '')
PORT = int(os.environ.get('PORT', 8080))

# ========== SETUP ==========
app = Flask(__name__)
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)
logging.basicConfig(level=logging.INFO)

async def resolve_user(identifier):
    """
    Kisi bhi identifier se user info lao:
    - Username (with/without @)
    - User ID (number)
    - Phone number (if available)
    """
    try:
        # Pehle username ki tarah try karo
        if isinstance(identifier, str) and not identifier.isdigit():
            if identifier.startswith('@'):
                identifier = identifier[1:]
            entity = await client.get_entity(identifier)
        else:
            # ID hai toh direct resolve
            user_id = int(identifier)
            entity = await client.get_entity(user_id)
        
        # Full profile fetch karo
        full = await client(GetFullUserRequest(entity.id))
        
        return {
            'success': True,
            'user_id': entity.id,
            'username': entity.username,
            'first_name': entity.first_name,
            'last_name': entity.last_name,
            'phone': entity.phone,  # ✅ Phone number (agar visible ho)
            'is_bot': entity.bot,
            'is_verified': entity.verified,
            'is_premium': entity.premium,
            'bio': full.full_user.about,
            'profile_link': f"tg://user?id={entity.id}",
            'public_link': f"https://t.me/{entity.username}" if entity.username else None,
            'privacy_status': 'Public' if entity.username else 'Private'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ========== TELEGRAM BOT COMMANDS ==========
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

app_bot = Application.builder().token(bot_token).build()

@app.route(f'/{bot_token}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), app_bot.bot)
    app_bot.process_update(update)
    return 'OK', 200

async def resolve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Universal resolver - username ya ID dono kaam karega"""
    if not context.args:
        await update.message.reply_text(
            "❌ *Usage:*\n"
            "`/resolve <username_or_id>`\n\n"
            "Examples:\n"
            "• `/resolve @username`\n"
            "• `/resolve 123456789`",
            parse_mode='Markdown'
        )
        return
    
    identifier = context.args[0]
    msg = await update.message.reply_text("🔍 Searching...")
    
    result = await resolve_user(identifier)
    
    if not result['success']:
        await msg.edit_text(f"❌ Error: {result['error']}")
        return
    
    # Format response
    response = f"""
╔════════════════════════════════╗
║  PROFILE RESOLVED - EDITION 🔥
╚════════════════════════════════╝

👤 **Name:** {result['first_name']} {result.get('last_name', '')}
🆔 **User ID:** `{result['user_id']}`
📛 **Username:** @{result['username'] if result['username'] else 'None'}
📱 **Phone:** {result['phone'] if result.get('phone') else 'Hidden'}
✅ **Verified:** {'Yes' if result['is_verified'] else 'No'}
⭐ **Premium:** {'Yes' if result['is_premium'] else 'No'}
🤖 **Is Bot:** {'Yes' if result['is_bot'] else 'No'}
📝 **Bio:** {result.get('bio', 'No bio')[:200]}

🔗 **Profile Links:**
• `tg://user?id={result['user_id']}` (Universal)
{f'• https://t.me/{result["username"]}' if result['username'] else ''}
"""
    
    # Add buttons
    keyboard = []
    if result['username']:
        keyboard.append([InlineKeyboardButton("🌐 Public Profile", url=f"https://t.me/{result['username']}")])
    keyboard.append([InlineKeyboardButton("📱 Open in App", url=f"tg://user?id={result['user_id']}")])
    
    await msg.edit_text(
        response,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

app_bot.add_handler(CommandHandler("resolve", resolve_cmd))

@app.route('/')
def home():
    return "🔥  Universal Telegram Resolver is LIVE!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
