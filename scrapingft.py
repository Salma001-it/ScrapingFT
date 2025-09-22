# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os
from huggingface_hub import login
from datasets import load_dataset, Dataset
import time
import pandas as pd
import openpyxl
df_tickers=pd.read_excel("SP500CompanyNameTicker.xlsx")
companies=df_tickers["Company"].to_list()

# Lista aziende da scrapare
#companies = ["Microsoft", "Apple", "Google", "Amazon", "Facebook",
#             "Tesla", "IBM", "Intel", "Netflix", "Adobe"]

# Configurazione Selenium headless
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

dataset = []

from huggingface_hub import login

login(token="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")

for company in companies:
    print(f"Scraping {company}...")
    link = f"https://www.ft.com/search?q={company}"
    driver = webdriver.Chrome(options=options)

    for i in range(2, 15):  # Pagine da navigare
        driver.get(link)
        wait = WebDriverWait(driver, 10)

        # Gestione banner cookie
        try:
            iframe = wait.until(EC.presence_of_element_located((By.ID, "sp_message_iframe_1349677")))
            driver.switch_to.frame(iframe)
            accept_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[title='Accept'], button[aria-label='Accept']")))
            accept_button.click()
            driver.switch_to.default_content()
        except:
            pass

        lista = driver.find_elements(By.CLASS_NAME, "search-results__list-item")

        for index, titolo in enumerate(lista, start=1+(i-1)*len(lista)):
            try:
                link_element = titolo.find_element(By.CLASS_NAME, "js-teaser-heading-link")
                url_articolo = link_element.get_attribute("href")
                testo = link_element.text

                riassunto_element = titolo.find_element(By.CLASS_NAME, "js-teaser-standfirst-link")
                riassunto = riassunto_element.text

                try:
                    time_element = titolo.find_element(By.CLASS_NAME, "o-teaser__timestamp-date")
                    datetime_attr = time_element.get_attribute("datetime")
                    dt = datetime.strptime(datetime_attr, "%Y-%m-%dT%H:%M:%S%z")
                    data = dt.strftime("%Y-%m-%d")
                    ora = dt.strftime("%H:%M:%S")
                except:
                    data = ""
                    ora = ""

                dataset.append({
                    "Company": company,
                    "Index": index,
                    "Title": testo,
                    "Link": url_articolo,
                    "Summary": riassunto,
                    "Date": data,
                    "Time": ora
                })

            except Exception as e_inner:
                print(f"Errore elemento {index}: {e_inner}")

    driver.quit()
    time.sleep(2)  # piccola pausa tra aziende

# Salva in DataFrame pandas
df = pd.DataFrame(dataset)
print(df)

# Repo Hugging Face
repo_id = "SelmaNajih001/FT_MultiCompany"

# Carica dataset esistente
try:
    old = load_dataset(repo_id, split="train")
    old_df = old.to_pandas()
except:
    old_df = pd.DataFrame()

# Unisci vecchi + nuovi e rimuovi duplicati
all_df = pd.concat([old_df, df]).drop_duplicates(subset=["Company", "Title", "Date"], keep="last")
all_df = all_df.reset_index(drop=True)

# Crea dataset Hugging Face e pubblica
final_ds = Dataset.from_pandas(all_df)
final_ds.push_to_hub(repo_id, private=False)

print("Dataset aggiornato con successo!")
