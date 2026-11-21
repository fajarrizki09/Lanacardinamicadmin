import secrets


_LOCAL_APP_TOKEN = secrets.token_urlsafe(32)


def get_local_app_token():
    return _LOCAL_APP_TOKEN


def verify_local_app_token(token):
    if not token:
        return False
    return secrets.compare_digest(str(token), _LOCAL_APP_TOKEN)
