import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def fetch_timetree_html(email, password, calendar_id):
    """Login to TimeTree and fetch rendered calendar page HTML."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://timetreeapp.com/signin")
        
        email_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        password_field = driver.find_element(By.NAME, "current-password")
        email_field.send_keys(email)
        password_field.send_keys(password)

        password_field.submit()
        
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".calendar-item")))
        
        driver.get(f"https://timetreeapp.com/calendars/{calendar_id}")
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".event-item")))

        rendered_html = driver.page_source
        return rendered_html
    
    except Exception as e:
        st.error(f"登入或取得日曆時發生錯誤: {e}")
        return ""
    finally:
        driver.quit()


def parse_timetree_html(html):
    """解析渲染後HTML，整理出需要的数据。 """
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for item in soup.select('.event-item'):
        time = item.select_one('.time').get_text(strip=True) if item.select_one('.time') else ''
        name = item.select_one('.name').get_text(strip=True) if item.select_one('.name') else ''
        events.append([time, name])

    return events


def write_to_sheets(events, credentials_file, sheet_key, sheet_name):
    """登入 Google Sheets，寫入整理出的 events。"""
    creds = Credentials.from_service_account_file(credentials_file, ['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(sheet_key).worksheet(sheet_name)

    sheet.clear()
    sheet.append_row(['Time', 'Event Name'])

    for event in events:
        sheet.append_row(event)

    return "寫入成功!"

def main():
    st.title("📆 TimeTree To Google Sheets")
    st.write("登入 TimeTree, 抓取日曆事件後寫入 Google Sheets")

    if st.button("執行"):
        email = st.secrets["EMAIL"]
        password = st.secrets["PASSWORD"]
        calendar_id = st.secrets["CALENDAR_ID"]
        sheet_key = st.secrets["SHEET_ID"]
        sheet_name = st.secrets["SHEET_NAME"]
        credentials_file = "app/credentials/service_account.json"

        rendered = fetch_timetree_html(email, password, calendar_id)
        if rendered:
            events = parse_timetree_html(rendered)
            if events:
                result = write_to_sheets(events, credentials_file, sheet_key, sheet_name)
                st.success(result)
            else:
                st.error("未找到任何事件")
        else:
            st.error("登入 TimeTree 失敗")

if __name__ == "__main__":
    main()
