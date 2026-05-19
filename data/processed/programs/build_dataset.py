from pathlib import Path
import json
import os
from haversine import calculate_haversine_distance

current_file = Path(__file__).resolve()
# thư mục chứa file (processed)
current_dir = current_file.parent
project_root = current_dir.parent.parent.parent
# đường dẫn tới file trong raw
raw_relation_path = project_root / "data" / "raw" / "subway_relation02.geojson"
raw_nodes_edges_path = project_root / "data" / "raw" / "subway_nodes-edges.geojson"

if not raw_relation_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {raw_relation_path}")
if not raw_nodes_edges_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {raw_nodes_edges_path}")

try:
    with open(raw_relation_path, 'r', encoding='utf-8') as f:
        raw_relation_data = json.load(f)
    with open(raw_nodes_edges_path, 'r', encoding='utf-8') as f:
        raw_nodes_edges_data = json.load(f)
except FileNotFoundError as e:
    print(e)
    
node_roles = {}

stop_morethan_1relation = []

features01 = raw_relation_data.get('features')
features02 = raw_nodes_edges_data.get('features')
stop_dict_id = {}       # dictionary of stops, index by id
stop_dict_coord = {}    # dictionary of stops, index by coord
way_dict_id = {}        # dictionary of ways, index by id
edge_list = []          # edge connecting 2 adjacent stops
station_dict = {}       # stations containing essential information: stop belonging to, line_id ...
edge_counter = 0
fake_id = 1
unknown_stations = []

# Từ điển dịch mã HEX sang tên tiếng Anh (nhớ viết thường toàn bộ để dễ so sánh)
HEX_TO_NAME = {
    "#943e90": "violet",
    "#ffcbdb": "lightpink",
    "#ef161e": "red",
    "#2db45a": "green",
    "#b4d445": "lightgreen",
    "#0078d9": "blue",
    "#306fb3": "blue",
    "#894e35": "brown",
    "#ed9121": "orange",
    "#ffc61e": "yellow",
    "#a1a2a3": "grey",
    "#82c0c0": "teal",
    "#99cc00": "lime",
    "#4ac9e3": "lightblue"
    # Bạn có thể print các mã HEX bị lỗi ra và bổ sung thêm vào đây
}

special_stop_colours = {}
special_stop_colours['5330792104'] = 'green'
special_stop_colours['5330792103'] = 'green'
special_stop_colours['6938823577'] = 'red'
special_stop_colours['6938823578'] = 'red'

# Build a stop_dict_id.json file for indexing stops with id only
def build_stop_dicts():
    for feature in features01:
        properties = feature.get('properties')
        raw_id = properties.get('@id')
        clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
        relations = properties.get('@relations')
        pub_trans = properties.get('public_transport')
        geom = feature.get('geometry')
        geom_type = geom.get('type')

        # Meet a stop
        if (geom_type == 'Point' and pub_trans == 'stop_position'):
            lon, lat = geom.get('coordinates')
            name = properties.get('name')
            
            line_id = relations[0].get('reltags').get('ref')
            
            stop_dict_id[clean_id] = {
                'id': clean_id,
                'name': name,
                'lon': lon,
                'lat': lat,
                'line_id': line_id,
                'role': 'stop' 
            }
            
            coord_id = f"{lon},{lat}"
            stop_dict_coord[coord_id] = {
                'id': clean_id,
                'name': name,
                'lon': lon,
                'lat': lat,
                'line_id': line_id,
                'role': 'stop'
            }
        
            
# Creating an edge
# Cần cải tiến: vừa đọc, vừa ghi từ điển chứ không nên build dict sau edge_list
def create_edge(source_id, dest_id, weight, line_id, edge_type, colour, geometry):
    global edge_counter
    
    new_edge = {
        'edge_id': f"e_{edge_counter}",
        'source_id': source_id,
        'dest_id': dest_id,
        'weight': round(weight, 2),
        'line_id': line_id,
        'edge_type': edge_type,
        'colour': colour,
        'geometry': geometry.copy()
    }
    
    if (new_edge in edge_list):
        print("something went wrong in creat_edge!")
        return
    
    edge_list.append(new_edge)
    edge_counter += 1       


