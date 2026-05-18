# 1\. Dữ liệu

### ***(Gợi ý được sinh bởi Gemini Pro, chỉ mang tính tham khảo)***

### **Giai đoạn 1: Lọc và Bóc tách dữ liệu (Data Parsing)**

Mục tiêu của bước này là loại bỏ "rác" và chỉ giữ lại mạng lưới tàu điện ngầm. Mặc dù chương trình lõi tìm kiếm sau này có thể tận dụng sức mạnh quản lý bộ nhớ và con trỏ cấp thấp để tối ưu tốc độ duyệt đồ thị, việc xử lý chuỗi JSON thô ban đầu nên được thực hiện bằng một script tự động ngắn gọn (Python là một lựa chọn tuyệt vời nhờ các thư viện hỗ trợ JSON mạnh mẽ).

* **Nhận diện "Đỉnh" (Nodes):** Quét file JSON để tìm các thực thể được gắn thẻ (tags) là trạm tàu điện. Cụ thể, bạn cần lọc các node có thuộc tính `railway=station` và `station=subway`.  
* **Nhận diện "Cạnh" (Ways/Edges):** Tìm các thực thể đại diện cho đường ray nối các ga. Hãy lọc các way có thuộc tính `railway=subway`.  
* **Khớp nối dữ liệu:** Trong OSM, một đoạn đường (Way) chứa danh sách các ID của các trạm (Node) mà nó đi qua. Bạn cần viết logic để liên kết đúng ID của ga với tuyến đường tương ứng.

### **Giai đoạn 2: Thiết kế Cấu trúc Lưu trữ chuẩn hóa**

Dữ liệu thô sau khi lọc cần được định hình lại thành một cấu trúc đồ thị chặt chẽ. Tư duy tổ chức bảng biểu và quan hệ dữ liệu sẽ phát huy tác dụng tối đa ở đây. Tương tự như việc thiết kế các bảng thực thể riêng biệt (như nhân khẩu, căn hộ, hóa đơn) và kết nối chúng qua khóa chính/khóa ngoại, bạn cần cấu trúc đồ thị thành hai tập hợp rõ ràng:

* **Tập hợp Ga tàu (Vertices):** Mỗi ga cần có một ID duy nhất, Tên ga, Tọa độ (Vĩ độ \- Tọa độ X, Kinh độ \- Tọa độ Y), và Tuyến tàu (Color/Line).  
* **Tập hợp Kết nối (Edges):** Lưu trữ thông tin ga A nối với ga B.

### **Giai đoạn 3: Tính toán Trọng số (Weights)**

Thuật toán tìm đường không thể chạy nếu không biết "chi phí" đi từ ga A đến ga B.

* **Tính khoảng cách địa lý:** Lấy tọa độ (Vĩ độ, Kinh độ) của hai ga liền kề đã trích xuất ở Giai đoạn 2, áp dụng công thức toán học **Haversine** để tính ra khoảng cách thực tế (theo đơn vị mét hoặc kilometer).  
* **Cập nhật vào tập hợp Edges:** Gắn giá trị khoảng cách này làm trọng số (weight) cho từng đoạn kết nối.

### **Giai đoạn 4: Đóng gói và Xuất dữ liệu sạch (Export)**

File JSON của OSM ban đầu có thể nặng hàng trăm MB, nhưng sau khi qua 3 bước trên, bạn cần tạo ra một bộ dữ liệu siêu nhẹ và sạch sẽ để Tổ Thuật toán dễ dàng đọc vào bộ nhớ.

* **Định dạng xuất:** Ghi dữ liệu đã xử lý ra định dạng dễ đọc nhất cho chương trình lõi. Có thể là một file JSON cấu trúc mới tối giản, hoặc chia thành 2 file CSV (một file `nodes.csv` và một file `edges.csv`).  
* **Kiểm tra tính toàn vẹn:** Mở file dữ liệu mới ra kiểm tra xem có ga tàu nào bị "cô lập" (không có đường kết nối) do lỗi lọc dữ liệu ở Giai đoạn 1 hay không.

**Nhiệm vụ cụ thể:**

Các bảng cần thiết:

* Nodes.csv: node\_id (PK), name\_en, lat, lon, line\_id (lưu thông tin tuyến), is\_active (dùng cho tính năng cấm đường).  
* Edges.csv: edge\_id (PK), source\_id (FK-\>nodes), target\_id (FK-\>nodes), type, weight, geometry, status (dùng cho cấm đường).  
* Lines.csv: line\_id (PK), colour\_code, is\_operational (dùng cho cấm đường).

Sau khi có các bảng:

- Tạo dictionary (danh sách kề), ví dụ:

  graph \= {

      "Ga\_A": \[

          {"to": "Ga\_B", "weight": 120, "edge\_type": "rail", "line": "M1", "status": "open"},

          {"to": "Ga\_C", "weight": 300, "edge\_type": "transfer", "line": "none", "status": "open"} 

      \],

      "Ga\_B": \[

          {"to": "Ga\_A", "weight": 120, "edge\_type": "rail", "line": "M1", "status": "open"},

          \# ... các đỉnh kề khác của Ga B

      \]

  }


