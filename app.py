import streamlit as st
import os
import json
import requests
import google.generativeai as genai
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Smart Irrigation System", page_icon="🪴", layout="wide")
st_autorefresh(interval=5000, limit=None, key="datarefresh")

FIREBASE_URL = "https://smart-irrigation-system-oron-default-rtdb.firebaseio.com"

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Heebo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #f4f7f6; background-image: linear-gradient(120deg, #e0c3fc 0%, #8ec5fc 100%); opacity: 0.95; }
    [data-testid="column"] { 
        background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); 
        border-radius: 20px; padding: 25px 15px; 
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07); border: 1px solid rgba(255, 255, 255, 0.5); 
        text-align: center; transition: transform 0.3s ease;
    }
    .planter-container { position: relative; margin-top: 25px; }
    .plant-wrapper { position: absolute; top: -65px; left: 0; width: 100%; display: flex; justify-content: center; z-index: 10; pointer-events: none; }
    @keyframes growUp { 0% { transform: scale(0) translateY(40px); opacity: 0; } 60% { transform: scale(1.15) translateY(-10px); opacity: 1; } 100% { transform: scale(1) translateY(0); opacity: 1; } }
    .plant-emoji { font-size: 5.5rem; animation: growUp 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; filter: drop-shadow(0px 12px 10px rgba(0,0,0,0.25)); }
    .stTextInput>div>div>input { border-radius: 10px; border: 2px solid #e0e0e0; text-align: center; font-weight: 600; margin-bottom: 5px; }
    .main-title { text-align: center; font-size: 4rem; font-weight: 800; color: #2c3e50; padding-top: 10px; margin-bottom: 0;}
    .sub-title { text-align: center; font-size: 1.2rem; color: #34495e; margin-bottom: 40px;}
    .progress-bg { background-color: #eee; border-radius: 10px; height: 12px; width: 100%; margin: 10px 0; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 10px; transition: width 1s ease-in-out; }
    .ai-threshold-box { background: #e0f2f1; border-radius: 10px; padding: 10px; margin-top: 10px; border: 1px dashed #26a69a; color: #00695c; font-weight: 600; font-size: 0.95rem; }
    .welcome-card { background: white; padding: 40px; border-radius: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); max-width: 600px; margin: 80px auto; text-align: center; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'profile_name' not in st.session_state: st.session_state.profile_name = ""
if 'api_key' not in st.session_state: st.session_state.api_key = ""

def get_firebase_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/system.json")
        if response.status_code == 200 and response.json():
            return response.json()
    except: pass
    return {"tank_level": 50, "planters": [{"moisture": 50, "lower": 0, "upper": 0} for _ in range(5)]}

def update_thresholds_in_firebase(index, lower, upper):
    try:
        requests.patch(f"{FIREBASE_URL}/system/planters/{index}.json", json={
            "lower": lower, "upper": upper
        })
    except: pass

if not st.session_state.logged_in:
    st.markdown("<br><br><h1 style='text-align: center; color: #2c3e50;'>🌿 Smart Irrigation System</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
        input_name = st.text_input("שם פרופיל:", placeholder="אורון")
        input_key = st.text_input("מפתח Gemini API:", type="password")
        if st.button("התחל לעבוד 🚀"):
            if input_name and input_key:
                st.session_state.logged_in = True
                st.session_state.profile_name = input_name
                st.session_state.api_key = input_key
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
else:
    with st.sidebar:
        st.success(f"מחובר: **{st.session_state.profile_name}**")
        if st.button("התנתק"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<h1 class='main-title'>🌿 Smart Irrigation System</h1>", unsafe_allow_html=True)
    firebase_data = get_firebase_data()
    tank_level = firebase_data.get("tank_level", 50)
    planters_data = firebase_data.get("planters", [{"moisture": 50, "lower": 0, "upper": 0} for _ in range(5)])

    if tank_level <= 10:
        st.error(f"🚨 אזהרה: מפלס המים במיכל נמוך מאוד ({tank_level}%)!")
    else:
        st.info(f"💧 מפלס המים במיכל: {tank_level}%")

    if 'previous_plants' not in st.session_state: st.session_state.previous_plants = ["", "", "", "", ""]
    if 'ai_thresholds' not in st.session_state: st.session_state.ai_thresholds = [{"lower": 0, "upper": 0} for _ in range(5)]

    def get_plant_icon(name):
        if not name: return ""
        name = name.lower()
        if "עגבני" in name: return "🍅"
        if "מלפפון" in name: return "🥒"
        if "בצל" in name: return "🧅"
        if "גזר" in name: return "🥕"
        if "נענע" in name or "בזיליקום" in name: return "🌿"
        if "לימון" in name: return "🍊"
        if "קקטוס" in name: return "🌵"
        return "🪴"

    def fetch_ai_irrigation_data(plant_name):
        if not st.session_state.api_key: return {"lower": 35, "upper": 70}
        genai.configure(api_key=st.session_state.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Provide exact optimal soil moisture thresholds for: "{plant_name}". Return ONLY valid JSON: {{"lower": <integer 25-50>, "upper": <integer 70-90>}}"""
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            res = json.loads(raw_text[raw_text.find('{'):raw_text.rfind('}')+1])
            return {"lower": int(res["lower"]), "upper": int(res["upper"])}
        except:
            return {"lower": 40, "upper": 75}

    cols = st.columns(5)
    current_plants = []
    for i in range(5):
        with cols[i]:
            st.markdown(f"<h3 style='text-align: center;'>אדנית {i + 1}</h3>", unsafe_allow_html=True)
            plant = st.text_input("", key=f"plant_{i}", placeholder="הזן צמח")
            current_plants.append(plant)

            if plant != st.session_state.previous_plants[i] and plant != "":
                with st.spinner("מנתח..."):
                    ai_data = fetch_ai_irrigation_data(plant)
                    st.session_state.ai_thresholds[i] = ai_data
                    update_thresholds_in_firebase(i, ai_data['lower'], ai_data['upper'])
                    st.session_state.previous_plants[i] = plant

            icon = get_plant_icon(plant)
            st.markdown("<div class='planter-container'>", unsafe_allow_html=True)
            if icon: st.markdown(f"<div class='plant-wrapper'><div class='plant-emoji'>{icon}</div></div>", unsafe_allow_html=True)
            if os.path.exists("image_a1419e.jpg"): st.image("image_a1419e.jpg", use_container_width=True)
            st.markdown("</div><hr>", unsafe_allow_html=True)

            p_data = planters_data[i]
            low_th = p_data.get("lower", 0)
            up_th = p_data.get("upper", 0)
            current_moisture = p_data.get("moisture", 0)

            if plant and low_th > 0:
                st.markdown(f"<div class='ai-threshold-box'>💧 סף הפעלה: {low_th}%<br>🛑 סף עצירה: {up_th}%</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size: 0.8rem; color: #e74c3c;'>⚠️ לא הוגדר צמח / סף</div>", unsafe_allow_html=True)

            st.markdown(f"<div style='font-weight: 700; margin-top: 10px;'>לחות: {current_moisture}%</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='progress-bg'><div class='progress-fill' style='width: {current_moisture}%; background: #3498db;'></div></div>", unsafe_allow_html=True)
    st.session_state.previous_plants = current_plants