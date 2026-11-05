import html
import json
import math
import re
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BOT_TOKEN = "9247494433:AAGR2dYXMWNfHKPpsKgRdey1SJ8tvpjnIZ8"
SITE_URL = "https://rodion2345234.github.io/otc/"
BOT_USERNAME = "LolzMrktXBot"
ADMIN_URL = "https://t.me/NFT_Exchanger1"
API_URL = "https://api.telegram.org/bot{}/{}"
DEALS_DB = Path.home() / ".lolzmarket" / "deals.sqlite3"
DEAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,48}$")

# Configure https://rodion2345234.github.io as the Telegram Web App domain in BotFather.
WELCOME_TEXT = (
    "🌿 <b>Добро пожаловать в LolzMarket!</b>\n\n"
    "Здесь можно создать предложение и обсудить сделку с NFT "
    "или Telegram-подарком.\n\n"
    "<b>Как проходит сделка</b>\n"
    "1. Сначала согласуйте с администратором предмет, цену и порядок действий.\n"
    "2. После подтверждения условий продавец передаёт подарок администратору, "
    "а покупатель отправляет согласованную оплату.\n"
    "3. После подтверждения получения подарка и оплаты администратор передаёт "
    "подарок покупателю, а оплату продавцу.\n\n"
    "🛡️ <b>Пожалуйста, будьте внимательны.</b> Сайт не принимает и не проверяет "
    "платежи или подарки. Перед отправкой обязательно подтвердите с "
    "администратором получателя, сумму и условия. Если что-то не совпадает — "
    "остановитесь и сначала свяжитесь с администратором."
)


def connect_db():
    DEALS_DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DEALS_DB)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS deals "
        "(deal_id TEXT PRIMARY KEY, payload TEXT NOT NULL, owner_id INTEGER NOT NULL)"
    )
    connection.commit()
    return connection


def save_deal(data, owner_id):
    deal_id = data.get("deal_id")
    if not isinstance(deal_id, str) or not DEAL_ID_PATTERN.fullmatch(deal_id):
        raise ValueError("Некорректный номер сделки.")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("В заявке не указано название NFT.")
    name = name.strip()[:60]

    item_url = data.get("link")
    if not isinstance(item_url, str) or len(item_url) > 500:
        raise ValueError("Некорректная ссылка на NFT.")
    if not item_url.startswith("https://") or any(char.isspace() for char in item_url):
        raise ValueError("Ссылка на NFT должна быть безопасной ссылкой https://.")

    price = data.get("price")
    try:
        amount = float(price)
    except (TypeError, ValueError):
        raise ValueError("Некорректная цена.") from None
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Цена должна быть больше нуля.")

    role = data.get("role")
    if role not in ("sell", "buy"):
        raise ValueError("Некорректный тип предложения.")

    deal = {
        "deal_id": deal_id,
        "role": role,
        "name": name,
        "link": item_url,
        "price": str(price)[:32],
        "currency": str(data.get("currency", "USDT"))[:12],
        "chain": str(data.get("chain", "TON"))[:24],
        "contact": str(data.get("contact", ""))[:40],
        "note": str(data.get("note", ""))[:300],
    }
    with closing(connect_db()) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO deals (deal_id, payload, owner_id) VALUES (?, ?, ?)",
            (deal_id, json.dumps(deal, ensure_ascii=False), owner_id),
        )
        connection.commit()
    return deal


def get_deal(deal_id):
    if not DEAL_ID_PATTERN.fullmatch(deal_id):
        return None
    with closing(connect_db()) as connection:
        row = connection.execute(
            "SELECT payload FROM deals WHERE deal_id = ?", (deal_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def telegram_api(method, payload):
    request = Request(
        API_URL.format(BOT_TOKEN, method),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=40) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            "Telegram API вернул ошибку HTTP {}: {}".format(error.code, details)
        ) from error
    except URLError as error:
        raise RuntimeError("Не удалось подключиться к Telegram API: {}".format(error.reason)) from error

    if not result.get("ok"):
        raise RuntimeError("Ошибка Telegram API: {}".format(result.get("description", "неизвестная ошибка")))
    return result["result"]


def send_welcome(chat_id):
    telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": WELCOME_TEXT,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "✨ Открыть LolzMarket", "web_app": {"url": SITE_URL}}],
                    [{"text": "Открыть сайт в браузере", "url": SITE_URL}],
                    [{"text": "💬 Написать администратору", "url": ADMIN_URL}],
                ]
            },
        },
    )


def deal_app_url(deal):
    params = {
        "deal_id": deal["deal_id"],
        "role": deal["role"],
        "name": deal["name"],
        "item_url": deal["link"],
        "price": deal["price"],
        "currency": deal["currency"],
        "chain": deal["chain"],
        "note": deal["note"],
    }
    return SITE_URL + "deal.html?" + urlencode(params)


