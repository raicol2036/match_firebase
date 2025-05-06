import streamlit as st
import pandas as pd
from streamlit.components.v1 import html
from datetime import datetime

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# 初始化 Firebase（只做一次）
if "firebase_initialized" not in st.session_state:
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        })
        firebase_admin.initialize_app(cred)
    st.session_state.firebase_initialized = True

db = firestore.client()

st.set_page_config(page_title="高爾夫Match play-1 vs N", layout="wide")
st.title("\u26f3\ufe0f \u9ad8\u723e\u592bMatch play - 1 vs N")

# ========== 新增：從 Firebase 讀取今日成績 ==========
if st.button("\ud83d\udcc5 \u5f9e Firebase \u8b80\u53d6\u4eca\u65e5\u7403\u54e1\u6210\u7e3e"):
    today_str = datetime.today().strftime("%Y-%m-%d")
    doc_ref = db.collection("golf_games").document(today_str)
    doc = doc_ref.get()
    if doc.exists:
        game_data = doc.to_dict()
        st.success(f"\u5df2\u8b80\u53d6 {today_str} \u7684\u6bd4\u8cfd\u8cc7\u6599")
        st.json(game_data)
    else:
        st.error(f"\u67e5\u7121 {today_str} \u7684\u6bd4\u8cfd\u8cc7\u6599")

# ...這裡是原本的主程式碼，照舊保留，從 st.set_page_config() 之後繼續寫...
