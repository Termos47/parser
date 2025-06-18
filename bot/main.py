import os
import time
import threading
from dotenv import load_dotenv
import telebot
from loguru import logger
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand

# Импорт наших модулей
from rss_parser import RSSParser
from ai_generator import AIGenerator
from text_templates import get_text

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
OWNER_ID = int(os.getenv('OWNER_ID'))
RSS_URLS = [url.strip() for url in os.getenv('RSS_URLS', '').split(',') if url.strip()]
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))
USE_AI = os.getenv('USE_AI_GENERATION', 'true') == 'true'
MAX_POST_LENGTH = int(os.getenv('MAX_POST_LENGTH', 2000))

bot = telebot.TeleBot(TOKEN)
sent_entries = set()
ai_generator = AIGenerator() if USE_AI else None
parser = RSSParser()

# Настройка логирования
logger.add("rss_bot.log", rotation="10 MB", level="INFO")
logger.info("===== BOT STARTED =====")

# Статистика
stats = {
    'start_time': None,
    'posts_sent': 0,
    'ai_generated': 0,
    'errors': 0,
    'last_check': None,
    'last_post': None,
    'last_ai_error': None
}

# Настройки пользователя
user_settings = {
    'language': 'ru'  # ru - русский
}

class BotController:
    def __init__(self):
        self.is_running = False
        self.worker_thread = None
        self.stop_event = threading.Event()
        
    def start(self):
        if self.is_running:
            return False
            
        self.is_running = True
        self.stop_event.clear()
        self.worker_thread = threading.Thread(target=self.rss_loop, daemon=True)
        self.worker_thread.start()
        stats['start_time'] = datetime.now()
        stats['errors'] = 0
        return True
        
    def stop(self):
        if not self.is_running:
            return False
            
        self.is_running = False
        self.stop_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        return True
        
    def status(self):
        return self.is_running
        
    def rss_loop(self):
        logger.info("RSS loop started")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                stats['last_check'] = datetime.now()
                logger.info(f"Checking {len(RSS_URLS)} sources")
                
                for url in RSS_URLS:
                    if self.stop_event.is_set():
                        break
                        
                    entries = parser.parse_feed(url)
                    for entry in reversed(entries[:10]):  # обрабатываем последние 10 в обратном порядке
                        if self.stop_event.is_set():
                            break
                            
                        if not hasattr(entry, 'link') or entry.link in sent_entries:
                            continue
                            
                        self.process_entry(entry)
                
                # Ожидание с возможностью прерывания
                wait_time = CHECK_INTERVAL
                while wait_time > 0 and not self.stop_event.is_set():
                    sleep_interval = min(10, wait_time)
                    time.sleep(sleep_interval)
                    wait_time -= sleep_interval
                
            except Exception as e:
                logger.error(f"Loop error: {str(e)}")
                stats['errors'] += 1
                time.sleep(30)
                
        logger.info("RSS loop stopped")
    
    def process_entry(self, entry):
        try:
            title = parser.clean_html(entry.title) if hasattr(entry, 'title') else "No title"
            description = parser.clean_html(entry.description) if hasattr(entry, 'description') else ""
            link = entry.link
            
            # Ограничение длины описания
            if len(description) > 1000:
                description = description[:1000] + "..."
            
            # Генерация контента через ИИ
            if USE_AI and ai_generator:
                try:
                    description = ai_generator.generate_content(title, description)
                    stats['ai_generated'] += 1
                except Exception as e:
                    logger.error(f"AI error: {str(e)}")
                    stats['last_ai_error'] = str(e)
                    # В случае ошибки ИИ используем оригинальный текст
            
            # Форматирование сообщения
            image_url = parser.extract_image(entry)
            
            # Обрезаем сообщение, если оно слишком длинное
            message_text = f"<b>{title}</b>\n\n{description}\n\n<a href='{link}'>🔗 Источник</a>"
            if len(message_text) > MAX_POST_LENGTH:
                message_text = message_text[:MAX_POST_LENGTH-100] + "..."
            
            # Отправка
            if image_url:
                bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image_url,
                    caption=message_text,
                    parse_mode='HTML'
                )
            else:
                bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=message_text,
                    parse_mode='HTML'
                )
            
            sent_entries.add(link)
            stats['posts_sent'] += 1
            stats['last_post'] = datetime.now()
            logger.info(f"Posted: {link}")
            
            # Пауза между постами
            time.sleep(1.5)
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            stats['errors'] += 1

