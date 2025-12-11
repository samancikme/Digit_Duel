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
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
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

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "7701613822:AAFEOPYnLokpQpF-mu73edLbH5e7PINiLMo")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@samancikschannel")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "bulls_cows_bot")

logger.info(f"🔧 Bot Token: {BOT_TOKEN[:20]}...")
logger.info(f"🔧 MongoDB URI: {MONGODB_URI[:30]}...")
logger.info(f"🔧 Database: {DB_NAME}")
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

LANGUAGES = {
    "uz": "🇺🇿 O'zbek",
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "kk": "🇰🇿 Qaraqalpaq"
}

ACHIEVEMENTS = {
    "first_win": {"name_uz": "🏆 Birinchi g'alaba", "name_ru": "🏆 Первая победа", "name_en": "🏆 First Win", "coins": 100},
    "speed_3": {"name_uz": "⚡ Tezkor (3 ta)", "name_ru": "⚡ Скорость (3)", "name_en": "⚡ Speed (3)", "coins": 200},
    "streak_3": {"name_uz": "🔥 Seriya 3", "name_ru": "🔥 Серия 3", "name_en": "🔥 Streak 3", "coins": 150},
    "streak_5": {"name_uz": "🔥🔥 Seriya 5", "name_ru": "🔥🔥 Серия 5", "name_en": "🔥🔥 Streak 5", "coins": 300},
    "bot_killer": {"name_uz": "🤖 Bot o'ldirgich", "name_ru": "🤖 Убийца ботов", "name_en": "🤖 Bot Killer", "coins": 100},
}

