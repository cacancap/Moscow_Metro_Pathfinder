from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='.')

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.route('/')
def index():
    return send_from_directory('.', 'map.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith(('.html', '.css', '.js')):
        return send_from_directory('.', filename)
    return send_from_directory('.', filename)

@app.route('/data/processed/Khanh/<path:filepath>')
def serve_data(filepath):
    data_path = os.path.join(PROJECT_ROOT, 'data', 'processed', 'Khanh', filepath)
    return send_from_directory(os.path.dirname(data_path), os.path.basename(data_path))

if __name__ == '__main__':
    print("🗺️ Moscow Metro Pathfinder")
    print("=" * 40)
    print("Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=5000)