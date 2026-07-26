import requests

from config import ZABBIX_URL, ZABBIX_AUTH


def zabbix_api(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": ZABBIX_AUTH,
        "id": 1
    }

    response = requests.post(
        ZABBIX_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise Exception(data["error"]["data"])

    return data["result"]