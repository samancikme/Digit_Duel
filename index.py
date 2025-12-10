"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 BULLS & COWS - PROFESSIONAL BOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Xususiyatlar:
✅ MongoDB integratsiyasi
✅ 4 ta til (uz, ru, en, kk)
✅ Bot bilan va do'st bilan o'ynash
✅ 4 ta qiyinlik darajasi
✅ Rating tizimi (ELO)
✅ Coin va Streak
✅ Hint tizimi
✅ Achievements (yutuqlar)
✅ Leaderboard
✅ Statistika
✅ Kunlik bonus

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import logging
import random
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from motor.motor_asyncio import AsyncIOMotorClient
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN", "7701613822:AAFEOPYnLokpQpF-mu73edLbH5e7PINiLMo")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@samancikschannel")

# MongoDB sozlamalari
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "bulls_cows_bot")

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class GameMode(str, Enum):
    VS_PLAYER = "vs_player"
    VS_BOT = "vs_bot"

class Difficulty(int, Enum):
    EASY = 3
    MEDIUM = 4
    HARD = 5
    EXTREME = 6

LANGUAGES = {
    "uz": "🇺🇿 O'zbek",
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "kk": "🇰🇿 Qaraqalpaq"
}

# Achievements
ACHIEVEMENTS = {
    "first_win": {"name_uz": "🏆 Birinchi g'alaba", "name_ru": "🏆 Первая победа", "name_en": "🏆 First Win", "coins": 100},
    "speed_3": {"name_uz": "⚡ Tezkor (3 ta)", "name_ru": "⚡ Скорость (3)", "name_en": "⚡ Speed (3)", "coins": 200},
    "streak_3": {"name_uz": "🔥 Seriya 3", "name_ru": "🔥 Серия 3", "name_en": "🔥 Streak 3", "coins": 150},
    "streak_5": {"name_uz": "🔥🔥 Seriya 5", "name_ru": "🔥🔥 Серия 5", "name_en": "🔥🔥 Streak 5", "coins": 300},
    "streak_10": {"name_uz": "🔥🔥🔥 Seriya 10", "name_ru": "🔥🔥🔥 Серия 10", "name_en": "🔥🔥🔥 Streak 10", "coins": 500},
    "bot_killer": {"name_uz": "🤖 Bot o'ldirgich", "name_ru": "🤖 Убийца ботов", "name_en": "🤖 Bot Killer", "coins": 100},
    "hard_mode": {"name_uz": "💪 Qiyin rejim", "name_ru": "💪 Сложный режим", "name_en": "💪 Hard Mode", "coins": 250},
    "games_100": {"name_uz": "🎮 100 o'yin", "name_ru": "🎮 100 игр", "name_en": "🎮 100 Games", "coins": 500},
    "master": {"name_uz": "👑 Ustoz", "name_ru": "👑 Мастер", "name_en": "👑 Master", "coins": 1000}
}

# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGES
# ═══════════════════════════════════════════════════════════════════════════════

