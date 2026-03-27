import os
from supabase import create_client, Client

class SupabaseAuth:
    _instance: Client = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")  # для auth используем anon key
            if not url or not key:
                raise ValueError("SUPABASE_URL или SUPABASE_ANON_KEY не заданы")
            cls._instance = create_client(url, key)
        return cls._instance

    @classmethod
    def register(cls, email: str, password: str, full_name: str):
        client = cls.get_client()
        return client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name}
            }
        })

    @classmethod
    def login(cls, email: str, password: str):
        client = cls.get_client()
        return client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

    @classmethod
    def logout(cls, access_token: str):
        client = cls.get_client()
        return client.auth.sign_out()

    @classmethod
    def get_user(cls, access_token: str):
        client = cls.get_client()
        return client.auth.get_user(access_token)

    @classmethod
    def reset_password(cls, email: str):
        client = cls.get_client()
        return client.auth.reset_password_for_email(email)

    @classmethod
    def update_password(cls, access_token: str, new_password: str):
        client = cls.get_client()
        return client.auth.update_user({"password": new_password})