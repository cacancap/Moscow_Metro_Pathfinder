from pathlib import Path
import folium
import json

# --- THIẾT LẬP ĐƯỜNG DẪN ĐỘC LẬP ---
current_file = Path(__file__).resolve()
current_dir = current_file.parent
project_root = current_dir.parent.parent.parent

# CHỈ trỏ đến đúng 1 file dữ liệu thô duy nhất
raw_data_path = project_root / "data" / "raw" / "subway_relation02.geojson"
stop_dict_path = project_root / "data" / "processed" / "outputs" / "stop_dict_id.json"
way_dict_path = project_root / "data" / "processed" / "outputs" / "way_dict_id.json"

try:
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    with open(stop_dict_path, 'r', encoding='utf-8') as f:
        stop_dict_id = json.load(f)
    with open(way_dict_path, 'r', encoding='utf-8') as f:
        way_dict_id = json.load(f)
except FileNotFoundError as e:
    raise FileNotFoundError(f"Lỗi: Không tìm thấy file: {e}")

# Khởi tạo bản đồ 
m = folium.Map(location=[55.7394, 37.5348], zoom_start=14)

def visualize_point(lon, lat, colour):
    popup_html = f"coord: {lat}, {lon}"
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=300, parse_html=True),
        icon=folium.Icon(color=colour, icon="star")
    ).add_to(m)

def visualize_node(node_id, colour):
    indicated_node = stop_dict_id[node_id]
    if (indicated_node is None):
        print("Error")
        return
    name = indicated_node.get('name')
    lat = indicated_node.get('lat')
    lon = indicated_node.get('lon')
    
    popup_html = f"<b>Ga:</b> {name}  <b>id: </b> {node_id} <br> {lat}, {lon}" 
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=300, parse_html=True),
        icon=folium.Icon(color=colour, icon="star")
    ).add_to(m)
    
def visualize_way(way_id):
    indicated_way = way_dict_id[way_id]
    if (indicated_way is None):
        print(f"Error: way {way_id} not found!")
        return

    coords = indicated_way.get('geometry')
    colour = indicated_way.get('colour')
    for coord in coords:
        visualize_point(coord[0], coord[1], colour)
    


# --- QUÉT VÀ TRỰC QUAN HÓA TRỰC TIẾP TỪ RAW DATA ---
for feature in geojson_data.get('features', []):
    properties = feature.get('properties', {})
    geometry = feature.get('geometry', {})
    
    if not geometry:
        continue
        
    geom_type = geometry.get('type')
    
    # Chỉ quan tâm đến Đỉnh (Node) và Cạnh (Way)
    if geom_type not in ['Point', 'LineString']:
        continue

    # Lấy thông tin cơ bản nhất có sẵn trong file thô
    raw_id = properties.get('@id', '')
    clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
    name = properties.get('name:en') or properties.get('name', 'N/A')
    relations = properties.get('@relations')
    line_id = properties.get('@relations')[0].get('reltags').get('ref') if (relations != None) else None
    # Nếu file thô có lưu màu sẵn thì dùng, không thì mặc định là màu xanh dương
    item_color = properties.get('colour', 'blue') 

    # 1. TRỰC QUAN ĐỈNH (Nodes)
    if geom_type == 'Point':
        lon, lat = geometry.get('coordinates', [0, 0])
        
        # Xem thuộc tính của điểm này là gì (ga, trạm đệm, điểm chuyển làn...)
        node_type = properties.get('railway', properties.get('highway', 'station'))
        
        # Đổi màu để dễ phân biệt bằng mắt thường
        if node_type == "stop" or node_type == "stop_position": 
            icon_color, radius = "green", 4
        elif node_type == "switch": 
            icon_color, radius = "orange", 4
        elif node_type == "buffer_stop": 
            icon_color, radius = "red", 6
        else: icon_color, radius = "black", 5

        
        popup_html = f"<b>Điểm:</b> {name} - Line: {line_id}<br><b>ID gốc:</b> {clean_id}<br><b>Loại (Tag):</b> {node_type}"
        
        folium.CircleMarker(
            location=[lat, lon], 
            radius=radius,
            popup=folium.Popup(popup_html, max_width=250),
            color=icon_color, 
            fill=True, 
            fill_opacity=0.8
        ).add_to(m)
        
    # 2. TRỰC QUAN CẠNH (Ways)
    elif geom_type == 'LineString':
        coordinates = geometry.get('coordinates', [])
        points = [[lat, lon] for lon, lat in coordinates]
        way_type = properties.get('railway')
        if (way_type != 'subway'): continue
        
        popup_html = f"<b>Đường ray:</b> {name} - Line: {line_id}<br><b>ID:</b> {clean_id}"
        
        folium.PolyLine(
            locations=points,
            popup=folium.Popup(popup_html, max_width=250),
            color=item_color, 
            weight=4, 
            opacity=0.8
        ).add_to(m)

# --- LƯU BẢN ĐỒ ---

stop_morethan_1relation = ['1135674408', '1191237441', '6937381513', '6937381514', '6938823556', '6939665020', '6939665021', '6939665025', '6939665026', '6939665027', '6939665028', '10703951289', '10703951290']
way_morethan_1relation = ['22476058', '23397053', '23397056', '55518853', '80498006', '98150198', '98180700', '98180705', '98180710', '98180712', '98185805', '98185808', '98185812', '98185815', '98185817', '98185819', '98185820', '103150803', '103152210', '103152213', '103152214', '103152215', '134151194', '134151261', '429982492']
for id in way_morethan_1relation:
    visualize_way(id)

output_file = "visualization_output.html"
m.save(output_file)
print("Thành công! Đã vẽ xong dữ liệu thô.")
print(f"Hãy mở file '{output_file}' để xem các nút và đường ray mới.")