# Build the way_dict_id.json file for indexing ways with id only
def build_way_dict():
    
    for feature in features01:
        properties = feature.get('properties')
        raw_id = properties.get('@id')
        clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
        relations = properties.get('@relations')
        pub_trans = properties.get('public_transport')
        geom = feature.get('geometry')
        geom_type = geom.get('type')

        if (geom_type == 'LineString'):
            railway = properties.get('railway')
            
            if (railway != 'subway'): continue
            
            coords = geom.get('coordinates')
            line_id = relations[0].get('reltags').get('ref')
            colour = properties.get('colour')
            name = properties.get('name')
            way_dict_id[clean_id] = {
                'id': clean_id, 
                'name': name,
                'colour': colour,
                'line_id': line_id,
                'geometry': coords
            }
            
            # Create fake node (in the first and last element of LineString): 
            first_coord = coords[0]
            last_coord = coords[len(coords) - 1]
            
            first_key = f"{first_coord[0]},{first_coord[1]}"
            last_key = f"{last_coord[0]},{last_coord[1]}"
            
            global fake_id
            
            
            if (stop_dict_coord.get(first_key) is None):
                stop_dict_coord[first_key] = {
                    'id': f"fake/{fake_id}",
                    'name': name,
                    'lon': first_coord[0],
                    'lat': first_coord[1],
                    'line_id': line_id,
                    'role': 'temp' # this attribute is for differentiating with official stop node
                }
                
                fake_id += 1
            
            if (stop_dict_coord.get(last_key) is None):
                stop_dict_coord[last_key] = {
                    'id': f"fake/{fake_id}",
                    'name': name,
                    'lon': last_coord[0],
                    'lat': last_coord[1],
                    'line_id': line_id,
                    'role': 'temp' # this attribute is for differentiating with official stop node
                }
                
                fake_id += 1
                
            prev_node = None
            cur_node = None
            current_geometry = []
            current_distance = 0
            for i in range(len(coords)):
                cur_coord = coords[i]
                prev_coord = coords[i - 1] if i > 0 else None
                current_geometry.append(cur_coord)
                cur_key = f"{cur_coord[0]},{cur_coord[1]}"
                
                # update cur distance 
                if (prev_coord != None): current_distance += calculate_haversine_distance(prev_coord[0], prev_coord[1], cur_coord[0], cur_coord[1])
                
                if (stop_dict_coord.get(cur_key) != None):  # Found a node
                    cur_node = stop_dict_coord[cur_key]
                    
                    cur_node['colour'] = colour 
                    # Cập nhật màu cho từ điển id (chỉ node thật mới có trong này)
                    if cur_node['id'] in stop_dict_id:
                        if (cur_node['id'] in special_stop_colours.keys()):
                            stop_dict_id[cur_node['id']]['colour'] = special_stop_colours[cur_node['id']]
                        
                        else: stop_dict_id[cur_node['id']]['colour'] = colour

                    if (prev_node != None and prev_node != cur_node):   # Found a prev node => add 
                        create_edge(prev_node.get('id'), cur_node.get('id'), current_distance / 40000 * 3600, line_id, 'subway', colour, current_geometry)
                        current_geometry = [cur_coord]
                        current_distance = 0
                    
                    prev_node = cur_node
                    cur_node = None
                    
# clustering: create walkways for transferring line       
def stop_clustering(max_distance, transfer_penalty):
    transfer_count = 0
    stop_list = list(stop_dict_id.values())
    
    for i in range(len(stop_list)):
        for j in range(i + 1, len(stop_list)):
            stop_A = stop_list[i]
            stop_B = stop_list[j]
            coord_A = [stop_A.get('lon'), stop_A.get('lat')]
            coord_B = [stop_B.get('lon'), stop_B.get('lat')]
            
            
            distance = calculate_haversine_distance(coord_A[0], coord_A[1], coord_B[0], coord_B[1])
            weight_secs = distance / 40000 * 3600
            # if (distance < max_distance and (f"{stop_A.get('name')},{stop_A.get('colour')}" == f"{stop_B.get('name')}"))
            
            if (distance < max_distance):
                if (stop_A.get('name') == stop_B.get('name') and stop_A.get('colour') == stop_B.get('colour')):
                    create_edge(stop_A['id'], stop_B['id'], 0, 'walk', 'swap', 'black', [coord_A, coord_B])
                    create_edge(stop_B['id'], stop_A['id'], 0, 'walk', 'swap', 'black', [coord_B, coord_A])
                else:
                    create_edge(stop_A['id'], stop_B['id'], weight_secs * 20, 'walk', 'transfer', 'purple', [coord_A, coord_B])
                    create_edge(stop_B['id'], stop_A['id'], weight_secs * 20, 'walk', 'transfer', 'purple', [coord_B, coord_A])
                transfer_count += 2
            
    return transfer_count
                    
def fix_bad_stop_data():
    for stop in stop_dict_id.values():
        if (stop.get('line_id') == '2'): stop['colour'] = 'green'    
        elif (stop.get('line_id') == '15'): stop['colour'] = 'lightpink'        
        