# Инициализация контроллера
controller = BotController()

# Создаем клавиатуру с кнопками
def create_reply_keyboard():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Первый ряд - управление
    if controller.status():
        markup.add(
            KeyboardButton(get_text('main_menu', 'pause', user_settings['language'])),
            KeyboardButton(get_text('main_menu', 'stop', user_settings['language'])),
        )
    else:
        markup.add(
            KeyboardButton(get_text('main_menu', 'start', user_settings['language'])),
            KeyboardButton(get_text('main_menu', 'restart', user_settings['language'])),
        )
    
    # Второй ряд - информация
    markup.add(
        KeyboardButton(get_text('main_menu', 'stats', user_settings['language'])),
        KeyboardButton(get_text('main_menu', 'info', user_settings['language'])),
    )
    
    # Третий ряд - помощь и настройки
    markup.add(
        KeyboardButton(get_text('main_menu', 'help', user_settings['language'])),
        KeyboardButton(get_text('main_menu', 'settings', user_settings['language']))
    )
    
    return markup

# Клавиатура настроек
def create_settings_keyboard():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(KeyboardButton(get_text('settings_menu', 'ai_toggle', user_settings['language'])))
    markup.add(KeyboardButton(get_text('settings_menu', 'back', user_settings['language'])))
    return markup

# Регистрируем команды для бокового меню
def setup_bot_commands():
    lang = user_settings['language']
    bot.set_my_commands([
        BotCommand("start", get_text('commands', 'start', lang)),
        BotCommand("help", get_text('commands', 'help', lang)),
        BotCommand("status", get_text('commands', 'status', lang)),
        BotCommand("stats", get_text('commands', 'stats', lang)),
        BotCommand("start_bot", get_text('commands', 'start_bot', lang)),
        BotCommand("pause", get_text('commands', 'pause', lang)),
        BotCommand("stop", get_text('commands', 'stop', lang)),
        BotCommand("restart", get_text('commands', 'restart', lang)),
        BotCommand("info", get_text('commands', 'info', lang)),
        BotCommand("settings", get_text('commands', 'settings', lang)),
        BotCommand("ai_toggle", get_text('commands', 'ai_toggle', lang))
    ])

# Генерация отчета о состоянии бота
def generate_status_report():
    if not stats['start_time']:
        return get_text('responses', 'bot_stopped', user_settings['language'])
    
    uptime = datetime.now() - stats['start_time']
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    last_check = stats['last_check'].strftime("%H:%M:%S") if stats['last_check'] else get_text('responses', 'never', user_settings['language'])
    last_post = stats['last_post'].strftime("%H:%M:%S") if stats['last_post'] else get_text('responses', 'never', user_settings['language'])
    
    # Статус ИИ
    ai_status = "❌ OFF"
    ai_errors = "N/A"
    if ai_generator:
        ai_info = ai_generator.get_status()
        ai_status = f"✅ DeepSeek (запросов: {ai_info['stats']['total_requests']})"
        ai_errors = f"Ошибок: {ai_info['stats']['errors']}"
        
        if ai_info['stats']['last_error']:
            last_error = ai_info['stats']['last_error']
            error_time = last_error['time']
            error_type = last_error['type']
            error_code = last_error['code'] or "N/A"
            ai_errors += f"\nПоследняя ошибка: [{error_code}] {error_type} в {error_time}"
    
    # Последняя ошибка ИИ
    last_ai_error = f"\n🤖 Последняя ошибка ИИ: {stats['last_ai_error']}" if stats['last_ai_error'] else ""
    
    report = (
        f"🤖 <b>Статус бота</b>\n"
        f"⏱ Время работы: {int(hours)}ч {int(minutes)}м\n"
        f"📊 Отправлено новостей: {stats['posts_sent']}\n"
        f"🤖 ИИ-генерация: {ai_status}\n"
        f"❌ Ошибки ИИ: {ai_errors}{last_ai_error}\n"
        f"🔄 Последняя проверка: {last_check}\n"
        f"📬 Последняя публикация: {last_post}\n"
        f"🔗 Источников: {len(RSS_URLS)}\n"
        f"📝 Состояние: {'🟢 ' + get_text('responses', 'running', user_settings['language']) if controller.status() else '🔴 ' + get_text('responses', 'stopped', user_settings['language'])}"
    )
    return report

