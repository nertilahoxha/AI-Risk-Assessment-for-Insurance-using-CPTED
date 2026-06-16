import folium

m = folium.Map(location=[41.9028, 12.4964], zoom_start=12, tiles=None)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri"
).add_to(m)

folium.Marker([41.9028, 12.4964], popup="Roma").add_to(m)
m.save("mappa_satellite_esri.html")