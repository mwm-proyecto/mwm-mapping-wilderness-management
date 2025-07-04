import json
import streamlit as st
import geemap.foliumap as geemap
import ee

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

st.markdown("<h3>Áreas Protegidas en Argentina</h3>", unsafe_allow_html=True)
st.markdown("<p style='font-size:18px;'>Argentina cuenta con un extenso Sistema Nacional de Áreas Protegidas (SNAP) que abarca diversas categorías como parques nacionales, reservas naturales y monumentos naturales, con el objetivo de proteger la biodiversidad y los ecosistemas del país.</p>", unsafe_allow_html=True)
Map = geemap.Map(center=[-38.0, -64.0], zoom=4.5)

paises = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
argentina = paises.filter(ee.Filter.eq("country_na", "Argentina"))

areas_protegidas = ee.FeatureCollection("WCMC/WDPA/current/polygons")
ap_argentina = areas_protegidas.filterBounds(argentina.geometry())

Map.addLayer(argentina, {'color': 'blue'}, 'Límite Argentina')
Map.addLayer(ap_argentina, {'color': 'green'}, 'Áreas protegidas (todo el país)')
Map.to_streamlit()

st.divider()
st.header("Variación del NDVI en el Norte Argentino")
st.markdown("<p style='font-size:18px;'>Cálculo del estado promedio de la vegetación en todas las áreas protegidas terrestres de Argentina para dos años clave: 2015 y 2024, usando imágenes satelitales y el índice NDVI. Para cada región y para los años 2015 y 2020, se calcula el NDVI promedio anual utilizando imágenes Sentinel-2.</p>", unsafe_allow_html=True)

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

Map_ndvi.to_streamlit()
