import logging
import google.generativeai as genai
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# --- Logging konfiguratsiyasi ---
# Dastur xatolarini va holatini kuzatish uchun loglash sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Global o'zgaruvchilar va ma'lumotlar tuzilmasi ---
# Har bir foydalanuvchining til sozlamalarini saqlash uchun lug'at
user_languages = {}
# Har bir foydalanuvchi uchun alohida suhbat sessiyalarini saqlash uchun lug'at
user_chats = {}

# Google Gemini API kaliti
# Eslatma: Kodga API kalitini kiritish xavfsizlik nuqtai nazaridan tavsiya etilmaydi.
GOOGLE_API_KEY = "AIzaSyC_9DmcHNpRyg2EUJcDwXT5Q4GU1Rl-4eM"
genai.configure(api_key=GOOGLE_API_KEY)

# --- Gemini AI modelini ishga tushirish ---
try:
    # Modeldan foydalanishdan oldin uning mavjudligini tekshirish
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    logger.error(f"Gemini AI modeli yuklanmadi: {e}")
    model = None

# --- Bot tugmalari (klaviaturalar) ---
# Til tanlash uchun tugmalar
language_keyboard = [
    [KeyboardButton("O'zbekcha"), KeyboardButton("English")],
    [KeyboardButton("Тоҷикӣ"), KeyboardButton("Русский")]
]
markup_languages = ReplyKeyboardMarkup(language_keyboard, resize_keyboard=True)

# Asosiy menyu uchun tugmalar
main_keyboard = [
    [KeyboardButton("Tilni o'zgartirish"), KeyboardButton("👨‍💻 Admin")]
]
markup_main = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

# Admin bilan bog'lanish uchun inline tugma (URL bilan)
admin_keyboard = [[InlineKeyboardButton("👨‍💻 Admin", url="https://t.me/Ahliddin_Safarov ")]]
markup_admin = InlineKeyboardMarkup(admin_keyboard)


# --- Yordamchi funksiyalar ---
def add_emojis(text: str, lang: str) -> str:
    """Javob matniga mazmuniga mos keladigan smayliklar qo'shadi."""
    emojis = {
        'uz': {
            'xursand': '😄', 'yaxshi': '👍', 'yomon': '👎',
            'tushundim': '💡', 'rahmat': '🙏', 'salom': '👋',
            'ha': '✅', 'yoʻq': '❌', 'sevgi': '❤️', 'muvaffaqiyat': '🏆'
        },
        'en': {
            'happy': '😄', 'good': '👍', 'bad': '👎',
            'understood': '💡', 'thanks': '🙏', 'hello': '👋',
            'yes': '✅', 'no': '❌', 'love': '❤️', 'success': '🏆'
        },
        'tj': {
            'хурсанд': '😄', 'хуб': '👍', 'бад': '👎',
            'фаҳмидам': '💡', 'ташаккур': '🙏', 'салом': '👋',
            'ҳа': '✅', 'не': '❌', 'ишқ': '❤️', 'муваффақият': '🏆'
        },
        'ru': {
            'счастлив': '😄', 'хорошо': '👍', 'плохо': '👎',
            'понял': '💡', 'спасибо': '🙏', 'привет': '👋',
            'да': '✅', 'нет': '❌', 'любовь': '❤️', 'успех': '🏆'
        }
    }

    emoji_list = emojis.get(lang, {})

    for keyword, emoji in emoji_list.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text.lower()):
            text += f" {emoji}"

    return text


# --- Telegram Bot handler funksiyalari ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start buyrug'ini boshqaradi va til tanlash tugmalarini chiqaradi."""
    user = update.effective_user
    user_languages[user.id] = None
    if model:
        user_chats[user.id] = model.start_chat(history=[])

    start_message = f"Assalomu alaykum, {user.mention_html()}!\nIltimos, gaplashish tilini tanlang:"
    await update.message.reply_html(
        add_emojis(start_message, 'uz'),
        reply_markup=markup_languages,
    )


