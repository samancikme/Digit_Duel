from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import logging




logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

user_data = {}
games = {}
pending_send = {}
game_counter = 0

WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
WAITING_FOR_SECRET  = "WAITING_FOR_SECRET"
PLAYING             = "PLAYING"
FINISHED            = "FINISHED"

LANGUAGES = {
    "uz": "O'zbek",
    "ru": "Русский",
    "en": "English",
    "kk": "Qaraqalpaq"
}

MESSAGES = {
    "uz": {
        "choose_language": "Tilni tanlang:",
        "subscribe": "Botdan foydalanish uchun kanalga a'zo bo'ling: [Kanal](https://t.me/samancikschannel)",
        "lang_confirmed": "Siz {lang} tilini tanladingiz!",
        "not_subscribed": "Iltimos, kanalga a'zo bo'ling❗️",
        "subscription_confirmed": "Muvaffaqiyatli a'zo bo'ldingiz! Asosiy menyuga o'ting.",
        "main_menu": "Asosiy menyu:",
        "game_created": "Yangi o'yin yaratildi! Do'stingizga ushbu havolani yuboring:\n{invite_link}",
        "game_start_info": "O'yin boshlandi! Sizning raqibingiz: {opponent}.\nIltimos, 4 xonali maxfiy raqamingizni kiriting.",
        "prompt_secret": "Iltimos, 4 xonali maxfiy raqamingizni kiriting.",
        "secret_set": "Maxfiy raqamingiz saqlandi.",
        "your_turn": "Endi sizning navbatingiz. Taxminingizni yuboring.",
        "opponent_turn": "Endi raqibingizning navbati.",
        "turn_notification": "Endi {player} ning navbati.",
        "invalid_input": "❌ Iltimos, 4 xonali son kiriting.",
        "bulls_cows": "{bulls} ta to'g'ri✅. \nnavbatingiz kelganda yana urinib ko'ring.",
        "win": "Tabriklaymiz!🥳🥳🥳 \nSiz {attempts} urinishda g'olib bo'ldingiz!\nRaqibingizning maxfiy raqami: {secret}\nYana o'ynashni xoxlasangiz /start bosing",
        "lost": "Afsuski, siz mag'lub bo'ldingiz.\nRaqibingizning maxfiy raqami: {secret} \nYana o'ynashni xoxlasangiz /start bosing",
        "surrendered_self": "Siz taslim bo'ldingiz. Siz yutqazdingiz.\nYana o'ynashni xoxlasangiz /start bosing",
        "surrendered_opponent": "Sizning raqibingiz taslim bo'ldi. Siz yutdingiz.\nYana o'ynashni xoxlasangiz /start bosing",
        "game_cancelled": "Yangi o'yin bekor qilindi, chunki ikkinchi o'yinchi qo'shilmagan.",
        "not_your_turn" : "Sizning navbatingiz emas❗️❗️❗️",
        "new_game_button": "🎮 Yangi o'yin",
        "settings_button": "⚙ Sozlamalar",
        "subscribe_button": "✅ A'zo bo'ldim",
        "finish_game_button": "🏁 O'yinni tugatish",
        "send_message_button": "✉️ Xabar yuborish",
        "cancel_send_button": "❌ Bekor qilish",
        "game_rules_button": "📜 O'yin shartlari",
        "surrender_confirm" : "Haqiqatan ham taslim bo'lmoqchimisiz?",
        "game_rules": "O'yin shartlari: Bulls & Cows o'yinida, har bir taxminda to'g'ri raqamlar va ularning joylashuvi aniqlanadi. G'olib – raqibning maxfiy raqamini to'liq topgan o'yinchi."
    },
    "ru": {
        "choose_language": "Выберите язык:",
        "subscribe": "Пожалуйста, подпишитесь на канал: [Канал](https://t.me/samancikschannel)",
        "lang_confirmed": "Вы выбрали {lang}!",
        "not_subscribed": "Пожалуйста, подпишитесь на канал!",
        "subscription_confirmed": "Вы успешно подписались! Переход в главное меню.",
        "main_menu": "Главное меню:",
        "game_created": "Новая игра создана! Пригласите друга по ссылке:\n{invite_link}",
        "game_start_info": "Игра началась! Ваш противник: {opponent}.\nПожалуйста, введите ваше 4-значное секретное число.",
        "prompt_secret": "Пожалуйста, введите ваше 4-значное секретное число.",
        "secret_set": "Ваше секретное число сохранено.",
        "your_turn": "Теперь ваша очередь. Отправьте ваш прогноз.",
        "opponent_turn": "Сейчас очередь противника.",
        "turn_notification": "Сейчас очередь {player}.",
        "invalid_input": "❌ Пожалуйста, введите 4-значное число.",
        "bulls_cows": "{bulls} правильных ответа ✅. \n Попробуйте еще раз, когда придет ваша очередь.",
        "win": "Поздравляем! Вы выиграли за {attempts} попыток!\nСекрет соперника: {secret}\nЕсли вы хотите начать игру снова, нажмите /start.",
        "lost": "К сожалению, вы проиграли.\nСекретный номер вашего противника: {secret}\nЕсли вы хотите начать игру снова, нажмите /start.",
        "surrendered_self": "Вы сдались. Вы проиграли.",
        "surrendered_opponent": "Ваш противник сдался. Вы выиграли.",
        "game_cancelled": "Новая игра отменена, так как второй игрок не присоединился.",
        "not_your_turn" : "Сейчас не твоя очередь❗️❗️❗️",
        "new_game_button": "🎮 Новая игра",
        "settings_button": "⚙ Настройки",
        "subscribe_button": "✅ Подписался",
        "finish_game_button": "🏁 Завершить игру",
        "send_message_button": "✉️ Отправить сообщение",
        "cancel_send_button": "❌ Отмена",
        "game_rules_button": "📜 Правила игры",
        "surrender_confirm" : "Вы уверены, что хотите сдаться?",
        "game_rules": "Правила игры: В игре Bulls & Cows при каждой попытке определяется количество правильных цифр и их позиций. Победителем считается тот, кто полностью угадает секретное число."
    },
    "en": {
        "choose_language": "Choose a language:",
        "subscribe": "Please join the channel: [Channel](https://t.me/samancikschannel)",
        "lang_confirmed": "You have selected {lang}!",
        "not_subscribed": "Please join the channel!",
        "subscription_confirmed": "Subscription confirmed! Proceeding to main menu.",
        "main_menu": "Main Menu:",
        "game_created": "New game created! Invite your friend using this link:\n{invite_link}",
        "game_start_info": "Game started! Your opponent is {opponent}.\nPlease enter your 4-digit secret number.",
        "prompt_secret": "Please enter your 4-digit secret number.",
        "secret_set": "Your secret number has been saved.",
        "your_turn": "It's your turn now. Please enter your guess.",
        "opponent_turn": "It's your opponent's turn.",
        "turn_notification": "It's now {player}'s turn.",
        "invalid_input": "❌ Please enter a 4-digit number.",
        "bulls_cows": "{bulls} correct ✅.\n Try again when it's your turn.",
        "win": "Congratulations! You won in {attempts} attempts!\nOpponent's secret: {secret}\nIf you want to play again, press /start.",
        "lost": "Unfortunately, you lost.\nYour opponent's secret number: {secret} \nIf you want to play again, press /start.",
        "surrendered_self": "You surrendered. You lost.",
        "surrendered_opponent": "Your opponent surrendered. You win.",
        "game_cancelled": "The new game has been cancelled because the second player did not join.",
        "not_your_turn" : "It's not your turn❗️❗️❗️",
        "new_game_button": "🎮 New Game",
        "settings_button": "⚙ Settings",
        "subscribe_button": "✅ Subscribed",
        "finish_game_button": "🏁 Finish Game",
        "send_message_button": "✉️ Send Message",
        "cancel_send_button": "❌ Cancel",
        "game_rules_button": "📜 Game Rules",
        "surrender_confirm" : "Are you sure you want to surrender?",
        "game_rules": "Game Rules: In Bulls & Cows, each guess reveals the number of correct digits and their positions. The winner is the one who completely guesses the secret number."
    },
    "kk": {
        "choose_language": "Tildi saylań :",
        "subscribe": "Ótinish, kanalǵa jazılıw bolıń :[Kanal](https://t.me/samancikschannel) ",
        "lang_confirmed": "Siz {lang} tańladingiz! ",
        "not_subscribed": "Ótinish, kanalımızǵa jazılıw bolıń! ",
        "subscription_confirmed": "Siz tabıslı jazılıw boldıńız!",
        "main_menu": "Bas menyu :",
        "game_created": "Jańa oyın jaratıldı! Dosıńızdı usınıs etiń :\n{invite_link}",
        "game_start_info": "Oyın baslandı! Raxibińiz: {opponent}. \nTórtew cifrlı jasırın nomerińizdi kiritiń. ",
        "prompt_secret": "Ótinish, tórtew cifrlı jasırın nomerińizdi kiriting",
        "secret_set": "Sizdiń jasırın nomerińiz saqlanǵan. ",
        "your_turn": "Házir sizdiń gezegińiz Óz prognozıńızdı jibering",
        "opponent_turn": "Endi qarsılastıń gezegi bolıp tabıladı. ",
        "turn_notification": "Házir {player}ning gezeginde turıpsız",
        "invalid_input": "❌ Ótinish, tórtew cifrlı sannı kiriting",
        "bulls_cows": "{bulls} ewi durıs ✅. \nSizdiń gezegińiz kelgeninde taǵı urınıp kóriń.",
        "win": "Jeńilpaz bolǵanińız menen qutlıqlawlaymız! Siz {attempts} urınıslar menen jeńimpaz boldıńız! \nQarsılasńızdıń sırlı nomeri: {secret}\nTaǵı oynawdı qaleseńız /start basıń",
        "lost": " Ókiniw menen aytamız, siz jeńiliske ushıraǵan boldıńız. \nQarsılasńızdıń sırlı nomeri: {secret}\nTaǵı oynawdı qaleseńız /start basıń",
        "surrendered_self": "Siz taslim boldıńız Siz jeńiliske ushıraǵan boldıngiz",
        "surrendered_opponent": "Sizdiń raxibińiz taslim boldı Siz uttıngiz",
        "game_cancelled": "Jańa oyın biykar etildi, sebebi ekinshi oyınshı qatnasmadi. ",
        "not_your_turn": "Sizdiń gezegińiz emes ❗️❗️❗️",
        "new_game_button": "🎮 Jańa oyın",
        "settings_button": " ⚙  Sazlamalar",
        "subscribe_button": " ✅ Jazılıw boldım",
        "finish_game_button": " 🏁 Oyındı tamamlaw",
        "send_message_button": "✉️ Xabar jiberiw",
        "cancel_send_button": "❌ Bıykarlaw",
        "game_rules_button": "📜 Oyın qaǵıydalari",
        "surrender_confirm" : "Taslim bolıwdı qáleytuǵinińizga isenimińiz kámilma?",
        "game_rules": " Oyın qaǵıydaları :Bulls & Cows oyınında hár bir urınıwda tuwrı nomerler sanı hám olardıń pozitsiyalari anıqlanadı  Sırlı nomerdi tolıq anıqlaǵan kisi jeńimpaz esaplanadı",
 }
}