# Обработчики команд
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id != OWNER_ID:
        return
        
    lang = user_settings['language']
    bot.reply_to(message, 
        f"{get_text('bot_description', lang=lang)}\n\n{get_text('commands_list', lang=lang)}",
        parse_mode="HTML",
        reply_markup=create_reply_keyboard()
    )

@bot.message_handler(commands=['status', 'stats'])
def send_status(message):
    if message.from_user.id != OWNER_ID:
        return
        
    bot.reply_to(message, generate_status_report(), 
                parse_mode="HTML",
                reply_markup=create_reply_keyboard())

@bot.message_handler(commands=['start_bot'])
def start_command(message):
    if message.from_user.id != OWNER_ID:
        return
        
    if controller.start():
        bot.reply_to(message, get_text('responses', 'start_success', user_settings['language']), 
                    parse_mode="HTML",
                    reply_markup=create_reply_keyboard())
    else:
        bot.reply_to(message, get_text('responses', 'start_fail', user_settings['language']), 
                    parse_mode="HTML",
                    reply_markup=create_reply_keyboard())

@bot.message_handler(commands=['stop', 'pause'])
def stop_command(message):
    if message.from_user.id != OWNER_ID:
        return
        
    if controller.stop():
        bot.reply_to(message, get_text('responses', 'stop_success', user_settings['language']), 
                    parse_mode="HTML",
                    reply_markup=create_reply_keyboard())
    else:
        bot.reply_to(message, get_text('responses', 'stop_fail', user_settings['language']), 
                    parse_mode="HTML",
                    reply_markup=create_reply_keyboard())

@bot.message_handler(commands=['restart'])
def restart_command(message):
    if message.from_user.id != OWNER_ID:
        return
        
    controller.stop()
    time.sleep(1)
    if controller.start():
        bot.reply_to(message, get_text('responses', 'restart_success', user_settings['language']), 
                    parse_mode="HTML",
                    reply_markup=create_reply_keyboard())
    else:
        bot.reply_to(message, get_text('responses', 'restart_fail', user_settings['language']), 
                    parse_mode="HTML",
                    reply_markup=create_reply_keyboard())

@bot.message_handler(commands=['info'])
def info_command(message):
    if message.from_user.id != OWNER_ID:
        return
        
    bot.reply_to(message, get_text('info_message', lang=user_settings['language']), 
                parse_mode="HTML",
                reply_markup=create_reply_keyboard())

@bot.message_handler(commands=['settings'])
def settings_command(message):
    if message.from_user.id != OWNER_ID:
        return
        
    bot.reply_to(message, f"⚙️ <b>Настройки бота</b>\nВыберите опцию:", 
                parse_mode="HTML",
                reply_markup=create_settings_keyboard())

