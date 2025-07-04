import json
import streamlit as st
import geemap.foliumap as geemap
import ee

st.set_page_config(layout="wide")
st.title("MWM Mapping Wilderness Management")

# Cargar directamente desde secrets
service_account_info = st.secrets["GEE_JSON"]

credentials = ee.ServiceAccountCredentials(
    email=service_account_info["client_email"],
    key_data=json.dumps(dict(service_account_info))  # aquí sí generamos el string JSON para las credenciales
)
ee.Initialize(credentials)

Map = geemap.Map(center=[-38.0, -64.0], zoom=4.5)

paises = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
argentina = paises.filter(ee.Filter.eq("country_na", "Argentina"))

areas_protegidas = ee.FeatureCollection("WCMC/WDPA/current/polygons")
ap_argentina = areas_protegidas.filterBounds(argentina.geometry())

Map.addLayer(argentina, {'color': 'blue'}, 'Límite Argentina')
Map.addLayer(ap_argentina, {'color': 'green'}, 'Áreas protegidas (todo el país)')

Map.to_streamlit()
