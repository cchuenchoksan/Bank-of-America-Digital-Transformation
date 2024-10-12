from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import requests
from bs4 import BeautifulSoup
from time import sleep
import random
from tqdm import tqdm

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd



def pause_screen(mid_val):
    wait_time = min(abs(3.14 + mid_val + random.normalvariate(0, 1)), 5)
    sleep(wait_time)


def fill_in_search_bar(driver, text1, text2):
    search_field_1 = Select(driver.find_element(By.ID, "searchField1"))
    search_field_1.select_by_value('AANM')

    search_field_2 = Select(driver.find_element(By.ID, "searchField2"))
    search_field_2.select_by_value('AANM')

    search_text_1 = driver.find_element(By.ID, "searchText1")
    search_text_1.send_keys(text1)

    search_text_2 = driver.find_element(By.ID, "searchText2")
    search_text_2.send_keys(text2)

    button = driver.find_element(By.ID, "basicSearchBtn")
    button.click()
    pause_screen(3)


def get_df(driver):
    table = driver.find_element(By.ID, "searchResults_wrapper").get_attribute('innerHTML')
    df = pd.read_html(table)[0]
    return df


def press_next(driver):
    try:
        driver.find_element(By.ID, "paginationNextItem").click()
        pause_screen(2)
        return True
    except:
        print("WARNING: Cannot press next")
        return False


def get_session_token(driver):
    return driver.find_elements(By.CLASS_NAME, "btn-link")[-1].get_attribute("href").split("Token=")[-1]


def get_num_pages(driver):
    inner_text = driver.find_element(By.ID, "pageInfo").get_attribute("innerText")
    words = inner_text.split(" ")
    return int(words[-1])


def get_patent_link(id, sesh_token):
    id = id.split("-")[1]
    return f"https://ppubs.uspto.gov/dirsearch-public/patents/html/{id}?source=US-PGPUB&requestToken={sesh_token}"


def get_driver():
    driver = webdriver.Chrome()
    driver.get("https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsbasic.html")
    pause_screen(3)  # for screen to load
    return driver


if __name__ == "__main__":
    driver = get_driver()

    fill_in_search_bar(driver, "Bank", "America")  # NOTE: A pop-up screen is present in some cases
    token = get_session_token(driver)
    print("token: ", token)

    num_pages = get_num_pages(driver)
    print("num_pages: ", num_pages)
    # num_pages = 1  # NOTE: Remove this for actual run

    # Get all of the patents metadata using selenium
    dataframes = []
    for _ in range(num_pages):
        df = get_df(driver)
        dataframes.append(df)
        res = press_next(driver)  # NOTE: Not sure what will happen at the last page but should be fine as button should just be disabled
        if res is False:
            break
    driver.quit()
    
    df_overall = pd.concat(dataframes)
    df_overall = df_overall[["Document/Patent number", "Title", "Inventor name", "Publication date"]]
    df_overall.to_csv("./data/results.csv", index=False)

    # Get all the patents abstracts and other data using bs
    with open("./data/results_abstract.csv", 'w') as f:
        f.write("Document/Patent number|abstract|filed_date|name\n")
        patent_numbers = list(df_overall["Document/Patent number"])
        for patent_number in tqdm(patent_numbers):
            abstract = ""
            name = ""
            date = ""
            patent_link = get_patent_link(patent_number, token)
            soup = BeautifulSoup(requests.get(patent_link).content, "html.parser")

            if soup.contents[0] == '{ "message": "Too many requests" }':
                wait_time = 8
                while soup.contents[0] == '{ "message": "Too many requests" }':
                    print("Access Denied: too many requests")
                    pause_screen(wait_time)
                    soup = BeautifulSoup(requests.get(patent_link).content, "html.parser")
                    wait_time *= 2

            if str(soup) == 'unauthorized':
                print("Access Denied: sesssion timeout")
                driver = get_driver()
                fill_in_search_bar(driver, "Bank", "America")  # NOTE: A pop-up screen is present in some cases
                token = get_session_token(driver)
                driver.quit()
                patent_link = get_patent_link(patent_number, token)
                soup = BeautifulSoup(requests.get(patent_link).content, "html.parser")
            
            p_tags = soup.find_all('p')
            abstract = p_tags[0].text
            for i, p_tag in enumerate(p_tags[:min(len(p_tags)-1, 20)]):  # NOTE: Using the top 20 here. Might need to increase or decrease
                if p_tag.text.strip() == "Applicant:":
                    name = p_tags[i+1].text
                if p_tag.text.strip() == "Filed:":
                    date = p_tags[i+1].text

            f.write(f"{patent_number}|{abstract}|{date}|{name}\n")
            pause_screen(3)