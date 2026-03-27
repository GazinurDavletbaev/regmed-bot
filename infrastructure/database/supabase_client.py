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
            key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # для таблиц используем service_role
            proxy_url = os.getenv("PROXY_URL")

            if not url or not key:
                raise ValueError("SUPABASE_URL или SUPABASE_SERVICE_ROLE_KEY не заданы")
            logger.info(f"Подключаемся к Supabase: {url[:20]}...")

            if proxy_url:
                os.environ["HTTP_PROXY"] = proxy_url
                os.environ["HTTPS_PROXY"] = proxy_url
                logger.info(f"Установлен прокси: {proxy_url}")

            cls._instance = create_client(url, key)

        return cls._instance