from flask import Flask, request, jsonify
import redis
import requests
import os
import yaml
import json


# Загружаем конфиг из файла
config_path = os.getenv("CONFIG_PATH", "/etc/cache-api/config.yaml")

try:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    config = {}


# Читаем настройки из конфига, затем из переменных окружения
# Переменные окружения имеют приоритет
REDIS_HOST = os.getenv(
    "REDIS_HOST",
    config.get("redis", {}).get("host", "redis")
)
REDIS_PORT = int(
    os.getenv(
        "REDIS_PORT",
        config.get("redis", {}).get("port", 6379)
    )
)

BACKEND_HOST = os.getenv(
    "BACKEND_HOST",
    config.get("backend", {}).get("host", "backend-api")
)
BACKEND_PORT = int(
    os.getenv(
        "BACKEND_PORT",
        config.get("backend", {}).get("port", 8080)
    )
)

APP_PORT = int(
    os.getenv(
        "APP_PORT",
        config.get("app", {}).get("port", 5000)
    )
)


# Инициализация Flask
app = Flask(__name__)

# Подключение к Redis
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


@app.route("/user")
def get_user():
    user_id = request.args.get("id")

    # Проверяем наличие пользователя в кэше
    cached = r.get(user_id)

    if cached:
        return jsonify({
            "cached": True,
            "user": json.loads(cached)
        })

    # Если данных нет в кэше, обращаемся к backend
    resp = requests.get(
        f"http://{BACKEND_HOST}:{BACKEND_PORT}/user?id={user_id}"
    )

    if resp.status_code == 200:
        # Сохраняем ответ в Redis на 60 секунд
        r.set(user_id, resp.text, ex=60)

        return jsonify({
            "cached": False,
            "user": resp.json()
        })

    return resp.text, resp.status_code


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=APP_PORT
    )
