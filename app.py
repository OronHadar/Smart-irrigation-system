import streamlit as st
import os
import json
import requests
import google.generativeai as genai

st.set_page_config(page_title="Smart Irrigation System", page_icon="🪴", layout="wide")

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
    [data-testid="column"]:hover { transform: translateY(-5px); }

    .planter-container { position: relative; margin-top: 25px; }
    .plant-wrapper { position: absolute; top: -65px; left: 0; width: 100%; display: flex; justify-content: center; z-index: 10; pointer-events: none; }

    @keyframes growUp { 0% { transform: scale(0) translateY(40px); opacity: 0; } 60% { transform: scale(1.15) translateY(-10px); opacity: 1; } 100% { transform: scale(1) translateY(0); opacity: 1; } }
    .plant-emoji { font-size: 5.5rem; animation: growUp 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; filter: drop-shadow(0px 12px 10px rgba(0,0,0,0.25)); }

    .stTextInput>div>div>input { border-radius: 10px; border: 2px solid #e0e0e0; text-align: center; font-weight: 600; margin-bottom: 5px; }
    .stTextInput>div>div>input:focus { border-color: #38ef7d; box-shadow: 0 0 5px rgba(56,239,125,0.5); }

    .main-title { text-align: center; font-size: 4rem; font-weight: 800; color: #2c3e50; padding-top: 10px; margin-bottom: 0;}
    .sub-title { text-align: center; font-size: 1.2rem; color: #34495e; margin-bottom: 40px;}

    .progress-bg { background-color: #eee; border-radius: 10px; height: 12px; width: 100%; margin: 10px 0; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 10px; transition: width 1s ease-in-out; }
    .ai-threshold-box { background: #e0f2f1; border-radius: 10px; padding: 10px; margin-top: 10px; border: 1px dashed #26a69a; color: #00695c; font-weight: 600; font-size: 0.95rem; }

    .welcome-card {
        background: white; padding: 40px; border-radius: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        max-width: 600px; margin: 80px auto; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'profile_name' not in st.session_state:
    st.session_state.profile_name = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""


def get_firebase_data():
    try:
        response = requests.get(f"{FIREBASE_URL}/planters.json")
        if response.status_code == 200:
            data = response.json()
            if data:
                return data
    except Exception as e:
        pass
    return [{"moisture": 50, "lower": 30, "upper": 70} for _ in range(5)]


def update_thresholds_in_firebase(index, lower, upper):
    try:
        requests.patch(f"{FIREBASE_URL}/planters/{index}.json", json={
            "lower": lower,
            "upper": upper
        })
    except Exception as e:
        pass


if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #2c3e50; font-weight: 900;'>🌿 Smart Irrigation System</h1>",
                unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #64748b; font-size: 1.3rem;'>מערכת חקלאות מדייקת אוטונומית מבוססת AI</p>",
        unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
        st.markdown("<h3>הגדרת פרופיל משתמש</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; font-size: 0.95rem;'>אנא הזן את פרטי ההתחברות שלך למערכת בפעם הראשונה:</p>",
                    unsafe_allow_html=True)

        input_name = st.text_input("שם פרופיל / מנהל מערכת:", placeholder="למשל: אורון")
        input_key = st.text_input("הכנס מפתח Gemini API:", type="password", placeholder="AIzaSy...")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("התחל לעבוד 🚀"):
            if input_name and input_key:
                st.session_state.logged_in = True
                st.session_state.profile_name = input_name
                st.session_state.api_key = input_key
                st.rerun()
            else:
                st.error("חובה למלא את שתי התיבות כדי להמשיך.")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    with st.sidebar:
        st.header("הגדרות מערכת ⚙️")
        st.success(f"מחובר כפרופיל: **{st.session_state.profile_name}**")
        if st.button("התנתק / החלף פרופיל"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("---")
        st.write("סנכרון מלא מול בקר ה-ESP32 דרך ענן Firebase בזמן אמת.")

    st.markdown("<h1 class='main-title'>🌿 Smart Irrigation System</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='sub-title'>מרכז בקרה וטלמטריה חי | מנוהל על ידי {st.session_state.profile_name}</p>",
                unsafe_allow_html=True)

    if 'previous_plants' not in st.session_state:
        st.session_state.previous_plants = ["", "", "", "", ""]
    if 'ai_thresholds' not in st.session_state:
        st.session_state.ai_thresholds = [{"lower": None, "upper": None} for _ in range(5)]


    def get_plant_icon(plant_name):
        if not plant_name: return ""
        name = plant_name.lower()
        if "בצל ירוק" in name or "עירית" in name: return "🌾"
        if "תפוח אדמה" in name: return "🥔"
        if "עגבני" in name: return "🍅"
        if "מלפפון" in name: return "🥒"
        if "חציל" in name: return "🍆"
        if "פלפל" in name: return "🫑"
        if "גזר" in name: return "🥕"
        if "בזיליקום" in name or "ריחן" in name: return "🌿"
        if "נענע" in name: return "🍃"
        if "רוזמרין" in name or "מרווה" in name: return "🌿"
        if "תות" in name: return "🍓"
        if "קקטוס" in name or "סוקולנט" in name: return "🌵"
        if "ורד" in name: return "🌹"
        return "🪴"


    def fetch_ai_irrigation_data(plant_name):
        if not st.session_state.api_key: return None
        genai.configure(api_key=st.session_state.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are a strict and highly precise agricultural expert for precision IoT irrigation systems.
        The user planted: "{plant_name}".
        Provide exact, unique, non-generic moisture thresholds for this specific plant. 
        Return ONLY valid JSON with two integer percentages (0 to 100):
        {{"lower": <min_moisture_percentage>, "upper": <max_moisture_percentage>}}
        """
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            start_idx = raw_text.find('{')
            end_idx = raw_text.rfind('}')
            json_str = raw_text[start_idx:end_idx + 1]
            return json.loads(json_str)
        except Exception as e:
            return {"lower": 35, "upper": 68}


    firebase_data = get_firebase_data()
    cols = st.columns(5)
    image_file = "image_a1419e.jpg"
    current_plants = []

    for i in range(5):
        with cols[i]:
            st.markdown(
                f"<h3 style='color: #2c3e50; font-weight: 800; margin-bottom: 5px; text-align: center;'>אדנית {i + 1}</h3>",
                unsafe_allow_html=True)

            plant = st.text_input("", key=f"plant_{i}", placeholder="הזן צמח ולחץ Enter")
            current_plants.append(plant)

            if plant != st.session_state.previous_plants[i] and plant != "":
                with st.spinner("מנתח ספי צימאון ומעדכן ענן..."):
                    ai_data = fetch_ai_irrigation_data(plant)
                    if ai_data:
                        st.session_state.ai_thresholds[i] = ai_data
                        update_thresholds_in_firebase(i, ai_data['lower'], ai_data['upper'])

            icon = get_plant_icon(plant)
            st.markdown("<div class='planter-container'>", unsafe_allow_html=True)
            if icon:
                st.markdown(f"<div class='plant-wrapper'><div class='plant-emoji'>{icon}</div></div>",
                            unsafe_allow_html=True)
            if os.path.exists(image_file):
                st.image(image_file, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 15px 0; border-color: #eaeaea;'>", unsafe_allow_html=True)

            try:
                current_moisture = firebase_data[i].get("moisture", 50)
                stored_lower = firebase_data[i].get("lower", 35)
                stored_upper = firebase_data[i].get("upper", 70)
            except:
                current_moisture = 50
                stored_lower = 35
                stored_upper = 70

            thresholds = st.session_state.ai_thresholds[i]
            display_lower = thresholds['lower'] if thresholds['lower'] is not None else stored_lower
            display_upper = thresholds['upper'] if thresholds['upper'] is not None else stored_upper

            if plant:
                st.markdown(f"""
                    <div class='ai-threshold-box'>
                        💧 סף הפעלה (צימאון): {display_lower}%<br>
                        🛑 סף עצירה (אידיאלי): {display_upper}%
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='height: 50px;'></div>", unsafe_allow_html=True)

            st.markdown(
                f"<div style='font-size: 1rem; font-weight: 700; color: #34495e; margin-top: 10px;'>לחות נוכחית: {current_moisture}%</div>",
                unsafe_allow_html=True)

            bar_color = "#3498db"
            if current_moisture <= display_lower:
                bar_color = "#e74c3c"
            elif current_moisture >= display_upper:
                bar_color = "#9b59b6"
            else:
                bar_color = "#2ecc71"

            st.markdown(
                f"<div class='progress-bg'><div class='progress-fill' style='width: {current_moisture}%; background: {bar_color};'></div></div>",
                unsafe_allow_html=True)

    st.session_state.previous_plants = current_plants