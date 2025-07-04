import json
import streamlit as st
import geemap.foliumap as geemap
import ee
from streamlit_folium import st_folium
import folium

st.set_page_config(
    page_title="MWM",
    page_icon="🌲",
    layout="wide"
)
st.markdown('<h1 style="color:green;">Mapping Wilderness Management</h1>', unsafe_allow_html=True)

# Cargar directamente desde secrets
service_account_info = st.secrets["GEE_JSON"]

credentials = ee.ServiceAccountCredentials(
    email=service_account_info["client_email"],
    key_data=json.dumps(dict(service_account_info))  # aquí sí generamos el string JSON para las credenciales
)
ee.Initialize(credentials)

st.header("Áreas Protegidas en Argentina")
st.markdown("<p style='font-size:18px;'>Argentina cuenta con un extenso Sistema Nacional de Áreas Protegidas (SNAP) que abarca diversas categorías como parques nacionales, reservas naturales y monumentos naturales, con el objetivo de proteger la biodiversidad y los ecosistemas del país.</p>", unsafe_allow_html=True)
Map = geemap.Map(center=[-38.0, -64.0], zoom=4.5)

paises = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
argentina = paises.filter(ee.Filter.eq("country_na", "Argentina"))

areas_protegidas = ee.FeatureCollection("WCMC/WDPA/current/polygons")
ap_argentina = areas_protegidas.filterBounds(argentina.geometry())

Map.addLayer(argentina, {'color': 'blue'}, 'Límite Argentina')
Map.addLayer(ap_argentina, {'color': 'green'}, 'Áreas protegidas (todo el país)')

col1, col2, col3 = st.columns([1, 3, 1])  # o [1, 2, 1] para más ancho

with col2:
    Map.to_streamlit(height=500)
    
st.divider()
st.header("Variación del NDVI en el Norte Argentino")
st.markdown("<p style='font-size:18px;'>Cálculo del estado promedio de la vegetación en áreas terrestres del Norte Argentino para dos años clave: 2015 y 2024, usando imágenes satelitales y el índice NDVI. Para cada región y para los años 2015 y 2020, se calcula el NDVI promedio anual utilizando imágenes Sentinel-2.</p>", unsafe_allow_html=True)

# Definir regiones con polígonos aproximados
norte = ee.Geometry.Polygon([[[-64.5, -21], [-60, -21], [-60, -26.5], [-65, -26.5], [-65, -21]]])
sur = ee.Geometry.Polygon([[[-70, -40], [-60, -40], [-60, -55], [-70, -55], [-70, -40]]])
este = ee.Geometry.Polygon([[[-60, -26], [-56, -26], [-56, -30], [-60, -30], [-60, -26]]])
oeste = ee.Geometry.Polygon([[[-70, -29], [-66, -29], [-66, -36], [-70, -36], [-70, -29]]])

regiones = {
    'Norte': norte,
    'Sur': sur,
    'Este': este,
    'Oeste': oeste
}

# Función para calcular NDVI de una imagen Sentinel-2
def calcular_ndvi(imagen):
    ndvi = imagen.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return ndvi

# Función para obtener NDVI medio anual en un área específica
def obtener_ndvi_por_region_y_año(region_geom, anio):
    fecha_inicio = f'{anio}-01-01'
    fecha_fin = f'{anio}-12-31'

    coleccion = ee.ImageCollection("COPERNICUS/S2") \
        .filterDate(fecha_inicio, fecha_fin) \
        .filterBounds(region_geom) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .map(calcular_ndvi)

    ndvi_anual = coleccion.select('NDVI').mean().clip(region_geom)
    return ndvi_anual

# Calcular NDVI para cada región y año
ndvi_por_region = {}
anios = [2015, 2024]

for region_name, geom in regiones.items():
    ndvi_por_region[region_name] = {}
    for anio in anios:
        ndvi_por_region[region_name][anio] = obtener_ndvi_por_region_y_año(geom, anio)

# Calcular diferencia de NDVI entre 2024 y 2015
ndvi_diferencia_norte = ndvi_por_region['Norte'][2024].subtract(ndvi_por_region['Norte'][2015]).rename('Delta_NDVI')

# Crear mapa y mostrarlo
Map_ndvi = geemap.Map(center=[-24, -63], zoom=5)

vis_params = {
    'min': -0.5,
    'max': 0.5,
    'palette': ['red', 'yellow', 'green']
}

Map_ndvi.addLayer(ndvi_diferencia_norte, vis_params, 'Delta NDVI Norte (2024 - 2015)')

col1, col2, col3 = st.columns([1, 3, 1])  # o [1, 2, 1] para más ancho

with col2:
    Map_ndvi.to_streamlit(height=500)

st.divider()
st.subheader("NDVI y áreas protegidas")
st.markdown("<p style='font-size:18px;'>Análisis de las variaciones del índice NDVI en las regiones protegidas de Argentina.</p>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("ap_ndvi.png", use_container_width=True)

st.markdown("<p style='font-size:18px;'>Existe una tendencia general negativa. Solamente cinco áreas mejoraron su NDVI. La mayoría sufrieron una disminución en la calidad de vegetación. El deterioro evidente se concentra en regiones que deberían estar conservadas.</p>", unsafe_allow_html=True)
st.divider()

st.subheader("El Impenetrable en riesgo")
st.markdown(
    "<p style='font-size:18px;'>Mapa interactivo que muestra las zonas protegidas con riesgo ambiental según análisis recientes.</p>",
    unsafe_allow_html=True
)

import pandas as pd
df = pd.read_csv('alerta_deforestacion.csv')
# Crear mapa base
m = folium.Map(location=[-25, -60], zoom_start=5)

# Función de color según riesgo
def color(r):
    return 'red' if r == 1 else 'green'

# Agregar puntos del DataFrame
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row['Latitud'], row['Longitud']],
        radius=6,
        color=color(row['Prediccion']),
        fill=True,
        fill_opacity=0.7,
        popup=row['Nombre']
    ).add_to(m)
    
# Centrado en la página usando columnas
col1, col2, col3 = st.columns([1, 2, 1])  # columna central más grande
with col2:
    st_folium(m, width=700, height=500)

st.markdown(
    "<p style='font-size:18px;'>El Chaco argentino es uno de los focos de deforestación de Sudamérica, siendo la segunda región más deforestada de Argentina tras la Pampa Húmeda.</p>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='font-size:18px;'>Entre 1998 y 2020, Chaco perdió más de 1 millón de hectáreas de bosque nativo. Los departamentos de General Güemes y General San Martín (donde se encuentra Villa Río Bermejito y El Espinillo) son de los más afectados en deforestación chaqueña.</p>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='font-size:18px;'>Dado los resultados validados con el análisis del Chaco, resulta elevado el riesgo de deforestación identificado en El Impenetrable, se avanzará con un estudio detallado en esta área protegida. Se implementarán nuevas mallas de mayor resolución para localizar con precisión las coordenadas de riesgo inminente, facilitando intervenciones más efectivas y oportunas.</p>",
    unsafe_allow_html=True
)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("chaco_def.png", width=550)  # Ajustá el ancho a un tamaño más pequeño (por ej. 300px)
    st.caption("Puntos de deforestación registrados en la zona del norte argentino hasta 2022.")  # Texto abajo, estilo pequeño y gris