MESSAGES = {
    "uz": {
        "choose_language": "🌍 Tilni tanlang:",
        "subscribe": "📢 Botdan foydalanish uchun kanalga a'zo bo'ling:",
        "not_subscribed": "❌ Siz hali kanalga a'zo emassiz!",
        "subscribed": "✅ Tabriklaymiz! Endi botdan foydalanishingiz mumkin.",
        "main_menu": """
🏠 <b>Asosiy Menyu</b>

👤 {name}
💰 Coins: <b>{coins}</b>
🏆 Rating: <b>{rating}</b>
🔥 Streak: <b>{streak}</b>
📊 O'yinlar: <b>{wins}/{games}</b> ({win_rate:.1f}%)
""",
        "choose_mode": """
🎮 <b>O'yin turini tanlang:</b>

🤖 <b>Bot bilan</b> - sun'iy intellekt bilan o'ynash
👥 <b>Do'st bilan</b> - havolani ulashing
""",
        "choose_difficulty": """
📊 <b>Qiyinlik darajasini tanlang:</b>

🟢 <b>Oson</b> - 3 xonali raqam
🟡 <b>O'rtacha</b> - 4 xonali raqam
🔴 <b>Qiyin</b> - 5 xonali raqam
⚫ <b>Ekstremal</b> - 6 xonali raqam
""",
        "game_created": """
✅ <b>O'yin yaratildi!</b>

🔗 Do'stingizga bu havolani yuboring:
{invite_link}

⏳ Raqib kutilmoqda...
""",
        "game_started": """
🎮 <b>O'yin boshlandi!</b>

👤 Raqib: <b>{opponent}</b>
📊 Qiyinlik: <b>{difficulty}</b> xonali

🔢 Maxfiy raqamingizni kiriting:
(Raqamlar takrorlanmasin!)
""",
        "secret_set": "✅ Maxfiy raqamingiz saqlandi! Raqibingizni kuting...",
        "both_ready": "✅ Ikkala o'yinchi ham tayyor! O'yin boshlandi!",
        "your_turn": """
🎯 <b>Sizning navbatingiz!</b>

💡 Hintlar: {hints} ta qoldi
🔄 Urinishlar: {attempts}

Taxminingizni yuboring:
""",
        "opponent_turn": "⏳ Raqibingizning navbati. Kuting...",
        "result": """
📊 <b>Natija:</b> <code>{guess}</code>

🎯 {bulls} Bull | 🐄 {cows} Cow
🔄 Urinish: {attempts}
""",
        "win": """
🎉🎉🎉 <b>TABRIKLAYMIZ!</b> 🎉🎉🎉

Siz <b>{attempts}</b> urinishda g'olib bo'ldingiz!
🎯 Raqibning maxfiy raqami: <code>{secret}</code>

💰 +{coins} coins
🏆 +{rating} rating
{streak_msg}
{achievements}
""",
        "lose": """
😔 <b>Afsuski, yutqazdingiz!</b>

🎯 Raqibning maxfiy raqami: <code>{secret}</code>
🏆 -{rating} rating
""",
        "hint_used": """
💡 <b>Maslahat:</b>

Pozitsiya <b>{position}</b>: raqam <b>{digit}</b>

💰 -{cost} coins
💡 Qolgan: {remaining} ta
""",
        "not_enough_coins": "❌ Sizda yetarli coin yo'q! Kerak: {cost}",
        "invalid_number": "❌ Noto'g'ri format! {length} xonali raqam kiriting (takrorlanmasin).",
        "not_your_turn": "❌ Sizning navbatingiz emas!",
        "surrender_confirm": "🏳️ Haqiqatan ham taslim bo'lmoqchimisiz?",
        "surrendered": "🏳️ Siz taslim bo'ldingiz.",
        "opponent_surrendered": "🎉 Raqibingiz taslim bo'ldi! Siz g'olib bo'ldingiz!",
        "leaderboard": """
🏆 <b>TOP O'YINCHILAR</b>

{players}

Sizning o'rningiz: <b>#{rank}</b>
""",
        "profile": """
👤 <b>Profil: {name}</b>

🆔 ID: <code>{user_id}</code>
🏆 Rating: {rating} (#{rank})
💰 Coins: {coins}
🔥 Streak: {streak} (Eng yaxshi: {best_streak})

📊 <b>Statistika:</b>
🎮 O'yinlar: {games}
🏆 G'alabalar: {wins}
📈 G'alaba foizi: {win_rate:.1f}%
📊 O'rtacha urinish: {avg_attempts:.1f}

🏅 Yutuqlar: {achievement_count}/{total_achievements}
""",
        "stats": """
📊 <b>Batafsil statistika</b>

🎮 Jami o'yinlar: {games}
🏆 G'alabalar: {wins}
😔 Mag'lubiyatlar: {losses}
📈 G'alaba foizi: {win_rate:.1f}%

🔥 Hozirgi streak: {current_streak}
🏆 Eng yaxshi streak: {best_streak}

📊 O'rtacha urinish: {avg_attempts:.1f}
💡 Ishlatilgan hintlar: {hints_used}

🤖 Bot bilan: {vs_bot_games}
👥 Do'st bilan: {vs_player_games}
""",
        "daily_bonus": """
🎁 <b>Kunlik bonus!</b>

Siz <b>{coins}</b> coin oldingiz!
🔥 Kunlik streak: {streak} kun

Ertaga yana qaytib keling! 🎉
""",
        "daily_already": "❌ Siz bugun bonusni oldingiz!\n\nKeyingi bonus: {next_time}",
        "achievement_unlocked": """
🏅 <b>YANGI YUTUQ!</b>

{name}

💰 +{coins} coins
""",
        "game_not_found": "❌ O'yin topilmadi!",
        "already_in_game": "❌ Siz allaqachon o'yindasiz!",
        "cannot_play_self": "❌ O'zingiz bilan o'ynay olmaysiz!",
        "game_already_started": "❌ Bu o'yin allaqachon boshlangan!",
        
        # Buttons
        "btn_new_game": "🎮 Yangi o'yin",
        "btn_vs_bot": "🤖 Bot bilan",
        "btn_vs_player": "👥 Do'st bilan",
        "btn_leaderboard": "🏆 Reytinglar",
        "btn_profile": "👤 Profil",
        "btn_stats": "📊 Statistika",
        "btn_daily": "🎁 Kunlik bonus",
        "btn_settings": "⚙️ Sozlamalar",
        "btn_hint": "💡 Hint ({cost} coin)",
        "btn_surrender": "🏳️ Taslim",
        "btn_back": "🔙 Orqaga",
        "btn_yes": "✅ Ha",
        "btn_no": "❌ Yo'q",
        "btn_subscribe": "📢 Kanalga o'tish",
        "btn_check": "✅ Tekshirish",
        "btn_easy": "🟢 Oson (3)",
        "btn_medium": "🟡 O'rtacha (4)",
        "btn_hard": "🔴 Qiyin (5)",
        "btn_extreme": "⚫ Ekstremal (6)",
    },
    "ru": {
        "choose_language": "🌍 Выберите язык:",
        "subscribe": "📢 Подпишитесь на канал для использования бота:",
        "not_subscribed": "❌ Вы еще не подписаны на канал!",
        "subscribed": "✅ Поздравляем! Теперь вы можете пользоваться ботом.",
        "main_menu": """
🏠 <b>Главное меню</b>

👤 {name}
💰 Монеты: <b>{coins}</b>
🏆 Рейтинг: <b>{rating}</b>
🔥 Серия: <b>{streak}</b>
📊 Игры: <b>{wins}/{games}</b> ({win_rate:.1f}%)
""",
        "choose_mode": """
🎮 <b>Выберите режим игры:</b>

🤖 <b>Против бота</b> - играть с ИИ
👥 <b>С другом</b> - отправьте ссылку
""",
        "choose_difficulty": """
📊 <b>Выберите сложность:</b>

🟢 <b>Легко</b> - 3-значное число
🟡 <b>Средне</b> - 4-значное число
🔴 <b>Сложно</b> - 5-значное число
⚫ <b>Экстрим</b> - 6-значное число
""",
        "game_created": """
✅ <b>Игра создана!</b>

🔗 Отправьте другу эту ссылку:
{invite_link}

⏳ Ожидание противника...
""",
        "game_started": """
🎮 <b>Игра началась!</b>

👤 Противник: <b>{opponent}</b>
📊 Сложность: <b>{difficulty}</b>-значное

🔢 Введите ваше секретное число:
(Цифры не должны повторяться!)
""",
        "secret_set": "✅ Ваше секретное число сохранено! Ожидайте противника...",
        "both_ready": "✅ Оба игрока готовы! Игра началась!",
        "your_turn": """
🎯 <b>Ваш ход!</b>

💡 Подсказок: {hints}
🔄 Попыток: {attempts}

Введите вашу догадку:
""",
        "opponent_turn": "⏳ Ход противника. Ожидайте...",
        "result": """
📊 <b>Результат:</b> <code>{guess}</code>

🎯 {bulls} Bull | 🐄 {cows} Cow
🔄 Попытка: {attempts}
""",
        "win": """
🎉🎉🎉 <b>ПОЗДРАВЛЯЕМ!</b> 🎉🎉🎉

Вы выиграли за <b>{attempts}</b> попыток!
🎯 Секрет противника: <code>{secret}</code>

💰 +{coins} монет
🏆 +{rating} рейтинга
{streak_msg}
{achievements}
""",
        "lose": """
😔 <b>К сожалению, вы проиграли!</b>

🎯 Секрет противника: <code>{secret}</code>
🏆 -{rating} рейтинга
""",
        "hint_used": """
💡 <b>Подсказка:</b>

Позиция <b>{position}</b>: цифра <b>{digit}</b>

💰 -{cost} монет
💡 Осталось: {remaining}
""",
        "not_enough_coins": "❌ Недостаточно монет! Нужно: {cost}",
        "invalid_number": "❌ Неверный формат! Введите {length}-значное число без повторов.",
        "not_your_turn": "❌ Сейчас не ваш ход!",
        "surrender_confirm": "🏳️ Вы уверены, что хотите сдаться?",
        "surrendered": "🏳️ Вы сдались.",
        "opponent_surrendered": "🎉 Противник сдался! Вы победили!",
        "leaderboard": """
🏆 <b>ТОП ИГРОКОВ</b>

{players}

Ваше место: <b>#{rank}</b>
""",
        "profile": """
👤 <b>Профиль: {name}</b>

🆔 ID: <code>{user_id}</code>
🏆 Рейтинг: {rating} (#{rank})
💰 Монеты: {coins}
🔥 Серия: {streak} (Лучшая: {best_streak})

📊 <b>Статистика:</b>
🎮 Игры: {games}
🏆 Победы: {wins}
📈 % побед: {win_rate:.1f}%
📊 Средн. попыток: {avg_attempts:.1f}

🏅 Достижения: {achievement_count}/{total_achievements}
""",
        "daily_bonus": """
🎁 <b>Ежедневный бонус!</b>

Вы получили <b>{coins}</b> монет!
🔥 Дневная серия: {streak} дней

Возвращайтесь завтра! 🎉
""",
        "daily_already": "❌ Вы уже получили бонус сегодня!\n\nСледующий бонус: {next_time}",
        "achievement_unlocked": """
🏅 <b>НОВОЕ ДОСТИЖЕНИЕ!</b>

{name}

💰 +{coins} монет
""",
        "game_not_found": "❌ Игра не найдена!",
        "already_in_game": "❌ Вы уже в игре!",
        "cannot_play_self": "❌ Нельзя играть с самим собой!",
        "game_already_started": "❌ Эта игра уже началась!",
        
        # Buttons
        "btn_new_game": "🎮 Новая игра",
        "btn_vs_bot": "🤖 Против бота",
        "btn_vs_player": "👥 С другом",
        "btn_leaderboard": "🏆 Рейтинг",
        "btn_profile": "👤 Профиль",
        "btn_stats": "📊 Статистика",
        "btn_daily": "🎁 Ежедневный бонус",
        "btn_settings": "⚙️ Настройки",
        "btn_hint": "💡 Подсказка ({cost} монет)",
        "btn_surrender": "🏳️ Сдаться",
        "btn_back": "🔙 Назад",
        "btn_yes": "✅ Да",
        "btn_no": "❌ Нет",
        "btn_subscribe": "📢 Перейти на канал",
        "btn_check": "✅ Проверить",
        "btn_easy": "🟢 Легко (3)",
        "btn_medium": "🟡 Средне (4)",
        "btn_hard": "🔴 Сложно (5)",
        "btn_extreme": "⚫ Экстрим (6)",
    },
    "en": {
        "choose_language": "🌍 Choose a language:",
        "subscribe": "📢 Please subscribe to the channel:",
        "not_subscribed": "❌ You haven't subscribed yet!",
        "subscribed": "✅ Congratulations! You can now use the bot.",
        "main_menu": """
🏠 <b>Main Menu</b>

👤 {name}
💰 Coins: <b>{coins}</b>
🏆 Rating: <b>{rating}</b>
🔥 Streak: <b>{streak}</b>
📊 Games: <b>{wins}/{games}</b> ({win_rate:.1f}%)
""",
        "choose_mode": """
🎮 <b>Choose game mode:</b>

🤖 <b>vs Bot</b> - play against AI
👥 <b>vs Friend</b> - share the link
""",
        "choose_difficulty": """
📊 <b>Choose difficulty:</b>

🟢 <b>Easy</b> - 3 digits
🟡 <b>Medium</b> - 4 digits
🔴 <b>Hard</b> - 5 digits
⚫ <b>Extreme</b> - 6 digits
""",
        "game_created": """
✅ <b>Game created!</b>

🔗 Send this link to your friend:
{invite_link}

⏳ Waiting for opponent...
""",
        "game_started": """
🎮 <b>Game started!</b>

👤 Opponent: <b>{opponent}</b>
📊 Difficulty: <b>{difficulty}</b> digits

🔢 Enter your secret number:
(No repeating digits!)
""",
        "secret_set": "✅ Your secret number is saved! Waiting for opponent...",
        "both_ready": "✅ Both players ready! Game started!",
        "your_turn": """
🎯 <b>Your turn!</b>

💡 Hints left: {hints}
🔄 Attempts: {attempts}

Enter your guess:
""",
        "opponent_turn": "⏳ Opponent's turn. Please wait...",
        "result": """
📊 <b>Result:</b> <code>{guess}</code>

🎯 {bulls} Bull | 🐄 {cows} Cow
🔄 Attempt: {attempts}
""",
        "win": """
🎉🎉🎉 <b>CONGRATULATIONS!</b> 🎉🎉🎉

You won in <b>{attempts}</b> attempts!
🎯 Opponent's secret: <code>{secret}</code>

💰 +{coins} coins
🏆 +{rating} rating
{streak_msg}
{achievements}
""",
        "lose": """
😔 <b>Unfortunately, you lost!</b>

🎯 Opponent's secret: <code>{secret}</code>
🏆 -{rating} rating
""",
        "hint_used": """
💡 <b>Hint:</b>

Position <b>{position}</b>: digit <b>{digit}</b>

💰 -{cost} coins
💡 Remaining: {remaining}
""",
        "not_enough_coins": "❌ Not enough coins! Need: {cost}",
        "invalid_number": "❌ Invalid format! Enter a {length}-digit number (no repeats).",
        "not_your_turn": "❌ It's not your turn!",
        "surrender_confirm": "🏳️ Are you sure you want to surrender?",
        "surrendered": "🏳️ You surrendered.",
        "opponent_surrendered": "🎉 Opponent surrendered! You win!",
        "leaderboard": """
🏆 <b>TOP PLAYERS</b>

{players}

Your rank: <b>#{rank}</b>
""",
        "profile": """
👤 <b>Profile: {name}</b>

🆔 ID: <code>{user_id}</code>
🏆 Rating: {rating} (#{rank})
💰 Coins: {coins}
🔥 Streak: {streak} (Best: {best_streak})

📊 <b>Statistics:</b>
🎮 Games: {games}
🏆 Wins: {wins}
📈 Win rate: {win_rate:.1f}%
📊 Avg attempts: {avg_attempts:.1f}

🏅 Achievements: {achievement_count}/{total_achievements}
""",
        "daily_bonus": """
🎁 <b>Daily bonus!</b>

You received <b>{coins}</b> coins!
🔥 Daily streak: {streak} days

Come back tomorrow! 🎉
""",
        "daily_already": "❌ You already claimed today's bonus!\n\nNext bonus: {next_time}",
        "achievement_unlocked": """
🏅 <b>NEW ACHIEVEMENT!</b>

{name}

💰 +{coins} coins
""",
        "game_not_found": "❌ Game not found!",
        "already_in_game": "❌ You're already in a game!",
        "cannot_play_self": "❌ You can't play with yourself!",
        "game_already_started": "❌ This game has already started!",
        
        # Buttons
        "btn_new_game": "🎮 New Game",
        "btn_vs_bot": "🤖 vs Bot",
        "btn_vs_player": "👥 vs Friend",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_profile": "👤 Profile",
        "btn_stats": "📊 Statistics",
        "btn_daily": "🎁 Daily Bonus",
        "btn_settings": "⚙️ Settings",
        "btn_hint": "💡 Hint ({cost} coins)",
        "btn_surrender": "🏳️ Surrender",
        "btn_back": "🔙 Back",
        "btn_yes": "✅ Yes",
        "btn_no": "❌ No",
        "btn_subscribe": "📢 Go to channel",
        "btn_check": "✅ Check",
        "btn_easy": "🟢 Easy (3)",
        "btn_medium": "🟡 Medium (4)",
        "btn_hard": "🔴 Hard (5)",
        "btn_extreme": "⚫ Extreme (6)",
    },
    "kk": {
        "choose_language": "🌍 Tildi saylań:",
        "subscribe": "📢 Kanalǵa jazılıń:",
        "not_subscribed": "❌ Siz áli jazılmadıńız!",
        "subscribed": "✅ Qutlıqlaymız! Endi bottan paydala alasız.",
        "main_menu": """
🏠 <b>Bas menyu</b>

👤 {name}
💰 Coins: <b>{coins}</b>
🏆 Rating: <b>{rating}</b>
🔥 Seriya: <b>{streak}</b>
📊 Oyınlar: <b>{wins}/{games}</b> ({win_rate:.1f}%)
""",
        "btn_new_game": "🎮 Jańa oyın",
        "btn_vs_bot": "🤖 Bot penen",
        "btn_vs_player": "👥 Dos penen",
        "btn_leaderboard": "🏆 Reytinglar",
        "btn_profile": "👤 Profil",
        "btn_stats": "📊 Statistika",
        "btn_daily": "🎁 Kúnlik bonus",
        "btn_settings": "⚙️ Sazlamalar",
        "btn_hint": "💡 Kómek ({cost} coin)",
        "btn_surrender": "🏳️ Taslim",
        "btn_back": "🔙 Artqa",
        "btn_yes": "✅ Awa",
        "btn_no": "❌ Yaq",
        "btn_subscribe": "📢 Kanalǵa ótiw",
        "btn_check": "✅ Tekserip kóriw",
        "btn_easy": "🟢 Jeńil (3)",
        "btn_medium": "🟡 Ortasha (4)",
        "btn_hard": "🔴 Qıyın (5)",
        "btn_extreme": "⚫ Ekstrim (6)",
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    """MongoDB database manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URI)
            self.db = self.client[DB_NAME]
            
            self.players = self.db.players
            self.games = self.db.games
            
            await self.create_indexes()
            await self.client.admin.command('ping')
            
            logger.info("✅ MongoDB connected!")
        except Exception as e:
            logger.error(f"❌ MongoDB error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")
    
    async def create_indexes(self):
        """Create indexes."""
        await self.players.create_index("user_id", unique=True)
        await self.players.create_index([("rating", -1)])
        await self.games.create_index("game_id", unique=True)
        await self.games.create_index([("is_finished", 1)])
    
    # Players
    async def get_player(self, user_id: int) -> Optional[Dict]:
        return await self.players.find_one({"user_id": user_id})
    
    async def create_player(self, user_id: int, username: str = "", first_name: str = "", language: str = "uz") -> Dict:
        player = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "language": language,
            "coins": 100,
            "rating": 1000,
            "games_played": 0,
            "games_won": 0,
            "current_streak": 0,
            "best_streak": 0,
            "total_attempts": 0,
            "hints_used": 0,
            "achievements": [],
            "last_daily": None,
            "created_at": datetime.utcnow()
        }
        await self.players.insert_one(player)
        return player
    
    async def update_player(self, user_id: int, data: Dict) -> bool:
        result = await self.players.update_one({"user_id": user_id}, {"$set": data})
        return result.modified_count > 0
    
    async def increment_stats(self, user_id: int, increments: Dict) -> bool:
        result = await self.players.update_one({"user_id": user_id}, {"$inc": increments})
        return result.modified_count > 0
    
    async def add_achievement(self, user_id: int, achievement: str) -> bool:
        result = await self.players.update_one(
            {"user_id": user_id},
            {"$addToSet": {"achievements": achievement}}
        )
        return result.modified_count > 0
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        cursor = self.players.find().sort("rating", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_rank(self, user_id: int) -> int:
        player = await self.get_player(user_id)
        if not player:
            return 0
        count = await self.players.count_documents({"rating": {"$gt": player["rating"]}})
        return count + 1
    
    # Games
    async def create_game(self, game_data: Dict) -> str:
        game_data["created_at"] = datetime.utcnow()
        await self.games.insert_one(game_data)
        return game_data["game_id"]
    
    async def get_game(self, game_id: str) -> Optional[Dict]:
        return await self.games.find_one({"game_id": game_id})
    
    async def get_active_game(self, user_id: int) -> Optional[Dict]:
        return await self.games.find_one({
            "$or": [{"player1_id": user_id}, {"player2_id": user_id}],
            "is_finished": False
        })
    
    async def update_game(self, game_id: str, data: Dict) -> bool:
        result = await self.games.update_one({"game_id": game_id}, {"$set": data})
        return result.modified_count > 0
    
    async def add_move(self, game_id: str, move: Dict) -> bool:
        result = await self.games.update_one(
            {"game_id": game_id},
            {"$push": {"history": move}}
        )
        return result.modified_count > 0

db = Database()

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_text(lang: str, key: str, **kwargs) -> str:
    """Get translated text."""
    text = MESSAGES.get(lang, MESSAGES["uz"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

def get_button_text(lang: str, key: str, **kwargs) -> str:
    """Get button text."""
    btn_key = f"btn_{key}"
    return get_text(lang, btn_key, **kwargs)

def generate_secret(length: int) -> str:
    """Generate secret number."""
    digits = list("0123456789")
    random.shuffle(digits)
    if digits[0] == "0":
        for i in range(1, len(digits)):
            if digits[i] != "0":
                digits[0], digits[i] = digits[i], digits[0]
                break
    return "".join(digits[:length])

def validate_number(text: str, length: int) -> bool:
    """Validate number."""
    if len(text) != length or not text.isdigit():
        return False
    return len(set(text)) == length and text[0] != "0"

def calculate_bulls_cows(secret: str, guess: str) -> Tuple[int, int]:
    """Calculate bulls and cows."""
    bulls = sum(s == g for s, g in zip(secret, guess))
    cows = sum(min(secret.count(d), guess.count(d)) for d in set(guess)) - bulls
    return bulls, cows

def calculate_rating_change(winner_rating: int, loser_rating: int) -> int:
    """Calculate ELO rating change."""
    expected = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    return max(10, int(32 * (1 - expected)))

def get_hint_cost(difficulty: int) -> int:
    """Get hint cost."""
    costs = {3: 20, 4: 30, 5: 50, 6: 80}
    return costs.get(difficulty, 30)

def get_max_hints(difficulty: int) -> int:
    """Get max hints."""
    return difficulty - 1

def check_achievements(player: Dict, game: Dict, attempts: int) -> List[str]:
    """Check for new achievements."""
    new_achievements = []
    current = set(player.get("achievements", []))
    
    # First win
    if "first_win" not in current and player["games_won"] == 0:
        new_achievements.append("first_win")
    
    # Speed (3 attempts or less)
    if "speed_3" not in current and attempts <= 3:
        new_achievements.append("speed_3")
    
    # Streak
    if "streak_3" not in current and player["current_streak"] + 1 >= 3:
        new_achievements.append("streak_3")
    if "streak_5" not in current and player["current_streak"] + 1 >= 5:
        new_achievements.append("streak_5")
    if "streak_10" not in current and player["current_streak"] + 1 >= 10:
        new_achievements.append("streak_10")
    
    # Bot killer
    if "bot_killer" not in current and game["mode"] == GameMode.VS_BOT.value:
        new_achievements.append("bot_killer")
    
    # Hard mode
    if "hard_mode" not in current and game["difficulty"] >= 5:
        new_achievements.append("hard_mode")
    
    # 100 games
    if "games_100" not in current and player["games_played"] + 1 >= 100:
        new_achievements.append("games_100")
    
    # Master (2000+ rating)
    if "master" not in current and player["rating"] >= 2000:
        new_achievements.append("master")
    
    return new_achievements

# ═══════════════════════════════════════════════════════════════════════════════
# AI PLAYER
# ═══════════════════════════════════════════════════════════════════════════════

class AIPlayer:
    """Simple AI player."""
    
    def __init__(self, difficulty: int):
        self.difficulty = difficulty
        self.possible = self._generate_all()
        self.guesses = []
    
    def _generate_all(self) -> List[str]:
        """Generate all possible numbers."""
        from itertools import permutations
        all_nums = []
        for perm in permutations("0123456789", self.difficulty):
            if perm[0] != "0":
                all_nums.append("".join(perm))
        return all_nums
    
    def make_guess(self) -> str:
        """Make a guess."""
        if self.possible:
            guess = random.choice(self.possible)
        else:
            guess = generate_secret(self.difficulty)
        self.guesses.append(guess)
        return guess
    
    def update(self, guess: str, bulls: int, cows: int):
        """Update possibilities."""
        self.possible = [
            num for num in self.possible
            if calculate_bulls_cows(num, guess) == (bulls, cows)
        ]

# ═══════════════════════════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════════

def get_language_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"lang_{code}")]
               for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_subscribe_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button_text(lang, "subscribe"), url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text=get_button_text(lang, "check"), callback_data="check_sub")]
    ])

def get_main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button_text(lang, "new_game"), callback_data="new_game")],
        [
            InlineKeyboardButton(text=get_button_text(lang, "leaderboard"), callback_data="leaderboard"),
            InlineKeyboardButton(text=get_button_text(lang, "profile"), callback_data="profile")
        ],
        [
            InlineKeyboardButton(text=get_button_text(lang, "daily"), callback_data="daily"),
            InlineKeyboardButton(text=get_button_text(lang, "stats"), callback_data="stats")
        ],
        [InlineKeyboardButton(text=get_button_text(lang, "settings"), callback_data="settings")]
    ])

def get_mode_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button_text(lang, "vs_bot"), callback_data="mode_bot")],
        [InlineKeyboardButton(text=get_button_text(lang, "vs_player"), callback_data="mode_player")],
        [InlineKeyboardButton(text=get_button_text(lang, "back"), callback_data="back_main")]
    ])

def get_difficulty_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button_text(lang, "easy"), callback_data="diff_3")],
        [InlineKeyboardButton(text=get_button_text(lang, "medium"), callback_data="diff_4")],
        [InlineKeyboardButton(text=get_button_text(lang, "hard"), callback_data="diff_5")],
        [InlineKeyboardButton(text=get_button_text(lang, "extreme"), callback_data="diff_6")],
        [InlineKeyboardButton(text=get_button_text(lang, "back"), callback_data="back_mode")]
    ])

def get_game_keyboard(lang: str, hints_left: int, hint_cost: int) -> InlineKeyboardMarkup:
    buttons = []
    if hints_left > 0:
        buttons.append([InlineKeyboardButton(
            text=get_button_text(lang, "hint", cost=hint_cost),
            callback_data="use_hint"
        )])
    buttons.append([InlineKeyboardButton(text=get_button_text(lang, "surrender"), callback_data="surrender")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_button_text(lang, "yes"), callback_data="confirm_yes"),
            InlineKeyboardButton(text=get_button_text(lang, "no"), callback_data="confirm_no")
        ]
    ])

def get_back_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button_text(lang, "back"), callback_data="back_main")]
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# FSM STATES
# ═══════════════════════════════════════════════════════════════════════════════

class GameStates(StatesGroup):
    choosing_language = State()
    main_menu = State()
    choosing_mode = State()
    choosing_difficulty = State()
    waiting_opponent = State()
    entering_secret = State()
    playing = State()

# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

router = Router()

# ──────────────────────────────────────────────────────────────────────────────
# START & LANGUAGE
# ──────────────────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start command."""
    user_id = message.from_user.id
    player = await db.get_player(user_id)
    
    # Check for invite
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("invite_"):
        await state.update_data(pending_invite=args[1])
    
    # New user
    if not player:
        await state.set_state(GameStates.choosing_language)
        await message.answer(
            "🌍 Tilni tanlang / Выберите язык / Choose language:",
            reply_markup=get_language_keyboard()
        )
        return
    
    # Existing user
    lang = player["language"]
    
    # Check subscription
    try:
        member = await message.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status not in ["member", "creator", "administrator", "restricted"]:
            await message.answer(
                get_text(lang, "subscribe"),
                reply_markup=get_subscribe_keyboard(lang)
            )
            return
    except:
        pass
    
    # Check active game
    active_game = await db.get_active_game(user_id)
    if active_game:
        await message.answer(
            get_text(lang, "surrender_confirm"),
            reply_markup=get_confirm_keyboard(lang)
        )
        return
    
    # Show main menu
    await show_main_menu(message, player)

@router.callback_query(F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery, state: FSMContext):
    """Select language."""
    lang_code = callback.data.split("_")[1]
    user = callback.from_user
    
    player = await db.create_player(user.id, user.username or "", user.first_name or "", lang_code)
    
    await callback.answer()
    await state.set_state(GameStates.main_menu)
    
    # Check subscription
    await callback.message.edit_text(
        get_text(lang_code, "subscribe"),
        reply_markup=get_subscribe_keyboard(lang_code)
    )

@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery, state: FSMContext):
    """Check subscription."""
    user_id = callback.from_user.id
    player = await db.get_player(user_id)
    lang = player["language"]
    
    try:
        member = await callback.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "creator", "administrator", "restricted"]:
            await callback.answer(get_text(lang, "subscribed"), show_alert=True)
            
            # Check pending invite
            data = await state.get_data()
            if "pending_invite" in data:
                await process_invite(callback.message, player, data["pending_invite"], state, callback.bot)
                await state.update_data(pending_invite=None)
            else:
                await show_main_menu(callback.message, player, edit=True)
        else:
            await callback.answer(get_text(lang, "not_subscribed"), show_alert=True)
    except:
        await callback.answer(get_text(lang, "not_subscribed"), show_alert=True)

