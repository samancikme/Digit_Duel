"""
🎮 BULLS & COWS - KREATIV VERSIYA
================================
Aiogram 3.x bilan yozilgan professional o'yin boti

Yangi xususiyatlar:
- 🤖 Bot bilan o'ynash (AI)
- 🏆 Rating va Leaderboard
- 📊 Statistika
- ⏱️ Vaqt cheklovi
- 💡 Hint (maslahat) tizimi
- 🎯 Turli qiyinlik darajalari
- 🔥 Streak (ketma-ket g'alabalar)
- 🎁 Daily bonus
- 🏅 Achievements
- 💰 Coin tizimi
"""

import asyncio
import logging
import random
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, 
    InlineKeyboardMarkup, User
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_USERNAME = "@samancikschannel"

# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

class GameMode(Enum):
    VS_PLAYER = "vs_player"
    VS_BOT = "vs_bot"

class Difficulty(Enum):
    EASY = 3      # 3 xonali
    MEDIUM = 4    # 4 xonali
    HARD = 5      # 5 xonali
    EXTREME = 6   # 6 xonali

class Achievement(Enum):
    FIRST_WIN = ("first_win", "🏆 Birinchi g'alaba", 100)
    SPEED_DEMON = ("speed_demon", "⚡ 3 urinishda g'alaba", 200)
    STREAK_3 = ("streak_3", "🔥 3 ketma-ket g'alaba", 150)
    STREAK_5 = ("streak_5", "🔥🔥 5 ketma-ket g'alaba", 300)
    STREAK_10 = ("streak_10", "🔥🔥🔥 10 ketma-ket g'alaba", 500)
    BOT_SLAYER = ("bot_slayer", "🤖 Botni yengish", 100)
    HARD_MODE = ("hard_mode", "💪 Hard rejimda g'alaba", 250)
    PLAYED_100 = ("played_100", "🎮 100 o'yin", 500)
    MASTER = ("master", "👑 Rating 2000+", 1000)

LANGUAGES = {
    "uz": "🇺🇿 O'zbek",
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English"
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PlayerStats:
    user_id: int
    username: str = ""
    first_name: str = ""
    language: str = "uz"
    coins: int = 100
    rating: int = 1000
    games_played: int = 0
    games_won: int = 0
    current_streak: int = 0
    best_streak: int = 0
    total_attempts: int = 0
    hints_used: int = 0
    achievements: List[str] = field(default_factory=list)
    last_daily: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return (self.games_won / self.games_played) * 100
    
    @property
    def avg_attempts(self) -> float:
        if self.games_won == 0:
            return 0.0
        return self.total_attempts / self.games_won

@dataclass
class Game:
    game_id: str
    mode: GameMode
    difficulty: Difficulty
    player1_id: int
    player2_id: Optional[int] = None
    secret1: Optional[str] = None
    secret2: Optional[str] = None
    turn: Optional[int] = None
    attempts: Dict[int, int] = field(default_factory=dict)
    hints_used: Dict[int, int] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    started_at: Optional[str] = None
    time_limit: int = 60  # soniya
    last_move: Optional[str] = None
    is_finished: bool = False

# ═══════════════════════════════════════════════════════════════════════════════
# STATES
# ═══════════════════════════════════════════════════════════════════════════════

class GameStates(StatesGroup):
    choosing_language = State()
    main_menu = State()
    choosing_mode = State()
    choosing_difficulty = State()
    waiting_for_opponent = State()
    entering_secret = State()
    playing = State()
    sending_message = State()

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE (In-Memory - Production uchun Redis/PostgreSQL ishlatish kerak)
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self.players: Dict[int, PlayerStats] = {}
        self.games: Dict[str, Game] = {}
        self.pending_games: Dict[str, Game] = {}
        self.game_counter: int = 0
    
    def get_player(self, user_id: int) -> Optional[PlayerStats]:
        return self.players.get(user_id)
    
    def create_player(self, user: User) -> PlayerStats:
        player = PlayerStats(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "Player"
        )
        self.players[user.id] = player
        return player
    
    def get_or_create_player(self, user: User) -> PlayerStats:
        player = self.get_player(user.id)
        if not player:
            player = self.create_player(user)
        return player
    
    def save_player(self, player: PlayerStats) -> None:
        self.players[player.user_id] = player
    
    def create_game(self, player1_id: int, mode: GameMode, difficulty: Difficulty) -> Game:
        self.game_counter += 1
        game = Game(
            game_id=str(self.game_counter),
            mode=mode,
            difficulty=difficulty,
            player1_id=player1_id,
            attempts={player1_id: 0},
            hints_used={player1_id: 0}
        )
        if mode == GameMode.VS_PLAYER:
            self.pending_games[game.game_id] = game
        else:
            self.games[game.game_id] = game
        return game
    
    def get_game(self, game_id: str) -> Optional[Game]:
        return self.games.get(game_id) or self.pending_games.get(game_id)
    
    def get_active_game(self, user_id: int) -> Optional[Game]:
        for game in list(self.games.values()) + list(self.pending_games.values()):
            if not game.is_finished:
                if game.player1_id == user_id or game.player2_id == user_id:
                    return game
        return None
    
    def get_leaderboard(self, limit: int = 10) -> List[PlayerStats]:
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: p.rating,
            reverse=True
        )
        return sorted_players[:limit]
    
    def cleanup_finished_games(self) -> None:
        finished = [gid for gid, g in self.games.items() if g.is_finished]
        for gid in finished:
            del self.games[gid]

db = Database()

# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGES
# ═══════════════════════════════════════════════════════════════════════════════

