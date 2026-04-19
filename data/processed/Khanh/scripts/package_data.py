import json
import os

def package_hybrid_data(input_dir, output_dir):
    print(f"Loading data from {input_dir}...")
    with open(os.path.join(input_dir, '03_connected_network/nodes_with_hubs.json'), 'r', encoding='utf-8') as f:
        nodes = json.load(f)
    with open(os.path.join(input_dir, '03_connected_network/edges_with_hubs.json'), 'r', encoding='utf-8') as f:
        edges = json.load(f)

    # 1. Xây dựng Adjacency List cho Thuật toán
    # Cấu trúc: { "nodes": {id: [lon, lat]}, "graph": {id: {neighbor_id: weight}} }
    # Lưu toạ độ nhằm phục vụ A* khi giải thuật
    adj_list = {
        "nodes": {},
        "graph": {}
    }
 
    for node in nodes:
        node_id = node['id']
        adj_list["nodes"][node_id] = node['coords']
        adj_list["graph"][node_id] = {}

    for edge in edges:
        u = edge['source']
        v = edge['target']
        w = edge['weight']
        
        # Chỉ lấy trọng số nhỏ nhất nếu có nhiều cạnh giữa 2 node (ví dụ: nhiều tuyến chạy song song)
        if v not in adj_list["graph"][u] or w < adj_list["graph"][u][v]:
            adj_list["graph"][u][v] = w

    # 2. Xây dựng Metadata cho UI
    # Tập trung vào các ga (stations) và Hubs để hiển thị
    metadata = {}
    for node in nodes:
        if node.get('type') in ['station', 'hub']:
            metadata[node['id']] = {
                'name_ru': node.get('name_ru'),
                'name_en': node.get('name_en'),
                'type': node['type'],
                'coords': node['coords']
            }

    # Bổ sung thông tin màu sắc tuyến vào metadata ga (nếu có)
    for edge in edges:
        if edge.get('type') == 'track' and edge.get('line'):
            u = edge['source']
            if u in metadata:
                if 'lines' not in metadata[u]:
                    metadata[u]['lines'] = []
                line_info = {'name': edge['line'], 'colour': edge.get('colour')}
                if line_info not in metadata[u]['lines']:
                    metadata[u]['lines'].append(line_info)

    # 3. Lưu kết quả
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, '04_final_output/adjacency_list.json'), 'w', encoding='utf-8') as f:
        json.dump(adj_list, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(output_dir, '04_final_output/station_metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Data packaging complete:")
    print(f"- Adjacency List: {len(adj_list['graph'])} nodes indexed")
    print(f"- Station Metadata: {len(metadata)} stations/hubs prepared")
    print(f"- Files saved in: {output_dir}")

if __name__ == "__main__":
    package_hybrid_data(
        'data/processed/Khanh/',
        'data/processed/Khanh/'
    )
