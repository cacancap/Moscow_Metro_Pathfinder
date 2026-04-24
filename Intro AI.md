# Steps

1. **Mô hình hóa bài toán mạng lưới đường sắt (Problem Formulation)**  
- **Trạng thái đầu (Initial state):** Ga tàu mà tác tử (hành khách) bắt đầu xuất phát.  
- **Hàm chuyển trạng thái (Successor function / Actions):** Tập hợp các hành động hợp lệ. Với bài toán tìm đường, nó trả về các cặp `<hành_động, trạng_thái_tiếp_theo>`, ví dụ: đi từ ga hiện tại đến các ga kề nó.  
- **Kiểm tra mục tiêu (Goal test)**: Cách hệ thống xác định xem trạng thái (ga) hiện tại có phải là đích đến hay không.  
- **Chi phí đường đi (Path cost):** Hàm gán chi phí (ví dụ: khoảng cách km hoặc thời gian) cho mỗi con đường

## **1\. Mục tiêu nghiệp vụ (Business Objectives)**

Mục tiêu cốt lõi của hệ thống không chỉ là "tìm thấy đường", mà là **"tối ưu hóa lựa chọn di chuyển"** trong một môi trường biến động.

- **Mục tiêu chính:** Cung cấp lộ trình tối ưu về **khoảng cách di chuyển**  
- **Giá trị đột phá (Real-time AI):** Khả năng **tái lập lộ trình (Dynamic Rerouting)** ngay lập tức khi người dùng giả lập một sự cố (nghẽn tuyến, bảo trì ga). Hệ thống phải trả lời được câu hỏi: *"Nếu tuyến Vòng màu nâu bị đóng, tôi phải đi đường nào để tới Kremlin nhanh nhất?"*  
- **Tính đa mục tiêu:** Hỗ trợ tìm đường qua nhiều điểm dừng (Intermediate stops) mà vẫn đảm bảo tính tối ưu.

## **2\. Cách sử dụng & Tương tác (Usage/User Experience)**

- **Đầu vào (Input):**  
+ Người dùng chọn **Ga đi** và **Ga đến** trực tiếp bằng cách click vào các Node trên bản đồ hoặc tìm kiếm theo tên.  
+ Người dùng có thể thêm các **Ràng buộc** (Constraints): "Tránh tuyến số 5", "Đi qua ga Mayakovskaya".  
- **Xử lý (Processing):** \* Khi có sự thay đổi (thêm điểm dừng hoặc báo sự cố), Backend Python sẽ tính toán lại trong tích tắc.  
- **Đầu ra (Output):**  
+ Lộ trình được vẽ trực quan với các màu sắc tương ứng của các Line tàu tại Moscow.  
+ Bảng tóm tắt: khoảng cách, số lần chuyển tuyến, danh sách các ga đi qua.  
2.  **Lựa chọn và cài đặt "Bộ não AI" (Thuật toán Tìm kiếm)**

## **1\. Chuẩn bị dữ liệu (Data Preparation)**

Làm việc với dữ liệu địa lý như Moscow Metro đòi hỏi sự cẩn trọng để tránh làm hỏng cấu trúc đồ thị.

- Tính toàn vẹn (Data Persistence): Luôn lưu file moscow\_raw.json làm gốc, tạo biến mới là bản sao để tạo tác  
- Tiền xử lý (Cleaning):  
+ Lọc bỏ các nodes không phải là nhà ga.  
+ Tính toán khoảng cách vật lý giữa các ga nối nhau bằng Công thức Haversine (để tính chi phí g(n)).  
- Xử lý tọa độ: Chuyển đổi tọa độ GPS sang một hệ quy chiếu đồng nhất để tính toán hàm Heuristic chính xác.

## **2\. Phát triển thuật toán (Explore Models)**

Mạng lưới đường sắt thực chất là một Đồ thị (Graph). Bạn không nên dùng các thuật toán vét cạn mù quáng mà hãy dùng các giải thuật **Tìm kiếm có tri thức bổ sung (Informed Search)**.  
*(A-star Search)*\* Thuật toán này sẽ đánh giá các ga thông qua hàm *f*(*n*)=*g*(*n*)+*h*(*n*):

- *g*(*n*)**:** Chi phí thực tế (khoảng cách/thời gian) đã đi từ ga xuất phát đến ga hiện tại *n*.  
- *h*(*n*) **(Hàm Heuristic):** Đây là "trí thông minh" của dự án. Bạn có thể dùng *h*(*n*) là **khoảng cách đường chim bay** (Straight-line distance) từ ga hiện tại *n* tới ga đích. Khoảng cách chim bay luôn nhỏ hơn hoặc bằng quãng đường đường sắt thực tế, do đó nó là một "ước lượng chấp nhận được" (Admissible heuristic). Điều này đảm bảo thuật toán A\* của bạn **chắc chắn tìm được đường đi ngắn nhất/tối ưu nhất**.