# ──────────────────────────────────────────────────────────────────────────────
# MAIN MENU
# ──────────────────────────────────────────────────────────────────────────────

async def show_main_menu(message: Message, player: Dict, edit: bool = False):
    """Show main menu."""
    lang = player["language"]
    
    text = get_text(
        lang, "main_menu",
        name=player["first_name"],
        coins=player["coins"],
        rating=player["rating"],
        streak=player["current_streak"],
        wins=player["games_won"],
        games=player["games_played"],
        win_rate=player["games_won"] / player["games_played"] * 100 if player["games_played"] > 0 else 0
    )
    
    if edit:
        await message.edit_text(text, reply_markup=get_main_menu_keyboard(lang))
    else:
        await message.answer(text, reply_markup=get_main_menu_keyboard(lang))

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    """Back to main menu."""
    player = await db.get_player(callback.from_user.id)
    await callback.answer()
    await show_main_menu(callback.message, player, edit=True)

# ──────────────────────────────────────────────────────────────────────────────
# NEW GAME
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "new_game")
async def new_game(callback: CallbackQuery, state: FSMContext):
    """New game."""
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    
    # Check active game
    active = await db.get_active_game(callback.from_user.id)
    if active:
        await callback.answer(get_text(lang, "already_in_game"), show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(GameStates.choosing_mode)
    
    await callback.message.edit_text(
        get_text(lang, "choose_mode"),
        reply_markup=get_mode_keyboard(lang)
    )

@router.callback_query(F.data.startswith("mode_"))
async def select_mode(callback: CallbackQuery, state: FSMContext):
    """Select game mode."""
    mode = callback.data.split("_")[1]
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    
    await state.update_data(game_mode=mode)
    await callback.answer()
    await state.set_state(GameStates.choosing_difficulty)
    
    await callback.message.edit_text(
        get_text(lang, "choose_difficulty"),
        reply_markup=get_difficulty_keyboard(lang)
    )

@router.callback_query(F.data == "back_mode")
async def back_to_mode(callback: CallbackQuery, state: FSMContext):
    """Back to mode selection."""
    player = await db.get_player(callback.from_user.id)
    await callback.answer()
    await state.set_state(GameStates.choosing_mode)
    
    await callback.message.edit_text(
        get_text(player["language"], "choose_mode"),
        reply_markup=get_mode_keyboard(player["language"])
    )

@router.callback_query(F.data.startswith("diff_"))
async def select_difficulty(callback: CallbackQuery, state: FSMContext):
    """Select difficulty."""
    difficulty = int(callback.data.split("_")[1])
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    data = await state.get_data()
    mode = data.get("game_mode", "bot")
    
    await callback.answer()
    
    # Generate game ID
    game_id = f"{int(datetime.utcnow().timestamp() * 1000)}"
    
    # Create game
    game_data = {
        "game_id": game_id,
        "mode": f"vs_{mode}",
        "difficulty": difficulty,
        "player1_id": callback.from_user.id,
        "player2_id": None,
        "secret1": None,
        "secret2": None,
        "turn": None,
        "attempts": {},
        "hints_used": {},
        "history": [],
        "is_finished": False
    }
    
    if mode == "bot":
        # vs Bot
        game_data["player2_id"] = 0
        game_data["secret2"] = generate_secret(difficulty)
        await db.create_game(game_data)
        await state.update_data(game_id=game_id)
        await state.set_state(GameStates.entering_secret)
        
        await callback.message.edit_text(
            get_text(lang, "game_started", opponent="🤖 Bot", difficulty=difficulty)
        )
    else:
        # vs Player
        await db.create_game(game_data)
        await state.update_data(game_id=game_id)
        await state.set_state(GameStates.waiting_opponent)
        
        bot_info = await callback.bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start=invite_{game_id}"
        
        await callback.message.edit_text(
            get_text(lang, "game_created", invite_link=invite_link)
        )

async def process_invite(message: Message, player: Dict, invite_arg: str, state: FSMContext, bot: Bot):
    """Process invite."""
    game_id = invite_arg.replace("invite_", "")
    game = await db.get_game(game_id)
    lang = player["language"]
    
    if not game:
        await message.edit_text(get_text(lang, "game_not_found"))
        return
    
    if game["player1_id"] == player["user_id"]:
        await message.edit_text(get_text(lang, "cannot_play_self"))
        return
    
    if game["player2_id"]:
        await message.edit_text(get_text(lang, "game_already_started"))
        return
    
    # Join game
    await db.update_game(game_id, {"player2_id": player["user_id"]})
    await state.update_data(game_id=game_id)
    await state.set_state(GameStates.entering_secret)
    
    # Notify both players
    player1 = await db.get_player(game["player1_id"])
    
    await bot.send_message(
        game["player1_id"],
        get_text(player1["language"], "game_started", 
                opponent=player["first_name"], 
                difficulty=game["difficulty"])
    )
    
    await message.edit_text(
        get_text(lang, "game_started", 
                opponent=player1["first_name"], 
                difficulty=game["difficulty"])
    )

# ──────────────────────────────────────────────────────────────────────────────
# GAME PLAY
# ──────────────────────────────────────────────────────────────────────────────

@router.message(StateFilter(GameStates.entering_secret))
async def enter_secret(message: Message, state: FSMContext):
    """Enter secret number."""
    player = await db.get_player(message.from_user.id)
    lang = player["language"]
    data = await state.get_data()
    game = await db.get_game(data.get("game_id"))
    
    if not game:
        await message.answer(get_text(lang, "game_not_found"))
        return
    
    text = message.text.strip()
    difficulty = game["difficulty"]
    
    if not validate_number(text, difficulty):
        await message.answer(get_text(lang, "invalid_number", length=difficulty))
        return
    
    # Save secret
    if game["player1_id"] == player["user_id"]:
        await db.update_game(game["game_id"], {"secret1": text})
        game["secret1"] = text
    else:
        await db.update_game(game["game_id"], {"secret2": text})
        game["secret2"] = text
    
    await message.answer(get_text(lang, "secret_set"))
    
    # Check if both ready
    if game["secret1"] and game["secret2"]:
        await db.update_game(game["game_id"], {
            "turn": game["player1_id"],
            "attempts": {str(game["player1_id"]): 0, str(game["player2_id"]): 0},
            "hints_used": {str(game["player1_id"]): 0, str(game["player2_id"]): 0}
        })
        
        await state.set_state(GameStates.playing)
        
        # Notify player 1
        player1 = await db.get_player(game["player1_id"])
        max_hints = get_max_hints(difficulty)
        hint_cost = get_hint_cost(difficulty)
        
        await message.bot.send_message(
            game["player1_id"],
            get_text(player1["language"], "your_turn", hints=max_hints, attempts=0),
            reply_markup=get_game_keyboard(player1["language"], max_hints, hint_cost)
        )
        
        # Notify player 2 if not bot
        if game["player2_id"] != 0:
            player2 = await db.get_player(game["player2_id"])
            await message.bot.send_message(
                game["player2_id"],
                get_text(player2["language"], "opponent_turn")
            )

@router.message(StateFilter(GameStates.playing))
async def make_guess(message: Message, state: FSMContext):
    """Make a guess."""
    player = await db.get_player(message.from_user.id)
    lang = player["language"]
    data = await state.get_data()
    game = await db.get_game(data.get("game_id"))
    
    if not game:
        await message.answer(get_text(lang, "game_not_found"))
        return
    
    # Check turn
    if game["turn"] != player["user_id"]:
        await message.answer(get_text(lang, "not_your_turn"))
        return
    
    text = message.text.strip()
    difficulty = game["difficulty"]
    
    if not validate_number(text, difficulty):
        await message.answer(get_text(lang, "invalid_number", length=difficulty))
        return
    
    # Calculate result
    player_key = str(player["user_id"])
    attempts = game["attempts"].get(player_key, 0) + 1
    game["attempts"][player_key] = attempts
    
    if player["user_id"] == game["player1_id"]:
        secret = game["secret2"]
        opponent_id = game["player2_id"]
    else:
        secret = game["secret1"]
        opponent_id = game["player1_id"]
    
    bulls, cows = calculate_bulls_cows(secret, text)
    
    # Save move
    await db.add_move(game["game_id"], {
        "player": player["user_id"],
        "guess": text,
        "bulls": bulls,
        "cows": cows,
        "attempt": attempts
    })
    await db.update_game(game["game_id"], {"attempts": game["attempts"]})
    
    # Check win
    if bulls == difficulty:
        await handle_win(message, player, game, secret, opponent_id, attempts, state)
        return
    
    # Show result
    await message.answer(
        get_text(lang, "result", guess=text, bulls=bulls, cows=cows, attempts=attempts)
    )
    
    # Bot move
    if game["mode"] == GameMode.VS_BOT.value:
        await asyncio.sleep(1)
        await bot_move(message, player, game, state)
    else:
        # Switch turn
        await db.update_game(game["game_id"], {"turn": opponent_id})
        
        opponent = await db.get_player(opponent_id)
        max_hints = get_max_hints(difficulty)
        hint_cost = get_hint_cost(difficulty)
        hints_left = max_hints - game["hints_used"].get(str(opponent_id), 0)
        opponent_attempts = game["attempts"].get(str(opponent_id), 0)
        
        await message.bot.send_message(
            opponent_id,
            get_text(opponent["language"], "your_turn", hints=hints_left, attempts=opponent_attempts),
            reply_markup=get_game_keyboard(opponent["language"], hints_left, hint_cost)
        )
        
        await message.answer(get_text(lang, "opponent_turn"))

async def bot_move(message: Message, player: Dict, game: Dict, state: FSMContext):
    """Bot makes a move."""
    lang = player["language"]
    
    # Get or create AI
    data = await state.get_data()
    ai_possible = data.get("ai_possible")
    
    if not ai_possible:
        ai = AIPlayer(game["difficulty"])
    else:
        ai = AIPlayer(game["difficulty"])
        ai.possible = ai_possible
    
    # Update AI with history
    for move in game.get("history", []):
        if move["player"] == 0:
            ai.update(move["guess"], move["bulls"], move["cows"])
    
    # Make guess
    guess = ai.make_guess()
    bot_key = "0"
    attempts = game["attempts"].get(bot_key, 0) + 1
    game["attempts"][bot_key] = attempts
    
    bulls, cows = calculate_bulls_cows(game["secret1"], guess)
    
    # Save move
    await db.add_move(game["game_id"], {
        "player": 0,
        "guess": guess,
        "bulls": bulls,
        "cows": cows,
        "attempt": attempts
    })
    await db.update_game(game["game_id"], {"attempts": game["attempts"]})
    
    # Update AI
    ai.update(guess, bulls, cows)
    await state.update_data(ai_possible=ai.possible)
    
    # Check win
    if bulls == game["difficulty"]:
        await handle_loss(message, player, game, game["secret1"], state)
        return
    
    # Show bot move
    await message.answer(
        f"🤖 Bot taxmini: <code>{guess}</code>\n🎯 {bulls} Bull | 🐄 {cows} Cow"
    )
    
    # Player turn
    await db.update_game(game["game_id"], {"turn": player["user_id"]})
    
    max_hints = get_max_hints(game["difficulty"])
    hint_cost = get_hint_cost(game["difficulty"])
    hints_left = max_hints - game["hints_used"].get(str(player["user_id"]), 0)
    player_attempts = game["attempts"].get(str(player["user_id"]), 0)
    
    await message.answer(
        get_text(lang, "your_turn", hints=hints_left, attempts=player_attempts),
        reply_markup=get_game_keyboard(lang, hints_left, hint_cost)
    )

async def handle_win(message: Message, player: Dict, game: Dict, secret: str, opponent_id: int, attempts: int, state: FSMContext):
    """Handle win."""
    lang = player["language"]
    
    await db.update_game(game["game_id"], {"is_finished": True, "winner_id": player["user_id"]})
    
    # Calculate rewards
    base_coins = 50
    speed_bonus = max(0, (10 - attempts) * 10)
    diff_bonus = game["difficulty"] * 20
    
    # Update streak
    new_streak = player["current_streak"] + 1
    streak_coins = new_streak * 10
    
    total_coins = base_coins + speed_bonus + diff_bonus + streak_coins
    
    # Rating
    if opponent_id == 0:
        rating_change = 15
    else:
        opponent = await db.get_player(opponent_id)
        rating_change = calculate_rating_change(player["rating"], opponent["rating"])
    
    # Update player
    await db.increment_stats(player["user_id"], {
        "coins": total_coins,
        "rating": rating_change,
        "games_played": 1,
        "games_won": 1,
        "total_attempts": attempts,
        "current_streak": 1,
    })
    
    # Update best streak
    if new_streak > player["best_streak"]:
        await db.update_player(player["user_id"], {"best_streak": new_streak})
    
    # Check achievements
    new_achievements = check_achievements(player, game, attempts)
    achievement_text = ""
    
    for ach_id in new_achievements:
        await db.add_achievement(player["user_id"], ach_id)
        ach = ACHIEVEMENTS[ach_id]
        await db.increment_stats(player["user_id"], {"coins": ach["coins"]})
        achievement_text += f"\n🏅 {ach[f'name_{lang}']} (+{ach['coins']} coins)"
    
    streak_msg = f"🔥 Streak bonus: +{streak_coins} coins" if new_streak > 1 else ""
    
    # Send win message
    await message.answer(
        get_text(lang, "win",
                attempts=attempts,
                secret=secret,
                coins=total_coins,
                rating=rating_change,
                streak_msg=streak_msg,
                achievements=achievement_text),
        reply_markup=get_main_menu_keyboard(lang)
    )
    
    # Notify opponent
    if opponent_id != 0:
        opponent = await db.get_player(opponent_id)
        await db.increment_stats(opponent_id, {
            "games_played": 1,
            "rating": -rating_change,
            "current_streak": -opponent["current_streak"]
        })
        
        await message.bot.send_message(
            opponent_id,
            get_text(opponent["language"], "lose", secret=game["secret1"] if player["user_id"] == game["player2_id"] else game["secret2"], rating=rating_change),
            reply_markup=get_main_menu_keyboard(opponent["language"])
        )
    
    await state.set_state(GameStates.main_menu)

async def handle_loss(message: Message, player: Dict, game: Dict, secret: str, state: FSMContext):
    """Handle loss (vs bot)."""
    lang = player["language"]
    
    await db.update_game(game["game_id"], {"is_finished": True, "winner_id": 0})
    
    rating_change = 15
    
    await db.increment_stats(player["user_id"], {
        "games_played": 1,
        "rating": -rating_change,
        "current_streak": -player["current_streak"]
    })
    
    await message.answer(
        get_text(lang, "lose", secret=secret, rating=rating_change),
        reply_markup=get_main_menu_keyboard(lang)
    )
    
    await state.set_state(GameStates.main_menu)

# ──────────────────────────────────────────────────────────────────────────────
# HINT
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "use_hint")
async def use_hint(callback: CallbackQuery, state: FSMContext):
    """Use hint."""
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    data = await state.get_data()
    game = await db.get_game(data.get("game_id"))
    
    if not game or game["turn"] != player["user_id"]:
        await callback.answer(get_text(lang, "not_your_turn"), show_alert=True)
        return
    
    cost = get_hint_cost(game["difficulty"])
    max_hints = get_max_hints(game["difficulty"])
    player_key = str(player["user_id"])
    used = game["hints_used"].get(player_key, 0)
    
    if used >= max_hints:
        await callback.answer("❌ Hintlar tugadi!", show_alert=True)
        return
    
    if player["coins"] < cost:
        await callback.answer(get_text(lang, "not_enough_coins", cost=cost), show_alert=True)
        return
    
    # Use hint
    await db.increment_stats(player["user_id"], {"coins": -cost, "hints_used": 1})
    
    game["hints_used"][player_key] = used + 1
    await db.update_game(game["game_id"], {"hints_used": game["hints_used"]})
    
    # Reveal position
    if player["user_id"] == game["player1_id"]:
        secret = game["secret2"]
    else:
        secret = game["secret1"]
    
    revealed = data.get("revealed_positions", [])
    available = [i for i in range(len(secret)) if i not in revealed]
    
    if available:
        pos = random.choice(available)
        revealed.append(pos)
        await state.update_data(revealed_positions=revealed)
        
        await callback.answer()
        await callback.message.answer(
            get_text(lang, "hint_used",
                    position=pos + 1,
                    digit=secret[pos],
                    cost=cost,
                    remaining=max_hints - used - 1)
        )
    else:
        await callback.answer("❌ Barcha pozitsiyalar ochilgan!", show_alert=True)

