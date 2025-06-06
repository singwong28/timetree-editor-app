import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

# ---------- 設定範圍及授權 ----------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["SHEET_ID"]).worksheet(st.secrets["SHEET_NAME"])

# ---------- UI ----------
st.title("🗓️ TimeTree 值班表轉換工具")
url = st.text_input("請貼上 TimeTree 分享連結（例如：https://timetreeapp.com/calendars/xxxxx）")

if url:
    with st.spinner("讀取中..."):

        # 計算日期範圍（今天到三週後的星期六）
        today = datetime.today()
        end_date = today + timedelta(weeks=3)
        end_date += timedelta(days=(5 - end_date.weekday()) % 7)  # 下一個週六

        date_range = [(today + timedelta(days=i)).strftime("%-m/%-d") for i in range((end_date - today).days + 1)]

        # 儲存結果
        results = []

        # 嘗試抓頁面
        try:
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')

            # 找出所有事件文字
            raw_text = soup.get_text()

            # 對每一天進行搜尋
            for d in date_range:
                pattern = re.compile(rf"{d}.*?(?=\d+/|\Z)", re.DOTALL)
                matches = pattern.findall(raw_text)

                for match in matches:
                    if re.search(r"\b(A|B)\b", match):  # A / B 場地
                        line = match.strip().replace("\n", " ")

                        # 擷取時間
                        time_match = re.search(r"(\d{1,2})[:\-\.](\d{1,2})", line)
                        time_text = ""
                        if time_match:
                            h1, h2 = time_match.groups()
                            time_text = f"{h1.zfill(2)}-{h2.zfill(2)}"

                        # 擷取人數（30+ 才寫出來）
                        people_match = re.search(r"(\d{2,})\s*位", line)
                        people_text = ""
                        if people_match and int(people_match.group(1)) > 30:
                            people_text = f"{int(people_match.group(1))}位"

                        # 場地（A or B）
                        location = "A" if "A" in line else "B"

                        # 最終格式
                        formatted = f"{d} {location} {time_text}".strip()
                        if people_text:
                            formatted += f" {people_text}"
                        results.append([formatted])

        except Exception as e:
            st.error("❌ 讀取失敗：" + str(e))

        # 顯示 + 寫入
        if results:
            st.success(f"找到 {len(results)} 條資料，已寫入 Google Sheets ✅")
            for r in results:
                st.write(r[0])

            sheet.clear()
            sheet.append_rows([["日期與排班資訊"]])  # 標題列
            sheet.append_rows(results)
        else:
            st.warning("沒有找到任何符合的事件 🙁")