def build_station_dict():
    # features02 là dữ liệu từ file subway_nodes-edges.geojson (chứa Ga - Point)
    count_station = 0
    for feature in features02:
        properties = feature.get('properties', {})
        geom = feature.get('geometry', {})
        geom_type = geom.get('type')
        
        # Chỉ lấy các Point là Ga tàu (station)
        if geom_type == 'Point' and (properties.get('station') == 'subway' or properties.get('railway') == 'station'):
            count_station += 1
            raw_id = feature.get('id', '')
            clean_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id
            
            name = properties.get('name', '')
            name_en = properties.get('name:en', '')
            raw_colour = properties.get('colour', '')
            colour = raw_colour.split(';')[0] if ';' in raw_colour else raw_colour
            lon, lat = geom.get('coordinates', [0, 0])
            
            
            matched_stops = []
            line_ids = set() # Dùng set để tránh trùng lặp nếu có nhiều stop cùng line
            
            # --- LOGIC GOM STOP VỀ STATION ---
            # Quét toàn bộ stops, nếu trùng Tên và Màu thì stop đó thuộc về Ga này
            
            if (name == 'Селигерская'): print('found01: ', clean_id, colour)
            
            
            for stop_id, stop_data in stop_dict_id.items():
                
                
                raw_stop_colour = str(stop_data.get('colour', '')).lower()
                raw_station_colour = str(colour).lower()

                # Nếu màu là mã HEX, tra từ điển. Nếu không có trong từ điển, giữ nguyên màu gốc.
                normalized_stop_colour = HEX_TO_NAME.get(raw_stop_colour, raw_stop_colour)
                normalized_station_colour = HEX_TO_NAME.get(raw_station_colour, raw_station_colour)
                
                # if (name == 'Селигерская' and stop_data.get('name') == 'Селигерская'):
                #     print('found2: ', stop_id, normalized_stop_colour, '=>', normalized_station_colour)
                
                if str(stop_data.get('name', '')).lower() == str(name).lower() and normalized_stop_colour == normalized_station_colour:
                    matched_stops.append(stop_id)
                    
                    # Trích xuất line_id từ stop (vì stop được lấy từ relation nên line_id rất chuẩn)
                    if stop_data.get('line_id') and stop_data.get('line_id') != 'unknown':
                        line_ids.add(stop_data.get('line_id'))
            
            # Chuẩn hóa line_id (nếu 1 ga phục vụ nhiều tuyến cùng màu - hiếm, nhưng set() sẽ gom thành list)
            
            
            final_line_id = list(line_ids)[0] if len(line_ids) == 1 else list(line_ids) if len(line_ids) > 1 else 'unknown'
            
            if (final_line_id == 'unknown'):
                unknown_stations.append(clean_id)
            
            station_data = {
                'name': name,
                'name_en': name_en,
                'colour': colour,
                'line_id': final_line_id,
                'geometry': [lon, lat],
                'stops': matched_stops
            }
            
            station_dict[clean_id] = station_data
    print("total stations: ", count_station)




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


if __name__ == "__main__":
    build_stop_dicts()
    build_way_dict()
    transfer_count = stop_clustering(200, 500)
    fix_bad_stop_data()
    build_station_dict()
    
    output_path_01 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'stop_dict_id.json'))
    output_path_02 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'stop_dict_coord.json'))
    output_path_03 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'way_dict_id.json'))
    output_path_04 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'edge_list.json'))
    output_path_05 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'station_dict.json'))
    
    with open(output_path_01, 'w', encoding='utf-8') as outfile:
        json.dump(stop_dict_id, outfile, ensure_ascii=False, indent=2)
    print(f"\nĐã xuất dữ liệu thành công ra file: {output_path_01}")
    
    with open(output_path_02, 'w', encoding='utf-8') as outfile:
        json.dump(stop_dict_coord, outfile, ensure_ascii=False, indent=2)
    print(f"\nĐã xuất dữ liệu thành công ra file: {output_path_02}")
    
    with open(output_path_03, 'w', encoding='utf-8') as outfile:
        json.dump(way_dict_id, outfile, ensure_ascii=False, indent=2)
    print(f"\nĐã xuất dữ liệu thành công ra file: {output_path_03}")
    
    with open(output_path_04, 'w', encoding='utf-8') as outfile:
        json.dump(edge_list, outfile, ensure_ascii=False, indent=2)
    print(f"\nĐã xuất dữ liệu thành công ra file: {output_path_04}")
    
    with open(output_path_05, 'w', encoding='utf-8') as outfile:
        json.dump(station_dict, outfile, ensure_ascii=False, indent=2)
    print(f"\nĐã xuất dữ liệu thành công ra file: {output_path_05}")
    
    print("unknown stations: ", len(unknown_stations))