# ──────────────────────────────────────────────────────────────────────────────
# SURRENDER
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "surrender")
async def surrender(callback: CallbackQuery, state: FSMContext):
    """Surrender confirmation."""
    player = await db.get_player(callback.from_user.id)
    await callback.answer()
    
    await callback.message.edit_text(
        get_text(player["language"], "surrender_confirm"),
        reply_markup=get_confirm_keyboard(player["language"])
    )

@router.callback_query(F.data == "confirm_yes")
async def confirm_surrender(callback: CallbackQuery, state: FSMContext):
    """Confirm surrender."""
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    data = await state.get_data()
    game = await db.get_game(data.get("game_id"))
    
    if game:
        await db.update_game(game["game_id"], {"is_finished": True})
        
        # Update stats
        await db.increment_stats(player["user_id"], {
            "games_played": 1,
            "rating": -20,
            "current_streak": -player["current_streak"]
        })
        
        # Notify opponent
        opponent_id = game["player2_id"] if player["user_id"] == game["player1_id"] else game["player1_id"]
        if opponent_id and opponent_id != 0:
            opponent = await db.get_player(opponent_id)
            await db.increment_stats(opponent_id, {
                "games_played": 1,
                "games_won": 1,
                "rating": 20,
                "coins": 30,
                "current_streak": 1
            })
            
            await callback.bot.send_message(
                opponent_id,
                get_text(opponent["language"], "opponent_surrendered"),
                reply_markup=get_main_menu_keyboard(opponent["language"])
            )
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(lang, "surrendered"),
        reply_markup=get_main_menu_keyboard(lang)
    )
    await state.set_state(GameStates.main_menu)

