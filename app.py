import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuración de la página
st.set_page_config(page_title="Sala Situacional de Salud", layout="wide")

ARCHIVO_DATOS = "sala_situacional_cloud.csv"
MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
CONDICIONES_EGRESO = ["Vivo", "Fallecido", "Referido", "Contraopinión/Fuga"]
VARIABLES_DISPONIBLES = ["Año", "SemanaEpi", "Mes", "Edad", "Sexo", "Procedencia", "CondicionEgreso", "Diagnosticos", "CIE10"]

# Base de datos de usuarios y roles
CREDENCIALES = {
    "Luis": {"password": "LuisAdmin2026", "admin": True},
    "Marcos": {"password": "MarcosDoc1", "admin": False},
    "Juan": {"password": "JuanDoc2", "admin": False}
}

# Inicializar Base de Datos en la nube
if not os.path.exists(ARCHIVO_DATOS):
    df_inicial = pd.DataFrame(columns=[
        "ID", "Usuario", "Año", "Mes", "SemanaEpi", "Edad", "Sexo", 
        "Procedencia", "CondicionEgreso", "Diagnosticos", "CIE10"
    ])
    df_inicial.to_csv(ARCHIVO_DATOS, index=False)

def cargar_datos():
    return pd.read_csv(ARCHIVO_DATOS)

def guardar_datos(df):
    df.to_csv(ARCHIVO_DATOS, index=False)

def expandir_columna(df, col):
    if df.empty or col not in df.columns:
        return df
    df_copia = df.copy()
    df_copia[col] = df_copia[col].astype(str).str.split(';')
    df_exp = df_copia.explode(col)
    df_exp[col] = df_exp[col].str.strip()
    return df_exp

