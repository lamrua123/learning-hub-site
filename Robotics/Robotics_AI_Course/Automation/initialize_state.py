"""Bước khởi tạo một lần, dừng sau Bài 001. Từ chối ghi đè state hiện hữu."""
import json
from pathlib import Path
import controller as c

root = Path(__file__).resolve().parents[1]
if (root/'02_COURSE_STATE.md').exists():
    raise SystemExit('State đã tồn tại; không được khởi tạo đè.')
index = c.read_index(root)
usage = c.probe_usage(c.resolve_codex(),c.detect_features(c.resolve_codex()))
state = dict(
    schema_version=1,revision=0,course_status='IN_PROGRESS',automation_state='RUNNING',
    current_lesson=None,last_completed_lesson=None,next_lesson=1,current_module=1,
    completed_lessons=0,total_planned_lessons=160,current_project=None,completed_projects=[],
    learner_progress='NOT_ASSESSED — chưa có minh chứng thực hành từ người học',
    current_checkpoint=None,last_checkpoint=None,last_checkpoint_number=0,last_checkpoint_lesson=0,
    checkpoint_pending=False,major_checkpoints_completed=[],last_major_checkpoint=None,pending_repairs=[],
    known_problems=['Chưa xác định board ESP32-S3 thực tế: không có GPIO được phê duyệt.',
                    'Chưa thử bài trên phần cứng người học; mọi kết quả thao tác cần tự ghi.',
                    'Các project mới là brief; chỉ Bài 001 được biên soạn trong unit khởi tạo.'],
    hardware_already_introduced=[],concepts_already_taught=[],
    concepts_not_yet_taught=[
        'Điện áp giải thích đầy đủ (002); dòng và A (003); điện trở và Ohm (004); công suất W Wh (005)',
        'GND (006); nối tiếp/song song; DC/AC; 3.3V/5V; linh kiện điện tử',
        'Dụng cụ, multimeter, breadboard, hàn, schematic, pinout và datasheet',
        'ESP32 C/C++ GPIO ADC PWM timer interrupt memory và protocols',
        'Cảm biến, nguồn lithium và bảo vệ, cơ khí CAD, actuator và robot hai bánh',
        'Display HRI, mạng, audio, Pi Linux Python, computer vision',
        'Voice/speaker recognition, AI tools MCP realtime, control PID sensor fusion',
        'ROS 2 TF, localization SLAM navigation, PCB reliability và capstone'],
    last_run_date=c.utcnow(),last_state_update=c.utcnow(),pause_reason=None,last_unit=None,
    usage=usage,usage_unavailable_since_checkpoint=(usage['mode']=='UNAVAILABLE'),
    validation_status='INITIALIZING',automation_cli_version='0.149.1',next_unit=None)
prefix = '''# 02 — Course State

Nguồn tiến độ duy nhất của khóa học. Khối JSON là machine-readable và cũng đọc được trong Obsidian; không sửa cache để thay tiến độ. Course status nói việc biên soạn (IN_PROGRESS / BLOCKED / COMPLETE). Automation state chỉ PAUSED / RUNNING / COMPLETE. BLOCKED là lỗi cần sửa, không phải tên thứ tư của automation state.

completed_lessons = bài đã biên soạn và review, KHÔNG là bài người học đã học xong. completed_projects chỉ chứa project có minh chứng người học. Các checkpoint/major xác nhận chất lượng tài liệu, không tự chứng nhận kỹ năng thực tế.

'''
suffix = '''

## Cách đọc tiến độ

current_lesson là bài gần nhất đã viết; next_lesson là số bài sẽ viết khi không còn checkpoint/repair ưu tiên. next_unit chỉ rõ việc phải làm trước. last_checkpoint_lesson là coverage đã review, không được reset khi resume. UsageGuardMode chính là usage.mode; số null nghĩa là không có dữ liệu. Reset và ngày chạy ghi UTC.

Khi roadmap đổi, cập nhật tổng và dependency cùng Reference/ROADMAP_INDEX.json; không đánh dấu bài tương lai COMPLETE. Các ghi chú cá nhân để dưới đây, bên ngoài khối JSON.

## Ghi chú của người học

Chưa có.
'''
(root/'02_COURSE_STATE.md').write_text(prefix+c.START+'\n'+c.END+suffix,encoding='utf-8')
c.write_state(root,state,index)
if c.usage_low(usage):
    c.pause(root,state,index,'USAGE_GUARD')
    raise SystemExit('USAGE_GUARD: không bắt đầu hoặc đánh dấu hoàn tất Bài 001.')
