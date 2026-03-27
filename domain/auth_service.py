from infrastructure.database.auth.supabase_auth import SupabaseAuth

class AuthService:
    @staticmethod
    def register(email: str, password: str, full_name: str):
        response = SupabaseAuth.register(email, password, full_name)
        if response.user:
            return {"success": True, "user_id": response.user.id, "message": "Проверьте почту для подтверждения"}
        return {"success": False, "message": "Ошибка регистрации"}

    @staticmethod
    def login(email: str, password: str):
        response = SupabaseAuth.login(email, password)
        if response.session:
            return {
                "success": True,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": response.user
            }
        return {"success": False, "message": "Неверный email или пароль"}

    @staticmethod
    def logout(access_token: str):
        return SupabaseAuth.logout(access_token)

    @staticmethod
    def reset_password(email: str):
        return SupabaseAuth.reset_password(email)

    @staticmethod
    def update_password(access_token: str, new_password: str):
        return SupabaseAuth.update_password(access_token, new_password)