import streamlit as st
import datetime
import requests
from bs4 import BeautifulSoup
import json

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
    </style>
""", unsafe_allow_html=True)

# --- 1. DATAN HAKU: LAIVAT (Port of Helsinki) ---
@st.cache_data(ttl=600)
def get_ships():
    url = "https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    laivat_lista = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Etsitään Helsingin sataman saapuvien laivojen taulukkoa
        # Käytetään laajaa hakua löytämään olennaiset taulukkorivit (tr)
        rivit = soup.find_all('tr')
        
        for rivi in rivit:
            solut = rivi.find_all(['td'])
            if len(solut) >= 4: # Tyypillinen sataman taulukko: Aika, Laiva, Varustamo, Terminaali
                aika = solut[0].text.strip()
                laiva = solut[1].text.strip()
                terminaali = solut[3].text.strip() if len(solut) > 3 else "Tarkista"
                
                if aika and laiva and "Lähtee" not in laiva: # Yritetään suodattaa vain saapuvat
                    laivat_lista.append({
                        "ship": laiva,
                        "port": terminaali,
                        "time": aika,
                        "pax": "Katso varustamo", # Satama ei ilmoita matkustajamäärää suoraan
                        "status": "Live"
                    })
                    
        # Jos raapinta onnistui, palautetaan 4 seuraavaa
        if laivat_lista:
            return laivat_lista[:4]
        else:
            return [{"ship": "Data vaatii JavaScriptin", "port": "Port of Helsinki", "time": "-", "pax": "-", "status": "Yhteys OK"}]

    except Exception as e:
        return [{"ship": "Yhteysvirhe satamaan", "port": "-", "time": "-", "pax": "-", "status": str(e)[:30]}]


# --- 2. DATAN HAKU: JUNAT (DIGITRAFFIC API - REAL TIME) ---
# TÄMÄ ON AITO, REAALIAIKAINEN RAJAPINTA SUOMEN VALTION LIIKENTEENOHJAUKSESTA
@st.cache_data(ttl=60) # Päivitetään minuutin välein (API sallii tiheän haun)
def get_trains(asema_nimi):
    # Asemien viralliset lyhenteet Fintrafficin järjestelmässä
    asema_koodit = {'Helsinki': 'HKI', 'Pasila': 'PSL', 'Tikkurila': 'TKL'}
    koodi = asema_koodit.get(asema_nimi, 'HKI')
    
    # Haetaan 10 seuraavaa saapuvaa kaukojunaa
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{koodi}?arriving_trains=10&train_categories=Long-distance"
    
    # Sanakirja lähtöasemien lyhenteiden suomentamiseksi
    kaupungit = {'ROV': 'Rovaniemi', 'OUL': 'Oulu', 'TPE': 'Tampere', 'TKU': 'Turku', 
                 'KAI': 'Kajaani', 'JNS': 'Joensuu', 'YV': 'Ylivieska', 'VAA': 'Vaasa', 'JY': 'Jyväskylä', 'KOP': 'Kuopio'}
    
    junat_lista = []
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for juna in data:
            juna_tyyppi = juna.get('trainType', '')
            juna_numero = juna.get('trainNumber', '')
            juna_nimi = f"{juna_tyyppi} {juna_numero}"
            
            # Selvitetään mistä juna on lähtenyt (reitin ensimmäinen asema)
            lahto_koodi = juna['timeTableRows'][0]['stationShortCode']
            lahto_kaupunki = kaupungit.get(lahto_koodi, lahto_koodi)
            
            # Etsitään saapumisaika ja mahdollinen myöhästyminen valitulle asemalle
            aika_str = ""
            viive_min = 0
            peruttu = juna.get('cancelled', False)
            
            for rivi in juna['timeTableRows']:
                if rivi['stationShortCode'] == koodi and rivi['type'] == 'ARRIVAL':
                    # Aika on muodossa 2026-03-12T19:12:00.000Z. Pilkotaan siitä tunnit ja minuutit.
                    # Muunnetaan UTC-aika Suomen aikaan (lisätään 2h tai 3h). Yksinkertaisuuden vuoksi otetaan aika suoraan raakadatasta ja formatoidaan.
                    aika_raaka = rivi.get('liveEstimateTime', rivi.get('scheduledTime', ''))
                    if aika_raaka:
                        # Haetaan tuntiosa (Helsingin aikavyöhyke asettaa haasteita UTC:lle, mutta liveEstimateTime on usein jo korjattu. Tehdään turvallinen haku).
                        try:
                            aika_obj = datetime.datetime.strptime(aika_raaka[:16], "%Y-%m-%dT%H:%M")
                            # Yksinkertainen aikavyöhykekorjaus (+2 tuntia talviaika, +3 kesäaika. Laitetaan +2 oletuksena)
                            aika_obj = aika_obj + datetime.timedelta(hours=2)
                            aika_str = aika_obj.strftime("%H:%M")
                        except:
                            aika_str = aika_raaka[11:16] # Vara-suunnitelma
                    
                    viive_min = rivi.get('differenceInMinutes', 0)
                    break
            
            if not peruttu and aika_str:
                viive_teksti = "Ei" if viive_min <= 0 else f"{viive_min} min"
                
                junat_lista.append({
                    "train": juna_nimi,
                    "origin": lahto_kaupunki,
                    "time": aika_str,
                    "delay": viive_teksti,
                    "link": f"https://www.vr.fi/radalla?station={koodi}&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D"
                })
        
        # Järjestetään ajan mukaan ja palautetaan 5 seuraavaa
        junat_lista = sorted(junat_lista, key=lambda k: k['time'])
        return junat_lista[:5]

    except Exception as e:
        return [{"train": "API Virhe", "origin": "-", "time": "-", "delay": "Ei", "link": f"https://www.vr.fi/radalla?station={koodi}"}]


# --- 3. DATAN HAKU: LENNOT ---
def get_flights():
    return [
        {"flight": "AY1338", "origin": "Lontoo", "time": "23:15", "type": "Laajarunko", "status": "🔥 Massapurku"},
        {"flight": "AY074", "origin": "Tokio", "time": "23:40", "type": "Laajarunko", "status": "🔥 Massapurku"},
        {"flight": "D8 3213", "origin": "Tukholma", "time": "00:10", "type": "Kapearunko", "status": "Myöhässä 40min"}
    ]

# ==========================================
# --- KÄYTTÖLIITTYMÄN PIIRTÄMINEN (UI) ---
# ==========================================

current_time = datetime.datetime.now().strftime("%H:%M")
weather_link = "https://www.ilmatieteenlaitos.fi/sadealueet-suomessa"

# YLÄPALKKI
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

# LOHKO 1: JUNALIIKENNE (LIVE API)
st.markdown("<h3 style='color:#e0e0e0; font-size: 26px;'>🚆 KAUKOJUNAT (LIVE Fintraffic API)</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
if col1.button("Helsinki", use_container_width=True): st.session_state.valittu_asema = 'Helsinki'
if col2.button("Pasila", use_container_width=True): st.session_state.valittu_asema = 'Pasila'
if col3.button("Tikkurila", use_container_width=True): st.session_state.valittu_asema = 'Tikkurila'

valittu = st.session_state.valittu_asema
trains = get_trains(valittu)

train_html = f"<div style='margin-bottom: 15px; color: #a3c2a3;'>Näkymä: <b>{valittu}</b> (Päivittyy minuutin välein)</div>"
for t in trains:
    delay_class = "delay-text" if t['delay'] != "Ei" else "ok-text"
    delay_text = f"Myöhässä: {t['delay']}" if t['delay'] != "Ei" else "Aikataulussa"
    train_html += f"<b>{t['time']}</b> - {t['train']} ({t['origin']} -> {valittu}) <br>└ Tila: <span class='{delay_class}'>{delay_text}</span><br><br>"

st.markdown(f"<div class='taksi-card'>{train_html}<a href='{trains[0]['link']}' class='taksi-link' target='_blank'>Avaa VR Radalla ({valittu}) ➔</a></div>", unsafe_allow_html=True)


# LOHKO 2: LAIVAT (Helsingin Satama)
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px; font-size: 26px;'>🚢 MATKUSTAJALAIVAT (Helsingin Satama)</h3>", unsafe_allow_html=True)
ships = get_ships()
ship_html = ""
for s in ships:
    pax_str = f"<br>└ Matkustajavolyymi: <span class='pax-count' style='font-size: 20px;'>{s['pax']}</span>" if s['pax'] != "-" else ""
    ship_html += f"<b>{s['time']}</b> - {s['ship']} ({s['port']}) {pax_str}<br><br>"

st.markdown(f"""
<div class='taksi-card'>
    {ship_html}
    <a href='https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2' class='taksi-link' target='_blank'>Avaa Helsingin Satama ➔</a>