**Bước 3: Xây dựng Giao diện Web (System Development)**  
**Backend (Xử lý logic):** Dùng ngôn ngữ bạn thạo nhất (Python, Node.js, Java...) để lưu trữ dữ liệu các ga tàu (dưới dạng danh sách kề hoặc ma trận kề) và chạy thuật toán A\*.

**Frontend (Giao diện người dùng):** Bạn có thể tích hợp Google Maps API, OpenStreetMap, hoặc Leaflet.js để vẽ bản đồ trực quan. Người dùng click chọn ga A, ga B, hệ thống gọi API về Backend, lấy chuỗi các ga cần đi qua, và vẽ đường highlight nối các ga đó trên bản đồ Web.

**Lưu ý bắt buộc:** Học phần cho phép bạn sử dụng lại các thư viện bản đồ có sẵn, nhưng bạn **phải ghi rõ ràng và chính xác việc sử dụng các công cụ/gói phần mềm này trong tài liệu báo cáo**

# Data

## [**Link xem giá trị**](http://taginfo.openstreetmap.org/keys/railway)

[**Link lấy data**](https://overpass-turbo.eu/)

## **1\. Nhóm 1: Các "Trạng thái" (Nodes/Stations) \- Cực kỳ quan trọng**

Đây là các đỉnh trong đồ thị của bạn. Người dùng sẽ chọn điểm bắt đầu và kết thúc từ danh sách này.

| Giá trị Railway | Ý nghĩa | Độ ưu tiên |
| :---- | :---- | :---- |
| **station** | Ga tàu chính (Subway, Railway). Đây là các nút giao quan trọng nhất. | **Bắt buộc** |
| **stop** | Điểm dừng (thường dùng cho Tram). | **Cần thiết** (nếu làm cả Tram) |
| **halt** | Điểm dừng nhỏ của tàu hỏa liên tỉnh. | **Cần thiết** |

## **2\. Nhóm 2: Các "Cạnh" (Edges/Tracks) \- Cốt lõi của di chuyển**

Đây là các đường nối giữa các ga. Dựa vào đây bạn sẽ tính chi phí thực tế

* **subway**: Xương sống của Moscow.  
* **rail**: Các tuyến tàu hỏa, Moscow Central Circle (MCC), Moscow Central Diameters (MCD).  
* **tram**: Nếu bạn muốn mạng lưới dày đặc hơn trong nội đô.  
* **light\_rail**: Các tuyến tàu điện nhẹ.  
* **narrow\_gauge**: Tàu khổ hẹp (có thể giữ lại hoặc bỏ tùy quy mô bạn muốn).3

**3\. Phân loại chúng theo các tầng (Layers):**

1. **Layer 1 (Subway/MCC/MCD):** Mạng lưới tốc độ cao, khoảng cách các ga xa.  
2. **Layer 2 (Tram/Light Rail):** Mạng lưới bổ trợ, kết nối các điểm trong nội đô đến Layer 1\.  
3. **Layer 3 (Walking/Transfer):** Các đường nối giữa các ga của các Layer khác nhau.

# Thuật toán

**1\. Nguyên lý kỹ thuật của thuật toán A\***  
Thuật toán A\* là một trong những chiến lược tìm kiếm với tri thức bổ sung (informed/heuristic search) nổi tiếng và được sử dụng rộng rãi nhất. Ý tưởng cốt lõi của A\* là tránh việc phát triển (xét) các nhánh tìm kiếm đã được xác định là có chi phí cao, ưu tiên hướng đi tối ưu nhất.

- Để đánh giá mức độ "phù hợp" của một nút (trạng thái) trong quá trình tìm kiếm, A\* kết hợp hai yếu tố thông qua **hàm đánh giá** *f*(*n*):

*f*(*n*)=*g*(*n*)+*h*(*n*)

Trong đó:

+ *g*(*n*): Là chi phí thực tế của đường đi từ nút trạng thái ban đầu cho đến nút hiện tại *n*.  
+ *h*(*n*): Là hàm heuristic biểu diễn chi phí ước lượng để đi từ nút hiện tại *n* tới nút đích (mục tiêu).  
+ (*n*): Là tổng chi phí ước lượng của đường đi rẻ nhất (tối ưu nhất) đi từ trạng thái bắt đầu, đi qua nút *n*, và tới đích.  
- **Cách thức hoạt động:** Trong quá trình tìm kiếm, thuật toán luôn ưu tiên chọn phát triển nút có giá trị *f*(*n*) thấp nhất (nhỏ nhất) nằm trong tập hợp các nút chưa xét (fringe). Nếu *h*(*n*) thỏa mãn một số điều kiện nhất định, chiến lược này không chỉ hợp lý mà còn đảm bảo tính hoàn chỉnh và tối ưu. So với thuật toán Tìm kiếm chi phí cực tiểu (UCS) thường phát triển theo mọi hướng, A\* sử dụng hàm heuristic để định hướng phát triển chủ yếu về phía đích nhưng vẫn đảm bảo tính tối ưu.

**2\. Đặc điểm lý thuyết của A\***  
Thuật toán A\* được đánh giá qua 4 tiêu chí cơ bản của một giải thuật tìm kiếm:

- **Tính hoàn chỉnh (Completeness):** A\* là một thuật toán hoàn chỉnh. Nó đảm bảo sẽ tìm thấy lời giải nếu lời giải đó tồn tại, ngoại trừ trường hợp có vô hạn các nút có chi phí *f*≤*f*(*G*) (với G là nút đích) hoặc không gian trạng thái là vô hạn.  
- **Tính tối ưu (Optimality):** A\* đảm bảo tìm được lời giải có chi phí thấp nhất (tối ưu) dưới các điều kiện đặc biệt của hàm heuristic *h*(*n*). Về mặt lý thuyết, trong số các thuật toán tìm kiếm tối ưu xuất phát từ nút gốc, A\* là thuật toán đạt hiệu quả tối ưu nhất vì không có thuật toán tối ưu nào khác mở rộng ít nút hơn A\* với cùng một hàm heuristic (ngoại trừ các trường hợp phá vỡ rào cản khi *f*(*n*)=*C*\*).  
- **Độ phức tạp về thời gian (Time Complexity):** Độ phức tạp thời gian của A\* thường ở bậc của hàm mũ, do số lượng các nút được xét là hàm mũ của độ dài đường đi của lời giải. Mức độ phức tạp này phụ thuộc rất lớn vào chất lượng của hàm heuristic.  
- **Độ phức tạp về bộ nhớ (Space Complexity):** Thuật toán A\* lưu giữ tất cả các nút đã được sinh ra trong bộ nhớ. Độ phức tạp bộ nhớ cũng ở mức hàm mũ và đây là nhược điểm lớn nhất của thuật toán này.

**3\. Những điểm quan trọng cần lưu ý (Caveats)**  
Việc thiết kế hàm heuristic *h*(*n*) quyết định sự thành bại của thuật toán A\*. Có hai tính chất cực kỳ quan trọng đối với *h*(*n*):  
**Thứ nhất: Ước lượng chấp nhận được (Admissible Heuristic)**

- Để thuật toán A\* tối ưu khi áp dụng trên **cấu trúc tìm kiếm dạng Cây (TREE-SEARCH)**, hàm *h*(*n*) bắt buộc phải là một "ước lượng chấp nhận được".  
- Một ước lượng là chấp nhận được nếu nó không bao giờ đánh giá cao hơn (overestimate) chi phí thực tế để đi tới đích. Nghĩa là 0≤*h*(*n*)≤*h*\*(*n*), trong đó *h*\*(*n*) là chi phí thật từ *n* đến đích. Về bản chất, hàm heuristic này luôn mang tính "lạc quan" vì nó nghĩ rằng chi phí giải quyết bài toán nhỏ hơn thực tế. Ví dụ kinh điển là việc dùng "khoảng cách đường chim bay" làm *h*(*n*) trong bài toán tìm đường.

**Thứ hai: Ước lượng kiên định / Đơn điệu (Consistent / Monotonic Heuristic)**

- Khi A\* được áp dụng trên **cấu trúc tìm kiếm dạng Đồ thị (GRAPH-SEARCH)** (có cơ chế tránh duyệt lại các trạng thái bị lặp), tính "chấp nhận được" là chưa đủ để đảm bảo tối ưu. Lúc này, *h*(*n*) bắt buộc phải thỏa mãn tính "kiên định" (consistency).  
- Tính kiên định yêu cầu: Với mọi nút *n* và mọi nút tiếp theo *n*′ của *n* (được sinh ra bởi hành động *a*), ta phải có *h*(*n*)≤*c*(*n*,*a*,*n*′)+*h*(*n*′) (trong đó *c* là chi phí bước đi). Đây chính là dạng tổng quát của bất đẳng thức tam giác.  
- Hệ quả quan trọng của tính kiên định là giá trị hàm *f*(*n*) dọc theo bất kỳ con đường nào cũng sẽ luôn tăng dần (không giảm). Nếu *h*(*n*) kiên định, thuật toán A\* sử dụng đồ thị tìm kiếm sẽ chắc chắn tối ưu. (Lưu ý: Mọi heuristic kiên định đều là heuristic chấp nhận được).

**Vấn đề về bộ nhớ (Memory Constraint):**

- Mặc dù A\* rất mạnh, nhưng hạn chế chí mạng của nó không phải là thời gian tính toán mà là bộ nhớ. Vì nó giữ tất cả các nút đã tạo ra trong bộ nhớ, A\* thường "hết bộ nhớ" trước khi "hết thời gian" trong nhiều bài toán thực tế quy mô lớn.  
- Để khắc phục điểm yếu này, người ta thường sử dụng các biến thể của A\* hạn chế bộ nhớ, ví dụ như thuật toán IDA\* (Iterative-deepening A\*) hay RBFS (Recursive best-first search)

