from pathlib import Path
import json
import os
import sys

current_file = Path(__file__).resolve()
current_dir = current_file.parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))
from data.processed.programs.haversine import calculate_haversine_distance



# CHỈ trỏ đến đúng 1 file dữ liệu thô duy nhất
raw_relation_path = project_root / "data" / "raw" / "subway_relation02.geojson"
stop_dict_id_path = project_root / "data" / "processed" / "outputs" / "stop_dict_id.json"
stop_dict_coord_path = project_root / "data" / "processed" / "outputs" / "stop_dict_coord.json"
way_dict_path = project_root / "data" / "processed" / "outputs" / "way_dict_id.json"
station_dict_path = project_root / "data" / "processed" / "outputs" / "station_dict.json"
adjacency_list_path = project_root / "data" / "processed" / "outputs" / "adjacency_list.json"
raw_nodes_edges_path = project_root / "data" / "raw" / "subway_nodes-edges.geojson"

try:
    with open(raw_relation_path, 'r', encoding='utf-8') as f:
        raw_relation_data = json.load(f)
    with open(raw_nodes_edges_path, 'r', encoding='utf-8') as f:
        raw_nodes_edges_data = json.load(f)
    with open(stop_dict_id_path, 'r', encoding='utf-8') as f:
        stop_dict_id = json.load(f)
    with open(stop_dict_coord_path, 'r', encoding='utf-8') as f:
        stop_dict_coord = json.load(f)
    with open(way_dict_path, 'r', encoding='utf-8') as f:
        way_dict_id = json.load(f)
    with open(adjacency_list_path, 'r', encoding='utf-8') as f:
        adjacency_list = json.load(f)
    with open(station_dict_path, 'r', encoding='utf-8') as f:
        station_dict = json.load(f)
except FileNotFoundError as e:
    raise FileNotFoundError(f"Lỗi: Không tìm thấy file: {e}")
    
node_roles = {}

stop_morethan_1relation = []

features01 = raw_relation_data.get('features')
features02 = raw_nodes_edges_data.get('features')

# Từ điển dịch mã HEX sang tên tiếng Anh (nhớ viết thường toàn bộ để dễ so sánh)
HEX_TO_NAME = {
    "#943e90": "violet",
    "#ef161e": "red",
    "#2db45a": "green",
    "#0078d9": "blue",
    "#306fb3": "blue",
    "#894e35": "brown",
    "#ed9121": "orange",
    "#ffc61e": "yellow",
    "#a1a2a3": "grey",
    "#82c0c0": "teal",
    "#99cc00": "lime",
    "#4ac9e3": "light_blue"
    # Bạn có thể print các mã HEX bị lỗi ra và bổ sung thêm vào đây
}

special_stop_colours = {}
special_stop_colours['5330792104'] = 'green'
special_stop_colours['5330792103'] = 'green'



def investigate_node_roles():
    point_count = 0
    way_count = 0
    other_count = 0
    None_list = []
    for feature in features01:
        properties = feature.get('properties')
        raw_id = properties.get('@id')
        clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
        relations = properties.get('@relations')
        
        geom_type = feature.get('geometry').get('type')
        
        if (geom_type == 'Point'):
            pub_trans = properties.get('public_transport')
            railway = properties.get('railway')
            if (node_roles.get(pub_trans) is not None):
                node_roles[pub_trans] += 1
                if (pub_trans == None): None_list.append(clean_id)
                
                if (pub_trans == "stop_position"):
                    relation_count = 0
                    for relation in relations:
                        relation_count += 1
                    if (relation_count > 1):
                        stop_morethan_1relation.append(clean_id)
                
                
                    
            else: node_roles[pub_trans] = 1
    
    for key, value in node_roles.items():
        print(key, ": ", value)

test_list_way01 = [] #ways that first or last point wasn't added to dict 
 
# return a list of ways that have more than 1 relation
def investigate_way():
    way_morethan_1relation = []
    total_way = 0
    railway_types = {}
    for feature in features01:
        properties = feature.get('properties')
        raw_id = properties.get('@id')
        clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
        relations = properties.get('@relations')
        geometry = feature.get('geometry')
        geom_type = geometry.get('type')
        if (geom_type == 'LineString'):
            total_way += 1
            railway = properties.get('railway')
            if (railway != 'subway'): continue
            
            if (railway_types.get(railway) is not None):
                railway_types[railway] += 1
            else: railway_types[railway] = 1
            
            if (len(relations) > 1):
                way_morethan_1relation.append(clean_id)
                print("(way) rel of ", clean_id, ":", end='')
                for relation in relations:
                    ref = relation.get('reltags').get('ref')
                    print(ref, end=' ')
                print()
                
            coords = geometry.get('coordinates')
            first_coord = coords[0]
            last_coord = coords[len(coords) - 1]
            first_key = f"{first_coord[0]},{first_coord[1]}"
            last_key  = f"{last_coord[0]},{last_coord[1]}"
            
            if (stop_dict_coord[first_key] is None or stop_dict_coord[last_key] is None):
                test_list_way01.append(clean_id)
            
    print("Total way: ", total_way)
    print("types: ")
    for key, value in railway_types.items():
        print(key, ": ", value)
    return way_morethan_1relation

def investigate_node_line():
    line_02_list = []
    
    for stop in stop_dict_id.values():
        if (stop.get('line_id') == '2'):
            line_02_list.append(stop.get('id'))
    return line_02_list


if __name__ == "__main__":
    test_string = "orange;violet"
    
    final_colour = test_string.split(';')[0] if ';' in test_string else test_string
    print(final_colour)
