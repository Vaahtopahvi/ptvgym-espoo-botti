#!/usr/bin/env python3

"""Requirements: 
- requests- beautifulsoup4
- python-dotenv"""

import os
import time
import logging
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime

load_dotenv()

# config

TARGET_URL = "https://kauppa.ptvgym.fi/cg/454/espoo/"

# ----- Discord webhook
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# interval to check in seconds. 120 = 2 minutes.
CHECK_INTERVAL_SECONDS = 120

# used to detect "empty" state of no products
NO_PRODUCTS_TEXT = "Tuotteita ei löytynyt"

# logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# core logic

def fetch_page() -> str | None:
    """Fetch the page HTML. Returns None on error."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; SaliJasenyysBotti/1.0; "
            "personal subscription checker)"
        )
    }
    try:
        resp = requests.get(TARGET_URL, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        log.error("Failed to fetch page: %s", e)
        return None

def has_products(html: str) -> bool:
    """return true if the page contains product listings"""
    soup = BeautifulSoup(html, "html.parser")

    #primary signal
    page_text = soup.get_text()
    if NO_PRODUCTS_TEXT in page_text:
        return False

    #secondary signal. look for products and add to cart buttons
    product_indicators = [
        soup.find("a", class_="jasenyys-espoo-toistuva-korttiveloitus"),
        soup.find("h4", class_="product-title"),
        soup.find("button", class_="btn btn-oldstyle-info btn-block"),
        soup.find("a", class_="ennakkojasenyys-espoo-toistuva-korttiveloitus"),
        soup.find("span", class_="product-price"),
        soup.find("div", class_="container-folio row"),
        soup.find("div", class_="container-folio row product-grid"),
        soup.find("div")
    ]
    return any(product_indicators)

def extract_product_names(html: str) -> list[str]:
    """try pulling product names from the page"""
    soup = BeautifulSoup(html, "html.parser")
    names = []
    # common patterns for product title elements
    for tag in soup.select(".product-title, .product-name, h2.title, h3.title, h4.title"):
        text = tag.get_text(strip=True)
        if text:
            names.append(text)
    return names[:10] #cap at 10

def send_discord_alert(product_name: list[str]) -> None:
    """ send a discord webhook notification """
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "web hook here ###":
        log.warning("Discord webhook URL not configured - skipping notification.")
        return

    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    description = (
        "Jäsenyydet löytyivät!!!!!!!!!!!"
        if not product_name
        else "\n".join(f"• {n}" for n in product_name)
    )

    payload = {
        "username": "PTV GYM Monitoring",
        "embeds" : [
            {
                "title": "PTV GYM ESPOO - JÄSENYYDET JULKI. NYT TILAAMAAN POJAT!!!!!",
                "description": description,
                "url": TARGET_URL,
                "color": 0x00A651,  # ptv gymin vihreä :D
                "fields": [
                    {"name": "Page", "value": TARGET_URL, "inline": False},
                    {"name": "Detected at", "value": timestamp, "inline": True},
                ],
                "footer": {"text": "main.py"}
            }
        ],
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        log.info("Discord notification sent succesfully")
    except requests.RequestException as e:
        log.error("Failed to send discord notification: %s", e)

def send_discord_heartbeat(check_count: int) -> None:
    """sending periodic message, to confirm bot is still alive"""
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "url tähä #######":
        return

    payload = {
        "username": "PTV GYM Monitoring",
        "content": (
            f"Tarkkailen nyt... ({check_count} kertaa. "
            f"Jäsenyydet tarkistettu {datetime.now().strftime('%H:%M')})"
        ),
    }
    try:
        request.post(DISCORD_WEBHOOK_URL, json-payload, timeout=10)
    except requests.RequestException:
        pass  # Heartbeat failures are non-critical




# --- main loop

def main() -> None:
    log.info("PTV GYM Espoon salin tarkkailu aloitettu")
    log.info("Kohde : %s", TARGET_URL)
    log.info("Aikaa tarkistuksen välissä: %d sekuntia", CHECK_INTERVAL_SECONDS)

    if DISCORD_WEBHOOK_URL == "tänne taas":
        log.warning(
            "Aseta Discord webhook! #####"
            "Set DISCORD_WEBHOOK_URL env var or edit the script."
        )

    check_count = 0
    alerted = False

    while True:
        check_count += 1
        log.info("Tarkistettu #%d - tarkistetaan sivua...", check_count)

        html = fetch_page()
        if html is None:
            log.warning("Ohitetaan tämä tarkistus kun sivun tietoja ei löytynyt.")
        elif has_products(html):
            log.info("JÄSENYYDET LÖYTYIVÄT!. Lähetetään discord viesti......")
            names = extract_product_names(html)
            send_discord_alert(names)
            alerted = True
            log.info("Ilmoitus lähetetty. Tarkistellaan vielä sivua muutosten varalta...")
            # hidastetaan tarkastusväliä
            time.sleep(CHECK_INTERVAL_SECONDS * 5)
            continue
        else:
            log.info("Sivu näyttää vieläkin samalta. Ei tuotteita löytynyt.")

        # lähetetään heartbeat ilmoitus joka tunti
        if check_count % 30 == 0 and not alerted:
            send_discord_heartbeat(check_count)

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()