@router.callback_query(F.data == "confirm_no")
async def cancel_surrender(callback: CallbackQuery, state: FSMContext):
    """Cancel surrender."""
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    data = await state.get_data()
    game = await db.get_game(data.get("game_id"))
    
    await callback.answer()
    
    if game and game["turn"] == player["user_id"]:
        max_hints = get_max_hints(game["difficulty"])
        hint_cost = get_hint_cost(game["difficulty"])
        player_key = str(player["user_id"])
        hints_left = max_hints - game["hints_used"].get(player_key, 0)
        attempts = game["attempts"].get(player_key, 0)
        
        await callback.message.edit_text(
            get_text(lang, "your_turn", hints=hints_left, attempts=attempts),
            reply_markup=get_game_keyboard(lang, hints_left, hint_cost)
        )
    else:
        await callback.message.edit_text(
            get_text(lang, "opponent_turn")
        )

# ──────────────────────────────────────────────────────────────────────────────
# LEADERBOARD
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    """Show leaderboard."""
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    
    top = await db.get_leaderboard(10)
    rank = await db.get_rank(player["user_id"])
    
    players_text = ""
    medals = ["🥇", "🥈", "🥉"]
    
    for i, p in enumerate(top):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = p["first_name"][:15]
        you = " ← Siz" if p["user_id"] == player["user_id"] else ""
        players_text += f"{medal} <b>{name}</b> - {p['rating']} 🏆{you}\n"
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(lang, "leaderboard", players=players_text, rank=rank),
        reply_markup=get_back_keyboard(lang)
    )

