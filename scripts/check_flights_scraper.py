import json
import time
import requests
import sys
import os
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile
import time

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

def scrape_flights_from_homepage(config):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium-browser"

    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")

    service = Service("/usr/lib/chromium-browser/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://www.skyscanner.es/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))

        # Cierre de cookies
        try:
            print("[DEBUG] Intentando cerrar cookies...")
            for btn in driver.find_elements(By.TAG_NAME, "button"):
                if "Aceptar solo lo esencial" in btn.text:
                    btn.click()
                    print("[DEBUG] Botón de cookies encontrado y pulsado")
                    time.sleep(1)
                    break
        except Exception as e:
            print(f"[DEBUG] Cookie modal no visible: {e}")

        # DEBUG: Captura antes de fallo posible
        driver.save_screenshot("pantalla_debug.png")

        # ORIGEN
        origin_button = wait.until(EC.element_to_be_clickable((By.ID, "OriginButton")))
        origin_button.click()
        origin_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Desde?']")))
        origin_input.clear()
        origin_input.send_keys(config["origin"])
        time.sleep(1)
        origin_input.send_keys(Keys.DOWN, Keys.ENTER)

        # DESTINO
        destination_button = wait.until(EC.element_to_be_clickable((By.ID, "DestinationButton")))
        destination_button.click()
        dest_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='A dónde?']")))
        dest_input.clear()
        dest_input.send_keys(config["destination"])
        time.sleep(1)
        dest_input.send_keys(Keys.DOWN, Keys.ENTER)

        # FECHAS
        date_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='dates-btn']")))
        date_button.click()
        time.sleep(1)

        def select_date(fecha):
            yyyy, mm, dd = fecha.split("-")
            selector = f"button[aria-label*='{int(dd)} de {get_spanish_month(mm)} de {yyyy}']"
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()
            time.sleep(1)

        select_date(config["departure_date"])
        select_date(config["return_date"])

        # Confirmar búsqueda
        confirm_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='search-controls-submit-button']")))
        confirm_button.click()

        # Esperar resultados
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.DayViewItinerary")))
        time.sleep(5)

        flight_titles = driver.find_elements(By.CSS_SELECTOR, "div.DayViewItinerary")[:3]
        results = [f.text for f in flight_titles if f.text.strip()]
        print("[DEBUG] Vuelos encontrados:")
        for r in results:
            print(r)

        return results

    finally:
        driver.quit()



def get_spanish_month(mm):
    meses = {
        "01": "enero", "02": "febrero", "03": "marzo", "04": "abril", "05": "mayo", "06": "junio",
        "07": "julio", "08": "agosto", "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
    }
    return meses[mm]

def main():
    config = load_config()
    flights = scrape_flights_from_homepage(config)

    if not flights:
        print("No se encontraron vuelos.")
        return
    else:
        print("[DEBUG] Vuelos encontrados:")
        for f in flights:
            print(f)

    body = "\n\n".join(flights)

    print("[DEBUG] Tratando de enviar email a : ", config["emails"])
    print("[DEBUG] Contenido del email:\n", body)
    send_email(config["emails"], "Top 3 vuelos baratos desde Skyscanner", body)
    print("[DEBUG] Email enviado correctamente:\n", body)
if __name__ == "__main__":
    main()