def send_deal(chat_id, deal):
    role = "Продажа" if deal["role"] == "sell" else "Покупка"
    text = (
        "📦 <b>Предложение LolzMarket</b>\n\n"
        "<b>Сделка:</b> <code>{}</code>\n"
        "<b>Тип:</b> {}\n"
        "<b>NFT:</b> {}\n"
        "<b>Цена:</b> {} {}\n"
        "<b>Сеть:</b> {}\n\n"
        "Откройте карточку сделки, чтобы посмотреть детали и порядок действий. "
        "Сначала согласуйте всё с администратором. Не отправляйте подарок или "
        "деньги до подтверждения условий. Сайт и бот не принимают и не проверяют переводы."
    ).format(
        html.escape(deal["deal_id"]),
        role,
        html.escape(deal["name"]),
        html.escape(deal["price"]),
        html.escape(deal["currency"]),
        html.escape(deal["chain"]),
    )
    app_url = deal_app_url(deal)
    telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "📱 Открыть сделку в мини-приложении", "web_app": {"url": app_url}}],
                    [{"text": "Связаться с администратором", "url": ADMIN_URL}],
                ]
            },
        },
    )


def handle_web_app_data(message):
    web_app_data = message.get("web_app_data")
    chat = message.get("chat")
    user = message.get("from")
    if not isinstance(web_app_data, dict) or not isinstance(chat, dict) or not isinstance(user, dict):
        return

    raw_data = web_app_data.get("data")
    if not isinstance(raw_data, str) or len(raw_data) > 4096:
        if isinstance(chat.get("id"), int):
            telegram_api(
                "sendMessage",
                {"chat_id": chat["id"], "text": "Не удалось прочитать заявку. Вернитесь в мини-приложение и попробуйте ещё раз."},
            )
        return
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        chat_id = chat.get("id")
        if isinstance(chat_id, int):
            telegram_api(
                "sendMessage",
                {"chat_id": chat_id, "text": "Не удалось прочитать заявку. Вернитесь в мини-приложение и попробуйте ещё раз."},
            )
        return
    if not isinstance(data, dict) or data.get("action") != "create_offer":
        return

    chat_id = chat.get("id")
    user_id = user.get("id")
    if not isinstance(chat_id, int) or not isinstance(user_id, int):
        raise ValueError("В сообщении заявки отсутствует ID пользователя Telegram.")
    try:
        deal = save_deal(data, user_id)
    except ValueError as error:
        telegram_api(
            "sendMessage",
            {"chat_id": chat_id, "text": "Не удалось создать сделку: {}".format(error)},
        )
        return
    send_deal(chat_id, deal)
    join_url = "https://t.me/{}?start=join_{}".format(BOT_USERNAME, deal["deal_id"])
    telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": "✅ Заявка сохранена. Отправьте эту ссылку участнику сделки:\n{}".format(join_url),
            "disable_web_page_preview": True,
        },
    )


def handle_update(update):
    message = update.get("message")
    if not isinstance(message, dict):
        return

    if isinstance(message.get("web_app_data"), dict):
        handle_web_app_data(message)
        return

    text = message.get("text")
    chat = message.get("chat")
    if not isinstance(text, str) or not isinstance(chat, dict):
        return

    command_parts = text.split(maxsplit=1)
    command = command_parts[0].split("@", maxsplit=1)[0].lower()
    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        raise RuntimeError("В обновлении Telegram отсутствует корректный ID чата.")

    if command == "/start":
        argument = command_parts[1].strip() if len(command_parts) > 1 else ""
        if argument.startswith("join_"):
            deal_id = argument[len("join_"):]
            deal = get_deal(deal_id)
            if deal is None:
                telegram_api(
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "Эта сделка не найдена. Возможно, продавец ещё не отправил заявку боту. Попросите его сначала завершить создание сделки.",
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "Открыть LolzMarket", "url": SITE_URL}],
                                [{"text": "Написать администратору", "url": ADMIN_URL}],
                            ]
                        },
                    },
                )
                return
            send_deal(chat_id, deal)
            return
        send_welcome(chat_id)
    elif command == "/help":
        send_welcome(chat_id)


def main():
    if BOT_TOKEN == "PASTE_NEW_TOKEN_HERE":
        sys.exit("Замените PASTE_NEW_TOKEN_HERE на новый токен от BotFather.")
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]{20,}", BOT_TOKEN):
        sys.exit("Токен имеет неверный формат. Скопируйте новый токен целиком из BotFather.")

    offset = None
    while True:
        payload = {"timeout": 30, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset

        updates = telegram_api("getUpdates", payload)
        for update in updates:
            if not isinstance(update, dict) or not isinstance(update.get("update_id"), int):
                raise RuntimeError("Telegram returned an invalid update")
            handle_update(update)
            offset = update["update_id"] + 1


if __name__ == "__main__":
    main()
