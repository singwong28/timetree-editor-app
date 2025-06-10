import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

# ---------- Google Sheets 授權 ----------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["GOOGLE_SHEETS_CREDENTIALS"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["SHEET_ID"]).worksheet(st.secrets["SHEET_NAME"])

# ---------- Streamlit UI ----------
st.title("📆 TimeTree ➜ Google Sheets 編更工具")

url = st.text_input("請貼上 TimeTree 分享連結（例如：https://timetreeapp.com/calendars/xxxxx）")

if url:
    with st.spinner("⏳ 正在讀取 TimeTree 資料..."):

        today = datetime.today()
        end_date = today + timedelta(weeks=3)
        end_date += timedelta(days=(5 - end_date.weekday()) % 7)  # 補到最近週六

        date_range = [(today + timedelta(days=i)).strftime("%-m/%-d") for i in range((end_date - today).days + 1)]
        results = []

        try:
            res = requests.get(url)
            soup = BeautifulSoup(res.text, "html.parser")
            raw_text = soup.get_text()

            for d in date_range:
                pattern = re.compile(rf"{d}.*?(?=\d{{1,2}}/\d{{1,2}}|\Z)", re.DOTALL)
                matches = pattern.findall(raw_text)

                for match in matches:
                    if re.search(r"\b(A|B)\b", match):
                        line = match.strip().replace("\n", " ")

                        # 場地
                        location = "A" if "A" in line else "B"

                        # 時間擷取
                        time_match = re.search(r"(\d{1,2})[:\-\.](\d{1,2})", line)
                        time_text = ""
                        if time_match:
                            h1, h2 = time_match.groups()
                            time_text = f"{h1.zfill(2)}-{h2.zfill(2)}"

                        # 人數
                        people_match = re.search(r"(\d{2,})\s*位", line)
                        people_text = ""
                        if people_match and int(people_match.group(1)) > 30:
                            people_text = f"{int(people_match.group(1))}位"

                        # 組合格式
                        summary = f"{d} {location} {time_text}".strip()
                        if people_text:
                            summary += f" {people_text}"
                        results.append([summary])

        except Exception as e:
            st.error("❌ 無法讀取 TimeTree 資料：" + str(e))

        if results:
            st.success(f"✅ 成功讀取 {len(results)} 條活動資料，已寫入 Google Sheets！")
            for r in results:
                st.write(r[0])

            # 寫入試算表
            sheet.clear()
            sheet.append_rows([["日期與排班資訊"]])
            sheet.append_rows(results)
        else:
            st.warning("⚠️ 沒有找到任何活動資料")
