import json
import os

def extract_raw_data(nodes_edges_path, relation_path, output_dir):
    print(f"Loading {nodes_edges_path}...")
    with open(nodes_edges_path, 'r', encoding='utf-8') as f:
        nodes_edges = json.load(f)
    
    print(f"Loading {relation_path}...")
    with open(relation_path, 'r', encoding='utf-8') as f:
        relations = json.load(f)

    stations = []
    stops = []
    tracks = []
    lines = []

    # 1. Trích xuất Stations và Tracks từ subway_nodes-edges.geojson
    for feature in nodes_edges['features']:
        props = feature['properties']
        geom = feature['geometry']
        
        # Trích xuất Stations (Nodes)
        if props.get('railway') == 'station':
            stations.append({
                'id': feature['id'],
                'name_ru': props.get('name:ru') or props.get('name'),
                'name_en': props.get('name:en'),
                'colour': props.get('colour'),
                'coords': geom['coordinates']
            })
            
        # Trích xuất Tracks (Ways)
        elif props.get('railway') == 'subway' and geom['type'] == 'LineString':
            tracks.append({
                'id': feature['id'],
                'name_ru': props.get('name:ru') or props.get('name'),
                'colour': props.get('colour'),
                'oneway': props.get('oneway', 'no'),
                'coords': geom['coordinates']
            })

    # 2. Trích xuất Stops và Line Metadata từ subway_relation_kh.geojson
    for feature in relations['features']:
        props = feature['properties']
        geom = feature['geometry']
        
        # Trích xuất Stops
        if props.get('railway') == 'stop' or props.get('public_transport') == 'stop_position':
            # Lấy màu từ relation đầu tiên trong danh sách @relations
            rel_colour = None
            relations_list = props.get('@relations', [])
            if relations_list:
                rel_colour = relations_list[0].get('reltags', {}).get('colour')

            stops.append({
                'id': feature['id'],
                'name_ru': props.get('name:ru') or props.get('name'),
                'name_en': props.get('name:en'),
                'colour': rel_colour,
                'coords': geom['coordinates']
            })
            
        # Trích xuất Line Metadata (Relations)
        elif props.get('type') == 'route' and props.get('route') == 'subway':
            lines.append({
                'id': feature['id'],
                'name': props.get('name:ru') or props.get('name'),
                'ref': props.get('ref'),
                'colour': props.get('colour'),
                'from': props.get('from'),
                'to': props.get('to')
            })

    # Lưu kết quả
    os.makedirs(output_dir, exist_ok=True)
    
    files = {
        'stations_raw.json': stations,
        'stops_raw.json': stops,
        'tracks_raw.json': tracks,
        'lines_raw.json': lines
    }

    for filename, data in files.items():
        path = os.path.join(output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(data)} items to {path}")

if __name__ == "__main__":
    extract_raw_data(
        'data/raw/subway_nodes-edges.geojson',
        'data/raw/subway_relation_kh.geojson',
        'data/processed/Khanh/01_raw_extracted/'
    )
