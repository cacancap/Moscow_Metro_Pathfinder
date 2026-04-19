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
adjacent_list_path = project_root / "data" / "processed" / "outputs" / "adjacency_list.json"
graph_data_path = project_root / "data" / "processed" / "outputs" / "clean_graph02.json"
way_line_path = project_root / "data" / "processed"  / "outputs" / "way_to_line.json"

if not raw_data_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {raw_data_path}")

if not adjacent_list_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {adjacent_list_path}")

if not graph_data_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {graph_data_path}")

if not way_line_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {way_line_path}")


try:
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    with open(graph_data_path, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)   
    with open(adjacent_list_path, 'r', encoding='utf-8') as adjacent_file:
        adjacency_list = json.load(adjacent_file)    
    with open(way_line_path, 'r', encoding='utf-8') as f:
        way_line_mapping = json.load(f)
except FileNotFoundError as e:
    print(e)


# --- PHẦN 1: TỌA ĐỘ ĐIỂM BẠN CHO TRƯỚC ---
# Vị trí bạn muốn bản đồ trỏ chính vào (Ví dụ: Trung tâm Moscow)
targets = [[]]
node_list = graph_data.get('nodes')
node_dict = {}

for node in node_list:
    node_dict[node.get('node_id')] = node
    
m = folium.Map(location=[55.6595519, 37.417239], zoom_start=12)

# Nhận vào toạ độ và các thông tin để trực quan
def visualize_point(node_id, node_name_en, node_colour, lat, lon):
    target_node = node_dict.get(node_id)
    
    line_id = target_node.get('line_id') if target_node is not None else None
    
    popup_html = f"<b>Ga:</b> {node_name_en} - Line:{line_id} <b>id: </b> {node_id} <br> {lat:.6f}, {lon:.6f}" if target_node is not None else f"<b>Ga:</b> {node_name_en} <b>id: </b> {node_id} <br> {lat:.6f}, {lon:.6f}" 
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=300, parse_html=True),
        icon=folium.Icon(color=node_colour, icon="star")
    ).add_to(m)
    
def visualize_point_coord(lat, lon, node_colour):
    
    popup_html = f"<b>Ga:</b>  - Line: <b>id: </b>  <br> {lat:.6f}, {lon:.6f}" 
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

def visualize_node(node_id, color):
    features = geojson_data.get('features')
    for feature in features:
        geom = feature.get('geometry')
        
        if (geom.get('type') == 'Point'):
            raw_id = feature.get('id')
            clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
            if (clean_id == node_id):
                coord = geom.get('coordinates')
                name_en = feature.get('properties').get('name:en')
                visualize_point(clean_id, name_en, color, coord[1], coord[0])
                break
    pass

# Trực quan các toạ độ trong LineString của một way - chỉ với way id
def visualize_way(way_id):
    
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

# Trực quan các lân cận của một node
def visualize_node_neighbors(node_id):
    

    
    neighbors = adjacency_list[node_id]
    print("neighbors of ", node_id, ': ')
    visualize_node(node_id, "orange")
    for key, value in neighbors.items():
        print(key)
        visualize_node(key, "green")

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
            color = props.get('colour', 'black')
            node_id = raw_node_id.split('/')[-1] if '/' in raw_node_id else raw_node_id
            
            popup_html = f"<b>Ga:</b> {node_name} -  <b>id: </b> {node_id} <br> {coord[1]:.6f}, {coord[0]:.6f}"
            folium.Marker(
                location=[coord[1], coord[0]],
                popup=folium.Popup(popup_html, max_width=300, parse_html=True),
                icon=folium.Icon(color=color, icon="star")
            ).add_to(m)
            count +=1
        
    return count

isolated_nodes_list = ['60660466', '68916801', '253016895', '253017004', '253043175', '253780238', '292019726', '292146578', '292148161', '296949283', '297291268', '1890426555', '2080924763', '2692857848', '5202107564', '5868122990', '6560279949', '6560279950', '6560279951', '8581944518', '8581944519', '11171697213', '11171729958', '12157560726']
test_edges = ['22476058', '22745717', '23387050', '23387051', '23397053', '23397056', '23398510', '23398511', '23402746', '23427086']
for i in range(len(isolated_nodes_list)):
    visualize_node(isolated_nodes_list[i], "purple")

# Duyệt toàn bộ geojson
for feature in geojson_data.get('features', []):
    properties = feature.get('properties', {})
    geometry = feature.get('geometry', {})
    geom_type = geometry.get('type')
    raw_id = properties.get('@id')
    clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
    # Ưu tiên lấy tên tiếng Anh (name:en), nếu không có thì lấy tên gốc (name)
    name = properties.get('name:en') or properties.get('name', 'Chưa xác định')
    
    # Lấy màu sắc từ dữ liệu OSM (nếu có), mặc định là xanh dương/xanh lá
    item_color = properties.get('colour', 'blue') 

    # 1. XỬ LÝ NHÀ GA (Node -> Point)
    if geom_type == 'Point':
        # GeoJSON là [lon, lat]. Phải tách ra để đưa vào Folium là [lat, lon]
        lon, lat = geometry['coordinates']
        line_id = node_dict[clean_id].get("line_id")
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=f"<b>Ga:</b> {name} - {clean_id} - Line ID: {line_id}",
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
        line_id = way_line_mapping.get(clean_id) if way_line_mapping.get(clean_id) is not None else None
        folium.PolyLine(
            locations=points,
            popup=f"<b>Tuyến:</b> {name} - way_id: {clean_id} - line_id: {line_id}",
            color=item_color,
            weight=5,
            opacity=0.7
        ).add_to(m)


# --- PHẦN 3: LƯU BẢN ĐỒ ---

for edge_id in test_edges:
    visualize_way(edge_id)

m.save("trackpoint_output.html")
print("Thành công! Đã xử lý xong file GeoJSON.")
print("Hãy mở file 'trackpoint_output' để xem kết quả.")
print("test line_id of node: ", node_dict.get('292143796').get('line_id'))

