import streamlit as st
import os
import json
import google.generativeai as genai

st.set_page_config(page_title="Smart Irrigation System", page_icon="🪴", layout="wide")

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

# --- מסך פתיחה ראשוני ---
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
    # --- הדשבורד המרכזי ---
    with st.sidebar:
        st.header("הגדרות מערכת ⚙️")
        st.success(f"מחובר כפרופיל: **{st.session_state.profile_name}**")
        if st.button("התנתק / החלף פרופיל"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("---")
        st.write("מערכת ה-AI מנתחת את הצרכים הבוטניים המדויקים של כל צמח בנפרד.")

    st.markdown("<h1 class='main-title'>🌿 Smart Irrigation System</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='sub-title'>מרכז בקרה וטלמטריה חי | מנוהל על ידי {st.session_state.profile_name}</p>",
                unsafe_allow_html=True)

    # --- חיווי מפלס מים ---
    tank_level = 8  # ערך לבדיקה (מתחת ל-10 כדי שתראה את ההתראה הקופצת)

    if tank_level <= 10:
        st.error(f"🚨 אזהרה: מפלס המים במיכל נמוך מאוד ({tank_level}%)! המיכל כמעט ריק, נא למלא מים בהקדם.")
    else:
        st.info(f"💧 מפלס המים במיכל המרכזי: {tank_level}%")

    if 'previous_plants' not in st.session_state:
        st.session_state.previous_plants = ["", "", "", "", ""]
    if 'ai_thresholds' not in st.session_state:
        st.session_state.ai_thresholds = [{"lower": None, "upper": None} for _ in range(5)]


    def get_plant_icon(plant_name):
        if not plant_name: return ""
        name = plant_name.lower()

        if "בצל ירוק" in name or "עירית" in name or "כרישה" in name or "שום ירוק" in name: return "🌾"
        if "תפוח אדמה" in name or "תפוד" in name: return "🥔"
        if "תפוח ירוק" in name or "גרני סמית" in name: return "🍏"
        if "עגבניות שרי" in name or "תמר" in name and "עגבני" in name: return "🍅"
        if "עשב לימון" in name or "למונגראס" in name: return "🌾"
        if "פלפל חריף" in name or "שיפקה" in name: return "🌶️"
        if "ציפור גן עדן" in name or "שושן צחור" in name: return "🌺"
        if "יהודי נודד" in name or "בת שבע" in name: return "🌿"
        if "אמנון ותמר" in name or "כובע הנזיר" in name or "לוע הארי" in name or "כליל החורש" in name: return "🌸"
        if "זקן נחש" in name or "לריופה" in name or "כריזנטמה" in name: return "🌾"
        if "כרוב ניצנים" in name: return "🥬"

        if "בצל" in name: return "🧅"
        if "שום" in name: return "🧄"
        if "גזר" in name: return "🥕"
        if "בטטה" in name: return "🍠"
        if "עגבני" in name: return "🍅"
        if "מלפפון" in name or "קישוא" in name or "זוקיני" in name or "פקוס" in name: return "🥒"
        if "חציל" in name: return "🍆"
        if "פלפל" in name or "גמבה" in name: return "🫑"
        if "חריף" in name or "צ'ילי" in name or "חלפניו" in name or "הבנרו" in name: return "🌶️"
        if "תירס" in name: return "🌽"
        if "ברוקולי" in name or "כרובית" in name or "ארטישוק" in name: return "🥦"
        if "פטרי" in name: return "🍄"
        if "אבוקדו" in name: return "🥑"
        if "צנון" in name or "צנונית" in name or "לפת" in name or "סלק" in name: return "🫚"
        if "קולורבי" in name or "שומר" in name or "סלרי" in name or "כרפס" in name: return "🥬"
        if "אפונה" in name or "שעועית" in name or "פצפצים" in name or "פול" in name or "במיה" in name: return "🫛"
        if "דלעת" in name or "דלורית" in name: return "🎃"

        if "בזיליקום" in name or "ריחן" in name: return "🌿"
        if "נענע" in name or "מנטה" in name or "מליסה" in name: return "🍃"
        if "פטרוזיליה" in name or "כוסברה" in name or "שמיר" in name: return "☘️"
        if "רוזמרין" in name or "טימין" in name or "זעתר" in name or "מרווה" in name or "אורגנו" in name: return "🌿"
        if "חסה" in name or "כרוב" in name or "תרד" in name or "מנגולד" in name or "רוקט" in name or "קייל" in name: return "🥬"
        if "לוונדר" in name or "אזוביון" in name: return "🪻"
        if "לואיזה" in name or "טרגון" in name or "שיבה" in name: return "🌿"

        if "תות" in name: return "🍓"
        if "אוכמני" in name or "פטל" in name or "אסנה" in name or "חמוציות" in name: return "🫐"
        if "אבטיח" in name: return "🍉"
        if "מלון" in name or "פפאיה" in name: return "🍈"
        if "ענב" in name or "גפן" in name: return "🍇"
        if "תפוז" in name or "קלמנטינה" in name or "פומלה" in name or "אשכולית" in name: return "🍊"
        if "לימון" in name or "הדר" in name or "אתרוג" in name: return "🍋"
        if "תפוח" in name or "אגס" in name: return "🍎"
        if "אפרסק" in name or "משמש" in name or "שזיף" in name or "נקטרינה" in name: return "🍑"
        if "דובדבן" in name: return "🍒"
        if "אננס" in name: return "🍍"
        if "קיווי" in name: return "🥝"
        if "בננה" in name: return "🍌"
        if "מנגו" in name or "אפרסמון" in name or "פיטיה" in name or "קרמבולה" in name or "ליצ'י" in name: return "🥭"
        if "רימון" in name or "תאנה" in name or "תמר" in name: return "🍎"

        if "אגפנתוס" in name or "לובליה" in name or "אנגלוניה" in name or "עכנאי" in name or "סלביה" in name: return "🪻"
        if "קאלה" in name or "אמריליס" in name or "נורית" in name or "פרג" in name or "כלנית" in name: return "🌷"
        if "גזניה" in name or "פרזיה" in name or "אסטר" in name or "קמומיל" in name: return "🌼"
        if "בשמת" in name or "גאורה" in name or "פנטס" in name or "אליסום" in name or "ורבנה" in name: return "🌸"
        if "אלמון הודי" in name or "סטרליציה" in name or "ביגוניה" in name or "רקפת" in name: return "🌺"
        if "גרניום" in name or "פלרגוניום" in name: return "🌸"
        if "פטוניה" in name or "וינקה" in name or "פורטולקה" in name or "ציניה" in name or "קוסמוס" in name: return "🌸"
        if "בוגנוויליה" in name or "פיטנה" in name or "פלומריה" in name: return "🌸"

        if "פילודנדרון" in name or "סינגוניום" in name or "פיטוניה" in name or "אלוכסיה" in name: return "🌿"
        if "דיפנבכיה" in name or "קרוטון" in name or "קלתיאה" in name or "מרנטה" in name: return "🪴"
        if "קיסוס" in name or "יערה" in name or "פסיפלורה" in name: return "🌿"
        if "שרך" in name or "מונסטרה" in name or "פוטוס" in name: return "🍀"
        if "סנסיווריה" in name or "זמיוקולקס" in name or "קליביה" in name or "אנטוריום" in name or "ספטיפילום" in name: return "🪴"

        if "ורד" in name or "שושנ" in name or "אדמונית" in name: return "🌹"
        if "חמניה" in name or "חרצית" in name: return "🌻"
        if "צבעוני" in name or "טוליפ" in name or "נרקיס" in name or "אירוס" in name: return "🌷"
        if "סחלב" in name or "לוטוס" in name or "נימפאה" in name: return "🪷"
        if "היביסקוס" in name or "דם המכבים" in name or "דליה" in name: return "🌺"
        if "יסמין" in name or "שקד" in name or "פריחת" in name or "גרדניה" in name: return "🌸"
        if "פרח" in name or "סביון" in name or "מרגנית" in name or "תורמוס" in name: return "🌼"

        if "קקטוס" in name or "סוקולנט" in name or "צבר" in name or "אלוורה" in name or "ניצנית" in name or "חלבלוב" in name: return "🌵"

        if "זית" in name or "פיקוס" in name or "בונסאי" in name or "אלון" in name or "חרוב" in name: return "🌳"
        if "דקל" in name or "ציקס" in name or "קוקוס" in name: return "🌴"
        if "אורן" in name or "ברוש" in name or "ארז" in name: return "🌲"
        if "שיטה" in name or "צאלון" in name or "סיגלון" in name: return "🌳"
        if "עץ" in name: return "🌳"

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

        Strict rules to prevent generic outputs:
        - Cacti/Succulents: lower 10-18, upper 30-45.
        - Mediterranean herbs (Rosemary, Thyme, Sage/מרווה): lower 22-30, upper 50-60.
        - Heavy water vegetables (Cucumbers, Tomatoes, Peppers): lower 48-60, upper 80-90.
        - Leafy greens (Mint, Basil, Lettuce): lower 40-52, upper 72-82.
        - Roots (Carrots, Onions): lower 30-40, upper 65-75.
        Make sure the numbers are realistic, highly specific, and distinct for "{plant_name}".
        """
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            start_idx = raw_text.find('{')
            end_idx = raw_text.rfind('}')
            json_str = raw_text[start_idx:end_idx + 1]
            return json.loads(json_str)
        except Exception as e:
            name = plant_name.lower()
            if "קקטוס" in name or "סוקולנט" in name:
                return {"lower": 15, "upper": 38}
            elif "עגבני" in name or "מלפפון" in name or "פלפל" in name:
                return {"lower": 52, "upper": 85}
            elif "רוזמרין" in name or "טימין" in name or "מרווה" in name:
                return {"lower": 24, "upper": 58}
            elif "נענע" in name or "בזיליקום" in name:
                return {"lower": 45, "upper": 78}
            else:
                return {"lower": 35, "upper": 68}


    mock_moisture = [45, 82, 12, 67, 95]
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
                with st.spinner("מנתח ספי צימאון מדויקים..."):
                    ai_data = fetch_ai_irrigation_data(plant)
                    if ai_data:
                        st.session_state.ai_thresholds[i] = ai_data

            icon = get_plant_icon(plant)
            st.markdown("<div class='planter-container'>", unsafe_allow_html=True)

            if icon:
                st.markdown(f"<div class='plant-wrapper'><div class='plant-emoji'>{icon}</div></div>",
                            unsafe_allow_html=True)

            if os.path.exists(image_file):
                st.image(image_file, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 15px 0; border-color: #eaeaea;'>", unsafe_allow_html=True)

            thresholds = st.session_state.ai_thresholds[i]
            if thresholds['lower'] is not None and plant:
                st.markdown(f"""
                    <div class='ai-threshold-box'>
                        💧 סף הפעלה (צימאון): {thresholds['lower']}%<br>
                        🛑 סף עצירה (אידיאלי): {thresholds['upper']}%
                    </div>
                """, unsafe_allow_html=True)
            elif plant:
                st.markdown(
                    f"<div style='font-size: 0.85rem; font-weight: 800; color: #11998e; margin-bottom: 8px;'>✨ ממתין לחיבור AI...</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='height: 50px;'></div>", unsafe_allow_html=True)

            st.markdown(
                f"<div style='font-size: 1rem; font-weight: 700; color: #34495e; margin-top: 10px;'>לחות נוכחית: {mock_moisture[i]}%</div>",
                unsafe_allow_html=True)

            bar_color = "#3498db"
            if thresholds['lower']:
                if mock_moisture[i] <= thresholds['lower']:
                    bar_color = "#e74c3c"
                elif mock_moisture[i] >= thresholds['upper']:
                    bar_color = "#9b59b6"
                else:
                    bar_color = "#2ecc71"

            st.markdown(
                f"<div class='progress-bg'><div class='progress-fill' style='width: {mock_moisture[i]}%; background: {bar_color};'></div></div>",
                unsafe_allow_html=True)

    st.session_state.previous_plants = current_plants