from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

class JwtAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query = dict(
            x.split("=") for x in scope["query_string"].decode().split("&") if "=" in x
        )
        token = query.get("token")

        try:
            user_id = AccessToken(token)["user_id"]
            scope["user"] = await User.objects.aget(id=user_id)
        except:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
