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


def get_memory():
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
            "itemids": [ITEMIDS_PVE03["Memory Utilization"]]
        }
    )

    item = result[0]

    memory = {
        "value": float(item["lastvalue"]),
        "unit": item["units"],
        "timestamp": int(item["lastclock"])
    }

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Memory : {memory['value']} {memory['unit']}")

    return memory

from zabbix_api import zabbix_api
from config import ITEMIDS_PVE03