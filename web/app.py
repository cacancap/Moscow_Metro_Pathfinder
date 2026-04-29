from flask import Flask, send_from_directory, jsonify, request
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'map.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith(('.html', '.css', '.js')):
        return send_from_directory('.', filename)
    return send_from_directory('.', filename)

# Serve edge_list.json from parent data directory
@app.route('/api/edge_list')
def get_edge_list():
    edge_list_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   'data', 'processed', 'outputs', 'edge_list.json')
    try:
        with open(edge_list_path, 'r', encoding='utf-8') as f:
            edges = json.load(f)
        return jsonify(edges)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve station_dict.json for station dropdown selection
@app.route('/api/station_list')
def get_station_list():
    station_dict_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                      'data', 'processed', 'outputs', 'station_dict.json')
    try:
        with open(station_dict_path, 'r', encoding='utf-8') as f:
            stations = json.load(f)
        # Convert to list format
        station_list = []
        for station_id, station_data in stations.items():
            station_list.append({
                'id': station_id,
                'name': station_data.get('name', ''),
                'name_en': station_data.get('name_en', ''),
                'colour': station_data.get('colour', ''),
                'line_id': station_data.get('line_id', ''),
                'geometry': station_data.get('geometry', []),
                'stops': station_data.get('stops', [])
            })
        return jsonify(station_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Proxy /api/find-path to root API at localhost:8000
@app.route('/api/find-path', methods=['POST'])
def proxy_find_path():
    api_url = 'http://127.0.0.1:8000/find-path'
    try:
        body = request.get_data()
        request_obj = Request(api_url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        with urlopen(request_obj, timeout=10) as response:
            data = response.read()
            return data, response.getcode(), {'Content-Type': 'application/json'}
    except HTTPError as e:
        return jsonify({'error': f'Root API returned {e.code}: {e.reason}'}), e.code
    except URLError as e:
        return jsonify({'error': f'Cannot reach root API: {e.reason}'}), 502
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🗺️ Moscow Metro Pathfinder - Web Frontend")
    print("=" * 50)
    print("Frontend Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=5000)