MESSAGES = {
    "uz": {
        "choose_language": "🌍 Tilni tanlang:",
        "subscribe": "📢 Botdan foydalanish uchun kanalga a'zo bo'ling:",
        "not_subscribed": "❌ Siz hali kanalga a'zo emassiz!",
        "subscribed": "✅ Tabriklaymiz! Endi botdan foydalanishingiz mumkin.",
        "main_menu": "🏠 <b>Asosiy Menyu</b>\n\n👤 {name}\n💰 Coins: <b>{coins}</b>\n🏆 Rating: <b>{rating}</b>\n🔥 Streak: <b>{streak}</b>\n📊 O'yinlar: <b>{wins}/{games}</b> ({win_rate:.1f}%)",
        "choose_mode": "🎮 <b>O'yin turini tanlang:</b>\n\n🤖 <b>Bot bilan</b> - sun'iy intellekt bilan\n👥 <b>Do'st bilan</b> - havolani ulashing",
        "choose_difficulty": "📊 <b>Qiyinlik darajasini tanlang:</b>\n\n🟢 <b>Oson</b> - 3 xonali\n🟡 <b>O'rtacha</b> - 4 xonali\n🔴 <b>Qiyin</b> - 5 xonali\n⚫ <b>Ekstremal</b> - 6 xonali",
        "game_created": "✅ <b>O'yin yaratildi!</b>\n\n🔗 Havolani do'stingizga yuboring:\n{invite_link}\n\n⏳ Raqib kutilmoqda...",
        "game_started": "🎮 <b>O'yin boshlandi!</b>\n\n👤 Raqib: <b>{opponent}</b>\n📊 Qiyinlik: <b>{difficulty}</b> xonali\n\n🔢 Maxfiy raqamingizni kiriting (takrorlanmasin!):",
        "secret_set": "✅ Maxfiy raqamingiz saqlandi! Raqibingizni kuting...",
        "your_turn": "🎯 <b>Sizning navbatingiz!</b>\n\n💡 Hintlar: {hints} ta\n🔄 Urinishlar: {attempts}\n\nTaxminingizni yuboring:",
        "opponent_turn": "⏳ Raqibingizning navbati. Kuting...",
        "result": "📊 <b>Natija:</b> <code>{guess}</code>\n\n🎯 {bulls} Bull | 🐄 {cows} Cow\n🔄 Urinish: {attempts}",
        "win": "🎉 <b>TABRIKLAYMIZ!</b> 🎉\n\nSiz <b>{attempts}</b> urinishda g'olib bo'ldingiz!\n🎯 Maxfiy: <code>{secret}</code>\n\n💰 +{coins} coins\n🏆 +{rating} rating\n{streak_msg}\n{achievements}",
        "lose": "😔 <b>Afsuski, yutqazdingiz!</b>\n\n🎯 Maxfiy: <code>{secret}</code>\n🏆 -{rating} rating",
        "invalid_number": "❌ Noto'g'ri! {length} xonali raqam kiriting (takrorlanmasin).",
        "not_your_turn": "❌ Sizning navbatingiz emas!",
        "surrender_confirm": "🏳️ Taslim bo'lmoqchimisiz?",
        "surrendered": "🏳️ Siz taslim bo'ldingiz.",
        "opponent_surrendered": "🎉 Raqibingiz taslim bo'ldi! Siz g'olib!",
        "game_not_found": "❌ O'yin topilmadi!",
        "already_in_game": "❌ Siz allaqachon o'yindasiz!",
        "leaderboard": "🏆 <b>TOP O'YINCHILAR</b>\n\n{players}\n\nSizning o'rningiz: <b>#{rank}</b>",
        "profile": "👤 <b>{name}</b>\n\n🆔 ID: <code>{user_id}</code>\n🏆 Rating: {rating} (#{rank})\n💰 Coins: {coins}\n🔥 Streak: {streak}\n\n📊 O'yinlar: {games}\n🏆 G'alabalar: {wins}\n📈 Foiz: {win_rate:.1f}%\n\n🏅 Yutuqlar: {achievement_count}/{total_achievements}",
        "daily_bonus": "🎁 <b>Kunlik bonus!</b>\n\nSiz <b>{coins}</b> coin oldingiz!\n🔥 Streak: {streak} kun",
        "daily_already": "❌ Bugun bonusni oldingiz!\n\nKeyingi: {next_time}",
        
        "btn_new_game": "🎮 Yangi o'yin",
        "btn_vs_bot": "🤖 Bot bilan",
        "btn_vs_player": "👥 Do'st bilan",
        "btn_leaderboard": "🏆 Reytinglar",
        "btn_profile": "👤 Profil",
        "btn_daily": "🎁 Bonus",
        "btn_settings": "⚙️ Sozlamalar",
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
        "subscribe": "📢 Подпишитесь на канал:",
        "not_subscribed": "❌ Вы не подписаны!",
        "subscribed": "✅ Отлично! Теперь можете пользоваться ботом.",
        "main_menu": "🏠 <b>Главное меню</b>\n\n👤 {name}\n💰 Монеты: <b>{coins}</b>\n🏆 Рейтинг: <b>{rating}</b>\n🔥 Серия: <b>{streak}</b>\n📊 Игры: <b>{wins}/{games}</b> ({win_rate:.1f}%)",
        "choose_mode": "🎮 <b>Выберите режим:</b>\n\n🤖 <b>Против бота</b>\n👥 <b>С другом</b>",
        "choose_difficulty": "📊 <b>Сложность:</b>\n\n🟢 <b>Легко</b> - 3 цифры\n🟡 <b>Средне</b> - 4 цифры\n🔴 <b>Сложно</b> - 5 цифр\n⚫ <b>Экстрим</b> - 6 цифр",
        "game_created": "✅ <b>Игра создана!</b>\n\n🔗 Отправьте ссылку другу:\n{invite_link}\n\n⏳ Ожидание...",
        "game_started": "🎮 <b>Игра началась!</b>\n\n👤 Противник: <b>{opponent}</b>\n📊 Сложность: <b>{difficulty}</b>\n\n🔢 Введите секретное число:",
        "secret_set": "✅ Число сохранено! Ожидайте...",
        "your_turn": "🎯 <b>Ваш ход!</b>\n\n💡 Подсказок: {hints}\n🔄 Попыток: {attempts}\n\nВаша догадка:",
        "opponent_turn": "⏳ Ход противника...",
        "result": "📊 <b>Результат:</b> <code>{guess}</code>\n\n🎯 {bulls} Bull | 🐄 {cows} Cow\n🔄 Попытка: {attempts}",
        "win": "🎉 <b>ПОЗДРАВЛЯЕМ!</b> 🎉\n\nВы выиграли за <b>{attempts}</b> попыток!\n🎯 Секрет: <code>{secret}</code>\n\n💰 +{coins} монет\n🏆 +{rating} рейтинга\n{streak_msg}\n{achievements}",
        "lose": "😔 <b>Вы проиграли!</b>\n\n🎯 Секрет: <code>{secret}</code>\n🏆 -{rating} рейтинга",
        "invalid_number": "❌ Неверно! Введите {length}-значное число без повторов.",
        "not_your_turn": "❌ Не ваш ход!",
        "surrender_confirm": "🏳️ Сдаться?",
        "surrendered": "🏳️ Вы сдались.",
        "opponent_surrendered": "🎉 Противник сдался! Победа!",
        "game_not_found": "❌ Игра не найдена!",
        "already_in_game": "❌ Вы уже в игре!",
        "leaderboard": "🏆 <b>ТОП ИГРОКОВ</b>\n\n{players}\n\nВаше место: <b>#{rank}</b>",
        "profile": "👤 <b>{name}</b>\n\n🆔 ID: <code>{user_id}</code>\n🏆 Рейтинг: {rating} (#{rank})\n💰 Монеты: {coins}\n🔥 Серия: {streak}\n\n📊 Игры: {games}\n🏆 Победы: {wins}\n📈 %: {win_rate:.1f}%\n\n🏅 Достижения: {achievement_count}/{total_achievements}",
        "daily_bonus": "🎁 <b>Ежедневный бонус!</b>\n\nВы получили <b>{coins}</b> монет!\n🔥 Серия: {streak} дней",
        "daily_already": "❌ Вы уже получили бонус!\n\nСледующий: {next_time}",
        
        "btn_new_game": "🎮 Новая игра",
        "btn_vs_bot": "🤖 Против бота",
        "btn_vs_player": "👥 С другом",
        "btn_leaderboard": "🏆 Рейтинг",
        "btn_profile": "👤 Профиль",
        "btn_daily": "🎁 Бонус",
        "btn_settings": "⚙️ Настройки",
        "btn_surrender": "🏳️ Сдаться",
        "btn_back": "🔙 Назад",
        "btn_yes": "✅ Да",
        "btn_no": "❌ Нет",
        "btn_subscribe": "📢 Перейти",
        "btn_check": "✅ Проверить",
        "btn_easy": "🟢 Легко (3)",
        "btn_medium": "🟡 Средне (4)",
        "btn_hard": "🔴 Сложно (5)",
        "btn_extreme": "⚫ Экстрим (6)",
    },
    "en": {
        "choose_language": "🌍 Choose a language:",
        "subscribe": "📢 Subscribe to the channel:",
        "not_subscribed": "❌ Not subscribed!",
        "subscribed": "✅ Great! You can now use the bot.",
        "main_menu": "🏠 <b>Main Menu</b>\n\n👤 {name}\n💰 Coins: <b>{coins}</b>\n🏆 Rating: <b>{rating}</b>\n🔥 Streak: <b>{streak}</b>\n📊 Games: <b>{wins}/{games}</b> ({win_rate:.1f}%)",
        "choose_mode": "🎮 <b>Choose mode:</b>\n\n🤖 <b>vs Bot</b>\n👥 <b>vs Friend</b>",
        "choose_difficulty": "📊 <b>Difficulty:</b>\n\n🟢 <b>Easy</b> - 3 digits\n🟡 <b>Medium</b> - 4 digits\n🔴 <b>Hard</b> - 5 digits\n⚫ <b>Extreme</b> - 6 digits",
        "game_created": "✅ <b>Game created!</b>\n\n🔗 Send link to friend:\n{invite_link}\n\n⏳ Waiting...",
        "game_started": "🎮 <b>Game started!</b>\n\n👤 Opponent: <b>{opponent}</b>\n📊 Difficulty: <b>{difficulty}</b>\n\n🔢 Enter secret number:",
        "secret_set": "✅ Number saved! Wait...",
        "your_turn": "🎯 <b>Your turn!</b>\n\n💡 Hints: {hints}\n🔄 Attempts: {attempts}\n\nYour guess:",
        "opponent_turn": "⏳ Opponent's turn...",
        "result": "📊 <b>Result:</b> <code>{guess}</code>\n\n🎯 {bulls} Bull | 🐄 {cows} Cow\n🔄 Attempt: {attempts}",
        "win": "🎉 <b>CONGRATULATIONS!</b> 🎉\n\nYou won in <b>{attempts}</b> attempts!\n🎯 Secret: <code>{secret}</code>\n\n💰 +{coins} coins\n🏆 +{rating} rating\n{streak_msg}\n{achievements}",
        "lose": "😔 <b>You lost!</b>\n\n🎯 Secret: <code>{secret}</code>\n🏆 -{rating} rating",
        "invalid_number": "❌ Invalid! Enter {length}-digit number (no repeats).",
        "not_your_turn": "❌ Not your turn!",
        "surrender_confirm": "🏳️ Surrender?",
        "surrendered": "🏳️ You surrendered.",
        "opponent_surrendered": "🎉 Opponent surrendered! Victory!",
        "game_not_found": "❌ Game not found!",
        "already_in_game": "❌ Already in game!",
        "leaderboard": "🏆 <b>TOP PLAYERS</b>\n\n{players}\n\nYour rank: <b>#{rank}</b>",
        "profile": "👤 <b>{name}</b>\n\n🆔 ID: <code>{user_id}</code>\n🏆 Rating: {rating} (#{rank})\n💰 Coins: {coins}\n🔥 Streak: {streak}\n\n📊 Games: {games}\n🏆 Wins: {wins}\n📈 %: {win_rate:.1f}%\n\n🏅 Achievements: {achievement_count}/{total_achievements}",
        "daily_bonus": "🎁 <b>Daily bonus!</b>\n\nYou got <b>{coins}</b> coins!\n🔥 Streak: {streak} days",
        "daily_already": "❌ Already claimed!\n\nNext: {next_time}",
        
        "btn_new_game": "🎮 New Game",
        "btn_vs_bot": "🤖 vs Bot",
        "btn_vs_player": "👥 vs Friend",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_profile": "👤 Profile",
        "btn_daily": "🎁 Bonus",
        "btn_settings": "⚙️ Settings",
        "btn_surrender": "🏳️ Surrender",
        "btn_back": "🔙 Back",
        "btn_yes": "✅ Yes",
        "btn_no": "❌ No",
        "btn_subscribe": "📢 Go",
        "btn_check": "✅ Check",
        "btn_easy": "🟢 Easy (3)",
        "btn_medium": "🟡 Medium (4)",
        "btn_hard": "🔴 Hard (5)",
        "btn_extreme": "⚫ Extreme (6)",
    }, # Fallback to Uzbek
}
MESSAGES["kk"] = MESSAGES["uz"].copy()

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    """MongoDB database with error handling."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.connected = False
        
    async def connect(self):
        """Connect to MongoDB with retry logic."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"📡 Connecting to MongoDB (attempt {attempt + 1}/{max_retries})...")
                
                self.client = AsyncIOMotorClient(
                    MONGODB_URI,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                )
                
                self.db = self.client[DB_NAME]
                self.players = self.db.players
                self.games = self.db.games
                
                # Test connection
                await self.client.admin.command('ping')
                
                # Create indexes
                await self.create_indexes()
                
                self.connected = True
                logger.info("✅ MongoDB connected successfully!")
                return
                
            except Exception as e:
                logger.error(f"❌ MongoDB connection error (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.warning("⚠️ MongoDB unavailable. Using in-memory storage.")
                    self.connected = False
                    # Initialize in-memory fallback
                    self._init_memory_storage()
    
    def _init_memory_storage(self):
        """Initialize in-memory storage as fallback."""
        self.memory_players = {}
        self.memory_games = {}
        logger.info("💾 In-memory storage initialized")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")
    
    async def create_indexes(self):
        """Create indexes."""
        try:
            await self.players.create_index("user_id", unique=True)
            await self.players.create_index([("rating", -1)])
            await self.games.create_index("game_id", unique=True)
            await self.games.create_index([("is_finished", 1)])
            logger.info("✅ Indexes created")
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    # Players (with fallback)
    async def get_player(self, user_id: int) -> Optional[Dict]:
        if not self.connected:
            return self.memory_players.get(user_id)
        try:
            return await self.players.find_one({"user_id": user_id})
        except:
            return self.memory_players.get(user_id)
    
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
            "achievements": [],
            "last_daily": None,
            "created_at": datetime.utcnow()
        }
        
        if not self.connected:
            self.memory_players[user_id] = player
        else:
            try:
                await self.players.insert_one(player)
            except:
                self.memory_players[user_id] = player
        
        return player
    
    async def update_player(self, user_id: int, data: Dict) -> bool:
        if not self.connected:
            if user_id in self.memory_players:
                self.memory_players[user_id].update(data)
                return True
            return False
        
        try:
            result = await self.players.update_one({"user_id": user_id}, {"$set": data})
            return result.modified_count > 0
        except:
            if user_id in self.memory_players:
                self.memory_players[user_id].update(data)
                return True
            return False
    
    async def increment_stats(self, user_id: int, increments: Dict) -> bool:
        if not self.connected:
            if user_id in self.memory_players:
                for key, val in increments.items():
                    self.memory_players[user_id][key] = self.memory_players[user_id].get(key, 0) + val
                return True
            return False
        
        try:
            result = await self.players.update_one({"user_id": user_id}, {"$inc": increments})
            return result.modified_count > 0
        except:
            if user_id in self.memory_players:
                for key, val in increments.items():
                    self.memory_players[user_id][key] = self.memory_players[user_id].get(key, 0) + val
                return True
            return False
    
    async def add_achievement(self, user_id: int, achievement: str) -> bool:
        if not self.connected:
            if user_id in self.memory_players:
                if achievement not in self.memory_players[user_id]["achievements"]:
                    self.memory_players[user_id]["achievements"].append(achievement)
                return True
            return False
        
        try:
            result = await self.players.update_one(
                {"user_id": user_id},
                {"$addToSet": {"achievements": achievement}}
            )
            return result.modified_count > 0
        except:
            if user_id in self.memory_players:
                if achievement not in self.memory_players[user_id]["achievements"]:
                    self.memory_players[user_id]["achievements"].append(achievement)
                return True
            return False
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        if not self.connected:
            sorted_players = sorted(
                self.memory_players.values(),
                key=lambda p: p.get("rating", 0),
                reverse=True
            )
            return sorted_players[:limit]
        
        try:
            cursor = self.players.find().sort("rating", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except:
            sorted_players = sorted(
                self.memory_players.values(),
                key=lambda p: p.get("rating", 0),
                reverse=True
            )
            return sorted_players[:limit]
    
    async def get_rank(self, user_id: int) -> int:
        player = await self.get_player(user_id)
        if not player:
            return 0
        
        if not self.connected:
            count = sum(1 for p in self.memory_players.values() if p.get("rating", 0) > player.get("rating", 0))
            return count + 1
        
        try:
            count = await self.players.count_documents({"rating": {"$gt": player["rating"]}})
            return count + 1
        except:
            count = sum(1 for p in self.memory_players.values() if p.get("rating", 0) > player.get("rating", 0))
            return count + 1
    
    # Games
    async def create_game(self, game_data: Dict) -> str:
        game_data["created_at"] = datetime.utcnow()
        
        if not self.connected:
            self.memory_games[game_data["game_id"]] = game_data
        else:
            try:
                await self.games.insert_one(game_data)
            except:
                self.memory_games[game_data["game_id"]] = game_data
        
        return game_data["game_id"]
    
    async def get_game(self, game_id: str) -> Optional[Dict]:
        if not self.connected:
            return self.memory_games.get(game_id)
        
        try:
            return await self.games.find_one({"game_id": game_id})
        except:
            return self.memory_games.get(game_id)
    
    async def get_active_game(self, user_id: int) -> Optional[Dict]:
        if not self.connected:
            for game in self.memory_games.values():
                if not game.get("is_finished", False):
                    if game.get("player1_id") == user_id or game.get("player2_id") == user_id:
                        return game
            return None
        
        try:
            return await self.games.find_one({
                "$or": [{"player1_id": user_id}, {"player2_id": user_id}],
                "is_finished": False
            })
        except:
            for game in self.memory_games.values():
                if not game.get("is_finished", False):
                    if game.get("player1_id") == user_id or game.get("player2_id") == user_id:
                        return game
            return None
    
    async def update_game(self, game_id: str, data: Dict) -> bool:
        if not self.connected:
            if game_id in self.memory_games:
                self.memory_games[game_id].update(data)
                return True
            return False
        
        try:
            result = await self.games.update_one({"game_id": game_id}, {"$set": data})
            return result.modified_count > 0
        except:
            if game_id in self.memory_games:
                self.memory_games[game_id].update(data)
                return True
            return False
    
    async def add_move(self, game_id: str, move: Dict) -> bool:
        if not self.connected:
            if game_id in self.memory_games:
                if "history" not in self.memory_games[game_id]:
                    self.memory_games[game_id]["history"] = []
                self.memory_games[game_id]["history"].append(move)
                return True
            return False
        
        try:
            result = await self.games.update_one(
                {"game_id": game_id},
                {"$push": {"history": move}}
            )
            return result.modified_count > 0
        except:
            if game_id in self.memory_games:
                if "history" not in self.memory_games[game_id]:
                    self.memory_games[game_id]["history"] = []
                self.memory_games[game_id]["history"].append(move)
                return True
            return False

db = Database()

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def get_text(lang: str, key: str, **kwargs) -> str:
    text = MESSAGES.get(lang, MESSAGES["uz"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

def get_button_text(lang: str, key: str, **kwargs) -> str:
    return get_text(lang, f"btn_{key}", **kwargs)

def generate_secret(length: int) -> str:
    digits = list("0123456789")
    random.shuffle(digits)
    if digits[0] == "0":
        for i in range(1, len(digits)):
            if digits[i] != "0":
                digits[0], digits[i] = digits[i], digits[0]
                break
    return "".join(digits[:length])

def validate_number(text: str, length: int) -> bool:
    if len(text) != length or not text.isdigit():
        return False
    return len(set(text)) == length and text[0] != "0"

def calculate_bulls_cows(secret: str, guess: str) -> Tuple[int, int]:
    bulls = sum(s == g for s, g in zip(secret, guess))
    cows = sum(min(secret.count(d), guess.count(d)) for d in set(guess)) - bulls
    return bulls, cows

def calculate_rating_change(winner_rating: int, loser_rating: int) -> int:
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
    new_achievements = []
    current = set(player.get("achievements", []))
    
    if "first_win" not in current and player["games_won"] == 0:
        new_achievements.append("first_win")
    
    if "speed_3" not in current and attempts <= 3:
        new_achievements.append("speed_3")
    
    if "streak_3" not in current and player["current_streak"] + 1 >= 3:
        new_achievements.append("streak_3")
    
    if "streak_5" not in current and player["current_streak"] + 1 >= 5:
        new_achievements.append("streak_5")
    
    if "bot_killer" not in current and game.get("mode") == GameMode.VS_BOT.value:
        new_achievements.append("bot_killer")
    
    return new_achievements

# ═══════════════════════════════════════════════════════════════════════════════
# AI PLAYER
# ═══════════════════════════════════════════════════════════════════════════════

class AIPlayer:
    def __init__(self, difficulty: int):
        self.difficulty = difficulty
        self.possible = self._generate_all()
    
    def _generate_all(self) -> List[str]:
        from itertools import permutations
        all_nums = []
        for perm in permutations("0123456789", self.difficulty):
            if perm[0] != "0":
                all_nums.append("".join(perm))
        return all_nums
    
    def make_guess(self) -> str:
        if self.possible:
            return random.choice(self.possible)
        return generate_secret(self.difficulty)
    
    def update(self, guess: str, bulls: int, cows: int):
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
            InlineKeyboardButton(text=get_button_text(lang, "settings"), callback_data="settings")
        ]
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

def get_game_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button_text(lang, "surrender"), callback_data="surrender")]
    ])

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
    user_id = message.from_user.id
    player = await db.get_player(user_id)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("invite_"):
        await state.update_data(pending_invite=args[1])
    
    if not player:
        await state.set_state(GameStates.choosing_language)
        await message.answer(
            "🌍 Tilni tanlang / Выберите язык / Choose language:",
            reply_markup=get_language_keyboard()
        )
        return
    
    lang = player["language"]
    
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
    
    await show_main_menu(message, player)



@router.callback_query(F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_")[1]
    user = callback.from_user
    
    player = await db.create_player(user.id, user.username or "", user.first_name or "", lang_code)
    
    await callback.answer()
    await state.set_state(GameStates.main_menu)
    
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
    await db.connect()
    logger.info("🚀 Bot started!")

async def on_shutdown(bot: Bot):
    await db.disconnect()
    logger.info("👋 Bot stopped!")

async def main():
    # Fixed: Use DefaultBotProperties instead of parse_mode parameter
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    logger.info("🎮 Starting bot polling...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
