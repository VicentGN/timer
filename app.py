from datetime import date, time
import streamlit as st
from astropy.time import Time
from astropy.utils.iers import IERSRangeError, conf

conf.auto_max_age = None

st.set_page_config(page_title="Reloj Multiescala", page_icon="⏱️", layout="centered")
st.title("⏱️ Monitor Multiescala de Tiempo")

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
t_tai = t_utc.tai
t_gps = t_utc.replicate(scale='gps')  				
t_tt  = t_utc.tt                      # TT = TAI + 32.184 s
t_tcg = t_utc.tcg                     # Tiempo de Coordenadas Geocéntrico

# 2. Escala rotacional UT1 y Tiempo Sidéreo protegidos
ut1_str = None
dut1_val = None
gmst_str = "No disponible"
gast_str = "No disponible"
iers_error_msg = None

try:
    t_ut1 = t_utc.ut1
    ut1_str = t_ut1.iso
    dut1_val = float(t_utc.delta_ut1_utc)
    
    gmst = t_utc.sidereal_time('mean', 'greenwich')
    gast = t_utc.sidereal_time('apparent', 'greenwich')
    gmst_str = gmst.to_string(sep=':', precision=3, pad=True)
    gast_str = gast.to_string(sep=':', precision=3, pad=True)
except (IERSRangeError, Exception):
    ut1_str = "Fuera de cobertura IERS"
    iers_error_msg = (
        "La fecha seleccionada no cuenta con datos de orientación terrestre en las tablas IERS."
    )

# 3. Desfases entre escalas (en segundos)
diff_tai_utc = ((t_tai.jd1 - t_utc.jd1) + (t_tai.jd2 - t_utc.jd2)) * 86400.0
diff_tai_gps = ((t_tai.jd1 - t_gps.jd1) + (t_tai.jd2 - t_gps.jd2)) * 86400.0
diff_tcg_tt  = ((t_tcg.jd1 - t_tt.jd1)  + (t_tcg.jd2 - t_tt.jd2))  * 86400.0

# --- Visualización ---

if iers_error_msg:
    st.warning(f"⚠️ **Aviso IERS:** {iers_error_msg}")

st.markdown("### 1. Escalas Civiles y Atómicas")
col1, col2 = st.columns(2)
with col1:
    st.info(f"**UTC (Coordinado)**\n\n`{t_utc.iso}`")
    st.success(f"**TAI (Atómico Internacional)**\n\n`{t_tai.iso}`")
with col2:
    st.warning(f"**GPS (Sistema GPS)**\n\n`{t_gps.iso}`")
    st.error(f"**UT1 (Rotacional)**\n\n`{ut1_str}`")

st.markdown("### 2. Escalas Dinámicas y Coordenadas")
col3, col4 = st.columns(2)
with col3:
    st.info(f"**TT (Tiempo Terrestre)**\n\n`{t_tt.iso}`")
with col4:
    st.info(f"**TCG (Coordenadas Geocéntrico)**\n\n`{t_tcg.iso}`")

st.markdown("### 3. Tiempo Sidéreo en Greenwich")
col5, col6 = st.columns(2)
with col5:
    st.metric(label="GMST (Medio)", value=gmst_str)
with col6:
    st.metric(label="GAST (Aparente)", value=gast_str)

st.markdown("---")
st.markdown("### Desfases y Parámetros")
st.write(f"- **TAI − GPS:** `{diff_tai_gps:.3f} s` (fijo: TAI va 19 s por delante de GPS)")
st.write(f"- **TAI − UTC:** `{diff_tai_utc:.3f} s` (segundos intercalares acumulados)")
st.write(f"- **GPS − UTC:** `{diff_tai_utc - diff_tai_gps:.3f} s` (diferencia visible entre GPS y UTC)")
st.write(f"- **TT − TAI:** `32.184 s` (fijo por definición)")
st.write(f"- **TCG − TT:** `{diff_tcg_tt:.6f} s` (deriva secular relativista)")

if dut1_val is not None:
    st.write(f"- **DUT1 (UT1 − UTC):** `{dut1_val:+.6f} s`")
else:
    st.write("- **DUT1:** *No disponible para esta fecha.*")
