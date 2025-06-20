# 🚀 Life Automation System

**Универсальная платформа для автоматизации жизненных процессов с использованием AI и Telegram**

Команда для быстрого комита
```python
git commit -m "Auto-update"
```

## 🌟 Цель проекта
Создать масштабируемую систему, которая:
1. Автоматизирует рутинные задачи (сбор новостей, публикации в соцсети)
2. Использует AI для улучшения контента
3. Предоставляет единый центр управления для всех процессов
4. Легко расширяется новыми модулями и функциями

## 🧠 Направление развития
- **Базовый функционал**: Telegram бот для публикации AI-улучшенных новостей
- **Будущие модули**:
  - Автопостинг в Instagram/Twitter
  - Персональный AI-ассистент
  - Система напоминаний и планирования
  - Аналитика эффективности контента

## 🛠️ Технологический стек
- Python 3.10+
- Telegram Bot API
- YandexGPT (с возможностью перехода на другие AI)
- RabbitMQ для межмодульного взаимодействия
- Docker для контейнеризации
- Pydantic для валидации данных

## 📂 Структура проекта
```
life/
├── ai_config/       # Все настройки AI (провайдеры, промпты)
├── core/            # Общие модули (конфиг, БД, шина сообщений)
├── projects/        # Основные проекты
│   ├── project1_tg_bot/  # Telegram бот (текущий фокус)
│   ├── project2_future/  # Будущие разработки
│   └── project3_future/
├── shared/          # Общие ресурсы (схемы, константы)
├── tests/           # Тесты
├── .env.example     # Шаблон конфигурации
├── docker-compose.yml
├── main.py          # Главный оркестратор
└── requirements.txt
```

## 🚀 Быстрый старт

1. Склонируйте репозиторий:
```bash
git clone https://github.com/Termos47/life.git
cd life
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте окружение:
```bash
cp .env.example .env
# Отредактируйте .env файл
```

4. Запустите систему:
```bash
python main.py
```

## ⚙️ Настройка Telegram бота

Добавьте в `.env` свои учетные данные:
```ini
TG_BOT_TOKEN=your_telegram_bot_token
TG_CHANNEL_ID=@your_channel
YANDEX_API_KEY=your_api_key
YANDEX_FOLDER_ID=your_folder_id
```

## 🤖 Пример работы с AI

```python
from ai_config.adapter import AIAdapter

async def enhance_news(text: str) -> str:
    """Улучшение новости с помощью AI"""
    ai = AIAdapter()
    return await ai.enhance_text(
        text=text,
        prompt_key="news_enhance"
    )

# Использование
original = "Новое открытие в науке..."
improved = await enhance_news(original)
print(f"Улучшенный текст: {improved}")
```

## 🐳 Запуск в Docker
```bash
docker-compose up --build
```

## 🤝 Как внести вклад
1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add some amazing feature'`)
4. Запушьте ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия
Этот проект распространяется под лицензией MIT. Подробнее см. в [LICENSE](LICENSE).

---
**🚧 Проект в активной разработке**  
Все предложения и Pull Requests приветствуются!