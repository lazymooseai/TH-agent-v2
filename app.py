import streamlit as st
import datetime
import time

# --- ASETUKSET JA SIVUN MÄÄRITYS ---
st.set_page_config(page_title="TH Taktinen Tutka", page_icon="🚕", layout="centered")

# CSS-tyylittely mobiilinäkymää varten (esim. häiriölaatikon punainen väri)
st.markdown("""
    <style>
    .critical-alert { background-color: #ffcccc; padding: 10px; border-radius: 5px; border-left: 5px solid red; margin-bottom: 10px;}
    .event-card { background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .small-clock { font-size: 14px; color: gray; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# --- DATAN HAKU (Simuloitu, 5 min välimuisti) ---
# ttl=300 tarkoittaa, että data haetaan uudelleen vain 5 minuutin (300 sekunnin) välein.
@st.cache_data(ttl=300)
def get_disruptions():
    # Tähän rakennetaan myöhemmin rajapintakutsu (Fintraffic/HSL)
    return [
        {"type": "Metro", "info": "Liikenne poikki välillä Sörnäinen-Itäkeskus.", "link": "https://www.hsl.fi"}
    ]

@st.cache_data(ttl=300)
def get_trains():
    # Painopiste: Helsinki, Pasila, Tikkurila
    return [
        {"train": "IC 28", "origin": "Rovaniemi", "time": "19:12", "delay": "1h 15min", "link": "https://www.vr.fi/junaliikenne-nyt"},
        {"train": "S 144", "origin": "Joensuu", "time": "19:40", "delay": "Ei", "link": "https://www.vr.fi/junaliikenne-nyt"}
    ]

@st.cache_data(ttl=300)
def get_weather():
    return {"status": "Puolipilvistä, ei sateita lähitunteina.", "link": "https://www.ilmatieteenlaitos.fi/paikallissaa/helsinki"}

# --- KÄYTTÖLIITTYMÄ ---

# 1. Yläpalkki ja kello
current_time = datetime.datetime.now().strftime("%H:%M")
st.markdown(f"<div class='small-clock'>Kello: {current_time} (Päivittyy 5 min välein)</div>", unsafe_allow_html=True)
st.title("TH Taktinen Tutka 🚕")

# 2. HÄIRIÖTILANTEET (Korkein prioriteetti)
disruptions = get_disruptions()
if disruptions:
    st.subheader("🚨 KRIITTISET HÄIRIÖT")
    for d in disruptions:
        st.markdown(f"""
        <div class='critical-alert'>
            <b>{d['type']}:</b> {d['info']}<br>
            <a href='{d['link']}' target='_blank'>[Siirry HSL häiriötiedotteisiin]</a>
        </div>
        """, unsafe_allow_html=True)

# 3. KAUKOJUNAT (Hki, Pasila, Tikkurila)
st.subheader("🚆 SAAPUVAT KAUKOJUNAT")
trains = get_trains()
for t in trains:
    delay_text = f"🚨 <b>Myöhässä: {t['delay']}</b>" if t['delay'] != "Ei" else "Aikataulussa"
    st.markdown(f"""
    <div class='event-card'>
        <b>{t['train']} ({t['origin']})</b> -> Saapuu {t['time']} <br>
        {delay_text} | <a href='{t['link']}' target='_blank'>[VR Seuranta]</a>
    </div>
    """, unsafe_allow_html=True)

# 4. SÄÄTILA
st.subheader("🌦️ SÄÄTILA")
weather = get_weather()
st.markdown(f"""
<div class='event-card'>
    {weather['status']} | <a href='{weather['link']}' target='_blank'>[Avaa sadetutka]</a>
</div>
""", unsafe_allow_html=True)

# 5. TAPAHTUMAT RYHMITTÄIN
st.subheader("📅 PÄIVÄN TAPAHTUMAT")

tab1, tab2, tab3 = st.tabs(["Kulttuuri", "Urheilu", "Meriliikenne"])

with tab1:
    st.markdown("""
    **Helsingin Kaupunginteatteri (HKT)**
    * Purku n. klo 21:15. *Arvio: ~20 autoa.*
    * [Siirry HKT sivuille](https://hkt.fi)
    
    **Musiikkitalo / Kansallisteatteri**
    * Purku n. klo 21:40. *Arvio: Mahdollisesti jonkin verran asiakkaita.*
    * [Siirry Musiikkitalon sivuille](https://www.musiikkitalo.fi)
    """)

with tab2:
    st.markdown("""
    **HIFK - Kärpät (Nordis)**
    * Arvioitu purku klo 21:00 (2,5h aloituksesta).
    * [Siirry Liigan sivuille](https://liiga.fi)
    """)

with tab3:
    st.markdown("""
    **Länsisatama T2**
    * MS Finlandia saapuu klo 00:30 (Su/Ma yönä maltillinen).
    * [Helsingin Sataman aikataulut](https://portofhelsinki.fi)
    """)

# 6. BONUS-KYYDIT
with st.expander("🩸 Bonus-kyydit (SPR / Laboratoriot)"):
    st.write("Verikuljetukset ja näytteet ovat kiva bonus, jos satut olemaan lähistöllä (esim. Vantaan härkälenkki) ja tolpalla on tilaa.")

st.divider()

# 7. KULJETTAJAN TILANNEPÄIVITYS & PALAUTE
st.subheader("📡 TILANNEILMOITUS & PALAUTE")
st.write("Jaa tilannekentällä muille (5-10 auton ydinryhmälle):")

col1, col2, col3 = st.columns(3)
if col1.button("🟢 Purku alkoi"):
    st.success("Tieto lähetetty: Purku alkoi!")
if col2.button("🔴 Hiljaista"):
    st.warning("Tieto lähetetty: Hiljaista.")
if col3.button("🔥 Paljon asiakkaita"):
    st.error("Tieto lähetetty: Paljon asiakkaita!")

# Palautelaatikko
kuljettajan_palaute = st.text_area("Kirjaa toteutuneet automäärät tai huomiot tähän:")
if st.button("Lähetä palaute"):
    if kuljettajan_palaute:
        # Tulevaisuudessa tämä tallentaa tiedon tietokantaan (esim. Firebase tai Google Sheets)
        st.success("Kiitos! Palaute tallennettu lokiin tulevaisuuden ennusteiden parantamiseksi.")
    else:
        st.info("Kirjoita jotain palautekenttään ennen lähetystä.")
