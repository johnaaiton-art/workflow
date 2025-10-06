# B2+ Collocations Telegram Bot

This bot receives CEFR B2+ collocations from an N8N workflow and allows students to select vocabulary for study.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the bot:
```bash
python collocation_bot.py
```

## How it works

1. N8N workflow processes video text and extracts collocations using DeepSeek API
2. Collocations are saved to `collocations.json` in this repository
3. Bot loads collocations and presents them to students for selection
4. Student selections are saved to individual files and JSON data files

## File Structure

- `collocation_bot.py` - Main bot code
- `requirements.txt` - Python dependencies
- `collocations.json` - Collocations data from N8N (auto-generated)
- `cards/` - Directory for student selection files
- `selection_*.json` - Individual student selection data

## Configuration

The bot token is currently hardcoded. For production, use environment variables:

```python
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-bot-token-here')
```

## N8N Integration

The bot expects collocations in this JSON format:

```json
{
  "_metadata": {
    "topic": "Video Topic Name",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "category_1": {
    "name": "📚 Category Name",
    "expressions": [
      "expression 1 - translation",
      "expression 2 - translation"
    ]
  }
}
```


live

Jump to live
Task progress
