import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
import os
from datetime import datetime

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8303374569:AAET1a2LBPruLnDPzIfYiFOFSpFeTSb5Eng"
GROUP_CHAT_ID = "-4667941192"  # ЗАМЕНИТЕ НА ID ВАШЕЙ ГРУППЫ

# Локальные файлы изображений
IMAGES = {
    "welcome": "images/welcome.jpg",
    "company": "images/company.jpg", 
    "age": "images/age.jpg",
    "kyc": "images/kyc.jpg",
    "crypto": "images/crypto.jpg",
    "success": "images/success.jpg",
    "mentor": "images/mentor.jpg"
}

# Хранилище ответов пользователей
user_responses = {}

async def send_to_group(context, user_data):
    """Отправляет данные пользователя в группу"""
    try:
        message_text = f"""
🆕 НОВАЯ АНКЕТА

👤 Пользователь: @{user_data['username']}
🆔 ID: {user_data['user_id']}
📅 Дата: {user_data['timestamp']}

📋 Ответы:
• Возраст 18+: {user_data['age_answer']}
• Опыт с криптой: {user_data['crypto_answer']}
• KYC верификация: {user_data.get('kyc_answer', 'Не применимо')}

📊 Статус: {user_data['status']}
        """
        
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message_text
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки в группу: {e}")
        return False

async def send_photo_or_text(chat_id, context, image_key, text, reply_markup=None):
    """Универсальная функция для отправки фото или текста если фото нет"""
    try:
        # Проверяем длину текста
        if len(text) > 1024:
            # Сначала отправляем фото без подписи
            with open(IMAGES[image_key], 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo
                )
            # Затем отправляем текст с кнопками
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )
            return True
        else:
            # Если текст короткий, отправляем как обычно
            with open(IMAGES[image_key], 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup
                )
            return True
    except FileNotFoundError:
        # Если фото нет, отправляем просто текст
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )
        return False

async def edit_message_photo_or_text(query, image_key, text, reply_markup=None):
    """Универсальная функция для редактирования сообщения с фото или текстом"""
    try:
        # Проверяем длину текста
        if len(text) > 1024:
            # Удаляем старое сообщение
            await query.message.delete()
            
            # Отправляем фото без подписи
            with open(IMAGES[image_key], 'rb') as photo:
                await query.message.reply_photo(photo=photo)
            
            # Отправляем текст с кнопками
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup
            )
            return True
        else:
            # Если текст короткий, редактируем как обычно
            with open(IMAGES[image_key], 'rb') as photo:
                await query.edit_message_media(
                    media=InputMediaPhoto(media=photo, caption=text),
                    reply_markup=reply_markup
                )
            return True
    except FileNotFoundError:
        # Если фото нет, редактируем просто текст
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - начало анкеты"""
    user = update.effective_user
    user_id = user.id
    username = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
    
    # Сохраняем базовую информацию о пользователе
    user_responses[user_id] = {
        'user_id': user_id,
        'username': username,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    greeting_text = """👋 Приветствуем в Prime Traders Team.

Предлагаем для начала познакомиться. Сначала мы расскажем о нас, а после Вам потребуется ответить на несколько вопросов.

Исходя из ваших ответов мы подберем для Вас подходящего наставника.

Приступим?"""
    
    keyboard = [[InlineKeyboardButton("🚀 Приступить", callback_data="begin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем приветствие с фото
    await send_photo_or_text(
        update.message.chat_id,
        context,
        "welcome",
        greeting_text,
        reply_markup
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на инлайн кнопки"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or f"{query.from_user.first_name or ''} {query.from_user.last_name or ''}".strip() or "Без имени"

    # Обновляем информацию о пользователе
    if user_id not in user_responses:
        user_responses[user_id] = {
            'user_id': user_id,
            'username': username,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    if data == "begin":
        company_text = """🏛️ Prime Traders Team – закрытое сообщество

Зарабатываем на разнице курсов: купили дешевле, продали дороже.

Мы ищем новых участников, которых готовы обучить с нуля бесплатно и перевести в основной состав.

🛡️ Безопасность
Сделки на ваших биржах по нашим сигналам. Доверяем информацию, получаем 20% прибыли.

🎓 Обучение
Бесплатное обучение от лучших наставников.

💰 Прибыльность
Лучшие ученики выходят на 100$+ в день через неделю.

