import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

async def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ SUPABASE_URL или SUPABASE_KEY не заданы в .env")
        return
    
    client = create_client(url, key)
    
    # Проверяем подключение
    try:
        response = client.table("bot_users").select("*", count="exact").limit(1).execute()
        print(f"✅ Таблица bot_users существует (записей: {response.count})")
    except Exception as e:
        # Если таблицы нет — создадим через SQL вручную (пока просто сообщение)
        print(f"⚠️ Таблица bot_users отсутствует или ошибка: {e}")
        print("Создайте таблицу вручную в Supabase SQL Editor:")
        print("""
CREATE TABLE IF NOT EXISTS bot_users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username TEXT,
    full_name TEXT,
    role TEXT CHECK (role IN ('admin', 'manager', 'user')) DEFAULT 'user',
    approved_by BIGINT,
    approved_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
        """)

if __name__ == "__main__":
    asyncio.run(main())