async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reset buyrug'i orqali suhbat tarixini tozalash."""
    user_id = update.effective_user.id
    if user_id in user_chats:
        user_chats[user_id] = model.start_chat(history=[])
        message = "Suhbat tarixi tozalandi. Endi yangi suhbatni boshlashingiz mumkin."
        await update.message.reply_text(add_emojis(message, 'uz'))
    else:
        message = "Suhbat tarixi allaqachon tozalanmoqda."
        await update.message.reply_text(add_emojis(message, 'uz'))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchidan kelgan barcha matnli xabarlarni boshqaradi."""
    user_input = update.message.text
    user = update.effective_user
    user_id = user.id

    if not model:
        message = "Kechirasiz, AI modeli ishlamayapti. Iltimos, keyinroq qayta urinib ko'ring."
        await update.message.reply_text(add_emojis(message, 'uz'))
        return

    # "Admin" yoki "Tilni o'zgartirish" tugmalarini tekshirish
    if user_input == "👨‍💻 Admin":
        message = "Admin bilan bog'lanish:"
        await update.message.reply_text(add_emojis(message, 'uz'), reply_markup=markup_admin)
        return

    if user_input == "Tilni o'zgartirish":
        user_languages[user_id] = None
        message = "Iltimos, gaplashish tilini tanlang:"
        await update.message.reply_text(add_emojis(message, 'uz'), reply_markup=markup_languages)
        return

    # Foydalanuvchi til tanlaganini tekshirish
    if user_id not in user_languages or user_languages[user_id] is None:
        lang_prompts = {
            "O'zbekcha": "Siz O'zbek tilida gapiradigan yordamchi bot siz. Faqat o'zbek tilida javob bering.",
            "English": "You are an English-speaking assistant. Answer only in English.",
            "Тоҷикӣ": "Шумо ёвари бо забони тоҷикӣ ҳастед. Танҳо бо забони тоҷикӣ ҷавоб диҳед.",
            "Русский": "Вы помощник, говорящий на русском языке. Отвечайте только на русском языке."
        }

        selected_lang_key = user_input
        if selected_lang_key in lang_prompts:
            user_languages[user_id] = selected_lang_key

            if user_id in user_chats:
                user_chats[user_id] = model.start_chat(history=[])
            else:
                user_chats[user_id] = model.start_chat(history=[])

            user_chats[user_id].send_message(lang_prompts[selected_lang_key])

            if selected_lang_key == "O'zbekcha":
                message = "Siz bilan o'zbek tilida gaplashaman. Marhamat, nima haqida gaplashamiz do'stim?"
                await update.message.reply_text(add_emojis(message, 'uz'), reply_markup=markup_main)
            elif selected_lang_key == "English":
                message = "I will speak with you in English."
                await update.message.reply_text(add_emojis(message, 'en'), reply_markup=markup_main)
            elif selected_lang_key == "Тоҷикӣ":
                message = "Ман бо шумо бо забони тоҷикӣ гап мезанам."
                await update.message.reply_text(add_emojis(message, 'tj'), reply_markup=markup_main)
            elif selected_lang_key == "Русский":
                message = "Я буду говорить с вами на русском языке."
                await update.message.reply_text(add_emojis(message, 'ru'), reply_markup=markup_main)
        else:
            message = "Iltimos, quyidagi tugmalardan birini tanlang."
            await update.message.reply_text(add_emojis(message, 'uz'))
        return

    # "Yozmoqda..." animatsiyasini yoqish
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])

        lang_key = user_languages[user_id]
        response = user_chats[user_id].send_message(user_input)

        if response.text:
            final_response = add_emojis(response.text, lang_key)
            await update.message.reply_text(final_response)
        elif response.parts and response.parts[0].text:
            final_response = add_emojis(response.parts[0].text, lang_key)
            await update.message.reply_text(final_response)
        else:
            message = "Kechirasiz, javobni qabul qilishda xatolik yuz berdi. Noma'lum format."
            await update.message.reply_text(add_emojis(message, lang_key))

    except Exception as e:
        logger.error(f"Gemini API xatoligi: {e}")
        message = "Afsuski, sizda limit tugadi 24 soat ichida yangi limit beriladi.🥰."
        await update.message.reply_text(add_emojis(message, lang_key))


# --- Asosiy funksiya ---
def main() -> None:
    """Botni ishga tushirish."""
    # Telegram bot token
    import os
TOKEN = os.environ.get("8242646309:AAEoXVrdk-SVyEwW8Pjhyr2shSL_wrKtYp0")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset_chat))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
