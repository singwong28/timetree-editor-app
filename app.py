import streamlit as st
import re

st.title("TimeTree 編更表轉換器")

text_input = st.text_area("請貼上 TimeTree 活動內容", height=300)

def parse_entry(text):
    lines = text.split('\n')
    date = ""
    time_range = ""
    people = ""
    shift = "B"

    for line in lines:
        if "日期" in line:
            date_match = re.search(r"\d{1,2}/\d{1,2}", line)
            if date_match:
                date = date_match.group()
        if "時間" in line:
            time_match = re.search(r"(\d{1,2}):?(\d{2})?-?(\d{1,2}):?(\d{2})?", line)
            if time_match:
                start_hour = int(time_match.group(1))
                end_hour = int(time_match.group(3))
                # 24hr to 12hr
                if start_hour >= 12: start_hour -= 12
                if end_hour >= 12: end_hour -= 12
                time_range = f"{start_hour}-{end_hour}"
        if "人數" in line or "位" in line:
            ppl_match = re.search(r"(\d+位[^\s]*)", line)
            if ppl_match:
                people = ppl_match.group(1)
        if "A+b" in line or "a+b" in line:
            shift = "A+B"
        elif "A" in line:
            shift = "A"
        elif "B" in line:
            shift = "B"

    if date and time_range:
        return f"{date} {shift} {time_range} {people}"
    else:
        return ""

if st.button("轉換"):
    results = []
    chunks = text_input.split("晶晶")  # 根據你提供的原始資料格式分段
    for chunk in chunks:
        result = parse_entry(chunk)
        if result:
            results.append(result)
    if results:
        st.success("轉換成功！")
        st.code("\n".join(results), language='text')
    else:
        st.warning("找不到可轉換內容，請檢查格式。")
