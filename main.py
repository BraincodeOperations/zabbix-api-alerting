import time

from service.zabbix.cpu import get_last_values
from service.telegram import send_message

from config import (
    CPU_THRESHOLD,
    MEMORY_THRESHOLD,
    DISK_THRESHOLD
)

# ==========================================
# Cooldown
# ==========================================

CPU_MEMORY_COOLDOWN = 600      # 10 menit
DISK_COOLDOWN = 86400          # 24 jam

last_cpu_alert = 0
last_memory_alert = 0
last_sda_alert = 0
last_sdb_alert = 0


def main():

    global last_cpu_alert
    global last_memory_alert
    global last_sda_alert
    global last_sdb_alert

    while True:

        try:

            print("=" * 50)
            print(f"Update: {time.strftime('%Y-%m-%d %H:%M:%S')}")

            data = get_last_values()

            for name, info in data.items():
                print(f"{name}: {info['value']} {info['unit']}")

            now = time.time()

            # ==========================================
            # CPU
            # ==========================================

            cpu = data["CPU Utilization"]["value"]

            if cpu >= CPU_THRESHOLD:

                if now - last_cpu_alert >= CPU_MEMORY_COOLDOWN:

                    send_message(
                        f"🚨‼️ CPU PVE03 sudah mencapai {cpu:.2f}% ‼️"
                    )

                    last_cpu_alert = now

            # ==========================================
            # MEMORY
            # ==========================================

            memory = data["Memory Utilization"]["value"]

            if memory >= MEMORY_THRESHOLD:

                if now - last_memory_alert >= CPU_MEMORY_COOLDOWN:

                    send_message(
                        f"🚨‼️ Memory PVE03 sudah mencapai {memory:.2f}% ‼️"
                    )

                    last_memory_alert = now

            # ==========================================
            # DISK SDA
            # ==========================================

            sda = data["sda: Disk utilization"]["value"]

            if sda >= DISK_THRESHOLD:

                if now - last_sda_alert >= DISK_COOLDOWN:

                    send_message(
                        f"🚨‼️ Disk SDA PVE03 sudah mencapai {sda:.2f}% ‼️"
                    )

                    last_sda_alert = now

            # ==========================================
            # DISK SDB
            # ==========================================

            sdb = data["sdb: Disk utilization"]["value"]

            if sdb >= DISK_THRESHOLD:

                if now - last_sdb_alert >= DISK_COOLDOWN:

                    send_message(
                        f"🚨‼️ Disk SDB PVE03 sudah mencapai {sdb:.2f}% ‼️"
                    )

                    last_sdb_alert = now

        except Exception as e:

            print(f"Error: {e}")

        print("Menunggu 60 detik...\n")

        time.sleep(60)


if __name__ == "__main__":
    main()