# --- SISTEMA DE AUTENTICACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.admin = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso a la Sala Situacional")
    st.markdown("Ingrese sus credenciales institucionales.")
    
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")
        
        if submit:
            if username in CREDENCIALES and CREDENCIALES[username]["password"] == password:
                st.session_state.autenticado = True
                st.session_state.usuario = username
                st.session_state.admin = CREDENCIALES[username]["admin"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop()

# --- APLICACIÓN PRINCIPAL ---
st.sidebar.title(f"Dr(a). {st.session_state.usuario}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()

st.title("🏥 Sala Situacional de Salud y Vigilancia Epidemiológica")

df_global = cargar_datos()

# Panel lateral para Registro de Casos
st.sidebar.markdown("---")
st.sidebar.subheader("📝 Registrar Caso Clínico")

with st.sidebar.form("form_registro"):
    anio = st.number_input("Año", value=2026, min_value=2000, max_value=2100)
    mes = st.selectbox("Mes", MESES_NOMBRES)
    semana_epi = st.number_input("Semana Epidemiológica (1-53)", value=1, min_value=1, max_value=53)
    sexo = st.radio("Sexo", ["Femenino", "Masculino"], horizontal=True)
    edad = st.number_input("Edad (años)", value=30, min_value=0, max_value=120)
    
    proc_hist = list(df_global["Procedencia"].dropna().unique()) if not df_global.empty else ["Central", "Norte", "Sur"]
    procedencia = st.text_input("Procedencia (Municipio/Área)", value=proc_hist[0] if proc_hist else "Central")
    
    condicion_egreso = st.selectbox("Condición de Egreso", CONDICIONES_EGRESO)
    diagnosticos = st.text_input("Diagnóstico(s) (Separar con punto y coma ';')", value="Apendicitis aguda")
    cie10 = st.text_input("Código(s) CIE-10 (Separar con ';')", value="K35")
    
    btn_guardar = st.form_submit_button("Guardar Caso en la Nube")
    
    if btn_guardar:
        nuevo_id = int(df_global["ID"].max() + 1) if not df_global.empty and not pd.isna(df_global["ID"].max()) else 1
        nuevo_registro = pd.DataFrame([{
            "ID": nuevo_id, "Usuario": st.session_state.usuario, "Año": anio, "Mes": mes,
            "SemanaEpi": semana_epi, "Edad": edad, "Sexo": sexo, "Procedencia": procedencia,
            "CondicionEgreso": condicion_egreso, "Diagnosticos": diagnosticos, "CIE10": cie10
        }])
        df_global = pd.concat([df_global, nuevo_registro], ignore_index=True)
        guardar_datos(df_global)
        st.sidebar.success("¡Caso registrado con éxito!")
        st.rerun()

# --- CONTROL DE ROLES Y FILTROS GLOBALES ---
if st.session_state.admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Panel de Auditoría (Admin)")
    usuarios_disponibles = ["Todos los usuarios"] + list(df_global["Usuario"].dropna().unique()) if not df_global.empty else ["Todos los usuarios"]
    filtro_medico = st.sidebar.selectbox("Ver registros de:", usuarios_disponibles)
    if filtro_medico != "Todos los usuarios":
        df_autorizado = df_global[df_global["Usuario"] == filtro_medico]
    else:
        df_autorizado = df_global
else:
    df_autorizado = df_global[df_global["Usuario"] == st.session_state.usuario]

# Filtros superiores de visualización
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    anios_disp = ["Todos los años"] + sorted(list(df_autorizado["Año"].dropna().unique())) if not df_autorizado.empty else ["Todos los años"]
    f_anio = st.selectbox("Filtrar por Año", anios_disp)
with col_f2:
    f_mes = st.selectbox("Filtrar por Mes", ["Todos los meses"] + MESES_NOMBRES)
with col_f3:
    f_egreso = st.selectbox("Filtrar por Egreso", ["Todos los egresos"] + CONDICIONES_EGRESO)

# Aplicar filtros
df_filtrado = df_autorizado.copy()
if f_anio != "Todos los años":
    df_filtrado = df_filtrado[df_filtrado["Año"] == int(f_anio)]
if f_mes != "Todos los meses":
    df_filtrado = df_filtrado[df_filtrado["Mes"] == f_mes]
if f_egreso != "Todos los egresos":
    df_filtrado = df_filtrado[df_filtrado["CondicionEgreso"] == f_egreso]

# --- PESTAÑAS DE LA SALA SITUACIONAL ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Demografía & Territorio", "Morbilidad", "Mortalidad", "Análisis Bivariado", "Base de Datos"])

with tab1:
    st.subheader("Demografía y Territorio")
    if df_filtrado.empty:
        st.info("No hay datos registrados con los filtros seleccionados.")
    else:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fig_proc = px.bar(df_filtrado["Procedencia"].value_counts().reset_index(), x="index", y="Procedencia", 
                              labels={"index": "Procedencia", "Procedencia": "Casos"}, title="Casos por Procedencia Geográfica",
                              color_discrete_sequence=["#E67E22"])
            st.plotly_chart(fig_proc, use_container_width=True)
        with col_p2:
            fig_sexo = px.bar(df_filtrado["Sexo"].value_counts().reset_index(), x="index", y="Sexo",
                              labels={"index": "Sexo", "Sexo": "Casos"}, title="Distribución por Sexo",
                              color="index", color_discrete_map={"Femenino": "coral", "Masculino": "lightgreen"})
            st.plotly_chart(fig_sexo, use_container_width=True)

with tab2:
    st.subheader("Canal de Morbilidad y Tendencias")
    if df_filtrado.empty:
        st.info("No hay datos para mostrar en morbilidad.")
    else:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            fig_meses = px.bar(df_filtrado["Mes"].value_counts().reindex(MESES_NOMBRES).reset_index(), x="index", y="Mes",
                               labels={"index": "Mes", "Mes": "Casos"}, title="Tendencia Mensual de Casos",
                               color_discrete_sequence=["mediumpurple"])
            st.plotly_chart(fig_meses, use_container_width=True)
            
        with col_m2:
            df_exp_dx = expandir_columna(df_filtrado, "Diagnosticos")
            lista_dx_disp = ["Todos los diagnósticos"] + sorted(list(df_exp_dx["Diagnosticos"].dropna().unique()))
            sel_dx_curva = st.selectbox("Curva por Diagnóstico específico:", lista_dx_disp)
            
            df_curva = df_exp_dx.copy()
            if sel_dx_curva != "Todos los diagnósticos":
                df_curva = df_curva[df_curva["Diagnosticos"] == sel_dx_curva]
                
            tabla_sem = df_curva["SemanaEpi"].value_counts().sort_index().reset_index()
            tabla_sem.columns = ["Semana", "Freq"]
            
            fig_sem = px.line(tabla_sem, x="Semana", y="Freq", markers=True,
                              title=f"Curva Epi: {sel_dx_curva}",
                              labels={"Semana": "Semana Epidemiológica", "Freq": "Casos"})
            fig_sem.update_traces(line_color="#8E44AD", line_width=2)
            st.plotly_chart(fig_sem, use_container_width=True)

        col_m3, col_m4 = st.columns(2)
        with col_m3:
            df_dx_freq = expandir_columna(df_filtrado, "Diagnosticos")
            fig_dx = px.bar(df_dx_freq["Diagnosticos"].value_counts().reset_index(), x="index", y="Diagnosticos",
                            labels={"index": "Diagnóstico", "Diagnosticos": "Frecuencia"}, title="Diagnósticos Frecuentes",
                            color_discrete_sequence=["lightcoral"])
            st.plotly_chart(fig_dx, use_container_width=True)
        with col_m4:
            df_cie_freq = expandir_columna(df_filtrado, "CIE10")
            fig_cie = px.bar(df_cie_freq["CIE10"].value_counts().reset_index(), x="index", y="CIE10",
                             labels={"index": "CIE-10", "CIE10": "Frecuencia"}, title="Códigos CIE-10 Registrados",
                             color_discrete_sequence=["steelblue"])
            st.plotly_chart(fig_cie, use_container_width=True)

with tab3:
    st.subheader("Mortalidad y Letalidad")
    total_casos = len(df_filtrado)
    df_fallecidos = df_filtrado[df_filtrado["CondicionEgreso"] == "Fallecido"]
    num_fallecidos = len(df_fallecidos)
    tasa_let = (num_fallecidos / total_casos * 100) if total_casos > 0 else 0
    
    st.metric(label="Indicador Global", value=f"{num_fallecidos} Fallecidos de {total_casos} casos", delta=f"Letalidad: {tasa_let:.2f}%")
    
    if num_fallecidos > 0:
        col_mort1, col_mort2 = st.columns(2)
        with col_mort1:
            df_mort_dx = expandir_columna(df_fallecidos, "Diagnosticos")
            fig_m_dx = px.bar(df_mort_dx["Diagnosticos"].value_counts().reset_index(), x="index", y="Diagnosticos",
                              labels={"index": "Diagnóstico", "Diagnosticos": "Fallecidos"}, title="Causas de Mortalidad",
                              color_discrete_sequence=["#C0392B"])
            st.plotly_chart(fig_m_dx, use_container_width=True)
        with col_mort2:
            fig_m_edad = px.histogram(df_fallecidos, x="Edad", title="Distribución de Edad en Fallecidos",
                                      labels={"Edad": "Edad", "count": "Fallecidos"}, color_discrete_sequence=["#7F8C8D"])
            st.plotly_chart(fig_m_edad, use_container_width=True)
    else:
        st.info("No hay defunciones registradas en el filtro actual.")

with tab4:
    st.subheader("Análisis Bivariado Estadístico")
    if len(df_filtrado) < 2:
        st.warning("Se requieren al menos 2 registros para realizar cruces estadísticos.")
    else:
        col_bx1, col_bx2 = st.columns(2)
        with col_bx1:
            var_x = st.selectbox("Variable X", VARIABLES_DISPONIBLES, index=5)
        with col_bx2:
            var_y = st.selectbox("Variable Y", VARIABLES_DISPONIBLES, index=6)
            
        df_biv = expandir_columna(df_filtrado, var_x)
        if var_x != var_y:
            df_biv = expandir_columna(df_biv, var_y)
            
        fig_biv = px.histogram(df_biv, x=var_x, color=var_y, barmode="group",
                               title=f"Cruce Bivariado: {var_y} según {var_x}")
        st.plotly_chart(fig_biv, use_container_width=True)

with tab5:
    st.subheader("Base de Datos Autorizada")
    st.dataframe(df_autorizado, use_container_width=True)