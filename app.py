import streamlit as st
import datetime

# --- ASETUKSET JA SIVUN MÄÄRITYS ---
st.set_page_config(page_title="TH Taktinen Tutka", page_icon="🚕", layout="wide")

# --- TILAN HALLINTA (SESSION STATE) JUNILLE ---
if 'valittu_asema' not in st.session_state:
    st.session_state.valittu_asema = 'Helsinki'

# --- KÄYTTÖLIITTYMÄN TYYLITTELY (CSS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .main { background-color: #121212; }
    
    .header-container { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px; }
    .app-title { font-size: 32px; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
    .time-display { font-size: 42px; font-weight: bold; color: #e0e0e0; line-height: 1; }
    
    .taksi-card { background-color: #2b2b36; color: #e0e0e0; padding: 22px; border-radius: 12px; margin-bottom: 20px; font-size: 22px; border: 1px solid #3f3f4e; box-shadow: 0 4px 6px rgba(0,0,0,0.1); line-height: 1.5; }
    .card-title { font-size: 28px; font-weight: bold; margin-bottom: 12px; color: #ffffff; border-bottom: 2px solid #444; padding-bottom: 8px;}
    .taksi-link { color: #5bc0de; text-decoration: none; font-size: 20px; display: inline-block; margin-top: 15px; font-weight: bold;}
    
    .sold-out { color: #ff4b4b; font-weight: bold; font-size: 24px; }
    .pax-count { color: #ffeb3b; font-weight: bold; font-size: 26px; }
    .delay-text { color: #ff9999; font-weight: bold; font-size: 22px; }
    .ok-text { color: #a3c2a3; font-size: 22px; }
    
    .stTabs [data-baseweb="tab"] { font-size: 22px; padding: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- DATAN HAKU (Simuloitu) ---

def get_trains(asema):
    if asema == 'Helsinki':
        linkki = "https://www.vr.fi/radalla?station=HKI&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D"
        return [
            {"train": "IC 28", "origin": "Rovaniemi -> Helsinki", "time": "19:12", "delay": "1h 15min", "link": linkki},
            {"train": "S 144", "origin": "Joensuu -> Helsinki", "time": "19:40", "delay": "Ei", "link": linkki}
        ]
    elif asema == 'Pasila':
        linkki = "https://www.vr.fi/radalla?station=PSL&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D"
        return [
            {"train": "IC 28", "origin": "Rovaniemi -> Pasila", "time": "19:07", "delay": "1h 15min", "link": linkki},
            {"train": "S 144", "origin": "Joensuu -> Pasila", "time": "19:35", "delay": "Ei", "link": linkki}
        ]
    elif asema == 'Tikkurila':
        linkki = "https://www.vr.fi/radalla?station=TKL&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D"
        return [
            {"train": "IC 28", "origin": "Rovaniemi -> Tikkurila", "time": "18:55", "delay": "1h 15min", "link": linkki},
            {"train": "S 144", "origin": "Joensuu -> Tikkurila", "time": "19:20", "delay": "Ei", "link": linkki}
        ]

def get_ships():
    return [
        {"ship": "MS Finlandia", "port": "Länsisatama T2", "time": "Tänään 23:15", "pax": "980"},
        {"ship": "MyStar", "port": "Länsisatama T2", "time": "Huomenna 07:30", "pax": "1 450"},
        {"ship": "Megastar", "port": "Länsisatama T2", "time": "Huomenna 09:00", "pax": "2 120"}
    ]

def get_flights():
    # Tässä simuloitu 1-7 lennon taktinen suodatus. 
    # Tulevaisuudessa koodi poimii Finavian rajapinnasta max 7 tärkeintä.
    return [
        {"flight": "AY1338", "origin": "Lontoo", "time": "23:15", "type": "Laajarunko", "status": "🔥 Massapurku"},
        {"flight": "AY074", "origin": "Tokio", "time": "23:40", "type": "Laajarunko", "status": "🔥 Massapurku"},
        {"flight": "D8 3213", "origin": "Tukholma", "time": "00:10", "type": "Kapearunko", "status": "Myöhässä 40min"},
        {"flight": "AY432", "origin": "Oulu", "time": "00:25", "type": "Kapearunko", "status": "Ajallaan"}
    ]

# --- KÄYTTÖLIITTYMÄ ---

current_time = datetime.datetime.now().strftime("%H:%M")
weather_link = "https://www.ilmatieteenlaitos.fi/sadealueet-suomessa"

st.markdown(f"""
<div class='header-container'>
    <div>
        <div class='app-title'>TH Taktinen Tutka 🚕</div>
        <div class='time-display'>{current_time}</div>
    </div>
    <div style='text-align: right;'>
        <div style='font-size: 32px; color: #a3c2a3; font-weight: bold;'>⛅ +12°C</div>
        <a href='{weather_link}' class='taksi-link' target='_blank'>Avaa sadetutka ➔</a>
    </div>
</div>
""", unsafe_allow_html=True)


# LOHKO 1: JUNALIIKENNE
st.markdown("<h3 style='color:#e0e0e0; font-size: 26px;'>🚆 KAUKOJUNAT</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
if col1.button("Helsinki", use_container_width=True):
    st.session_state.valittu_asema = 'Helsinki'
if col2.button("Pasila", use_container_width=True):
    st.session_state.valittu_asema = 'Pasila'
if col3.button("Tikkurila", use_container_width=True):
    st.session_state.valittu_asema = 'Tikkurila'

valittu = st.session_state.valittu_asema
trains = get_trains(valittu)

train_html = f"<div style='margin-bottom: 15px; color: #a3c2a3;'>Näkymä: <b>{valittu}</b></div>"
for t in trains:
    delay_class = "delay-text" if t['delay'] != "Ei" else "ok-text"
    delay_text = f"Myöhässä: {t['delay']}" if t['delay'] != "Ei" else "Aikataulussa"
    train_html += f"<b>{t['time']}</b> - {t['train']} ({t['origin']}) <br>└ Tila: <span class='{delay_class}'>{delay_text}</span><br><br>"

st.markdown(f"<div class='taksi-card'>{train_html}<a href='{trains[0]['link']}' class='taksi-link' target='_blank'>Avaa VR Radalla ({valittu}) ➔</a></div>", unsafe_allow_html=True)


# LOHKO 2: LAIVAT
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px; font-size: 26px;'>🚢 MATKUSTAJALAIVAT</h3>", unsafe_allow_html=True)
ships = get_ships()
ship_html = ""
for s in ships:
    ship_html += f"<b>{s['time']}</b> - {s['ship']} ({s['port']}) <br>└ Matkustajia: <span class='pax-count'>{s['pax']}</span> <br><br>"

st.markdown(f"""
<div class='taksi-card'>
    <div class='card-title'>3 Seuraavaa saapuvaa alusta</div>
    {ship_html}
    <a href='https://averio.fi/laivat' class='taksi-link' target='_blank'>Avaa Averio.fi ➔</a>
</div>
""", unsafe_allow_html=True)


# LOHKO 3: LENTOKENTTÄ (Dynaaminen 1-7 poimintaa)
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px; font-size: 26px;'>✈️ LENTOKENTTÄ (HELSINKI-VANTAA)</h3>", unsafe_allow_html=True)
flights = get_flights()

# Näytetään visuaalisesti poimintojen määrä
flight_html = f"<div style='margin-bottom: 15px; color: #a3c2a3;'>Näkymä: <b>Taktiset poiminnat ({len(flights)} kpl)</b></div>"

for f in flights:
    # Korostetaan punaisella jos kyseessä on massapurku tai myöhästyminen
    status_color = "#ff4b4b" if "🔥" in f['status'] or "Myöhässä" in f['status'] else "#a3c2a3"
    flight_html += f"<b>{f['time']}</b> - {f['origin']} ({f['flight']}) <br>└ Tyyppi: {f['type']} | Tila: <span style='color:{status_color}; font-weight:bold;'>{f['status']}</span><br><br>"

st.markdown(f"""
<div class='taksi-card'>
    {flight_html}
    <a href='https://www.finavia.fi/fi/lennot' class='taksi-link' target='_blank'>Avaa Finavia Saapuvat ➔</a>
</div>
""", unsafe_allow_html=True)


# LOHKO 4: TAPAHTUMAT & KAPASITEETIT
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px; font-size: 26px;'>📅 TAPAHTUMAT & KAPASITEETTI</h3>", unsafe_allow_html=True)

st.markdown("""
<div class='taksi-card'>
    <div class='card-title'>Helsingin Kaupunginteatteri (HKT)</div>
    Tapahtuma: <b>Pieni merenneito</b><br>
    Purku n. <b>klo 21:15</b><br>
    Kapasiteetti: <b>947 henkilöä</b> | <span class='sold-out'>🔥 LOPPUUNMYYTY</span><br>
    <i>Arvio: ~14-20 autoa.</i><br>
    <a href='https://hkt.fi/kalenteri/' class='taksi-link' target='_blank'>Avaa HKT Kalenteri ➔</a>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='taksi-card'>
    <div class='card-title'>Musiikkitalo</div>
    Tapahtuma: <b>RSO:n konsertti</b><br>
    Purku n. <b>klo 21:30</b><br>
    Kapasiteetti: <b>1 704 henkilöä</b><br>
    <i>Huomio: Aseman vieressä, paljon kävelijöitä junaan.</i><br>
    <a href='https://musiikkitalo.fi/konsertit-ja-tapahtumat' class='taksi-link' target='_blank'>Avaa Musiikkitalon tapahtumat ➔</a>
</div>
""", unsafe_allow_html=True)
