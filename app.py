import json
import streamlit as st
import geemap.foliumap as geemap
import ee

st.set_page_config(
    page_title="MWM",
    page_icon="🌲",
    layout="wide"
)
st.markdown('<h1 style="color:green;">MWM</h1>', unsafe_allow_html=True)
st.title("_Mapping Wilderness Management_")

# Cargar directamente desde secrets
service_account_info = st.secrets["GEE_JSON"]

credentials = ee.ServiceAccountCredentials(
    email=service_account_info["client_email"],
    key_data=json.dumps(dict(service_account_info))  # aquí sí generamos el string JSON para las credenciales
)
ee.Initialize(credentials)

st.header("Áreas Protegidas en Argentina")
st.write("Argentina cuenta con un extenso Sistema Nacional de Áreas Protegidas (SNAP) que abarca diversas categorías como parques nacionales, reservas naturales y monumentos naturales, con el objetivo de proteger la biodiversidad y los ecosistemas del país. ")
Map = geemap.Map(center=[-38.0, -64.0], zoom=4.5)

paises = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
argentina = paises.filter(ee.Filter.eq("country_na", "Argentina"))

areas_protegidas = ee.FeatureCollection("WCMC/WDPA/current/polygons")
ap_argentina = areas_protegidas.filterBounds(argentina.geometry())

Map.addLayer(argentina, {'color': 'blue'}, 'Límite Argentina')
Map.addLayer(ap_argentina, {'color': 'green'}, 'Áreas protegidas (todo el país)')

st.divider()
st.header("Variación del NDVI en el Norte Argentino")

Map.to_streamlit()
