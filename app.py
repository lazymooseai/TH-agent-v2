import streamlit as st
import streamlit.components.v1 as components
import datetime
import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
import json

# --- ASETUKSET JA SIVUN MÄÄRITYS ---
st.set_page_config(page_title="TH Taktinen Tutka", page_icon="🚕", layout="wide")

# --- AUTOMAATTINEN PÄIVITYS (60 SEKUNTIA) ---
components.html(
    """
    <script>
    setTimeout(function(){
        window.parent.location.reload();
    }, 60000);
    </script>
    """,
    height=0,
    width=0
)

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

# --- 1. DATAN HAKU: LAIVAT ---
@st.cache_data(ttl=600)
def get_ships():
    url = "https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2"
    headers = {'User-Agent': 'Mozilla/5.0'}
    laivat_lista = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rivit = soup.find_all('tr')
        for rivi in rivit:
            solut = rivi.find_all(['td'])
            if len(solut) >= 4:
                aika = solut[0].text.strip()
                laiva = solut[1].text.strip()
                terminaali = solut[3].text.strip() if len(solut) > 3 else "Tarkista"
                
                if aika and laiva and "Lähtee" not in laiva:
                    laivat_lista.append({"ship": laiva, "port": terminaali, "time": aika, "pax": "Katso varustamo", "status": "Live"})
                    
        if laivat_lista: return laivat_lista[:4]
        return [{"ship": "Data vaatii JavaScriptin", "port": "Port of Helsinki", "time": "-", "pax": "-", "status": "Yhteys OK"}]
    except Exception as e:
        return [{"ship": "Yhteysvirhe satamaan", "port": "-", "time": "-", "pax": "-", "status": str(e)[:30]}]

# --- 2. DATAN HAKU: JUNAT ---
@st.cache_data(ttl=50) 
def get_trains(asema_nimi):
    nykyhetki = datetime.datetime.now(ZoneInfo("Europe/Helsinki"))
    asema_koodit = {'Helsinki': 'HKI', 'Pasila': 'PSL', 'Tikkurila': 'TKL'}
    koodi = asema_koodit.get(asema_nimi, 'HKI')
    
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{koodi}?arrived_trains=0&arriving_trains=20&train_categories=Long-distance"
    
    kaupungit = {'ROV': 'Rovaniemi', 'OUL': 'Oulu', 'TPE': 'Tampere', 'TKU': 'Turku', 
                 'KJA': 'Kajaani', 'JNS': 'Joensuu', 'YV': 'Ylivieska', 'VAA': 'Vaasa', 
                 'JY': 'Jyväskylä', 'KUO': 'Kuopio', 'POR': 'Pori', 'SJK': 'Seinäjoki', 
                 'LVT': 'Lappeenranta', 'KOK': 'Kokkola', 'KEM': 'Kemi'}
    
    junat_lista = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for juna in data:
            juna_tyyppi = juna.get('trainType', '')
            juna_numero = juna.get('trainNumber', '')
            juna_nimi = f"{juna_tyyppi} {juna_numero}"
            
            lahto_koodi = juna['timeTableRows'][0]['stationShortCode']
            if lahto_koodi in ['HKI', 'PSL']:
                continue
                
            lahto_kaupunki = kaupungit.get(lahto_koodi, lahto_koodi)
            aika_obj = None
            aika_str = ""
            viive_min = 0
            peruttu = juna.get('cancelled', False)
            mennyt_juna = False
            
            for rivi in juna['timeTableRows']:
                if rivi['stationShortCode'] == koodi and rivi['type'] == 'ARRIVAL':
                    aika_raaka = rivi.get('liveEstimateTime', rivi.get('scheduledTime', ''))
                    if aika_raaka:
                        try:
                            aika_obj = datetime.datetime.strptime(aika_raaka[:16], "%Y-%m-%dT%H:%M")
                            aika_obj = aika_obj.replace(tzinfo=datetime.timezone.utc).astimezone(ZoneInfo("Europe/Helsinki"))
                            if aika_obj < nykyhetki - datetime.timedelta(minutes=2):
                                mennyt_juna = True
                            aika_str = aika_obj.strftime("%H:%M")
                        except Exception:
                            aika_str = aika_raaka[11:16]
                    
                    viive_min = rivi.get('differenceInMinutes', 0)
                    break
            
            if not peruttu and aika_str and aika_obj and not mennyt_juna:
                viive_teksti = "Ei" if viive_min <= 0 else f"{viive_min} min"
                junat_lista.append({
                    "train": juna_nimi,
                    "origin": lahto_kaupunki,
                    "time": aika_str,
                    "datetime_obj": aika_obj, 
                    "delay": viive_teksti
                })
        
        junat_lista = sorted(junat_lista, key=lambda k: k['datetime_obj'])
        return junat_lista[:5] 

    except Exception as e:
        return [{"train": "API Virhe", "origin": "-", "time": "-", "delay": "Ei"}]

