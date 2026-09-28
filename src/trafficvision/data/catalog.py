"""Vietnamese 82-class traffic sign catalog according to star092304/Traffic-sign-detection-VietNam."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignClass:
    """Represents a traffic sign category in the Vietnamese catalog."""

    id: int
    code: str
    name_vi: str
    category: str

    @property
    def name_en(self) -> str:
        """Alias for English code name."""
        return self.code


VIETNAM_TRAFFIC_SIGN_CATALOG: list[SignClass] = [
    SignClass(0, "No Entry", "Cấm đi ngược chiều", "cấm"),
    SignClass(1, "Turn Right Only", "Đi về bên phải", "hiệu lệnh"),
    SignClass(2, "Speed limit 40hm/h", "Giới hạn tốc độ 40km/h", "cấm"),
    SignClass(3, "No Trucks and Bus", "Cấm xe tải và buýt", "cấm"),
    SignClass(4, "No Trucks", "Cấm xe tải", "cấm"),
    SignClass(5, "Low Clearance", "Cảnh báo giới hạn chiều cao", "cảnh báo"),
    SignClass(6, "No Cars", "Cấm ô tô", "cấm"),
    SignClass(7, "Danger", "Cảnh báo nguy hiểm", "nguy hiểm"),
    SignClass(8, "Slown Down", "Giảm tốc độ", "cảnh báo"),
    SignClass(9, "Double curve first to right", "Nhiều chỗ ngoặc liên tiếp", "nguy hiểm"),
    SignClass(10, "Obstacle on the Road", "Cảnh báo chướng ngại vật phía trước", "cảnh báo"),
    SignClass(11, "Road with Surveillance Camera", "Đường có camera giám sát", "chỉ dẫn"),
    SignClass(12, "Speed limit 60hm/h", "Giới hạn tốc độ 60km/h", "cấm"),
    SignClass(13, "No Moto", "Cấm mô tô xe máy", "cấm"),
    SignClass(14, "Lane Allocation", "Biển phân làn", "hiệu lệnh"),
    SignClass(15, "Height Limit", "Biển Cấm Hạn chế chiều cao", "cấm"),
    SignClass(16, "No Horns", "Cấm còi", "cấm"),
    SignClass(17, "No Left Turn", "Cấm rẽ trái", "cấm"),
    SignClass(18, "No Right Turn", "Cấm rẽ phải", "cấm"),
    SignClass(19, "No U-Turn", "Cấm quay đầu", "cấm"),
    SignClass(20, "No U-Turn and No Left Turn", "Cấm quay đầu và rẽ trái", "cấm"),
    SignClass(21, "No U-Turn and No Right Turn", "Cấm quay đầu và rẽ phải", "cấm"),
    SignClass(22, "Traffic light ahead", "Giao nhau với đèn giao thông", "cảnh báo"),
    SignClass(23, "No Stopping & No Parking", "Cấm dừng đỗ xe", "cấm"),
    SignClass(24, "No Parking", "Cấm đỗ xe", "cấm"),
    SignClass(25, "No Straight and Right Turn", "Cấm đi thẳng và rẽ phải", "cấm"),
    SignClass(26, "No Left or Right Turn", "Cấm rẽ trái và phải", "cấm"),
    SignClass(27, "Sharp Left Turn", "Cua gấp trái", "nguy hiểm"),
    SignClass(28, "Sharp Right Turn", "Cua gấp phải", "nguy hiểm"),
    SignClass(29, "Intersection with a Minor Road", "Giao nhau với đường không ưu tiên", "cảnh báo"),
    SignClass(30, "Intersection with Equal Roads", "Giao nhau cùng cấp", "cảnh báo"),
    SignClass(31, "No Moto Turn Left", "Cấm xe máy rẽ trái", "cấm"),
    SignClass(32, "Intersection with a Priority Road", "Giao nhau với đường ưu tiên", "chỉ dẫn"),
    SignClass(33, "Pedestrian Lane", "Đường dành cho người đi bộ", "hiệu lệnh"),
    SignClass(34, "Narrow Road Left Side", "Đường hẹp bên trái", "cảnh báo"),
    SignClass(35, "Narrow Road Right Side", "Đường hẹp bên phải", "cảnh báo"),
    SignClass(36, "Narrow road both sides", "Đường hẹp hai bên", "cảnh báo"),
    SignClass(37, "No Two or Three-wheeled Vehicles", "Cấm xe hai và ba bánh", "cấm"),
    SignClass(38, "Speed Bump", "Đoạn đường có gờ giảm tốc", "cảnh báo"),
    SignClass(39, "Speed limit 50hm/h", "Giới hạn tốc độ 50km/h", "cấm"),
    SignClass(40, "Speed limit 70hm/h", "Giới hạn tốc độ 70km/h", "cấm"),
    SignClass(41, "Speed limit 80hm/h", "Giới hạn tốc độ 80km/h", "cấm"),
    SignClass(42, "Level Crossing with Barriers", "Giao nhau với đường sắt có rào chắn", "cảnh báo"),
    SignClass(43, "No U-Turn for Cars", "Cấm ô tô quay đầu", "cấm"),
    SignClass(44, "No bus", "Cấm xe buýt", "cấm"),
    SignClass(45, "No Overtaking", "Cấm vượt", "cấm"),
    SignClass(46, "Children Crossing", "Cảnh báo Khu vực có trẻ em", "cảnh báo"),
    SignClass(47, "Pedestrian Crossing", "Cảnh báo Người đi bộ cắt ngang", "cảnh báo"),
    SignClass(48, "End of all prohibition", "Hết tất cả các lệnh cấm", "hiệu lệnh"),
    SignClass(49, "Keep left", "Đi về bên trái", "hiệu lệnh"),
    SignClass(50, "Road Work Ahead", "Công trường đang thi công", "cảnh báo"),
    SignClass(51, "One way street", "Đường một chiều", "chỉ dẫn"),
    SignClass(52, "Turn Left", "Rẽ trái", "hiệu lệnh"),
    SignClass(53, "Turn Right", "Rẽ phải", "hiệu lệnh"),
    SignClass(54, "Green Light", "Đèn xanh", "tín hiệu"),
    SignClass(55, "Red Light", "Đèn đỏ", "tín hiệu"),
    SignClass(56, "Roundabout", "Đi theo vòng xuyến", "hiệu lệnh"),
    SignClass(57, "Speed limit 10km/h", "Giới hạn tốc độ 10km/h", "cấm"),
    SignClass(58, "Speed limit 100km/h", "Giới hạn tốc độ 100km/h", "cấm"),
    SignClass(59, "Speed limit 110km/h", "Giới hạn tốc độ 110km/h", "cấm"),
    SignClass(60, "Speed limit 120km/h", "Giới hạn tốc độ 120km/h", "cấm"),
    SignClass(61, "Speed limit 20km/h", "Giới hạn tốc độ 20km/h", "cấm"),
    SignClass(62, "Speed limit 30km/h", "Giới hạn tốc độ 30km/h", "cấm"),
    SignClass(63, "Speed limit 90km/h", "Giới hạn tốc độ 90km/h", "cấm"),
    SignClass(64, "Stop", "Dừng lại", "cấm"),
    SignClass(65, "U-Turn Area", "Nơi quay đầu xe", "chỉ dẫn"),
    SignClass(66, "No Parking on Odd Days", "Cấm đỗ xe vào ngày lẻ", "cấm"),
    SignClass(67, "No Parking on Even Days", "Cấm đỗ xe vào ngày chẵn", "cấm"),
    SignClass(68, "Parking", "Chỗ đỗ xe", "chỉ dẫn"),
    SignClass(69, "Bus Stop", "Bến xe buýt", "chỉ dẫn"),
    SignClass(70, "Hospital", "Bệnh viện", "chỉ dẫn"),
    SignClass(71, "No U-Turn and Left Turn for Cars", "Cấm ô tô quay đầu và rẽ trái", "cấm"),
    SignClass(72, "Accident area", "Đoạn đường hay xảy ra tai nạn", "cảnh báo"),
    SignClass(73, "Dual carriageway", "Đường đôi", "chỉ dẫn"),
    SignClass(74, "No left turn for cars", "Cấm ô tô rẽ trái", "cấm"),
    SignClass(75, "Steep ascent", "Lên dốc nguy hiểm", "nguy hiểm"),
    SignClass(76, "Narrow bridge", "Cầu hẹp", "cảnh báo"),
    SignClass(77, "Uneven road", "Đường không bằng phẳng", "cảnh báo"),
    SignClass(78, "End of 50km/h speed limit", "Hết giới hạn tốc độ 50km/h", "hiệu lệnh"),
    SignClass(79, "Residential area", "Khu dân cư", "chỉ dẫn"),
    SignClass(80, "sparsely populated area", "Khu ít dân cư", "chỉ dẫn"),
    SignClass(81, "Slippery Road", "Đường trơn", "cảnh báo"),
]

_CATALOG_BY_ID: dict[int, SignClass] = {sc.id: sc for sc in VIETNAM_TRAFFIC_SIGN_CATALOG}
_CATALOG_BY_CODE: dict[str, SignClass] = {sc.code: sc for sc in VIETNAM_TRAFFIC_SIGN_CATALOG}


def get_class_names() -> list[str]:
    """Return ordered list of 82 Vietnamese sign names (index = class_id)."""
    return [sc.name_vi for sc in VIETNAM_TRAFFIC_SIGN_CATALOG]


def get_catalog_by_id(class_id: int) -> SignClass:
    """Retrieve SignClass by its 0-based integer ID."""
    if class_id not in _CATALOG_BY_ID:
        raise ValueError(f"Unknown traffic sign class_id: {class_id}. Must be in 0..81.")
    return _CATALOG_BY_ID[class_id]


def get_catalog_by_code(code: str) -> SignClass:
    """Retrieve SignClass by its unique English code/name."""
    if code not in _CATALOG_BY_CODE:
        raise ValueError(f"Unknown traffic sign code: '{code}'.")
    return _CATALOG_BY_CODE[code]


def get_catalog_dict() -> dict[int, str]:
    """Return mapping of class_id to Vietnamese name."""
    return {sc.id: sc.name_vi for sc in VIETNAM_TRAFFIC_SIGN_CATALOG}
