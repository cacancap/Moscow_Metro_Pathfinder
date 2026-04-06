from pathlib import Path
import folium
import os
import json

# --- PHẦN 1: TỌA ĐỘ ĐIỂM BẠN CHO TRƯỚC ---
# Vị trí bạn muốn bản đồ trỏ chính vào (Ví dụ: Trung tâm Moscow)
target = [37.7982815,55.8129175]
target_lat = target[1]
target_lon = target[0]
test_nodeId = 6937381514

# Khởi tạo bản đồ trỏ thẳng vào điểm trên
m = folium.Map(location=[target_lat, target_lon], zoom_start=12)

# Gắn một Marker đặc biệt cho điểm gốc này
folium.Marker(
    location=[target_lat, target_lon],
    popup="<b>ĐIỂM TRỎ</b>",
    icon=folium.Icon(color="red", icon="star")
).add_to(m)

# --- PHẦN 2: ĐỌC VÀ XỬ LÝ FILE GEOJSON ---
current_file = Path(__file__).resolve()
# thư mục chứa file (processed)
current_dir = current_file.parent
project_root = current_dir.parent.parent.parent
# đường dẫn tới file trong raw
raw_data_path = project_root / "data" / "raw" / "subway_nodes-edges.geojson"

# kiểm tra tồn tại
if not raw_data_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {raw_data_path}")

# dùng raw_path.open(...) hoặc str(raw_path) khi cần
with raw_data_path.open('r', encoding='utf-8') as f:
    data = f.read()


try:
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

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

except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file '{raw_data_path}'.")
    print("Hãy đảm bảo file .geojson của bạn nằm cùng thư mục với file Python này.")
except Exception as e:
    print(f"Có lỗi xảy ra trong quá trình xử lý: {e}")