import streamlit as st
from astropy.time import Time
from astropy.utils import iers
from datetime import date, time

st.set_page_config(page_title="Reloj Multiescala", page_icon="⏱️", layout="centered")

st.title("⏱️ Monitor Multiescala de Tiempo")

# Carga de tablas de rotación terrestre IERS
iers.IERS_Auto.open()

# Selector de modo
modo = st.radio("Modo de consulta:", ["Instante actual", "Fecha y hora específica"], horizontal=True)

if modo == "Instante actual":
    t_utc = Time.now()
    if st.button("🔄 Actualizar ahora"):
        st.rerun()
else:
    c_fecha, c_hora = st.columns(2)
    with c_fecha:
        d = st.date_input("Fecha:", value=date.today())
    with c_hora:
        h = st.time_input("Hora (UTC):", value=time(12, 0, 0))
    dt_str = f"{d.isoformat()} {h.strftime('%H:%M:%S')}"
    t_utc = Time(dt_str, format='iso', scale='utc')

# 1. Escalas atómicas y uniformes
t_tai = t_utc.replicate(scale='tai')
t_gps = t_utc.replicate(scale='gps')
t_tt  = t_utc.replicate(scale='tt')  # TT = TAI + 32.184 s
t_te  = t_tt       # Ephemeris Time (ET/TE) continuado formalmente por TT

# 2. Escalas rotacionales y solares
t_ut1 = t_utc.replicate(scale='ut1')  # UT1 con corrección del IERS
# UT (de forma genérica en astronomía civil equivale a UTC con desglose entero)
t_ut  = t_utc

# 3. Tiempo Sidéreo en Greenwich (en formato de horas, minutos y segundos)
gmst_hours = t_utc.sidereal_time('mean', 'greenwich').hour
gast_hours = t_utc.sidereal_time('apparent', 'greenwich').hour

def format_sidereal(h_decimal):
    h = int(h_decimal)
    m = int((h_decimal - h) * 60)
    s = (h_decimal - h - m / 60) * 3600
    return f"{h:02d}:{m:02d}:{s:06.3f}"

gmst_str = format_sidereal(gmst_hours)
gast_str = format_sidereal(gast_hours)

# --- Visualización ---

st.markdown("### 1. Escalas Civiles y Atómicas")
col1, col2 = st.columns(2)
with col1:
    st.info(f"**UTC (Coordinado)**\n\n`{t_utc.iso}`")
    st.success(f"**TAI (Atómico Internacional)**\n\n`{t_tai.iso}`")
    st.warning(f"**TGPS (Tiempo GPS)**\n\n`{t_gps.iso}`")
with col2:
    st.info(f"**UT (Universal Civil)**\n\n`{t_ut.iso}`")
    st.error(f"**UT1 (Rotación Real Terrestre)**\n\n`{t_ut1.iso}`")

st.markdown("### 2. Escalas Dinámicas y Efemérides")
col3, col4 = st.columns(2)
with col3:
    st.info(f"**TT (Tiempo Terrestre)**\n\n`{t_tt.iso}`")
with col4:
    st.info(f"**TE / ET (Tiempo de Efemérides)**\n\n`{t_te.iso}`")

st.markdown("### 3. Tiempo Sidéreo (Greenwich)")
col5, col6 = st.columns(2)
with col5:
    st.metric(label="GMST (Sidéreo Medio)", value=gmst_str)
with col6:
    st.metric(label="GAST (Sidéreo Aparente)", value=gast_str)

st.markdown("---")
st.markdown("### Desfases y Parámetros IERS")
st.write(f"- **TAI − UTC:** `{(t_tai - t_utc).to('s').value:.3f} s`")
st.write(f"- **TGPS − UTC:** `{(t_gps - t_utc).to('s').value:.3f} s`")
st.write(f"- **TT − TAI:** `32.184 s` (constante fija de calibración)")
st.write(f"- **UT1 − UTC ($DUT1$):** `{(t_ut1 - t_utc).to('s').value:.6f} s`")
