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
    
    /* Yläpalkki: Kello ja Sää samalla rivillä */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #333;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
    
    .app-title { font-size: 24px; font-weight: bold; color: #ffffff; }
    
    .weather-widget { 
        font-size: 16px; 
        color: #a3c2a3; 
        text-align: right; 
    }
    .weather-link { color: #5bc0de; text-decoration: none; font-size: 14px; }

    .taksi-card { 
        background-color: #2b2b36; color: #e0e0e0; padding: 18px; 
        border-radius: 10px; margin-bottom: 15px; font-size: 18px;
        border: 1px solid #3f3f4e; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .taksi-alert { 
        background-color: #3b2a2a; color: #f2caca; padding: 18px; 
        border-radius: 10px; border-left: 6px solid #d9534f; margin-bottom: 15px; 
        font-size: 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .card-title { font-size: 22px; font-weight: 600; margin-bottom: 10px; color: #ffffff; }
    .alert-title { font-size: 22px; font-weight: 600; margin-bottom: 10px; color: #ff9999; }
    .taksi-link { color: #5bc0de; text-decoration: none; font-size: 16px; display: inline-block; margin-top: 10px; font-weight: 500;}
    
    </style>
""", unsafe_allow_html=True)

# --- DATAN HAKU (Simuloitu) ---
@st.cache_data(ttl=300)
def get_disruptions():
    return [{"type": "Metro", "info": "Liikenne poikki välillä Sörnäinen-Itäkeskus.", "link": "https://www.hsl.fi"}]

@st.cache_data(ttl=300)
def get_trains():
    return [
        {"train": "IC 28", "origin": "Rovaniemi", "time": "19:12", "delay": "1h 15min", "link": "https://www.vr.fi/junaliikenne-nyt"},
        {"train": "S 144", "origin": "Joensuu", "time": "19:40", "delay": "Ei", "link": "https://www.vr.fi/junaliikenne-nyt"}
    ]

@st.cache_data(ttl=300)
def get_weather():
    return {"temp": "+12°C", "status": "Puolipilvistä", "link": "https://www.ilmatieteenlaitos.fi/paikallissaa/helsinki"}


# --- KÄYTTÖLIITTYMÄ ---

# 1. YLÄPALKKI (Otsikko, Kello ja Sää)
current_time = datetime.datetime.now().strftime("%H:%M")
weather = get_weather()

st.markdown(f"""
<div class='header-container'>
    <div class='app-title'>TH Taktinen Tutka 🚕</div>
    <div class='weather-widget'>
        <b>{current_time}</b><br>
        {weather['temp']} | {weather['status']}<br>
        <a href='{weather['link']}' class='weather-link' target='_blank'>Avaa sadetutka ➔</a>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. HÄIRIÖTILANTEET
disruptions = get_disruptions()
if disruptions:
    for d in disruptions:
        st.markdown(f"""
        <div class='taksi-alert'>
            <div class='alert-title'>🚨 HÄIRIÖ: {d['type']}</div>
            {d['info']}<br>
            <a href='{d['link']}' class='taksi-link' target='_blank'>Avaa HSL tiedote ➔</a>
        </div>
        """, unsafe_allow_html=True)

# 3. KAUKOJUNAT (Painikkeilla)
st.markdown("<h3 style='color:#e0e0e0; margin-top:20px;'>🚆 KAUKOJUNAT</h3>", unsafe_allow_html=True)

# Asemapainikkeet
col1, col2, col3 = st.columns(3)
with col1:
    st.button("Helsinki", use_container_width=True)
with col2:
    st.button("Pasila", use_container_width=True)
with col3:
    st.button("Tikkurila", use_container_width=True)

# Junalistaus
trains = get_trains()
for t in trains:
    delay_text = f"<span style='color:#ff9999;'><b>Myöhässä: {t['delay']}</b></span>" if t['delay'] != "Ei" else "<span style='color:#a3c2a3;'>Aikataulussa</span>"
    st.markdown(f"""
    <div class='taksi-card' style='margin-top: 10px;'>
        <b>{t['train']} ({t['origin']})</b> -> Saapuu: <b>{t['time']}</b><br>
        {delay_text} | <a href='{t['link']}' class='taksi-link' target='_blank'>VR Seuranta ➔</a>
    </div>
    """, unsafe_allow_html=True)

# 4. TAPAHTUMAT RYHMITTÄIN
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px;'>📅 TAPAHTUMAT</h3>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🎭 Kulttuuri", "🏒 Urheilu", "🚢 Satamat"])

with tab1:
    st.markdown("""
    <div class='taksi-card'>
        <div class='card-title'>Helsingin Kaupunginteatteri</div>
        Purku n. <b>klo 21:15</b><br>
        <i>Arvio: ~20 autoa.</i><br>
        <a href='https://hkt.fi' class='taksi-link' target='_blank'>HKT sivut ➔</a>
    </div>
    
    <div class='taksi-card'>
        <div class='card-title'>Musiikkitalo</div>
        Purku n. <b>klo 21:30</b><br>
        <i>Huomio: Aseman vieressä, paljon kävelijöitä.</i><br>
        <a href='https://www.musiikkitalo.fi' class='taksi-link' target='_blank'>Musiikkitalo ➔</a>
    </div>

    <div class='taksi-card'>
        <div class='card-title'>Kansallisteatteri</div>
        Purku n. <b>klo 21:40</b><br>
        <i>Huomio: Aseman vieressä, maltillinen kysyntä.</i><br>
        <a href='https://www.kansallisteatteri.fi' class='taksi-link' target='_blank'>Kansallisteatteri ➔</a>
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("""
    <div class='taksi-card'>
        <div class='card-title'>HIFK - Kärpät (Nordis)</div>
        Arvioitu purku <b>klo 21:00</b> <i>(2,5h aloituksesta)</i><br>
        <a href='https://liiga.fi' class='taksi-link' target='_blank'>Liigan sivut ➔</a>
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown("""
    <div class='taksi-card'>
        <div class='card-title'>Länsisatama T2</div>
        MS Finlandia saapuu <b>klo 00:30</b><br>
        <i>Su/Ma yönä matkustajia maltillisesti.</i><br>
        <a href='https://portofhelsinki.fi' class='taksi-link' target='_blank'>Sataman aikataulut ➔</a>
    </div>
    """, unsafe_allow_html=True)

# 5. BONUS-KYYDIT
with st.expander("🩸 Näyte- ja verikuljetukset (SPR)"):
    st.markdown("<div style='font-size: 18px; color:#cccccc;'>Verikuljetukset ja laboratorionäytteet ovat hyvä bonus, jos satut olemaan lähistöllä (esim. Vantaan härkälenkki) eikä tolpalla ole tunkua.</div>", unsafe_allow_html=True)

# 6. KULJETTAJAN TILANNEPÄIVITYS & PALAUTE
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px;'>📡 KENTÄN TILANNE</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
if col1.button("🟢 PURKU ALKOI", use_container_width=True):
    st.success("Tieto jaettu ydinryhmälle.")
if col2.button("🔴 HILJAISTA", use_container_width=True):
    st.warning("Tieto jaettu ydinryhmälle.")
if col3.button("🔥 PALJON ASIAKKAITA", use_container_width=True):
    st.error("Tieto jaettu ydinryhmälle.")

st.markdown("<br>", unsafe_allow_html=True)
kuljettajan_palaute = st.text_input("Lyhyt huomio kentältä (esim. toteutuneet autot):")
if st.button("LÄHETÄ TIETO", use_container_width=True):
    if kuljettajan_palaute:
        st.success("Huomio tallennettu lokiin.")

