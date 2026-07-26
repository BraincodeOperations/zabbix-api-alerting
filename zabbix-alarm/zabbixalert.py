#!/usr/bin/env python3
"""
Website / API Status Monitor Bot -> Telegram
==============================================
 
Script ini melakukan pengecekan (polling) ke satu atau beberapa URL API/website
secara berkala, terus-menerus (loop selamanya).
 
PERUBAHAN DARI VERSI SEBELUMNYA:
- Interval polling sekarang 2 MENIT (120 detik), sebelumnya 1 menit.
- Selain alert saat DOWN dan notifikasi saat RECOVERED, sekarang bot JUGA
  mengirim LAPORAN STATUS OTOMATIS ke Telegram setiap kali selesai satu
  putaran cek (default: tiap 2 menit). Jadi kamu selalu dapat update
  real-time semua endpoint tanpa perlu ketik /status manual.
- Command /status TETAP ada dan tetap bisa dipakai kapan saja untuk cek
  manual instan (tidak dihapus).
 
Cara pakai singkat:
1. Isi bagian KONFIGURASI di bawah (daftar URL, token & chat id Telegram).
2. Jalankan: python3 zabbixalert.py
3. Biarkan berjalan terus di background (tmux/screen/systemd), karena ini loop.
4. Kapan saja, ketik /status di chat Telegram bot untuk cek manual instan.
"""
 
import time
import logging
import threading
import requests
from datetime import datetime
 
# =============================================================================
# KONFIGURASI - EDIT BAGIAN INI
# =============================================================================
 
# --- Telegram ---
TELEGRAM_BOT_TOKEN = "8825658334:AAFyuOFBNNLNWDnPJ1tUIm9TQUyWP4xoeXo"
TELEGRAM_CHAT_ID = "6455944327"
 
# --- Daftar endpoint yang mau dipantau ---
ENDPOINTS = [
    {
        "name": "Website Utama",
        "url": "https://pthsci.com",
        "method": "GET",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Bahan Baku by Vendor",
        "url": "https://pthsci.com/api/bahan-baku/by-vendor",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Barang Dalam Proses",
        "url": "https://pthsci.com/api/barang/dalam-proses",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Barang Jadi",
        "url": "https://pthsci.com/api/barang/jadi",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Barang Sisa dan Scrap",
        "url": "https://pthsci.com/api/barang/sisa-dan-scrap",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Mesin dan Peralatan",
        "url": "https://pthsci.com/api/mesin-dan-peralatan",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Pemasukan Barang",
        "url": "https://pthsci.com/api/pemasukan-barang",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Pemasukan Barang Non-RM",
        "url": "https://pthsci.com/api/pemasukan-barang-nonrm",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Pengeluaran Barang",
        "url": "https://pthsci.com/api/pengeluaran-barang",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Stock Opname",
        "url": "https://pthsci.com/api/stock-opname",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API RM Details Transaction",
        "url": "https://pthsci.com/api/rm-details-transaction",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API Bahan Baku",
        "url": "https://pthsci.com/api/bahan-baku",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    {
        "name": "API WHS Movement",
        "url": "https://pthsci.com/api/whs-movement",
        "method": "POST",
        "expected_status": 200,
        "timeout": 10,
    },
    # Tambah endpoint lain di sini kalau perlu, tinggal copy-paste blok di atas.
]
 
# --- Interval polling (detik) ---
# Diubah jadi 2 menit sesuai permintaan (sebelumnya 60 detik / 1 menit).
POLL_INTERVAL_SECONDS = 120
 
# --- Berapa kali GAGAL berturut-turut sebelum status dianggap "down" ---
CONSECUTIVE_FAILURE_COUNT = 2
 
# --- Kirim laporan status otomatis (ringkasan semua endpoint) tiap putaran? ---
# True  = tiap POLL_INTERVAL_SECONDS, bot kirim laporan status semua endpoint
#         (jadi kamu selalu tahu kondisi terkini secara real-time).
# False = bot cuma kirim pesan kalau ada perubahan (down / recovered) seperti
#         versi sebelumnya, dan laporan lengkap hanya lewat /status manual.
AUTO_STATUS_REPORT = True
 
# --- Kontrol pause/resume monitoring via Telegram ---
# Dipakai oleh command /stop dan /start di Telegram. Saat "paused", bot TETAP
# hidup/jalan di server dan tetap bisa dengerin command Telegram, tapi
# berhenti mengecek endpoint & berhenti kirim alert, sampai di-/start lagi.
monitoring_active = threading.Event()
monitoring_active.set()  # mulai dalam kondisi aktif
 
# =============================================================================
# LOGGING
# =============================================================================
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("website-monitor-bot")
 
 
# =============================================================================
# TELEGRAM
# =============================================================================
 
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot8825658334:AAFyuOFBNNLNWDnPJ1tUIm9TQUyWP4xoeXo/sendMessage"
    payload = {
        "chat_id": 6455944327,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"Gagal kirim pesan Telegram: {e}")
 
 
def format_alert_message(name, url, reason):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"🔴 <b>ALERT - API/Website Down</b>\n"
        f"Nama    : <b>{name}</b>\n"
        f"URL     : {url}\n"
        f"Alasan  : <b>{reason}</b>\n"
        f"Waktu   : {now}"
    )
 
 
