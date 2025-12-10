import logging
import os
from typing import Optional, Tuple, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING SOZLAMALARI
# ═══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL O'ZGARUVCHILAR
# ═══════════════════════════════════════════════════════════════════════════════
user_data: Dict[int, Dict[str, Any]] = {}
games: Dict[str, Dict[str, Any]] = {}
pending_send: Dict[int, str] = {}
game_counter: int = 0

# ═══════════════════════════════════════════════════════════════════════════════
# O'YIN HOLATLARI
# ═══════════════════════════════════════════════════════════════════════════════
WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
WAITING_FOR_SECRET = "WAITING_FOR_SECRET"
PLAYING = "PLAYING"
FINISHED = "FINISHED"

# ═══════════════════════════════════════════════════════════════════════════════
# TILLAR
# ═══════════════════════════════════════════════════════════════════════════════
LANGUAGES = {
    "uz": "O'zbek",
    "ru": "Русский",
    "en": "English",
    "kk": "Qaraqalpaq"
}

# ═══════════════════════════════════════════════════════════════════════════════
# XABARLAR
# ═══════════════════════════════════════════════════════════════════════════════
MESSAGES = {
    "uz": {
        "choose_language": "Tilni tanlang:",
        "subscribe": "Botdan foydalanish uchun kanalga a'zo bo'ling: [Kanal](https://t.me/samancikschannel)",
        "lang_confirmed": "Siz {lang} tilini tanladingiz!",
        "not_subscribed": "Iltimos, kanalga a'zo bo'ling❗️",
        "subscription_confirmed": "Muvaffaqiyatli a'zo bo'ldingiz! Asosiy menyuga o'ting.",
        "main_menu": "Asosiy menyu:",
        "game_created": "Yangi o'yin yaratildi! Do'stingizga ushbu havolani yuboring:\n{invite_link}",
        "game_start_info": "O'yin boshlandi! Sizning raqibingiz: {opponent}.\nIltimos, 4 xonali maxfiy raqamingizni kiriting (raqamlar takrorlanmasin).",
        "prompt_secret": "Iltimos, 4 xonali maxfiy raqamingizni kiriting.",
        "secret_set": "Maxfiy raqamingiz saqlandi. Raqibingiz ham kiritishini kuting.",
        "your_turn": "Endi sizning navbatingiz. Taxminingizni yuboring.",
        "opponent_turn": "Endi raqibingizning navbati. Kuting...",
        "invalid_input": "❌ Iltimos, 4 xonali son kiriting (raqamlar takrorlanmasin).",
        "bulls_cows": "🎯 {bulls} Bull, {cows} Cow.\nNavbatingiz kelganda yana urinib ko'ring.",
        "win": "🥳 Tabriklaymiz! Siz {attempts} urinishda g'olib bo'ldingiz!\nRaqibingizning maxfiy raqami: {secret}",
        "lost": "😔 Afsuski, siz mag'lub bo'ldingiz.\nRaqibingizning maxfiy raqami: {secret}",
        "surrendered_self": "Siz taslim bo'ldingiz. Siz yutqazdingiz.",
        "surrendered_opponent": "Sizning raqibingiz taslim bo'ldi. Siz yutdingiz! 🎉",
        "game_cancelled": "O'yin bekor qilindi.",
        "not_your_turn": "Sizning navbatingiz emas❗️",
        "new_game_button": "🎮 Yangi o'yin",
        "settings_button": "⚙️ Sozlamalar",
        "subscribe_button": "✅ A'zo bo'ldim",
        "finish_game_button": "🏳️ Taslim bo'lish",
        "send_message_button": "✉️ Xabar yuborish",
        "cancel_send_button": "❌ Bekor qilish",
        "game_rules_button": "📜 O'yin qoidalari",
        "surrender_confirm": "Haqiqatan ham taslim bo'lmoqchimisiz?",
        "yes_button": "Ha",
        "no_button": "Yo'q",
        "game_rules": "📜 O'yin qoidalari:\n\nBulls & Cows o'yinida har bir o'yinchi 4 xonali maxfiy raqam tanlaydi.\n\n🎯 Bull - raqam to'g'ri va joyi to'g'ri\n🐄 Cow - raqam to'g'ri, lekin joyi noto'g'ri\n\nG'olib - raqibning maxfiy raqamini birinchi topgan o'yinchi!",
        "game_not_found": "Faol o'yin topilmadi.",
        "already_in_game": "Siz allaqachon faol o'yinda ishtirok etmoqdasiz!",
        "game_already_started": "Bu o'yin allaqachon boshlangan!",
        "cannot_play_self": "O'zingiz bilan o'ynay olmaysiz!",
        "secret_already_set": "Siz allaqachon maxfiy raqamingizni kiritgansiz.",
        "message_sent": "Xabar yuborildi ✅",
        "write_message": "Yubormoqchi bo'lgan xabaringizni yozing:",
        "message_from": "💬 {name} dan xabar: {text}",
        "send_cancelled": "Xabar yuborish bekor qilindi.",
        "play_again": "Yana o'ynash uchun /start bosing",
        "waiting_opponent": "Raqibingiz kutilmoqda...",
        "back_button": "🔙 Orqaga"
    },
    "ru": {
        "choose_language": "Выберите язык:",
        "subscribe": "Пожалуйста, подпишитесь на канал: [Канал](https://t.me/samancikschannel)",
        "lang_confirmed": "Вы выбрали {lang}!",
        "not_subscribed": "Пожалуйста, подпишитесь на канал❗️",
        "subscription_confirmed": "Вы успешно подписались! Переход в главное меню.",
        "main_menu": "Главное меню:",
        "game_created": "Новая игра создана! Пригласите друга по ссылке:\n{invite_link}",
        "game_start_info": "Игра началась! Ваш противник: {opponent}.\nПожалуйста, введите ваше 4-значное секретное число (цифры не должны повторяться).",
        "prompt_secret": "Пожалуйста, введите ваше 4-значное секретное число.",
        "secret_set": "Ваше секретное число сохранено. Ожидайте противника.",
        "your_turn": "Теперь ваша очередь. Отправьте ваш прогноз.",
        "opponent_turn": "Сейчас очередь противника. Ожидайте...",
        "invalid_input": "❌ Пожалуйста, введите 4-значное число (цифры не должны повторяться).",
        "bulls_cows": "🎯 {bulls} Bull, {cows} Cow.\nПопробуйте еще раз, когда придет ваша очередь.",
        "win": "🥳 Поздравляем! Вы выиграли за {attempts} попыток!\nСекрет соперника: {secret}",
        "lost": "😔 К сожалению, вы проиграли.\nСекретный номер противника: {secret}",
        "surrendered_self": "Вы сдались. Вы проиграли.",
        "surrendered_opponent": "Ваш противник сдался. Вы выиграли! 🎉",
        "game_cancelled": "Игра отменена.",
        "not_your_turn": "Сейчас не ваша очередь❗️",
        "new_game_button": "🎮 Новая игра",
        "settings_button": "⚙️ Настройки",
        "subscribe_button": "✅ Подписался",
        "finish_game_button": "🏳️ Сдаться",
        "send_message_button": "✉️ Отправить сообщение",
        "cancel_send_button": "❌ Отмена",
        "game_rules_button": "📜 Правила игры",
        "surrender_confirm": "Вы уверены, что хотите сдаться?",
        "yes_button": "Да",
        "no_button": "Нет",
        "game_rules": "📜 Правила игры:\n\nВ игре Bulls & Cows каждый игрок выбирает 4-значное секретное число.\n\n🎯 Bull - цифра верна и на своём месте\n🐄 Cow - цифра верна, но не на своём месте\n\nПобедитель - тот, кто первым угадает секрет противника!",
        "game_not_found": "Активная игра не найдена.",
        "already_in_game": "Вы уже участвуете в активной игре!",
        "game_already_started": "Эта игра уже началась!",
        "cannot_play_self": "Нельзя играть с самим собой!",
        "secret_already_set": "Вы уже ввели секретное число.",
        "message_sent": "Сообщение отправлено ✅",
        "write_message": "Напишите сообщение для отправки:",
        "message_from": "💬 Сообщение от {name}: {text}",
        "send_cancelled": "Отправка сообщения отменена.",
        "play_again": "Нажмите /start чтобы играть снова",
        "waiting_opponent": "Ожидание противника...",
        "back_button": "🔙 Назад"
    },
    "en": {
        "choose_language": "Choose a language:",
        "subscribe": "Please join the channel: [Channel](https://t.me/samancikschannel)",
        "lang_confirmed": "You have selected {lang}!",
        "not_subscribed": "Please join the channel❗️",
        "subscription_confirmed": "Subscription confirmed! Proceeding to main menu.",
        "main_menu": "Main Menu:",
        "game_created": "New game created! Invite your friend using this link:\n{invite_link}",
        "game_start_info": "Game started! Your opponent is {opponent}.\nPlease enter your 4-digit secret number (no repeating digits).",
        "prompt_secret": "Please enter your 4-digit secret number.",
        "secret_set": "Your secret number has been saved. Waiting for opponent.",
        "your_turn": "It's your turn now. Please enter your guess.",
        "opponent_turn": "It's your opponent's turn. Please wait...",
        "invalid_input": "❌ Please enter a 4-digit number (no repeating digits).",
        "bulls_cows": "🎯 {bulls} Bull, {cows} Cow.\nTry again when it's your turn.",
        "win": "🥳 Congratulations! You won in {attempts} attempts!\nOpponent's secret: {secret}",
        "lost": "😔 Unfortunately, you lost.\nOpponent's secret number: {secret}",
        "surrendered_self": "You surrendered. You lost.",
        "surrendered_opponent": "Your opponent surrendered. You win! 🎉",
        "game_cancelled": "Game cancelled.",
        "not_your_turn": "It's not your turn❗️",
        "new_game_button": "🎮 New Game",
        "settings_button": "⚙️ Settings",
        "subscribe_button": "✅ Subscribed",
        "finish_game_button": "🏳️ Surrender",
        "send_message_button": "✉️ Send Message",
        "cancel_send_button": "❌ Cancel",
        "game_rules_button": "📜 Game Rules",
        "surrender_confirm": "Are you sure you want to surrender?",
        "yes_button": "Yes",
        "no_button": "No",
        "game_rules": "📜 Game Rules:\n\nIn Bulls & Cows, each player chooses a 4-digit secret number.\n\n🎯 Bull - correct digit in correct position\n🐄 Cow - correct digit in wrong position\n\nThe winner is the first to guess the opponent's secret!",
        "game_not_found": "No active game found.",
        "already_in_game": "You are already in an active game!",
        "game_already_started": "This game has already started!",
        "cannot_play_self": "You cannot play against yourself!",
        "secret_already_set": "You have already entered your secret number.",
        "message_sent": "Message sent ✅",
        "write_message": "Write your message to send:",
        "message_from": "💬 Message from {name}: {text}",
        "send_cancelled": "Message sending cancelled.",
        "play_again": "Press /start to play again",
        "waiting_opponent": "Waiting for opponent...",
        "back_button": "🔙 Back"
    },
    "kk": {
        "choose_language": "Tildi saylań:",
        "subscribe": "Ótinish, kanalǵa jazılıń: [Kanal](https://t.me/samancikschannel)",
        "lang_confirmed": "Siz {lang} tańladıńız!",
        "not_subscribed": "Ótinish, kanalǵa jazılıń❗️",
        "subscription_confirmed": "Siz tabıslı jazıldıńız!",
        "main_menu": "Bas menyu:",
        "game_created": "Jańa oyın jaratıldı! Dosıńızdı shaqırıń:\n{invite_link}",
        "game_start_info": "Oyın baslandı! Qarsılasıńız: {opponent}.\n4 sanli jasırın nomerińizdi kiritiń.",
        "prompt_secret": "4 sanli jasırın nomerińizdi kiritiń.",
        "secret_set": "Jasırın nomerińiz saqlandı. Qarsılastı kútiń.",
        "your_turn": "Házir sizdiń gezegińiz. Boljawinizdi jiberiń.",
        "opponent_turn": "Qarsılastıń gezegi. Kútiń...",
        "invalid_input": "❌ 4 sanli nomer kiritiń (sanlar qaytalanbasın).",
        "bulls_cows": "🎯 {bulls} Bull, {cows} Cow.\nGezegińizde qayta urınıp kóriń.",
        "win": "🥳 Qutlıqlaymız! Siz {attempts} urınısta jeńdińiz!\nQarsılastıń jasırın nomeri: {secret}",
        "lost": "😔 Ókinishtey, siz uттıldıńız.\nQarsılastıń jasırın nomeri: {secret}",
        "surrendered_self": "Siz taslim boldıńız. Siz utıldıńız.",
        "surrendered_opponent": "Qarsılasıńız taslim boldı. Siz jeńdińiz! 🎉",
        "game_cancelled": "Oyın biykar etildi.",
        "not_your_turn": "Sizdiń gezegińiz emes❗️",
        "new_game_button": "🎮 Jańa oyın",
        "settings_button": "⚙️ Sazlamalar",
        "subscribe_button": "✅ Jazıldım",
        "finish_game_button": "🏳️ Taslim bolıw",
        "send_message_button": "✉️ Xabar jiberiw",
        "cancel_send_button": "❌ Biykarlaw",
        "game_rules_button": "📜 Oyın qağıydalari",
        "surrender_confirm": "Taslim bolıwǵa isenimińiz barma?",
        "yes_button": "Awa",
        "no_button": "Yaq",
        "game_rules": "📜 Oyın qağıydalari:\n\nBulls & Cows oyınında hár bir oyınshı 4 sanli jasırın nomer saylaydi.\n\n🎯 Bull - san durıs hám orni durıs\n🐄 Cow - san durıs, biraq orni durıs emes\n\nJeńimpaz - qarsılastıń jasırın nomerin birinshi tapqan!",
        "game_not_found": "Aktiv oyın tabılmadı.",
        "already_in_game": "Siz allaqashan oyındasisiz!",
        "game_already_started": "Bul oyın allaqashan baslanǵan!",
        "cannot_play_self": "Ózińiz benen oynay almaysız!",
        "secret_already_set": "Siz jasırın nomerdi kiritkensiz.",
        "message_sent": "Xabar jiberildi ✅",
        "write_message": "Xabarıńızdı jazıń:",
        "message_from": "💬 {name} dan xabar: {text}",
        "send_cancelled": "Xabar jiberiw biykar etildi.",
        "play_again": "Qayta oylaw ushın /start basıń",
        "waiting_opponent": "Qarsılas kútilmekte...",
        "back_button": "🔙 Artqa"
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# YORDAMCHI FUNKSIYALAR
# ═══════════════════════════════════════════════════════════════════════════════

def get_user_lang(user_id: int) -> str:
    """Foydalanuvchi tilini olish."""
    return user_data.get(user_id, {}).get("language", "uz")


def get_msg(user_id: int, key: str, **kwargs) -> str:
    """Foydalanuvchi tiliga mos xabarni olish."""
    lang = get_user_lang(user_id)
    msg = MESSAGES.get(lang, MESSAGES["uz"]).get(key, MESSAGES["uz"].get(key, key))
    if kwargs:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg
    return msg


def init_user(user_id: int, first_name: str) -> None:
    """Foydalanuvchini ro'yxatdan o'tkazish."""
    if user_id not in user_data:
        user_data[user_id] = {"first_name": first_name}


def is_valid_secret(text: str) -> bool:
    """Maxfiy raqam to'g'ri formatda ekanligini tekshirish."""
    if len(text) != 4 or not text.isdigit():
        return False
    # Takrorlanuvchi raqamlar yo'qligini tekshirish
    return len(set(text)) == 4


def is_valid_guess(text: str) -> bool:
    """Taxmin to'g'ri formatda ekanligini tekshirish."""
    return len(text) == 4 and text.isdigit()


def calculate_bulls_cows(secret: str, guess: str) -> Tuple[int, int]:
    """Bulls va Cows hisoblash."""
    bulls = sum(s == g for s, g in zip(secret, guess))
    cows = sum(min(secret.count(d), guess.count(d)) for d in set(guess)) - bulls
    return bulls, cows


def find_game(user_id: int) -> Tuple[Optional[str], Optional[Dict]]:
    """Foydalanuvchining faol o'yinini topish."""
    for gid, game in games.items():
        if game["status"] != FINISHED:
            if game["player1"] == user_id or game["player2"] == user_id:
                return gid, game
    return None, None


def get_opponent_id(game: Dict, user_id: int) -> Optional[int]:
    """Raqib ID sini olish."""
    if game["player1"] == user_id:
        return game["player2"]
    return game["player1"]


def cleanup_finished_games() -> None:
    """Tugagan o'yinlarni tozalash."""
    finished = [gid for gid, game in games.items() if game["status"] == FINISHED]
    for gid in finished:
        del games[gid]


# ═══════════════════════════════════════════════════════════════════════════════
# KLAVIATURA FUNKSIYALARI
# ═══════════════════════════════════════════════════════════════════════════════

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Til tanlash klaviaturasi."""
    keyboard = [[InlineKeyboardButton(name, callback_data=f"lang_{code}")]
                for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu(user_id: int) -> InlineKeyboardMarkup:
    """Asosiy menyu klaviaturasi."""
    lang = get_user_lang(user_id)
    msgs = MESSAGES.get(lang, MESSAGES["uz"])
    keyboard = [
        [InlineKeyboardButton(msgs["new_game_button"], callback_data="new_game")],
        [InlineKeyboardButton(msgs["game_rules_button"], callback_data="game_rules")],
        [InlineKeyboardButton(msgs["settings_button"], callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_subscribe_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Obuna bo'lish klaviaturasi."""
    lang = get_user_lang(user_id)
    msgs = MESSAGES.get(lang, MESSAGES["uz"])
    keyboard = [[InlineKeyboardButton(msgs["subscribe_button"], callback_data="check_subscription")]]
    return InlineKeyboardMarkup(keyboard)


def get_game_controls(user_id: int) -> InlineKeyboardMarkup:
    """O'yin boshqaruv klaviaturasi."""
    lang = get_user_lang(user_id)
    msgs = MESSAGES.get(lang, MESSAGES["uz"])
    keyboard = [
        [
            InlineKeyboardButton(msgs["finish_game_button"], callback_data="finish_game"),
            InlineKeyboardButton(msgs["send_message_button"], callback_data="send_message")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_surrender_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Taslim bo'lish tasdiqlash klaviaturasi."""
    lang = get_user_lang(user_id)
    msgs = MESSAGES.get(lang, MESSAGES["uz"])
    keyboard = [[
        InlineKeyboardButton(msgs["yes_button"], callback_data="surrender_yes"),
        InlineKeyboardButton(msgs["no_button"], callback_data="surrender_no")
    ]]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_send_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Xabar yuborishni bekor qilish klaviaturasi."""
    lang = get_user_lang(user_id)
    msgs = MESSAGES.get(lang, MESSAGES["uz"])
    keyboard = [[InlineKeyboardButton(msgs["cancel_send_button"], callback_data="cancel_send")]]
    return InlineKeyboardMarkup(keyboard)


# ═══════════════════════════════════════════════════════════════════════════════
# ASOSIY HANDLERLAR
# ═══════════════════════════════════════════════════════════════════════════════

async def start_handler(update: Update, context: CallbackContext) -> None:
    """Start komandasi handleri."""
    user = update.effective_user
    init_user(user.id, user.first_name)
    
    # Taklifnoma bilan kelgan bo'lsa
    if context.args and context.args[0].startswith("invite_"):
        if "language" in user_data[user.id]:
            await process_invite(update, context, context.args[0])
        else:
            user_data[user.id]["pending_invite"] = context.args[0]
            await update.message.reply_text(
                "Tilni tanlang / Выберите язык / Choose a language:",
                reply_markup=get_language_keyboard()
            )
        return
    
    # Faol o'yinda bo'lsa
    gid, game = find_game(user.id)
    if game and game["status"] in [PLAYING, WAITING_FOR_SECRET]:
        await update.message.reply_text(
            get_msg(user.id, "surrender_confirm"),
            reply_markup=get_surrender_confirm_keyboard(user.id)
        )
        return
    
    # Kutilayotgan o'yinni bekor qilish
    if game and game["status"] == WAITING_FOR_PLAYERS and game["player1"] == user.id:
        game["status"] = FINISHED
        await update.message.reply_text(get_msg(user.id, "game_cancelled"))
    
    # Til tanlanmagan bo'lsa
    if "language" not in user_data[user.id]:
        await update.message.reply_text(
            "Tilni tanlang / Выберите язык / Choose a language:",
            reply_markup=get_language_keyboard()
        )
        return
    
    # Obuna tekshirish
    if not user_data[user.id].get("subscribed", False):
        await update.message.reply_text(
            get_msg(user.id, "subscribe"),
            parse_mode="Markdown",
            reply_markup=get_subscribe_keyboard(user.id)
        )
        return
    
    # Asosiy menyuni ko'rsatish
    cleanup_finished_games()
    await update.message.reply_text(
        get_msg(user.id, "main_menu"),
        reply_markup=get_main_menu(user.id)
    )


async def set_language_handler(update: Update, context: CallbackContext) -> None:
    """Til tanlash handleri (birinchi marta)."""
    query = update.callback_query
    await query.answer()
    
    lang_code = query.data.split("_")[1]
    user_id = query.from_user.id
    
    init_user(user_id, query.from_user.first_name)
    user_data[user_id]["language"] = lang_code
    user_data[user_id]["subscribed"] = False
    
    await query.edit_message_text(
        get_msg(user_id, "subscribe"),
        parse_mode="Markdown",
        reply_markup=get_subscribe_keyboard(user_id)
    )


async def change_language_handler(update: Update, context: CallbackContext) -> None:
    """Tilni o'zgartirish handleri (sozlamalardan)."""
    query = update.callback_query
    await query.answer()
    
    lang_code = query.data.split("_")[1]
    user_id = query.from_user.id
    
    user_data[user_id]["language"] = lang_code
    confirm = get_msg(user_id, "lang_confirmed", lang=LANGUAGES[lang_code])
    
    await query.edit_message_text(
        f"{confirm}\n\n{get_msg(user_id, 'main_menu')}",
        reply_markup=get_main_menu(user_id)
    )


async def settings_handler(update: Update, context: CallbackContext) -> None:
    """Sozlamalar handleri."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    keyboard = [[InlineKeyboardButton(name, callback_data=f"setlang_{code}")]
                for code, name in LANGUAGES.items()]
    keyboard.append([InlineKeyboardButton(
        get_msg(user_id, "back_button"),
        callback_data="back_to_menu"
    )])
    
    await query.edit_message_text(
        get_msg(user_id, "choose_language"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def back_to_menu_handler(update: Update, context: CallbackContext) -> None:
    """Asosiy menyuga qaytish."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    await query.edit_message_text(
        get_msg(user_id, "main_menu"),
        reply_markup=get_main_menu(user_id)
    )


async def check_subscription_handler(update: Update, context: CallbackContext) -> None:
    """Obuna tekshirish handleri."""
    query = update.callback_query
    user_id = query.from_user.id
    channel_username = "@samancikschannel"
    
    try:
        member = await context.bot.get_chat_member(channel_username, user_id)
        if member.status in ["member", "creator", "administrator", "restricted"]:
            user_data[user_id]["subscribed"] = True
            await query.answer(get_msg(user_id, "subscription_confirmed"), show_alert=True)
            
            # Kutilayotgan taklifnoma bo'lsa
            if "pending_invite" in user_data[user_id]:
                invite = user_data[user_id].pop("pending_invite")
                await query.edit_message_text(get_msg(user_id, "main_menu"))
                await process_invite(update, context, invite)
            else:
                await query.edit_message_text(
                    get_msg(user_id, "main_menu"),
                    reply_markup=get_main_menu(user_id)
                )
        else:
            await query.answer(get_msg(user_id, "not_subscribed"), show_alert=True)
    except Exception as e:
        logger.error("Subscription check error: %s", e)
        await query.answer(get_msg(user_id, "not_subscribed"), show_alert=True)


async def game_rules_handler(update: Update, context: CallbackContext) -> None:
    """O'yin qoidalari handleri."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    keyboard = [[InlineKeyboardButton(
        get_msg(user_id, "back_button"),
        callback_data="back_to_menu"
    )]]
    
    await query.edit_message_text(
        get_msg(user_id, "game_rules"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# O'YIN HANDLERLARI
# ═══════════════════════════════════════════════════════════════════════════════

async def new_game_handler(update: Update, context: CallbackContext) -> None:
    """Yangi o'yin yaratish handleri."""
    global game_counter
    query = update.callback_query
    user_id = query.from_user.id
    
    # Faol o'yinda emasligini tekshirish
    _, existing_game = find_game(user_id)
    if existing_game:
        await query.answer(get_msg(user_id, "already_in_game"), show_alert=True)
        return
    
    await query.answer()
    
    game_id = str(game_counter)
    game_counter += 1
    
    games[game_id] = {
        "player1": user_id,
        "player2": None,
        "secret1": None,
        "secret2": None,
        "status": WAITING_FOR_PLAYERS,
        "turn": None,
        "attempts": {user_id: 0}
    }
    
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=invite_{game_id}"
    
    await query.edit_message_text(
        get_msg(user_id, "game_created", invite_link=invite_link)
    )


async def process_invite(update: Update, context: CallbackContext, invite_arg: str) -> None:
    """Taklifnomani qayta ishlash."""
    user = update.effective_user
    user_id = user.id
    
    game_id = invite_arg.split("_")[1]
    
    if game_id not in games:
        await context.bot.send_message(user_id, get_msg(user_id, "game_not_found"))
        return
    
    game = games[game_id]
    
    # O'zi bilan o'ynashni oldini olish
    if game["player1"] == user_id:
        await context.bot.send_message(user_id, get_msg(user_id, "cannot_play_self"))
        return
    
    if game["player2"] is not None:
        await context.bot.send_message(user_id, get_msg(user_id, "game_already_started"))
        return
    
    # O'yinni boshlash
    game["player2"] = user_id
    game["status"] = WAITING_FOR_SECRET
    game["attempts"][user_id] = 0
    
    p1_name = user_data.get(game["player1"], {}).get("first_name", "Opponent")
    p2_name = user_data.get(user_id, {}).get("first_name", "Opponent")
    
    # Ikkala o'yinchiga xabar yuborish
    await context.bot.send_message(
        game["player1"],
        get_msg(game["player1"], "game_start_info", opponent=p2_name)
    )
    await context.bot.send_message(
        user_id,
        get_msg(user_id, "game_start_info", opponent=p1_name)
    )


async def finish_game_handler(update: Update, context: CallbackContext) -> None:
    """O'yinni tugatish (taslim bo'lish) handleri."""
    query = update.callback_query
    user_id = query.from_user.id
    
    gid, game = find_game(user_id)
    if not game:
        await query.answer(get_msg(user_id, "game_not_found"), show_alert=True)
        return
    
    await query.answer()
    await query.edit_message_text(
        get_msg(user_id, "surrender_confirm"),
        reply_markup=get_surrender_confirm_keyboard(user_id)
    )


async def surrender_yes_handler(update: Update, context: CallbackContext) -> None:
    """Taslim bo'lishni tasdiqlash."""
    query = update.callback_query
    user_id = query.from_user.id
    
    gid, game = find_game(user_id)
    if not game:
        await query.answer(get_msg(user_id, "game_not_found"), show_alert=True)
        return
    
    await query.answer()
    game["status"] = FINISHED
    
    # O'yinchiga xabar
    await query.edit_message_text(
        f"{get_msg(user_id, 'surrendered_self')}\n\n{get_msg(user_id, 'play_again')}"
    )
    await context.bot.send_message(
        user_id,
        get_msg(user_id, "main_menu"),
        reply_markup=get_main_menu(user_id)
    )
    
    # Raqibga xabar
    opponent_id = get_opponent_id(game, user_id)
    if opponent_id:
        await context.bot.send_message(
            opponent_id,
            f"{get_msg(opponent_id, 'surrendered_opponent')}\n\n{get_msg(opponent_id, 'play_again')}"
        )
        await context.bot.send_message(
            opponent_id,
            get_msg(opponent_id, "main_menu"),
            reply_markup=get_main_menu(opponent_id)
        )


async def surrender_no_handler(update: Update, context: CallbackContext) -> None:
    """Taslim bo'lishni bekor qilish."""
    query = update.callback_query
    user_id = query.from_user.id
    
    gid, game = find_game(user_id)
    
    await query.answer()
    
    if game and game["status"] == PLAYING:
        if game["turn"] == user_id:
            msg = get_msg(user_id, "your_turn")
        else:
            msg = get_msg(user_id, "opponent_turn")
        await query.edit_message_text(msg, reply_markup=get_game_controls(user_id))
    elif game and game["status"] == WAITING_FOR_SECRET:
        await query.edit_message_text(
            get_msg(user_id, "prompt_secret"),
            reply_markup=get_game_controls(user_id)
        )
    else:
        await query.edit_message_text(
            get_msg(user_id, "main_menu"),
            reply_markup=get_main_menu(user_id)
        )


async def send_message_handler(update: Update, context: CallbackContext) -> None:
    """Xabar yuborish tugmasi handleri."""
    query = update.callback_query
    user_id = query.from_user.id
    
    gid, game = find_game(user_id)
    if not game or game["status"] not in [PLAYING, WAITING_FOR_SECRET]:
        await query.answer(get_msg(user_id, "game_not_found"), show_alert=True)
        return
    
    await query.answer()
    pending_send[user_id] = gid
    
    await query.edit_message_text(
        get_msg(user_id, "write_message"),
        reply_markup=get_cancel_send_keyboard(user_id)
    )


async def cancel_send_handler(update: Update, context: CallbackContext) -> None:
    """Xabar yuborishni bekor qilish."""
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id in pending_send:
        del pending_send[user_id]
    
    await query.answer(get_msg(user_id, "send_cancelled"), show_alert=True)
    
    gid, game = find_game(user_id)
    if game and game["status"] == PLAYING:
        if game["turn"] == user_id:
            msg = get_msg(user_id, "your_turn")
        else:
            msg = get_msg(user_id, "opponent_turn")
        await query.edit_message_text(msg, reply_markup=get_game_controls(user_id))
    else:
        await query.edit_message_text(
            get_msg(user_id, "main_menu"),
            reply_markup=get_main_menu(user_id)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# XABAR HANDLERI
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Matn xabarlarini qayta ishlash."""
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()
    
    # Xabar yuborish rejimida
    if user_id in pending_send:
        gid = pending_send.pop(user_id)
        game = games.get(gid)
        
        if not game or game["status"] == FINISHED:
            await update.message.reply_text(get_msg(user_id, "game_not_found"))
            return
        
        opponent_id = get_opponent_id(game, user_id)
        if opponent_id:
            await context.bot.send_message(
                opponent_id,
                get_msg(opponent_id, "message_from", name=user.first_name, text=text)
            )
        
        await update.message.reply_text(
            get_msg(user_id, "message_sent"),
            reply_markup=get_game_controls(user_id)
        )
        return
    
    # O'yinni topish
    gid, game = find_game(user_id)
    if not game:
        await update.message.reply_text(
            f"{get_msg(user_id, 'game_not_found')}\n\n{get_msg(user_id, 'play_again')}"
        )
        return
    
    # Maxfiy raqam kiritish
    if game["status"] == WAITING_FOR_SECRET:
        await handle_secret_input(update, context, game, gid, user_id, text)
        return
    
    # Taxmin kiritish
    if game["status"] == PLAYING:
        await handle_guess_input(update, context, game, gid, user_id, text)
        return


async def handle_secret_input(update: Update, context: CallbackContext, 
                              game: Dict, gid: str, user_id: int, text: str) -> None:
    """Maxfiy raqam kiritishni qayta ishlash."""
    if not is_valid_secret(text):
        await update.message.reply_text(get_msg(user_id, "invalid_input"))
        return
    
    # Maxfiy raqamni saqlash
    if user_id == game["player1"]:
        if game["secret1"] is not None:
            await update.message.reply_text(get_msg(user_id, "secret_already_set"))
            return
        game["secret1"] = text
    else:
        if game["secret2"] is not None:
            await update.message.reply_text(get_msg(user_id, "secret_already_set"))
            return
        game["secret2"] = text
    
    await update.message.reply_text(get_msg(user_id, "secret_set"))
    
    # Ikkala o'yinchi ham kiritganmi?
    if game["secret1"] and game["secret2"]:
        game["status"] = PLAYING
        game["turn"] = game["player1"]
        
        # Player1 ga navbat xabari
        await context.bot.send_message(
            game["player1"],
            get_msg(game["player1"], "your_turn"),
            reply_markup=get_game_controls(game["player1"])
        )
        
        # Player2 ga kutish xabari
        await context.bot.send_message(
            game["player2"],
            get_msg(game["player2"], "opponent_turn"),
            reply_markup=get_game_controls(game["player2"])
        )


async def handle_guess_input(update: Update, context: CallbackContext,
                             game: Dict, gid: str, user_id: int, text: str) -> None:
    """Taxminni qayta ishlash."""
    # Navbatni tekshirish
    if user_id != game["turn"]:
        await update.message.reply_text(get_msg(user_id, "not_your_turn"))
        return
    
    # Formatni tekshirish
    if not is_valid_guess(text):
        await update.message.reply_text(get_msg(user_id, "invalid_input"))
        return
    
    game["attempts"][user_id] += 1
    opponent_id = get_opponent_id(game, user_id)
    
    # Raqibning maxfiy raqami
    if user_id == game["player1"]:
        target_secret = game["secret2"]
        own_secret = game["secret1"]
    else:
        target_secret = game["secret1"]
        own_secret = game["secret2"]
    
    bulls, cows = calculate_bulls_cows(target_secret, text)
    
    # G'alaba!
    if bulls == 4:
        game["status"] = FINISHED
        
        # G'olibga xabar
        await update.message.reply_text(
            get_msg(user_id, "win", attempts=game["attempts"][user_id], secret=target_secret)
        )
        await context.bot.send_message(
            user_id,
            get_msg(user_id, "main_menu"),
            reply_markup=get_main_menu(user_id)
        )
        
        # Mag'lubga xabar
        if opponent_id:
            await context.bot.send_message(
                opponent_id,
                get_msg(opponent_id, "lost", secret=own_secret)
            )
            await context.bot.send_message(
                opponent_id,
                get_msg(opponent_id, "main_menu"),
                reply_markup=get_main_menu(opponent_id)
            )
        return
    
    # Natija xabari
    result_msg = get_msg(user_id, "bulls_cows", bulls=bulls, cows=cows)
    await update.message.reply_text(result_msg)
    
    # Navbatni o'zgartirish
    game["turn"] = opponent_id
    
    # Ikkala o'yinchiga navbat haqida xabar
    await context.bot.send_message(
        user_id,
        get_msg(user_id, "opponent_turn"),
        reply_markup=get_game_controls(user_id)
    )
    
    if opponent_id:
        await context.bot.send_message(
            opponent_id,
            get_msg(opponent_id, "your_turn"),
            reply_markup=get_game_controls(opponent_id)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Botni ishga tushirish."""
    TOKEN = os.getenv("BOT_TOKEN", "7701613822:AAFEOPYnLokpQpF-mu73edLbH5e7PINiLMo")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Komanda handlerlari
    app.add_handler(CommandHandler("start", start_handler))
    
    # Callback handlerlari
    app.add_handler(CallbackQueryHandler(set_language_handler, pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(change_language_handler, pattern=r"^setlang_"))
    app.add_handler(CallbackQueryHandler(check_subscription_handler, pattern=r"^check_subscription$"))
    app.add_handler(CallbackQueryHandler(new_game_handler, pattern=r"^new_game$"))
    app.add_handler(CallbackQueryHandler(settings_handler, pattern=r"^settings$"))
    app.add_handler(CallbackQueryHandler(game_rules_handler, pattern=r"^game_rules$"))
    app.add_handler(CallbackQueryHandler(back_to_menu_handler, pattern=r"^back_to_menu$"))
    app.add_handler(CallbackQueryHandler(finish_game_handler, pattern=r"^finish_game$"))
    app.add_handler(CallbackQueryHandler(send_message_handler, pattern=r"^send_message$"))
    app.add_handler(CallbackQueryHandler(cancel_send_handler, pattern=r"^cancel_send$"))
    app.add_handler(CallbackQueryHandler(surrender_yes_handler, pattern=r"^surrender_yes$"))
    app.add_handler(CallbackQueryHandler(surrender_no_handler, pattern=r"^surrender_no$"))
    
    # Matn handleri
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