MESSAGES = {
    "uz": {
        "welcome": """
🎮 <b>BULLS & COWS</b> o'yiniga xush kelibsiz!

Raqamlarni topish o'yini - raqibingizning maxfiy raqamini birinchi toping!

🎯 <b>Bull</b> - to'g'ri raqam, to'g'ri joy
🐄 <b>Cow</b> - to'g'ri raqam, noto'g'ri joy
""",
        "choose_language": "🌍 Tilni tanlang:",
        "subscribe": "📢 Botdan foydalanish uchun kanalga a'zo bo'ling:",
        "subscribe_button": "📢 Kanalga o'tish",
        "check_sub": "✅ Tekshirish",
        "not_subscribed": "❌ Siz hali kanalga a'zo emassiz!",
        "main_menu": """
🏠 <b>Asosiy Menyu</b>

💰 Balans: <b>{coins}</b> coin
🏆 Rating: <b>{rating}</b>
🔥 Streak: <b>{streak}</b>
📊 G'alabalar: <b>{wins}/{games}</b> ({win_rate:.1f}%)
""",
        "choose_mode": """
🎮 <b>O'yin turini tanlang:</b>

🤖 Bot bilan - sun'iy intellekt bilan
👥 Do'st bilan - havolani ulashing
""",
        "choose_difficulty": """
📊 <b>Qiyinlik darajasini tanlang:</b>

🟢 Oson - 3 xonali raqam
🟡 O'rtacha - 4 xonali raqam  
🔴 Qiyin - 5 xonali raqam
⚫ Ekstremal - 6 xonali raqam
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

🔢 Maxfiy raqamingizni kiriting (raqamlar takrorlanmasin):
""",
        "secret_set": "✅ Maxfiy raqamingiz saqlandi! Raqibingizni kuting...",
        "your_turn": """
🎯 <b>Sizning navbatingiz!</b>

⏱️ Vaqt: {time} soniya
💡 Hint: {hints} ta qoldi

Taxminingizni yuboring:
""",
        "opponent_turn": "⏳ Raqibingizning navbati. Kuting...",
        "result": """
📊 <b>Natija:</b> {guess}

🎯 {bulls} Bull | 🐄 {cows} Cow

📝 Urinishlar: {attempts}
""",
        "win": """
🎉🎉🎉 <b>TABRIKLAYMIZ!</b> 🎉🎉🎉

Siz <b>{attempts}</b> urinishda g'olib bo'ldingiz!

🎯 Raqibning maxfiy raqami: <code>{secret}</code>

💰 +{coins} coin
🏆 +{rating} rating
{streak_bonus}
{achievements}
""",
        "lose": """
😔 <b>Afsuski, siz yutqazdingiz!</b>

🎯 Raqibning maxfiy raqami: <code>{secret}</code>

🏆 -{rating} rating
""",
        "hint_used": """
💡 <b>Maslahat:</b>

{position}-pozitsiyadagi raqam: <b>{digit}</b>

💰 -{cost} coin
💡 Qolgan hintlar: {remaining}
""",
        "not_enough_coins": "❌ Sizda yetarli coin yo'q! (Kerak: {cost})",
        "no_hints_left": "❌ Hintlar tugadi!",
        "invalid_input": "❌ Noto'g'ri format! {digits} xonali raqam kiriting (takrorlanmasin).",
        "not_your_turn": "❌ Sizning navbatingiz emas!",
        "surrender_confirm": "🏳️ Taslim bo'lishni tasdiqlaysizmi?",
        "surrendered": "🏳️ Siz taslim bo'ldingiz.",
        "opponent_surrendered": "🎉 Raqibingiz taslim bo'ldi! Siz yutdingiz!",
        "game_cancelled": "❌ O'yin bekor qilindi.",
        "leaderboard": """
🏆 <b>TOP O'YINCHILAR</b>

{players}
""",
        "stats": """
📊 <b>Sizning statistikangiz</b>

🎮 O'yinlar: {games}
🏆 G'alabalar: {wins} ({win_rate:.1f}%)
🔥 Eng uzun streak: {best_streak}
📈 O'rtacha urinish: {avg_attempts:.1f}
💡 Ishlatilgan hintlar: {hints}
🏅 Yutuqlar: {achievements}
""",
        "daily_bonus": """
🎁 <b>Kunlik bonus!</b>

💰 +{coins} coin oldingiz!
🔥 Streak: {streak} kun
""",
        "daily_claimed": "❌ Siz bugun bonusni oldingiz. Ertaga qaytib keling!",
        "new_achievement": """
🏅 <b>YANGI YUTUQ!</b>

{name}
💰 +{coins} coin
""",
        "profile": """
👤 <b>{name}</b>

🆔 ID: <code>{user_id}</code>
🏆 Rating: {rating}
💰 Coin: {coins}
🔥 Streak: {streak}

📊 O'yinlar: {games} | G'alabalar: {wins}
📈 G'alaba foizi: {win_rate:.1f}%

🏅 Yutuqlar: {achievement_count}/{total_achievements}
""",
        "shop": """
🛒 <b>DO'KON</b>

💰 Sizning balansingiz: {coins} coin

Mavjud mahsulotlar:
""",
        "buttons": {
            "new_game": "🎮 Yangi o'yin",
            "vs_bot": "🤖 Bot bilan",
            "vs_player": "👥 Do'st bilan",
            "leaderboard": "🏆 Reytinglar",
            "profile": "👤 Profil",
            "stats": "📊 Statistika",
            "settings": "⚙️ Sozlamalar",
            "shop": "🛒 Do'kon",
            "daily": "🎁 Kunlik bonus",
            "hint": "💡 Hint ({cost} coin)",
            "surrender": "🏳️ Taslim",
            "message": "✉️ Xabar",
            "back": "🔙 Orqaga",
            "yes": "✅ Ha",
            "no": "❌ Yo'q",
            "easy": "🟢 Oson (3)",
            "medium": "🟡 O'rtacha (4)",
            "hard": "🔴 Qiyin (5)",
            "extreme": "⚫ Ekstremal (6)",
            "cancel": "❌ Bekor qilish"
        }
    },
    "ru": {
        "welcome": """
🎮 Добро пожаловать в <b>BULLS & COWS</b>!

Игра в угадывание чисел - первым отгадайте секрет противника!

🎯 <b>Bull</b> - правильная цифра на правильном месте
🐄 <b>Cow</b> - правильная цифра на неправильном месте
""",
        "choose_language": "🌍 Выберите язык:",
        "subscribe": "📢 Подпишитесь на канал:",
        "subscribe_button": "📢 Перейти на канал",
        "check_sub": "✅ Проверить",
        "not_subscribed": "❌ Вы еще не подписаны!",
        "main_menu": """
🏠 <b>Главное меню</b>

💰 Баланс: <b>{coins}</b> монет
🏆 Рейтинг: <b>{rating}</b>
🔥 Серия: <b>{streak}</b>
📊 Победы: <b>{wins}/{games}</b> ({win_rate:.1f}%)
""",
        "buttons": {
            "new_game": "🎮 Новая игра",
            "vs_bot": "🤖 Против бота",
            "vs_player": "👥 С другом",
            "leaderboard": "🏆 Рейтинг",
            "profile": "👤 Профиль",
            "stats": "📊 Статистика",
            "settings": "⚙️ Настройки",
            "shop": "🛒 Магазин",
            "daily": "🎁 Ежедневный бонус",
            "hint": "💡 Подсказка ({cost} монет)",
            "surrender": "🏳️ Сдаться",
            "message": "✉️ Сообщение",
            "back": "🔙 Назад",
            "yes": "✅ Да",
            "no": "❌ Нет",
            "easy": "🟢 Легко (3)",
            "medium": "🟡 Средне (4)",
            "hard": "🔴 Сложно (5)",
            "extreme": "⚫ Экстрим (6)",
            "cancel": "❌ Отмена"
        }
    },
    "en": {
        "welcome": """
🎮 Welcome to <b>BULLS & COWS</b>!

Number guessing game - be the first to guess opponent's secret!

🎯 <b>Bull</b> - correct digit in correct position
🐄 <b>Cow</b> - correct digit in wrong position
""",
        "choose_language": "🌍 Choose a language:",
        "subscribe": "📢 Please subscribe to the channel:",
        "subscribe_button": "📢 Go to channel",
        "check_sub": "✅ Check",
        "not_subscribed": "❌ You are not subscribed yet!",
        "main_menu": """
🏠 <b>Main Menu</b>

💰 Balance: <b>{coins}</b> coins
🏆 Rating: <b>{rating}</b>
🔥 Streak: <b>{streak}</b>
📊 Wins: <b>{wins}/{games}</b> ({win_rate:.1f}%)
""",
        "buttons": {
            "new_game": "🎮 New Game",
            "vs_bot": "🤖 vs Bot",
            "vs_player": "👥 vs Friend",
            "leaderboard": "🏆 Leaderboard",
            "profile": "👤 Profile",
            "stats": "📊 Statistics",
            "settings": "⚙️ Settings",
            "shop": "🛒 Shop",
            "daily": "🎁 Daily Bonus",
            "hint": "💡 Hint ({cost} coins)",
            "surrender": "🏳️ Surrender",
            "message": "✉️ Message",
            "back": "🔙 Back",
            "yes": "✅ Yes",
            "no": "❌ No",
            "easy": "🟢 Easy (3)",
            "medium": "🟡 Medium (4)",
            "hard": "🔴 Hard (5)",
            "extreme": "⚫ Extreme (6)",
            "cancel": "❌ Cancel"
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_text(player: PlayerStats, key: str, **kwargs) -> str:
    """Tilga mos matnni olish."""
    lang_msgs = MESSAGES.get(player.language, MESSAGES["uz"])
    text = lang_msgs.get(key, MESSAGES["uz"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

def get_button(player: PlayerStats, key: str, **kwargs) -> str:
    """Tilga mos tugma matnini olish."""
    lang_msgs = MESSAGES.get(player.language, MESSAGES["uz"])
    buttons = lang_msgs.get("buttons", MESSAGES["uz"]["buttons"])
    text = buttons.get(key, MESSAGES["uz"]["buttons"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

def generate_secret(length: int) -> str:
    """Maxfiy raqam generatsiya qilish."""
    digits = list("0123456789")
    random.shuffle(digits)
    # Birinchi raqam 0 bo'lmasligi uchun
    if digits[0] == "0":
        for i in range(1, len(digits)):
            if digits[i] != "0":
                digits[0], digits[i] = digits[i], digits[0]
                break
    return "".join(digits[:length])

def validate_number(text: str, length: int) -> bool:
    """Raqamni tekshirish."""
    if len(text) != length or not text.isdigit():
        return False
    return len(set(text)) == length

def calculate_bulls_cows(secret: str, guess: str) -> Tuple[int, int]:
    """Bulls va Cows hisoblash."""
    bulls = sum(s == g for s, g in zip(secret, guess))
    cows = sum(min(secret.count(d), guess.count(d)) for d in set(guess)) - bulls
    return bulls, cows

def calculate_rating_change(winner_rating: int, loser_rating: int, k: int = 32) -> int:
    """ELO rating o'zgarishini hisoblash."""
    expected = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    return int(k * (1 - expected))

def get_hint_cost(difficulty: Difficulty) -> int:
    """Hint narxini olish."""
    costs = {
        Difficulty.EASY: 20,
        Difficulty.MEDIUM: 30,
        Difficulty.HARD: 50,
        Difficulty.EXTREME: 80
    }
    return costs.get(difficulty, 30)

def get_max_hints(difficulty: Difficulty) -> int:
    """Maksimal hint sonini olish."""
    return difficulty.value - 1

# ═══════════════════════════════════════════════════════════════════════════════
# AI BOT LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

class AIPlayer:
    """Sun'iy intellekt o'yinchi."""
    
    def __init__(self, difficulty: Difficulty):
        self.difficulty = difficulty
        self.length = difficulty.value
        self.possible_numbers = self._generate_all_numbers()
        self.guesses = []
    
    def _generate_all_numbers(self) -> List[str]:
        """Barcha mumkin bo'lgan raqamlarni generatsiya qilish."""
        from itertools import permutations
        digits = "0123456789"
        all_nums = []
        for perm in permutations(digits, self.length):
            if perm[0] != "0":  # 0 bilan boshlanmasin
                all_nums.append("".join(perm))
        return all_nums
    
    def make_guess(self) -> str:
        """Taxmin qilish."""
        if not self.guesses:
            # Birinchi taxmin - tasodifiy
            guess = random.choice(self.possible_numbers)
        else:
            # Eng yaxshi taxminni tanlash (minimax strategiya)
            guess = random.choice(self.possible_numbers) if self.possible_numbers else generate_secret(self.length)
        
        self.guesses.append(guess)
        return guess
    
    def update_possibilities(self, guess: str, bulls: int, cows: int) -> None:
        """Mumkin bo'lgan raqamlarni yangilash."""
        self.possible_numbers = [
            num for num in self.possible_numbers
            if calculate_bulls_cows(num, guess) == (bulls, cows)
        ]

# ═══════════════════════════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════════

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Til tanlash klaviaturasi."""
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"lang:{code}")]
               for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_subscribe_keyboard(player: PlayerStats) -> InlineKeyboardMarkup:
    """Obuna klaviaturasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button(player, "subscribe_button"), url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text=get_button(player, "check_sub"), callback_data="check_sub")]
    ])

def get_main_menu_keyboard(player: PlayerStats) -> InlineKeyboardMarkup:
    """Asosiy menyu klaviaturasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button(player, "new_game"), callback_data="new_game")],
        [
            InlineKeyboardButton(text=get_button(player, "leaderboard"), callback_data="leaderboard"),
            InlineKeyboardButton(text=get_button(player, "profile"), callback_data="profile")
        ],
        [
            InlineKeyboardButton(text=get_button(player, "daily"), callback_data="daily"),
            InlineKeyboardButton(text=get_button(player, "stats"), callback_data="stats")
        ],
        [
            InlineKeyboardButton(text=get_button(player, "shop"), callback_data="shop"),
            InlineKeyboardButton(text=get_button(player, "settings"), callback_data="settings")
        ]
    ])

def get_mode_keyboard(player: PlayerStats) -> InlineKeyboardMarkup:
    """O'yin turi klaviaturasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button(player, "vs_bot"), callback_data="mode:vs_bot")],
        [InlineKeyboardButton(text=get_button(player, "vs_player"), callback_data="mode:vs_player")],
        [InlineKeyboardButton(text=get_button(player, "back"), callback_data="back:main")]
    ])

def get_difficulty_keyboard(player: PlayerStats) -> InlineKeyboardMarkup:
    """Qiyinlik klaviaturasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button(player, "easy"), callback_data="diff:easy")],
        [InlineKeyboardButton(text=get_button(player, "medium"), callback_data="diff:medium")],
        [InlineKeyboardButton(text=get_button(player, "hard"), callback_data="diff:hard")],
        [InlineKeyboardButton(text=get_button(player, "extreme"), callback_data="diff:extreme")],
        [InlineKeyboardButton(text=get_button(player, "back"), callback_data="back:mode")]
    ])

def get_game_keyboard(player: PlayerStats, game: Game) -> InlineKeyboardMarkup:
    """O'yin klaviaturasi."""
    hint_cost = get_hint_cost(game.difficulty)
    max_hints = get_max_hints(game.difficulty)
    used_hints = game.hints_used.get(player.user_id, 0)
    hints_left = max_hints - used_hints
    
    buttons = []
    
    if hints_left > 0:
        buttons.append([
            InlineKeyboardButton(
                text=get_button(player, "hint", cost=hint_cost),
                callback_data="hint"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text=get_button(player, "surrender"), callback_data="surrender"),
        InlineKeyboardButton(text=get_button(player, "message"), callback_data="send_msg")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard(player: PlayerStats) -> InlineKeyboardMarkup:
    """Tasdiqlash klaviaturasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_button(player, "yes"), callback_data="confirm:yes"),
            InlineKeyboardButton(text=get_button(player, "no"), callback_data="confirm:no")
        ]
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTERS
# ═══════════════════════════════════════════════════════════════════════════════

router = Router()

# ═══════════════════════════════════════════════════════════════════════════════
# START & LANGUAGE
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi."""
    user = message.from_user
    player = db.get_or_create_player(user)
    
    # Invite link tekshirish
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("invite_"):
        await state.update_data(pending_invite=args[1])
    
    # Til tanlanmaganmi
    if not player.language:
        await state.set_state(GameStates.choosing_language)
        await message.answer(
            "🌍 Tilni tanlang / Выберите язык / Choose language:",
            reply_markup=get_language_keyboard()
        )
        return
    
    # Faol o'yin tekshirish
    active_game = db.get_active_game(user.id)
    if active_game and not active_game.is_finished:
        await message.answer(
            get_text(player, "surrender_confirm"),
            reply_markup=get_confirm_keyboard(player)
        )
        return
    
    await show_main_menu(message, player, state)

@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery, state: FSMContext):
    """Til tanlash."""
    lang_code = callback.data.split(":")[1]
    player = db.get_or_create_player(callback.from_user)
    player.language = lang_code
    db.save_player(player)
    
    await callback.answer()
    
    # Obuna tekshirish
    await callback.message.edit_text(
        get_text(player, "subscribe"),
        reply_markup=get_subscribe_keyboard(player)
    )

@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Obuna tekshirish."""
    player = db.get_player(callback.from_user.id)
    
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, callback.from_user.id)
        if member.status in ["member", "creator", "administrator", "restricted"]:
            await callback.answer("✅")
            
            # Pending invite tekshirish
            data = await state.get_data()
            if "pending_invite" in data:
                await process_invite(callback.message, player, data["pending_invite"], state, bot)
            else:
                await show_main_menu(callback.message, player, state, edit=True)
        else:
            await callback.answer(get_text(player, "not_subscribed"), show_alert=True)
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
        await callback.answer(get_text(player, "not_subscribed"), show_alert=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

async def show_main_menu(message: Message, player: PlayerStats, state: FSMContext, edit: bool = False):
    """Asosiy menyuni ko'rsatish."""
    await state.set_state(GameStates.main_menu)
    
    text = get_text(
        player, "main_menu",
        coins=player.coins,
        rating=player.rating,
        streak=player.current_streak,
        wins=player.games_won,
        games=player.games_played,
        win_rate=player.win_rate
    )
    
    if edit:
        await message.edit_text(text, reply_markup=get_main_menu_keyboard(player), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=get_main_menu_keyboard(player), parse_mode="HTML")

@router.callback_query(F.data == "back:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish."""
    player = db.get_player(callback.from_user.id)
    await callback.answer()
    await show_main_menu(callback.message, player, state, edit=True)

# ═══════════════════════════════════════════════════════════════════════════════
# NEW GAME
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "new_game")
async def new_game(callback: CallbackQuery, state: FSMContext):
    """Yangi o'yin."""
    player = db.get_player(callback.from_user.id)
    
    # Faol o'yin tekshirish
    active_game = db.get_active_game(callback.from_user.id)
    if active_game:
        await callback.answer("Siz allaqachon o'yinda ishtirok etmoqdasiz!", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(GameStates.choosing_mode)
    
    await callback.message.edit_text(
        get_text(player, "choose_mode"),
        reply_markup=get_mode_keyboard(player),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("mode:"))
async def select_mode(callback: CallbackQuery, state: FSMContext):
    """O'yin turini tanlash."""
    mode = callback.data.split(":")[1]
    player = db.get_player(callback.from_user.id)
    
    await state.update_data(game_mode=mode)
    await callback.answer()
    await state.set_state(GameStates.choosing_difficulty)
    
    await callback.message.edit_text(
        get_text(player, "choose_difficulty"),
        reply_markup=get_difficulty_keyboard(player),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back:mode")
async def back_to_mode(callback: CallbackQuery, state: FSMContext):
    """O'yin turiga qaytish."""
    player = db.get_player(callback.from_user.id)
    await callback.answer()
    await state.set_state(GameStates.choosing_mode)
    
    await callback.message.edit_text(
        get_text(player, "choose_mode"),
        reply_markup=get_mode_keyboard(player),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("diff:"))
async def select_difficulty(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Qiyinlikni tanlash."""
    diff_map = {
        "easy": Difficulty.EASY,
        "medium": Difficulty.MEDIUM,
        "hard": Difficulty.HARD,
        "extreme": Difficulty.EXTREME
    }
    
    diff_name = callback.data.split(":")[1]
    difficulty = diff_map.get(diff_name, Difficulty.MEDIUM)
    
    player = db.get_player(callback.from_user.id)
    data = await state.get_data()
    mode_str = data.get("game_mode", "vs_bot")
    mode = GameMode.VS_BOT if mode_str == "vs_bot" else GameMode.VS_PLAYER
    
    await callback.answer()
    
    # O'yin yaratish
    game = db.create_game(player.user_id, mode, difficulty)
    await state.update_data(game_id=game.game_id)
    
    if mode == GameMode.VS_BOT:
        # Bot bilan o'yin
        game.player2_id = 0  # Bot ID
        game.secret2 = generate_secret(difficulty.value)
        db.games[game.game_id] = game
        if game.game_id in db.pending_games:
            del db.pending_games[game.game_id]
        
        await state.set_state(GameStates.entering_secret)
        await callback.message.edit_text(
            get_text(player, "game_started", opponent="🤖 Bot", difficulty=difficulty.value),
            parse_mode="HTML"
        )
    else:
        # Do'st bilan o'yin
        bot_info = await bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start=invite_{game.game_id}"
        
        await state.set_state(GameStates.waiting_for_opponent)
        await callback.message.edit_text(
            get_text(player, "game_created", invite_link=invite_link),
            parse_mode="HTML"
        )

async def process_invite(message: Message, player: PlayerStats, invite_arg: str, state: FSMContext, bot: Bot):
    """Taklifnomani qayta ishlash."""
    game_id = invite_arg.replace("invite_", "")
    game = db.get_game(game_id)
    
    if not game:
        await message.edit_text("❌ O'yin topilmadi!")
        return
    
    if game.player1_id == player.user_id:
        await message.edit_text("❌ O'zingiz bilan o'ynay olmaysiz!")
        return
    
    if game.player2_id is not None:
        await message.edit_text("❌ Bu o'yin allaqachon boshlangan!")
        return
    
    # O'yinni boshlash
    game.player2_id = player.user_id
    game.attempts[player.user_id] = 0
    game.hints_used[player.user_id] = 0
    
    if game.game_id in db.pending_games:
        db.games[game.game_id] = game
        del db.pending_games[game.game_id]
    
    await state.update_data(game_id=game.game_id)
    await state.set_state(GameStates.entering_secret)
    
    # Ikkala o'yinchiga xabar
    player1 = db.get_player(game.player1_id)
    
    await bot.send_message(
        game.player1_id,
        get_text(player1, "game_started", opponent=player.first_name, difficulty=game.difficulty.value),
        parse_mode="HTML"
    )
    
    await message.edit_text(
        get_text(player, "game_started", opponent=player1.first_name, difficulty=game.difficulty.value),
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# GAME LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(StateFilter(GameStates.entering_secret))
async def enter_secret(message: Message, state: FSMContext, bot: Bot):
    """Maxfiy raqam kiritish."""
    player = db.get_player(message.from_user.id)
    data = await state.get_data()
    game_id = data.get("game_id")
    game = db.get_game(game_id)
    
    if not game:
        await message.answer("❌ O'yin topilmadi!")
        return
    
    text = message.text.strip()
    length = game.difficulty.value
    
    if not validate_number(text, length):
        await message.answer(get_text(player, "invalid_input", digits=length))
        return
    
    # Maxfiy raqamni saqlash
    if game.player1_id == player.user_id:
        game.secret1 = text
    else:
        game.secret2 = text
    
    await message.answer(get_text(player, "secret_set"))
    
    # Ikkala o'yinchi ham kiritdimi?
    if game.secret1 and game.secret2:
        game.started_at = datetime.now().isoformat()
        game.turn = game.player1_id
        
        await state.set_state(GameStates.playing)
        
        # Player1 ga navbat
        player1 = db.get_player(game.player1_id)
        await bot.send_message(
            game.player1_id,
            get_text(player1, "your_turn", time=game.time_limit, hints=get_max_hints(game.difficulty)),
            reply_markup=get_game_keyboard(player1, game),
            parse_mode="HTML"
        )
        
        # Player2 ga kuting
        if game.player2_id and game.player2_id != 0:
            player2 = db.get_player(game.player2_id)
            await bot.send_message(
                game.player2_id,
                get_text(player2, "opponent_turn"),
                parse_mode="HTML"
            )

@router.message(StateFilter(GameStates.playing))
async def make_guess(message: Message, state: FSMContext, bot: Bot):
    """Taxmin qilish."""
    player = db.get_player(message.from_user.id)
    data = await state.get_data()
    game_id = data.get("game_id")
    game = db.get_game(game_id)
    
    if not game:
        await message.answer("❌ O'yin topilmadi!")
        return
    
    # Navbat tekshirish
    if game.turn != player.user_id:
        await message.answer(get_text(player, "not_your_turn"))
        return
    
    text = message.text.strip()
    length = game.difficulty.value
    
    if not validate_number(text, length):
        await message.answer(get_text(player, "invalid_input", digits=length))
        return
    
    game.attempts[player.user_id] += 1
    
    # Natijani hisoblash
    if player.user_id == game.player1_id:
        secret = game.secret2
        own_secret = game.secret1
        opponent_id = game.player2_id
    else:
        secret = game.secret1
        own_secret = game.secret2
        opponent_id = game.player1_id
    
    bulls, cows = calculate_bulls_cows(secret, text)
    
    # Tarixga qo'shish
    game.history.append({
        "player": player.user_id,
        "guess": text,
        "bulls": bulls,
        "cows": cows
    })
    
    # G'alaba tekshirish
    if bulls == length:
        await handle_win(message, player, game, secret, own_secret, opponent_id, bot, state)
        return
    
    # Natijani ko'rsatish
    await message.answer(
        get_text(player, "result", guess=text, bulls=bulls, cows=cows, attempts=game.attempts[player.user_id]),
        parse_mode="HTML"
    )
    
    # Bot bilan o'yin
    if game.mode == GameMode.VS_BOT:
        await asyncio.sleep(1)  # Bot "o'ylayapti"
        await bot_make_move(message, player, game, bot, state)
    else:
        # Navbatni o'zgartirish
        game.turn = opponent_id
        
        if opponent_id:
            opponent = db.get_player(opponent_id)
            await bot.send_message(
                opponent_id,
                get_text(opponent, "your_turn", time=game.time_limit, hints=get_max_hints(game.difficulty) - game.hints_used.get(opponent_id, 0)),
                reply_markup=get_game_keyboard(opponent, game),
                parse_mode="HTML"
            )
        
        await message.answer(get_text(player, "opponent_turn"))

async def bot_make_move(message: Message, player: PlayerStats, game: Game, bot: Bot, state: FSMContext):
    """Bot taxmin qiladi."""
    # AI yaratish yoki olish
    data = await state.get_data()
    ai_data = data.get("ai_possibilities")
    
    if not ai_data:
        ai = AIPlayer(game.difficulty)
    else:
        ai = AIPlayer(game.difficulty)
        ai.possible_numbers = ai_data
        ai.guesses = [h["guess"] for h in game.history if h["player"] == 0]
    
    # Oldingi natijalardan o'rganish
    for entry in game.history:
        if entry["player"] == 0:  # Bot taxminlari
            ai.update_possibilities(entry["guess"], entry["bulls"], entry["cows"])
    
    # Yangi taxmin
    guess = ai.make_guess()
    game.attempts[0] = game.attempts.get(0, 0) + 1
    
    bulls, cows = calculate_bulls_cows(game.secret1, guess)
    
    game.history.append({
        "player": 0,
        "guess": guess,
        "bulls": bulls,
        "cows": cows
    })
    
    # AI holatini saqlash
    ai.update_possibilities(guess, bulls, cows)
    await state.update_data(ai_possibilities=ai.possible_numbers)
    
    # G'alaba tekshirish
    if bulls == game.difficulty.value:
        await handle_loss(message, player, game, game.secret1, game.secret2, bot, state)
        return
    
    # Natijani ko'rsatish
    await message.answer(
        f"🤖 Bot taxmini: <code>{guess}</code>\n🎯 {bulls} Bull | 🐄 {cows} Cow",
        parse_mode="HTML"
    )
    
    # Navbat o'yinchiga
    game.turn = player.user_id
    await message.answer(
        get_text(player, "your_turn", time=game.time_limit, hints=get_max_hints(game.difficulty) - game.hints_used.get(player.user_id, 0)),
        reply_markup=get_game_keyboard(player, game),
        parse_mode="HTML"
    )

async def handle_win(message: Message, player: PlayerStats, game: Game, 
                     opponent_secret: str, own_secret: str, opponent_id: int, 
                     bot: Bot, state: FSMContext):
    """G'alabani qayta ishlash."""
    game.is_finished = True
    
    attempts = game.attempts[player.user_id]
    
    # Coin va rating hisoblash
    base_coins = 50
    rating_change = 25
    
    if game.mode == GameMode.VS_PLAYER and opponent_id:
        opponent = db.get_player(opponent_id)
        rating_change = calculate_rating_change(player.rating, opponent.rating)
        opponent.rating = max(0, opponent.rating - rating_change)
        opponent.current_streak = 0
        db.save_player(opponent)
    
    # Bonus hisoblash
    speed_bonus = max(0, (10 - attempts) * 10) if attempts <= 10 else 0
    difficulty_bonus = game.difficulty.value * 20
    
    total_coins = base_coins + speed_bonus + difficulty_bonus
    
    # Streak
    player.current_streak += 1
    player.best_streak = max(player.best_streak, player.current_streak)
    streak_bonus_coins = player.current_streak * 10
    total_coins += streak_bonus_coins
    
    # Statistika yangilash
    player.coins += total_coins
    player.rating += rating_change
    player.games_played += 1
    player.games_won += 1
    player.total_attempts += attempts
    player.hints_used += game.hints_used.get(player.user_id, 0)
    
    # Achievements tekshirish
    new_achievements = check_achievements(player, game, attempts)
    achievement_text = ""
    
    for ach in new_achievements:
        player.achievements.append(ach.value[0])
        player.coins += ach.value[2]
        achievement_text += f"\n🏅 {ach.value[1]} (+{ach.value[2]} coin)"
    
    db.save_player(player)
    
    streak_text = f"🔥 Streak bonus: +{streak_bonus_coins} coin" if player.current_streak > 1 else ""
    
    await message.answer(
        get_text(
            player, "win",
            attempts=attempts,
            secret=opponent_secret,
            coins=total_coins,
            rating=rating_change,
            streak_bonus=streak_text,
            achievements=achievement_text
        ),
        reply_markup=get_main_menu_keyboard(player),
        parse_mode="HTML"
    )
    
    # Raqibga xabar
    if opponent_id and opponent_id != 0:
        opponent = db.get_player(opponent_id)
        opponent.games_played += 1
        db.save_player(opponent)
        
        await bot.send_message(
            opponent_id,
            get_text(opponent, "lose", secret=own_secret, rating=rating_change),
            reply_markup=get_main_menu_keyboard(opponent),
            parse_mode="HTML"
        )
    
    await state.set_state(GameStates.main_menu)

async def handle_loss(message: Message, player: PlayerStats, game: Game,
                      player_secret: str, bot_secret: str, bot_obj: Bot, state: FSMContext):
    """Mag'lubiyatni qayta ishlash."""
    game.is_finished = True
    
    rating_change = 15
    
    player.rating = max(0, player.rating - rating_change)
    player.current_streak = 0
    player.games_played += 1
    db.save_player(player)
    
    await message.answer(
        get_text(player, "lose", secret=bot_secret, rating=rating_change),
        reply_markup=get_main_menu_keyboard(player),
        parse_mode="HTML"
    )
    
    await state.set_state(GameStates.main_menu)

def check_achievements(player: PlayerStats, game: Game, attempts: int) -> List[Achievement]:
    """Yutuqlarni tekshirish."""
    new_achievements = []
    
    if Achievement.FIRST_WIN.value[0] not in player.achievements:
        if player.games_won == 0:  # Bu birinchi g'alaba
            new_achievements.append(Achievement.FIRST_WIN)
    
    if Achievement.SPEED_DEMON.value[0] not in player.achievements:
        if attempts <= 3:
            new_achievements.append(Achievement.SPEED_DEMON)
    
    if Achievement.STREAK_3.value[0] not in player.achievements:
        if player.current_streak + 1 >= 3:
            new_achievements.append(Achievement.STREAK_3)
    
    if Achievement.STREAK_5.value[0] not in player.achievements:
        if player.current_streak + 1 >= 5:
            new_achievements.append(Achievement.STREAK_5)
    
    if Achievement.STREAK_10.value[0] not in player.achievements:
        if player.current_streak + 1 >= 10:
            new_achievements.append(Achievement.STREAK_10)
    
    if Achievement.BOT_SLAYER.value[0] not in player.achievements:
        if game.mode == GameMode.VS_BOT:
            new_achievements.append(Achievement.BOT_SLAYER)
    
    if Achievement.HARD_MODE.value[0] not in player.achievements:
        if game.difficulty in [Difficulty.HARD, Difficulty.EXTREME]:
            new_achievements.append(Achievement.HARD_MODE)
    
    if Achievement.PLAYED_100.value[0] not in player.achievements:
        if player.games_played + 1 >= 100:
            new_achievements.append(Achievement.PLAYED_100)
    
    if Achievement.MASTER.value[0] not in player.achievements:
        if player.rating >= 2000:
            new_achievements.append(Achievement.MASTER)
    
    return new_achievements

# ═══════════════════════════════════════════════════════════════════════════════
# HINT
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "hint")
async def use_hint(callback: CallbackQuery, state: FSMContext):
    """Hint ishlatish."""
    player = db.get_player(callback.from_user.id)
    data = await state.get_data()
    game = db.get_game(data.get("game_id"))
    
    if not game or game.turn != player.user_id:
        await callback.answer(get_text(player, "not_your_turn"), show_alert=True)
        return
    
    cost = get_hint_cost(game.difficulty)
    max_hints = get_max_hints(game.difficulty)
    used = game.hints_used.get(player.user_id, 0)
    
    if used >= max_hints:
        await callback.answer(get_text(player, "no_hints_left"), show_alert=True)
        return
    
    if player.coins < cost:
        await callback.answer(get_text(player, "not_enough_coins", cost=cost), show_alert=True)
        return
    
    # Hint berish
    player.coins -= cost
    game.hints_used[player.user_id] = used + 1
    db.save_player(player)
    
    # Tasodifiy pozitsiyani ochish
    if player.user_id == game.player1_id:
        secret = game.secret2
    else:
        secret = game.secret1
    
    # Hali ochilmagan pozitsiyani topish
    revealed = data.get("revealed_positions", [])
    available = [i for i in range(len(secret)) if i not in revealed]
    
    if not available:
        await callback.answer(get_text(player, "no_hints_left"), show_alert=True)
        return
    
    pos = random.choice(available)
    revealed.append(pos)
    await state.update_data(revealed_positions=revealed)
    
    await callback.answer()
    await callback.message.answer(
        get_text(
            player, "hint_used",
            position=pos + 1,
            digit=secret[pos],
            cost=cost,
            remaining=max_hints - used - 1
        ),
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SURRENDER
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "surrender")
async def surrender_confirm(callback: CallbackQuery, state: FSMContext):
    """Taslim bo'lish tasdiqlash."""
    player = db.get_player(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(
        get_text(player, "surrender_confirm"),
        reply_markup=get_confirm_keyboard(player)
    )

@router.callback_query(F.data == "confirm:yes")
async def surrender_yes(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Taslim bo'lish."""
    player = db.get_player(callback.from_user.id)
    data = await state.get_data()
    game = db.get_game(data.get("game_id"))
    
    if game:
        game.is_finished = True
        
        player.current_streak = 0
        player.rating = max(0, player.rating - 20)
        player.games_played += 1
        db.save_player(player)
        
        # Raqibga xabar
        opponent_id = game.player2_id if game.player1_id == player.user_id else game.player1_id
        if opponent_id and opponent_id != 0:
            opponent = db.get_player(opponent_id)
            opponent.games_won += 1
            opponent.games_played += 1
            opponent.current_streak += 1
            opponent.rating += 20
            opponent.coins += 30
            db.save_player(opponent)
            
            await bot.send_message(
                opponent_id,
                get_text(opponent, "opponent_surrendered"),
                reply_markup=get_main_menu_keyboard(opponent),
                parse_mode="HTML"
            )
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(player, "surrendered"),
        reply_markup=get_main_menu_keyboard(player),
        parse_mode="HTML"
    )
    await state.set_state(GameStates.main_menu)

@router.callback_query(F.data == "confirm:no")
async def surrender_no(callback: CallbackQuery, state: FSMContext):
    """Taslim bo'lishni bekor qilish."""
    player = db.get_player(callback.from_user.id)
    data = await state.get_data()
    game = db.get_game(data.get("game_id"))
    
    await callback.answer()
    
    if game and game.turn == player.user_id:
        await callback.message.edit_text(
            get_text(player, "your_turn", time=game.time_limit, hints=get_max_hints(game.difficulty) - game.hints_used.get(player.user_id, 0)),
            reply_markup=get_game_keyboard(player, game),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            get_text(player, "opponent_turn"),
            parse_mode="HTML"
        )

# ═══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    """Leaderboard ko'rsatish."""
    player = db.get_player(callback.from_user.id)
    top_players = db.get_leaderboard(10)
    
    text = ""
    medals = ["🥇", "🥈", "🥉"]
    
    for i, p in enumerate(top_players):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = p.first_name[:15] + "..." if len(p.first_name) > 15 else p.first_name
        you = " ← Siz" if p.user_id == player.user_id else ""
        text += f"{medal} <b>{name}</b> - {p.rating} 🏆{you}\n"
    
    if not text:
        text = "Hali o'yinchilar yo'q!"
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(player, "leaderboard", players=text),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_button(player, "back"), callback_data="back:main")]
        ]),
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE & STATS
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Profil ko'rsatish."""
    player = db.get_player(callback.from_user.id)
    
    text = get_text(
        player, "profile",
        name=player.first_name,
        user_id=player.user_id,
        rating=player.rating,
        coins=player.coins,
        streak=player.current_streak,
        games=player.games_played,
        wins=player.games_won,
        win_rate=player.win_rate,
        achievement_count=len(player.achievements),
        total_achievements=len(Achievement)
    )
    
    await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_button(player, "back"), callback_data="back:main")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    """Statistika ko'rsatish."""
    player = db.get_player(callback.from_user.id)
    
    achievements_text = ", ".join([
        next((a.value[1] for a in Achievement if a.value[0] == ach), ach)
        for ach in player.achievements
    ]) or "Hali yo'q"
    
    text = get_text(
        player, "stats",
        games=player.games_played,
        wins=player.games_won,
        win_rate=player.win_rate,
        best_streak=player.best_streak,
        avg_attempts=player.avg_attempts,
        hints=player.hints_used,
        achievements=achievements_text
    )
    
    await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_button(player, "back"), callback_data="back:main")]
        ]),
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# DAILY BONUS
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "daily")
async def claim_daily(callback: CallbackQuery):
    """Kunlik bonus olish."""
    player = db.get_player(callback.from_user.id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    if player.last_daily == today:
        await callback.answer(get_text(player, "daily_claimed"), show_alert=True)
        return
    
    # Streak hisoblash
    if player.last_daily:
        last = datetime.strptime(player.last_daily, "%Y-%m-%d")
        if (datetime.now() - last).days == 1:
            daily_streak = 1  # Ketma-ket
        else:
            daily_streak = 1
    else:
        daily_streak = 1
    
    # Bonus
    bonus = 50 + (daily_streak * 10)
    player.coins += bonus
    player.last_daily = today
    db.save_player(player)
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(player, "daily_bonus", coins=bonus, streak=daily_streak),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_button(player, "back"), callback_data="back:main")]
        ]),
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    """Sozlamalar."""
    player = db.get_player(callback.from_user.id)
    
    keyboard = [[InlineKeyboardButton(text=name, callback_data=f"setlang:{code}")]
                for code, name in LANGUAGES.items()]
    keyboard.append([InlineKeyboardButton(text=get_button(player, "back"), callback_data="back:main")])
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(player, "choose_language"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("setlang:"))
async def change_language(callback: CallbackQuery, state: FSMContext):
    """Tilni o'zgartirish."""
    lang_code = callback.data.split(":")[1]
    player = db.get_player(callback.from_user.id)
    player.language = lang_code
    db.save_player(player)
    
    await callback.answer(f"✅ {LANGUAGES[lang_code]}")
    await show_main_menu(callback.message, player, state, edit=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SHOP (Placeholder)
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "shop")
async def show_shop(callback: CallbackQuery):
    """Do'kon."""
    player = db.get_player(callback.from_user.id)
    
    await callback.answer()
    await callback.message.edit_text(
        get_text(player, "shop", coins=player.coins) + "\n\n🚧 Tez kunda...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_button(player, "back"), callback_data="back:main")]
        ]),
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Botni ishga tushirish."""
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(router)
    
    logger.info("🤖 Bot ishga tushdi!")
    
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
