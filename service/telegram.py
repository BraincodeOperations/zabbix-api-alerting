import requests

from config import TOKEN, CHAT_ID


def send_message(text):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=10
    )

    response.raise_for_status()