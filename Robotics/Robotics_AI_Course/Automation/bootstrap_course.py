"""Khởi tạo một lần; không ghi đè tài liệu đã có. Không dùng để tiếp tục khóa học."""
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def put(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        f.write(text.strip() + '\n')

def slug(text):
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return ''.join(c if c not in '\\/:*?"<>|' else '-' for c in text)

# Mỗi dòng là một kết quả học tập độc lập: tên bài | sản phẩm hoặc phép kiểm chứng.
MODULES = [
('Điện tử từ số 0', 'A', '''Điện là gì và mạch kín đầu tiên|Quan sát đèn pin dùng AA và lập bảng bật tắt
Điện áp và cực tính|Đọc nhãn nguồn và so sánh điện áp định mức của thiết bị
Dòng điện và đường đi của điện|Vẽ đường dòng điện quy ước trong mạch kín
Điện trở và định luật Ohm|Tính dòng qua tải điện trở ở ba mức điện áp
Công suất và năng lượng|Tính công suất tải và phân biệt W với Wh
GND và mốc điện áp chung|Dùng mô hình hai thước đo để giải thích common ground
Mạch nối tiếp và song song|So sánh dòng và điện áp qua hai cách mắc trên giấy
DC AC và mức 3.3V 5V|Phân loại nguồn và nhận ra tín hiệu 5V không mặc nhiên hợp GPIO 3.3V
Điện trở LED và diode|Xác định chiều LED và tính điện trở hạn dòng trước khi đấu
Tụ điện transistor và MOSFET|Giải thích tích trữ điện và công tắc điện tử bằng sơ đồ khối'''),
('Dụng cụ và phép đo đầu tiên', 'B', '''Breadboard và jumper wire|Lập bản đồ các hàng nối bên trong breadboard chưa cấp nguồn
Multimeter continuity và điện trở|Đo điện trở rời và kiểm chứng các hàng breadboard không cấp điện
Đo điện áp DC an toàn|Đo pin AA bằng cổng COM và V rồi ghi cực tính
Nguồn giới hạn dòng và mạch LED đầu tiên|Đấu LED với điện trở đã tính và đo điện áp trên từng phần
Dây điện đầu nối và bàn thao tác|Tuốt dây bấm cos nhận dạng JST và làm mối nối có co nhiệt'''),
('Hàn mạch từ đầu', 'C', '''An toàn mỏ hàn flux và tinning|Tráng thiếc dây luyện tập trên bàn hàn có thông gió
Hàn pin header resistor và LED|Hàn một mạch mẫu rồi kiểm tra khi chưa cấp nguồn
Hàn dây và connector|Tạo mối nối có giữ dây và thử kéo nhẹ khi đã nguội
Cold joint solder bridge và tháo hàn|Sửa mối hàn mẫu bằng flux dây hút và bơm hút thiếc
Board perfboard hoàn chỉnh|Hoàn thiện đèn báo nguồn và hồ sơ continuity trước cấp điện'''),
('Đọc bảng mạch và tài liệu', 'D', '''Symbol schematic và wiring diagram|Đổi một mạch LED giữa sơ đồ nguyên lý và bảng đấu dây
PCB trace pad via và connector|Lần đường dẫn trên board đã tháo nguồn bằng kính và continuity
Pinout và datasheet|Tách absolute maximum khỏi điều kiện vận hành của linh kiện
Block diagram và reference design|Lần nguồn từ đầu vào đến bộ ổn áp trên schematic thật
Chọn và lập hồ sơ board ESP32-S3|Ghi đúng hãng revision module bộ nhớ pinout và chân bị dành riêng'''),
('ESP32 và embedded C C++', 'E', '''ESP32 CPU RAM Flash và PSRAM|So sánh tài nguyên ESP32-S3 với Arduino STM32 và Pico
Firmware Arduino framework và nạp chương trình|Cài môi trường được chốt phiên bản và đọc Serial đầu tiên
C C++ biến kiểu dữ liệu và toán tử|In giá trị đo giả lập và quan sát tràn số có kiểm soát
Điều kiện vòng lặp và hàm|Tách một chương trình đọc trạng thái thành hàm nhỏ
GPIO HIGH LOW và đầu ra LED|Điều khiển LED ngoài theo pin map đã xác minh
Button pull-up pull-down và debounce|PROJECT 01 LED và button với trạng thái nhấn ổn định
ADC potentiometer và sai số đo|So điện áp đồng hồ với ADC trên cùng điểm đo
PWM và độ sáng LED|Quan sát duty cycle và phân biệt PWM với điện áp analog thật
Timer millis và lập lịch không chặn|Cho hai tác vụ chạy cùng lúc mà không dùng delay dài
Interrupt và dữ liệu chia sẻ|Đếm sự kiện chậm và chuyển xử lý ra khỏi ISR
Mảng chuỗi struct và quản lý bộ nhớ|Đóng gói mẫu đo tránh vượt mảng và tránh cấp phát tùy tiện
State machine và mini control panel|PROJECT 02 bảng điều khiển với nút chiết áp LED và log lỗi'''),
('Giao thức có thực hành phần cứng', 'F', '''UART baud rate và khung dữ liệu|Dùng USB UART logic 3.3V nhận gửi gói có ký tự kết thúc
I2C địa chỉ pull-up và bus scan|Đọc thanh ghi từ cảm biến I2C breakout có mức điện áp rõ
SPI clock chip select và mode|Giao tiếp một màn hình SPI 3.3V và kiểm tra thứ tự dây
I2S clock slot và mẫu số|Nhận mẫu thô từ INMP441 và quan sát im lặng so với tiếng vỗ
CAN transceiver termination và lỗi bus|Truyền một frame giữa hai node thật trên bus có hai đầu kết thúc'''),
('Cảm biến và độ tin cậy phép đo', 'G', '''Touch TTP223 và cảm biến ánh sáng|So ngưỡng nhận sự kiện với ảnh hưởng ánh sáng môi trường
Ultrasonic và chuyển mức tín hiệu|Đo khoảng cách và giải thích vì sao Echo 5V cần bảo vệ đầu vào
ToF VL53L0X và trạng thái phép đo|So khoảng cách với thước và loại mẫu báo lỗi
IMU accelerometer và gyroscope|Ghi dữ liệu đứng yên quay nghiêng để tách gia tốc và tốc độ góc
Magnetometer nhiệt độ và hiệu chuẩn|So nhiễu từ gần motor tắt nguồn với một vùng thoáng
Encoder xung hướng và chống mất đếm|Quay encoder bằng tay để kiểm tra quadrature và interrupt
Distance alarm có lọc nhiễu|PROJECT 05 cảnh báo bằng LED khi có vật gần và phát hiện sensor lỗi'''),
('Nguồn điện trước khi chạy động cơ', 'J', '''Power budget và dòng đỉnh|Lập bảng tải liên tục khởi động và biên dự phòng của robot
USB regulator buck boost và buck-boost|Chọn kiểu biến đổi nguồn từ khoảng điện áp đầu vào đầu ra
Đo buck và phân phối nguồn|Chỉnh bộ nguồn khi tách tải rồi đo lại với tải điện trở
Li-ion LiPo pack bảo vệ và BMS|Đọc nhãn pack thương mại và phân biệt BMS với bộ sạc
Charging fuse công tắc và bảo vệ cực tính|Vẽ đường nguồn có cầu chì và bộ sạc đúng loại pack
Decoupling grounding và motor noise|Đo dấu hiệu sụt nguồn tải biến thiên trên bộ nguồn giới hạn dòng
Brownout và ngân sách năng lượng thực tế|Hoàn thành power harness và quy trình cắt nguồn an toàn'''),
('Cơ khí và prototype', 'K', '''Torque RPM và hộp số|Tính yêu cầu mô-men sơ bộ từ tải và bán kính bánh
Bánh xe trọng tâm và differential drive hình học|Lắp mô hình giấy để dự đoán hướng quay của robot hai bánh
Ốc M2 M3 standoff bearing và shaft|Lắp cụm cơ khí không rơ và không cọ dây
CAD cơ bản với Onshape hoặc Fusion|Vẽ một giá đỡ có kích thước và lỗ bắt vít
3D printing dung sai và hướng in|In hoặc đặt in mẫu thử lỗ trước khi in toàn bộ vỏ
Thiết kế vỏ và bảo trì|Tạo bố trí có thông gió tiếp cận công tắc và tháo pin thuận tiện'''),
('Bộ truyền động và điều khiển công suất', 'H', '''RGB WS2812 và buzzer|Tạo phản hồi có giới hạn độ sáng và mức logic phù hợp
Servo nguồn riêng và servo horn|Điều khiển SG90 trong dải cơ khí đã kiểm tra không kẹt
Servo creature và tay máy một khớp|PROJECT 03 sinh vật servo có giới hạn chuyển động
Motor DC gear motor H-bridge và driver|Chọn driver theo dòng stall và giải thích không nối motor vào GPIO
TB6612FNG chiều quay phanh và dừng|Chạy motor trên giá với STBY và nguồn được bảo vệ
Stepper driver và giới hạn dòng|Chạy stepper nhỏ không tháo dây khi đang cấp điện
Encoder motor và lớp driver|Ghép lệnh tốc độ với số xung đo được chưa đóng vòng PID'''),
('Robot hai bánh', 'I', '''Lắp chassis bánh caster và dây nguồn|Hoàn thiện base có nút ngắt công suất dễ tiếp cận
Robot hai bánh chạy trên giá|PROJECT 06 chạy từng bánh đúng chiều trước khi hạ xuống sàn
Tốc độ rẽ và vùng thử an toàn|Đo quãng đường đi chậm và dừng theo lệnh
Robot tránh vật cản|PROJECT 07 máy trạng thái tiến dừng quay có timeout cảm biến
Line follower và ngưỡng cảm biến|Theo vạch ở tốc độ thấp với xử lý mất vạch
Robot encoder và đo quãng đường|PROJECT 08 hiệu chuẩn số xung trên một vòng bánh
Pose odometry và sai số trượt bánh|Tính x y góc từ hai encoder trong đơn vị SI
Heartbeat watchdog và lỗi mất lệnh|Robot tự dừng khi ngắt liên lạc hoặc reset bộ điều khiển'''),
('Màn hình và tương tác', 'L', '''OLED SSD1306 LCD và bố cục trạng thái|Hiển thị chữ số đo và phân biệt giao tiếp với nội dung màn hình
Robot eyes animation và thời gian|Tạo chớp mắt không chặn vòng điều khiển
OLED robot face|PROJECT 04 khuôn mặt biểu thị trạng thái thực của robot
HRI personality và phản hồi dễ hiểu|Thiết kế nút dừng đèn mic camera và âm báo không gây hiểu lầm'''),
('Mạng cho robot', 'N', '''Wi-Fi STA AP IP TCP và UDP|Kết nối mạng thử nghiệm và ghi độ trễ mất gói
HTTP REST JSON và kiểm tra dữ liệu|Gửi telemetry và từ chối lệnh thiếu trường hay ngoài giới hạn
WebSocket và điều khiển điện thoại|PROJECT 09 giao diện web với deadman timeout
MQTT topic QoS và retained message|Đo hành vi mất mạng và tránh lệnh motor retained nguy hiểm
Wi-Fi provisioning TLS và API key|Cấu hình mạng không để bí mật trong kho mã hay Serial công khai
OTA và phục hồi firmware|Thử cập nhật rollback trên board đứng yên đã ngắt nguồn motor'''),
('Âm thanh robot', 'M', '''Âm thanh PCM sample rate và bit depth|Tính dung lượng và thời gian của bản thu mono
INMP441 thu âm I2S hoàn chỉnh|Lưu mẫu đúng slot định dạng và phát hiện clipping
MAX98357A amplifier và speaker|Phát âm mẫu với loa phù hợp không nối đầu loa về GND
Record playback và bộ đệm|Phát lại tiếng nói ngắn không tràn buffer
Noise echo và bố trí microphone|So bản ghi trước sau thay bố trí mic loa và nguồn
VAD và trạng thái đang nói|Đo false trigger từ tiếng quạt và tiếng gõ bàn
Wake word và quyền riêng tư|Bật nghe chủ động bằng từ khóa với nút mute vật lý phù hợp'''),
('Raspberry Pi Linux và Python', 'O', '''Chọn Pi edge computer và cài Linux|Chốt OS nguồn lưu trữ tản nhiệt có tương thích phần mềm
Terminal filesystem SSH và cập nhật|Quản lý tập tin và đăng nhập SSH bằng khóa trên mạng riêng
Python hàm module venv và lỗi|Đọc file mẫu đo xử lý ngoại lệ và viết một module nhỏ
Pi và ESP32 qua serial|Truyền gói có sequence checksum và timeout cho controller
Process service và network bridge|Chạy chương trình tự khởi động có restart giới hạn và log
Camera audio và kiểm tra tài nguyên Pi|Đo CPU RAM nhiệt độ độ trễ khi camera và audio cùng chạy'''),
('Computer vision', 'P', '''Pixel RGB resolution và tốc độ khung hình|Đọc ảnh và giải thích chi phí tăng độ phân giải
Camera robot và OpenCV|PROJECT 13 hiển thị khung hình có chỉ báo camera
Threshold contour và feature|Tìm vật màu có thước kiểm chứng dưới hai nguồn sáng
Camera calibration và méo ảnh|Chụp bảng chuẩn lưu ma trận camera và đánh giá sai số
Neural network inference và edge AI|Chạy model có phiên bản rõ đo latency RAM và điều kiện ánh sáng
Object detection robot|PROJECT 14 phản ứng với nhãn đủ tin cậy trong vùng cho phép
Object tracking và mất dấu|Theo object ID và xử lý che khuất không nhầm với nhận danh tính
Depth sensor và đổi tọa độ|So depth với khoảng cách thật và chuyển điểm sang khung robot'''),
('Voice AI và người đang nói', 'Q', '''ASR STT và lệnh tiếng Việt|PROJECT 10 nhận câu lệnh vào tập ý định giới hạn có xác nhận phù hợp
TTS và Talking Robot|PROJECT 11 robot đọc câu trả lời và cho phép ngắt lời
Speaker verification và speaker identification|Tách ai nói khỏi nói gì và đo tỷ lệ chấp nhận sai từ mẫu có consent
Speaker-aware robot|PROJECT 15 hồ sơ người nói có unknown từ chối và xóa dữ liệu
Diarization chồng tiếng và giới hạn nhận biết|Phân đoạn lượt nói và phân biệt nhãn speaker với định danh thật'''),
('AI architecture và tools', 'R', '''LLM AI API và system prompt|Tạo hội thoại có thông báo giới hạn và giữ khóa ở backend
Structured output function calling và safety layer|Kiểm tra schema allowlist biên tốc độ trước khi thực thi lệnh
ESP32 AI Voice Robot|PROJECT 12 tích hợp voice backend và đánh giá Xiaozhi ESP32 theo board thật
Realtime streaming audio và latency|Đo thời gian nghe phản hồi ngắt lời và hồi phục mất mạng
Context memory và personality có kiểm soát|Lưu điều được phép nhớ có thời hạn nút xem và xóa
MCP và công cụ có quyền hạn|Dùng một tool đọc trạng thái rồi tool được phép có kiểm tra đầu vào
High-level planning và tách realtime control|Mô phỏng AI ra lệnh sai và chứng minh firmware từ chối
AI education robot|PROJECT 19 kịch bản STEM có người lớn giám sát và quyền riêng tư trẻ em'''),
('Điều khiển phản hồi', 'S', '''Feedback closed loop và sai số|So điều khiển hở với phản hồi dưới tải thay đổi
PID rời rạc và chu kỳ lấy mẫu|Tính P I D từ dữ liệu mẫu và quan sát ảnh hưởng dt
PID tốc độ motor với encoder|Tune từ P thấp trên giá có giới hạn dòng và tốc độ
Anti-windup lọc đạo hàm và saturation|Gây giới hạn có kiểm soát rồi đo hồi phục không tích lũy quá mức
Heading IMU và sensor fusion|Kết hợp gyro với tham chiếu phù hợp và so drift
Odometry hợp nhất và kiểm thử quỹ đạo|Chạy đường vuông chậm báo sai số thay vì tuyên bố vị trí tuyệt đối'''),
('ROS 2', 'T', '''ROS 2 kiến trúc và chọn distribution|Chốt ROS OS driver đã xác minh bằng ma trận tương thích
Node topic message và QoS|Tạo hai node Python trao đổi sensor có timestamp
Service action và hủy tác vụ|So truy vấn ngắn với mục tiêu dài có cancel
Coordinate frame TF và thời gian|Kiểm tra cây map odom base_link sensor không có vòng
URDF joint và RViz|Hiển thị mô hình base và cảm biến ở đúng vị trí
rosbag và chẩn đoán dữ liệu|Ghi phát lại phiên chạy thử không phát lệnh motor ngoài ý muốn
Sensor và motor controller integration|Bridge ESP32 tới ROS với watchdog độc lập
ROS 2 Mobile Robot|PROJECT 17 điều khiển base có telemetry TF và hủy lệnh an toàn'''),
('Robot tự hành trong nhà', 'U', '''LiDAR depth và phát hiện vật cản|So góc chết kính vật thấp và vùng mù của từng sensor
Occupancy grid mapping và costmap|Đọc ô chưa biết trống có vật và lớp khoảng cách an toàn
SLAM và mapping robot|PROJECT 16 tạo bản đồ phòng bằng sensor phù hợp có đánh giá loop closure
Localization pose và độ bất định|Định vị lại trên bản đồ và phát hiện mất localization
Global path planning|Tìm đường trên grid và giải thích đường hợp lệ với footprint
Local planning và vật cản động|Giảm tốc dừng và replanning khi người đi qua vùng thử
Nav2 lifecycle behavior tree và recovery|Cấu hình stack phù hợp phiên bản và thử hủy goal
Indoor autonomous robot|PROJECT 18 đi A đến B trong vùng kiểm soát có log thất bại
Nhiều phòng điểm nghỉ và giới hạn tự chủ|Lập route phòng với geofence và quay về điểm nghỉ không mặc định tự sạc'''),
('PCB thực dụng với KiCad', 'W', '''KiCad schematic capture và ERC|Vẽ board giao tiếp nguồn logic connector theo thiết kế đã chạy
Footprint connector và mounting hole|In tỷ lệ 1-1 kiểm tra chân linh kiện và lỗ gá
PCB layout power trace signal và ground|Tách đường dòng motor khỏi tín hiệu nhỏ theo đường hồi dòng
DRC Gerber và rà soát sản xuất|Xuất bộ hồ sơ đối chiếu footprint và quy tắc nhà gia công
Bring-up PCB prototype|Kiểm tra không nguồn rồi cấp nguồn giới hạn dòng từng khối'''),
('Reliability safety và production thinking', 'X', '''Fail-safe emergency stop và watchdog độc lập|Lập ma trận lỗi và đo thời gian cắt chuyển động
Overcurrent thermal battery và child safety|Kiểm tra nhiệt dòng giữ dây cạnh sắc theo điều kiện thử đã giới hạn
Privacy camera mic và local cloud|Kiểm tra mute chỉ báo consent retention và xóa dữ liệu thực
Network security API keys và cập nhật|Kiểm tra quyền tối thiểu bí mật log và hồi phục update lỗi
Test plan BOM phiên bản và production thinking|Lập hồ sơ nghiệm thu hồi quy và thay linh kiện có truy vết'''),
('Final Home AI Companion Robot', 'V', '''Capstone yêu cầu kiến trúc và ngân sách|PROJECT 20 chọn cấu hình tối thiểu đáp ứng toàn bộ tiêu chí cốt lõi
Tích hợp base ESP32 và compute|Kiểm thử đường lệnh telemetry E-stop và watchdog từ đầu đến cuối
Tích hợp camera voice và speaker consent|Đo tài nguyên độ trễ nhận lệnh object detection và chế độ unknown
Tích hợp navigation và AI tools|Đi tới vị trí hợp lệ qua tool có kiểm tra safety và quyền hạn
Fault injection và nghiệm thu trong nhà|Thử mất Wi-Fi sensor lỗi AI sai localization mất và pin yếu trong vùng thử
Bàn giao demo và hướng phát triển robot mới|Hoàn tất hồ sơ capstone giới hạn đã đo và chọn kiến trúc cho robot tiếp theo''')]

rows = []
modules = []
for mi, (name, original, raw) in enumerate(MODULES, 1):
    start = len(rows) + 1
    for line in raw.splitlines():
        title, outcome = line.split('|')
        num = len(rows) + 1
        stem = f'Bai {num:03d} - {slug(title)}'
        rows.append(dict(number=num, module=mi, title=title, outcome=outcome, stem=stem,
                         path=f'Lessons/Part_{mi:02d}/{stem}.md', prerequisites=[num-1] if num > 1 else []))
    modules.append(dict(number=mi, name=name, original=original, start=start, end=len(rows)))
    (ROOT / f'Lessons/Part_{mi:02d}').mkdir(parents=True, exist_ok=True)
assert len(rows) == 160
for directory in ('Checkpoints', 'Projects', 'Reference', 'Automation/Logs', 'Automation/Receipts'):
    (ROOT / directory).mkdir(parents=True, exist_ok=True)

roadmap = ['# ROBOTICS VÀ AI ROBOT TỪ SỐ 0 ĐẾN NÂNG CAO', '',
           'Phiên bản 1 — 160 bài dự kiến, 24 module. Đây là kế hoạch; chỉ bài có trong state mới được tính đã biên soạn. Liên kết bài tương lai cố ý chưa có tệp.', '',
           'Học theo số bài. Cột prerequisite là bài bắt buộc gần nhất; quan hệ bắc cầu bao gồm toàn bộ nền tảng trước đó. Bài project ứng dụng kiến thức đã học, không lặp nguyên lý. Có thể thêm bài khi major checkpoint có bằng chứng thiếu nền; cập nhật số, liên kết, state và tổng cùng lúc, không đổi số bài đã hoàn thành.', '',
           'Mỗi bài dự kiến 60–120 phút, project có thể nhiều buổi. Đây là nhịp gợi ý, không hứa thời lượng cố định. HIỂU → LÀM → ĐO → QUAN SÁT → DEBUG → GIẢI THÍCH LẠI.', '',
           'Sau mỗi 5 bài: một checkpoint riêng, rồi dừng unit. Cuối mỗi module: một major checkpoint riêng. Nếu trùng mốc: checkpoint thường trước, major checkpoint sau; không gộp hai unit. Major checkpoint xác nhận độ đầy đủ của giáo trình; kỹ năng thực hành của người học chỉ được ghi khi có bằng chứng từ họ.', '',
           'Lý do sắp thứ tự: dụng cụ đo trước đấu mạch; pinout trước GPIO; nguồn và cơ khí trước motor; watchdog trước điều khiển qua mạng; Linux trước AI/vision; điều khiển phản hồi trước ROS; navigation trước tích hợp capstone. I2S ở Part 06 chỉ kiểm chứng bus bằng mẫu thô, phần âm thanh sau đó mới xử lý record/playback.', '']
for m in modules:
    roadmap += [f"## Part {m['number']:02d} - {m['name']}", '',
                f"Phạm vi tương ứng phần {m['original']} trong yêu cầu. Bài {m['start']:03d}–{m['end']:03d}. Gate đầu vào: " + ('không có.' if m['start'] == 1 else f"bài {m['start']-1:03d} và major checkpoint module trước đã PASS."), '',
                '| ID | Bài học | Prerequisite | Kết quả kiểm chứng |', '| --- | --- | --- | --- |']
    for r in rows[m['start']-1:m['end']]:
        roadmap.append(f"| {r['number']:03d} | [[{r['stem']}]] | {r['number']-1:03d} | {r['outcome']} |" if r['number'] > 1 else f"| 001 | [[{r['stem']}]] | Không | {r['outcome']} |")
    roadmap += ['', f"**Major checkpoint Part {m['number']:02d}:** kiểm tra mọi sản phẩm ở cột kết quả, phân biệt đã giải thích với đã thực nghiệm; ghi thiếu prerequisite và sửa trước khi sang module tiếp theo.", '']
roadmap += ['## Kiểm soát phạm vi', '', 'CAN cần hai node thật. FreeRTOS task/queue/event có nhịp giới thiệu tại Bài 091; ESP-IDF tại Bài 116 khi firmware voice cần; driver abstraction và class khi phù hợp tại Bài 120. Major checkpoint chèn bài cầu nối khi quá tải. Face detection là nhánh tùy chọn của Bài 106. Bài 065 dạy động học một khớp. Không khẳng định người học đã thực hành khi chưa có bằng chứng.', '', 'Mọi API, thư viện, model, board revision và tổ hợp ROS/OS cần tra nguồn chính thức tại thời điểm viết bài tương ứng. Không khóa cả khóa học vào một model AI hay một board clone. Các lựa chọn triển khai và nguồn được ghi ở [[SOURCES]] và [[HARDWARE_PROFILES]].']
put('01_COURSE_ROADMAP.md', '\n'.join(roadmap))
# Chỉ là index sinh từ roadmap, controller đối chiếu với bảng Markdown mỗi lần.
put('Reference/ROADMAP_INDEX.json', json.dumps(dict(schema_version=1, modules=modules, lessons=rows), ensure_ascii=False, indent=2))

put('AGENTS.md', '''# Quy tắc bền vững — Robotics AI Course

Phạm vi là thư mục Robotics_AI_Course. Viết tiếng Việt dễ hiểu, thuật ngữ Việt kèm English. Không xóa nội dung người dùng, không mua hàng, nạp firmware, chạy motor hay gọi API tính phí chỉ để viết bài. Khởi tạo được phép tạo hạ tầng và Bài 001 trong cùng run; mọi run tiếp theo chính xác MỘT UNIT. Không gọi controller/Codex đệ quy, không tự tạo lịch chạy nền, không viết tiếp bài sau trong cùng run.

## Đọc và chọn việc

1. Luôn đọc AGENTS.md và 02_COURSE_STATE.md trước khi sửa. JSON nằm giữa COURSE_STATE_JSON_START/END là single source of truth; không lấy cache Automation làm tiến độ gốc.
2. Đọc phần roadmap hiện tại; đọc prerequisite và tối đa 5 bài gần nhất khi cần. Không quét toàn vault mỗi lần. Full curriculum audit ở major checkpoint hoặc khi state yêu cầu.
3. Nếu có Automation/ACTIVE_UNIT.json, làm đúng kind/target/id/path trong đó. Đây là yêu cầu tạm của controller, không phải nguồn tiến độ. Nếu state BLOCKED, dừng và nêu lỗi; chỉ sửa lỗi được người dùng cho phép. PAUSED chỉ resume khi người dùng nói tiếp tục hoặc có --resume rõ ràng. COMPLETE không viết nữa.
4. Ưu tiên pending_repairs → checkpoint sau mỗi 5 bài → major checkpoint cuối module → lesson kế tiếp. Các mốc không được bỏ qua. Nếu đủ 160 bài vẫn làm checkpoint 160 và major cuối rồi mới COMPLETE. Có checkpoint_pending khi chờ checkpoint, kể cả lúc usage dừng.
5. Trước unit trực tiếp trong app, dùng usage tool nếu có. Hai cửa sổ 300 và 10080 phút, remaining = 100 - usedPercent, thiếu không bằng 0. Nếu một remaining <= 10 hoặc báo reached thì PAUSED/USAGE_GUARD, ghi reset khi có. Không tự resume sau reset. Nếu controller đã probe ngay trước run, dùng snapshot trong ACTIVE_UNIT; không suy diễn hạn mức từ token count. Không gọi reset credit.
6. Nếu không đọc được usage chính thức: UNAVAILABLE. Tối đa 5 lesson kể từ checkpoint gần nhất; checkpoint vẫn phải làm thành unit kế tiếp rồi PAUSED/USAGE_DATA_UNAVAILABLE_SAFE_PAUSE. Nếu usage thấp trước checkpoint: giữ pending. Resume không xóa bộ đếm hay bỏ checkpoint.

## Chất lượng bài

Mỗi khái niệm mới trả lời: là gì, vì sao cần, thiếu thì sao, ở đâu trong robot, ví dụ, cách tự kiểm chứng. Không giả định V A Ω GND breadboard đã biết. Không padding. HIỂU → LÀM → ĐO → QUAN SÁT → DEBUG → GIẢI THÍCH LẠI. Nhắc bài cũ chỉ làm prerequisite, nâng cấp, so sánh hoặc debug; không dạy lại toàn bộ.

Đọc Reference/LESSON_TEMPLATE.md khi viết lesson. Giữ toàn bộ heading, kể cả không code/hàn/wiring: ghi rõ không áp dụng và lý do, không bịa code hay pin. Một bài có đầu ra đáng kiểm chứng, 3–6 bài tập, mini challenge, 5 câu kiểm tra và đáp án; Debug Lab ít nhất 3 lỗi với Triệu chứng / Nguyên nhân có thể / Cách đo / Cách sửa. Ghi nhớ 5–10 dòng. Giải thích WHY cho mọi đường dây và mọi phần code. Code phải hoàn chỉnh, comment tiếng Việt, khóa board và phiên bản thư viện/framework; không để dấu ba chấm thay phần bắt buộc. Không tuyên bố code đã compile hoặc hardware đã thử nếu chưa thử.

Tên tệp ASCII an toàn Windows: Bai XXX - Ten bai.md trong Lessons/Part_XX. H1 tiếng Việt: # Bài XXX - Tên bài. Chỉ tạo lesson đang viết, liên kết lesson tương lai là liên kết dự kiến. Thuật ngữ đã dạy mới đưa vào glossary có link bài gốc.

## Hardware và safety

Mỗi bài có điện/hàn/motor/pin cần callout [!warning] Safety Box cụ thể. Chỉ low-voltage DC; không thực hành điện lưới. Không đo dòng bằng cách đặt hai que qua nguồn; continuity/ohm chỉ khi đã ngắt mọi nguồn và xả tụ theo tài liệu. Cổng COM/V phải kiểm tra trước đo áp. Không short chủ động để thử lỗi. Không hàn trực tiếp cell lithium, dùng pin phồng, bypass BMS, sạc bằng buck thường hay nguồn không rõ thông số. Không để trẻ dùng mỏ hàn không giám sát.

Không gán GPIO thật trước khi chốt hãng, model, revision và module trong HARDWARE_PROFILES. N16R8 mô tả bộ nhớ, không xác định pinout board. Pin map ví dụ bắt buộc có câu: PIN MAP MẪU - kiểm tra board thực tế trước khi đấu. Kiểm tra strap, USB/JTAG, flash/PSRAM, điện áp logic, ADC và khả năng nguồn theo datasheet. Phân biệt bare IC với breakout có regulator/level shifting. Không cấp motor từ GPIO hay mặc định từ 3V3 board; chọn driver theo dòng stall và tản nhiệt. Common ground có lý do cho giao tiếp không cách ly, không nối tùy tiện các nguồn cách ly/đất lưới. MAX98357A đầu loa là ngõ ra vi sai, không nối một đầu loa xuống GND. E-stop và watchdog hoạt động khi AI/Linux/Wi-Fi hỏng.

Mua theo giai đoạn BUY NOW / BUY LATER / ADVANCED / OPTIONAL. Không một phần cứng làm mọi project. ESP32 điều khiển phần cứng có yêu cầu thời gian; Pi/edge chạy tác vụ mức cao. AI tool request phải qua schema, quyền, giới hạn và local safety; không bypass bằng MCP hoặc lời nói. Speaker recognition khác ASR; có unknown, sai số, consent, xóa dữ liệu. Camera/mic có chỉ báo, mute và retention. Không cam kết tự sạc nếu chưa có dock và hệ bảo vệ tương ứng.

## Checkpoint và sửa

Checkpoint XXX review đúng 5 bài, ghi PASS / NEEDS_REPAIR từng tiêu chí trong Reference/CHECKPOINT_TEMPLATE.md. Phải có bằng chứng cụ thể số bài/đoạn, không tích PASS hàng loạt. Chỉnh roadmap/state trước khi tiếp tục; nếu thấy lỗi nguy hiểm ở bài cũ, sửa ngay trong checkpoint và ghi patch. Lỗi còn lại đặt pending_repairs (id, path, reason, required_changes); mỗi repair là unit riêng; xong mới qua gate. Major checkpoint cuối MỖI module audit tính đầy đủ toàn curriculum và mức sẵn sàng sang module sau; chèn bài nếu thiếu thật, không tự kéo tiếp.

Phân biệt biên soạn và người học: completed_lessons nghĩa là đã viết + kiểm tra; learner_progress và completed_projects chỉ cập nhật từ minh chứng thực hành, không tự đánh dấu đã học/làm. Major có thể PASS về giáo trình và NOT_ASSESSED về người học.

## Validate và commit một unit

Chạy python Automation/controller.py --validate-only sau khi viết bản nháp; trong ACTIVE_UNIT dùng prepare-commit theo Reference/UNIT_PROTOCOL.md. Tự rà nội dung kỹ thuật và tối đa 2 lần sửa trong cùng run. Không gọi run mới để retry. Nếu vẫn fail: automation_state PAUSED, course_status BLOCKED, pause_reason VALIDATION_FAILED, known_problems cụ thể; không tăng completed_lessons.

Chỉ khi đã đạt: ghi receipt có hash nội dung, tiêu chí kỹ thuật với lý do và mức kiểm thử thật; cập nhật state cuối cùng một lần với last_unit.id/kind/target/path/receipt, tăng revision; cập nhật HOME, glossary, hardware introduced, concepts taught/not yet taught. Dùng helper prepare-commit để xác thực cấu trúc và commit nhất quán; tự đánh giá semantic trước helper. Receipt chỉ là khai báo review, không chứng nhận thực nghiệm. Sau commit chạy --validate-only. Dừng run với báo cáo ngắn. Không viết thêm unit để tận dụng quota.
''')

put('Reference/LESSON_TEMPLATE.md', '''# Mẫu lesson bắt buộc

H1: # Bài XXX - Tên bài

Metadata đầu bài: prerequisite, kết quả, thời lượng gợi ý, trạng thái tài liệu, trạng thái thử phần cứng/code. Liên kết vừa đủ. Mọi heading dưới đây phải có nội dung; mục không áp dụng ghi rõ tại sao.

## Hôm nay chúng ta làm được gì?
## Tại sao phải học thứ này?
## Kiến thức mới
Với mỗi khái niệm: Nó là gì? Tại sao cần? Không có thì sao? Ở đâu trong robot? Ví dụ? Tự kiểm chứng?
## Thuật ngữ quan trọng
| Tiếng Việt | English | Ý nghĩa |
| --- | --- | --- |
## Hình dung đơn giản
Sơ đồ ASCII nếu giúp hiểu; không dùng thay bảng dây thật.
## Phần cứng cần dùng
Đúng thông số và số lượng, không mua trước nhiều module.
## Hiểu chân linh kiện
| Pin | Meaning | Connect to |
| --- | --- | --- |
## Sơ đồ đấu dây
| Điểm đầu | Điểm cuối | Điều kiện điện áp |
| --- | --- | --- |
## Tại sao nối như vậy?
## Thực hành
STEP 1, STEP 2, STEP 3...; kiểm tra không nguồn trước cấp điện.
## Nếu có hàn
Nhiệt độ tham khảo theo hợp kim/đầu mỏ, trình tự, điểm hàn, kiểm continuity, short.
## Code
## Code hoạt động như thế nào?
## Kết quả mong đợi
## Debug Lab
Ít nhất 3 mục ### Lỗi ...; mỗi mục chứa Triệu chứng, Nguyên nhân có thể, Cách đo, Cách sửa.
## Thử nghiệm thêm
## Bài tập
3–6 thao tác/câu giải thích kết quả.
## Mini Challenge
## Kiểm tra hiểu bài
5 câu ngắn.
## Đáp án
Callout [!success]- Đáp án gợi ý gồm bài tập, challenge và 5 câu.
## Ghi nhớ
5–10 dòng.
## Bài tiếp theo
Giới thiệu ngắn, có thể là checkpoint trước bài tiếp theo.
''')

criteria = ['Dependency order có đúng không', 'Có bài nào quá sớm không', 'Có prerequisite bị thiếu không', 'Có lặp không cần thiết không', 'Có bài quá dài không', 'Có bài quá ngắn không', 'Người mới có hiểu nổi không', 'Thuật ngữ English có được giải thích không', 'Có đủ WHY không', 'Có thực hành thật không', 'Wiring có an toàn không', 'Pin voltage có hợp lý không', 'Code có phù hợp hardware không', 'Có risk làm cháy linh kiện không', 'Debug có thực tế không', 'Roadmap có cần điều chỉnh không']
put('Reference/CHECKPOINT_TEMPLATE.md', '# Mẫu checkpoint\n\n# Checkpoint XXX - Review Bài AAA đến BBB\n\n## Phạm vi và bằng chứng\nĐọc 5 bài và prerequisite liên quan, ghi tên file/đoạn.\n\n## Đánh giá 16 tiêu chí\n\n| # | Tiêu chí | Kết luận | Bằng chứng và hành động |\n| --- | --- | --- | --- |\n' + '\n'.join(f'| {i} | {c}? | Chưa đánh giá | Cần dẫn bài cụ thể |' for i,c in enumerate(criteria,1)) + '\n\n## Lỗi và sửa đổi\nGhi lỗi nguy hiểm đã sửa ngay; các lỗi khác có pending_repairs.\n\n## Quyết định gate\nPASS hoặc NEEDS_REPAIR, không khẳng định người học đã có kỹ năng nếu chưa có minh chứng.\n\n## Cập nhật state\nCheckpoint coverage, next_unit, pending_repairs, usage mode.\n\n## Major checkpoint bổ sung\nAudit curriculum tổng thể, glossary, hardware, đủ prerequisite sang module sau, rubric thực hành đạt/chưa đánh giá; đề xuất bài bổ sung có lý do. Kết luận tách giáo trình với người học.')

put('03_HARDWARE_ROADMAP.md', '''# Hardware roadmap — mua theo bài

Chưa biết phần cứng người học đang sở hữu. introduced nghĩa là được nhắc/dạy, không phải đã mua. Không có giá giả định; đối chiếu mã linh kiện và tài liệu hãng trước mua. Ghi lựa chọn thật vào [[HARDWARE_PROFILES]].

## BUY NOW

| Khi cần | Số lượng và thông số | Dùng để làm gì |
| --- | --- | --- |
| Bài 001 | 1 đèn pin hoàn chỉnh ghi 2 × AA 1.5 V, ưu tiên có sẵn; 2 pin alkaline AA 1.5 V cùng loại | Học mạch kín mà chưa đấu dây rời; đèn đã tích hợp phần điện phù hợp |
| Bài 001 | Giấy và bút, mặt bàn khô | Dự đoán và ghi kết quả; không cần ESP32 |
| Trước 011–014 | 1 breadboard có rãnh giữa, jumper đực-đực; 1 multimeter đo DC V, Ω và continuity có que tốt, cổng rõ | Học phép đo trước mạch phức tạp |
| Trước 014 | LED đỏ rời 5 mm có datasheet; điện trở 330 Ω, 1 kΩ, 10 kΩ loại 1/4 W, mỗi loại 10; 5 nút nhấn | Dòng LED được tính theo nguồn và forward voltage; 1 kΩ là lựa chọn ban đầu dễ hạn dòng ở nguồn thấp |
| Trước 014 | Nguồn DC để bàn cách ly có giới hạn dòng và thông số rõ; có thể mượn | Chọn dải dùng 0–5 V ở bài đầu, không tự lắp bộ nguồn điện lưới |

Không dùng cell 14500 lithium thay AA chỉ vì cùng kích thước. Chưa có đèn pin thì làm phần sơ đồ trước; không tự tạo một mạch nối pin bằng dây trần.

## BUY LATER

| Mốc | Phần cứng | Tiêu chí chọn và lý do |
| --- | --- | --- |
| 015–020 | Kìm tuốt dây, dụng cụ bấm đúng loại cos, connector khóa, co nhiệt; mỏ hàn điều nhiệt, giá đỡ, kính, thông gió hút khói, flux, thiếc, dây hút, bơm hút, perfboard | JST là họ đầu nối; xác minh series, pitch và cực tính, không mua chỉ theo màu dây |
| 025–037 | 1 board phát triển ESP32-S3 có schematic/pinout đúng revision, USB data cable, biến trở 10 kΩ | Ưu tiên module có PSRAM để tái dùng ở audio. N16R8 là ứng viên bộ nhớ, không là bảo đảm pinout hay chất lượng board |
| 038–042 | USB-UART 3.3 V; cảm biến I2C breakout 3.3 V; màn hình SPI logic 3.3 V; INMP441; cặp node CAN có transceiver tương thích | Mượn CAN nếu ít dùng; không thay thực hành bus bằng lý thuyết và gọi là đã thử |
| 043–049 | TTP223, LDR và điện trở; ultrasonic có đặc tả Echo, mạch chia áp nếu cần; VL53L0X breakout; IMU có tài liệu; encoder quay tay | Kiểm tra mức logic và pull-up trên breakout, không suy từ tên IC |
| 050–056 | Buck có datasheet và đủ dòng; fuse, công tắc, đầu nối và dây đúng tải; pack pin thương mại bảo vệ và bộ sạc đúng chemistry/số cell nếu cần chạy di động | Có thể dùng nguồn để bàn cho robot trên giá trước; BMS không thay chức năng bộ sạc |
| 057–069 | Chassis, 2 bánh, caster, ốc/standoff; SG90; DC gear motor có dòng stall; driver; stepper + driver phù hợp | TB6612FNG là ứng viên nếu dòng stall, điện áp và nhiệt đáp ứng; motor TT tùy nhà cung cấp phải kiểm tra thực tế |
| 063–081 | LED RGB hoặc WS2812, buzzer, OLED SSD1306 I2C, LCD nếu cần | Điện áp cấp và điện áp data có thể khác; không mặc định WS2812 nhận ổn mọi mức 3.3 V |
| 088–094 | INMP441, MAX98357A, loa đúng trở kháng/công suất theo breakout, dây ngắn | Xác minh I2S slot và định dạng; hai đầu ra loa không phải GND |

## ADVANCED

| Mốc | Phần cứng | Điều kiện mở mua |
| --- | --- | --- |
| 095–100 | Raspberry Pi 4/5 hoặc máy Linux phù hợp; nguồn được khuyến nghị cho model, thẻ/SSD, tản nhiệt | Chốt nhu cầu RAM, OS, inference và ROS; không mặc định Pi chạy mọi model realtime |
| 101–108 | Camera USB/CSI có driver, bảng calibration; depth camera khi cần | Chốt độ phân giải FPS latency và hỗ trợ Linux/ROS trước mua |
| 128–144 | LiDAR 2D có driver hỗ trợ; IMU; base có encoder | Mở khi odometry và ROS đã vững. ToF một tia không thay thế toàn bộ LiDAR mapping |
| 145–149 | PCB prototype KiCad và linh kiện theo BOM đã review | Chỉ đặt gia công sau ERC/DRC và đối chiếu footprint vật lý |
| 155–160 | Nút E-stop cắt đường công suất motor phù hợp tải, hệ mic/loa/camera, LiDAR hoặc depth + stack khả dụng | Mobile base, voice, vision và navigation có ngân sách nguồn/compute rõ |

## OPTIONAL

Logic analyzer để nhìn protocol; oscilloscope để đo transient/noise (multimeter có thể bỏ sót); microphone array để định hướng tiếng nói; Jetson/accelerator khi model yêu cầu; printer 3D có thể thay bằng dịch vụ; dock sạc chỉ khi thiết kế tiếp điểm, sạc và bảo vệ riêng được đánh giá. Arduino/STM32/Pico là nhánh chuyển nền tảng, không mua tất cả.

## Lý do chọn

Nguyên lý điện, tín hiệu và giao tiếp được giữ độc lập board. ESP32-S3 phù hợp giai đoạn embedded và audio nhẹ; compute Linux phục vụ tác vụ cao hơn khi ngân sách đo được yêu cầu. Không chốt GPIO cho board chưa xác minh. ESPressif có quy định chân flash/PSRAM tùy cấu hình, vì vậy mã bộ nhớ ảnh hưởng chân dùng được: [hướng dẫn schematic ESP32-S3](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html). Các lựa chọn còn lại là ứng viên thiết kế cần chốt ở bài triển khai, chưa là danh sách mua chính xác cho một cấu hình duy nhất.
''')

put('Reference/HARDWARE_PROFILES.md', '''# Hồ sơ phần cứng

## HP001 — đèn pin kín dùng 2 AA

Trạng thái: cấu hình bài học, chưa biết thiết bị thật. Đèn pin hoàn chỉnh theo nhãn 2 × AA 1.5 V, hai alkaline AA cùng loại. Không yêu cầu mở phần mạch bên trong; chỉ khoang pin do nhà sản xuất cho phép mở. Không có GPIO. Bài 001 dùng sơ đồ chức năng, không phải sơ đồ sửa chữa mọi đèn pin.

## HP002 — ESP32-S3 chưa chốt

Trạng thái: UNCONFIRMED. Ứng viên: board có module ESP32-S3 với PSRAM, có thể N16R8 khi tài liệu đủ. Không có bảng GPIO chính thức của khóa ở thời điểm này.

Trước bài 025/030 phải điền hãng, tên board, revision, module in trên shield, Flash/PSRAM, ảnh mặt trên/dưới do người học cung cấp nếu cần, URL schematic/datasheet, USB port, nguồn cho phép, danh sách chân flash/PSRAM/strap/USB và pin map đã đối chiếu. Nếu chưa có board thực tế, chỉ cung cấp PIN MAP MẪU - kiểm tra board thực tế trước khi đấu với model tham chiếu đã nêu rõ, không tuyên bố đó là board người học.

## Mẫu ghi module mới

Mã profile; hãng; part number; bare IC hay breakout; revision; link datasheet; supply range; logic level; peak/stall current; pin map; nguồn cấp; bảo vệ; firmware/library version; bài dùng; mức xác minh (datasheet / compile / bench / learner report). Không điền giá trị theo suy đoán.
''')

PROJECTS = [
(1,'LED và button',31,'LED đổi trạng thái theo nút đã debounce; giải thích pull-up và đo áp nút.'),
(2,'Mini control panel',37,'Nút chiết áp LED chạy bằng state machine; log trạng thái không chặn.'),
(3,'Servo creature',65,'Servo chuyển động trong dải cơ khí cho phép; dừng khi phát hiện điều kiện không hợp lệ.'),
(4,'OLED robot face',80,'Mắt hiển thị trạng thái thật; animation không chặn điều khiển.'),
(5,'Distance alarm',49,'Báo gần và báo sensor lỗi bằng hai mẫu LED khác nhau; có dữ liệu so với thước.'),
(6,'Robot hai bánh',71,'Từng bánh đúng chiều trên giá, sau đó chạy chậm trong vùng thử; có ngắt nguồn.'),
(7,'Robot tránh vật cản',73,'Dừng trước giới hạn đã đo và xử lý timeout khoảng cách.'),
(8,'Robot dùng encoder',75,'Đếm xung hai bánh, hiệu chuẩn quãng đường và báo sai số.'),
(9,'Robot điều khiển từ điện thoại web',84,'Lệnh có giới hạn tốc độ; nhả deadman hoặc mất mạng thì dừng.'),
(10,'Robot điều khiển bằng giọng nói',109,'Nhận tiếng Việt vào tập lệnh cho phép; lệnh mơ hồ không kích hoạt motor.'),
(11,'Talking Robot',110,'Nghe rồi trả lời bằng TTS; có mute và xử lý tiếng loa lọt mic.'),
(12,'ESP32 AI Voice Robot',116,'ESP32-S3 giao tiếp voice backend; khóa và safety nằm đúng tầng.'),
(13,'Camera Robot',102,'Video có chỉ báo hoạt động và nút tắt; đo FPS và latency.'),
(14,'Object Detection Robot',106,'Chạy model đã chốt; đo false positives và phản ứng trong phạm vi cho phép.'),
(15,'Speaker-aware Robot',112,'Có consent enrollment unknown và xóa hồ sơ; báo sai số theo bộ mẫu thử.'),
(16,'Mapping Robot',138,'Lưu bản đồ có scale hợp lý và đánh giá chỗ mù/loop closure.'),
(17,'ROS 2 Mobile Robot',135,'Node TF telemetry motor bridge hoạt động, watchdog vẫn độc lập.'),
(18,'Indoor Autonomous Robot',143,'Đi A–B, tránh vật cản, hủy goal và dừng khi localization không tin cậy.'),
(19,'AI Education Robot',121,'Kịch bản STEM có giám sát, feedback dễ hiểu và không thu dữ liệu trẻ vượt nhu cầu.'),
(20,'Final Home AI Companion Robot',160,'Đạt ma trận nghiệm thu toàn hệ thống tại các bài 155–160.')]
project_lines = ['# Projects — sản phẩm tăng dần', '', 'Số project giữ đúng yêu cầu; thứ tự làm theo số bài prerequisite, không theo số project. Mỗi trang dưới đây là project brief và tiêu chí nghiệm thu, chưa phải hướng dẫn chế tạo hoàn chỉnh. Hướng dẫn và code sẽ nằm ở lesson tương ứng.', '', '| Project | Bài tích hợp | Nghiệm thu |', '| --- | --- | --- |']
for pid,name,number,accept in PROJECTS:
    stem = f'PROJECT {pid:02d} - {slug(name)}'
    project_lines.append(f'| [[{stem}]] | {number:03d} | {accept} |')
    put(f'Projects/{stem}.md', f'''# PROJECT {pid:02d} - {name}

Trạng thái: PLANNED — brief đã tạo; hướng dẫn thực hành chưa biên soạn. Chưa có minh chứng người học hoàn thành.

## Điều kiện bắt đầu

Hoàn thành nền tảng đến bài {number-1:03d}, các checkpoint/major gate trước đó và yêu cầu nguồn/hardware ở [[03_HARDWARE_ROADMAP]]. Bài tích hợp: [[{rows[number-1]['stem']}]]. Riêng PROJECT 20 bắt đầu thiết kế từ bài 155 sau major Part 23; Bài 160 nghiệm thu cuối.

## Sản phẩm và tiêu chí đạt

{accept}

## Bằng chứng cần lưu

BOM đúng model; sơ đồ nguồn/pin map khi có điện; code và phiên bản nếu có; ảnh/số đo/log của người học; dự đoán so với quan sát; ít nhất một lỗi đã tự tìm ra; cách dừng và xử lý sensor/lệnh không hợp lệ. Chưa có số đo thì để NOT_TESTED.

## Quy trình thực hiện

Đọc lesson tích hợp; giải thích cấu trúc; lắp khi chưa cấp nguồn; kiểm tra; thử từng khối; đo kết quả; tạo lỗi bằng cách ngắt lệnh hoặc thay dữ liệu giả lập, không chập điện hay cố kẹt motor. Tài liệu nghiệm thu sẽ được cụ thể hóa trong unit lesson tương ứng, không tự đánh dấu project COMPLETE khi chỉ viết xong bài.

## Nhật ký của người học

- Ngày và cấu hình: chưa có.
- Kết quả đo: chưa có.
- Vấn đề còn lại: chưa đánh giá.
- Kết luận đạt: chưa đánh giá.
''')
put('05_PROJECTS.md','\n'.join(project_lines) + '\n\nNhánh bổ sung: line follower Bài 074, tay máy một khớp Bài 065, robot STEM ở Project 19. Tuần tra/giao hàng mini là cách áp dụng navigation với tải trọng và vùng hoạt động đã kiểm thử; không tự suy ra an toàn sử dụng công cộng.')

put('Projects/CAPSTONE_ACCEPTANCE.md', '''# Ma trận nghiệm thu Home AI Robot

## Kiến trúc tham chiếu

~~~text
Người dùng có quyền + mute + camera indicator
                 |
        AI conversation / planning / tools
                 |
      Pi hoặc edge computer: ROS 2, voice, vision
                 |
     Lệnh có schema + giới hạn + thời hạn hiệu lực
                 |
       ESP32-S3: local state, watchdog, control
                 |
           Driver --> motor + encoder
                 ^
         sensor / obstacle / E-stop
Nút E-stop cắt đường công suất motor theo thiết kế độc lập
~~~

AI có thể đưa lệnh sai hoặc mất mạng; controller tại robot phải tự từ chối lệnh sai, cũ hoặc vượt giới hạn. Ngắt công suất motor không được phụ thuộc cloud hoặc một lời gọi MCP. Audio có thể ở ESP hoặc Pi tùy tài nguyên, không bắt mọi luồng đi qua ESP.

| Hạng mục bắt buộc | Bằng chứng đạt | Trạng thái |
| --- | --- | --- |
| Mobile base + encoder | Chiều bánh, tốc độ, quãng đường và sai số đo | NOT_TESTED |
| Obstacle detection + local safety | Vật cản/sensor timeout làm dừng trong khoảng đã đặt | NOT_TESTED |
| Emergency stop + watchdog | Dừng khi AI/Pi/mạng không hoạt động; quy trình reset có chủ ý | NOT_TESTED |
| Mic + speaker + voice | Wake word/VAD/ASR/TTS hoặc realtime có mute, đo latency | NOT_TESTED |
| Camera + object detection | Chỉ báo rõ, bộ mẫu ánh sáng và ghi false detection | NOT_TESTED |
| Navigation | Đi A–B trong môi trường kiểm soát, hủy goal và tránh vật cản | NOT_TESTED |
| Mapping/localization | Nếu chọn SLAM: bản đồ và độ tin cậy pose; nếu thiếu hardware ghi giới hạn, bổ sung trước khi nhận năng lực SLAM | NOT_TESTED |
| AI conversation + tool calling | Schema/allowlist/timeouts, lệnh sai không tới motor | NOT_TESTED |
| State + memory | Xem/sửa/xóa trí nhớ, trạng thái lỗi có phản hồi | NOT_TESTED |
| Privacy | Consent speaker, unknown, mute camera/mic, retention, local/cloud | NOT_TESTED |
| Nguồn và nhiệt | Power budget đo dưới tải, fuse/BMS/sạc phù hợp | NOT_TESTED |
| Bàn giao | BOM, pin map, phiên bản, logs, hướng dẫn bảo trì và giới hạn | NOT_TESTED |

Không bỏ navigation khỏi nghiệm thu cốt lõi. Thiếu phần cứng thì ghi CAPSTONE_INCOMPLETE cho năng lực tương ứng và lập kế hoạch bổ sung. Quay về điểm nghỉ không đồng nghĩa tự sạc. Nhận giọng người nói không là khóa bảo mật đáng tin cậy duy nhất. Tránh người bằng hình ảnh đơn thuần không chứng minh chống va chạm trong mọi tình huống.
''')

put('06_SKILL_TREE.md', '''# Skill tree — học trước gì để làm được gì

~~~mermaid
flowchart TD
  A[Điện - mạch kín - điện áp - dòng - GND] --> B[Đo - breadboard - schematic - pinout]
  B --> C[GPIO và C C++]
  A --> P[Nguồn và bảo vệ]
  P --> D[Motor driver]
  C --> D
  K[Cơ khí - torque - bánh xe] --> E[DC motor và mobile base]
  D --> E
  C --> F[Encoder]
  E --> O[Odometry]
  F --> O
  O --> PID[Feedback và PID]
  O --> L[Localization]
  L --> SL[SLAM và mapping]
  SL --> N[Navigation]
  R[Linux - ROS 2 - TF] --> N
  C --> I[I2S]
  M[Microphone] --> I
  I --> AU[Audio - PCM - buffer]
  AU --> AS[ASR - nói gì]
  AU --> SR[Speaker recognition - ai nói]
  AS --> V[Voice AI]
  SR --> V
  CO[Consent - unknown - xóa dữ liệu] --> SR
  CA[Camera] --> IM[Images - pixels]
  IM --> CV[OpenCV]
  CV --> OD[Object detection]
  OD --> TR[Tracking]
  TR --> PE[Robot perception]
  V --> H[Home AI Robot]
  N --> H
  PE --> H
  SAFE[E-stop - watchdog - privacy - safety layer] --> H
~~~

Thứ tự đọc đầy đủ ở [[01_COURSE_ROADMAP]]. Sơ đồ là quan hệ kỹ năng, không là chứng nhận người học đã đạt. Speaker recognition là nhánh xử lý audio song song với ASR; học voice trước giúp có tình huống ứng dụng nhưng không làm ASR thành prerequisite toán học của speaker recognition. SLAM đồng thời ước lượng chuyển động và bản đồ; trước đó học localization riêng để hiểu pose và độ bất định.

## Cổng kỹ năng có bằng chứng

| Gate | Phải tự làm được | Bài/mốc |
| --- | --- | --- |
| Điện cơ bản | Giải thích mạch kín, V/A/Ω, GND và short | 010 |
| Đấu và đo | Continuity không nguồn, đo DC V đúng cổng, LED hạn dòng | 015 |
| Board | Đọc pinout/datasheet của đúng revision | 025 |
| Embedded | Nút không rung, timer không chặn, log có ích | 037 |
| Mobile | Nguồn đủ, motor driver phù hợp, odometry và mất lệnh thì dừng | 077 |
| AI | Lệnh cấu trúc có kiểm quyền và local safety | 121 |
| ROS | Cây TF hợp lệ và motor bridge có watchdog | 135 |
| Navigation | Mapping/localization đủ tin cậy, A–B có hủy goal | 144 |
| Capstone | Ma trận [[CAPSTONE_ACCEPTANCE]] có bằng chứng | 160 |

Hiện tại các gate thực hành đều NOT_ASSESSED. Hệ thống viết giáo trình có thể tiếp tục khi nội dung prerequisite đã đủ; người học không chuyển phần thực hành có nguy cơ khi kỹ năng cần thiết chưa đạt.
''')

put('Reference/DEBUG_METHOD.md', '''# Debug theo đường đi của hệ thống

POWER → GROUND → WIRING → SIGNAL → PROTOCOL → FIRMWARE → LOGIC.

Đây là bản đồ dùng xuyên khóa, chưa yêu cầu người học Bài 001 biết tất cả thuật ngữ. POWER = nguồn; GROUND = mốc điện áp chung; WIRING = đường nối; SIGNAL = tín hiệu; PROTOCOL = quy tắc trao đổi; FIRMWARE = chương trình trên controller; LOGIC = quyết định của chương trình.

Mỗi lần debug ghi: dự đoán → triệu chứng thật → một giả thuyết → phép kiểm tra ít nguy cơ nhất → một thay đổi → đo lại. Không thay đồng thời cả code, dây và nguồn rồi đoán nguyên nhân.

| Tầng | Phép kiểm tra sau khi đã học | Tránh |
| --- | --- | --- |
| Nguồn | Đọc nhãn, đo áp đúng cổng, đo dưới tải phù hợp | Nối que dòng qua nguồn; tăng áp để chữa lỗi |
| Ground | Lần đường tham chiếu theo schematic | Nối mọi GND/earth tùy tiện |
| Wiring | So bảng dây, continuity khi không nguồn | Rút cắm motor khi driver đang cấp điện |
| Signal | Đọc mức/nhịp bằng đồng hồ hoặc analyzer phù hợp | Tưởng multimeter nhìn được mọi xung ngắn |
| Protocol | Baud/address/mode/termination với tài liệu | Thử ngẫu nhiên GPIO |
| Firmware | Log reset, phiên bản, nguồn lỗi | Flash liên tục khi nguồn hỏng |
| Logic | State transition, timeout, dữ liệu giả lập | Cho AI vượt safety để test |

Nhật ký mẫu: ngày; cấu hình; lệnh; mong đợi; quan sát; giả thuyết; phép đo; kết quả; sửa gì; xác minh lại; còn chưa biết gì. Không ghi số đo giả hoặc secret vào log.
''')

put('Reference/SOURCES.md', '''# Nguồn và chính sách phiên bản

Kiểm tra ngày 2026-09-13. Nguồn được đọc để xây hạ tầng; các bài tương lai phải tra lại tài liệu tương ứng khi triển khai. Không dùng bài blog thay datasheet cho điện áp/chân/dòng.

| Chủ đề | Nguồn | Điều đã dùng |
| --- | --- | --- |
| Codex chạy một yêu cầu | [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) | exec JSONL có turn.completed/turn.failed/error; exit code không đủ để kết luận nội dung đạt |
| Hạn mức chính thức | [Codex App Server](https://learn.chatgpt.com/docs/app-server) | initialize rồi account/rateLimits/read qua stdio; dùng usedPercent và windowDurationMins |
| CLI cài thực tế | codex-cli 0.149.1, --help, exec --help, app-server --help, generate-json-schema | Có exec, app-server và schema cho account/rateLimits/read; không có status trong help đã kiểm |
| Chân ESP32-S3 | [Espressif hardware schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html) | Cấu hình flash/PSRAM có thể dành riêng GPIO; phải đối chiếu đúng module |

Controller feature-detect lại mỗi phiên chạy. Nếu API thay schema, timeout hoặc thiếu một cửa sổ hạn mức: UNAVAILABLE; không đọc cache tài khoản nội bộ hay scrape UI. Không lưu token đăng nhập, accountId hay thông tin nhận dạng vào vault.

ROS/OS, KiCad, OpenCV, model detection, Xiaozhi, MCP và voice API chưa chốt phiên bản thực hành. Bài liên quan phải ghi bộ phiên bản đã kiểm chứng và link tài liệu gốc. Chọn phiên bản được hỗ trợ phù hợp driver tại lúc triển khai; không suy từ danh sách roadmap rằng đã xác minh cả stack.
''')

put('Checkpoints/README.md', '''# Checkpoints

Chưa có checkpoint hoàn thành. Checkpoint 001 sẽ review Bài 001–005, là unit sau Bài 005. Major checkpoint Part 01 xuất hiện sau Bài 010 và checkpoint 002. Không tạo sẵn báo cáo PASS.

Tên thường: Checkpoint 001 - Review Bai 001 den 005.md. Tên major: Major Checkpoint 01 - Part 01.md. Quy tắc và tiêu chí: [[CHECKPOINT_TEMPLATE]].
''')

print(json.dumps({'lessons': len(rows), 'modules': len(modules), 'projects': len(PROJECTS)}, ensure_ascii=False))