# --- 3. DATAN HAKU: LENNOT (MANUAALINEN OHJAUS + OIKEA ENDPOINT) ---
@st.cache_data(ttl=60) 
def get_flights_live(): 
    # Usein Finavian oikea osoite saapuville lennoille (arr) Helsinkiin (HEL) on tämä:
    url = "https://apigw.finavia.fi/flights/public/v0/flights/arr/HEL"
    api_key = "838062ef175f47708d566bbf5a38a710" 
    
    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Cache-Control': 'no-cache',
        'Accept': 'application/json' 
    }
    
    lennot_lista = []
    
    try:
        # TAKTIIKKA: allow_redirects=False estää Pythonia hukkaamasta avainta!
        response = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
        
        # Jos palvelin käskee siirtyä toiseen osoitteeseen (301, 302, jne):
        while response.status_code in (301, 302, 303, 307, 308):
            uusi_osoite = response.headers['Location']
            # Mennään uuteen osoitteeseen ja PAKOTETAAN avain mukaan
            response = requests.get(uusi_osoite, headers=headers, allow_redirects=False, timeout=10)

        if response.status_code == 401:
            virhesyy = response.text
            return [{"flight": "Pääsy evätty", "origin": "Avain hukattiin", "time": "-", "type": "-", "status": "Virhe 401", "debug_json": f"Palvelin vastasi:\n{virhesyy}"}]
            
        response.raise_for_status()
        data = response.json()
        
        saapuvat = []
        if isinstance(data, dict):
            if 'arr' in data: saapuvat = data['arr']
            elif 'flights' in data and 'arr' in data['flights']: saapuvat = data['flights']['arr']
            elif 'body' in data and 'flight' in data['body']: saapuvat = data['body']['flight']
        elif isinstance(data, list):
            saapuvat = data

        if not saapuvat:
            raakadata_nayte = json.dumps(data, indent=2)[:1000]
            return [{"flight": "Yhteys OK", "origin": "Ota kuva Röntgenistä!", "time": "-", "type": "-", "status": "Rakennetta ei tunnistettu", "debug_json": raakadata_nayte}]
            
        laajarunko_koodit = ['359', '350', '333', '330', '340', '788', '789', '777', '77W']
        
        for lento in saapuvat:
            fltnr = lento.get('fltnr', lento.get('flightNumber', '??'))
            kohde = lento.get('route_n_1', lento.get('airport', 'Tuntematon'))
            aika_raaka = lento.get('sdt', lento.get('scheduledTime', ''))
            actype = lento.get('actype', lento.get('aircraftType', ''))
            status = lento.get('prt_f', lento.get('statusInfo', 'Odottaa'))
            
            aika_str = str(aika_raaka)[11:16] if 'T' in str(aika_raaka) else str(aika_raaka)[:5]
            
            is_wb = any(wb in str(actype) for wb in laajarunko_koodit)
            tyyppi = f"Laajarunko ✈️ ({actype})" if is_wb else f"Kapearunko ({actype})"
            
            tila_teksti = str(status)
            if "myöhässä" in tila_teksti.lower() or "delayed" in tila_teksti.lower():
                tila_teksti = f"🔴 {tila_teksti}"
            elif is_wb and "laskeutunut" not in tila_teksti.lower() and "landed" not in tila_teksti.lower():
                tila_teksti = f"🔥 Odottaa massapurkua ({tila_teksti})"
                
            lennot_lista.append({
                "flight": fltnr,
                "origin": kohde,
                "time": aika_str,
                "type": tyyppi,
                "status": tila_teksti,
                "debug_json": "" 
            })
            
        if lennot_lista:
            return lennot_lista[:7]
            
        return [{"flight": "Lista tyhjä", "origin": "-", "time": "-", "type": "-", "status": "Ei saapuvia lentoja"}]

    except Exception as e:
        return [{"flight": "Luku-virhe", "origin": "-", "time": "-", "type": "-", "status": str(e)[:30]}]

# ==========================================
# --- KÄYTTÖLIITTYMÄN PIIRTÄMINEN (UI) ---
# ==========================================

suomen_aika = datetime.datetime.now(ZoneInfo("Europe/Helsinki"))
current_time = suomen_aika.strftime("%H:%M")
weather_link = "https://www.ilmatieteenlaitos.fi/sadealueet-suomessa"

# YLÄPALKKI
st.markdown(f"""
<div class='header-container'>
    <div>
        <div class='app-title'>TH Taktinen Tutka 🚕</div>
        <div class='time-display'>{current_time} <span style='font-size:16px; color:#888;'>(Live)</span></div>
    </div>
    <div style='text-align: right;'>
        <div style='font-size: 32px; color: #a3c2a3; font-weight: bold;'>⛅ +12°C</div>
        <a href='{weather_link}' class='taksi-link' target='_blank'>Avaa sadetutka ➔</a>
    </div>
</div>
""", unsafe_allow_html=True)