# ──────────────────────────────────────────────────────────────────────────────
# PROFILE & STATS
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Show profile."""
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    rank = await db.get_rank(player["user_id"])
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(lang, "profile",
                name=player["first_name"],
                user_id=player["user_id"],
                rating=player["rating"],
                rank=rank,
                coins=player["coins"],
                streak=player["current_streak"],
                best_streak=player["best_streak"],
                games=player["games_played"],
                wins=player["games_won"],
                win_rate=player["games_won"] / player["games_played"] * 100 if player["games_played"] > 0 else 0,
                avg_attempts=player["total_attempts"] / player["games_won"] if player["games_won"] > 0 else 0,
                achievement_count=len(player.get("achievements", [])),
                total_achievements=len(ACHIEVEMENTS)),
        reply_markup=get_back_keyboard(lang)
    )

@router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    """Show statistics."""
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    
    # Note: For full stats, you'd need to track more data
    # This is a simplified version
    
    text = f"""
📊 <b>Batafsil statistika</b>

🎮 Jami o'yinlar: {player['games_played']}
🏆 G'alabalar: {player['games_won']}
😔 Mag'lubiyatlar: {player['games_played'] - player['games_won']}
📈 G'alaba foizi: {player['games_won'] / player['games_played'] * 100 if player['games_played'] > 0 else 0:.1f}%

