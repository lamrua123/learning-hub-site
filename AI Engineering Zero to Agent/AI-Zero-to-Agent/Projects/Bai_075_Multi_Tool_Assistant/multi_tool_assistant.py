import hashlib
import json
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
STATE_PATH = PROJECT_DIR / "assistant_state.json"
MAX_STEPS = 6


def new_state():
    return {
        "status": "running",
        "step_count": 0,
        "working_memory": [],
        "trace": [],
        "pending_action": None,
        "approved_fingerprints": [],
        "final_answer": None,
    }


def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return new_state()


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def resolve_inside_data(relative_path):
    target = (DATA_DIR / relative_path).resolve()
    data_root = DATA_DIR.resolve()
    if target != data_root and data_root not in target.parents:
        raise ValueError("Đường dẫn nằm ngoài thư mục data được phép")
    return target


def read_text(args):
    path = resolve_inside_data(args["path"])
    with open(path, "r", encoding="utf-8") as file:
        return {"path": args["path"], "text": file.read()}


def calculate_total(args):
    numbers = args["numbers"]
    if not isinstance(numbers, list) or not numbers:
        raise ValueError("numbers phải là list không rỗng")
    if not all(
        isinstance(number, (int, float)) and not isinstance(number, bool)
        for number in numbers
    ):
        raise ValueError("Mọi phần tử trong numbers phải là số")
    return {"count": len(numbers), "total": sum(numbers)}


def write_report(args):
    path = resolve_inside_data(args["path"])
    content = args["content"]
    if path.exists():
        old_content = path.read_text(encoding="utf-8")
        if old_content == content:
            return {"path": args["path"], "status": "already_written"}
        raise FileExistsError("File đã tồn tại với nội dung khác")
    path.write_text(content, encoding="utf-8")
    return {"path": args["path"], "status": "written"}


TOOLS = {
    "read_text": {
        "required": {"path": str},
        "risk": "read_only",
        "function": read_text,
    },
    "calculate_total": {
        "required": {"numbers": list},
        "risk": "read_only",
        "function": calculate_total,
    },
    "write_report": {
        "required": {"path": str, "content": str},
        "risk": "side_effect",
        "function": write_report,
    },
}


def validate_action(action):
    if set(action) != {"type", "tool", "args"}:
        raise ValueError("Action phải có đúng type, tool và args")
    if action["type"] != "tool_call":
        raise ValueError("type không hợp lệ")
    if action["tool"] not in TOOLS:
        raise ValueError("Tool không nằm trong allowlist")

    schema = TOOLS[action["tool"]]["required"]
    args = action["args"]
    if not isinstance(args, dict) or set(args) != set(schema):
        raise ValueError("Arguments không khớp schema")
    for name, expected_type in schema.items():
        if not isinstance(args[name], expected_type):
            raise ValueError(f"Argument {name} sai kiểu")


def action_fingerprint(action):
    canonical = json.dumps(action, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def latest_result(state, tool_name):
    for item in reversed(state["working_memory"]):
        if item["tool"] == tool_name:
            return item["result"]
    return None


def extract_amounts(text):
    amounts = []
    for line in text.splitlines():
        match = re.search(r":\s*(\d+)\s*$", line)
        if match:
            amounts.append(int(match.group(1)))
    return amounts


def mock_model(state):
    """Mô phỏng model trả structured output để demo chạy không cần API."""
    read_result = latest_result(state, "read_text")
    total_result = latest_result(state, "calculate_total")
    write_result = latest_result(state, "write_report")

    if read_result is None:
        return {
            "type": "tool_call",
            "tool": "read_text",
            "args": {"path": "chi_phi.txt"},
        }

    if total_result is None:
        return {
            "type": "tool_call",
            "tool": "calculate_total",
            "args": {"numbers": extract_amounts(read_result["text"])},
        }

    report = (
        "# Báo cáo chi phí\n\n"
        f"Có {total_result['count']} khoản chi.\n\n"
        f"Tổng cộng: {total_result['total']:,} đồng.\n"
    )
    if write_result is None:
        return {
            "type": "tool_call",
            "tool": "write_report",
            "args": {"path": "bao_cao.md", "content": report},
        }

    return {
        "type": "final",
        "answer": (
            f"Đã đọc {read_result['path']}, tính tổng "
            f"{total_result['total']:,} đồng và lưu báo cáo tại "
            f"{write_result['path']}."
        ),
    }


def request_approval(state, action):
    fingerprint = action_fingerprint(action)
    state["status"] = "waiting_approval"
    state["pending_action"] = {
        "action": action,
        "fingerprint": fingerprint,
        "reason": "Tool sẽ tạo file mới",
    }
    save_state(state)
    print("Đã dừng trước action có tác dụng phụ:")
    print(json.dumps(state["pending_action"], ensure_ascii=False, indent=2))


def receive_approval(state):
    pending = state["pending_action"]
    print("Đang chờ duyệt action:")
    print(json.dumps(pending, ensure_ascii=False, indent=2))
    decision = input("Nhập approve hoặc reject: ").strip().lower()

    if decision == "approve":
        state["approved_fingerprints"].append(pending["fingerprint"])
        state["pending_action"] = None
        state["status"] = "running"
    elif decision == "reject":
        state["status"] = "rejected"
    else:
        print("Decision không hợp lệ; workflow vẫn chờ.")
    save_state(state)


def run_agent(state):
    while state["status"] == "running":
        if state["step_count"] >= MAX_STEPS:
            state["status"] = "failed"
            state["trace"].append({"event": "stop", "reason": "step_limit"})
            save_state(state)
            return

        decision = mock_model(state)
        state["trace"].append({"event": "model_decision", "data": decision})

        if decision.get("type") == "final":
            state["final_answer"] = decision["answer"]
            state["status"] = "completed"
            save_state(state)
            print(decision["answer"])
            return

        try:
            validate_action(decision)
            tool_spec = TOOLS[decision["tool"]]
            fingerprint = action_fingerprint(decision)
            needs_approval = (
                tool_spec["risk"] == "side_effect"
                and fingerprint not in state["approved_fingerprints"]
            )
            if needs_approval:
                request_approval(state, decision)
                return

            result = tool_spec["function"](decision["args"])
            observation = {"tool": decision["tool"], "result": result}
            state["working_memory"].append(observation)
            state["trace"].append({"event": "observation", "data": observation})
            state["step_count"] += 1
            save_state(state)
            print("Observation:", json.dumps(observation, ensure_ascii=False))
        except (KeyError, TypeError, ValueError, OSError) as error:
            state["trace"].append(
                {"event": "tool_error", "error_type": type(error).__name__, "message": str(error)}
            )
            state["status"] = "failed"
            save_state(state)
            print("Agent dừng an toàn:", type(error).__name__, str(error))
            return


state = load_state()

if state["status"] == "waiting_approval":
    receive_approval(state)

if state["status"] == "running":
    run_agent(state)
else:
    print("Trạng thái hiện tại:", state["status"])
