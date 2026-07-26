import requests
from datetime import datetime

from config import ZABBIX_URL, ZABBIX_AUTH, ITEMIDS_PVE03


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


def get_last_values():

    result = zabbix_api(
        "item.get",
        {
            "output": [
                "itemid",
                "name",
                "lastvalue",
                "units",
                "lastclock"
            ],
            "itemids": list(ITEMIDS_PVE03.values())
        }
    )

    id_to_name = {v: k for k, v in ITEMIDS_PVE03.items()}

    values = {}

    for item in result:
        values[id_to_name[item["itemid"]]] = {
            "value": float(item["lastvalue"]),
            "unit": item["units"],
            "timestamp": int(item["lastclock"])
        }

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Success get last values")

    for name, info in values.items():
        print(f"{name:<25}: {info['value']} {info['unit']}")

    print("-" * 50)

    return values