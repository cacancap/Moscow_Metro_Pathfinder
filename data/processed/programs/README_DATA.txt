Khảo sát sơ bộ dữ liệu subway_relation02.geojson:

- Tổng số node: 928
    switch :  343
    stop :  544
    buffer_stop :  8
    None :  25
    signal :  4
    railway_crossing :  1
    crossing :  3
- Tổng số way: 749
    subway :  739
    platform :  4
    platform_edge :  6

- Không phải node/way: 213

- Có 13 stops chứa > 1 relation, nhưng một số cái bị lặp lại, có cái thì mang 2 tên tuyến khác nhau (VD: 4 và 4A) 

Update 28/04/2026:
- Sửa lại các stations bị unknown, cập nhật và đồng bộ hoá colour cho stop_dict_id.
- Thay đổi trọng số cho adjacency_list: tính bằng giây thay vì quãng đường, & cập nhật lại trọng số cho một số cạnh đặc biệt.