# 2\. Thuật toán

### ***(Gợi ý được sinh bởi Gemini Pro, chỉ mang tính tham khảo)***

### **1\. Nạp dữ liệu và Xây dựng cấu trúc Đồ thị (Graph Construction) (phần này có thể uỷ thác cho nhóm làm Dữ liệu)**

File CSV chỉ là những dòng văn bản vô tri trên ổ cứng. Tổ Thuật toán cần đọc các file này và dựng lại thành một mạng lưới (Đồ thị) sống động bên trong RAM (bộ nhớ trong) của máy tính.

* **Định nghĩa Cấu trúc dữ liệu:** Tạo một struct hoặc class đại diện cho một Ga tàu (Node). Nó sẽ chứa ID, Tên, Tọa độ, và quan trọng nhất là một danh sách các "Ga hàng xóm" (các ga có đường nối trực tiếp).  
* **Danh sách kề (Adjacency List):** Đây là cách lưu đồ thị tối ưu nhất. Thay vì tạo một ma trận khổng lồ chứa toàn bộ các cặp ga (gây lãng phí bộ nhớ), bạn chỉ cần lưu mỗi ga đi kèm với một mảng/danh sách các con trỏ trỏ tới những ga kề cạnh nó, kèm theo trọng số (khoảng cách).  
* **Quản lý bộ nhớ:** Khi cấp phát vùng nhớ cho hàng trăm Node này, hãy chú ý sử dụng con trỏ hợp lý để liên kết chúng với nhau mà không bị rò rỉ bộ nhớ (memory leak).

### **2\. Lập trình thuật toán Cốt lõi (Pathfinding Algorithms)**

Đây là "linh hồn" của môn học. Các bạn không cần phải làm thuật toán khó nhất ngay từ đầu, mà hãy đi theo từng cấp độ:

* **Cấp độ 1 \- Tìm đường ít trạm dừng nhất (BFS \- Breadth-First Search):** Đây là thuật toán cơ bản nhất. Nó sẽ lan tỏa đều ra xung quanh như vết dầu loang để tìm số trạm dừng ít nhất, nhưng nó KHÔNG quan tâm đến khoảng cách thực tế giữa các trạm dài hay ngắn.  
* **Cấp độ 2 \- Tìm đường ngắn nhất (Dijkstra):** Nâng cấp lên thuật toán Dijkstra. Thuật toán này sẽ sử dụng trọng số (khoảng cách) mà nhóm Dữ liệu đã tính toán. Nó ưu tiên duyệt qua những đoạn đường ray ngắn trước, đảm bảo kết quả cuối cùng là quãng đường thực tế ngắn nhất.  
* *Cấp độ 3 \- Thuật toán AI tối ưu (A \- A-star):*\* Đây là mục tiêu "điểm A" của môn học. A\* kết hợp Dijkstra với một "Tri thức bổ sung" (Heuristic) – ví dụ: khoảng cách đường chim bay từ ga hiện tại thẳng đến ga đích. Heuristic này giống như một chiếc la bàn định hướng, giúp thuật toán không bị lan man đi tìm ở những hướng ngược lại với đích đến, từ đó tăng tốc độ tính toán lên gấp nhiều lần.

### **3\. Truy vết đường đi (Path Reconstruction)**

Khi thuật toán chạm tới được Ga Đích, nó mới chỉ biết là "À, đã đến nơi và tổng quãng đường là 15km". Nhưng cái giao diện Web cần hiển thị là một chuỗi các ga cụ thể (Ga A \=\> Ga B \=\> Ga C).

* **Cách làm:** Trong quá trình thuật toán lan tỏa, mỗi khi nó quyết định đi từ ga hiện tại sang một ga mới, nó phải lưu lại "dấu vết" (ví dụ: tạo một mảng came\_from hoặc dùng một con trỏ parent bên trong struct của Node mới, trỏ ngược lại Node hiện tại).  
* Khi chạm tới đích, bạn chỉ cần dùng một vòng lặp while lần ngược theo các con trỏ parent này từ Đích về tới Xuất phát, sau đó đảo ngược mảng lại là sẽ có ngay lộ trình hoàn chỉnh.

### **4\. Đóng gói và Giao tiếp với Web (API / Interface)**

nhóm Thuật toán viết code Python, còn Tổ Web có thể làm giao diện bằng Framework. Hai bên này cần một cách để "nói chuyện" với nhau. Cách đơn giản nhất là:

* Tổ Thuật toán biên dịch đoạn code thành một tệp thực thi (ví dụ: find\_path.exe).  
* Chương trình này nhận 2 tham số đầu vào từ bên ngoài: ID\_Ga\_Di và ID\_Ga\_Den.  
* Sau khi tính toán xong, chương trình không in kết quả ra màn hình đen (Console) mà xuất kết quả (danh sách ID các ga đi qua và tổng quãng đường) ra một file result.json. Tổ Web chỉ việc đọc file JSON này để vẽ đường màu đỏ lên bản đồ.

# 3\. Web\&UI

### ***(Gợi ý được sinh bởi Gemini Pro, chỉ mang tính tham khảo)***

