import json
import time
import requests
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from utils.email_sender import send_email
from selenium.webdriver.chrome.service import Service

CONFIG_URL = "https://raw.githubusercontent.com/Lusku/skyscanner-alert/main/config/flight_params.json"

def load_config():
    response = requests.get(CONFIG_URL)
    print("[DEBUG] Respuesta cruda desde GitHub:")
    print(response.text)
    return json.loads(response.text)

def build_url(config):
    return (
        f"https://www.skyscanner.es/transporte/vuelos/"
        f"{config['origin'].lower()}/{config['destination'].lower()}/"
        f"{config['departure_date'].replace('-', '')}/"
        f"{config['return_date'].replace('-', '')}/"
        f"?adults=1"
    )

def scrape_flights(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/snap/bin/chromium"

    service = Service("/usr/lib/chromium-browser/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)

    time.sleep(15)  # espera a que cargue todo

    results = []
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='offer-listing']")[:3]
        for card in cards:
            price = card.find_element(By.CSS_SELECTOR, "div[data-test-id='listing-price-dollars']").text
            airline = card.find_element(By.CSS_SELECTOR, "span[data-test-id='airline-name']").text
            times = card.find_elements(By.CSS_SELECTOR, "div[data-test-id='departure-time']")
            departure = times[0].text
            arrival = times[1].text

            results.append({
                "price": price,
                "airline": airline,
                "departure": departure,
                "return": arrival
            })
    except Exception as e:
        print("Error durante scraping:", e)
    finally:
        driver.quit()

    return results

def main():
    config = load_config()
    url = build_url(config)
    flights = scrape_flights(url)

    if not flights:
        print("No se encontraron vuelos.")
        return
    else:
        print("[DEBUG] Vuelos encontrados:")
        for f in flights:
            print(f)

    body = "\n\n".join([
        f"{f['price']} - {f['airline']} - Ida: {f['departure']} / Vuelta: {f['return']}" for f in flights
    ])
    print("[DEBUG] Tratando de enviar email a : ", config["emails"])
    print("[DEBUG] Contenido del email:\n", body)
    send_email(config["emails"], "Top 3 vuelos baratos desde Skyscanner", body)
    print("[DEBUG] Email enviado correctamente:\n", body)
if __name__ == "__main__":
    main()
