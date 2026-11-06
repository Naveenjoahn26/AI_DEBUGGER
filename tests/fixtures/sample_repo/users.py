def create_user(username, email):
    return {
        "username": username,
        "email": email,
    }


def delete_user(user_id):
    return {
        "deleted": user_id,
    }