Готовы начать?"""
        
        keyboard = [[InlineKeyboardButton("➡️ Далее", callback_data="next")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await edit_message_photo_or_text(query, "company", company_text, reply_markup)

    elif data == "next":
        age_text = "❓ Есть ли вам 18 лет?"
        
        keyboard = [
            [InlineKeyboardButton("✅ ДА", callback_data="age_yes")],
            [InlineKeyboardButton("❌ НЕТ", callback_data="age_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await edit_message_photo_or_text(query, "age", age_text, reply_markup)

    elif data == "age_yes":
        user_responses[user_id]['age_answer'] = "Да"
        user_responses[user_id]['kyc_answer'] = "Не применимо"
        
        crypto_text = "❓ Вы ранее как либо взаимодействовали с криптовалютой?"
        
        keyboard = [
            [InlineKeyboardButton("✅ ДА", callback_data="crypto_yes")],
            [InlineKeyboardButton("❌ НЕТ", callback_data="crypto_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await edit_message_photo_or_text(query, "crypto", crypto_text, reply_markup)

    elif data == "age_no":
        user_responses[user_id]['age_answer'] = "Нет"
        
        kyc_text = """Для регистрации на биржах нужна KYC верификация с документами совершеннолетнего.

Вы можете попросить кого-то о прохождении этой верификации вместо Вас?"""
        
        keyboard = [
            [InlineKeyboardButton("✅ ДА", callback_data="kyc_yes")],
            [InlineKeyboardButton("❌ НЕТ", callback_data="kyc_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await edit_message_photo_or_text(query, "kyc", kyc_text, reply_markup)

    elif data == "kyc_yes":
        user_responses[user_id]['kyc_answer'] = "Да"
        
        crypto_text = "❓ Вы ранее как либо взаимодействовали с криптовалютой?"
        
        keyboard = [
            [InlineKeyboardButton("✅ ДА", callback_data="crypto_yes")],
            [InlineKeyboardButton("❌ НЕТ", callback_data="crypto_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await edit_message_photo_or_text(query, "crypto", crypto_text, reply_markup)

    elif data == "kyc_no":
        user_responses[user_id]['kyc_answer'] = "Нет"
        user_responses[user_id]['crypto_answer'] = "Не задан"
        user_responses[user_id]['status'] = "Не прошел KYC"
        
        final_text = """Хорошо! Если готовы работать в нашей команде, напишите наставнику:

👨‍🏫 Наставник: @glauzvomma"""
        
        # Отправляем данные в группу
        await send_to_group(context, user_responses[user_id])
        
        await edit_message_photo_or_text(query, "mentor", final_text)

    elif data == "crypto_yes":
        user_responses[user_id]['crypto_answer'] = "Да"
        user_responses[user_id]['status'] = "Опытный пользователь"
        
        final_text = """✅ Отлично!

Отправьте наставнику '+' в личные сообщения, он уже получил вашу анкету.

👨‍🏫 Наставник: @glauzvomma"""
        
        # Отправляем данные в группу
        await send_to_group(context, user_responses[user_id])
        
        await edit_message_photo_or_text(query, "success", final_text)

    elif data == "crypto_no":
        user_responses[user_id]['crypto_answer'] = "Нет"
        user_responses[user_id]['status'] = "Новичок"
        
        final_text = """📚 Отлично, что у вас нет опыта!

Ищем новичков для обучения с нуля. Отправьте наставнику '+' в личные сообщения.

👨‍🏫 Наставник: @glauzvomma"""
        
        # Отправляем данные в группу
        await send_to_group(context, user_responses[user_id])
        
        await edit_message_photo_or_text(query, "success", final_text)

def main():
    # Создаем папку для изображений если её нет
    if not os.path.exists('images'):
        os.makedirs('images')
        print("📁 Создана папка 'images'. Добавьте туда ваши изображения:")
        print("   - welcome.jpg")
        print("   - company.jpg") 
        print("   - age.jpg")
        print("   - kyc.jpg")
        print("   - crypto.jpg")
        print("   - success.jpg")
        print("   - mentor.jpg")
    
    print("⚠️  НЕ ЗАБУДЬТЕ ЗАМЕНИТЬ GROUP_CHAT_ID НА ID ВАШЕЙ ГРУППЫ!")
    print("   Текущий ID группы: -1001234567890")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button, pattern='^(begin|next|age_yes|age_no|kyc_yes|kyc_no|crypto_yes|crypto_no)$'))
    
    print("🤖 Бот Prime Traders Team запускается...")
    application.run_polling()

if __name__ == "__main__":
    main()