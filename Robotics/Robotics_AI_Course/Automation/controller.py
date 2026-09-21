"""Controller chuẩn-library: một codex exec / unit, kiểm quota, validate rồi mới tiếp.

Tiến độ chỉ đọc từ khối JSON của 02_COURSE_STATE.md. Cache không quyết định tiến độ.
Python >= 3.10. Không tự retry, reset credit, cài scheduler hoặc đọc auth/cache bí mật.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

START = '<!-- COURSE_STATE_JSON_START -->'
END = '<!-- COURSE_STATE_JSON_END -->'
HEADINGS = [
    'Hôm nay chúng ta làm được gì?', 'Tại sao phải học thứ này?', 'Kiến thức mới',
    'Thuật ngữ quan trọng', 'Hình dung đơn giản', 'Phần cứng cần dùng',
    'Hiểu chân linh kiện', 'Sơ đồ đấu dây', 'Tại sao nối như vậy?', 'Thực hành',
    'Nếu có hàn', 'Code', 'Code hoạt động như thế nào?', 'Kết quả mong đợi',
    'Debug Lab', 'Thử nghiệm thêm', 'Bài tập', 'Mini Challenge',
    'Kiểm tra hiểu bài', 'Đáp án', 'Ghi nhớ', 'Bài tiếp theo']
SEMANTIC = ['prerequisites', 'why', 'terminology', 'wiring', 'voltage', 'code',
            'safety', 'debug', 'exercises', 'sources']
PROMPT = ('Đọc AGENTS.md, phần hiện tại của 01_COURSE_ROADMAP.md và '
          '02_COURSE_STATE.md. Thực hiện chính xác ONE NEXT UNIT trong '
          'Automation/ACTIVE_UNIT.json theo quy trình khóa Robotics AI. '
          'Nếu tới checkpoint thì làm checkpoint thay vì lesson. '
          'Đọc Reference/UNIT_PROTOCOL.md, validate, commit bằng helper, cập nhật state và dừng. '
          'Tối đa 2 lần sửa trong cùng run. Không gọi controller hoặc Codex đệ quy.')

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Đường dẫn vượt thư mục khóa học')
    return path

def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(text, encoding='utf-8', newline='\n')
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'

def read_state(root):
    text = (root / '02_COURSE_STATE.md').read_text(encoding='utf-8-sig')
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('State phải có đúng một khối JSON canonical')
    block = text.split(START)[1].split(END)[0].strip()
    match = re.fullmatch(r'(?:```|~~~)json\s*\n(.*?)\n(?:```|~~~)', block, re.S)
    if not match:
        raise ValueError('Khối JSON state không hợp lệ')
    state = json.loads(match[1])
    for key in ('revision', 'course_status', 'automation_state', 'completed_lessons',
                'last_checkpoint_lesson', 'major_checkpoints_completed', 'pending_repairs',
                'next_lesson', 'last_unit', 'pause_reason', 'usage'):
        if key not in state:
            raise ValueError('State thiếu ' + key)
    return state

def read_index(root):
    index = json.loads((root / 'Reference/ROADMAP_INDEX.json').read_text(encoding='utf-8'))
    rows = index['lessons']
    if [r['number'] for r in rows] != list(range(1, len(rows)+1)):
        raise ValueError('Index lesson bị trùng hoặc không liên tục')
    roadmap = (root / '01_COURSE_ROADMAP.md').read_text(encoding='utf-8')
    table = re.findall(r'^\| (\d{3}) \| \[\[([^\]]+)\]\] \| ([^|]+) \|', roadmap, re.M)
    if [(int(n), stem) for n, stem, _ in table] != [(r['number'], r['stem']) for r in rows]:
        raise ValueError('ROADMAP_INDEX không khớp roadmap Markdown; sửa cả hai trước khi chạy')
    for (n, _, pre), row in zip(table, rows):
        refs = [int(v) for v in re.findall(r'\d+', pre)]
        if refs != row['prerequisites'] or any(v >= int(n) or v < 1 for v in refs):
            raise ValueError('Prerequisite không hợp lệ ở ' + n)
        if any(c in Path(row['path']).name for c in '\\:*?"<>|'):
            raise ValueError('Tên lesson không an toàn Windows')
        safe_path(root, row['path'])
    covered = []
    for m in index['modules']:
        covered.extend(range(m['start'], m['end']+1))
        if any(r['module'] != m['number'] for r in rows[m['start']-1:m['end']]):
            raise ValueError('Module và lesson index không khớp')
    if covered != list(range(1,len(rows)+1)):
        raise ValueError('Module không phủ đúng roadmap')
    return index

def next_unit(state, index):
    n = state['completed_lessons']
    if state['pending_repairs']:
        p = state['pending_repairs'][0]
        return dict(kind='repair', target=p['id'], path=p['path'], reason=p['reason'])
    coverage = state['last_checkpoint_lesson']
    if n - coverage >= 5 or (n == len(index['lessons']) and n > coverage):
        number = state.get('last_checkpoint_number', 0) + 1
        end = min(coverage + 5, n)
        return dict(kind='checkpoint', target=number, start=coverage+1, end=end,
                    path=f'Checkpoints/Checkpoint {number:03d} - Review Bai {coverage+1:03d} den {end:03d}.md')
    for m in index['modules']:
        if m['end'] <= n and m['number'] not in state['major_checkpoints_completed']:
            return dict(kind='major_checkpoint', target=m['number'],
                        path=f"Checkpoints/Major Checkpoint {m['number']:02d} - Part {m['number']:02d}.md")
    if n < len(index['lessons']):
        return dict(kind='lesson', target=n+1, path=index['lessons'][n]['path'])
    return None

def refresh_derived(state, index):
    n = state['completed_lessons']
    state['total_planned_lessons'] = len(index['lessons'])
    state['last_completed_lesson'] = n or None
    state['next_lesson'] = n+1 if n < len(index['lessons']) else None
    state['current_lesson'] = n or None
    projects = [(r['number'],re.search(r'PROJECT (\d{2})',r['outcome'])) for r in index['lessons'][:n]]
    introduced_projects = [(number,match[1]) for number,match in projects if match]
    state['current_project'] = (f'PROJECT {introduced_projects[-1][1]} (bài {introduced_projects[-1][0]:03d})'
                                if introduced_projects else None)
    state['current_module'] = index['lessons'][min(n, len(index['lessons'])-1)]['module']
    # Một module kết thúc vẫn hiển thị module đó tới khi major gate đã hoàn tất.
    if n and index['lessons'][n-1]['module'] not in state['major_checkpoints_completed']:
        state['current_module'] = index['lessons'][n-1]['module']
    unit = next_unit(state, index)
    state['next_unit'] = unit
    state['checkpoint_pending'] = (n - state['last_checkpoint_lesson'] >= 5 or
                                   (n == len(index['lessons']) and n > state['last_checkpoint_lesson']))
    state['current_checkpoint'] = unit['path'] if unit and 'checkpoint' in unit['kind'] else state.get('last_checkpoint')
    if unit is None and state['course_status'] != 'BLOCKED':
        state['course_status'] = 'COMPLETE'
        state['automation_state'] = 'COMPLETE'
        state['pause_reason'] = None

def render_home(root, s, index):
    m = next(m for m in index['modules'] if m['number'] == s['current_module'])
    next_lesson = 'Không còn' if s['next_lesson'] is None else f"[[{index['lessons'][s['next_lesson']-1]['stem']}]]"
    lines = ['# Robotics và AI Robot từ số 0 đến nâng cao', '',
             '> HIỂU → LÀM → ĐO → QUAN SÁT → DEBUG → GIẢI THÍCH LẠI', '',
             'Bắt đầu với [[Bai 001 - Dien la gi va mach kin dau tien]]. Chỉ đọc phần cứng cần cho bài đang học; chưa cần mua cả bộ robot.', '',
             '<!-- DASHBOARD_START -->', '| Chỉ số | Trạng thái |', '| --- | --- |',
             f"| Current Module | Part {m['number']:02d} — {m['name']} |",
             f"| Completed Lessons | {s['completed_lessons']} bài đã biên soạn và validate |",
             f"| Total Planned Lessons | {len(index['lessons'])}, có thể điều chỉnh tại checkpoint |",
             f"| Current Project | {s.get('current_project') or 'Chuẩn bị nền tảng; Project 01 ở Bài 031'} |",
             f"| Completed Projects | {len(s.get('completed_projects', []))} có minh chứng từ người học |",
             f"| Last Checkpoint | {s.get('last_checkpoint') or 'Chưa có; checkpoint đầu sau Bài 005'} |",
             f'| Next Lesson | {next_lesson} |',
             f"| Next Unit | {s.get('next_unit', {}).get('kind') if s.get('next_unit') else 'Không còn'} |",
             f"| Course % | {100*s['completed_lessons']/len(index['lessons']):.2f}% biên soạn theo roadmap hiện tại |",
             f"| Automation Status | {s['automation_state']} — {s.get('pause_reason') or 'Được phép chạy'} |",
             f"| Last Run | {s.get('last_run_date')} |", '<!-- DASHBOARD_END -->', '',
             'Số bài được viết không chứng minh người học đã thực hành. Trạng thái học hiện tại: ' + s.get('learner_progress', 'NOT_ASSESSED') + '.', '',
             '## Đi tới', '',
             '- [[01_COURSE_ROADMAP]] — 160 bài, dependency và sản phẩm từng bài.',
             '- [[02_COURSE_STATE]] — tiến độ gốc, lỗi và trạng thái tự động.',
             '- [[03_HARDWARE_ROADMAP]] — mua theo giai đoạn.',
             '- [[04_GLOSSARY]] — thuật ngữ đã thực sự được dạy.',
             '- [[05_PROJECTS]] — 20 project và tiêu chí đạt.',
             '- [[06_SKILL_TREE]] — các kỹ năng phụ thuộc nhau.',
             '- [[RESUME]] — cách tiếp tục từng unit hoặc bằng controller.',
             '- [[DEBUG_METHOD]] — tìm lỗi có phương pháp.',
             '- [[CAPSTONE_ACCEPTANCE]] — đầu ra cuối khóa.', '',
             '## Cách học một bài', '',
             'Đọc kết quả và Safety Box, dự đoán trước khi làm, ghi quan sát thật, thử Debug Lab theo giới hạn của bài, rồi tự giải thích bằng lời của mình. Chưa có dụng cụ thì ghi CHƯA THỰC HÀNH, không điền số đo tưởng tượng.', '',
             '## Ghi chú cá nhân', '', 'Viết ghi chú của bạn tại đây; controller giữ phần này khi cập nhật dashboard.']
    path = root / '00_HOME.md'
    if path.exists():
        old = path.read_text(encoding='utf-8')
        fresh = '\n'.join(lines)
        block = fresh.split('<!-- DASHBOARD_START -->')[1].split('<!-- DASHBOARD_END -->')[0]
        if '<!-- DASHBOARD_START -->' not in old or '<!-- DASHBOARD_END -->' not in old:
            raise ValueError('HOME thiếu marker; không ghi đè ghi chú người dùng')
        text = old.split('<!-- DASHBOARD_START -->')[0] + '<!-- DASHBOARD_START -->' + block + '<!-- DASHBOARD_END -->' + old.split('<!-- DASHBOARD_END -->')[1]
    else:
        text = '\n'.join(lines) + '\n'
    atomic_text(path, text)

def write_state(root, state, index):
    refresh_derived(state, index)
    state['revision'] += 1
    state['last_state_update'] = utcnow()
    path = root / '02_COURSE_STATE.md'
    old = path.read_text(encoding='utf-8') if path.exists() else '# Course State\n\n' + START + '\n' + END + '\n'
    text = old.split(START)[0] + START + '\n~~~json\n' + json_text(state) + '~~~\n' + END + old.split(END)[1]
    # Canonical ghi trước; cache và HOME có thể tái tạo nếu máy bị tắt giữa các file.
    atomic_text(path, text)
    atomic_text(root / 'Automation/AUTOMATION_STATE.json', json_text({
        'schema_version': 1, 'derived_from': '02_COURSE_STATE.md',
        'source_revision': state['revision'], 'automation_state': state['automation_state'],
        'pause_reason': state['pause_reason'], 'usage': state['usage'],
        'next_unit': state['next_unit'], 'updated_at': state['last_state_update']}))
    render_home(root, state, index)

def section(text, heading):
    match = re.search(r'^## ' + re.escape(heading) + r'\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match[1].strip() if match else ''

def validate_lesson(path, row):
    text = path.read_text(encoding='utf-8-sig')
    errors = []
    if not re.search(r'^# Bài ' + f"{row['number']:03d}" + ' - ' + re.escape(row['title']) + r'\s*$', text, re.M):
        errors.append('H1/số/tên bài không khớp roadmap')
    for h in HEADINGS:
        if not section(text, h):
            errors.append('Thiếu hoặc rỗng mục: ' + h)
    if '[!warning]' not in text:
        errors.append('Thiếu Safety Box')
    debug = section(text, 'Debug Lab')
    cases = re.split(r'^### ', debug, flags=re.M)[1:]
    if len(cases) < 3:
        errors.append('Debug Lab cần ít nhất 3 lỗi')
    for case in cases:
        for label in ('Triệu chứng', 'Nguyên nhân có thể', 'Cách đo', 'Cách sửa'):
            if label not in case:
                errors.append('Lỗi debug thiếu ' + label)
    ex = re.findall(r'^\d+\. ', section(text, 'Bài tập'), re.M)
    if not 3 <= len(ex) <= 6:
        errors.append('Bài tập phải có 3–6 mục đánh số')
    if len(re.findall(r'^\d+\. ', section(text, 'Kiểm tra hiểu bài'), re.M)) != 5:
        errors.append('Kiểm tra hiểu bài phải có 5 câu đánh số')
    if not 5 <= len(re.findall(r'^- ', section(text, 'Ghi nhớ'), re.M)) <= 10:
        errors.append('Ghi nhớ phải có 5–10 dòng')
    if 'STEP 1' not in section(text, 'Thực hành'):
        errors.append('Thực hành cần STEP')
    return errors

def validate_artifact(root, unit, index):
    path = safe_path(root, unit['path'])
    if not path.is_file():
        return ['Không có file unit: ' + unit['path']]
    if unit['kind'] == 'lesson':
        return validate_lesson(path, index['lessons'][unit['target']-1])
    text = path.read_text(encoding='utf-8')
    if unit['kind'] == 'repair':
        row = next((r for r in index['lessons'] if r['path'] == unit['path']), None)
        return validate_lesson(path, row) if row else ([] if text.strip() else ['File repair rỗng'])
    errors = []
    expected = (f"# Checkpoint {unit['target']:03d} - Review Bài {unit['start']:03d} đến {unit['end']:03d}"
                if unit['kind'] == 'checkpoint' else
                f"# Major Checkpoint {unit['target']:02d} - Part {unit['target']:02d}")
    if expected not in text.splitlines():
        errors.append('Title checkpoint sai')
    for h in ('Phạm vi và bằng chứng', 'Đánh giá 16 tiêu chí', 'Lỗi và sửa đổi', 'Quyết định gate', 'Cập nhật state'):
        if not section(text,h):
            errors.append('Thiếu mục checkpoint: ' + h)
    table = re.findall(r'^\| (\d+) \|[^\n]+', section(text,'Đánh giá 16 tiêu chí'), re.M)
    if [int(v) for v in table] != list(range(1,17)):
        errors.append('Checkpoint thiếu 16 dòng tiêu chí')
    if unit['kind'] == 'major_checkpoint' and not section(text,'Major checkpoint bổ sung'):
        errors.append('Thiếu audit và readiness của major checkpoint')
    return errors

def inventory(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in (root/'Lessons').glob('Part_*/*.md')}

def validate_course(root, state, index):
    errors = []
    n = state['completed_lessons']
    if type(n) is not int or not 0 <= n <= len(index['lessons']):
        return ['completed_lessons vượt giới hạn']
    if not 0 <= state['last_checkpoint_lesson'] <= n or n-state['last_checkpoint_lesson'] > 5:
        errors.append('Checkpoint coverage không hợp lệ hoặc bị bỏ qua')
    if state['next_lesson'] != (n+1 if n < len(index['lessons']) else None):
        errors.append('next_lesson không khớp tiến độ')
    if state['automation_state'] not in ('PAUSED','RUNNING','COMPLETE'):
        errors.append('Automation state sai enum')
    if state['course_status'] not in ('IN_PROGRESS','BLOCKED','COMPLETE'):
        errors.append('Course status sai enum')
    paths = inventory(root)
    expected = {r['path'] for r in index['lessons'][:n]}
    for missing in sorted(expected-set(paths)):
        errors.append('Thiếu bài đã hoàn thành: ' + missing)
    nums = [re.search(r'Bai (\d{3}) - ', Path(p).name) for p in paths]
    values = [v[1] for v in nums if v]
    if len(set(values)) != len(values) or any(v is None for v in nums):
        errors.append('Duplicate lesson hoặc tên không hợp lệ')
    # Cho phép đúng một bản nháp đang active, không cho bài ngoài unit.
    active_path = root / 'Automation/ACTIVE_UNIT.json'
    active = json.loads(active_path.read_text(encoding='utf-8')) if active_path.exists() else None
    allowed = {active['path']} if active and active['kind'] == 'lesson' else set()
    if set(paths) - expected - allowed:
        errors.append('Có lesson ngoài tiến độ và active unit')
    if state['course_status'] == 'COMPLETE' and next_unit(state,index) is not None:
        errors.append('COMPLETE khi còn unit')
    if n:
        errors += validate_lesson(root/index['lessons'][n-1]['path'],index['lessons'][n-1]) if (root/index['lessons'][n-1]['path']).exists() else []
    last = state.get('last_unit')
    if last:
        receipt_path = safe_path(root,last['receipt'])
        if not receipt_path.exists():
            errors.append('Thiếu receipt của last unit')
        else:
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            if receipt['id'] != last['id'] or receipt['sha256'] != digest(root/last['path']):
                errors.append('Receipt/hash không khớp last unit')
    return errors

def semantic_errors(review):
    errors = []
    for key in SEMANTIC:
        item = review.get('checks',{}).get(key,{})
        if item.get('passed') is not True or len(item.get('evidence','').strip()) < 12:
            errors.append('Review chưa đạt/thiếu bằng chứng: ' + key)
    if review.get('repair_attempts',0) not in (0,1,2):
        errors.append('Vượt 2 lần sửa hoặc giá trị không hợp lệ')
    if not review.get('test_level'):
        errors.append('Thiếu mức kiểm thử thực tế')
    return errors

def prepare_commit(root, review_path):
    index = read_index(root)
    state = read_state(root)
    active = json.loads((root/'Automation/ACTIVE_UNIT.json').read_text(encoding='utf-8'))
    if state['revision'] != active['start_revision']:
        raise ValueError('State đổi trong lúc viết; không commit đè')
    if next_unit(state,index) != {k:v for k,v in active.items() if k in ('kind','target','path','reason','start','end')}:
        raise ValueError('ACTIVE_UNIT không còn là next unit')
    review = json.loads(Path(review_path).read_text(encoding='utf-8'))
    errors = validate_artifact(root,active,index) + semantic_errors(review)
    changed = {p for p,h in inventory(root).items() if active['lesson_hashes'].get(p) != h}
    deleted = set(active['lesson_hashes']) - set(inventory(root))
    allowed = {active['path']}
    urgent = review.get('urgent_safety_fixes',[])
    if urgent and active['kind'] not in ('checkpoint','major_checkpoint'):
        errors.append('Chỉ checkpoint được sửa lỗi safety khẩn ở bài cũ ngoài target')
    for fix in urgent:
        safe_path(root,fix['path'])
        if not fix.get('reason') or fix['path'] not in active['lesson_hashes']:
            errors.append('Sửa safety thiếu lý do hoặc không phải bài cũ')
        allowed.add(fix['path'])
        row = next(r for r in index['lessons'] if r['path'] == fix['path'])
        errors += validate_lesson(root/fix['path'],row)
    if changed - allowed or deleted:
        errors.append('Unit sửa thêm lesson ngoài phạm vi hoặc xóa lesson')
    repairs = review.get('pending_repairs',[])
    if active['kind'] in ('checkpoint','major_checkpoint'):
        if review.get('gate') not in ('PASS','NEEDS_REPAIR'):
            errors.append('Checkpoint thiếu gate')
        if (review.get('gate') == 'NEEDS_REPAIR') != bool(repairs):
            errors.append('Gate và pending_repairs không khớp')
        for p in repairs:
            if not all(p.get(k) for k in ('id','path','reason','required_changes')):
                errors.append('Repair thiếu thông tin')
            safe_path(root,p['path'])
    if errors:
        raise ValueError('; '.join(errors))
    receipt = dict(id=active['id'], kind=active['kind'], target=active['target'], path=active['path'],
                   sha256=digest(root/active['path']), completed_at=utcnow(), review=review)
    receipt_rel = f"Automation/Receipts/{active['id']}.json"
    receipt_path = root/receipt_rel
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    with receipt_path.open('x',encoding='utf-8') as f:
        f.write(json_text(receipt))
    kind = active['kind']
    if kind == 'lesson':
        state['completed_lessons'] += 1
    elif kind == 'checkpoint':
        state['last_checkpoint_lesson'] = active['end']
        state['last_checkpoint_number'] = active['target']
        state['last_checkpoint'] = active['path']
        state['pending_repairs'].extend(repairs)
    elif kind == 'major_checkpoint':
        if review['gate'] == 'PASS':
            state['major_checkpoints_completed'].append(active['target'])
        state['last_major_checkpoint'] = active['path']
        state['pending_repairs'].extend(repairs)
    elif kind == 'repair':
        state['pending_repairs'] = [p for p in state['pending_repairs'] if p['id'] != active['target']]
    for field in ('hardware_already_introduced','concepts_already_taught'):
        state[field] = list(dict.fromkeys(state.get(field,[]) + review.get(field,[])))
    if 'concepts_not_yet_taught' in review:
        state['concepts_not_yet_taught'] = review['concepts_not_yet_taught']
    state['last_unit'] = {k:receipt[k] for k in ('id','kind','target','path')}
    state['last_unit']['receipt'] = receipt_rel
    state['last_run_date'] = receipt['completed_at']
    state['validation_status'] = 'PASS_STRUCTURAL_AND_AUTHOR_REVIEW'
    write_state(root,state,index)
    return receipt

def resolve_codex(explicit=None):
    candidate = explicit or shutil.which('codex.exe') or shutil.which('codex.ps1') or shutil.which('codex')
    if not candidate:
        raise FileNotFoundError('Không tìm thấy Codex CLI trên PATH')
    path = Path(candidate).resolve()
    if path.suffix.lower() in ('.ps1','.cmd'):
        ps1 = path.with_suffix('.ps1')
        shell = shutil.which('pwsh') or shutil.which('powershell')
        if ps1.exists() and shell:
            return [shell,'-NoProfile','-NonInteractive','-File',str(ps1)]
        raise ValueError('Cần codex.exe hoặc wrapper codex.ps1 cùng PowerShell; truyền --codex')
    return [str(path)]

def popen(command, **kwargs):
    options = dict(text=True,encoding='utf-8',errors='replace',
                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    options.update(kwargs)
    return subprocess.Popen(command,**options)

def kill_owned(process):
    if process.poll() is None:
        if os.name == 'nt':
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW,timeout=10)
        else:
            process.kill()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

def read_pump(stream, events, name):
    try:
        for line in iter(stream.readline,''):
            events.put((name,line))
    finally:
        events.put((name,None))

def capture(command,timeout=20):
    p = popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        out,err = p.communicate(timeout=timeout)
        if p.returncode:
            raise RuntimeError('CLI feature probe thất bại')
        return out
    finally:
        kill_owned(p)

def detect_features(command):
    top = capture(command+['--help'])
    if not re.search(r'^\s+exec\s',top,re.M):
        raise RuntimeError('CLI không cung cấp exec trong help')
    helptext = capture(command+['exec','--help'])
    for flag in ('--json','--skip-git-repo-check','--sandbox','--cd'):
        if flag not in helptext and flag not in top:
            raise RuntimeError('CLI thiếu tính năng bắt buộc: ' + flag)
    return {'version':capture(command+['--version']).strip(),
            'app_server':bool(re.search(r'^\s+app-server\s',top,re.M)),
            'search':'--search' in top, 'approval':'--ask-for-approval' in top}

def unavailable(reason):
    return dict(mode='UNAVAILABLE',source=None,checked_at=utcnow(),
                five_hour_remaining=None,weekly_remaining=None,
                five_hour_resets_at=None,weekly_resets_at=None,reason=reason,reached=False)

def normalize_usage(result):
    value = unavailable('MISSING_OR_INVALID_WINDOWS')
    value['source'] = 'Codex app-server account/rateLimits/read'
    buckets = result.get('rateLimitsByLimitId')
    if buckets is not None:
        bucket = buckets.get('codex') if isinstance(buckets,dict) else None
    else:
        bucket = result.get('rateLimits')
        if bucket and bucket.get('limitId') not in (None,'codex'):
            bucket = None
    if not isinstance(bucket,dict):
        return value
    value['reached'] = bool(bucket.get('rateLimitReachedType') or bucket.get('spendControlReached'))
    windows = [bucket.get('primary'),bucket.get('secondary')]
    for window in windows:
        if not isinstance(window,dict):
            continue
        mins,used = window.get('windowDurationMins'),window.get('usedPercent')
        if mins not in (300,10080) or type(used) not in (int,float) or not math.isfinite(used) or used < 0:
            continue
        prefix = 'five_hour' if mins == 300 else 'weekly'
        reset = window.get('resetsAt')
        if reset is not None and (type(reset) not in (int,float) or not math.isfinite(reset)):
            continue
        # Dữ liệu hết hạn không được tái dùng để cho phép một unit mới.
        if reset is not None and reset <= time.time():
            continue
        remaining = max(0.0,min(100.0,100-used))
        previous = value[prefix+'_remaining']
        value[prefix+'_remaining'] = min(previous,remaining) if previous is not None else remaining
        value[prefix+'_resets_at'] = datetime.fromtimestamp(reset,timezone.utc).isoformat() if reset else None
    if value['five_hour_remaining'] is not None and value['weekly_remaining'] is not None:
        value['mode'] = 'AVAILABLE'
        value['reason'] = None
    return value

def probe_usage(command,features):
    if not features.get('app_server'):
        return unavailable('APP_SERVER_NOT_ADVERTISED')
    p = None
    try:
        helptext = capture(command+['app-server','--help'])
        if '--stdio' in helptext:
            extra = ['--stdio']
        elif '--listen' in helptext and 'stdio://' in helptext:
            extra = ['--listen','stdio://']
        else:
            return unavailable('NO_DOCUMENTED_STDIO_TRANSPORT')
        p = popen(command+['app-server']+extra,stdin=subprocess.PIPE,
                  stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        events = queue.Queue()
        for name,stream in [('stdout',p.stdout),('stderr',p.stderr)]:
            threading.Thread(target=read_pump,args=(stream,events,name),daemon=True).start()
        def send(message):
            p.stdin.write(json.dumps(message)+'\n')
            p.stdin.flush()
        def receive(request_id):
            until = time.monotonic()+20
            while time.monotonic() < until:
                try:
                    source,line = events.get(timeout=min(0.5,max(0.01,until-time.monotonic())))
                except queue.Empty:
                    if p.poll() is not None:
                        raise RuntimeError('APP_SERVER_EXITED')
                    continue
                if source != 'stdout' or line is None:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if message.get('id') == request_id:
                    if 'error' in message:
                        err = message['error']
                        reason = 'RATE_LIMIT_ERROR' if re.search(r'rate.?limit|usage.?limit|quota',str(err),re.I) else 'RPC_UNSUPPORTED_OR_AUTH_UNAVAILABLE'
                        raise RuntimeError(reason)
                    return message['result']
            raise TimeoutError('APP_SERVER_TIMEOUT')
        send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'robotics_course_guard','title':'Robotics course usage guard','version':'1.0.0'}}})
        receive(1)
        send({'method':'initialized','params':{}})
        send({'id':2,'method':'account/rateLimits/read'})
        return normalize_usage(receive(2))
    except (OSError,ValueError,RuntimeError,TimeoutError) as exc:
        value = unavailable(str(exc))
        value['reached'] = str(exc) == 'RATE_LIMIT_ERROR'
        return value
    finally:
        if p is not None:
            if p.stdin:
                try:
                    p.stdin.close()
                except OSError:
                    pass
            kill_owned(p)

def usage_low(usage):
    return bool(usage.get('reached')) or any(usage.get(k) is not None and usage[k] <= 10
                                          for k in ('five_hour_remaining','weekly_remaining'))

def pause(root,state,index,reason,blocked=False,problem=None):
    state['automation_state'] = 'PAUSED'
    state['pause_reason'] = reason
    if blocked:
        state['course_status'] = 'BLOCKED'
    if problem:
        state['known_problems'] = list(dict.fromkeys(state.get('known_problems',[]) + [problem]))
    write_state(root,state,index)

def execute_unit(root,command,features,active,timeout):
    args = command + ['-a','never'] if features.get('approval') else command[:]
    if features.get('search'):
        args += ['--search']
    args += ['exec','--json','--skip-git-repo-check','--sandbox','workspace-write','--cd',str(root),'-']
    logpath = root / f"Automation/Logs/{active['id']}.jsonl"
    p = popen(args,cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    events = queue.Queue()
    for name,stream in [('stdout',p.stdout),('stderr',p.stderr)]:
        threading.Thread(target=read_pump,args=(stream,events,name),daemon=True).start()
    finished_streams,completed = set(),False
    until = time.monotonic()+timeout
    try:
        p.stdin.write(PROMPT+'\n')
        p.stdin.close()
        with logpath.open('x',encoding='utf-8') as log:
            while len(finished_streams) < 2:
                if time.monotonic() > until:
                    raise TimeoutError('UNIT_TIMEOUT')
                try:
                    source,line = events.get(timeout=0.25)
                except queue.Empty:
                    continue
                if line is None:
                    finished_streams.add(source)
                    continue
                log.write(json.dumps({'at':utcnow(),'stream':source,'data':line.rstrip()},ensure_ascii=False)+'\n')
                log.flush()
                if source == 'stderr':
                    if re.search(r'(rate.?limit|usage.?limit|quota).*(exceed|reach|error)|too many requests',line,re.I):
                        raise RuntimeError('RATE_LIMIT_ERROR')
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get('type') in ('error','turn.failed'):
                    reason = 'RATE_LIMIT_ERROR' if re.search(r'rate.?limit|usage.?limit|quota|too many requests',str(event),re.I) else 'CODEX_ERROR'
                    raise RuntimeError(reason)
                if event.get('type') == 'turn.completed':
                    completed = True
        code = p.wait(timeout=max(1,until-time.monotonic()))
        if code != 0 or not completed:
            raise RuntimeError('CODEX_FAILED_OR_NO_COMPLETION_EVENT')
    finally:
        kill_owned(p)

def validate_transition(root,before,after,active,index):
    errors = validate_course(root,after,index)
    last = after.get('last_unit') or {}
    if after['revision'] <= before['revision'] or last.get('id') != active['id']:
        errors.append('Codex chưa cập nhật state cho đúng unit')
    for key in ('kind','target','path'):
        if last.get(key) != active[key]:
            errors.append('last_unit sai ' + key)
    expected_count = before['completed_lessons'] + (1 if active['kind']=='lesson' else 0)
    if after['completed_lessons'] != expected_count:
        errors.append('Một run tăng sai số lesson')
    checkpoint_end = active['end'] if active['kind']=='checkpoint' else before['last_checkpoint_lesson']
    if after['last_checkpoint_lesson'] != checkpoint_end:
        errors.append('Checkpoint coverage thay đổi ngoài unit')
    current_hashes = inventory(root)
    changed = {p for p,h in current_hashes.items() if active['lesson_hashes'].get(p) != h}
    allowed = {active['path']}
    if last.get('receipt') and (root/last['receipt']).exists():
        receipt = json.loads((root/last['receipt']).read_text(encoding='utf-8'))
        errors += semantic_errors(receipt['review'])
        if active['kind'] in ('checkpoint','major_checkpoint'):
            allowed.update(fix['path'] for fix in receipt['review'].get('urgent_safety_fixes',[]))
    if changed - allowed or set(active['lesson_hashes']) - set(current_hashes):
        errors.append('Lesson bị thay đổi ngoài phạm vi sau commit')
    if after['course_status'] == 'BLOCKED':
        errors.append('Agent đã ghi BLOCKED')
    if errors:
        raise ValueError('; '.join(errors))

def run_controller(root,args):
    index,state = read_index(root),read_state(root)
    errors = validate_course(root,state,index)
    if errors:
        if not args.dry_run and not args.validate_only:
            pause(root,state,index,'VALIDATION_FAILED',True,'; '.join(errors))
        raise ValueError('; '.join(errors))
    if args.validate_only:
        print('PASS: cấu trúc, roadmap, state, bài gần nhất và receipt. Semantic/hardware xem receipt.')
        return
    if args.dry_run:
        print(json_text({'read_only':True,'state':state['automation_state'],'pause_reason':state['pause_reason'],
                         'resume_requested':args.resume,'next_unit':next_unit(state,index),
                         'usage_action':'Probe trực tiếp trước mỗi unit thật; dry-run không gọi Codex.'}))
        return
    if state['course_status'] == 'COMPLETE':
        print('COMPLETE — không còn unit.')
        return
    if state['course_status'] == 'BLOCKED':
        raise RuntimeError('BLOCKED: sửa known_problems và validate trước; --resume không xóa lỗi.')
    if state['automation_state'] == 'PAUSED' and not args.resume:
        print('PAUSED — ' + str(state['pause_reason']) + '. Chỉ --resume hoặc yêu cầu tiếp tục mới cho chạy.')
        return
    active_path = root/'Automation/ACTIVE_UNIT.json'
    if active_path.exists():
        raise RuntimeError('Có ACTIVE_UNIT chưa xử lý. Đọc RESUME.md; không tự ghi đè hoặc retry.')
    command = resolve_codex(args.codex)
    features = detect_features(command)
    state['automation_state'],state['pause_reason'] = 'RUNNING',None
    state['automation_cli_version'] = features['version']
    write_state(root,state,index)
    session = root/f"Automation/Logs/controller-{uuid.uuid4().hex}.jsonl"
    unknown_since_checkpoint = state.get('usage_unavailable_since_checkpoint',False)
    for _ in range(args.max_units):
        index = read_index(root)
        state = read_state(root)
        if state['automation_state'] != 'RUNNING':
            return
        unit = next_unit(state,index)
        if unit is None:
            write_state(root,state,index)
            return
        usage = probe_usage(command,features)
        state['usage'] = usage
        unknown_since_checkpoint |= usage['mode'] == 'UNAVAILABLE'
        state['usage_unavailable_since_checkpoint'] = unknown_since_checkpoint
        with session.open('a',encoding='utf-8') as log:
            log.write(json.dumps({'at':utcnow(),'unit':unit,'usage':usage},ensure_ascii=False)+'\n')
        if usage_low(usage):
            pause(root,state,index,'USAGE_GUARD')
            print('PAUSED / USAGE_GUARD; không bắt đầu unit. Checkpoint pending được giữ.')
            return
        # Khi không có usage, không bao giờ đi quá lesson thứ 5 trước checkpoint.
        if usage['mode'] == 'UNAVAILABLE' and unit['kind']=='lesson' and state['completed_lessons']-state['last_checkpoint_lesson'] >= 5:
            pause(root,state,index,'USAGE_DATA_UNAVAILABLE_SAFE_PAUSE')
            return
        write_state(root,state,index)
        active = dict(unit,id=uuid.uuid4().hex,start_revision=state['revision'],
                      usage=usage,created_at=utcnow(),lesson_hashes=inventory(root))
        atomic_text(active_path,json_text(active))
        before = copy.deepcopy(state)
        try:
            print(f"Bắt đầu {unit['kind']} {unit['target']} — {unit['path']}",flush=True)
            execute_unit(root,command,features,active,args.timeout)
            index = read_index(root)
            after = read_state(root)
            validate_transition(root,before,after,active,index)
        except BaseException as exc:
            current = read_state(root)
            reason = 'RATE_LIMIT_ERROR' if 'RATE_LIMIT_ERROR' in str(exc) else 'UNIT_FAILED'
            # Lỗi CLI có thể để lại draft/commit dở; không tự lùi tiến độ hay xóa file.
            pause(root,current,index,reason,blocked=(reason!='RATE_LIMIT_ERROR'),problem=str(exc))
            raise
        active_path.unlink()
        print('PASS unit; state và receipt đã xác thực.',flush=True)
        if after['course_status'] == 'COMPLETE':
            return
        if unit['kind']=='checkpoint' and unknown_since_checkpoint:
            after['usage_unavailable_since_checkpoint'] = False
            pause(root,after,index,'USAGE_DATA_UNAVAILABLE_SAFE_PAUSE')
            print('Checkpoint hoàn tất. PAUSED vì không có dữ liệu usage đầy đủ trong batch.')
            return
        if after['automation_state'] != 'RUNNING':
            return
    pause(root,read_state(root),index,'MAX_UNITS_REACHED')

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    for flag in ('resume','dry-run','validate-only','probe-usage','self-test'):
        parser.add_argument('--'+flag,action='store_true')
    parser.add_argument('--max-units',type=int,default=1000)
    parser.add_argument('--timeout',type=int,default=2700)
    parser.add_argument('--codex')
    parser.add_argument('--commit',type=Path,metavar='REVIEW_JSON')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not 1 <= args.max_units <= 1000 or not 60 <= args.timeout <= 7200:
        parser.error('max-units 1..1000, timeout 60..7200')
    if sum(bool(getattr(args,k)) for k in ('dry_run','validate_only','probe_usage','self_test','commit')) > 1:
        parser.error('Chỉ chọn một chế độ kiểm tra/commit')
    if args.self_test:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_controller.py')
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if args.commit:
        receipt = prepare_commit(root,args.commit)
        print('COMMITTED: '+receipt['id'])
        return 0
    if args.probe_usage:
        command = resolve_codex(args.codex)
        print(json_text(probe_usage(command,detect_features(command))))
        return 0
    lock = root/'Automation/controller.lock'
    owns_lock = False
    try:
        if not args.dry_run and not args.validate_only:
            lock.parent.mkdir(parents=True,exist_ok=True)
            with lock.open('x',encoding='utf-8') as f:
                f.write(json_text({'pid':os.getpid(),'created_at':utcnow()}))
            owns_lock = True
        run_controller(root,args)
        return 0
    except (Exception,KeyboardInterrupt) as exc:
        if owns_lock:
            try:
                log = root/'Automation/Logs/controller-errors.jsonl'
                with log.open('a',encoding='utf-8') as f:
                    f.write(json.dumps({'at':utcnow(),'error':str(exc)},ensure_ascii=False)+'\n')
                current = read_state(root)
                if current['course_status'] != 'COMPLETE' and current['pause_reason'] not in ('RATE_LIMIT_ERROR','UNIT_FAILED','VALIDATION_FAILED'):
                    pause(root,current,read_index(root),'CONTROLLER_ERROR',True,str(exc))
            except Exception:
                pass  # State bị hỏng vẫn giữ file/log, không ghi đè tiến độ bằng giá trị đoán.
        print('STOP: '+str(exc),file=sys.stderr)
        return 1
    finally:
        if owns_lock:
            lock.unlink(missing_ok=True)

if __name__ == '__main__':
    raise SystemExit(main())