active = dict(c.next_unit(state,index),id='bootstrap-001',start_revision=state['revision'],
              usage=usage,created_at=c.utcnow(),lesson_hashes={})
c.atomic_text(root/'Automation/ACTIVE_UNIT.json',c.json_text(active))
evidence = {
    'prerequisites':'Bài 001 không prerequisite; 6 nhóm khái niệm được giải thích bằng sáu câu hỏi. V/A/GND chỉ dẫn tới bài sau với độ sâu ghi rõ.',
    'why':'Mục nguồn, tải, mạch kín và công tắc đều giải thích nhu cầu, hậu quả thiếu, vị trí trên robot và cách kiểm chứng.',
    'terminology':'Bảng thuật ngữ có Việt English; glossary chỉ ghi phần đã giới thiệu và đánh dấu voltage/current/resistance sơ lược.',
    'wiring':'Không GPIO hoặc dây rời. Bảng pin chỉ theo dấu trong khoang đèn nguyên vẹn; sơ đồ có nhãn mô hình chức năng.',
    'voltage':'Chọn đèn yêu cầu 2 AA 1.5 V và pin alkaline cùng loại đúng nhãn; không suy pin giống hình dạng là tương thích.',
    'code':'Không có MCU/code nên hai mục code ghi không áp dụng có lý do. Không tuyên bố compile hay chạy firmware.',
    'safety':'Safety Box cấm nối tắt pin, lithium 14500 thay AA, pin lỗi và mở mạch; thực hành chỉ thao tác thiết bị nguyên vẹn.',
    'debug':'Có bốn lỗi cụ thể đủ triệu chứng/nguyên nhân/cách đo/cách sửa; phép đo chỉ là quan sát hoặc thay thế phù hợp, không dùng multimeter sớm.',
    'exercises':'Năm bài tập, năm câu kiểm tra, đáp án thu gọn, challenge giải thích lại và tám dòng ghi nhớ; bảng thực hành để trống kết quả thật.',
    'sources':'Điện học nhập môn là kiến thức nền ổn định; thao tác pin phụ thuộc nhãn/hướng dẫn đèn, không giả hãng. Nguồn chính thức CLI/ESP lưu ở SOURCES.'}
review = dict(repair_attempts=0,test_level='DOCUMENT_REVIEW_ONLY; hardware NOT_TESTED; code NOT_APPLICABLE',
              checks={k:dict(passed=True,evidence=v) for k,v in evidence.items()},
              hardware_already_introduced=['Đèn pin hoàn chỉnh yêu cầu 2 × alkaline AA 1.5 V','Giấy/bút và bảng quan sát'],
              concepts_already_taught=['Điện/điện tích/dòng điện: nhận diện, chưa định lượng',
                  'Nguồn điện, cực pin, cực tính và đọc nhãn điện áp sơ lược',
                  'Tải, vật dẫn, cách điện và đường trở về nguồn',
                  'Mạch kín, mạch hở, công tắc và trạng thái cơ bản',
                  'Ngắn mạch: nhận diện nguy cơ trên giấy; điện trở sơ lược',
                  'Debug bằng dự đoán, quan sát, giả thuyết và thử một thay đổi'])
c.atomic_text(root/'Automation/review-bootstrap-001.json',c.json_text(review))
c.prepare_commit(root,root/'Automation/review-bootstrap-001.json')
(root/'Automation/ACTIVE_UNIT.json').unlink()
state = c.read_state(root)
c.pause(root,state,index,'INITIALIZATION_COMPLETE')
errors = c.validate_course(root,c.read_state(root),index)
if errors:
    raise SystemExit('; '.join(errors))
print('Bootstrap PASS: 1/160 lesson, next 002, PAUSED / INITIALIZATION_COMPLETE.')