🔥 Hozirgi streak: {player['current_streak']}
🏆 Eng yaxshi streak: {player['best_streak']}

📊 O'rtacha urinish: {player['total_attempts'] / player['games_won'] if player['games_won'] > 0 else 0:.1f}
💡 Ishlatilgan hintlar: {player['hints_used']}
"""
    
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(lang))

# ──────────────────────────────────────────────────────────────────────────────
# DAILY BONUS
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "daily")
async def claim_daily(callback: CallbackQuery):
    """Claim daily bonus."""
    player = await db.get_player(callback.from_user.id)
    lang = player["language"]
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    if player.get("last_daily") == today:
        next_time = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d %H:00")
        await callback.answer(get_text(lang, "daily_already", next_time=next_time), show_alert=True)
        return
    
    # Calculate streak
    if player.get("last_daily"):
        last = datetime.strptime(player["last_daily"], "%Y-%m-%d")
        if (datetime.utcnow() - last).days == 1:
            daily_streak = 1
        else:
            daily_streak = 1
    else:
        daily_streak = 1
    
    bonus = 50 + (daily_streak * 10)
    
    await db.update_player(player["user_id"], {"last_daily": today})
    await db.increment_stats(player["user_id"], {"coins": bonus})
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(lang, "daily_bonus", coins=bonus, streak=daily_streak),
        reply_markup=get_back_keyboard(lang)
    )

# ──────────────────────────────────────────────────────────────────────────────
# SETTINGS
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    """Show settings."""
    player = await db.get_player(callback.from_user.id)
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(player["language"], "choose_language"),
        reply_markup=get_language_keyboard()
    )

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def on_startup(bot: Bot):
    """Startup."""
    await db.connect()
    logger.info("🚀 Bot started!")

async def on_shutdown(bot: Bot):
    """Shutdown."""
    await db.disconnect()
    logger.info("👋 Bot stopped!")

async def main():
    """Main function."""
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(router)
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped (Ctrl+C)")
