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

m = folium.Map(zoom_start=12)

# Trực quan các toạ độ trong LineString của một way - chỉ với way id
def visualize_way(way_id):
    global m
    features = geojson_data.get('features')
    coords = []
    
    for feature in features:
        raw_id = feature.get('properties').get('@id')
        clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
        
        if (clean_id == way_id):
            coords = feature.get('geometry').get('coordinates')
            break    
    if (len(coords) > 0):
        m = folium.Map(location = [coords[0][1], coords[0][0]] ,zoom_start=12)
    
    for i in range(len(coords)):
        lat_i = coords[i][1]
        lon_i = coords[i][0]
        
        popup_html = f"<b>Ga:</b> {lat_i:.6f}, {lon_i:.6f}"
        folium.Marker(
            location=[lat_i, lon_i],
            popup=folium.Popup(popup_html, max_width=300, parse_html=True),
            icon=folium.Icon(color="red", icon="star")
        ).add_to(m)
    pass

visualize_way("22476058")

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

