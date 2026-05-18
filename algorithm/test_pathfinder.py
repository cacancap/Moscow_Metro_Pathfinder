"""
Chạy nhanh để kiểm tra BFS, Dijkstra, A* trên dữ liệu thực.
Cách chạy (từ thư mục gốc dự án):
    python -m algorithm.test_pathfinder
"""

import json
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from algorithm.graph import load_graph, filter_graph
from algorithm.pathfinder import find_path

# ── Load dữ liệu ───────────────────────────────────────────────────────────────
graph, nodes = load_graph()

with open(
    os.path.join(os.path.dirname(__file__), "..", "data", "processed", "Khanh",
                 "04_final_output", "station_metadata.json"),
    encoding="utf-8",
) as f:
    meta = json.load(f)

with open(
    os.path.join(os.path.dirname(__file__), "..", "data", "processed", "Khanh",
                 "03_connected_network", "edges_with_hubs.json"),
    encoding="utf-8",
) as f:
    raw_edges = json.load(f)

# line_index : { line_name: set of (source, target) }
line_index: dict = {}
for e in raw_edges:
    line = e.get("line")
    if not line:
        continue
    if line not in line_index:
        line_index[line] = set()
    line_index[line].add((e["source"], e["target"]))


def station_name(node_id):
    name = meta.get(node_id, {}).get("name_en")
    return name if name else node_id


def build_graph(banned_lines: list):
    """Trả về graph đã loại bỏ các cạnh thuộc tuyến bị cấm."""
    excluded = set()
    for l in banned_lines:
        excluded |= line_index.get(l, set())
    return filter_graph(graph, excluded) if excluded else graph


# ── PHẦN 1: Kiểm tra 3 thuật toán ─────────────────────────────────────────────
TEST_CASES = [
    ("node_auto_1",  "node_auto_7"),   # Kurskaya -> Krylatskoye
    ("node_auto_5",  "node_auto_13"),  # Kitay-gorod -> VDNKh
    ("node_auto_9",  "node_auto_15"),  # Sokol -> Alekseyevskaya
]

ALGORITHMS = ["bfs", "dijkstra", "astar"]

print("=" * 70)
print(f"{'PHẦN 1 — SO SÁNH 3 THUẬT TOÁN':^70}")
print("=" * 70)

for start, goal in TEST_CASES:
    print(f"\n[ {station_name(start)}  →  {station_name(goal)} ]")
    print("-" * 70)

    for algo in ALGORITHMS:
        result = find_path(graph, nodes, start, goal, algorithm=algo)
        if result is None:
            print(f"  {algo.upper():10s}  KHÔNG TÌM ĐƯỢC ĐƯỜNG")
            continue

        path_preview = " → ".join(station_name(n) for n in result["path"][:4])
        if len(result["path"]) > 4:
            path_preview += f" → ... (+{len(result['path']) - 4} ga)"

        print(
            f"  {algo.upper():10s}"
            f"  {result['num_stations']:3d} ga"
            f"  {result['distance_km']:6.3f} km"
            f"  {result['elapsed_ms']:7.3f} ms"
            f"  |  {path_preview}"
        )


# ── PHẦN 2: Kiểm tra cấm tuyến ────────────────────────────────────────────────
# Cặp ga cố định để dễ so sánh ảnh hưởng của từng kịch bản cấm
BAN_START, BAN_GOAL = "node_auto_1", "node_auto_3"   # Kurskaya -> Kuntsevskaya

BAN_CASES = [
    ("Không cấm (baseline)",          []),
    ("Cấm Арбатско-Покровская",       ["Арбатско-Покровская линия"]),
    ("Cấm Кольцевая",                 ["Кольцевая линия"]),
    ("Cấm Сокольническая",            ["Сокольническая линия"]),
    ("Cấm АП + Кольцевая",            ["Арбатско-Покровская линия", "Кольцевая линия"]),
    ("Cấm АП + Кольц + Филёвская",    ["Арбатско-Покровская линия", "Кольцевая линия", "Филёвская линия"]),
    ("Cấm 10 tuyến lớn",              [
        "Арбатско-Покровская линия", "Кольцевая линия", "Филёвская линия",
        "Сокольническая линия", "Замоскворецкая линия", "Таганско-Краснопресненская линия",
        "Калужско-Рижская линия", "Серпуховско-Тимирязевская линия",
        "Люблинско-Дмитровская линия", "Большая кольцевая линия",
    ]),
    ("Cấm tất cả 20 tuyến",           list(line_index.keys())),
]

print("\n\n" + "=" * 70)
print(f"{'PHẦN 2 — KIỂM TRA CẤM TUYẾN  (A*)':^70}")
print(f"{'Hành trình: ' + station_name(BAN_START) + ' → ' + station_name(BAN_GOAL):^70}")
print("=" * 70)

baseline_km = None
for label, banned in BAN_CASES:
    active_graph = build_graph(banned)
    result = find_path(active_graph, nodes, BAN_START, BAN_GOAL, algorithm="astar")

    if result is None:
        print(f"  {label:<42s}  ->  KHÔNG TÌM ĐƯỢC ĐƯỜNG")
    else:
        km = result["distance_km"]
        if baseline_km is None:
            baseline_km = km
        delta = f"(+{km - baseline_km:.3f} km)" if km > baseline_km else ""
        print(
            f"  {label:<42s}  ->  {km:6.3f} km"
            f"  {result['num_stations']:3d} nodes"
            f"  {result['elapsed_ms']:6.2f} ms"
            f"  {delta}"
        )

print("\n" + "=" * 70)
print("Kiểm tra hoàn tất.")