from pathlib import Path
import subprocess
import time
import re
import sys


# ============================================================
# CONFIG
# ============================================================

# ĐỔI đường dẫn này thành folder khóa Python trong Obsidian của bạn.
COURSE_FOLDER = Path(
    r"C:\Users\truon\OneDrive\Tài liệu\Obsidian Vault\Python"
)

PROGRESS_FILE = COURSE_FOLDER / "00 - COURSE PROGRESS.md"
CHECKPOINT_FILE = COURSE_FOLDER / "Checkpoint.md"

# Nghỉ rất ngắn giữa hai lượt Codex.
PAUSE_BETWEEN_RUNS = 2

# Safety limit.
# Tránh script chạy vô hạn nếu COURSE PROGRESS bị lỗi.
MAX_RUNS = 500


# ============================================================
# HELPERS
# ============================================================

def read_progress():
    """Đọc trạng thái hiện tại của khóa học."""

    if not PROGRESS_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy progress file:\n{PROGRESS_FILE}"
        )

    return PROGRESS_FILE.read_text(
        encoding="utf-8"
    )


def checkpoint_due(progress):
    """
    Kiểm tra COURSE PROGRESS có yêu cầu checkpoint không.

    Chấp nhận:
    Checkpoint Due: YES
    Checkpoint Due: Yes
    Checkpoint Due: yes
    """

    return bool(
        re.search(
            r"Checkpoint\s+Due\s*:\s*YES",
            progress,
            flags=re.IGNORECASE,
        )
    )


def course_finished(progress):
    """
    Optional:
    Master Prompt có thể ghi một trong các trạng thái này
    khi khóa học hoàn thành.
    """

    patterns = [
        r"Course\s+Status\s*:\s*COMPLETE",
        r"Course\s+Complete\s*:\s*YES",
        r"Status\s*:\s*COMPLETE",
    ]

    return any(
        re.search(
            pattern,
            progress,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def run_codex(prompt):
    """
    Chạy một lượt Codex và CHỜ cho đến khi Codex hoàn thành.

    Chỉ khi process kết thúc,
    Python mới tiếp tục vòng lặp.
    """

    print()
    print("=" * 70)
    print("GỬI CHO CODEX:")
    print(prompt)
    print("=" * 70)
    print()

    command = [
    "codex",
    "exec",
    "--skip-git-repo-check",
    "--sandbox",
    "workspace-write",
    "-C",
    str(COURSE_FOLDER),
    prompt,
]

    result = subprocess.run(
        command,
        cwd=COURSE_FOLDER,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Codex kết thúc với error code: "
            f"{result.returncode}"
        )


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print()
    print("PYTHON SCHOOL AUTO RUNNER")
    print("=========================")
    print(f"Course: {COURSE_FOLDER}")
    print()

    if not COURSE_FOLDER.exists():
        print("ERROR: COURSE_FOLDER không tồn tại.")
        sys.exit(1)

    if not PROGRESS_FILE.exists():
        print("ERROR: Không tìm thấy COURSE PROGRESS.")
        sys.exit(1)

    if not CHECKPOINT_FILE.exists():
        print("ERROR: Không tìm thấy checkpoint.md.")
        sys.exit(1)

    for run_number in range(1, MAX_RUNS + 1):

        progress_before = read_progress()

        # ----------------------------------------------------
        # COURSE COMPLETE?
        # ----------------------------------------------------

        if course_finished(progress_before):

            print()
            print("🎓 COURSE COMPLETE")
            print("Không còn bài cần tạo.")
            return

        # ----------------------------------------------------
        # DECIDE WHAT CODEX SHOULD DO
        # ----------------------------------------------------

        if checkpoint_due(progress_before):

            action = "CHECKPOINT"

            prompt = """
Đọc và thực hiện đầy đủ file:

Checkpoint.md

Không tạo bài mới.
Sau khi hoàn tất checkpoint, cập nhật COURSE PROGRESS và dừng.
""".strip()

        else:

            action = "NEXT LESSON"

            prompt = "tiếp tục"

        print()
        print(
            f"[RUN {run_number}] "
            f"{action}"
        )

        # ----------------------------------------------------
        # RUN CODEX AND WAIT UNTIL FINISHED
        # ----------------------------------------------------

        run_codex(prompt)

        # ----------------------------------------------------
        # VERIFY THAT SOMETHING CHANGED
        # ----------------------------------------------------

        progress_after = read_progress()

        if progress_after == progress_before:

            print()
            print("⚠️ COURSE PROGRESS không thay đổi.")
            print()
            print(
                "Script dừng để tránh gọi Codex "
                "liên tục khi workflow có lỗi."
            )

            return

        print()
        print("✓ Codex hoàn thành lượt hiện tại.")

        time.sleep(PAUSE_BETWEEN_RUNS)

    print()
    print(
        f"Đã đạt MAX_RUNS = {MAX_RUNS}. "
        "Script dừng vì safety limit."
    )


if __name__ == "__main__":
    main()