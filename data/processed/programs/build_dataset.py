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

if not raw_relation_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {raw_relation_path}")

try:
    with open(raw_relation_path, 'r', encoding='utf-8') as f:
        raw_relation_data = json.load(f)
        
except FileNotFoundError as e:
    print(e)
    
node_roles = {}

stop_morethan_1relation = []

features = raw_relation_data.get('features')
stop_dict_id = {}       # dictionary of stops, index by id
stop_dict_coord = {}    # dictionary of stops, index by coord
way_dict_id = {}        # dictionary of ways, index by id
edge_list = []          # edge connecting 2 adjacent stops
edge_counter = 0
fake_id = 1

# Build a stop_dict_id.json file for indexing stops with id only
def build_stop_dicts():
    for feature in features:
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

def create_edge(source_id, dest_id, weight, line_id, edge_type, colour, geometry):
    global edge_counter
    
    edge_counter += 1
    new_edge = {
        'edge_id': f"e_{edge_counter}",
        'source_id': source_id,
        'dest_id': dest_id,
        'weight': weight,
        'line_id': line_id,
        'edge_type': edge_type,
        'colour': colour,
        'geometry': geometry.copy()
    }
    
    if (new_edge in edge_list):
        print("something went wrong in create_edge!")
        return
    
    edge_list.append(new_edge)
       


# Build the way_dict_id.json file for indexing ways with id only
def build_way_dict():
    
    for feature in features:
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
                    if (prev_node != None and prev_node != cur_node):   # Found a prev node => add 
                        create_edge(prev_node.get('id'), cur_node.get('id'), current_distance, line_id, 'subway', colour, current_geometry)
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
            if (distance < max_distance and (stop_A.get('line_id') != stop_B.get('line_id'))):
                create_edge(stop_A['id'], stop_B['id'], distance + transfer_penalty, 'walk', 'transfer', 'purple', [coord_A, coord_B])
                create_edge(stop_B['id'], stop_A['id'], distance + transfer_penalty, 'walk', 'transfer', 'purple', [coord_B, coord_A])
                transfer_count += 2
    return transfer_count
                    


def investigate_node_roles():
    point_count = 0
    way_count = 0
    other_count = 0
    None_list = []
    for feature in features:
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
    for feature in features:
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
    way_morethan_1relation = investigate_way()
    
    output_path_01 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'stop_dict_id.json'))
    output_path_02 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'stop_dict_coord.json'))
    output_path_03 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'way_dict_id.json'))
    output_path_04 = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'edge_list.json'))
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
    
    print("total transfer: ", transfer_count)