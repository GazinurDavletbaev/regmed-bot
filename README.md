# RegMed Bot — интеллектуальная система для работы с ГОСТами

Telegram-бот и веб-интерфейс с RAG (Retrieval-Augmented Generation) для поиска и анализа нормативной документации в области медицинских изделий.

## 🚀 Возможности

### Telegram-бот
- Авторизация через Supabase (роли: admin, manager, user)
- Загрузка документов (PDF, DOCX) в хранилище (Яндекс.Диск / локально)
- Вопросы по документам с ответами на основе RAG
- Администрирование: добавление/удаление пользователей, просмотр списка ГОСТов

### Веб-интерфейс (FastAPI)
- Чат для вопросов по ГОСТам
- Загрузка PDF с указанием лаборатории
- Создание отдельных чатов
- Интеграция с RAG-сервисом

## 🏗 Архитектура (Clean Architecture)
regmed-bot/
├── presentation/ # Точки входа
│ ├── telegram/ # Aiogram-бот
│ │ ├── handlers/ # Обработчики команд
│ │ │ ├── access_requests.py # Запросы доступа
│ │ │ ├── admin.py # Администрирование
│ │ │ ├── gost_list.py # Список ГОСТов
│ │ │ └── questions.py # Вопросы (RAG)
│ │ └── middlewares/ # Проверка доступа
│ │ └── access.py # AccessMiddleware
│ └── web/ # FastAPI веб-интерфейс
│ ├── fast_api_main.py # Основное приложение
│ ├── static/ # CSS, JS
│ └── templates/ # HTML шаблоны
├── domain/ # Бизнес-логика
│ ├── rag_service.py # RAGService (поиск + DeepSeek)
│ ├── user.py # Управление пользователями
│ └── document.py # Работа с документами
├── infrastructure/ # Внешние сервисы
│ └── database/ # Supabase клиент
│ └── supabase_client.py # Подключение к Supabase
├── core/ # Конфигурация, утилиты
│ ├── config.py # Настройки из .env
│ └── logging.py # Логирование
├── scripts/ # Вспомогательные скрипты
│ └── init_db.py # Инициализация таблиц Supabase
├── data/ # Локальные данные
│ ├── uploads/ # Загруженные PDF
│ └── qdrant_storage/ # Данные Qdrant
├── docker-compose.yml # Запуск Qdrant + веб-сервиса
├── Dockerfile # Сборка веб-сервиса
├── pyproject.toml # Зависимости (uv)
├── .env.example # Пример переменных окружения
└── README.md

## 🛠 Технологии

| Компонент | Технология |
|-----------|------------|
| Telegram-бот | Aiogram 3.11.0 |
| Веб-интерфейс | FastAPI + Jinja2 + HTML/CSS/JS |
| Векторная БД | Qdrant (Docker) |
| Эмбеддинги | Sentence Transformers (`intfloat/multilingual-e5-large`) |
| LLM | DeepSeek API |
| База данных | Supabase (PostgreSQL) |
| Хранилище | Яндекс.Диск / локальное |
| Контейнеризация | Docker Compose |
| Пакетный менеджер | uv |

## 🔄 Рабочий процесс RAG

1. **Загрузка документа**  
   → Telegram-бот или веб-интерфейс  
   → сохранение в хранилище  
   → парсинг (pdfplumber / python-docx)  
   → чанкинг  
   → эмбеддинги → Qdrant (с меткой лаборатории/пользователя)

2. **Вопрос пользователя**  
   → Telegram-бот или веб-чат  
   → поиск релевантных чанков в Qdrant  
   → формирование контекста  
   → DeepSeek API  
   → ответ с источниками

## 📦 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/regmed-bot.git
cd regmed-bot

2. Настройка окружения
Скопируйте .env.example в .env и заполните переменные:

bash
cp .env.example .env
Переменные окружения:
Переменная	Описание	Обязательная
TELEGRAM_BOT_TOKEN	Токен Telegram-бота	✅
SUPABASE_URL	URL Supabase проекта	✅
SUPABASE_KEY	API-ключ Supabase (anon или service_role)	✅
DEEPSEEK_API_KEY	API-ключ DeepSeek	✅
YANDEX_DISK_TOKEN	Токен Яндекс.Диска (опционально)	❌
QDRANT_URL	Адрес Qdrant (по умолчанию http://localhost:6333)	❌
QDRANT_API_KEY	API-ключ Qdrant	❌
PROXY_URL	Прокси-сервер (например, http://127.0.0.1:10809)	❌
3. Инициализация базы данных Supabase
Запустите скрипт для создания таблицы bot_users:

bash
python scripts/init_db.py
4. Запуск через Docker Compose
bash
docker-compose up --build
Веб-интерфейс будет доступен по адресу: http://localhost:8000

5. Запуск Telegram-бота (локально)
bash
python -m presentation.telegram.main
🔧 Разработка
Быстрая перезагрузка веб-интерфейса
При изменении кода (без изменения зависимостей):

bash
docker-compose restart web
Добавление новых зависимостей
Добавьте пакет в pyproject.toml

Выполните uv lock

Пересоберите образ:

bash
docker-compose up --build
📝 Дальнейшие планы
Автоматическая индексация загруженных PDF через веб

Привязка лаборатории к чату (поиск только по её документам)

API-эндпоинт /api/ask для внешних систем (1С, CRM, ЭДО)

Интеграция с ЭДО (автоматическая проверка документов перед подписанием)

📄 Лицензия
MIT