def get_message(user_id, key):
    lang = user_data.get(user_id, {}).get("language", "uz")
    return MESSAGES.get(lang, MESSAGES["uz"]).get(key, "")










def get_main_menu(user_id):
    lang = user_data.get(user_id, {}).get("language", "uz")
    keyboard = [
        [InlineKeyboardButton(MESSAGES[lang].get("new_game_button", "🎮 New Game"), callback_data="new_game")],
        [InlineKeyboardButton(MESSAGES[lang].get("settings_button", "⚙ Settings"), callback_data="settings")],
        [InlineKeyboardButton(MESSAGES[lang].get("game_rules_button", "📜 Game Rules"), callback_data="game_rules")]
    ]
    return InlineKeyboardMarkup(keyboard)









def get_game_controls(user_id):
    lang = user_data.get(user_id, {}).get("language", "uz")
    keyboard = [
        [InlineKeyboardButton(MESSAGES[lang].get("finish_game_button", "🏁 Finish Game"), callback_data="finish_game"),
         InlineKeyboardButton(MESSAGES[lang].get("send_message_button", "✉️ Send Message"), callback_data="send_message")]
    ]
    return InlineKeyboardMarkup(keyboard)










def find_game(user_id):
    for gid, game in games.items():
        if game["status"] != FINISHED and (game["player1"] == user_id or game["player2"] == user_id):
            return gid, game
    return None, None












