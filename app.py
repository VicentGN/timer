
from datetime import date, datetime, time, timezone
import astropy.units as u
from astropy.time import Time
from astropy.utils.iers import IERS_Auto, IERSRangeError, conf as iers_conf
import streamlit as st

# --- Configuración y Optimización de IERS ---
@st.cache_resource(show_spinner="Cargando tablas de orientación terrestre (IERS)...")
def inicializar_iers():
    """Descarga/carga una única vez la tabla IERS en caché y bloquea llamadas remotas sucesivas."""
    iers_conf.auto_download = True
    # Forzar la carga de la tabla en memoria
    tabla = IERS_Auto.open()
    # Desactivar descargas automáticas para re-runs posteriores
    iers_conf.auto_download = False
    return tabla

# Inicializar recurso único
tabla_iers = inicializar_iers()

st.set_page_config(page_title="Reloj Multiescala", page_icon="⏱️", layout="wide")
st.title("⏱️ Monitor Multiescala de Tiempo")

# --- Selector de Entrada ---
modo = st.radio("Modo de consulta:", ["Instante actual", "Fecha y hora específica"], horizontal=True)

if modo == "Instante actual":
    t_utc = Time.now()
    if st.button("🔄 Actualizar instante"):
        st.rerun()
else:
    c_fecha, c_hora, c_frac = st.columns([2, 2, 1])
    with c_fecha:
        d = st.date_input("Fecha:", value=date.today())
    with c_hora:
        h = st.time_input("Hora (UTC):", value=time(12, 0, 0), step=1)
    with c_frac:
        frac_s = st.number_input("Fracción (s):", min_value=0.0, max_value=0.999999, value=0.0, step=0.001, format="%.6f")

    dt_base = datetime.combine(d, h).replace(tzinfo=timezone.utc)
    t_utc = Time(dt_base) + frac_s * u.second

# --- Función de cálculo con caché para fechas fijas ---
@st.cache_data
def computar_escalas(iso_timestamp: str):
    """Calcula todas las transformaciones temporales reutilizando memoria."""
    t = Time(iso_timestamp, scale='utc')
    
    t_tai = t.tai
    t_gps = t.gps
    t_tt  = t.tt
    t_tcg = t.tcg
    t_tdb = t.tdb

    iers_ok = True
    try:
        dut1 = float(t.delta_ut1_utc)
        ut1_txt = t.ut1.iso
        gmst_txt = t.sidereal_time('mean', 'greenwich', model='IAU_2006').to_string(sep=':', precision=3, pad=True)
        gast_txt = t.sidereal_time('apparent', 'greenwich', model='IAU_2006').to_string(sep=':', precision=3, pad=True)
    except (IERSRangeError, ValueError, Exception):
        iers_ok = False
        dut1 = None
        ut1_txt = "Fuera de cobertura IERS"
        gmst_txt = "No disponible"
        gast_txt = "No disponible"

    return {
        "utc": t.iso,
        "tai": t_tai.iso,
        "gps": t_gps.iso,
        "tt": t_tt.iso,
        "tcg": t_tcg.iso,
        "tdb": t_tdb.iso,
        "ut1": ut1_txt,
        "gmst": gmst_txt,
        "gast": gast_txt,
        "dut1": dut1,
        "iers_disponible": iers_ok,
        "diff_tai_utc": (t_tai - t).to('s').value,
        "diff_tai_gps": (t_tai - t_gps).to('s').value,
        "diff_tt_tai": (t_tt - t_tai).to('s').value,
        "diff_tcg_tt": (t_tcg - t_tt).to('s').value,
    }

# Si es modo histórico/fijo, se aprovecha el caché; en tiempo real computa directo
datos = computar_escalas(t_utc.iso)

# --- Renderizado UI ---
st.markdown("### 1. Escalas Civiles, Atómicas y Navegación")
col1, col2, col3 = st.columns(3)
col1.info(f"**UTC (Coordinado)**\n\n`{datos['utc']}`")
col2.success(f"**TAI (Atómico Internacional)**\n\n`{datos['tai']}`")
col3.warning(f"**GPS (Sistema Satelital)**\n\n`{datos['gps']}`")

st.markdown("### 2. Rotación Terrestre y Orientación Celeste (Observadas)")
col4, col5, col6 = st.columns(3)
col4.error(f"**UT1 (Ángulo de Rotación Terrestre)**\n\n`{datos['ut1']}`")
col5.metric(label="GMST (Sidéreo Medio Greenwich)", value=datos['gmst'])
col6.metric(label="GAST (Sidéreo Aparente Greenwich)", value=datos['gast'])

st.markdown("### 3. Escalas Dinámicas y Relativistas")
col7, col8, col9 = st.columns(3)
col7.info(f"**TT (Tiempo Terrestre - Geoide)**\n\n`{datos['tt']}`")
col8.info(f"**TCG (Coordenada Geocéntrica)**\n\n`{datos['tcg']}`")
col9.info(f"**TDB (Dinámico Baricéntrico, Geocentro)**\n\n`{datos['tdb']}`")

st.markdown("---")
st.markdown("### Transformaciones y Desfases")
k1, k2, k3, k4 = st.columns(4)
k1.metric("TAI − UTC", f"{datos['diff_tai_utc']:.0f} s", help="Segundos intercalares acumulados.")
k2.metric("TAI − GPS", f"{datos['diff_tai_gps']:.1f} s", help="Offset canónico fijo (19 s).")
k3.metric("TT − TAI", f"{datos['diff_tt_tai']:.3f} s", help="Constante IAU: 32.184 s.")
k4.metric("TCG − TT", f"{datos['diff_tcg_tt']:.6f} s", help="Efecto relativista acumulado.")

if datos['iers_disponible']:
    st.caption(f"**DUT1 ($UT1 - UTC$):** `{datos['dut1']:+.6f} s` (IERS Bulletin A/B en memoria local).")
else:
    st.caption("⚠️ **Aviso:** Fecha fuera del rango predictivo u observacional de las tablas IERS.")
