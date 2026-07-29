import time
import requests

from config import ZABBIX_URL, ZABBIX_AUTH
from service.telegram import send_message

last_eventid = 0

# key = triggerid
active_problems = {}

SEVERITY = {
    "0": "⚪ Not classified",
    "1": "🔵 Information",
    "2": "🟡 Warning",
    "3": "🟠 Average",
    "4": "🔴 High",
    "5": "🚨 Disaster"
}


def get_events():
    payload = {
        "jsonrpc": "2.0",
        "method": "event.get",
        "params": {
            "output": [
                "eventid",
                "objectid",
                "name",
                "severity",
                "value",
                "clock"
            ],
            "source": 0,
            "object": 0,
            "sortfield": "eventid",
            "sortorder": "DESC",
            "limit": 20
        },
        "auth": ZABBIX_AUTH,
        "id": 1
    }

    response = requests.post(ZABBIX_URL, json=payload)
    return response.json()["result"]


def main():

    global last_eventid

    while True:

        try:

            print("=" * 60)
            print(f"Update : {time.strftime('%Y-%m-%d %H:%M:%S')}")

            events = get_events()

            # Inisialisasi agar event lama tidak ikut terkirim
            if last_eventid == 0 and events:
                last_eventid = int(events[0]["eventid"])
                print(f"Init last_eventid = {last_eventid}")

            resolved_messages = []
            active_changed = False

            # proses dari event lama -> baru
            for event in reversed(events):

                eventid = int(event["eventid"])

                if eventid <= last_eventid:
                    continue

                triggerid = event["objectid"]

                print(f"Event ID  : {eventid}")
                print(f"TriggerID : {triggerid}")
                print(f"Problem   : {event['name']}")


                if event["value"] == "1":

                    severity = SEVERITY.get(
                        event["severity"],
                        event["severity"]
                    )

                    print(f"Severity  : {severity}")
                    print("Status    : Active")

                    active_problems[triggerid] = {
                        "name": event["name"],
                        "severity": severity
                    }

                    active_changed = True

                else:

                    info = active_problems.get(triggerid)

                    if info:

                        print(f"Severity  : {info['severity']}")
                        print("Status    : Resolved")

                        resolved_messages.append(
                            f"- {info['name']} • Severity : {info['severity']}, Status : Resolved"
                        )

                        del active_problems[triggerid]

                    else:

                        print("Status    : Resolved (severity tidak ditemukan)")
                        print("Kemungkinan bot baru dijalankan setelah problem sudah aktif.")

                last_eventid = eventid

            # Kirim Active Problem
            if active_changed:

                active_messages = []

                for info in active_problems.values():
                    active_messages.append(
                        f"- {info['name']} • Severity : {info['severity']}, Status : Active"
                    )

                if active_messages:
                    send_message(
                        "🚨 Zabbix Monitoring Alert\n\n"
                        "The following monitoring events have been detected:\n\n"
                        + "\n".join(active_messages)
                        + "\n\n"
                        "Please investigate the affected systems as soon as possible."
                    )


            # Kirim Resolved Problem
            if resolved_messages:

                send_message(
                    "✅ Zabbix Monitoring Alert\n\n"
                    "The following monitoring events have been resolved:\n\n"
                    + "\n".join(resolved_messages)
                )

        except Exception as e:
            print(f"Error : {e}")

        print("Menunggu 10 detik...\n")
        time.sleep(10)


if __name__ == "__main__":
    main()