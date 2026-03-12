import streamlit as st
import streamlit.components.v1 as components
import datetime
import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
import json
import re

st.set_page_config(page_title="TH Taktinen Tutka", page_icon="🚕", layout="wide")

FINAVIA_API_KEY = "838062ef175f47708d566bbf5a38a710"

components.html("""
<script>
setTimeout(function(){ window.parent.location.reload(); }, 60000);
</script>
""", height=0, width=0)

if "valittu_asema" not in st.session_state:
    st.session_state.valittu_asema = "Helsinki"

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
.main { background-color: #121212; }
.header-container {
    display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 20px;
}
.app-title { font-size: 32px; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
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
.venue-name { color: #ffffff; font-weight: bold; }
.venue-address { color: #aaaaaa; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# ── AVERIO ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_averio_ships():
    url = "https://averio.fi/laivat"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ),
        "Accept-Language": "fi-FI,fi;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    laivat = []
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for taulu in soup.find_all("table"):
            for rivi in taulu.find_all("tr"):
                solut = [td.get_text(strip=True) for td in rivi.find_all(["td", "th"])]
                if len(solut) < 3:
                    continue
                rivi_teksti = " ".join(solut).lower()
                if any(h in rivi_teksti for h in ["alus", "laiva", "ship", "vessel"]):
                    continue
                pax = None
                for solu in solut:
                    puhdas = re.sub(r"[^\d]", "", solu)
                    if puhdas and 50 <= int(puhdas) <= 9999:
                        pax = int(puhdas)
                        break
                nimi_kandidaatit = [s for s in solut if re.search(r"[A-Za-zÀ-ÿ]{3,}", s)]
                if not nimi_kandidaatit:
                    continue
                nimi = max(nimi_kandidaatit, key=len)
                laivat.append({
                    "ship": nimi,
                    "terminal": _tunnista_terminaali(rivi_teksti),
                    "time": _etsi_aika(solut),
                    "pax": pax,
                })
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
                })
        return laivat[:5] if laivat else [{"ship": "Averio: HTML-rakenne muuttunut", "terminal": "Tarkista manuaalisesti", "time": "-", "pax": None}]
    except Exception as e:
        return [{"ship": f"Averio-virhe: {e}", "terminal": "-", "time": "-", "pax": None}]

def _tunnista_terminaali(teksti):
    if "t2" in teksti or "lansisatama" in teksti or "länsisatama" in teksti:
        return "Länsisatama T2"
    if "t1" in teksti or "olympia" in teksti:
        return "Olympia T1"
    if "katajanokka" in teksti:
        return "Katajanokka"
    if "vuosaari" in teksti:
        return "Vuosaari (rahti)"
    return "Tarkista"

def _etsi_aika(osat):
    for osa in osat:
        m = re.search(r"\b([0-2]?\d:[0-5]\d)\b", str(osa))
        if m:
            return m.group(1)
    return "-"

def _pax_arvio(pax):
    if pax is None:
        return "Ei tietoa", "pax-ok"
    autoa = round(pax * 0.025)
    if pax >= 400:
        return f"🔥 {pax} matkustajaa (~{autoa} autoa, ERINOMAINEN)", "pax-good"
    if pax >= 200:
        return f"✅ {pax} matkustajaa (~{autoa} autoa)", "pax-ok"
    return f"⬇️ {pax} matkustajaa (~{autoa} autoa, matala)", "pax-ok"

# ── HELSINGIN SATAMA ─────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_port_schedule():
    url = "https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        lista = []
        for rivi in soup.find_all("tr"):
            solut = rivi.find_all("td")
            if len(solut) >= 4:
                aika = solut[0].get_text(strip=True)
                laiva = solut[1].get_text(strip=True)
                terminaali = solut[3].get_text(strip=True) if len(solut) > 3 else "?"
                if aika and laiva and re.match(r"\d{1,2}:\d{2}", aika):
                    lista.append({"time": aika, "ship": laiva, "terminal": terminaali})
        return lista[:6] if lista else []
    except Exception as e:
        return [{"time": "-", "ship": f"Virhe: {e}", "terminal": "-"}]

# ── JUNAT ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=50)
def get_trains(asema_nimi):
    nykyhetki = datetime.datetime.now(ZoneInfo("Europe/Helsinki"))
    koodit = {"Helsinki": "HKI", "Pasila": "PSL", "Tikkurila": "TKL"}
    koodi = koodit.get(asema_nimi, "HKI")
    url = (
        f"https://rata.digitraffic.fi/api/v1/live-trains/station/{koodi}"
        "?arrived_trains=0&arriving_trains=25&train_categories=Long-distance"
    )
    kaupungit = {
        "ROV": "Rovaniemi", "OUL": "Oulu", "TPE": "Tampere", "TKU": "Turku",
        "KJA": "Kajaani", "JNS": "Joensuu", "YV": "Ylivieska", "VAA": "Vaasa",
        "JY": "Jyvaskyla", "KUO": "Kuopio", "POR": "Pori", "SJK": "Seinajoki",
        "LVT": "Lappeenranta", "KOK": "Kokkola", "KEM": "Kemi", "KTI": "Kittila",
    }
    tulos = []
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for juna in data:
            if juna.get("cancelled"):
                continue
            tyyppi = juna.get("trainType", "")
            numero = juna.get("trainNumber", "")
            nimi = f"{tyyppi} {numero}"
            lahto = juna["timeTableRows"][0]["stationShortCode"]
            if lahto in ("HKI", "PSL", "TKL"):
                continue
            lahto_kaupunki = kaupungit.get(lahto, lahto)
            aika_obj = aika_str = None
            viive = 0
            for rivi in juna["timeTableRows"]:
                if rivi["stationShortCode"] == koodi and rivi["type"] == "ARRIVAL":
                    raaka = rivi.get("liveEstimateTime") or rivi.get("scheduledTime", "")
                    try:
                        aika_obj = datetime.datetime.strptime(raaka[:16], "%Y-%m-%dT%H:%M")
                        aika_obj = aika_obj.replace(tzinfo=datetime.timezone.utc).astimezone(ZoneInfo("Europe/Helsinki"))
                        if aika_obj < nykyhetki - datetime.timedelta(minutes=3):
                            aika_obj = None
                        else:
                            aika_str = aika_obj.strftime("%H:%M")
                    except Exception:
                        pass
                    viive = rivi.get("differenceInMinutes", 0)
                    break
            if aika_str and aika_obj:
                tulos.append({"train": nimi, "origin": lahto_kaupunki, "time": aika_str, "dt": aika_obj, "delay": viive if viive > 0 else 0})
        tulos.sort(key=lambda k: k["dt"])
        return tulos[:6]
    except Exception as e:
        return [{"train": "API-virhe", "origin": str(e)[:30], "time": "-", "dt": None, "delay": 0}]

# ── LENNOT ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_flights():
    laajarunko = {"359", "350", "333", "330", "340", "788", "789", "777", "77W", "388", "744", "74H"}
    endpoints = [
        (f"https://apigw.finavia.fi/flights/public/v0/flights/arr/HEL?subscription-key={FINAVIA_API_KEY}", {}),
        ("https://apigw.finavia.fi/flights/public/v0/flights/arr/HEL", {"Ocp-Apim-Subscription-Key": FINAVIA_API_KEY}),
    ]
    for url, extra_headers in endpoints:
        hdrs = {"User-Agent": "Mozilla/5.0 (compatible; TH-Tutka/2.0)", "Accept": "application/json", "Cache-Control": "no-cache"}
        hdrs.update(extra_headers)
        try:
            resp = requests.get(url, headers=hdrs, timeout=10)
            if resp.status_code in (401, 403):
                continue
            resp.raise_for_status()
            data = resp.json()
            saapuvat = []
            
            if isinstance(data, list):
                saapuvat = data
            elif isinstance(data, dict):
                for avain in ("arr", "flights", "body"):
                    k = data.get(avain)
                    if isinstance(k, list):
                        saapuvat = k
                        break
                
                # Jos dataa ei vielä löytynyt listana, kokeillaan etsiä rakenteen sisältä dict:nä
                if not saapuvat:
                    k = data.get("body", {})
                    if isinstance(k, dict):
                        for ala in ("arr", "flight"):
                            if isinstance(k.get(ala), list):
                                saapuvat = k[ala]
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
                tyyppi = f"Laajarunko (✈ {actype})" if wb else f"Kapearunko ({actype})"
                if wb and "laskeutunut" not in status.lower() and "landed" not in status.lower():
                    status = f"🔥 Odottaa massapurkua - {status}"
                elif "delay" in status.lower() or "myohassa" in status.lower():
                    status = f"🔴 {status}"
                tulos.append({"flight": nro, "origin": kohde, "time": aika, "type": tyyppi, "wb": wb, "status": status})
            tulos.sort(key=lambda x: (not x["wb"], x["time"]))
            return tulos[:8], None
        except Exception:
            continue
    return [], "Finavia API ei vastannut. Avain saattaa olla vanhentunut."

# ── APUFUNKTIOT ──────────────────────────────────────────────────────────────

def viive_badge(minuutit):
    if minuutit <= 0:
        return "<span class='badge-green'>Aikataulussa</span>"
    if minuutit < 15:
        return f"<span class='badge-yellow'>+{minuutit} min</span>"
    if minuutit < 60:
        return f"<span class='badge-red'>⚠ +{minuutit} min</span>"
    return f"<span class='badge-red'>🚨 +{minuutit} min - VR-korvaus mahdollinen!</span>"

# ═══════════════════════════════════════════════════════════════════════════════
# UI
# ═══════════════════════════════════════════════════════════════════════════════

suomen_aika = datetime.datetime.now(ZoneInfo("Europe/Helsinki"))
klo  = suomen_aika.strftime("%H:%M")
paiva = suomen_aika.strftime("%a %d.%m.%Y").capitalize()

st.markdown(f"""
<div class='header-container'>
  <div>
    <div class='app-title'>🚕 TH Taktinen Tutka</div>
    <div class='time-display'>{klo} <span style='font-size:16px;color:#888;'>Helsinki - {paiva}</span></div>
  </div>
  <div style='text-align:right;'>
    <a href='https://www.ilmatieteenlaitos.fi/sade-ja-pilvialueet?area=etela-suomi' class='taksi-link' target='_blank' style='font-size:22px;'>🌧 Sadetutka &#x2192;</a><br>
    <a href='https://liikennetilanne.fintraffic.fi/?x=385557.5&y=6672322.0&z=10' class='taksi-link' target='_blank' style='font-size:18px;'>🗺 Liikennetilanne &#x2192;</a><br>
    <a href='https://hsl.fi/aikataulut-ja-reitit/hairiot' class='taksi-link' target='_blank' style='font-size:18px;'>🚇 HSL-häiriöt &#x2192;</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── LOHKO 1: JUNAT ───────────────────────────────────────────────────────────

st.markdown("<div class='section-header'>🚆 SAAPUVAT KAUKOJUNAT</div>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
if c1.button("Helsinki (HKI)", use_container_width=True):
    st.session_state.valittu_asema = "Helsinki"
if c2.button("Pasila (PSL)", use_container_width=True):
    st.session_state.valittu_asema = "Pasila"
if c3.button("Tikkurila (TKL)", use_container_width=True):
    st.session_state.valittu_asema = "Tikkurila"

valittu = st.session_state.valittu_asema
junat = get_trains(valittu)
vr_linkit = {
    "Helsinki":  "https://www.vr.fi/radalla?station=HKI&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D&follow=true",
    "Pasila":    "https://www.vr.fi/radalla?station=PSL&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D",
    "Tikkurila": "https://www.vr.fi/radalla?station=TKL&direction=ARRIVAL&stationFilters=%7B%22trainCategory%22%3A%22Long-distance%22%7D&follow=true",
}
juna_html = f"<span style='color:#aaa;font-size:17px;'>Asema: <b>{valittu}</b> - vain kaukoliikenne</span><br><br>"
if junat and junat[0]["train"] != "API-virhe":
    for j in junat:
        tahti = " ⭐" if j["origin"] in ("Rovaniemi", "Kittila", "Oulu", "Kuopio") else ""
        juna_html += (
            f"<b>{j['time']}</b>  ·  {j['train']} "
            f"<span style='color:#aaa;'>(lähtö: {j['origin']}{tahti})</span><br>"
            f"  └ {viive_badge(j['delay'])}<br><br>"
        )
    if any(j["delay"] >= 60 for j in junat):
        juna_html += "<br><span class='badge-red'>🚨 Yli 60 min myöhässä - tarkista VR-korvauskäytäntö!</span><br>"
else:
    juna_html += "Ei saapuvia kaukojunia lähiaikoina."

st.markdown(f"""
<div class='taksi-card'>
  {juna_html}
  <a href='{vr_linkit[valittu]}' class='taksi-link' target='_blank'>VR Live ({valittu}) &#x2192;</a>
  &nbsp;&nbsp;
  <a href='https://www.vr.fi/radalla/poikkeustilanteet' class='taksi-link' target='_blank' style='color:#ff9999;'>⚠ VR Poikkeukset &#x2192;</a>
</div>
""", unsafe_allow_html=True)

# ── LOHKO 2: LAIVAT ──────────────────────────────────────────────────────────

st.markdown("<div class='section-header'>🚢 MATKUSTAJALAIVAT</div>", unsafe_allow_html=True)
col_a, col_b = st.columns(2)

with col_a:
    averio_laivat = get_averio_ships()
    averio_html = "<div class='card-title'>Averio - Matkustajamäärät</div>"
    averio_html += "<span style='color:#aaa;font-size:15px;'>⚠ klo 00:30 MS Finlandia → <b>Länsisatama T2</b>, ei Vuosaari</span><br><br>"
    for laiva in averio_laivat:
        arvio_teksti, arvio_css = _pax_arvio(laiva["pax"])
        averio_html += (
            f"<b>{laiva['time']}</b>  ·  {laiva['ship']}<br>"
            f"  └ Terminaali: {laiva['terminal']}<br>"
            f"  └ <span class='{arvio_css}'>{arvio_teksti}</span><br><br>"
        )
    st.markdown(f"<div class='taksi-card'>{averio_html}<a href='https://averio.fi/laivat' class='taksi-link' target='_blank'>Avaa Averio →</a></div>", unsafe_allow_html=True)

with col_b:
    port_laivat = get_port_schedule()
    port_html = "<div class='card-title'>Helsingin Satama - Aikataulu</div>"
    if port_laivat:
        for laiva in port_laivat:
            port_html += f"<b>{laiva['time']}</b>  ·  {laiva['ship']}<br>  └ {laiva['terminal']}<br><br>"
    else:
        port_html += "Ei dataa - sivu vaatii JavaScript-renderöinnin.<br>"
    st.markdown(f"""
    <div class='taksi-card'>
    {port_html}
    <a href='https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2'
    class='taksi-link' target='_blank'>Helsingin Satama →</a>
    </div>
    """, unsafe_allow_html=True)

# ── LOHKO 3: LENNOT ──────────────────────────────────────────────────────────

st.markdown("<div class='section-header'>✈️ LENTOKENTTÄ (Helsinki-Vantaa)</div>", unsafe_allow_html=True)
lennot, lento_virhe = get_flights()

if lento_virhe:
    st.markdown(f"""
    <div class='taksi-card'>
    <div class='card-title'>Finavia API</div>
    <span style='color:#ff9999;'>⚠ {lento_virhe}</span><br><br>
    <a href='https://www.finavia.fi/fi/lentoasemat/helsinki-vantaa/lennot?tab=arr' class='taksi-link' target='_blank'>Finavia - Saapuvat lennot →</a>
    </div>
    """, unsafe_allow_html=True)
else:
    lento_html = "<div class='card-title'>Taktiset poiminnat - saapuvat</div>"
    lento_html += "<span style='color:#aaa;font-size:15px;'>Frankfurt arki-iltaisin = paras business-lento | Sähköautoilla tolppaetuoikeus</span><br><br>"
    for lento in lennot:
        tyyppi_css = "pax-good" if lento["wb"] else "pax-ok"
        lento_html += (
            f"<b>{lento['time']}</b>  ·  {lento['origin']} "
            f"<span style='color:#aaa;'>({lento['flight']})</span><br>"
            f"  └ <span class='{tyyppi_css}'>{lento['type']}</span>"
            f" | {lento['status']}<br><br>"
        )
    st.markdown(f"""
    <div class='taksi-card'>
    {lento_html}
    <a href='https://www.finavia.fi/fi/lentoasemat/helsinki-vantaa/lennot?tab=arr' class='taksi-link' target='_blank'>Finavia Saapuvat →</a>
    </div>
    """, unsafe_allow_html=True)

# ── LOHKO 4: TAPAHTUMAT ───────────────────────────────────────────────────────

st.markdown("<div class='section-header'>📅 TAPAHTUMAT & KAPASITEETTI</div>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["Kulttuuri & VIP", "Urheilu", "Messut & Arenat", "Musiikki"])

def venue_html(paikat):
    html = ""
    for p in paikat:
        html += (
            f"<div style='margin-bottom:14px;'>"
            f"<span class='{p['badge']}'>●</span> "
            f"<span class='venue-name'>{p['nimi']}</span>"
            f"<span class='venue-address'> - {p['kap']}</span><br>"
            f"<span style='color:#ccc;font-size:17px;margin-left:18px;'>{p['huomio']}</span><br>"
            f"<a href='{p['linkki']}' class='taksi-link' target='_blank' style='font-size:16px;margin-left:18px;'>{p['teksti']} →</a>"
            f"</div>"
        )
    return html

with tab1:
    paikat = [
        {"nimi": "Helsingin Kaupunginteatteri (HKT)", "kap": "947 hlö", "huomio": "Erinomainen - jopa 50 autoa huonolla kelillä. Normi 20-30.", "linkki": "https://hkt.fi/kalenteri/", "teksti": "HKT Kalenteri", "badge": "badge-red"},
        {"nimi": "Kansallisooppera ja -baletti", "kap": "~1 700 hlö", "huomio": "Klassikot ja ooppera parhaita. Baletti noin puolet. 1-2 autoa/100 pax.", "linkki": "https://oopperabaletti.fi/ohjelmisto-ja-liput/", "teksti": "Ooppera Ohjelmisto", "badge": "badge-yellow"},
        {"nimi": "Kansallisteatteri", "kap": "~700 hlö", "huomio": "Aseman vieressä - asiakkaat usein junaan. Pienempi kyytimäärä.", "linkki": "https://kansallisteatteri.fi/esityskalenteri", "teksti": "Kansallisteatteri Kalenteri", "badge": "badge-blue"},
        {"nimi": "Musiikkitalo", "kap": "1 704 hlö", "huomio": "Päärautatieaseman vieressä - monet kävelijöitä. Kyytipotentiaali pieni.", "linkki": "https://musiikkitalo.fi/tapahtumat/", "teksti": "Musiikkitalo Tapahtumat", "badge": "badge-blue"},
        {"nimi": "Helsingin Suomalainen Klubi", "kap": "Yksityistilaisuudet", "huomio": "Kansakoulukuja 3, Kamppi. Yritysjohto - pitkät iltakyydit arki-iltaisin.", "linkki": "https://tapahtumat.klubi.fi/tapahtumat/", "teksti": "Klubi Tapahtumat", "badge": "badge-red"},
        {"nimi": "Svenska Klubben", "kap": "Yksityistilaisuudet", "huomio": "Maurinkatu 6, Kruununhaka. Korkeaprofiilinen - erityisseuranta tapahtumailtaisin.", "linkki": "https://klubben.fi/start/program/", "teksti": "Svenska Klubben Ohjelma", "badge": "badge-red"},
        {"nimi": "Finlandia-talo", "kap": "Vaihtelee", "huomio": "Kongressit, gaalat. Hyvä yrityspoistumat iltaisin.", "linkki": "https://finlandiatalo.fi/tapahtumakalenteri/", "teksti": "Finlandia-talo Kalenteri", "badge": "badge-yellow"},
        {"nimi": "Kaapelitehdas", "kap": "Vaihtelee", "huomio": "Kulttuuritapahtumat, messut. Tarkista päättymisaika.", "linkki": "https://kaapelitehdas.fi/tapahtumat", "teksti": "Kaapelitehdas Ohjelma", "badge": "badge-blue"},
    ]
    st.markdown(f"<div class='taksi-card'>{venue_html(paikat)}</div>", unsafe_allow_html=True)

with tab2:
    paikat = [
        {"nimi": "HIFK - Nordis (jääkiekko)", "kap": "~8 200 hlö", "huomio": "Tärkein seura. Poistuma ~2,5 h kiekon putoamisesta.", "linkki": "https://liiga.fi/fi/ohjelma?kausi=2025-2026&sarja=runkosarja&joukkue=hifk&kotiVieras=koti", "teksti": "HIFK Kotiottelut", "badge": "badge-red"},
        {"nimi": "Kiekko-Espoo - Metro Areena", "kap": "~13 000 hlö", "huomio": "Suurin areena. Hyvä potentiaali myös Espoosta Helsinkiin.", "linkki": "https://liiga.fi/fi/ohjelma?kausi=2025-2026&sarja=runkosarja&joukkue=k-espoo&kotiVieras=koti", "teksti": "Kiekko-Espoo Kotiottelut", "badge": "badge-yellow"},
        {"nimi": "Jokerit - Mestis / Nordis", "kap": "~7 000 hlö", "huomio": "Nordis + Kerava. Tarkista pelipaikka - vaihtelee.", "linkki": "https://jokerit.fi/ottelut", "teksti": "Jokerit Ottelut", "badge": "badge-yellow"},
        {"nimi": "Olympiastadion (jalkapallo)", "kap": "36 000 hlö", "huomio": "HJK kotiottelut, maaottelut. Suuri poistumapiikki.", "linkki": "https://olympiastadion.fi/tapahtumat", "teksti": "Olympiastadion Tapahtumat", "badge": "badge-red"},
        {"nimi": "Veikkausliiga (jalkapallo)", "kap": "Vaihtelee", "huomio": "HJK tärkein. 1-2 autoa/100 pax. Huono sää nostaa kertoimen.", "linkki": "https://veikkausliiga.com/tilastot/2024/veikkausliiga/ottelut/", "teksti": "Veikkausliiga Ohjelma", "badge": "badge-blue"},
    ]
    st.markdown(f"<div class='taksi-card'>{venue_html(paikat)}</div>", unsafe_allow_html=True)

with tab3:
    paikat = [
        {"nimi": "Messukeskus", "kap": "Jopa 50 000+", "huomio": "Pasila. Poistumapiikki oviensulkemisaikaan - ei alkamisaikaan!", "linkki": "https://messukeskus.com/kavijalle/tapahtumat/tapahtumakalenteri", "teksti": "Messukeskus Kalenteri", "badge": "badge-red"},
        {"nimi": "Aalto-yliopisto / Dipoli", "kap": "Kongressit", "huomio": "Kansainväliset kongressit. Business-asiakkaat, pitkät kyydit.", "linkki": "https://www.aalto.fi/fi/palvelut/dipoli", "teksti": "Dipoli Info", "badge": "badge-yellow"},
        {"nimi": "Kalastajatorppa / Pyöreä Sali", "kap": "~400 hlö", "huomio": "Munkkiniemi. Business-illalliset. Pitkät kyydit kantakaupunkiin.", "linkki": "https://kalastajatorppa.fi", "teksti": "Kalastajatorppa", "badge": "badge-yellow"},
        {"nimi": "Stadissa.fi (yleiskuva)", "kap": "Kaikki tapahtumat", "huomio": "Paras yleissilmäys Helsingin kaikista tapahtumista.", "linkki": "https://stadissa.fi/", "teksti": "Stadissa.fi", "badge": "badge-blue"},
    ]
    st.markdown(f"<div class='taksi-card'>{venue_html(paikat)}</div>", unsafe_allow_html=True)

with tab4:
    paikat = [
        {"nimi": "Tavastia", "kap": "~900 hlö", "huomio": "Rock, metal, pop. 1-2 autoa/100 pax. Huono sää nostaa.", "linkki": "https://tavastiaklubi.fi/fi_FI/ohjelma", "teksti": "Tavastia Ohjelma", "badge": "badge-yellow"},
        {"nimi": "On the Rocks", "kap": "~600 hlö", "huomio": "Rock, metal. Tarkista täyttöaste ennen siirtymistä.", "linkki": "https://www.ontherocks.fi/ohjelma", "teksti": "On the Rocks Ohjelma", "badge": "badge-yellow"},
        {"nimi": "Malmitalo", "kap": "~500 hlö", "huomio": "Malmilla - kauempana. Iskelmä, kansanmusiikki. Hyvä päivävuoroille.", "linkki": "https://malmitalo.fi/tapahtumat", "teksti": "Malmitalo Tapahtumat", "badge": "badge-blue"},
        {"nimi": "Sellosali (Espoo)", "kap": "~500 hlö", "huomio": "Leppävaara. Klassinen, jazz. Pitkä kyyti kaupunkiin.", "linkki": "https://sellosali.fi/ohjelma/", "teksti": "Sellosali Ohjelma", "badge": "badge-blue"},
    ]
    st.markdown(f"<div class='taksi-card'>{venue_html(paikat)}</div>", unsafe_allow_html=True)

# ── PIKALINKIT ────────────────────────────────────────────────────────────────

st.markdown("<div class='section-header'>📋 OPERATIIVISET PIKALINKIT</div>", unsafe_allow_html=True)
linkit_html = """
<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:17px;'>
  <div>
    <b style='color:#5bc0de;'>Liikenne</b><br>
    <a href='https://www.vr.fi/radalla/poikkeustilanteet' class='taksi-link' target='_blank' style='font-size:15px;'>VR Poikkeukset &#x2192;</a><br>
    <a href='https://hsl.fi/aikataulut-ja-reitit/hairiot' class='taksi-link' target='_blank' style='font-size:15px;'>HSL Häiriöt &#x2192;</a><br>
    <a href='https://liikennetilanne.fintraffic.fi/?x=385557.5&y=6672322.0&z=10' class='taksi-link' target='_blank' style='font-size:15px;'>Fintraffic Uusimaa &#x2192;</a>
  </div>
  <div>
    <b style='color:#5bc0de;'>Sää</b><br>
    <a href='https://www.ilmatieteenlaitos.fi/sade-ja-pilvialueet?area=etela-suomi' class='taksi-link' target='_blank' style='font-size:15px;'>Sadetutka Etelä-Suomi &#x2192;</a><br>
    <a href='https://www.ilmatieteenlaitos.fi/paikallissaa/helsinki' class='taksi-link' target='_blank' style='font-size:15px;'>Helsinki Paikallissää &#x2192;</a>
  </div>
  <div>
    <b style='color:#5bc0de;'>Meriliikenne</b><br>
    <a href='https://averio.fi/laivat' class='taksi-link' target='_blank' style='font-size:15px;'>Averio Laivat &#x2192;</a><br>
    <a href='https://www.portofhelsinki.fi/matkustajille/matkustajatietoa/lahtevat-ja-saapuvat-matkustajalaivat/#tabs-2' class='taksi-link' target='_blank' style='font-size:15px;'>Port of Helsinki &#x2192;</a>
  </div>
</div>
<hr style='border-color:#333;margin:16px 0;'>
<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:17px;'>
  <div>
    <b style='color:#5bc0de;'>Lentoliikenne</b><br>
    <a href='https://www.finavia.fi/fi/lentoasemat/helsinki-vantaa/lennot?tab=arr' class='taksi-link' target='_blank' style='font-size:15px;'>Finavia Saapuvat &#x2192;</a>
  </div>
  <div>
    <b style='color:#5bc0de;'>Business</b><br>
    <a href='https://tapahtumat.klubi.fi/tapahtumat/' class='taksi-link' target='_blank' style='font-size:15px;'>Suomalainen Klubi &#x2192;</a><br>
    <a href='https://klubben.fi/start/program/' class='taksi-link' target='_blank' style='font-size:15px;'>Svenska Klubben &#x2192;</a><br>
    <a href='https://messukeskus.com/kavijalle/tapahtumat/tapahtumakalenteri' class='taksi-link' target='_blank' style='font-size:15px;'>Messukeskus &#x2192;</a>
  </div>
  <div>
    <b style='color:#5bc0de;'>VR Korvaukset</b><br>
    <a href='https://www.vr.fi/asiakaspalvelu/korvaukset-ja-hyvitykset' class='taksi-link' target='_blank' style='font-size:15px;'>VR Myöhästymiskorvaus &#x2192;</a><br>
    <span style='color:#aaa;font-size:14px;'>Oikeutus: &gt;60 min myöhässä + taksilupa konduktööriltä</span>
  </div>
</div>
"""
st.markdown(f"<div class='taksi-card'>{linkit_html}</div>", unsafe_allow_html=True)
st.markdown("<div style='color:#555;font-size:14px;text-align:center;margin-top:20px;'>TH Taktinen Tutka - Päivittyy 60 s välein - Digitraffic (MIT) - Port of Helsinki - Averio - Finavia</div>", unsafe_allow_html=True)