# LOHKO 1: JUNALIIKENNE
st.markdown("<h3 style='color:#e0e0e0; font-size: 26px;'>🚆 SAAPUVAT KAUKOJUNAT (Inbound)</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
if col1.button("Helsinki", use_container_width=True): st.session_state.valittu_asema = 'Helsinki'
if col2.button("Pasila", use_container_width=True): st.session_state.valittu_asema = 'Pasila'
if col3.button("Tikkurila", use_container_width=True): st.session_state.valittu_asema = 'Tikkurila'

valittu = st.session_state.valittu_asema
trains = get_trains(valittu)

vr_linkit = {
    'Helsinki': 'https://www.vr.fi/radalla?station=HKI&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D&follow=true&direction=ARRIVAL',
    'Pasila': 'https://www.vr.fi/radalla?station=PSL&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D',
    'Tikkurila': 'https://www.vr.fi/radalla?station=TKL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D&follow=true&direction=ARRIVAL'
}
oikea_vr_linkki = vr_linkit.get(valittu, 'https://www.vr.fi/radalla')

train_html = f"<div style='margin-bottom: 15px; color: #a3c2a3;'>Näkymä: <b>{valittu}</b> (Vain kaukaa saapuvat)</div>"
if trains and trains[0]["train"] != "API Virhe":
    for t in trains:
        delay_class = "delay-text" if t['delay'] != "Ei" else "ok-text"
        delay_text = f"Myöhässä: {t['delay']}" if t['delay'] != "Ei" else "Aikataulussa"
        train_html += f"<b>{t['time']}</b> - {t['train']} (Lähtö: {t['origin']}) <br>└ Tila: <span class='{delay_class}'>{delay_text}</span><br><br>"
else:
    train_html += "Ei saapuvia kaukojunia lähiaikoina."

st.markdown(f"<div class='taksi-card'>{train_html}<a href='{oikea_vr_linkki}' class='taksi-link' target='_blank'>Avaa VR Radalla ({valittu}) ➔</a></div>", unsafe_allow_html=True)


# LOHKO 2: LAIVAT
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


# LOHKO 3: LENTOKENTTÄ (FINAVIA API)
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px; font-size: 26px;'>✈️ LENTOKENTTÄ (Finavia API Live)</h3>", unsafe_allow_html=True)
flights = get_flights_live()
flight_html = f"<div style='margin-bottom: 15px; color: #a3c2a3;'>Näkymä: <b>Taktiset poiminnat</b></div>"

for f in flights:
    status_color = "#ff4b4b" if "🔥" in f['status'] or "🔴" in f['status'] or "Virhe" in f['status'] else "#a3c2a3"
    type_color = "#ffeb3b" if "Laajarunko" in f['type'] else "#e0e0e0"
    
    flight_html += f"<b>{f['time']}</b> - {f['origin']} ({f['flight']}) <br>└ Tyyppi: <span style='color:{type_color};'>{f['type']}</span> | Tila: <span style='color:{status_color}; font-weight:bold;'>{f['status']}</span><br><br>"
    
st.markdown(f"<div class='taksi-card'>{flight_html}<a href='https://www.finavia.fi/fi/lentoasemat/helsinki-vantaa/lennot/saapuvat' class='taksi-link' target='_blank'>Avaa Finavia Saapuvat ➔</a></div>", unsafe_allow_html=True)

# RÖNTGEN
if flights and flights[0].get("debug_json"):
    with st.expander("🔍 TEKOÄLYN RÖNTGEN (Avaa ja ota kuva)"):
        st.write("Jos näet tämän, onnistuimme murtamaan oven! Ota kuva tästä:")
        st.code(flights[0]["debug_json"], language='json')

# LOHKO 4: TAPAHTUMAT
st.markdown("<h3 style='color:#e0e0e0; margin-top:30px; font-size: 26px;'>📅 TAPAHTUMAT & KAPASITEETTI</h3>", unsafe_allow_html=True)
st.markdown("""<div class='taksi-card'><div class='card-title'>Helsingin Kaupunginteatteri (HKT)</div>Tapahtuma: <b>Pieni merenneito</b><br>Purku n. <b>klo 21:15</b><br>Kapasiteetti: <b>947 henkilöä</b> | <span class='sold-out'>🔥 LOPPUUNMYYTY</span><br><i>Arvio: ~14-20 autoa.</i><br><a href='https://hkt.fi/kalenteri/' class='taksi-link' target='_blank'>Avaa HKT Kalenteri ➔</a></div>""", unsafe_allow_html=True)
st.markdown("""<div class='taksi-card'><div class='card-title'>Musiikkitalo</div>Tapahtuma: <b>RSO:n konsertti</b><br>Purku n. <b>klo 21:30</b><br>Kapasiteetti: <b>1 704 henkilöä</b><br><i>Huomio: Aseman vieressä, paljon kävelijöitä junaan.</i><br><a href='https://musiikkitalo.fi/konsertit-ja-tapahtumat' class='taksi-link' target='_blank'>Avaa Musiikkitalon tapahtumat ➔</a></div>""", unsafe_allow_html=True)
