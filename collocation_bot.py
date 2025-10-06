import os
import json
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load bot token from environment variable (set in Railway, NOT in code)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is not set! Please configure it in Railway.")

# Global variable to store collocations received from N8N
VIDEO_COLLOCATIONS = {}

def load_collocations_from_file():
    """Load collocations from JSON file created by N8N workflow"""
    global VIDEO_COLLOCATIONS
    try:
        if os.path.exists('collocations.json'):
            with open('collocations.json', 'r', encoding='utf-8') as f:
                VIDEO_COLLOCATIONS = json.load(f)
                logging.info(f"Loaded {len(VIDEO_COLLOCATIONS)} collocation categories")
        else:
            logging.warning("collocations.json not found, using empty collocations")
            VIDEO_COLLOCATIONS = {}
    except Exception as e:
        logging.error(f"Error loading collocations: {e}")
        VIDEO_COLLOCATIONS = {}

def load_collocations_from_url(url):
    """Load collocations from URL provided by N8N workflow"""
    global VIDEO_COLLOCATIONS
    try:
        response = requests.get(url)
        response.raise_for_status()
        VIDEO_COLLOCATIONS = response.json()
        logging.info(f"Loaded {len(VIDEO_COLLOCATIONS)} collocation categories from URL")
    except Exception as e:
        logging.error(f"Error loading collocations from URL: {e}")
        VIDEO_COLLOCATIONS = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Load collocations when bot starts
    load_collocations_from_file()
    
    user_name = update.effective_user.first_name

    if 'selected_expressions' not in context.user_data:
        context.user_data['selected_expressions'] = []

    # Check if collocations are available
    if not VIDEO_COLLOCATIONS:
        await update.message.reply_text(
            "⏳ Collocations are being prepared. Please wait a moment and try again."
        )
        return

    keyboard = []
    for category_id, category_data in VIDEO_COLLOCATIONS.items():
        keyboard.append([InlineKeyboardButton(
            category_data["name"],
            callback_data=f"cat_{category_id}"
        )])

    keyboard.append([
        InlineKeyboardButton("💾 Save & Download", callback_data="save_file"),
        InlineKeyboardButton("🗑️ Clear All", callback_data="clear_selection")
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    selected_count = len(context.user_data['selected_expressions'])

    # Get topic from collocations data or use default
    topic = VIDEO_COLLOCATIONS.get('_metadata', {}).get('topic', 'Video Content')

    welcome_message = f"""
👋 Hello {user_name}!

**B2+ Video Collocations Selector**
🎯 Topic: {topic}

📊 **Selected so far:** {selected_count} expressions

**How to use:**
1. Choose a category below
2. Click any expression to add it
3. Click "Save & Download" when done

Select a category:
"""

    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(welcome_message, reply_markup=reply_markup)

async def show_category_vocabulary(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str):
    query = update.callback_query

    if category_id not in VIDEO_COLLOCATIONS:
        await query.edit_message_text("❌ Category not found!")
        return

    category_data = VIDEO_COLLOCATIONS[category_id]
    keyboard = []
    for i, expression in enumerate(category_data['expressions']):
        display_text = expression[:40] + "..." if len(expression) > 40 else expression
        keyboard.append([InlineKeyboardButton(
            display_text,
            callback_data=f"add_{category_id}_{i}"
        )])

    keyboard.append([
        InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_start"),
        InlineKeyboardButton("💾 Save & Download", callback_data="save_file")
    ])

    message = f"""
📚 **{category_data['name']}**

Click any expression to add it to your collection.
"""

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup)

async def add_expression(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str, expression_index: int):
    query = update.callback_query
    await query.answer("✅ Added!", show_alert=False)

    if category_id not in VIDEO_COLLOCATIONS:
        return

    category_data = VIDEO_COLLOCATIONS[category_id]

    if expression_index >= len(category_data['expressions']):
        return

    expression = category_data['expressions'][expression_index]
    selected_expressions = context.user_data.get('selected_expressions', [])

    if expression not in selected_expressions:
        selected_expressions.append(expression)
        context.user_data['selected_expressions'] = selected_expressions

    await show_category_vocabulary(update, context, category_id)

async def save_selected_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_expressions = context.user_data.get('selected_expressions', [])
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id

    if not selected_expressions:
        await query.answer("❌ No expressions selected yet!", show_alert=True)
        return

    try:
        os.makedirs("cards", exist_ok=True)
        
        # Get topic from metadata
        topic = VIDEO_COLLOCATIONS.get('_metadata', {}).get('topic', 'Video Content')
        
        filename = f"{topic.lower().replace(' ', '_')}_collocations_{user_name}_{user_id}.txt"
        filepath = os.path.join("cards", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"My B2+ {topic} Collocations - {user_name}\n")
            f.write(f"Total selected: {len(selected_expressions)} expressions\n")
            f.write("=" * 50 + "\n\n")
            for i, expression in enumerate(selected_expressions, 1):
                f.write(f"{i}. {expression}\n")
            f.write("\n" + "=" * 50 + "\n")
            f.write("💡 Study these before watching the video!\n")

        # Save selection data for N8N workflow to access
        selection_data = {
            "user_name": user_name,
            "user_id": user_id,
            "topic": topic,
            "selected_expressions": selected_expressions,
            "filename": filename,
            "timestamp": str(context.user_data.get('timestamp', ''))
        }
        
        with open(f"selection_{user_name}_{user_id}.json", "w", encoding="utf-8") as f:
            json.dump(selection_data, f, ensure_ascii=False, indent=2)

        keyboard = [
            [InlineKeyboardButton("📚 Select More", callback_data="back_to_start")],
            [InlineKeyboardButton("🗑️ Start Over", callback_data="clear_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        success_message = f"""
✅ **File Saved Successfully!**

📁 **Filename:** {filename}
📊 **Expressions saved:** {len(selected_expressions)}
"""

        await query.edit_message_text(success_message, reply_markup=reply_markup)

        logging.info(f"Saved {len(selected_expressions)} expressions for user {user_name}")

    except Exception as e:
        logging.error(f"Error saving file: {e}")
        await query.edit_message_text("❌ Error saving file. Please try again.")

async def clear_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🗑️ Selection cleared!", show_alert=True)

    context.user_data['selected_expressions'] = []
    await start(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    logging.info(f"Callback data: {data}")

    if data.startswith("cat_"):
        category_id = data.replace("cat_", "")
        await show_category_vocabulary(update, context, category_id)

    elif data.startswith("add_"):
        try:
            parts = data.split("_")
            category_id = "_".join(parts[1:-1])
            expression_index = int(parts[-1])
            await add_expression(update, context, category_id, expression_index)
        except Exception as e:
            logging.error(f"Add expression error: {e}")
            await query.answer("❌ Error adding expression", show_alert=True)

    elif data == "save_file":
        await save_selected_file(update, context)

    elif data == "clear_selection":
        await clear_selection(update, context)

    elif data == "back_to_start":
        await start(update, context)

    else:
        await query.answer("❌ Unknown action", show_alert=True)

# Optional: Webhook handler for N8N (if you later use webhooks instead of file polling)
async def webhook_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle webhook calls from N8N with collocation data"""
    try:
        load_collocations_from_file()
        logging.info("Collocations reloaded via webhook trigger")
    except Exception as e:
        logging.error(f"Webhook handler error: {e}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))

    os.makedirs("cards", exist_ok=True)

    logging.info("🤖 B2+ Collocations Bot starting...")
    logging.info("Waiting for collocations data from N8N workflow...")
    application.run_polling()

if __name__ == "__main__":
    main()
