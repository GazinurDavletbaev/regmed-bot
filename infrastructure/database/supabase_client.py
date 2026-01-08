import os
import logging
from supabase import create_client, Client
from typing import Optional

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise ValueError("SUPABASE_URL или SUPABASE_KEY не заданы в .env")
            logger.info(f"Подключаемся к Supabase: {url[:20]}...")
            cls._instance = create_client(url, key)
        return cls._instance