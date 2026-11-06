JWT_SECRET = "secret"


def authenticate_user(username, password):
    if username == "admin" and password == "password":
        return create_token(username)

    return None


def create_token(username):
    return f"token:{username}"


def verify_token(token):
    return token.startswith("token:")