@bot.message_handler(commands=['ai_toggle'])
def toggle_ai_command(message):
    if message.from_user.id != OWNER_ID:
        return
        
    global USE_AI
    USE_AI = not USE_AI
    os.environ['USE_AI_GENERATION'] = str(USE_AI).lower()
    
    # Обновляем генератор
    global ai_generator
    if USE_AI:
        ai_generator = AIGenerator()
        status_text = get_text('responses', 'ai_enabled', user_settings['language'])
    else:
        ai_generator = None
        status_text = get_text('responses', 'ai_disabled', user_settings['language'])
    
    bot.reply_to(message, status_text, 
                parse_mode="HTML",
                reply_markup=create_settings_keyboard())

# Обработка текстовых сообщений (кнопок)
@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    if message.from_user.id != OWNER_ID:
        return
    
    text = message.text.strip()
    lang = user_settings['language']
    
    # Обработка кнопок основного меню
    if text == get_text('main_menu', 'start', lang):
        start_command(message)
    elif text == get_text('main_menu', 'pause', lang) or text == get_text('main_menu', 'stop', lang):
        stop_command(message)
    elif text == get_text('main_menu', 'restart', lang):
        restart_command(message)
    elif text == get_text('main_menu', 'stats', lang):
        report = generate_status_report()
        bot.reply_to(message, report, 
                    parse_mode="HTML",
                    reply_markup=create_reply_keyboard())
    elif text == get_text('main_menu', 'info', lang):
        info_command(message)
    elif text == get_text('main_menu', 'help', lang):
        send_welcome(message)
    elif text == get_text('main_menu', 'settings', lang):
        settings_command(message)
    
    # Обработка кнопок меню настроек
    elif text == get_text('settings_menu', 'ai_toggle', lang):
        toggle_ai_command(message)
    elif text == get_text('settings_menu', 'back', lang):
        bot.reply_to(message, "⬅️ Возврат в главное меню", 
                    parse_mode="HTML",
                    reply_markup=create_reply_keyboard())
    
    else:
        bot.reply_to(message, get_text('responses', 'unknown_cmd', lang),
                    reply_markup=create_reply_keyboard())

# Проверка доступа при запуске
def initial_check():
    try:
        me = bot.get_me()
        logger.info(f"Bot started: @{me.username}")
        
        # Проверка канала
        bot.send_chat_action(CHANNEL_ID, 'typing')
        logger.info(f"Channel access OK: {CHANNEL_ID}")
        
        # Проверка RSS
        for url in RSS_URLS:
            entries = parser.parse_feed(url)
            status = "OK" if entries else "ERROR"
            logger.info(f"RSS check: {url} - {status}")
            
        # Проверка AI
        if USE_AI:
            try:
                test_gen = ai_generator.generate_content("Test", "This is a connection test")
                logger.info(f"AI connection test passed: {test_gen[:50]}...")
                bot.send_message(OWNER_ID, "✅ AI connection test successful!")
            except Exception as e:
                logger.error(f"AI connection test failed: {str(e)}")
                bot.send_message(OWNER_ID, f"⚠️ AI connection test failed: {str(e)}")
        
        return True
    except Exception as e:
        logger.critical(f"STARTUP ERROR: {str(e)}")
        error_msg = f"⚠️ {get_text('responses', 'startup_error', user_settings['language'])}: {str(e)}"
        bot.send_message(OWNER_ID, error_msg, parse_mode="HTML")
        return False

if __name__ == '__main__':
    logger.info("===== BOT STARTING =====")
    
    # Настройка команд бота
    setup_bot_commands()
    
    # Инициализация и проверка
    if initial_check():
        logger.info("===== READY FOR COMMANDS =====")
        
        # Автозапуск бота
        controller.start()
        
        # Отправка статуса владельцу
        bot.send_message(
            OWNER_ID, 
            "🤖 Бот успешно запущен!\n" + generate_status_report(), 
            parse_mode="HTML"
        )
        
        # Запуск основного цикла
        bot.infinity_polling()
    else:
        logger.error("===== BOT FAILED TO START =====")