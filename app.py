import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Sala Situacional de Salud", layout="wide")

ARCHIVO_DATOS = "sala_situacional_cloud.csv"
MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
CONDICIONES_EGRESO = ["Vivo", "Fallecido", "Referido", "Contraopinión/Fuga"]
VARIABLES_DISPONIBLES = ["Año", "SemanaEpi", "Mes", "Edad", "Sexo", "Procedencia", "CondicionEgreso", "Diagnosticos", "CIE10"]

CREDENCIALES = {
    "Luis": {"password": "LuisAdmin2026", "admin": True},
    "Marcos": {"password": "MarcosDoc1", "admin": False},
    "Juan": {"password": "JuanDoc2", "admin": False}
}

# Inicializar Base de Datos con registros de prueba si no existe
if not os.path.exists(ARCHIVO_DATOS):
    df_inicial = pd.DataFrame([
        {
            "ID": 1, "Usuario": "Luis", "Año": 2026, "Mes": "Enero", "SemanaEpi": 1,
            "Edad": 35, "Sexo": "Masculino", "Procedencia": "Central",
            "CondicionEgreso": "Vivo", "Diagnosticos": "Apendicitis aguda", "CIE10": "K35"
        }
    ])
    df_inicial.to_csv(ARCHIVO_DATOS, index=False)

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        return pd.read_csv(ARCHIVO_DATOS)
    return pd.DataFrame()

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

# --- AUTENTICACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.admin = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso a la Sala Situacional")
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

