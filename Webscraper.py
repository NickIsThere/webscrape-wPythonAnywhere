import random
import smtplib
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import re
from selenium.webdriver.support.wait import WebDriverWait
import os
from dotenv import load_dotenv

load_dotenv()

remote = False
if remote:
    # BrowserStack credentials
    username = os.getenv("username")
    access_key = os.getenv("access_key")

    remote_url = f'https://{username}:{access_key}@hub-cloud.browserstack.com/wd/hub'

    # Browser capabilities
    capabilities = {
        "browser": "Chrome",
        "browser_version": "latest",
        "os": "Windows",
        "os_version": "10",
        "resolution": "1920x1080",
        "name": "Python Selenium WebDriver Example"
    }

    driver = webdriver.Remote(
        command_executor=remote_url,
        desired_capabilities=capabilities
    )
else:
    driver = webdriver.Chrome()

# Apartment scraping parameters
Price_Limit = 2000
Rooms = 3
Stadtteile = ["Binnenstad", "Jekerkwartier", "Kommelkwartier", "Statenkwartier", "Boschstraatkwartier", "Sint Maartenspoort", "Wyck"]

apartments = {}

def dismiss_overlay():
    try:
        time.sleep(random.uniform(2, 4))  # Simulate reading the popup
        cookie_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        cookie_button.click()
    except Exception:
        pass

def get_urls():
    try:
        URLs = driver.find_elements(By.XPATH, "//a[contains(@class, 'listing-search-item__link--title')]")
        return [URL.get_attribute("href") for URL in URLs]
    except Exception as e:
        print(f"Error while fetching URLs: {e}")
        return []

def get_price():
    try:
        prices = driver.find_elements(By.CSS_SELECTOR, "div.listing-search-item__price")
        return [price.get_attribute("textContent").strip() for price in prices]
    except Exception as e:
        print(f"Error while fetching prices: {e}")
        return []

def get_rooms():
    try:
        rooms = driver.find_elements(By.CSS_SELECTOR, "li.illustrated-features__item--number-of-rooms")
        return [room.get_attribute("textContent").strip() for room in rooms]
    except Exception as e:
        print(f"Error while fetching rooms: {e}")
        return []

def get_areas():
    try:
        areas_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'listing-search-item__sub-title')]")
        areas = []
        for element in areas_elements:
            matches = re.findall(r'\((.*?)\)', element.text)
            areas.extend(matches)
        return areas
    except Exception as e:
        print(f"Error while fetching areas: {e}")
        return []

def add_to_Dic(URLs, prices, rooms, areas):
    min_length = min(len(URLs), len(prices), len(rooms), len(areas))
    for i in range(min_length):
        apartments[URLs[i]] = [prices[i], rooms[i], areas[i]]

def get_next_url():
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination__liKingnoname04nk.pagination__link--next"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        return next_button.get_attribute("href")
    except Exception as e:
        print(f"Error while fetching next page URL: {e}")
        return None

def random_interaction():
    actions = ["hover", "scroll", "pause"]
    action = random.choice(actions)
    print(f"Mache grade was zufälliges, {action}")
    if action == "hover":
        elements = driver.find_elements(By.CSS_SELECTOR, "li")
        if elements:
            ActionChains(driver).move_to_element(random.choice(elements)).perform()
            time.sleep(random.uniform(1, 2))
    elif action == "scroll":
        driver.execute_script(f"window.scrollBy(0, {random.randint(80, 200)});")
        time.sleep(random.uniform(1, 2))
    else:
        time.sleep(random.uniform(3, 6))

def extract_numbers(string):
    numbers = re.findall(r'\d+', string)
    return int(''.join(numbers)) if numbers else 0

def dismiss_all_overlays():
    try:
        overlay_button = driver.find_element(By.XPATH, "//button[contains(@class, 'close-modal')]")
        overlay_button.click()
    except Exception:
        pass

def wait_for_page_load():
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'listing-search-item__link--title')]"))
        )
    except Exception as e:
        print(f"Error waiting for page to load: {e}")


driver.get(os.getenv("website"))
wait_for_page_load()
dismiss_overlay()
dismiss_all_overlays()

current_url = driver.current_url

while current_url:
    try:
        wait_for_page_load()
        URLs = get_urls()
        prices = get_price()
        rooms = get_rooms()
        areas = get_areas()

        add_to_Dic(URLs, prices, rooms, areas)
        print(f"Collected {len(apartments)} apartments so far.")

        random_interaction()

        # Random sleep to simulate human behavior
        if random.randint(1, 5) == 1:
            time.sleep(random.uniform(10, 20))

        # Get the next page URL
        next_url = get_next_url()

        # If there's a next page, visit it; otherwise, stop the loop
        if next_url:
            random_interaction()
            time.sleep(random.uniform(5, 7))
            driver.get(next_url)
            # Ensure the page has loaded
            wait_for_page_load()
            current_url = next_url
        else:
            current_url = None
            print("No more pages to scrape.")

    except Exception as e:
        print(f"Error: {e}")
        current_url = None
        print("Stopping due to an error.")

driver.quit()

sorted_apartments = {}
for apartment in apartments:
    if (int(extract_numbers(apartments[apartment][0]))) <= Price_Limit and int(extract_numbers(apartments[apartment][1])) >= Rooms and apartments[apartment][2] in Stadtteile:
        sorted_apartments[apartment] = apartments[apartment]

print(sorted_apartments)


email_content = "Subject: Frische Wohnungen\n\nAlles bereits gefiltert, sag bescheid wenn ich was ändern soll\n\n"
for apartment, details in sorted_apartments.items():
    email_content += f"Link: {apartment}\nMiete: {details[0]}\nZimmer: {details[1]}\nOrt: {details[2]}\n\n"

email_content = email_content.encode('utf-8')

email = os.getenv("email_send")
password = os.getenv("email_pass")
email_empfaenger = os.getenv("email_rec")

# Send the email with smtp

with smtplib.SMTP("smtp.gmail.com", 587) as connection:
    connection.starttls()
    connection.login(user=email, password=password)
    connection.sendmail(
        from_addr=email,
        to_addrs=email_empfaenger,
        msg=email_content
    )

print("Email sent")
