import streamlit as st
import streamlit.components.v1 as components
import datetime
import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
import json
import re

# ─────────────────────────────────────────────

# ASETUKSET

# ─────────────────────────────────────────────

st.set_page_config(page_title=“TH Taktinen Tutka”, page_icon=“🚕”, layout=“wide”)

FINAVIA_API_KEY = “838062ef175f47708d566bbf5a38a710”

# Automaattinen päivitys 60 sekunnin välein

components.html(”””

<script>
setTimeout(function(){ window.parent.location.reload(); }, 60000);
</script>

“””, height=0, width=0)

# Session state

if “valittu_asema” not in st.session_state:
st.session_state.valittu_asema = “Helsinki”

# ─────────────────────────────────────────────

# CSS – tumma teema

# ─────────────────────────────────────────────

st.markdown(”””

<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
.main { background-color: #121212; }

.header-container {
    display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px;
}
.app-title  { font-size: 32px; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
.time-display { font-size: 42px; font-weight: bold; color: #e0e0e0; line-height: 1; }

.taksi-card {
    background-color: #1e1e2a; color: #e0e0e0; padding: 22px;
    border-radius: 12px; margin-bottom: 20px; font-size: 20px;
    border: 1px solid #3a3a50; box-shadow: 0 4px 8px rgba(0,0,0,0.3); line-height: 1.7;
}
.card-title {
    font-size: 24px; font-weight: bold; margin-bottom: 12px;
    color: #ffffff; border-bottom: 2px solid #444; padding-bottom: 8px;
}
.taksi-link {
    color: #5bc0de; text-decoration: none; font-size: 18px;
    display: inline-block; margin-top: 12px; font-weight: bold;
}
.taksi-link:hover { color: #82d4ef; }

.badge-red    { background:#7a1a1a; color:#ff9999; padding:2px 8px; border-radius:4px; font-size:16px; font-weight:bold; }
.badge-yellow { background:#5a4a00; color:#ffeb3b; padding:2px 8px; border-radius:4px; font-size:16px; font-weight:bold; }
.badge-green  { background:#1a4a1a; color:#88d888; padding:2px 8px; border-radius:4px; font-size:16px; font-weight:bold; }
.badge-blue   { background:#1a2a5a; color:#8ab4f8; padding:2px 8px; border-radius:4px; font-size:16px; font-weight:bold; }

.sold-out  { color: #ff4b4b; font-weight: bold; }
.pax-good  { color: #ffeb3b; font-weight: bold; }
.pax-ok    { color: #a3c2a3; }
.delay-bad { color: #ff9999; font-weight: bold; }
.on-time   { color: #88d888; }

.section-header {
    color: #e0e0e0; font-size: 24px; font-weight: bold;
    margin-top: 28px; margin-bottom: 10px;
    border-left: 4px solid #5bc0de; padding-left: 12px;
}

.venue-row { margin-bottom: 6px; }
.venue-name { color: #ffffff; font-weight: bold; }
.venue-address { color: #aaaaaa; font-size: 16px; }
</style>

“””, unsafe_allow_html=True)

# ═══════════════════════════════════════════════

# DATA: AVERIO – matkustajamäärät

# ═══════════════════════════════════════════════

@st.cache_data(ttl=600)
def get_averio_ships():
“””
Hakee laivat ja matkustajamäärät averio.fi/laivat -sivulta.
Palauttaa listan dict-alkioita: {ship, terminal, arr_time, dep_time, pax, raw}.
“””
url = “https://averio.fi/laivat”
headers = {
“User-Agent”: (
“Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) “
“AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1”
),
“Accept-Language”: “fi-FI,fi;q=0.9”,
“Accept”: “text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8”,
}
laivat = []
try:
resp = requests.get(url, headers=headers, timeout=12)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, “html.parser”)

```
    # Etsitään taulukot tai rivit, joissa on laivadata
    # Averio käyttää tyypillisesti HTML-taulukkoa tai div-rakenteita
    taulukot = soup.find_all("table")

    for taulu in taulukot:
        rivit = taulu.find_all("tr")
        for rivi in rivit:
            solut = [td.get_text(strip=True) for td in rivi.find_all(["td", "th"])]
            if len(solut) < 3:
                continue

            rivi_teksti = " ".join(solut).lower()

            # Suodatetaan pois otsikkorivit
            if any(h in rivi_teksti for h in ["alus", "laiva", "ship", "vessel"]):
                continue

            # Haetaan matkustajamäärä – luku > 50
            pax = None
            for solu in solut:
                puhdas = re.sub(r"[^\d]", "", solu)
                if puhdas and 50 <= int(puhdas) <= 9999:
                    pax = int(puhdas)
                    break

            # Laivan nimi: pisin ei-numeerinen solu
            nimi_solu = max(
                [s for s in solut if re.search(r"[A-Za-zÄäÖöÅå]{3,}", s)],
                key=len,
                default=None,
            )
            if not nimi_solu or len(nimi_solu) < 3:
                continue

            laivat.append({
                "ship": nimi_solu,
                "terminal": _tunnista_terminaali(rivi_teksti),
                "time": _etsi_aika(solut),
                "pax": pax,
                "raw": " | ".join(solut),
            })

    # Jos taulukot tyhjät, kokeillaan div-rakennetta
    if not laivat:
        kortit = soup.find_all("div", class_=re.compile(r"(ship|laiva|vessel|row|card|item)", re.I))
        for kortti in kortit[:6]:
            teksti = kortti.get_text(separator=" ", strip=True)
            pax = None
            for token in teksti.split():
                puhdas = re.sub(r"[^\d]", "", token)
                if puhdas and 50 <= int(puhdas) <= 9999:
                    pax = int(puhdas)
                    break
            laivat.append({
                "ship": teksti[:40],
                "terminal": _tunnista_terminaali(teksti.lower()),
                "time": _etsi_aika(teksti.split()),
                "pax": pax,
                "raw": teksti[:80],
            })

    if laivat:
        return laivat[:5]

    # Viimeisenä hätäkeinona: raaka teksti
    return [{
        "ship": "Averio ladattu (HTML rakenne muuttunut)",
        "terminal": "Tarkista manuaalisesti",
        "time": "-",
        "pax": None,
        "raw": resp.text[:200],
    }]

except Exception as e:
    return [{"ship": f"Averio-virhe: {e}", "terminal": "-", "time": "-", "pax": None, "raw": ""}]
```

def _tunnista_terminaali(teksti: str) -> str:
if “t2” in teksti or “länsisatama” in teksti or “lansisatama” in teksti:
return “Länsisatama T2”
if “t1” in teksti or “olympia” in teksti:
return “Olympia T1”
if “katajanokka” in teksti:
return “Katajanokka”
if “vuosaari” in teksti:
return “Vuosaari (rahti)”
return “Tarkista”

def _etsi_aika(osat: list) -> str:
for osa in osat:
m = re.search(r”\b([0-2]?\d:[0-5]\d)\b”, str(osa))
if m:
return m.group(1)
return “-”

def _pax_arvio(pax) -> tuple[str, str]:
“”“Palauttaa (arvio-teksti, css-luokka)”””
if pax is None:
return “Ei tietoa”, “pax-ok”
autoa = round(pax * 0.025)  # ~2.5 autoa/100 matkustajaa
if pax >= 400:
return f”🔥 {pax} matkustajaa (~{autoa} autoa, ERINOMAINEN)”, “pax-good”
if pax >= 200:
return f”✅ {pax} matkustajaa (~{autoa} autoa)”, “pax-ok”
return f”⬇️ {pax} matkustajaa (~{autoa} autoa, matala)”, “pax-ok”

# ═══════════════════════════════════════════════

# DATA: HELSINGIN SATAMA – aikataulu

# ═══════════════════════════════════════════════

@st.cache_data(ttl=600)
def get_port_schedule():
url = “https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2”
headers = {“User-Agent”: “Mozilla/5.0”}
try:
resp = requests.get(url, headers=headers, timeout=12)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, “html.parser”)
lista = []
for rivi in soup.find_all(“tr”):
solut = rivi.find_all(“td”)
if len(solut) >= 4:
aika = solut[0].get_text(strip=True)
laiva = solut[1].get_text(strip=True)
terminaali = solut[3].get_text(strip=True) if len(solut) > 3 else “?”
if aika and laiva and re.match(r”\d{1,2}:\d{2}”, aika):
lista.append({“time”: aika, “ship”: laiva, “terminal”: terminaali})
return lista[:6] if lista else []
except Exception as e:
return [{“time”: “-”, “ship”: f”Virhe: {e}”, “terminal”: “-”}]

# ═══════════════════════════════════════════════

# DATA: JUNAT (Digitraffic API)

# ═══════════════════════════════════════════════

@st.cache_data(ttl=50)
def get_trains(asema_nimi: str):
nykyhetki = datetime.datetime.now(ZoneInfo(“Europe/Helsinki”))
koodit = {“Helsinki”: “HKI”, “Pasila”: “PSL”, “Tikkurila”: “TKL”}
koodi = koodit.get(asema_nimi, “HKI”)
url = (
f”https://rata.digitraffic.fi/api/v1/live-trains/station/{koodi}”
“?arrived_trains=0&arriving_trains=25&train_categories=Long-distance”
)
kaupungit = {
“ROV”: “Rovaniemi”, “OUL”: “Oulu”, “TPE”: “Tampere”, “TKU”: “Turku”,
“KJA”: “Kajaani”, “JNS”: “Joensuu”, “YV”: “Ylivieska”, “VAA”: “Vaasa”,
“JY”: “Jyväskylä”, “KUO”: “Kuopio”, “POR”: “Pori”, “SJK”: “Seinäjoki”,
“LVT”: “Lappeenranta”, “KOK”: “Kokkola”, “KEM”: “Kemi”, “KTI”: “Kittilä”,
“PMK”: “Paimio”, “TRE”: “Tampere”, “HMY”: “Hämeenlinna”,
}
tulos = []
try:
resp = requests.get(url, timeout=10)
resp.raise_for_status()
data = resp.json()
for juna in data:
tyyppi = juna.get(“trainType”, “”)
numero = juna.get(“trainNumber”, “”)
nimi = f”{tyyppi} {numero}”
lahto = juna[“timeTableRows”][0][“stationShortCode”]
if lahto in (“HKI”, “PSL”, “TKL”):
continue
lahto_kaupunki = kaupungit.get(lahto, lahto)
aika_obj = aika_str = None
viive = 0
if juna.get(“cancelled”):
continue
for rivi in juna[“timeTableRows”]:
if rivi[“stationShortCode”] == koodi and rivi[“type”] == “ARRIVAL”:
raaka = rivi.get(“liveEstimateTime”) or rivi.get(“scheduledTime”, “”)
try:
aika_obj = datetime.datetime.strptime(raaka[:16], “%Y-%m-%dT%H:%M”)
aika_obj = aika_obj.replace(tzinfo=datetime.timezone.utc).astimezone(
ZoneInfo(“Europe/Helsinki”)
)
if aika_obj < nykyhetki - datetime.timedelta(minutes=3):
aika_obj = None
else:
aika_str = aika_obj.strftime(”%H:%M”)
except Exception:
pass
viive = rivi.get(“differenceInMinutes”, 0)
break
if aika_str and aika_obj:
tulos.append({
“train”: nimi,
“origin”: lahto_kaupunki,
“time”: aika_str,
“dt”: aika_obj,
“delay”: viive if viive > 0 else 0,
})
tulos.sort(key=lambda k: k[“dt”])
return tulos[:6]
except Exception as e:
return [{“train”: “API-virhe”, “origin”: str(e)[:30], “time”: “-”, “dt”: None, “delay”: 0}]

# ═══════════════════════════════════════════════

# DATA: LENNOT (Finavia API)

# ═══════════════════════════════════════════════

@st.cache_data(ttl=60)
def get_flights():
“””
Kokeilee Finavia API:a kahdella tavalla:
1. Subscription-key URL-parametrina (Azure APIM standardi)
2. Subscription-key otsikkona (Ocp-Apim-Subscription-Key)
Molempien epäonnistuessa palauttaa informatiivisen virheen linkin kera.
“””
endpoints = [
f”https://apigw.finavia.fi/flights/public/v0/flights/arr/HEL?subscription-key={FINAVIA_API_KEY}”,
“https://apigw.finavia.fi/flights/public/v0/flights/arr/HEL”,
]
laajarunko = {“359”, “350”, “333”, “330”, “340”, “788”, “789”, “777”, “77W”, “388”, “744”, “74H”}

```
for i, url in enumerate(endpoints):
    hdrs = {
        "User-Agent": "Mozilla/5.0 (compatible; TH-Tutka/2.0)",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
    }
    if i == 1:
        hdrs["Ocp-Apim-Subscription-Key"] = FINAVIA_API_KEY

    try:
        resp = requests.get(url, headers=hdrs, timeout=10)
        if resp.status_code in (401, 403):
            continue  # Kokeile seuraavaa tapaa
        resp.raise_for_status()
        data = resp.json()

        # Poimitaan saapuvat lennot rakenteesta riippumatta
        saapuvat = []
        if isinstance(data, list):
            saapuvat = data
        elif isinstance(data, dict):
            for avain in ("arr", "flights", "body"):
                kandidaatti = data.get(avain)
                if isinstance(kandidaatti, list):
                    saapuvat = kandidaatti
                    break
                if isinstance(kandidaatti, dict):
                    for ala in ("arr", "flight"):
                        if isinstance(kandidaatti.get(ala), list):
                            saapuvat = kandidaatti[ala]
                            break

        if not saapuvat:
            continue

        tulos = []
        for lento in saapuvat:
            nro    = lento.get("fltnr") or lento.get("flightNumber", "??")
            kohde  = lento.get("route_n_1") or lento.get("airport", "Tuntematon")
            aika_r = str(lento.get("sdt") or lento.get("scheduledTime", ""))
            actype = str(lento.get("actype") or lento.get("aircraftType", ""))
            status = str(lento.get("prt_f") or lento.get("statusInfo", "Odottaa"))
            aika   = aika_r[11:16] if "T" in aika_r else aika_r[:5]
            wb     = any(c in actype for c in laajarunko)
            tyyppi = f"Laajarunko ✈ ({actype})" if wb else f"Kapearunko ({actype})"
            
            if wb and "laskeutunut" not in status.lower() and "landed" not in status.lower():
                status = f"🔥 Odottaa massapurkua – {status}"
            elif "delay" in status.lower() or "myöhässä" in status.lower():
                status = f"🔴 {status}"

            tulos.append({
                "flight": nro, "origin": kohde, "time": aika,
                "type": tyyppi, "wb": wb, "status": status,
            })

        # Järjestetään: laajarunkoiset ensin, sitten aika
        tulos.sort(key=lambda x: (not x["wb"], x["time"]))
        return tulos[:8], None

    except Exception:
        continue

# Kaikki yritykset epäonnistuivat
return [], "Finavia API ei vastannut. Avain saattaa olla vanhentunut tai rajapinta muuttunut."
```

# ═══════════════════════════════════════════════

# APUFUNKTIO: viive-badge

# ═══════════════════════════════════════════════

def viive_badge(min: int) -> str:
if min <= 0:
return “<span class='badge-green'>Aikataulussa</span>”
if min < 15:
return f”<span class='badge-yellow'>+{min} min</span>”
if min < 60:
return f”<span class='badge-red'>⚠ +{min} min</span>”
return f”<span class='badge-red'>🚨 +{min} min – VR-korvaus mahdollinen!</span>”

# ═══════════════════════════════════════════════

# UI: YLÄPALKKI

# ═══════════════════════════════════════════════

suomen_aika = datetime.datetime.now(ZoneInfo(“Europe/Helsinki”))
klo = suomen_aika.strftime(”%H:%M”)
paiva = suomen_aika.strftime(”%a %d.%m.%Y”).capitalize()

st.markdown(f”””

<div class='header-container'>
  <div>
    <div class='app-title'>🚕 TH Taktinen Tutka</div>
    <div class='time-display'>{klo} <span style='font-size:16px;color:#888;'>Helsinki · {paiva}</span></div>
  </div>
  <div style='text-align:right;'>
    <a href='https://www.ilmatieteenlaitos.fi/sade-ja-pilvialueet?area=etela-suomi'
       class='taksi-link' target='_blank' style='font-size:22px;'>🌧 Sadetutka ➔</a><br>
    <a href='https://liikennetilanne.fintraffic.fi/?x=385557.5&y=6672322.0&z=10'
       class='taksi-link' target='_blank' style='font-size:18px;'>🗺 Liikennetilanne ➔</a><br>
    <a href='https://hsl.fi/aikataulut-ja-reitit/hairiot'
       class='taksi-link' target='_blank' style='font-size:18px;'>🚇 HSL-häiriöt ➔</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════

# LOHKO 1: JUNAT

# ═══════════════════════════════════════════════

st.markdown(”<div class='section-header'>🚆 SAAPUVAT KAUKOJUNAT</div>”, unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
if c1.button(“📍 Helsinki”, use_container_width=True):
st.session_state.valittu_asema = “Helsinki”
if c2.button(“🏟 Pasila”, use_container_width=True):
st.session_state.valittu_asema = “Pasila”
if c3.button(“✈️ Tikkurila”, use_container_width=True):
st.session_state.valittu_asema = “Tikkurila”

valittu = st.session_state.valittu_asema
junat = get_trains(valittu)
vr_linkit = {
“Helsinki”:  “https://www.vr.fi/radalla?station=HKI&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D&follow=true”,
“Pasila”:    “https://www.vr.fi/radalla?station=PSL&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D”,
“Tikkurila”: “https://www.vr.fi/radalla?station=TKL&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D&follow=true”,
}
vr_hairiot = “https://www.vr.fi/radalla/poikkeustilanteet”

juna_html = f”<span style='color:#aaa;font-size:17px;'>Asema: <b>{valittu}</b> — vain kaukoliikenteen saapuvat</span><br><br>”
if junat and junat[0][“train”] != “API-virhe”:
for j in junat:
tähti = “”
if j[“origin”] in (“Rovaniemi”, “Kittilä”, “Oulu”, “Kuopio”):
tähti = “ ⭐”
juna_html += (
f”<b>{j[‘time’]}</b>  ·  {j[‘train’]} “
f”<span style='color:#aaa;'>(lähtö: {j[‘origin’]}{tähti})</span><br>”
f”  └ {viive_badge(j[‘delay’])}<br><br>”
)
if any(j[“delay”] >= 60 for j in junat):
juna_html += “<br><span class='badge-red'>🚨 Yli 60 min myöhässä – tarkista VR-korvauskäytäntö!</span><br>”
else:
juna_html += “Ei saapuvia kaukojunia lähiaikoina – tai API-yhteysongelma.”

st.markdown(f”””

<div class='taksi-card'>
  {juna_html}
  <a href='{vr_linkit[valittu]}' class='taksi-link' target='_blank'>VR Live ({valittu}) ➔</a>
  &nbsp;&nbsp;
  <a href='{vr_hairiot}' class='taksi-link' target='_blank' style='color:#ff9999;'>⚠ VR Poikkeustilanteet ➔</a>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════

# LOHKO 2: LAIVAT (Averio + Helsingin Satama)

# ═══════════════════════════════════════════════

st.markdown(”<div class='section-header'>🚢 MATKUSTAJALAIVAT</div>”, unsafe_allow_html=True)

col_a, col_b = st.columns(2)

# ── Vasemmalla: Averio (matkustajamäärät) ──────

with col_a:
averio_laivat = get_averio_ships()
averio_html = “<div class='card-title'>Averio – Matkustajamäärät</div>”
averio_html += “<span style='color:#aaa;font-size:15px;'>⚠ Huom: klo 00:30 MS Finlandia → <b>Länsisatama T2</b>, ei Vuosaari</span><br><br>”
for laiva in averio_laivat:
arvio_teksti, arvio_css = _pax_arvio(laiva[“pax”])
averio_html += (
f”<b>{laiva[‘time’]}</b>  ·  {laiva[‘ship’]}<br>”
f”  └ Terminaali: {laiva[‘terminal’]}<br>”
f”  └ <span class='{arvio_css}'>{arvio_teksti}</span><br><br>”
)
st.markdown(f”””
<div class='taksi-card'>
{averio_html}
<a href='https://averio.fi/laivat' class='taksi-link' target='_blank'>Avaa Averio ➔</a>
</div>
“””, unsafe_allow_html=True)

# ── Oikealla: Helsingin Satama (aikataulu) ─────

with col_b:
port_laivat = get_port_schedule()
port_html = “<div class='card-title'>Helsingin Satama – Aikataulu</div>”
if port_laivat:
for laiva in port_laivat:
port_html += (
f”<b>{laiva[‘time’]}</b>  ·  {laiva[‘ship’]}<br>”
f”  └ {laiva[‘terminal’]}<br><br>”
)
else:
port_html += “Ei dataa – sivu saattaa vaatia JavaScript-renderöinnin.<br>”
st.markdown(f”””
<div class='taksi-card'>
{port_html}
<a href='https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2'
class='taksi-link' target='_blank'>Avaa Helsingin Satama ➔</a>
</div>
“””, unsafe_allow_html=True)

# ═══════════════════════════════════════════════

# LOHKO 3: LENNOT (Finavia API)

# ═══════════════════════════════════════════════

st.markdown(”<div class='section-header'>✈️ LENTOKENTTÄ (Helsinki-Vantaa)</div>”, unsafe_allow_html=True)

lennot, lento_virhe = get_flights()

if lento_virhe:
st.markdown(f”””
<div class='taksi-card'>
<div class='card-title'>Finavia API</div>
<span style='color:#ff9999;'>⚠ {lento_virhe}</span><br><br>
<span style='color:#aaa;font-size:17px;'>Avaa manuaalinen näkymä alta:</span><br>
<a href='https://www.finavia.fi/fi/lentoasemat/helsinki-vantaa/lennot?tab=arr'
class='taksi-link' target='_blank'>Finavia – Saapuvat lennot ➔</a>
</div>
“””, unsafe_allow_html=True)
else:
lento_html = “<div class='card-title'>Taktiset poiminnat – saapuvat</div>”
lento_html += “<span style='color:#aaa;font-size:15px;'>Frankfurt arki-iltaisin = paras business-lento | Sähköautoilla tolppaetuoikeus</span><br><br>”
for l in lennot:
tyyppi_css = “pax-good” if l[“wb”] else “pax-ok”
lento_html += (
f”<b>{l[‘time’]}</b>  ·  {l[‘origin’]} “
f”<span style='color:#aaa;'>({l[‘flight’]})</span><br>”
f”  └ <span class='{tyyppi_css}'>{l[‘type’]}</span>”
f” | {l[‘status’]}<br><br>”
)
st.markdown(f”””
<div class='taksi-card'>
{lento_html}
<a href='https://www.finavia.fi/fi/lentoasemat/helsinki-vantaa/lennot?tab=arr'
class='taksi-link' target='_blank'>Finavia Saapuvat ➔</a>
</div>
“””, unsafe_allow_html=True)

# ═══════════════════════════════════════════════

# LOHKO 4: TAPAHTUMAT & KAPASITEETTI

# ═══════════════════════════════════════════════

st.markdown(”<div class='section-header'>📅 TAPAHTUMAT & KAPASITEETTI</div>”, unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([“🎭 Kulttuuri & VIP”, “🏒 Urheilu”, “🏢 Messut & Arenat”, “🎸 Musiikki”])

# ── Kulttuuri & VIP ────────────────────────────

with tab1:
kulttuuri_paikat = [
{
“nimi”: “Helsingin Kaupunginteatteri (HKT)”,
“kap”: “947 hlö”,
“huomio”: “Erinomainen – jopa 50 autoa huonolla kelillä. Normi 20–30.”,
“linkki”: “https://hkt.fi/kalenteri/”,
“linkki_teksti”: “HKT Kalenteri”,
“badge”: “badge-red”,
},
{
“nimi”: “Kansallisooppera ja -baletti”,
“kap”: “~1 700 hlö”,
“huomio”: “Klassikot ja ooppera parhaita. Baletti noin puolet. Normi 1–2 autoa/100 pax.”,
“linkki”: “https://oopperabaletti.fi/ohjelmisto-ja-liput/”,
“linkki_teksti”: “Ooppera Ohjelmisto”,
“badge”: “badge-yellow”,
},
{
“nimi”: “Kansallisteatteri”,
“kap”: “~700 hlö”,
“huomio”: “Aseman vieressä – asiakkaat usein junaan. Pienempi kyytimäärä.”,
“linkki”: “https://kansallisteatteri.fi/esityskalenteri”,
“linkki_teksti”: “Kansallisteatteri Kalenteri”,
“badge”: “badge-blue”,
},
{
“nimi”: “Musiikkitalo”,
“kap”: “1 704 hlö”,
“huomio”: “Päärautatieaseman vieressä – monet kävelijöitä. Kyytipotentiaali pieni.”,
“linkki”: “https://musiikkitalo.fi/tapahtumat/”,
“linkki_teksti”: “Musiikkitalo Tapahtumat”,
“badge”: “badge-blue”,
},
{
“nimi”: “Helsingin Suomalainen Klubi”,
“kap”: “Yksityistilaisuudet”,
“huomio”: “Kansakoulukuja 3, Kamppi. Yritysjohto – pitkät iltakyydit arki-iltaisin.”,
“linkki”: “https://tapahtumat.klubi.fi/tapahtumat/”,
“linkki_teksti”: “Klubi Tapahtumat”,
“badge”: “badge-red”,
},
{
“nimi”: “Svenska Klubben”,
“kap”: “Yksityistilaisuudet”,
“huomio”: “Maurinkatu 6, Kruununhaka. Korkeaprofiilinen – erityisseuranta tapahtumailtaisin.”,
“linkki”: “https://klubben.fi/start/program/”,
“linkki_teksti”: “Svenska Klubben Ohjelma”,
“badge”: “badge-red”,
},
{
“nimi”: “Finlandia-talo”,
“kap”: “Vaihtelee”,
“huomio”: “Kongressit, gaalat. Hyvä yrityspoistumat iltaisin.”,
“linkki”: “https://finlandiatalo.fi/tapahtumakalenteri/”,
“linkki_teksti”: “Finlandia-talo Kalenteri”,
“badge”: “badge-yellow”,
},
{
“nimi”: “Kaapelitehdas”,
“kap”: “Vaihtelee”,
“huomio”: “Kulttuuritapahtumat, messut. Tarkista päättymisaika.”,
“linkki”: “https://kaapelitehdas.fi/tapahtumat”,
“linkki_teksti”: “Kaapelitehdas Ohjelma”,
“badge”: “badge-blue”,
},
]
kulttuuri_html = “”
for p in kulttuuri_paikat:
kulttuuri_html += f”””
<div class='venue-row' style='margin-bottom:14px;'>
<span class='{p["badge"]}'>●</span>
 <span class='venue-name'>{p[‘nimi’]}</span>
<span class='venue-address'> · Kapasiteetti: {p[‘kap’]}</span><br>
    <span style='color:#ccc;font-size:17px;'>{p[‘huomio’]}</span><br>
    <a href=’{p[‘linkki’]}’ class=‘taksi-link’ target=’_blank’
style=‘font-size:16px;’>{p[‘linkki_teksti’]} ➔</a>
</div>”””
st.markdown(f”<div class='taksi-card'>{kulttuuri_html}</div>”, unsafe_allow_html=True)

# ── Urheilu ────────────────────────────────────

with tab2:
urheilu_paikat = [
{
“nimi”: “HIFK – Nordis (jääkiekko)”,
“kap”: “~8 200 hlö”,
“huomio”: “Tärkein seura. Nordi-areena Nordenskiöldinkatu. Poistuma ~2,5 h kiekon putoamisesta.”,
“linkki”: “https://liiga.fi/fi/ohjelma?kausi=2025-2026&sarja=runkosarja&joukkue=hifk&kotiVieras=koti”,
“linkki_teksti”: “HIFK Kotiottelut”,
“badge”: “badge-red”,
},
{
“nimi”: “Kiekko-Espoo – Metro Areena (jääkiekko)”,
“kap”: “~13 000 hlö”,
“huomio”: “Suurin areena. Hyvä potentiaali myös Espoosta Helsinkiin.”,
“linkki”: “https://liiga.fi/fi/ohjelma?kausi=2025-2026&sarja=runkosarja&joukkue=k-espoo&kotiVieras=koti”,
“linkki_teksti”: “Kiekko-Espoo Kotiottelut”,
“badge”: “badge-yellow”,
},
{
“nimi”: “Jokerit – Mestis / Nordis”,
“kap”: “~7 000 hlö”,
“huomio”: “Nordis + Kerava. Tarkista pelipaikka – vaihtelee.”,
“linkki”: “https://jokerit.fi/ottelut”,
“linkki_teksti”: “Jokerit Ottelut”,
“badge”: “badge-yellow”,
},
{
“nimi”: “Olympiastadion (jalkapallo / yleisurheilu)”,
“kap”: “36 000 hlö”,
“huomio”: “HJK kotiottelut, maaottelut. Suuri poistumapiikki päättymisestä.”,
“linkki”: “https://olympiastadion.fi/tapahtumat”,
“linkki_teksti”: “Olympiastadion Tapahtumat”,
“badge”: “badge-red”,
},
{
“nimi”: “Veikkausliiga (jalkapallo)”,
“kap”: “Vaihtelee”,
“huomio”: “HJK tärkein. Normi 1–2 autoa/100 pax. Huono sää nostaa kertoimen.”,
“linkki”: “https://veikkausliiga.com/tilastot/2024/veikkausliiga/ottelut/”,
“linkki_teksti”: “Veikkausliiga Ohjelma”,
“badge”: “badge-blue”,
},
]
urheilu_html = “”
for p in urheilu_paikat:
urheilu_html += f”””
<div class='venue-row' style='margin-bottom:14px;'>
<span class='{p["badge"]}'>●</span>
 <span class='venue-name'>{p[‘nimi’]}</span>
<span class='venue-address'> · {p[‘kap’]}</span><br>
    <span style='color:#ccc;font-size:17px;'>{p[‘huomio’]}</span><br>
    <a href=’{p[‘linkki’]}’ class=‘taksi-link’ target=’_blank’
style=‘font-size:16px;’>{p[‘linkki_teksti’]} ➔</a>
</div>”””
st.markdown(f”<div class='taksi-card'>{urheilu_html}</div>”, unsafe_allow_html=True)

# ── Messut & Arenat ────────────────────────────

with tab3:
messut_paikat = [
{
“nimi”: “Messukeskus”,
“kap”: “Jopa 50 000+”,
“huomio”: “Pasila. Poistumapiikki oviensulkemisaikaan – ei alkamisaikaan!”,
“linkki”: “https://messukeskus.com/kavijalle/tapahtumat/tapahtumakalenteri”,
“linkki_teksti”: “Messukeskus Kalenteri”,
“badge”: “badge-red”,
},
{
“nimi”: “Aalto-yliopisto / Dipoli (Espoo)”,
“kap”: “Kongressit”,
“huomio”: “Kansainväliset kongressit. Business-asiakkaat, pitkät kyydit.”,
“linkki”: “https://www.aalto.fi/fi/palvelut/dipoli”,
“linkki_teksti”: “Dipoli Info”,
“badge”: “badge-yellow”,
},
{
“nimi”: “Kalastajatorppa / Pyöreä Sali”,
“kap”: “~400 hlö”,
“huomio”: “Munkkiniemi. Business-illalliset, kongressit. Pitkät kyydit kantakaupunkiin.”,
“linkki”: “https://kalastajatorppa.fi”,
“linkki_teksti”: “Kalastajatorppa”,
“badge”: “badge-yellow”,
},
{
“nimi”: “Stadissa.fi (yleiskuva)”,
“kap”: “Kaikki tapahtumat”,
“huomio”: “Paras yleissilmäys Helsingin kaikista tapahtumista.”,
“linkki”: “https://stadissa.fi/”,
“linkki_teksti”: “Stadissa.fi”,
“badge”: “badge-blue”,
},
]
messut_html = “”
for p in messut_paikat:
messut_html += f”””
<div class='venue-row' style='margin-bottom:14px;'>
<span class='{p["badge"]}'>●</span>
 <span class='venue-name'>{p[‘nimi’]}</span>
<span class='venue-address'> · {p[‘kap’]}</span><br>
    <span style='color:#ccc;font-size:17px;'>{p[‘huomio’]}</span><br>
    <a href=’{p[‘linkki’]}’ class=‘taksi-link’ target=’_blank’
style=‘font-size:16px;’>{p[‘linkki_teksti’]} ➔</a>
</div>”””
st.markdown(f”<div class='taksi-card'>{messut_html}</div>”, unsafe_allow_html=True)

# ── Musiikki ───────────────────────────────────

with tab4:
musiikki_paikat = [
{
“nimi”: “Tavastia”,
“kap”: “~900 hlö”,
“huomio”: “Rock, metal, pop. Normi 1–2 autoa/100 pax. Huono sää nostaa.”,
“linkki”: “https://tavastiaklubi.fi/fi_FI/ohjelma”,
“linkki_teksti”: “Tavastia Ohjelma”,
“badge”: “badge-yellow”,
},
{
“nimi”: “On the Rocks”,
“kap”: “~600 hlö”,
“huomio”: “Rock, metal. Tarkista täyttöaste ennen siirtymistä.”,
“linkki”: “https://www.ontherocks.fi/ohjelma”,
“linkki_teksti”: “On the Rocks Ohjelma”,
“badge”: “badge-yellow”,
},
{
“nimi”: “Musiikkitalo (klassinen)”,
“kap”: “1 704 hlö”,
“huomio”: “Päärautatieaseman vieressä. Kyytipotentiaali pieni – useimmat junaan.”,
“linkki”: “https://musiikkitalo.fi/tapahtumat/”,
“linkki_teksti”: “Musiikkitalo Tapahtumat”,
“badge”: “badge-blue”,
},
{
“nimi”: “Malmitalo”,
“kap”: “~500 hlö”,
“huomio”: “Malmilla – kauempana. Iskelmä, kansanmusiikki. Hyvä päivävuoroille.”,
“linkki”: “https://malmitalo.fi/tapahtumat”,
“linkki_teksti”: “Malmitalo Tapahtumat”,
“badge”: “badge-blue”,
},
{
“nimi”: “Sellosali (Espoo)”,
“kap”: “~500 hlö”,
“huomio”: “Leppävaara. Klassinen, jazz. Pitkä kyyti kaupunkiin.”,
“linkki”: “https://sellosali.fi/ohjelma/”,
“linkki_teksti”: “Sellosali Ohjelma”,
“badge”: “badge-blue”,
},
]
musiikki_html = “”
for p in musiikki_paikat:
musiikki_html += f”””
<div class='venue-row' style='margin-bottom:14px;'>
<span class='{p["badge"]}'>●</span>
 <span class='venue-name'>{p[‘nimi’]}</span>
<span class='venue-address'> · {p[‘kap’]}</span><br>
    <span style='color:#ccc;font-size:17px;'>{p[‘huomio’]}</span><br>
    <a href=’{p[‘linkki’]}’ class=‘taksi-link’ target=’_blank’
style=‘font-size:16px;’>{p[‘linkki_teksti’]} ➔</a>
</div>”””
st.markdown(f”<div class='taksi-card'>{musiikki_html}</div>”, unsafe_allow_html=True)

# ═══════════════════════════════════════════════

# LOHKO 5: MUISTILISTA & PIKALINKIT

# ═══════════════════════════════════════════════

st.markdown(”<div class='section-header'>📋 OPERATIIVISET PIKALINKIT</div>”, unsafe_allow_html=True)

linkit_html = “””

<div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; font-size:17px;'>
  <div>
    <b style='color:#5bc0de;'>🚆 Liikenne</b><br>
    <a href='https://www.vr.fi/radalla/poikkeustilanteet' class='taksi-link' target='_blank' style='font-size:15px;'>VR Poikkeukset ➔</a><br>
    <a href='https://hsl.fi/aikataulut-ja-reitit/hairiot' class='taksi-link' target='_blank' style='font-size:15px;'>HSL Häiriöt ➔</a><br>
    <a href='https://liikennetilanne.fintraffic.fi/?x=385557.5&y=6672322.0&z=10' class='taksi-link' target='_blank' style='font-size:15px;'>Fintraffic Uusimaa ➔</a>
  </div>
  <div>
    <b style='color:#5bc0de;'>⛅ Sää</b><br>
    <a href='https://www.ilmatieteenlaitos.fi/sade-ja-pilvialueet?area=etela-suomi' class='taksi-link' target='_blank' style='font-size:15px;'>Sadetutka Etelä-Suomi ➔</a><br>
    <a href='https://www.ilmatieteenlaitos.fi/paikallissaa/helsinki' class='taksi-link' target='_blank' style='font-size:15px;'>Helsinki Paikallissää ➔</a>
  </div>
  <div>
    <b style='color:#5bc0de;'>🚢 Meriliikenne</b><br>
    <a href='https://averio.fi/laivat' class='taksi-link' target='_blank' style='font-size:15px;'>Averio Laivat ➔</a><br>
    <a href='https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2' class='taksi-link' target='_blank' style='font-size:15px;'>Port of Helsinki ➔</a>
  </div>
</div>
<hr style='border-color:#333; margin:16px 0;'>
<div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; font-size:17px;'>
  <div>
    <b style='color:#5bc0de;'>✈️ Lentoliikenne</b><br>
    <a href='https://www.finavia.fi/fi/lentoasemat/helsinki-vantaa/lennot?tab=arr' class='taksi-link' target='_blank' style='font-size:15px;'>Finavia Saapuvat ➔</a>
  </div>
  <div>
    <b style='color:#5bc0de;'>💼 Business</b><br>
    <a href='https://tapahtumat.klubi.fi/tapahtumat/' class='taksi-link' target='_blank' style='font-size:15px;'>Suomalainen Klubi ➔</a><br>
    <a href='https://klubben.fi/start/program/' class='taksi-link' target='_blank' style='font-size:15px;'>Svenska Klubben ➔</a><br>
    <a href='https://messukeskus.com/kavijalle/tapahtumat/tapahtumakalenteri' class='taksi-link' target='_blank' style='font-size:15px;'>Messukeskus ➔</a>
  </div>
  <div>
    <b style='color:#5bc0de;'>🎟 VR Korvaukset</b><br>
    <a href='https://www.vr.fi/asiakaspalvelu/korvaukset-ja-hyvitykset' class='taksi-link' target='_blank' style='font-size:15px;'>VR Myöhästymiskorvaus ➔</a><br>
    <span style='color:#aaa;font-size:14px;'>Oikeutus: &gt;60 min myöhässä + taksilupa konduktööriltä</span>
  </div>
</div>
"""
st.markdown(f"<div class='taksi-card'>{linkit_html}</div>", unsafe_allow_html=True)

# Alatunniste

st.markdown(
“<div style='color:#555; font-size:14px; text-align:center; margin-top:20px;'>”
“TH Taktinen Tutka · Päivittyy 60 s välein · Digitraffic (MIT) · Port of Helsinki · Averio · Finavia”
“</div>”,
unsafe_allow_html=True,
)
