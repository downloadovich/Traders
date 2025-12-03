import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
import os
from datetime import datetime
import json
import re

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8303374569:AAFxxm5BcHVA894hMFPvIbuYS-lsPLorc0U"
GROUP_CHAT_ID = "-4667941192"  

# ID администратора (ваш Telegram ID)
ADMIN_ID = 1855791379  

# ========== ДОБАВЛЕНО: УЛУЧШЕННАЯ РЕФЕРАЛЬНАЯ СИСТЕМА ==========
# Статистика реферальных ссылок
REF_STATS_FILE = "ref_stats.json"

# Начальные ссылки (можно удалить)
INITIAL_STATS = {
    "traffic1": {"name": "Трафик 1", "clicks": 0, "users": [], "started": False, "created": datetime.now().isoformat()},
    "traffic2": {"name": "Трафик 2", "clicks": 0, "users": [], "started": False, "created": datetime.now().isoformat()},
    "traffic3": {"name": "Трафик 3", "clicks": 0, "users": [], "started": False, "created": datetime.now().isoformat()},
    "traffic4": {"name": "Трафик 4", "clicks": 0, "users": [], "started": False, "created": datetime.now().isoformat()}
}

ref_stats = {}

def save_ref_stats():
    """Сохраняет статистику в файл"""
    try:
        with open(REF_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(ref_stats, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Статистика ссылок сохранена")
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

def load_ref_stats():
    """Загружает статистику из файла"""
    global ref_stats
    try:
        with open(REF_STATS_FILE, 'r', encoding='utf-8') as f:
            ref_stats = json.load(f)
        logger.info(f"Загружено {len(ref_stats)} реферальных ссылок")
    except FileNotFoundError:
        logger.info("Файл статистики не найден, создаем начальные ссылки")
        ref_stats = INITIAL_STATS.copy()
        save_ref_stats()
    except Exception as e:
        logger.error(f"Ошибка загрузки статистики: {e}")
        ref_stats = INITIAL_STATS.copy()
        save_ref_stats()

def get_next_traffic_number():
    """Получает следующий номер для новой ссылки"""
    traffic_numbers = []
    for link_id in ref_stats.keys():
        # Ищем номера в названиях типа "traffic1", "traffic2" и т.д.
        match = re.search(r'traffic(\d+)', link_id)
        if match:
            traffic_numbers.append(int(match.group(1)))
    
    # Также ищем в названиях ссылок
    for data in ref_stats.values():
        match = re.search(r'Трафик\s*(\d+)', data['name'])
        if match:
            traffic_numbers.append(int(match.group(1)))
    
    if not traffic_numbers:
        return 1
    return max(traffic_numbers) + 1

def create_new_traffic_link(custom_name=None):
    """Создает новую реферальную ссылку"""
    next_num = get_next_traffic_number()
    
    if custom_name:
        # Используем кастомное имя
        link_id = f"traffic_{next_num}"
        name = custom_name
    else:
        # Стандартное имя "Трафик N"
        link_id = f"traffic{next_num}"
        name = f"Трафик {next_num}"
    
    # Создаем новую запись
    ref_stats[link_id] = {
        "name": name,
        "clicks": 0,
        "users": [],
        "started": False,
        "started_count": 0,
        "created": datetime.now().isoformat(),
        "custom": custom_name is not None
    }
    
    save_ref_stats()
    return link_id, name

async def send_ref_links_to_admin(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет все реферальные ссылки администратору"""
    try:
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        
        if not ref_stats:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text="📭 Нет созданных реферальных ссылок.\n\n"
                     "Создайте новую ссылку командой:\n"
                     "/newref - создать ссылку 'Трафик N'\n"
                     "/newref [название] - создать ссылку с кастомным названием"
            )
            return
        
        links_message = f"🔗 **Реферальные ссылки ({len(ref_stats)} шт.):**\n\n"
        
        for link_id, data in ref_stats.items():
            url = f"https://t.me/{bot_username}?start={link_id}"
            custom_mark = " ✏️" if data.get('custom', False) else ""
            links_message += f"**{data['name']}**{custom_mark}\n`{url}`\n"
            links_message += f"📊 Переходов: {data['clicks']} | ✅ Начали: {data.get('started_count', 0)}\n\n"
        
        links_message += (
            "📋 **Команды управления:**\n"
            "/newref - создать ссылку 'Трафик N'\n"
            "/newref [название] - создать ссылку с кастомным названием\n"
            "/refstats - статистика\n"
            "/refexport - детальная статистика\n"
            "/refreset [id] - сбросить статистику ссылки\n"
            "/refdelete [id] - удалить ссылку\n"
            "/reflist - список ссылок\n"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=links_message,
            parse_mode="Markdown"
        )
        logger.info(f"Отправлено {len(ref_stats)} реферальных ссылок администратору")
    except Exception as e:
        logger.error(f"Ошибка отправки ссылок админу: {e}")

async def handle_newref_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание новой реферальной ссылки"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Эта команда только для администратора.")
        return
    
    try:
        # Проверяем аргументы
        custom_name = None
        if context.args:
            custom_name = " ".join(context.args)
            if len(custom_name) > 50:
                await update.message.reply_text("❌ Название слишком длинное (макс. 50 символов)")
                return
        
        # Создаем новую ссылку
        link_id, name = create_new_traffic_link(custom_name)
        
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        url = f"https://t.me/{bot_username}?start={link_id}"
        
        # Отправляем подтверждение
        if custom_name:
            message = f"✅ **Создана новая реферальная ссылка:**\n\n**Название:** {name}\n**ID:** `{link_id}`\n\n**Ссылка:**\n`{url}`"
        else:
            message = f"✅ **Создана новая реферальная ссылка:**\n\n**Название:** {name}\n**ID:** `{link_id}`\n\n**Ссылка:**\n`{url}`"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
        # Показываем обновленный список
        await send_ref_links_to_admin(context)
        
    except Exception as e:
        logger.error(f"Ошибка создания ссылки: {e}")
        await update.message.reply_text("❌ Ошибка при создании ссылки")

async def handle_reflist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список всех ссылок с ID"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        if not ref_stats:
            await update.message.reply_text("📭 Нет созданных реферальных ссылок.")
            return
        
        list_text = "📋 **Список реферальных ссылок:**\n\n"
        
        for i, (link_id, data) in enumerate(ref_stats.items(), 1):
            custom_mark = " ✏️" if data.get('custom', False) else ""
            list_text += f"{i}. **{data['name']}**{custom_mark}\n"
            list_text += f"   🆔 `{link_id}`\n"
            list_text += f"   📊 Переходов: {data['clicks']} | ✅ Начали: {data.get('started_count', 0)}\n"
            list_text += f"   📅 Создана: {data.get('created', 'N/A')[:10]}\n\n"
        
        list_text += "\n💡 Используйте ID для команд:\n/refreset [id] - сбросить статистику\n/refdelete [id] - удалить ссылку"
        
        await update.message.reply_text(list_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка показа списка: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка")

async def handle_refreset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сброс статистики конкретной ссылки или всех"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        if not context.args:
            # Сброс всех ссылок
            for link_id in ref_stats:
                ref_stats[link_id]["clicks"] = 0
                ref_stats[link_id]["users"] = []
                ref_stats[link_id]["started"] = False
                ref_stats[link_id]["started_count"] = 0
            
            save_ref_stats()
            await update.message.reply_text("✅ Статистика всех ссылок сброшена!")
            return
        
        # Сброс конкретной ссылки
        link_id = context.args[0]
        if link_id in ref_stats:
            ref_stats[link_id]["clicks"] = 0
            ref_stats[link_id]["users"] = []
            ref_stats[link_id]["started"] = False
            ref_stats[link_id]["started_count"] = 0
            
            save_ref_stats()
            await update.message.reply_text(f"✅ Статистика ссылки '{ref_stats[link_id]['name']}' сброшена!")
        else:
            await update.message.reply_text(f"❌ Ссылка с ID '{link_id}' не найдена.")
            
    except Exception as e:
        logger.error(f"Ошибка сброса статистики: {e}")
        await update.message.reply_text("❌ Ошибка при сбросе статистики")

async def handle_refdelete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление реферальной ссылки"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        if not context.args:
            await update.message.reply_text("❌ Укажите ID ссылки для удаления.\nПример: /refdelete traffic1")
            return
        
        link_id = context.args[0]
        if link_id in ref_stats:
            link_name = ref_stats[link_id]['name']
            del ref_stats[link_id]
            save_ref_stats()
            await update.message.reply_text(f"✅ Ссылка '{link_name}' удалена!")
        else:
            await update.message.reply_text(f"❌ Ссылка с ID '{link_id}' не найдена.")
            
    except Exception as e:
        logger.error(f"Ошибка удаления ссылки: {e}")
        await update.message.reply_text("❌ Ошибка при удалении ссылки")

async def handle_refstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /refstats - статистика реферальных ссылок (только для админа)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Эта команда только для администратора.")
        return
    
    try:
        if not ref_stats:
            await update.message.reply_text("📭 Нет созданных реферальных ссылок.")
            return
        
        stats_text = "📊 **Статистика реферальных ссылок:**\n\n"
        
        for link_id, data in ref_stats.items():
            bot_info = await context.bot.get_me()
            bot_username = bot_info.username
            url = f"t.me/{bot_username}?start={link_id}"
            
            started_count = data.get('started_count', 0)
            
            stats_text += (
                f"**{data['name']}**\n"
                f"🔗 {url}\n"
                f"📊 Переходов: {data['clicks']}\n"
                f"✅ Начали анкету: {started_count}\n"
                f"👥 Уникальных: {len(data['users'])}\n"
                f"---\n"
            )
        
        # Итоговая статистика
        total_clicks = sum(data['clicks'] for data in ref_stats.values())
        total_started = sum(data.get('started_count', 0) for data in ref_stats.values())
        total_users = sum(len(data['users']) for data in ref_stats.values())
        
        stats_text += (
            f"\n**ИТОГО ({len(ref_stats)} ссылок):**\n"
            f"📊 Всего переходов: {total_clicks}\n"
            f"✅ Начали анкету: {total_started}\n"
            f"👥 Всего пользователей: {total_users}"
        )
        
        await update.message.reply_text(stats_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка показа статистики: {e}")
        await update.message.reply_text("❌ Ошибка при получении статистики")

async def handle_refexport_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экспорт детальной статистики"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        if not ref_stats:
            await update.message.reply_text("📭 Нет созданных реферальных ссылок.")
            return
        
        export_text = "📋 **Детальная статистика по всем ссылкам:**\n\n"
        
        for link_id, data in ref_stats.items():
            export_text += f"=== {data['name']} (ID: {link_id}) ===\n"
            export_text += f"Переходов: {data['clicks']}\n"
            export_text += f"Начали анкету: {data.get('started_count', 0)}\n"
            export_text += f"Создана: {data.get('created', 'N/A')}\n\n"
            
            if data['users']:
                export_text += "Пользователи:\n"
                for i, user in enumerate(data['users'], 1):
                    started = "✅" if user.get('started', False) else "❌"
                    timestamp = user.get('timestamp', 'N/A')
                    export_text += f"{i}. @{user.get('username', 'без_username')} {started} ({timestamp})\n"
            else:
                export_text += "Нет пользователей\n"
            
            export_text += "\n" + "-"*40 + "\n\n"
        
        # Если текст слишком длинный, разбиваем на части
        if len(export_text) > 4000:
            parts = [export_text[i:i+4000] for i in range(0, len(export_text), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode="Markdown")
        else:
            await update.message.reply_text(export_text, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Ошибка экспорта статистики: {e}")
        await update.message.reply_text("❌ Ошибка при экспорте статистики")
# ========== КОНЕЦ ДОБАВЛЕНИЙ ==========

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
        # Добавляем информацию о трафике
        traffic_info = ""
        if 'traffic_source' in user_data:
            traffic_info = f"📊 Источник трафика: {user_data['traffic_source']}\n"
        
        message_text = f"""
🆕 НОВАЯ АНКЕТА

👤 Пользователь: @{user_data['username']}
🆔 ID: {user_data['user_id']}
📅 Дата: {user_data['timestamp']}
{traffic_info}
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
    
    # ========== ДОБАВЛЕНО: Обработка реферальных ссылок ==========
    ref_link_id = None
    traffic_source = None
    
    if context.args and context.args[0] in ref_stats:
        ref_link_id = context.args[0]
        traffic_source = ref_stats[ref_link_id]["name"]
        
        # Увеличиваем счётчик кликов
        ref_stats[ref_link_id]["clicks"] += 1
        
        # Проверяем, есть ли пользователь уже в списке
        user_exists = False
        for user_data in ref_stats[ref_link_id]["users"]:
            if user_data.get("id") == user_id:
                user_exists = True
                break
        
        # Добавляем пользователя если его нет
        if not user_exists:
            ref_stats[ref_link_id]["users"].append({
                "id": user_id,
                "username": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "started": False,
                "traffic_source": traffic_source
            })
        
        save_ref_stats()
        logger.info(f"Пользователь {user_id} перешел по ссылке {traffic_source}")
    # ========== КОНЕЦ ДОБАВЛЕНИЙ ==========
    
    # Сохраняем базовую информацию о пользователе
    user_responses[user_id] = {
        'user_id': user_id,
        'username': username,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # ========== ДОБАВЛЕНО: Добавляем источник трафика в данные пользователя ==========
    if traffic_source:
        user_responses[user_id]['traffic_source'] = traffic_source
    
    # ========== ДОБАВЛЕНО: Отмечаем что пользователь начал анкету ==========
    if ref_link_id:
        # Обновляем статус пользователя в статистике
        for user_data in ref_stats[ref_link_id]["users"]:
            if user_data.get("id") == user_id:
                user_data["started"] = True
                user_data["started_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        
        # Увеличиваем счетчик начавших анкету
        if "started_count" not in ref_stats[ref_link_id]:
            ref_stats[ref_link_id]["started_count"] = 0
        ref_stats[ref_link_id]["started_count"] += 1
        
        save_ref_stats()
    # ========== КОНЕЦ ДОБАВЛЕНИЙ ==========
    
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
        
        # Добавляем источник трафика в отправку в группу
        if 'traffic_source' in user_responses[user_id]:
            user_responses[user_id]['traffic_source'] = user_responses[user_id]['traffic_source']
        
        final_text = """Хорошо! Если готовы работать в нашей команде, напишите наставнику:

👨‍🏫 Наставник: @glauzvomma"""
        
        # Отправляем данные в группу
        await send_to_group(context, user_responses[user_id])
        
        await edit_message_photo_or_text(query, "mentor", final_text)

    elif data == "crypto_yes":
        user_responses[user_id]['crypto_answer'] = "Да"
        user_responses[user_id]['status'] = "Опытный пользователь"
        
        # Добавляем источник трафика в отправку в группу
        if 'traffic_source' in user_responses[user_id]:
            user_responses[user_id]['traffic_source'] = user_responses[user_id]['traffic_source']
        
        final_text = """✅ Отлично!

Отправьте наставнику '+' в личные сообщения, он уже получил вашу анкету.

👨‍🏫 Наставник: @glauzvomma"""
        
        # Отправляем данные в группу
        await send_to_group(context, user_responses[user_id])
        
        await edit_message_photo_or_text(query, "success", final_text)

    elif data == "crypto_no":
        user_responses[user_id]['crypto_answer'] = "Нет"
        user_responses[user_id]['status'] = "Новичок"
        
        # Добавляем источник трафика в отправку в группу
        if 'traffic_source' in user_responses[user_id]:
            user_responses[user_id]['traffic_source'] = user_responses[user_id]['traffic_source']
        
        final_text = """📚 Отлично, что у вас нет опыта!

Ищем новичков для обучения с нуля. Отправьте наставнику '+' в личные сообщения.

👨‍🏫 Наставник: @glauzvomma"""
        
        # Отправляем данные в группу
        await send_to_group(context, user_responses[user_id])
        
        await edit_message_photo_or_text(query, "success", final_text)

def main():
    # Загружаем статистику ссылок
    load_ref_stats()
    
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
    
    print("⚠️  НЕ ЗАБУДЬТЕ ЗАМЕНИТЬ:")
    print("   1. GROUP_CHAT_ID на ID вашей группы")
    print("   2. ADMIN_ID на ваш Telegram ID (можно узнать у @userinfobot)")
    print(f"   Текущий ID группы: {GROUP_CHAT_ID}")
    print(f"   Текущий ID админа: {ADMIN_ID}")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ========== ДОБАВЛЕНО: Обработчики для реферальной системы ==========
    # Отправляем ссылки админу при старте бота
    async def on_startup(app):
        await send_ref_links_to_admin(app)
    
    application.add_handler(CommandHandler("newref", handle_newref_command))
    application.add_handler(CommandHandler("reflist", handle_reflist_command))
    application.add_handler(CommandHandler("refstats", handle_refstats_command))
    application.add_handler(CommandHandler("refexport", handle_refexport_command))
    application.add_handler(CommandHandler("refreset", handle_refreset_command))
    application.add_handler(CommandHandler("refdelete", handle_refdelete_command))
    
    application.add_handler(CallbackQueryHandler(handle_button, pattern='^(begin|next|age_yes|age_no|kyc_yes|kyc_no|crypto_yes|crypto_no)$'))
    # ========== КОНЕЦ ДОБАВЛЕНИЙ ==========
    
    # Существующие обработчики
    application.add_handler(CommandHandler("start", start))
    
    print("\n🤖 Бот Prime Traders Team запускается...")
    print("📊 Реферальная система активирована")
    print(f"📁 Загружено {len(ref_stats)} реферальных ссылок")
    
    # Запускаем отправку ссылок при старте
    application.post_init = on_startup
    
    application.run_polling()

if __name__ == "__main__":
    main()
