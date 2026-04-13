import math

def calculate_haversine_distance(lon1, lat1, lon2, lat2):
    """Tính khoảng cách (mét) giữa 2 tọa độ địa lý"""
    R = 6371000  # Bán kính Trái Đất tính bằng mét
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c  # Trả về kết quả bằng mét