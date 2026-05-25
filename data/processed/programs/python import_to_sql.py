import json
import mysql.connector
from pathlib import Path
import sys

# --- CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "xabialonso123",  # Điền mật khẩu nếu có
    "database": "moscow_metro"
}

# --- ĐƯỜNG DẪN FILE ---
current_dir = Path(__file__).resolve().parent
# Chỉnh lại đường dẫn tới thư mục chứa file json
outputs_dir = current_dir.parent / "outputs"

station_dict_path = outputs_dir / "station_dict.json"
stop_dict_path = outputs_dir / "stop_dict_coord.json"
edge_list_path = outputs_dir / "edge_list.json"


def import_data():
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
        print("✅ Kết nối Database thành công!")

        # ==========================================
        # 1. ĐỌC VÀ IMPORT BẢNG STATIONS
        # ==========================================
        print("\n⏳ Đang xử lý bảng `stations`...")
        with open(station_dict_path, 'r', encoding='utf-8') as f:
            stations_data = json.load(f)

        insert_station_sql = """
            INSERT IGNORE INTO stations (id, name, name_en, colour, line_id, lon, lat) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        station_values = []
        stop_to_station_map = {}  # Dùng để nhớ xem stop nào thuộc station nào

        for st_id, st_info in stations_data.items():
            lon, lat = st_info.get('geometry', [None, None])
            station_values.append((
                st_id, st_info.get('name'), st_info.get('name_en'),
                st_info.get('colour'), str(st_info.get('line_id')), lon, lat
            ))
            # Lưu mapping các stop_id thuộc về station này
            for stop_id in st_info.get('stops', []):
                stop_to_station_map[str(stop_id)] = st_id

        cursor.executemany(insert_station_sql, station_values)
        db.commit()
        print(f"✅ Đã import {cursor.rowcount} ga tổng (stations).")

        # ==========================================
        # 2. ĐỌC VÀ IMPORT BẢNG STOPS (BAO GỒM FAKE NODES)
        # ==========================================
        print("\n⏳ Đang xử lý bảng `stops` (từ file coord)...")
        with open(stop_dict_path, 'r', encoding='utf-8') as f:
            stops_data = json.load(f)

        insert_stop_sql = """
            INSERT IGNORE INTO stops (id, station_id, name, lon, lat, line_id, role, colour) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        stop_values = []
        for coord_key, stop_info in stops_data.items():
            s_id = stop_info.get('id')
            # Tìm xem s_id này có thuộc station nào không, nếu fake node thì sẽ trả về None
            parent_station_id = stop_to_station_map.get(s_id, None)

            stop_values.append((
                s_id, parent_station_id, stop_info.get('name', ''),
                stop_info.get('lon'), stop_info.get('lat'),
                str(stop_info.get('line_id', '')), stop_info.get('role', ''),
                stop_info.get('colour', '')
            ))

        cursor.executemany(insert_stop_sql, stop_values)
        db.commit()
        print(f"✅ Đã import {cursor.rowcount} điểm dừng/fake nodes (stops).")

        # ==========================================
        # 3. ĐỌC VÀ IMPORT BẢNG EDGES & GEOMETRIES
        # ==========================================
        print("\n⏳ Đang xử lý bảng `edges` và `edge_geometries`...")
        with open(edge_list_path, 'r', encoding='utf-8') as f:
            edges_data = json.load(f)

        insert_edge_sql = """
            INSERT IGNORE INTO edges (edge_id, source_id, dest_id, weight, weight_secs, line_id, edge_type, colour) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        insert_geom_sql = """
            INSERT INTO edge_geometries (edge_id, seq_order, lon, lat) 
            VALUES (%s, %s, %s, %s)
        """

        edge_values = []
        geom_values = []

        for edge in edges_data:
            e_id = edge.get('edge_id')
            edge_values.append((
                e_id, edge.get('source_id'), edge.get('dest_id'),
                edge.get('weight', 0.0), edge.get('weight_secs', 0.0),
                str(edge.get('line_id', '')), edge.get('edge_type', ''), edge.get('colour', '')
            ))

            # Xử lý mảng tọa độ geometry
            geometries = edge.get('geometry', [])
            for seq, coord in enumerate(geometries):
                geom_values.append((e_id, seq, coord[0], coord[1]))

        # Chèn Edges trước
        cursor.executemany(insert_edge_sql, edge_values)
        db.commit()
        print(f"✅ Đã import {cursor.rowcount} đoạn ray (edges).")

        # Chèn Geometries sau
        cursor.executemany(insert_geom_sql, geom_values)
        db.commit()
        print(f"✅ Đã import {cursor.rowcount} điểm ảnh tọa độ (geometries).")

    except mysql.connector.Error as err:
        print(f"❌ Lỗi MySQL: {err}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()
            print("\n🔒 Đã ngắt kết nối an toàn.")


if __name__ == "__main__":
    import_data()