</div>
""", unsafe_allow_html=True)


# LOHKO 3: LENTOKENTTÄ
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px; font-size: 26px;'>✈️ LENTOKENTTÄ (HELSINKI-VANTAA)</h3>", unsafe_allow_html=True)
flights = get_flights()
flight_html = f"<div style='margin-bottom: 15px; color: #a3c2a3;'>Näkymä: <b>Taktiset poiminnat ({len(flights)} kpl)</b></div>"
for f in flights:
    status_color = "#ff4b4b" if "🔥" in f['status'] or "Myöhässä" in f['status'] else "#a3c2a3"
    flight_html += f"<b>{f['time']}</b> - {f['origin']} ({f['flight']}) <br>└ Tyyppi: {f['type']} | Tila: <span style='color:{status_color}; font-weight:bold;'>{f['status']}</span><br><br>"
st.markdown(f"<div class='taksi-card'>{flight_html}<a href='https://www.finavia.fi/fi/lennot' class='taksi-link' target='_blank'>Avaa Finavia Saapuvat ➔</a></div>", unsafe_allow_html=True)


# LOHKO 4: TAPAHTUMAT
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px; font-size: 26px;'>📅 TAPAHTUMAT & KAPASITEETTI</h3>", unsafe_allow_html=True)
st.markdown("""<div class='taksi-card'><div class='card-title'>Helsingin Kaupunginteatteri (HKT)</div>Tapahtuma: <b>Pieni merenneito</b><br>Purku n. <b>klo 21:15</b><br>Kapasiteetti: <b>947 henkilöä</b> | <span class='sold-out'>🔥 LOPPUUNMYYTY</span><br><i>Arvio: ~14-20 autoa.</i><br><a href='https://hkt.fi/kalenteri/' class='taksi-link' target='_blank'>Avaa HKT Kalenteri ➔</a></div>""", unsafe_allow_html=True)
st.markdown("""<div class='taksi-card'><div class='card-title'>Musiikkitalo</div>Tapahtuma: <b>RSO:n konsertti</b><br>Purku n. <b>klo 21:30</b><br>Kapasiteetti: <b>1 704 henkilöä</b><br><i>Huomio: Aseman vieressä, paljon kävelijöitä junaan.</i><br><a href='https://musiikkitalo.fi/konsertit-ja-tapahtumat' class='taksi-link' target='_blank'>Avaa Musiikkitalon tapahtumat ➔</a></div>""", unsafe_allow_html=True)