def format_recovery_message(name, url, status_code):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"✅ <b>RECOVERED</b>\n"
        f"Nama    : <b>{name}</b>\n"
        f"URL     : {url}\n"
        f"Status  : {status_code} (normal)\n"
        f"Waktu   : {now}"
    )
 
 
def format_status_report(results, auto=False):
    """
    Susun laporan status semua endpoint jadi satu pesan Telegram yang ringkas.
    auto=True dipakai untuk laporan otomatis tiap putaran polling (biar bisa
    dibedakan dari laporan hasil ketik /status manual).
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(results)
    ok_count = sum(1 for r in results if r["success"])
    problem_results = [r for r in results if not r["success"]]
 
    if problem_results:
        header_icon = "⚠️"
        summary = f"{ok_count}/{total} normal, {len(problem_results)} bermasalah"
    else:
        header_icon = "✅"
        summary = f"Semua {total} endpoint normal"
 
    title = "Laporan Status Otomatis" if auto else "Status Cek Manual"
 
    lines = [
        f"{header_icon} <b>{title}</b>",
        f"<i>{now}</i>",
        summary,
        "",
    ]
 
    name_width = max(len(r["name"]) for r in results) + 2
    table_lines = []
    for r in results:
        icon = "🟢" if r["success"] else "🔴"
        status_text = r["info"] if r["success"] else "GAGAL"
        row_text = f"{r['name'].ljust(name_width)}{status_text}"
        table_lines.append(f"{icon} <code>{row_text}</code>")
 
    lines.extend(table_lines)
 
    if problem_results:
        lines.append("")
        lines.append("<b>Detail yang bermasalah:</b>")
        for r in problem_results:
            lines.append(
                f"🔴 <b>{r['name']}</b>\n"
                f"   {r['url']}\n"
                f"   {r['info']}"
            )
 
    return "\n".join(lines)
 
 
def set_bot_commands():
    """
    Daftarkan daftar command bot ke Telegram, supaya muncul sebagai menu
    saran otomatis waktu kamu ketik "/" di chat bot.
    """
    url = f"https://api.telegram.org/bot8825658334:AAFyuOFBNNLNWDnPJ1tUIm9TQUyWP4xoeXo/setMyCommands"
    commands = [
        {"command": "status", "description": "Cek status semua API/website sekarang"},
        {"command": "stop", "description": "Pause monitoring & alert otomatis"},
        {"command": "start", "description": "Resume monitoring & alert otomatis"},
    ]
    try:
        resp = requests.post(url, json={"commands": commands}, timeout=10)
        resp.raise_for_status()
        log.info("Menu command Telegram berhasil didaftarkan.")
    except Exception as e:
        log.error(f"Gagal mendaftarkan menu command Telegram: {e}")
 
 
# =============================================================================
# PENGECEKAN ENDPOINT
# =============================================================================
 
def check_endpoint(endpoint):
    url = endpoint["url"]
    method = endpoint.get("method", "GET").upper()
    timeout = endpoint.get("timeout", 10)
    expected_status = endpoint.get("expected_status", 200)
 
    try:
        resp = requests.request(method, url, timeout=timeout)
        status_code = resp.status_code
 
        if status_code == expected_status:
            return True, str(status_code)
        else:
            return False, f"HTTP {status_code} (diharapkan {expected_status})"
 
    except requests.exceptions.Timeout:
        return False, f"Timeout (tidak respons dalam {timeout} detik)"
    except requests.exceptions.ConnectionError:
        return False, "Connection error (server tidak bisa dihubungi)"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {e}"
 
 
def check_all_endpoints_now():
    """Cek SEMUA endpoint saat ini juga (dipakai untuk command /status)."""
    results = []
    for endpoint in ENDPOINTS:
        success, info = check_endpoint(endpoint)
        results.append({
            "name": endpoint["name"],
            "url": endpoint["url"],
            "success": success,
            "info": info,
        })
    return results
 
 
# =============================================================================
# STATE TRACKING (supaya tidak spam alert tiap polling)
# =============================================================================
state = {}
 
 
def get_state(url):
    state.setdefault(url, {"failure_count": 0, "alerted": False})
    return state[url]
 
 
def evaluate_endpoint(endpoint):
    """
    Cek satu endpoint, kelola alert/recovery, dan kembalikan hasilnya
    (dipakai juga untuk menyusun laporan status otomatis).
    """
    name = endpoint["name"]
    url = endpoint["url"]
    st = get_state(url)
 
    success, info = check_endpoint(endpoint)
 
    if success:
        if st["alerted"]:
            log.info(f"[{name}] sudah normal lagi (status {info}) -> kirim recovery")
            send_telegram_message(format_recovery_message(name, url, info))
        st["failure_count"] = 0
        st["alerted"] = False
    else:
        st["failure_count"] += 1
        log.warning(f"[{name}] gagal ({info}) - percobaan gagal ke-{st['failure_count']}")
        if st["failure_count"] >= CONSECUTIVE_FAILURE_COUNT and not st["alerted"]:
            log.warning(f"[{name}] melewati batas gagal berturut-turut -> kirim alert")
            send_telegram_message(format_alert_message(name, url, info))
            st["alerted"] = True
 
    return {"name": name, "url": url, "success": success, "info": info}
 
 
# =============================================================================
# LISTENER COMMAND TELEGRAM (/status)
# =============================================================================
 
def listen_for_commands():
    log.info("Listener command Telegram dimulai (ketik /status di chat bot).")
    last_update_id = None
 
    while True:
        try:
            url = f"https://api.telegram.org/bot8825658334:AAFyuOFBNNLNWDnPJ1tUIm9TQUyWP4xoeXo/getUpdates"
            params = {"timeout": 30}
            if last_update_id is not None:
                params["offset"] = last_update_id + 1
 
            resp = requests.get(url, params=params, timeout=35)
            resp.raise_for_status()
            data = resp.json()
 
            for update in data.get("result", []):
                last_update_id = update["update_id"]
 
                message = update.get("message", {})
                text = message.get("text", "").strip().lower()
                chat_id = str(message.get("chat", {}).get("id", ""))
 
                if chat_id != str(TELEGRAM_CHAT_ID):
                    continue
 
                if text == "/status":
                    log.info("Perintah /status diterima, mengecek semua endpoint...")
                    results = check_all_endpoints_now()
                    send_telegram_message(format_status_report(results, auto=False))
 
                elif text == "/stop":
                    if monitoring_active.is_set():
                        monitoring_active.clear()
                        log.info("Perintah /stop diterima -> monitoring di-pause.")
                        send_telegram_message(
                            "⏸️ <b>Monitoring di-pause.</b>\n"
                            "Bot tidak akan mengecek endpoint atau kirim alert sampai "
                            "kamu ketik /start lagi. Command /status tetap bisa dipakai "
                            "untuk cek manual instan."
                        )
                    else:
                        send_telegram_message("⏸️ Monitoring memang sudah dalam kondisi paused.")
 
                elif text == "/start":
                    if not monitoring_active.is_set():
                        monitoring_active.set()
                        log.info("Perintah /start diterima -> monitoring diaktifkan lagi.")
                        send_telegram_message(
                            "▶️ <b>Monitoring diaktifkan lagi.</b>\n"
                            "Bot akan lanjut cek endpoint & kirim alert seperti biasa."
                        )
                    else:
                        send_telegram_message("▶️ Monitoring memang sudah aktif.")
 
        except Exception as e:
            log.error(f"Error di listener command Telegram: {e}")
            time.sleep(5)
 
 
# =============================================================================
# MAIN LOOP
# =============================================================================
 
def run():
    log.info("Website/API Monitor Bot dimulai...")
    log.info(
        f"Memantau {len(ENDPOINTS)} endpoint, cek tiap {POLL_INTERVAL_SECONDS} detik "
        f"({POLL_INTERVAL_SECONDS // 60} menit). Auto status report: {AUTO_STATUS_REPORT}."
    )
 
    set_bot_commands()
 
    command_thread = threading.Thread(target=listen_for_commands, daemon=True)
    command_thread.start()
 
    while True:
        if not monitoring_active.is_set():
            # Sedang di-pause lewat /stop -> jangan cek endpoint, jangan kirim
            # apa-apa, cukup tunggu dan cek lagi nanti (siapa tahu di-/start).
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
 
        cycle_results = []
        for endpoint in ENDPOINTS:
            try:
                result = evaluate_endpoint(endpoint)
                cycle_results.append(result)
            except Exception as e:
                log.error(f"Error tak terduga saat cek {endpoint.get('name')}: {e}")
                cycle_results.append({
                    "name": endpoint.get("name", "?"),
                    "url": endpoint.get("url", "?"),
                    "success": False,
                    "info": f"Error internal: {e}",
                })
 
        # Kirim laporan status otomatis tiap putaran (default tiap 2 menit),
        # supaya kondisi semua endpoint selalu terlihat real-time di Telegram,
        # bukan cuma pas ada perubahan status.
        if AUTO_STATUS_REPORT and cycle_results:
            send_telegram_message(format_status_report(cycle_results, auto=True))
 
        time.sleep(POLL_INTERVAL_SECONDS)
 
 
if __name__ == "__main__":
    run()