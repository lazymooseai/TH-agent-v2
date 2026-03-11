import streamlit as st
import datetime

# --- ASETUKSET JA SIVUN MÄÄRITYS ---
st.set_page_config(page_title="TH Taktinen Tutka", page_icon="🚕", layout="centered")

# --- KÄYTTÖLIITTYMÄN TYYLITTELY (CSS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .main { background-color: #121212; }
    
    .header-container { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px; }
    .app-title { font-size: 26px; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
    .time-display { font-size: 36px; font-weight: bold; color: #e0e0e0; line-height: 1; }
    .weather-widget { text-align: right; }
    .weather-temp { font-size: 32px; font-weight: bold; color: #a3c2a3; line-height: 1; margin-bottom: 5px; display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
    .weather-status { font-size: 18px; color: #cccccc; margin-bottom: 5px; }
    .weather-link { color: #5bc0de; text-decoration: none; font-size: 14px; }

    @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-3px); } 100% { transform: translateY(0px); } }
    .animated-icon { display: inline-block; animation: float 3s ease-in-out infinite; }

    .taksi-card { background-color: #2b2b36; color: #e0e0e0; padding: 18px; border-radius: 10px; margin-bottom: 15px; font-size: 18px; border: 1px solid #3f3f4e; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .card-title { font-size: 24px; font-weight: 600; margin-bottom: 10px; color: #ffffff; }
    .taksi-link { color: #5bc0de; text-decoration: none; font-size: 16px; display: inline-block; margin-top: 10px; font-weight: 500;}
    
    /* Pienempi marginaali expanderille (palautelaatikko) */
    .streamlit-expanderHeader { font-size: 16px; color: #a3c2a3; }
    </style>
""", unsafe_allow_html=True)

# --- APUFUNKTIO: PALAUTELAATIKKO JOKAISEEN KORTTIIN ---
# Tämä luo yhdenmukaisen palautelaatikon jokaisen tapahtuman sisälle.
def render_feedback_ui(event_id):
    with st.expander("📡 Raportoi tilanne kentältä"):
        # Pikanäppäimet
        col1, col2, col3 = st.columns(3)
        if col1.button("🟢 Purku alkoi", key=f"btn_purku_{event_id}", use_container_width=True):
            st.success("Lähetetty ydinryhmälle!")
        if col2.button("🔴 Hiljaista", key=f"btn_hiljaista_{event_id}", use_container_width=True):
            st.warning("Lähetetty ydinryhmälle!")
        if col3.button("🔥 Paljon asiakk.", key=f"btn_paljon_{event_id}", use_container_width=True):
            st.error("Lähetetty ydinryhmälle!")
        
        # Tekstipalaute
        palaute = st.text_input("Tarkentava huomio (esim. automäärä):", key=f"txt_{event_id}")
        if st.button("Lähetä huomio", key=f"btn_send_{event_id}", use_container_width=True):
            if palaute:
                st.success("Huomio tallennettu lokiin.")

# --- DATAN HAKU (Simuloitu) ---
@st.cache_data(ttl=300)
def get_weather():
    return {"temp": "+12°C", "status": "Puolipilvistä", "icon": "⛅", "link": "https://www.ilmatieteenlaitos.fi/paikallissaa/helsinki"}

# --- KÄYTTÖLIITTYMÄ ---

current_time = datetime.datetime.now().strftime("%H:%M")
weather = get_weather()

st.markdown(f"""
<div class='header-container'>
    <div>
        <div class='app-title'>TH Taktinen Tutka 🚕</div>
        <div class='time-display'>{current_time}</div>
    </div>
    <div class='weather-widget'>
        <div class='weather-temp'>
            <span class='animated-icon'>{weather['icon']}</span> {weather['temp']}
        </div>
        <div class='weather-status'>{weather['status']}</div>
        <a href='{weather['link']}' class='weather-link' target='_blank'>Avaa sadetutka ➔</a>
    </div>
</div>
""", unsafe_allow_html=True)

# KAUKOJUNAT
st.markdown("<h3 style='color:#e0e0e0; margin-top:20px;'>🚆 KAUKOJUNAT</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1: st.button("Helsinki", use_container_width=True)
with col2: st.button("Pasila", use_container_width=True)
with col3: st.button("Tikkurila", use_container_width=True)

# Juna 1
st.markdown("""<div class='taksi-card'><b>IC 28 (Rovaniemi)</b> -> Saapuu: <b>19:12</b><br><span style='color:#ff9999;'><b>Myöhässä: 1h 15min</b></span> | <a href='https://www.vr.fi/junaliikenne-nyt' class='taksi-link' target='_blank'>VR Seuranta ➔</a></div>""", unsafe_allow_html=True)
render_feedback_ui("juna_ic28")

# Juna 2
st.markdown("""<div class='taksi-card'><b>S 144 (Joensuu)</b> -> Saapuu: <b>19:40</b><br><span style='color:#a3c2a3;'>Aikataulussa</span> | <a href='https://www.vr.fi/junaliikenne-nyt' class='taksi-link' target='_blank'>VR Seuranta ➔</a></div>""", unsafe_allow_html=True)
render_feedback_ui("juna_s144")


# TAPAHTUMAT RYHMITTÄIN
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px;'>📅 TAPAHTUMAT</h3>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🎭 Kulttuuri", "🏒 Urheilu", "🚢 Satamat"])

with tab1:
    st.markdown("""<div class='taksi-card'><div class='card-title'>Helsingin Kaupunginteatteri</div>Tapahtuma: <b>Pieni merenneito</b><br>Purku n. <b>klo 21:15</b><br><i>Arvio: ~20 autoa.</i><br><a href='https://hkt.fi' class='taksi-link' target='_blank'>HKT sivut ➔</a></div>""", unsafe_allow_html=True)
    render_feedback_ui("tapahtuma_hkt")
    
    st.markdown("""<div class='taksi-card'><div class='card-title'>Musiikkitalo</div>Tapahtuma: <b>RSO:n konsertti</b><br>Purku n. <b>klo 21:30</b><br><i>Huomio: Aseman vieressä, paljon kävelijöitä.</i><br><a href='https://www.musiikkitalo.fi' class='taksi-link' target='_blank'>Musiikkitalo ➔</a></div>""", unsafe_allow_html=True)
    render_feedback_ui("tapahtuma_musiikkitalo")

with tab2:
    st.markdown("""<div class='taksi-card'><div class='card-title'>HIFK - Kärpät (Nordis)</div>Arvioitu purku <b>klo 21:00</b> <i>(2,5h aloituksesta)</i><br><a href='https://liiga.fi' class='taksi-link' target='_blank'>Liigan sivut ➔</a></div>""", unsafe_allow_html=True)
    render_feedback_ui("tapahtuma_hifk")

with tab3:
    st.markdown("""<div class='taksi-card'><div class='card-title'>Länsisatama T2</div>MS Finlandia saapuu <b>klo 00:30</b><br><i>Su/Ma yönä matkustajia maltillisesti.</i><br><a href='https://portofhelsinki.fi' class='taksi-link' target='_blank'>Sataman aikataulut ➔</a></div>""", unsafe_allow_html=True)
    render_feedback_ui("tapahtuma_finlandia")