async def game_rules(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    lang = user_data.get(user_id, {}).get("language", "uz")
    rules_text = MESSAGES[lang].get("game_rules", "Game rules not defined.")
    await query.answer()
    await query.edit_message_text(text=rules_text, reply_markup=get_main_menu(user_id))












async def finish_game(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    gid, game = find_game(user_id)
    if not game:
        await query.answer("Faol o'yin topilmadi.", show_alert=True)
        return
    lang = user_data.get(user_id, {}).get("language", "uz")
    keyboard = [
        [
            InlineKeyboardButton(MESSAGES[lang].get("surrender_yes", "Yes"), callback_data="surrender_yes"),
            InlineKeyboardButton(MESSAGES[lang].get("surrender_no", "No"), callback_data="surrender_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await query.edit_message_text(
            text=MESSAGES[lang].get("surrender_confirm", "Are you sure you want to surrender?"),
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error("Error editing message in finish_game: %s", e)
        await query.answer("Xabar yangilanishida xatolik yuz berdi.", show_alert=True)

async def surrender_yes(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    gid, game = find_game(user_id)
    if not game:
        await query.answer("Faol o'yin topilmadi.", show_alert=True)
        return
    user_lang = user_data.get(user_id, {}).get("language", "uz")
    surrender_self = MESSAGES[user_lang].get("surrendered_self", "You surrendered. You lost.")
    await query.answer(surrender_self, show_alert=True)
    game["status"] = FINISHED
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.error("Error removing buttons in surrender_yes: %s", e)
    await context.bot.send_message(
        chat_id=user_id,
        text=get_message(user_id, "main_menu"),
        reply_markup=get_main_menu(user_id)
    )
    opponent_id = game["player2"] if user_id == game["player1"] else game["player1"]
    if opponent_id:
        opponent_lang = user_data.get(opponent_id, {}).get("language", "uz")
        surrender_opponent = MESSAGES[opponent_lang].get("surrendered_opponent", "Your opponent surrendered. You win.")

        await context.bot.send_message(opponent_id, surrender_opponent)
        await context.bot.send_message(opponent_id, get_message(opponent_id, "main_menu"), reply_markup=get_main_menu(opponent_id))


async def surrender_no(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    lang = user_data.get(user_id, {}).get("language", "uz")
    gid, game = find_game(user_id)
    if game:
        if game["turn"] == user_id:
            msg = MESSAGES[lang].get("your_turn", "It's your turn.")
        else:
            msg = MESSAGES[lang].get("opponent_turn", "It's your opponent's turn.")
        try:
            await query.edit_message_text(
                text=msg,
                reply_markup=get_game_controls(user_id)
            )
        except Exception as e:
            logger.error("Error editing message in surrender_no: %s", e)
    else:
        await query.answer("Faol o'yin topilmadi.", show_alert=True)













async def start_handler(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id not in user_data:
        user_data[user.id] = {"first_name": user.first_name}
    if context.args and context.args[0].startswith("invite_"):
        if "language" in user_data[user.id]:
            await invite_join_handler(update, context)
            return
        else:
            user_data[user.id]["invite"] = context.args[0]
            keyboard = [[InlineKeyboardButton(LANGUAGES[lang], callback_data=f"lang_{lang}") for lang in LANGUAGES]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Tilni tanlang / Выберите язык / Choose a language:", reply_markup=reply_markup)
            return
    gid, game = find_game(user.id)
    if game and game["status"] in [PLAYING, WAITING_FOR_SECRET]:
        lang = user_data[user.id].get("language", "uz")
        btn_yes = InlineKeyboardButton(MESSAGES[lang].get("surrender_yes", "Yes"), callback_data="surrender_yes")
        btn_no = InlineKeyboardButton(MESSAGES[lang].get("surrender_no", "No"), callback_data="surrender_no")
        keyboard = [[btn_yes, btn_no]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(MESSAGES[lang].get("surrender_confirm", "Are you sure you want to surrender?"), reply_markup=reply_markup)
        return
    if "language" in user_data[user.id]:
        if game and game["player1"] == user.id and game["status"] == WAITING_FOR_PLAYERS:
            game["status"] = FINISHED
            cancel_msg = get_message(user.id, "game_cancelled")
            await update.message.reply_text(cancel_msg)
        if not user_data[user.id].get("subscribed", False):
            lang = user_data[user.id]["language"]
            subscribe_text = MESSAGES[lang]["subscribe"]
            btn_sub = InlineKeyboardButton(MESSAGES[lang].get("subscribe_button", "✅ A'zo bo'ldim"), callback_data="check_subscription")
            reply_markup = InlineKeyboardMarkup([[btn_sub]])
            await update.message.reply_text(subscribe_text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await update.message.reply_text(get_message(user.id, "main_menu"), reply_markup=get_main_menu(user.id))
    else:
        keyboard = [[InlineKeyboardButton(LANGUAGES[lang], callback_data=f"lang_{lang}") for lang in LANGUAGES]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Tilni tanlang / Выберите язык / Choose a language:", reply_markup=reply_markup)











async def set_language_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    lang_code = query.data.split("_")[1]
    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"first_name": query.from_user.first_name}
    user_data[user_id]["language"] = lang_code
    user_data[user_id]["subscribed"] = False
    confirm_text = MESSAGES[lang_code]["lang_confirmed"].format(lang=LANGUAGES[lang_code])
    await query.answer(confirm_text)
    subscribe_text = MESSAGES[lang_code]["subscribe"]
    btn_sub = InlineKeyboardButton(MESSAGES[lang_code].get("subscribe_button", "✅ A'zo bo'ldim"), callback_data="check_subscription")
    reply_markup = InlineKeyboardMarkup([[btn_sub]])
    await query.edit_message_text(text=subscribe_text, parse_mode="Markdown", reply_markup=reply_markup)




async def change_language_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    lang_code = query.data.split("_")[1]
    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"first_name": query.from_user.first_name}
    user_data[user_id]["language"] = lang_code
    confirm_text = MESSAGES[lang_code]["lang_confirmed"].format(lang=LANGUAGES[lang_code])
    await query.answer(confirm_text)
    await query.edit_message_text(text=get_message(user_id, "main_menu"), reply_markup=get_main_menu(user_id))





async def settings_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    keyboard = [[InlineKeyboardButton(LANGUAGES[lang], callback_data=f"setlang_{lang}")] for lang in LANGUAGES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=MESSAGES[user_data[user_id]["language"]].get("choose_language", "Tilni tanlang:"), reply_markup=reply_markup)




async def check_subscription_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    channel_username = "@samancikschannel"
    try:
        chat_member = await context.bot.get_chat_member(channel_username, user_id)
        logger.info("User %s chat_member.status: %s", user_id, chat_member.status)
        if chat_member.status in ["member", "creator", "administrator", "restricted"]:
            user_data[user_id]["subscribed"] = True
            await query.answer(get_message(user_id, "subscription_confirmed"), show_alert=True)
            if "invite" in user_data[user_id]:
                invite_arg = user_data[user_id].pop("invite")
                context.args = [invite_arg]
                await invite_join_handler(update, context)
            else:
                await query.edit_message_text(text=get_message(user_id, "main_menu"), reply_markup=get_main_menu(user_id))
        else:
            await query.answer(get_message(user_id, "not_subscribed"), show_alert=True)
    except Exception as e:
        logger.error("Kanal a'zoligini tekshirishda xato: %s", e)
        await query.answer("Kanal a'zoligini tekshirishda xato yuz berdi!", show_alert=True)


















async def invite_handler(update: Update, context: CallbackContext):
    await invite_join_handler(update, context)






async def new_game_handler(update: Update, context: CallbackContext):
    global game_counter
    query = update.callback_query
    user_id = query.from_user.id
    _, existing_game = find_game(user_id)
    if existing_game:
        await query.answer("Siz allaqachon faol o'yinda ishtirok etmoqdasiz!", show_alert=True)
        return
    game_id = str(game_counter)
    game_counter += 1
    games[game_id] = {
        "player1": user_id,
        "player2": None,
        "secret1": None,
        "secret2": None,
        "status": WAITING_FOR_PLAYERS,
        "turn": None,
        "attempts": {},
    }
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=invite_{game_id}"
    text = MESSAGES[user_data[user_id]["language"]]["game_created"].format(invite_link=invite_link)
    await query.edit_message_text(text=text)






async def invite_join_handler(update: Update, context: CallbackContext):
    user = update.effective_user
    if context.args and context.args[0].startswith("invite_"):
        invite_arg = context.args[0]
    elif "invite" in user_data.get(user.id, {}):
        invite_arg = user_data[user.id].pop("invite")
    else:
        return

    game_id = invite_arg.split("_")[1]
    if game_id not in games:
        await context.bot.send_message(user.id, "⚠️ O'yin topilmadi!")
        return

    game = games[game_id]
    if game["player2"] is not None:
        await context.bot.send_message(user.id, "⚠️ Bu o'yin allaqachon boshlangan!")
        return

    game["player2"] = user.id
    game["status"] = WAITING_FOR_SECRET
    game["attempts"][game["player1"]] = 0
    game["attempts"][game["player2"]] = 0

    player1_name = user_data.get(game["player1"], {}).get("first_name", "Opponent")
    player2_name = user_data.get(user.id, {}).get("first_name", "Opponent")

    msg_for_player1 = MESSAGES[user_data[game["player1"]]["language"]].get(
        "game_start_info",
        "O'yin boshlandi!"
    ).format(opponent=player2_name)
    
    msg_for_player2 = MESSAGES[user_data[user.id]["language"]].get(
        "game_start_info",
        "O'yin boshlandi!"
    ).format(opponent=player1_name)

    await context.bot.send_message(game["player1"], msg_for_player1)
    await context.bot.send_message(user.id, msg_for_player2)







async def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()
    





    if user_id in pending_send:
        gid = pending_send[user_id]
        game = games.get(gid)
        if not game or game["status"] != PLAYING:
            await update.message.reply_text("Faol o'yin topilmadi yoki o'yin PLAYING holatida emas.")
            del pending_send[user_id]
            return
        opponent_id = game["player2"] if user_id == game["player1"] else game["player1"]
        await context.bot.send_message(opponent_id, f"{user.first_name} sizga xabar yubordi: {text}")
        await update.message.reply_text("Xabar yuborildi.", reply_markup=get_game_controls(user_id))
        del pending_send[user_id]
        return

    gid, game = find_game(user_id)
    if not game:
        await update.message.reply_text("Hozirda faol o'yin yo'q. Yangi o'yin boshlash uchun /start buyrug'ini bosing.")
        return







    if game["status"] == WAITING_FOR_SECRET:
        if len(text) != 4 or not text.isdigit():
            await update.message.reply_text(get_message(user_id, "invalid_input"))
            return
        if user_id == game["player1"]:
            if game["secret1"] is None:
                game["secret1"] = text
                await update.message.reply_text(get_message(user_id, "secret_set"))
            else:
                await update.message.reply_text("Siz allaqachon secret raqamingizni kiritgansiz.")
        elif user_id == game["player2"]:
            if game["secret2"] is None:
                game["secret2"] = text
                await update.message.reply_text(get_message(user_id, "secret_set"))
            else:
                await update.message.reply_text("Siz allaqachon secret raqamingizni kiritgansiz.")
        logger.info("Game %s: secret1=%s, secret2=%s", gid, game["secret1"], game["secret2"])
        if game["secret1"] is not None and game["secret2"] is not None:
            game["status"] = PLAYING
            game["turn"] = game["player1"]  # Player1 boshlaydi
            msg_player1 = MESSAGES[user_data[game["player1"]]["language"]].get("your_turn", "Endi sizning navbatingiz.")
            msg_player2 = MESSAGES[user_data[game["player2"]]["language"]].get("opponent_turn", "Endi raqibingizning navbati.")
            await context.bot.send_message(game["player1"], msg_player1, reply_markup=get_game_controls(game["player1"]))
            await context.bot.send_message(game["player2"], msg_player2)
        return




    if game["status"] == PLAYING:
        if user_id != game["turn"]:
            await update.message.reply_text(get_message(user_id, "not_your_turn"))
            return
        if len(text) != 4 or not text.isdigit():
            await update.message.reply_text(get_message(user_id, "invalid_input"))
            return

        game["attempts"][user_id] += 1
        opponent_id = game["player2"] if user_id == game["player1"] else game["player1"]
        if user_id == game["player1"]:
            win_secret = game["secret2"]
            lose_secret = game["secret1"]
        else:
            win_secret = game["secret1"]
            lose_secret = game["secret2"]

        bulls = sum(s == g for s, g in zip(win_secret, text))
        cows = sum(min(win_secret.count(d), text.count(d)) for d in set(text)) - bulls

        if bulls == 4:
            win_msg = MESSAGES[user_data[user_id]["language"]]["win"].format(attempts=game["attempts"][user_id], secret=win_secret)
            await update.message.reply_text(win_msg)
            lose_msg = MESSAGES[user_data[opponent_id]["language"]]["lost"].format(secret=lose_secret)
            await context.bot.send_message(opponent_id, lose_msg)
            game["status"] = FINISHED
        else:
            result_msg = MESSAGES[user_data[user_id]["language"]]["bulls_cows"].format(bulls=bulls, cows=cows)
            await update.message.reply_text(result_msg, reply_markup=get_game_controls(user_id))
            game["turn"] = opponent_id
            p1_msg = (MESSAGES[user_data[game["player1"]]["language"]].get("your_turn", "Endi sizning navbatingiz.")
                      if game["turn"] == game["player1"] else
                      MESSAGES[user_data[game["player1"]]["language"]].get("opponent_turn", "Endi raqibingizning navbati."))
            p2_msg = (MESSAGES[user_data[game["player2"]]["language"]].get("your_turn", "Endi sizning navbatingiz.")
                      if game["turn"] == game["player2"] else
                      MESSAGES[user_data[game["player2"]]["language"]].get("opponent_turn", "Endi raqibingizning navbati."))
            await context.bot.send_message(game["player1"], p1_msg)
            await context.bot.send_message(game["player2"], p2_msg)
        return









async def send_message_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    gid, game = find_game(user_id)
    if not game or game["status"] != PLAYING:
        await query.answer("Faol o'yin PLAYING holatida emas.", show_alert=True)
        return
    pending_send[user_id] = gid
    lang = user_data.get(user_id, {}).get("language", "uz")
    cancel_text = MESSAGES[lang].get("cancel_send_button", "❌ Cancel")
    keyboard = [[InlineKeyboardButton(cancel_text, callback_data="cancel_send")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Yubormoqchi bo'lgan xabaringizni yozing:", reply_markup=reply_markup)
    await query.answer("Xabar yozishni boshlang.", show_alert=True)










async def cancel_send_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id in pending_send:
        del pending_send[user_id]
        await query.answer("Xabar yuborish bekor qilindi.", show_alert=True)
        await query.edit_message_text(text=get_message(user_id, "main_menu"), reply_markup=get_main_menu(user_id))
    else:
        await query.answer("Yuborilayotgan xabar mavjud emas.", show_alert=True)









async def start_in_game(update: Update, context: CallbackContext):
    user = update.effective_user
    gid, game = find_game(user.id)
    if game and game["status"] in [PLAYING, WAITING_FOR_SECRET]:
        lang = user_data[user.id].get("language", "uz")
        btn_yes = InlineKeyboardButton(MESSAGES[lang].get("surrender_yes", "Yes"), callback_data="surrender_yes")
        btn_no = InlineKeyboardButton(MESSAGES[lang].get("surrender_no", "No"), callback_data="surrender_no")
        keyboard = [[btn_yes, btn_no]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(MESSAGES[lang].get("surrender_confirm", "Are you sure you want to surrender?"), reply_markup=reply_markup)
    else:
        await update.message.reply_text("Faol o'yin topilmadi.")






if __name__ == "__main__":
    TOKEN = "7701613822:AAFEOPYnLokpQpF-mu73edLbH5e7PINiLMo"
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("start_in_game", start_in_game))
    app.add_handler(CommandHandler("invite", invite_handler))
    app.add_handler(CallbackQueryHandler(set_language_handler, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(change_language_handler, pattern="^setlang_"))
    app.add_handler(CallbackQueryHandler(check_subscription_handler, pattern="^check_subscription"))
    app.add_handler(CallbackQueryHandler(new_game_handler, pattern="^new_game"))
    app.add_handler(CallbackQueryHandler(settings_handler, pattern="^settings"))
    app.add_handler(CallbackQueryHandler(game_rules, pattern="^game_rules"))
    app.add_handler(CallbackQueryHandler(finish_game, pattern="^finish_game"))
    app.add_handler(CallbackQueryHandler(send_message_button, pattern="^send_message$"))
    app.add_handler(CallbackQueryHandler(cancel_send_callback, pattern="^cancel_send$"))
    app.add_handler(CallbackQueryHandler(surrender_yes, pattern="^surrender_yes$"))
    app.add_handler(CallbackQueryHandler(surrender_no, pattern="^surrender_no$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