### **Giai đoạn 1: Xây dựng khung giao diện cơ bản (UI Layout)**

Trước khi có bản đồ hay thuật toán, web cần một bộ khung để người dùng tương tác. Streamlit làm việc này rất nhanh chỉ với vài dòng code.

* **Tạo tiêu đề và bố cục:** Dùng `st.title()` để đặt tên dự án (vd: "Mô phỏng Tìm đường Tàu điện ngầm Moscow"). Phân chia màn hình thành 2 cột: một cột nhỏ bên trái (Sidebar) để chọn thông tin, một cột lớn bên phải để hiển thị bản đồ.  
* **Tạo bộ nhập liệu (Input Widgets):** Tổ Web cần tải file `nodes.csv` (mà Tổ Dữ liệu đã làm) vào hệ thống. Sau đó, tạo hai hộp thả xuống (Dropdown/Selectbox) bằng `st.selectbox()`:  
  * Hộp 1: Chọn "Ga xuất phát".  
  * Hộp 2: Chọn "Ga đích đến".  
* **Nút kích hoạt (Button):** Thêm một nút `st.button("Tìm đường")`. Mọi tính toán và vẽ vời trên bản đồ sẽ chỉ bắt đầu chạy khi người dùng bấm vào nút này.

### **Giai đoạn 2: Trực quan hóa Bản đồ (Map Visualization)**

Đây là phần quan trọng và "ăn điểm" nhất của giao diện. Mặc dù Streamlit có sẵn hàm vẽ bản đồ cơ bản, nhưng để hiển thị đẹp mạng lưới tàu điện chằng chịt, các bạn **bắt buộc nên dùng thư viện `Folium`** kết hợp với `streamlit-folium`.

* **Khởi tạo bản đồ nền:** Tạo một bản đồ Folium tập trung góc nhìn (center) vào tọa độ trung tâm của thủ đô Moscow.  
* **Vẽ các điểm Ga (Markers):** Đọc danh sách tọa độ từ file `nodes.csv` và dùng vòng lặp để đính các điểm (marker) lên bản đồ. Mỗi điểm khi click chuột vào sẽ hiện ra tên ga tàu.  
* **Hiển thị giao diện:** Đưa bản đồ Folium này lên trang Streamlit để người dùng có thể phóng to, thu nhỏ và kéo thả tương tác.

### **Giai đoạn 3: Tích hợp với Lõi Thuật toán (Integration)**

Đây là lúc 3 tổ (Dữ liệu, Thuật toán, Web) hợp nhất với nhau. Tổ Web cần biết cách "gọi" phần lõi AI chạy.

* **Nhận dữ liệu đầu vào:** Khi người dùng bấm nút "Tìm đường", Web lấy ID của Ga xuất phát và Ga đích.  
* **Kích hoạt Thuật toán:** \* *Trường hợp 1 (Thuật toán viết bằng Python):* Chỉ cần `import` hàm `find_path(start, end)` của Tổ Thuật toán vào file Streamlit và chạy trực tiếp.  
  * *Trường hợp 2 (Thuật toán viết bằng C++):* Dùng thư viện `subprocess` của Python để gọi file `.exe` chạy ngầm, truyền 2 ID ga vào, sau đó cấu hình để Python đợi file C++ tính xong và nhả ra file `result.json`.  
* **Đọc kết quả:** Web tiến hành đọc mảng kết quả (danh sách ID các ga thuộc lộ trình ngắn nhất) mà thuật toán vừa trả về.

### **Giai đoạn 4: Hiển thị Kết quả và Tối ưu Trải nghiệm**

Khi đã cầm trong tay mảng kết quả, Tổ Web cần vẽ nó lên bản đồ sao cho người dùng dễ hiểu nhất.

* **Vẽ tuyến đường (Polyline):** Dựa vào mảng ID kết quả, lấy tọa độ tương ứng của các ga này và dùng hàm `Polyline` của Folium để vẽ một đường liền nét (ví dụ: màu đỏ, nét đậm) nối các ga lại với nhau đè lên bản đồ gốc.  
* **Hiển thị thông số (Metrics):** Dùng `st.metric()` để in ra màn hình các chỉ số tự hào của dự án:  
  * Tổng khoảng cách lộ trình (bao nhiêu km).  
  * Tổng số ga phải đi qua.  
  * Thời gian thuật toán chạy xong (vd: 0.02 giây \- để khoe tốc độ của thuật toán A\*).

---

### **Gợi ý Phân công cho 2 thành viên Tổ Web:**

* **Thành viên A (Chuyên Giao diện & Bản đồ):** Tập trung nghiên cứu tài liệu của thư viện `Folium`. Chịu trách nhiệm nạp dữ liệu tọa độ để vẽ bản đồ gốc, vẽ các trạm, và vẽ đường thẳng (Polyline) lộ trình.  
* **Thành viên B (Chuyên Logic & Streamlit):** Tập trung làm quen với `Streamlit`. Xây dựng các nút bấm, khung chọn, hàm kết nối với Tổ Thuật toán (viết script chạy C++ nếu cần), và trang trí các bảng thông báo kết quả.

