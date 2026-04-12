from pathlib import Path
import folium
import os
import json
import numpy as np

current_file = Path(__file__).resolve()
# thư mục chứa file (processed)
current_dir = current_file.parent
project_root = current_dir.parent.parent.parent
# đường dẫn tới file trong raw
raw_data_path = project_root / "data" / "raw" / "subway_nodes-edges.geojson"

if not raw_data_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {raw_data_path}")

try:
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
except FileNotFoundError as e:
    print(e)


# --- PHẦN 1: TỌA ĐỘ ĐIỂM BẠN CHO TRƯỚC ---
# Vị trí bạn muốn bản đồ trỏ chính vào (Ví dụ: Trung tâm Moscow)
targets = [[]]

m = folium.Map(zoom_start=20)

# Nhận vào toạ độ và các thông tin để trực quan
def visualize_point(node_id, node_name_en, node_colour, lat, lon):
    popup_html = f"<b>Ga:</b> {node_name_en} -  <b>id: </b> {node_id} <br> {lat:.6f}, {lon:.6f}"
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=300, parse_html=True),
        icon=folium.Icon(color=node_colour, icon="star")
    ).add_to(m)
    
    
# Trực quan một node - chỉ với node_id
def visualize_node(node_id):
    features = geojson_data.get('features')
    for feature in features:
        geom = feature.get('geometry')
        
        if (geom.get('type') == 'Point'):
            raw_id = feature.get('id')
            clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
            if (clean_id == node_id):
                coord = geom.get('coordinates')
                name_en = feature.get('properties').get('name:en')
                visualize_point(clean_id, name_en, "purple", coord[1], coord[0])
                break
    pass

# Trực quan các toạ độ trong LineString của một way - chỉ với way id
def visualize_way(way_id):
    global m
    features = geojson_data.get('features')
    coords = []
    way_name = ""
    way_colour = ""
    for feature in features:
        props = feature.get('properties')
        raw_id = props.get('@id')
        clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
        way_name = props.get('name')
        way_colour = props.get('colour')
        if (clean_id == way_id):
            coords = feature.get('geometry').get('coordinates')
            break    
    if (len(coords) > 0):
        m = folium.Map(location = [coords[0][1], coords[0][0]] ,zoom_start=12)
    
    for i in range(len(coords)):
        lat_i = coords[i][1]
        lon_i = coords[i][0]
        
        visualize_point(way_id, way_name, way_colour, lat_i, lon_i)
    pass

def visualize_all_stations():
    global m
    count = 0
    features = geojson_data.get('features')
    for feature in features:
        geom = feature.get('geometry')
        if (geom.get('type') == 'Point'):
            props = feature.get('properties')
            raw_node_id = props.get('@id')
            node_name = props.get('name_en')
            coord = geom.get('coordinates')
            
            node_id = raw_node_id.split('/')[-1] if '/' in raw_node_id else raw_node_id
            
            popup_html = f"<b>Ga:</b> {node_name} -  <b>id: </b> {node_id} <br> {coord[1]:.6f}, {coord[0]:.6f}"
            folium.Marker(
                location=[coord[1], coord[0]],
                popup=folium.Popup(popup_html, max_width=300, parse_html=True),
                icon=folium.Icon(color="red", icon="star")
            ).add_to(m)
            count +=1
        
    return count

print(visualize_all_stations())
isolated_nodes_list = ['60660466', '68916801', '241158281', '241158327', '244036228', '253016892', '253016893', '253016894', '253016895', '253017004', '253043175', '253780238', '255744578', '266835845', '266835847', '277499849', '292019726', '292146578', '292148161', '296949274', '296949283', '296953136', '296957241', '296959502', '297291268', '297335182', '309752494', '1890426555', '2080924763', '2525101862', '2525101863', '2692857848', '2692882978', '2692905506', '3224593379', '3943961770', '4006225428', '4737155708', '4737155709', '4737155710', '4847996860', '5202107562', '5202107564', '5202107574', '5202107576', '5436412993', '5436420781', '5868122990', '6560279949', '6560279950', '6560279951', '6939665011', '8581944518', '8581944519', '10702113003', '11171697213', '11171729958', '12157560726']
for i in range(len(isolated_nodes_list)):
    visualize_node(isolated_nodes_list[i])

# Trong GeoJSON, dữ liệu được bọc trong một mảng tên là "features"
for feature in geojson_data.get('features', []):
    properties = feature.get('properties', {})
    geometry = feature.get('geometry', {})
    geom_type = geometry.get('type')

    # Ưu tiên lấy tên tiếng Anh (name:en), nếu không có thì lấy tên gốc (name)
    name = properties.get('name:en') or properties.get('name', 'Chưa xác định')
    
    # Lấy màu sắc từ dữ liệu OSM (nếu có), mặc định là xanh dương/xanh lá
    item_color = properties.get('colour', 'blue') 

    # 1. XỬ LÝ NHÀ GA (Node -> Point)
    if geom_type == 'Point':
        # GeoJSON là [lon, lat]. Phải tách ra để đưa vào Folium là [lat, lon]
        lon, lat = geometry['coordinates']
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=f"<b>Ga:</b> {name}",
            color=item_color,
            fill=True,
            fill_opacity=0.8
        ).add_to(m)

    # 2. XỬ LÝ TUYẾN ĐƯỜNG (Way -> LineString)
    elif geom_type == 'LineString':
        # Geometry chứa danh sách các [lon, lat]. Ta phải dùng vòng lặp để đảo ngược toàn bộ.
        coordinates = geometry['coordinates']
        # Đảo thành [lat, lon]
        points = [[lat, lon] for lon, lat in coordinates]
        
        folium.PolyLine(
            locations=points,
            popup=f"<b>Tuyến:</b> {name}",
            color=item_color,
            weight=5,
            opacity=0.7
        ).add_to(m)


# --- PHẦN 3: LƯU BẢN ĐỒ ---
m.save("trackpoint_output.html")
print("Thành công! Đã xử lý xong file GeoJSON.")
print("Hãy mở file 'trackpoint_output' để xem kết quả.")

