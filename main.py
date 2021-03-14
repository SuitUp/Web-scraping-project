"""
main module for selenium based web scraping pipeline
"""
# imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import DRIVER_BIN
from config import OUTPUT_DIR

from scrapping_links import webpage_dict

import time
import json
from bs4 import BeautifulSoup
import pandas as pd
import os
import csv
import joblib

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

speciality_links = webpage_dict

driver = webdriver.Chrome(executable_path=DRIVER_BIN, options=options)
wait = WebDriverWait(driver, 10)
load_more_xpath = "//div[text()='Load More']"
l = {}
for key, value in speciality_links.items():
    l[key] = []
    for url in value:
        print(f"automated for url ---> {url}")
        driver.get(url)
        discipline_page = driver.current_window_handle
        no_of_schools = (wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'Box-w0dun1-0.SearchHUD__Text-sc-1bf8uwa-1.iOBzTK.lliioc')))).text.split(' ')[0]
        # print(no_of_schools)
        no_of_schools = int(int(no_of_schools)/32)

        if no_of_schools >= 1:
            for i in range(no_of_schools):
                # element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[text()='Load More']")))
                wait.until(EC.presence_of_element_located((By.XPATH, load_more_xpath)))
                element = driver.find_element_by_xpath(load_more_xpath)
                print(element)
                school_page = driver.current_window_handle
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(5)
                # (wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Load More']")))).click()
                wait.until(EC.presence_of_element_located((By.XPATH, load_more_xpath)))
                # handling for possible overlays and popups in each school's page
                school_overlays = False 
                for handle in driver.window_handles:
                    if handle != school_page:
                        school_overlays = True
                if school_overlays == True:
                    driver.switch_to.window(school_page)
                    
                driver.find_element_by_xpath(load_more_xpath).click()
        
        time.sleep(5)
        page_source = driver.page_source
        # 'sailthru-overlay-close'
        # handling for possible overlays and popups in each school's page
        discipline_overlays = False 
        for handle in driver.window_handles:
            if handle != discipline_page:
                discipline_overlays = True
        if discipline_overlays == True:
            driver.switch_to.window(discipline_page)

        soup = BeautifulSoup(page_source, 'lxml')
        titles = soup.find_all('h3', class_='Heading__HeadingStyled-sc-1w5xk2o-0-h3 iYIdlp Heading-sc-1w5xk2o-1 bEFVwd')
        ranks = soup.find_all('ul', class_='RankList__List-sc-2xewen-0 fRavFb DetailCardCompare__CardRankList-sc-1x70p5o-9 djzeGY Hide-kg09cx-0 bXWqHm')
        locations = soup.find_all('p', class_='Paragraph-sc-1iyax29-0 gJYRMs')
        for title, rank, loc in zip(titles, ranks, locations):
            d = {}
            d[title.text] = {}
            d[title.text]['city'] = loc.text.split(', ')[0]
            d[title.text]['state'] = loc.text.split(', ')[1]
            ranks = rank.text.replace('#', '\n').replace('Unranked', '\n').splitlines()
            ranks = filter(None, ranks)
            for i in ranks:
                d[title.text][i.split('in ')[1].replace(u'\xa0', u'').replace('(tie)', '')] = i.split('in ')[0].replace('#','')
            l[key].append(d)
            try:
                joblib.dump(l, f"{OUTPUT_DIR}url_dumps/{speciality_links[key]}_{speciality_links[value]}.pkl")
                print(f"dumped {speciality_links[key]}_{speciality_links[value]} dict..")
            except:
                pass
    print(l[key])
# print(l)
joblib.dump(l, f"{OUTPUT_DIR}final_dumps/usnews.pkl")
print(f"Scrapping completed...")
driver.quit()
