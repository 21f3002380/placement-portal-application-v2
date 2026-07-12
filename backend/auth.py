import time
import jwt
from functools import wraps
from flask import request, jsonify, current_app, g
from backend.models import User


def create_token(user):
    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "email": user.email,
        "iat": now,
        "exp": now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])


def _load_user_from_request():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, "Missing or invalid Authorization header"
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"
    user = User.query.get(int(payload["sub"]))
    if not user:
        return None, "User not found"
    if not user.is_active:
        return None, "Account is deactivated"
    return user, None


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user, err = _load_user_from_request()
        if err:
            return jsonify({"error": err}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user, err = _load_user_from_request()
            if err:
                return jsonify({"error": err}), 401
            if user.role not in roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            g.current_user = user
            return f(*args, **kwargs)
        return wrapper
    return decorator
