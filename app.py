import streamlit as st
import datetime

# --- ASETUKSET JA SIVUN MÄÄRITYS ---
st.set_page_config(page_title="TH Taktinen Tutka", page_icon="🚕", layout="wide")

# --- TILAN HALLINTA (SESSION STATE) JUNILLE ---
# Tämä pitää huolen siitä, että valittu asema pysyy muistissa ja vaihtuu painikkeista.
if 'valittu_asema' not in st.session_state:
    st.session_state.valittu_asema = 'Helsinki'

# --- KÄYTTÖLIITTYMÄN TYYLITTELY (CSS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .main { background-color: #121212; }
    
    .header-container { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px; }
    .app-title { font-size: 26px; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
    .time-display { font-size: 36px; font-weight: bold; color: #e0e0e0; line-height: 1; }
    
    .taksi-card { background-color: #2b2b36; color: #e0e0e0; padding: 18px; border-radius: 10px; margin-bottom: 15px; font-size: 18px; border: 1px solid #3f3f4e; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .card-title { font-size: 22px; font-weight: 600; margin-bottom: 8px; color: #ffffff; border-bottom: 1px solid #444; padding-bottom: 5px;}
    .taksi-link { color: #5bc0de; text-decoration: none; font-size: 16px; display: inline-block; margin-top: 10px; font-weight: 500;}
    
    .sold-out { color: #ff4b4b; font-weight: bold; font-size: 18px; }
    .pax-count { color: #a3c2a3; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- DATAN HAKU ---
# HUOM: Täsmälliset, suodatetut linkit käytössä.

def get_trains(asema):
    # Palautetaan dataa riippuen siitä, mitä painiketta kuljettaja on painanut
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
        {"ship": "Megastar", "port": "Länsisatama T2", "time": "13:30", "pax": 2100, "link": "https://averio.fi/laivat"},
        {"ship": "MS Finlandia", "port": "Länsisatama T2", "time": "00:30", "pax": "Maltillinen", "link": "https://averio.fi/laivat"}
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
        <div style='font-size: 24px; color: #a3c2a3; font-weight: bold;'>⛅ +12°C</div>
        <a href='{weather_link}' class='taksi-link' target='_blank'>Avaa sadetutka (Sadealueet) ➔</a>
    </div>
</div>
""", unsafe_allow_html=True)


# LOHKO 1: JUNALIIKENNE (Reaaliaikaiset painikkeet)
st.markdown("<h3 style='color:#e0e0e0;'>🚆 KAUKOJUNAT (Häiriöt & Saapumiset)</h3>", unsafe_allow_html=True)

# Asemapainikkeet muuttavat session_statea
col1, col2, col3 = st.columns(3)
if col1.button("Helsinki", use_container_width=True):
    st.session_state.valittu_asema = 'Helsinki'
if col2.button("Pasila", use_container_width=True):
    st.session_state.valittu_asema = 'Pasila'
if col3.button("Tikkurila", use_container_width=True):
    st.session_state.valittu_asema = 'Tikkurila'

# Haetaan data valitun aseman mukaan
valittu = st.session_state.valittu_asema
trains = get_trains(valittu)

train_html = f"<div style='margin-bottom: 10px; color: #a3c2a3;'>Näkymä: <b>{valittu}</b></div>"
for t in trains:
    delay_style = "color:#ff9999; font-weight:bold;" if t['delay'] != "Ei" else "color:#a3c2a3;"
    delay_text = f"Myöhässä: {t['delay']}" if t['delay'] != "Ei" else "Aikataulussa"
    train_html += f"<b>{t['time']}</b> - {t['train']} ({t['origin']}) | <span style='{delay_style}'>{delay_text}</span><br>"

# Näytetään laatikko ja oikea suora linkki valitulle asemalle
st.markdown(f"<div class='taksi-card'>{train_html}<a href='{trains[0]['link']}' class='taksi-link' target='_blank'>Avaa VR Radalla ({valittu} saapuvat kaukoliikenne) ➔</a></div>", unsafe_allow_html=True)


# LOHKO 2: LAIVAT JA LENNOT
st.markdown("<h3 style='color:#e0e0e0; margin-top:20px;'>🚢 LAIVAT & ✈️ LENTOKENTTÄ</h3>", unsafe_allow_html=True)
ships = get_ships()
ship_html = ""
for s in ships:
    ship_html += f"<b>{s['time']}</b> - {s['ship']} ({s['port']}) | Matkustajia: <span class='pax-count'>{s['pax']}</span> <br>"
st.markdown(f"<div class='taksi-card'><div class='card-title'>Seuraavat saapuvat alukset</div>{ship_html}<a href='https://averio.fi/laivat' class='taksi-link' target='_blank'>Avaa Averio ➔</a></div>", unsafe_allow_html=True)


# LOHKO 3: TAPAHTUMAT & KAPASITEETIT
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px;'>📅 TAPAHTUMAT & KAPASITEETTI</h3>", unsafe_allow_html=True)

# HKT
st.markdown("""
<div class='taksi-card'>
    <div class='card-title'>Helsingin Kaupunginteatteri (HKT)</div>
    Tapahtuma: <b>Pieni merenneito</b><br>
    Purku n. <b>klo 21:15</b><br>
    Kapasiteetti: <b>947 henkilöä</b> | <span class='sold-out'>🔥 LOPPUUNMYYTY</span><br>
    <i>Tekoälyn laskema taksiarvio (1.5% sääntö): ~14-20 autoa.</i><br>
    <a href='https://hkt.fi/kalenteri/' class='taksi-link' target='_blank'>Avaa HKT Kalenteri ➔</a>
</div>
""", unsafe_allow_html=True)

# MUSIIKKITALO
st.markdown("""
<div class='taksi-card'>
    <div class='card-title'>Musiikkitalo</div>
    Tapahtuma: <b>RSO:n konsertti</b><br>
    Purku n. <b>klo 21:30</b><br>
    Kapasiteetti: <b>1 704 henkilöä</b><br>
    <i>Huomio: Aseman vieressä, paljon kävelijöitä.</i><br>
    <a href='https://musiikkitalo.fi/konsertit-ja-tapahtumat/' class='taksi-link' target='_blank'>Avaa Musiikkitalon tapahtumat ➔</a>
</div>
""", unsafe_allow_html=True)
