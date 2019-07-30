import folium
import polyline


def zoom_and_center(path):
    center =((path[0][0]+path[-1][0])/2,(path[0][1]+path[-1][1])/2)
    dist =abs(path[0][0]-path[-1][0])+abs(path[0][1]-path[-1][1])
    print(dist)
    
    if dist < 0.05:
        zoom = 14
    elif dist < 0.1:
        zoom = 13
    elif dist < 0.25:
        zoom = 12
    else:
        zoom = 11
        
    return center, zoom



def generate_map(poly):
    path = polyline.decode(poly)
    center, zoom = zoom_and_center(path)
    m = folium.Map(location=center,zoom_start=zoom)
    folium.Marker(path[0], popup='<i>Start</i>', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(path[-1], popup='<i>Stop</i>', tooltip="stop",icon=folium.Icon(color='red')).add_to(m)
    folium.PolyLine(path, color="red", weight=2.5, opacity=1).add_to(m)
    m.save('./app/static/map.html')