st.sidebar.title(f"Dr(a). {st.session_state.usuario}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()

st.title("🏥 Sala Situacional de Salud y Vigilancia Epidemiológica")

df_global = cargar_datos()

# Listas históricas dinámicas recopiladas de la base de datos
procedencias_hist = sorted(list(df_global["Procedencia"].dropna().unique())) if not df_global.empty and "Procedencia" in df_global.columns else ["Central"]
if not procedencias_hist: procedencias_hist = ["Central"]

dx_hist_list = []
if not df_global.empty and "Diagnosticos" in df_global.columns:
    for d in df_global["Diagnosticos"].dropna():
        dx_hist_list.extend([x.strip() for x in str(d).split(";") if x.strip()])
dx_hist_list = sorted(list(set(dx_hist_list)))
if not dx_hist_list: dx_hist_list = ["Apendicitis aguda", "Colelitiasis"]

cie_hist_list = []
if not df_global.empty and "CIE10" in df_global.columns:
    for c in df_global["CIE10"].dropna():
        cie_hist_list.extend([x.strip() for x in str(c).split(";") if x.strip()])
cie_hist_list = sorted(list(set(cie_hist_list)))
if not cie_hist_list: cie_hist_list = ["K35", "K80"]

# --- PANEL LATERAL DE REGISTRO / EDICIÓN ---
st.sidebar.markdown("---")
st.sidebar.subheader("📝 Registrar o Editar Caso Clínico")

if "editando_id" not in st.session_state:
    st.session_state.editando_id = None

fila_a_editar = None
if st.session_state.editando_id is not None and not df_global.empty:
    match = df_global[df_global["ID"] == st.session_state.editando_id]
    if not match.empty:
        fila_a_editar = match.iloc[0]

if fila_a_editar is not None:
    st.sidebar.warning(f"Editando Caso ID: {st.session_state.editando_id}")
    if st.sidebar.button("Cancelar Edición"):
        st.session_state.editando_id = None
        st.rerun()

with st.sidebar.form("form_registro"):
    val_anio = int(fila_a_editar["Año"]) if fila_a_editar is not None else 2026
    anio = st.number_input("Año", value=val_anio, min_value=2000, max_value=2100)
    
    val_mes_idx = MESES_NOMBRES.index(fila_a_editar["Mes"]) if fila_a_editar is not None and fila_a_editar["Mes"] in MESES_NOMBRES else 0
    mes = st.selectbox("Mes", MESES_NOMBRES, index=val_mes_idx)
    
    val_sem = int(fila_a_editar["SemanaEpi"]) if fila_a_editar is not None else 1
    semana_epi = st.number_input("Semana Epidemiológica (1-53)", value=val_sem, min_value=1, max_value=53)
    
    val_sexo_idx = 0 if fila_a_editar is not None and fila_a_editar["Sexo"] == "Femenino" else 1
    sexo = st.radio("Sexo", ["Femenino", "Masculino"], index=val_sexo_idx, horizontal=True)
    
    val_edad = int(fila_a_editar["Edad"]) if fila_a_editar is not None else 30
    edad = st.number_input("Edad (años)", value=val_edad, min_value=0, max_value=120)
    
    # Procedencia (Historial + Opción de nueva procedencia)
    val_proc = fila_a_editar["Procedencia"] if fila_a_editar is not None else procedencias_hist[0]
    idx_proc = procedencias_hist.index(val_proc) if val_proc in procedencias_hist else 0
    nueva_proc_select = st.selectbox("Procedencia (Historial)", options=procedencias_hist + ["[Escribir nueva procedencia]"], index=idx_proc)
    custom_proc = st.text_input("Nueva procedencia (si seleccionó escribir otra):", value="")
    procedencia_final = custom_proc.strip() if custom_proc.strip() else nueva_proc_select
    if procedencia_final == "[Escribir nueva procedencia]": procedencia_final = "Central"

    val_egreso_idx = CONDICIONES_EGRESO.index(fila_a_editar["CondicionEgreso"]) if fila_a_editar is not None and fila_a_editar["CondicionEgreso"] in CONDICIONES_EGRESO else 0
    condicion_egreso = st.selectbox("Condición de Egreso", CONDICIONES_EGRESO, index=val_egreso_idx)
    
    # 1. DIAGNÓSTICOS MÚLTIPLES INTELIGENTES
    val_dx_list = [x.strip() for x in str(fila_a_editar["Diagnosticos"]).split(";")] if fila_a_editar is not None else [dx_hist_list[0]]
    val_dx_list = [x for x in val_dx_list if x in dx_hist_list]
    if not val_dx_list: val_dx_list = [dx_hist_list[0]]
    
    diagnosticos_sel = st.multiselect("Diagnósticos (Seleccione del historial o escriba nuevos y pulse Enter)", options=dx_hist_list, default=val_dx_list)
    nuevo_dx_extra = st.text_input("Añadir otro diagnóstico nuevo (si son varios, separar con ';'):", value="")
    
    lista_dx_final = diagnosticos_sel.copy()
    if nuevo_dx_extra.strip():
        for item in nuevo_dx_extra.split(";"):
            if item.strip() and item.strip() not in lista_dx_final:
                lista_dx_final.append(item.strip())
    if not lista_dx_final: lista_dx_final = ["Apendicitis aguda"]
    diagnosticos_txt = "; ".join(lista_dx_final)

    # 2. CÓDIGOS CIE-10 MÚLTIPLES INTELIGENTES
    val_cie_list = [x.strip() for x in str(fila_a_editar["CIE10"]).split(";")] if fila_a_editar is not None else [cie_hist_list[0]]
    val_cie_list = [x for x in val_cie_list if x in cie_hist_list]
    if not val_cie_list: val_cie_list = [cie_hist_list[0]]
    
    cie10_sel = st.multiselect("Códigos CIE-10 (Seleccione del historial o escriba nuevos y pulse Enter)", options=cie_hist_list, default=val_cie_list)
    nuevo_cie_extra = st.text_input("Añadir otro código CIE-10 nuevo (si son varios, separar con ';'):", value="")
    
    lista_cie_final = cie10_sel.copy()
    if nuevo_cie_extra.strip():
        for item in nuevo_cie_extra.split(";"):
            if item.strip() and item.strip() not in lista_cie_final:
                lista_cie_final.append(item.strip())
    if not lista_cie_final: lista_cie_final = ["K35"]
    cie10_txt = "; ".join(lista_cie_final)
    
    btn_guardar = st.form_submit_button("Guardar en la Nube" if fila_a_editar is None else "Actualizar Registro")
    
    if btn_guardar:
        if st.session_state.editando_id is None:
            nuevo_id = int(df_global["ID"].max() + 1) if not df_global.empty and not pd.isna(df_global["ID"].max()) else 1
            nuevo_registro = pd.DataFrame([{
                "ID": nuevo_id, "Usuario": st.session_state.usuario, "Año": anio, "Mes": mes,
                "SemanaEpi": semana_epi, "Edad": edad, "Sexo": sexo, "Procedencia": procedencia_final,
                "CondicionEgreso": condicion_egreso, "Diagnosticos": diagnosticos_txt, "CIE10": cie10_txt
            }])
            df_global = pd.concat([df_global, nuevo_registro], ignore_index=True)
            st.sidebar.success("¡Caso registrado con éxito!")
        else:
            idx = df_global[df_global["ID"] == st.session_state.editando_id].index[0]
            df_global.loc[idx, ["Año", "Mes", "SemanaEpi", "Edad", "Sexo", "Procedencia", "CondicionEgreso", "Diagnosticos", "CIE10"]] = [
                anio, mes, semana_epi, edad, sexo, procedencia_final, condicion_egreso, diagnosticos_txt, cie10_txt
            ]
            st.session_state.editando_id = None
            st.sidebar.success("¡Registro actualizado correctamente!")
            
        guardar_datos(df_global)
        st.rerun()

# --- CONTROL DE ROLES Y FILTROS ---
if st.session_state.admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Auditoría (Admin)")
    usuarios_disponibles = ["Todos los usuarios"] + list(df_global["Usuario"].dropna().unique()) if not df_global.empty else ["Todos los usuarios"]
    filtro_medico = st.sidebar.selectbox("Ver registros de:", usuarios_disponibles)
    if filtro_medico != "Todos los usuarios":
        df_autorizado = df_global[df_global["Usuario"] == filtro_medico]
    else:
        df_autorizado = df_global
else:
    df_autorizado = df_global[df_global["Usuario"] == st.session_state.usuario] if not df_global.empty else pd.DataFrame()

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    anios_disp = ["Todos los años"] + sorted(list(df_autorizado["Año"].dropna().unique())) if not df_autorizado.empty and "Año" in df_autorizado.columns else ["Todos los años"]
    f_anio = st.selectbox("Filtrar por Año", anios_disp)
with col_f2:
    f_mes = st.selectbox("Filtrar por Mes", ["Todos los meses"] + MESES_NOMBRES)
with col_f3:
    f_egreso = st.selectbox("Filtrar por Egreso", ["Todos los egresos"] + CONDICIONES_EGRESO)

df_filtrado = df_autorizado.copy()
if not df_filtrado.empty:
    if f_anio != "Todos los años":
        df_filtrado = df_filtrado[df_filtrado["Año"] == int(f_anio)]
    if f_mes != "Todos los meses":
        df_filtrado = df_filtrado[df_filtrado["Mes"] == f_mes]
    if f_egreso != "Todos los egresos":
        df_filtrado = df_filtrado[df_filtrado["CondicionEgreso"] == f_egreso]

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Demografía & Territorio", "Morbilidad", "Mortalidad", "Análisis Bivariado", "Matriz Multivariada", "Base de Datos"])

with tab1:
    st.subheader("Demografía y Territorio")
    if df_filtrado.empty:
        st.info("No hay datos registrados con los filtros seleccionados.")
    else:
        cortes = list(range(0, 121, 10))
        etiquetas = [f"{cortes[i]}-{cortes[i+1]-1}" for i in range(len(cortes)-1)]
        df_piramide = df_filtrado.copy()
        df_piramide["GrupoEdad"] = pd.cut(df_piramide["Edad"], bins=cortes, labels=etiquetas, right=False)
        
        tabla_pob = df_piramide.groupby(["GrupoEdad", "Sexo"], observed=False).size().reset_index(name="Freq")
        tabla_pob_f = tabla_pob[tabla_pob["Sexo"] == "Femenino"]
        tabla_pob_m = tabla_pob[tabla_pob["Sexo"] == "Masculino"].copy()
        tabla_pob_m["Freq"] = -tabla_pob_m["Freq"]
        
        if not tabla_pob_f.empty or not tabla_pob_m.empty:
            fig_piramide = px.bar(tabla_pob_f, x="Freq", y="GrupoEdad", orientation="h", title="Pirámide Poblacional de Casos Atendidos", color_discrete_sequence=["coral"])
            if not tabla_pob_m.empty:
                fig_piramide_m = px.bar(tabla_pob_m, x="Freq", y="GrupoEdad", orientation="h", color_discrete_sequence=["lightgreen"])
                for trace in fig_piramide_m.data:
                    fig_piramide.add_trace(trace)
            fig_piramide.update_layout(barmode="relative", xaxis_title="Cantidad (Masculino izq. / Femenino der.)", yaxis_title="Grupo de Edad")
            st.plotly_chart(fig_piramide, use_container_width=True)
        else:
            st.info("Datos insuficientes para construir la pirámide poblacional.")
            
        st.markdown("---")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            conteo_proc = df_filtrado["Procedencia"].value_counts().reset_index()
            conteo_proc.columns = ["Procedencia", "Casos"]
            fig_proc = px.bar(conteo_proc, x="Procedencia", y="Casos", title="Casos por Procedencia Geográfica", color_discrete_sequence=["#E67E22"])
            st.plotly_chart(fig_proc, use_container_width=True)
        with col_p2:
            conteo_sexo = df_filtrado["Sexo"].value_counts().reset_index()
            conteo_sexo.columns = ["Sexo", "Casos"]
            fig_sexo = px.bar(conteo_sexo, x="Sexo", y="Casos", title="Distribución por Sexo", color="Sexo", color_discrete_map={"Femenino": "coral", "Masculino": "lightgreen"})
            st.plotly_chart(fig_sexo, use_container_width=True)

with tab2:
    st.subheader("Canal de Morbilidad y Tendencias")
    if df_filtrado.empty:
        st.info("No hay datos para mostrar en morbilidad.")
    else:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            conteo_meses = df_filtrado["Mes"].value_counts().reindex(MESES_NOMBRES).fillna(0).reset_index()
            conteo_meses.columns = ["Mes", "Casos"]
            fig_meses = px.bar(conteo_meses, x="Mes", y="Casos", title="Tendencia Mensual de Casos", color_discrete_sequence=["mediumpurple"])
            st.plotly_chart(fig_meses, use_container_width=True)
            
        with col_m2:
            df_exp_dx = expandir_columna(df_filtrado, "Diagnosticos")
            lista_dx_disp = ["Todos los diagnósticos"] + sorted(list(df_exp_dx["Diagnosticos"].dropna().unique())) if not df_exp_dx.empty else ["Todos los diagnósticos"]
            sel_dx_curva = st.selectbox("Curva por Diagnóstico específico:", lista_dx_disp)
            
            df_curva = df_exp_dx.copy()
            if sel_dx_curva != "Todos los diagnósticos":
                df_curva = df_curva[df_curva["Diagnosticos"] == sel_dx_curva]
                
            tabla_sem = df_curva["SemanaEpi"].value_counts().sort_index().reset_index() if not df_curva.empty else pd.DataFrame(columns=["SemanaEpi", "count"])
            if not tabla_sem.empty:
                tabla_sem.columns = ["Semana", "Freq"]
                fig_sem = px.line(tabla_sem, x="Semana", y="Freq", markers=True, title=f"Curva Epi: {sel_dx_curva}")
                fig_sem.update_traces(line_color="#8E44AD", line_width=2)
                st.plotly_chart(fig_sem, use_container_width=True)
            else:
                st.info("Sin registros para este gráfico.")

        col_m3, col_m4 = st.columns(2)
        with col_m3:
            df_dx_freq = expandir_columna(df_filtrado, "Diagnosticos")
            if not df_dx_freq.empty and "Diagnosticos" in df_dx_freq.columns:
                conteo_dx = df_dx_freq["Diagnosticos"].value_counts().reset_index()
                conteo_dx.columns = ["Diagnostico", "Frecuencia"]
                fig_dx = px.bar(conteo_dx, x="Diagnostico", y="Frecuencia", title="Diagnósticos Frecuentes", color_discrete_sequence=["lightcoral"])
                st.plotly_chart(fig_dx, use_container_width=True)
        with col_m4:
            df_cie_freq = expandir_columna(df_filtrado, "CIE10")
            if not df_cie_freq.empty and "CIE10" in df_cie_freq.columns:
                conteo_cie = df_cie_freq["CIE10"].value_counts().reset_index()
                conteo_cie.columns = ["CIE10", "Frecuencia"]
                fig_cie = px.bar(conteo_cie, x="CIE10", y="Frecuencia", title="Códigos CIE-10 Registrados", color_discrete_sequence=["steelblue"])
                st.plotly_chart(fig_cie, use_container_width=True)

with tab3:
    st.subheader("Mortalidad y Letalidad")
    total_casos = len(df_filtrado)
    df_fallecidos = df_filtrado[df_filtrado["CondicionEgreso"] == "Fallecido"] if not df_filtrado.empty else pd.DataFrame()
    num_fallecidos = len(df_fallecidos)
    tasa_let = (num_fallecidos / total_casos * 100) if total_casos > 0 else 0
    
    st.metric(label="Indicador Global", value=f"{num_fallecidos} Fallecidos de {total_casos} casos", delta=f"Letalidad: {tasa_let:.2f}%")
    
    if num_fallecidos > 0:
        col_mort1, col_mort2 = st.columns(2)
        with col_mort1:
            df_mort_dx = expandir_columna(df_fallecidos, "Diagnosticos")
            conteo_m_dx = df_mort_dx["Diagnosticos"].value_counts().reset_index()
            conteo_m_dx.columns = ["Diagnostico", "Fallecidos"]
            fig_m_dx = px.bar(conteo_m_dx, x="Diagnostico", y="Fallecidos", title="Causas de Mortalidad", color_discrete_sequence=["#C0392B"])
            st.plotly_chart(fig_m_dx, use_container_width=True)
        with col_mort2:
            fig_m_edad = px.histogram(df_fallecidos, x="Edad", title="Distribución de Edad en Fallecidos", color_discrete_sequence=["#7F8C8D"])
            st.plotly_chart(fig_m_edad, use_container_width=True)
    else:
        st.info("No hay defunciones registradas en el filtro actual.")

with tab4:
    st.subheader("Análisis Bivariado Estadístico")
    if df_filtrado.empty or len(df_filtrado) < 2:
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
            
        fig_biv = px.histogram(df_biv, x=var_x, color=var_y, barmode="group", title=f"Cruce Bivariado: {var_y} según {var_x}")
        st.plotly_chart(fig_biv, use_container_width=True)

with tab5:
    st.subheader("Matriz Multivariada y Correlación")
    if df_filtrado.empty or len(df_filtrado) < 3:
        st.warning("Se requieren al menos 3 registros para la matriz multivariada.")
    else:
        vars_multi = st.multiselect("Seleccione variables a incluir:", VARIABLES_DISPONIBLES, default=["Edad", "SemanaEpi", "CondicionEgreso"])
        if len(vars_multi) >= 2:
            df_multi = df_filtrado.copy()
            for v in vars_multi:
                df_multi = expandir_columna(df_multi, v)
                
            df_plot_multi = df_multi[vars_multi].copy()
            for col in df_plot_multi.columns:
                if not pd.api.types.is_numeric_dtype(df_plot_multi[col]):
                    df_plot_multi[col] = pd.factorize(df_plot_multi[col])[0]
                    
            fig_splom = px.scatter_matrix(df_plot_multi, dimensions=vars_multi, title="Matriz de Dispersión Multivariada")
            st.plotly_chart(fig_splom, use_container_width=True)
            
            st.markdown("##### Matriz de Correlación de Spearman:")
            corr_matrix = df_plot_multi.corr(method="spearman")
            st.dataframe(corr_matrix, use_container_width=True)
        else:
            st.info("Seleccione al menos 2 variables para generar la matriz.")

with tab6:
    st.subheader("Gestión y Base de Datos Autorizada")
    if not df_autorizado.empty:
        st.dataframe(df_autorizado, use_container_width=True)
        
        st.markdown("---")
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            st.subheader("✏️ Editar un Registro por ID")
            id_a_editar = st.number_input("Ingrese el ID del paciente a editar:", min_value=1, step=1, key="input_editar")
            if st.button("Cargar para Editar", type="secondary"):
                if id_a_editar in df_global["ID"].values:
                    fila_obj = df_global[df_global["ID"] == id_a_editar].iloc[0]
                    if st.session_state.admin or fila_obj["Usuario"] == st.session_state.usuario:
                        st.session_state.editando_id = int(id_a_editar)
                        st.success(f"¡Caso ID {id_a_editar} cargado en el panel izquierdo! Modifique sus datos y pulse 'Actualizar Registro'.")
                        st.rerun()
                    else:
                        st.error("No tienes permisos para editar este registro.")
                else:
                    st.error("El ID ingresado no existe.")
                    
        with col_ed2:
            st.subheader("🗑️ Eliminar un Registro por ID")
            id_a_borrar = st.number_input("Ingrese el ID del paciente a eliminar:", min_value=1, step=1, key="input_borrar")
            if st.button("Eliminar Registro", type="primary"):
                if id_a_borrar in df_global["ID"].values:
                    fila_obj = df_global[df_global["ID"] == id_a_borrar]
                    if st.session_state.admin or fila_obj["Usuario"].values[0] == st.session_state.usuario:
                        df_global = df_global[df_global["ID"] != id_a_borrar]
                        guardar_datos(df_global)
                        st.success(f"Registro con ID {id_a_borrar} eliminado correctamente.")
                        st.rerun()
                    else:
                        st.error("No tienes permisos para eliminar un registro que no es tuyo.")
                else:
                    st.error("El ID ingresado no existe en la base de datos.")
    else:
        st.info("No hay registros en la base de datos.")
