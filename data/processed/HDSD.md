# 🚇 Hướng dẫn Sử dụng Bộ Dữ liệu Moscow Metro Pathfinder


## 📁 1. Cấu trúc Tệp Dữ liệu 
Trong cơ sở dữ liệu trước, tôi đã xây dựng bằng các station. Nhưng một nhược điểm chí mạng là toạ độ station không nằm chính xác trên bất cứ LineString nào. Vì vậy, tôi đã sử dụng stop (mỗi station sẽ có 2 stop nằm 2 bên sườn). => Đương nhiên cách này cũng có nhược điểm  

Toàn bộ dữ liệu đã được làm sạch nằm trong thư mục `outputs/`. Các tệp quan trọng nhất bao gồm:

* **`adjacency_list.json`**: (⭐ **QUAN TRỌNG NHẤT**) Từ điển kề được thiết kế tối ưu $O(1)$ cho thuật toán tìm đường.
* **`stop_dict_id.json`**: Từ điển tra cứu nhanh thông tin chi tiết của một nhà ga dựa vào `node_id`.
* **`stop_dict_coord.json`**: Từ điển tra cứu thông tin của một stop dựa vào `coord`.
* **`way_dict_id.json`**: Từ điển tra cứu thông tin của một way dựa vào `way_id`.
* **`station_dict.json`**: Từ điển tra cứu station.
* **`edge_list.json`**: List các edge lưu thông tin về cạnh nối các đỉnh kề nhau.
---

## 📊 2. Lược đồ Dữ liệu  


### 2.1. Cấu trúc Từ điển kề (`adjacency_list.json`) 
File này tổ chức theo dạng `Dictionary của Dictionary` để truy xuất siêu tốc: `adj_map[source_id][dest_id]`.

| Thuộc tính | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `source_id` | `String` | Khóa chính cấp 1: ID của stop xuất phát. |
| `dest_id` | `String` | Khóa chính cấp 2: ID của stop đích đến liền kề. |
| `edge_id` | `String` | ID tự sinh của đoạn đường (VD: `e_124`). |
| `weight` | `Float` | **Trọng số cốt lõi (Đang lưu ở dạng quãng đường).** |
| `edge_type` | `String` | `subway` hoặc `transfer` (Đi bộ đổi tuyến). |
| `line_id` | `String` | Số hiệu/Tên tuyến (VD: `3`, `6`, hoặc `walk`). Dùng để UI tô màu hoặc Thuật toán lọc tuyến. |
| `colour` | `String` | Màu hex hoặc tên màu chuẩn của tuyến từ OSM. |
| `geometry` | `Array` | Mảng chứa các tọa độ `[Lon, Lat]` mô tả chính xác đường cong của đoạn ray. |

### 2.2. Cấu trúc ánh xạ `station -> stop`
Vì adjacency_list chỉ lưu các edges theo id của stop, mà yêu cầu là tra cứu theo id của station => cần làm từ điển station
Ví dụ json: 


```json
{
  "60660466": {
    "name": "Медведково",
    "name_en": "Medvedkovo",
    "colour": "orange",
    "line_id": "6",
    "geometry": [
      37.66155,
      55.8871767
    ],
    "stops": [
      "6938090606",
      "6938090607"
    ]
  }
}
```

=> Từ điển lưu id các ga, bên trong có chứa các stops (nằm 2 bên sườn) của nó
=> Đối với thuật toán tìm đường, chỉ cần lấy phần tử đầu tiên trong stops là ngon luôn.

## 3. Lưu ý

- Về bộ dữ liệu gốc: Một số way/stop có nhiều hơn một `relation` (chỉ với các tuyến như 4&4A, 8&8A, ...). Để dễ hiểu thì `relation` giúp xác định way/stop đó thuộc line nào. Nhưng trong trường hợp một way/stop dùng cho nhiều hơn một `line`, tôi đã "tham lam" lấy `line` đầu tiên được lưu. Điều này có ảnh hưởng đôi chút, đặc biệt là thuật toán tạo cạnh đi bộ.

**Ví dụ JSON:**
```json
"242546357": {
  "fake/172": {
    "edge_id": "e_202",
    "weight": 101.2,
    "edge_type": "subway",
    "line_id": "3",
    "colour": "blue",
    "geometry": [[37.658, 55.758], [37.656, 55.757]]
  }
}