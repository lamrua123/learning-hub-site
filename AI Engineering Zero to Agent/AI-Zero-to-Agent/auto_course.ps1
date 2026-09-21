# ============================================================
# AI ENGINEERING - CODEX AUTO COURSE
#
# Chức năng:
# - Đọc COURSE_STATE.md
# - Tự chạy tới checkpoint gần nhất
# - Mỗi Codex invocation chỉ tạo 1 bài
# - Hiển thị Codex realtime
# - Ghi log
# - Dừng nếu Codex lỗi
# - Dừng nếu COURSE_STATE không tiến triển
# - Không chạy vượt checkpoint
# ============================================================


# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

$DelaySeconds = 5

$Prompt = "tiếp tục"

$Root = $PSScriptRoot

$StateFile = Join-Path `
    $Root `
    "COURSE_STATE.md"

$LogFolder = Join-Path `
    $Root `
    "_codex_logs"


Set-Location $Root


# ============================================================
# FUNCTIONS
# ============================================================

function Get-StateContent {

    if (-not (Test-Path $StateFile)) {
        return $null
    }

    return Get-Content `
        $StateFile `
        -Raw `
        -Encoding UTF8
}


function Get-StateValue {

    param(
        [string]$Content,
        [string]$Key
    )

    if ([string]::IsNullOrWhiteSpace($Content)) {
        return $null
    }

    $EscapedKey = [regex]::Escape($Key)

    $Pattern =
        "(?im)^\s*" +
        $EscapedKey +
        "\s*:\s*(.+?)\s*$"

    $Match =
        [regex]::Match(
            $Content,
            $Pattern
        )

    if ($Match.Success) {
        return $Match.Groups[1].Value.Trim()
    }

    return $null
}


function Convert-ToNumber {

    param($Value)

    if ($null -eq $Value) {
        return $null
    }

    $Match =
        [regex]::Match(
            "$Value",
            "\d+"
        )

    if ($Match.Success) {
        return [int]$Match.Value
    }

    return $null
}


function Get-CourseState {

    $Content = Get-StateContent

    if ($null -eq $Content) {
        return $null
    }

    $CurrentLessonText =
        Get-StateValue `
            $Content `
            "Current Lesson"

    $LastCompletedText =
        Get-StateValue `
            $Content `
            "Last Completed"

    $NextLessonText =
        Get-StateValue `
            $Content `
            "Next Lesson"

    $NextCheckpointText =
        Get-StateValue `
            $Content `
            "Next Checkpoint"


    return [PSCustomObject]@{

        CurrentLesson =
            Convert-ToNumber $CurrentLessonText

        LastCompleted =
            Convert-ToNumber $LastCompletedText

        NextLesson =
            Convert-ToNumber $NextLessonText

        NextCheckpoint =
            Convert-ToNumber $NextCheckpointText

        NextLessonRaw =
            $NextLessonText

        Raw =
            $Content
    }
}


function Show-State {

    param($State)

    if ($null -eq $State) {

        Write-Host "Không đọc được COURSE_STATE.md"

        return
    }

    Write-Host "Current Lesson  : $($State.CurrentLesson)"
    Write-Host "Last Completed  : $($State.LastCompleted)"
    Write-Host "Next Lesson     : $($State.NextLessonRaw)"
    Write-Host "Next Checkpoint : $($State.NextCheckpoint)"
}


function Test-CourseComplete {

    param($State)

    if ($null -eq $State) {
        return $false
    }

    if (
        $State.NextLessonRaw -match "(?i)COMPLETE" -or
        $State.NextLessonRaw -match "(?i)FINISHED" -or
        $State.NextLessonRaw -match "(?i)DONE" -or
        $State.NextLessonRaw -match "(?i)HOÀN THÀNH" -or
        $State.NextLessonRaw -match "(?i)KẾT THÚC"
    ) {
        return $true
    }

    return $false
}


function Test-StateProgress {

    param(
        $Before,
        $After
    )

    if (
        $null -eq $Before -or
        $null -eq $After
    ) {
        return $false
    }

    if (
        $Before.LastCompleted -ne
        $After.LastCompleted
    ) {
        return $true
    }

    if (
        $Before.NextLessonRaw -ne
        $After.NextLessonRaw
    ) {
        return $true
    }

    return $false
}


# ============================================================
# STARTUP CHECK
# ============================================================

Clear-Host

Write-Host ""
Write-Host "======================================================"
Write-Host " AI ENGINEERING - AUTO COURSE"
Write-Host "======================================================"
Write-Host ""

Write-Host "Course:"
Write-Host $Root
Write-Host ""


if (-not (Test-Path $StateFile)) {

    Write-Host "ERROR"
    Write-Host ""

    Write-Host "Không tìm thấy COURSE_STATE.md:"
    Write-Host $StateFile

    exit 1
}


if (-not (Test-Path $LogFolder)) {

    New-Item `
        -ItemType Directory `
        -Path $LogFolder `
        | Out-Null
}


$InitialState =
    Get-CourseState


Write-Host "CURRENT STATE"
Write-Host ""

Show-State $InitialState


if (Test-CourseComplete $InitialState) {

    Write-Host ""
    Write-Host "Khóa học đã hoàn thành."

    exit 0
}


if (
    $null -eq $InitialState.LastCompleted -or
    $null -eq $InitialState.NextCheckpoint
) {

    Write-Host ""
    Write-Host "ERROR:"
    Write-Host "Không đọc được Last Completed hoặc Next Checkpoint."
    Write-Host ""
    Write-Host "Kiểm tra COURSE_STATE.md."

    exit 1
}


# ============================================================
# CALCULATE RUNS
# ============================================================

$TargetCheckpoint =
    $InitialState.NextCheckpoint


$RunsNeeded =
    $TargetCheckpoint -
    $InitialState.LastCompleted


if ($RunsNeeded -le 0) {

    Write-Host ""
    Write-Host "State cho thấy checkpoint hiện tại đã đạt hoặc bị sai."
    Write-Host ""

    Write-Host "Last Completed:"
    Write-Host $InitialState.LastCompleted

    Write-Host ""

    Write-Host "Next Checkpoint:"
    Write-Host $TargetCheckpoint

    Write-Host ""
    Write-Host "STOP."

    exit 1
}


Write-Host ""
Write-Host "Target Checkpoint : $TargetCheckpoint"
Write-Host "Lessons to create : $RunsNeeded"
Write-Host ""

Write-Host "Automation sẽ tạo:"
Write-Host ""

for (
    $Lesson =
        $InitialState.LastCompleted + 1;

    $Lesson -le
        $TargetCheckpoint;

    $Lesson++
) {

    Write-Host "Bài $Lesson"
}

Write-Host ""
Write-Host "Sau Bài ${TargetCheckpoint}:"
Write-Host "CHECKPOINT → STOP"

Write-Host ""
Write-Host "======================================================"
Write-Host ""


# ============================================================
# MAIN LOOP
# ============================================================

for (
    $Run = 1;
    $Run -le $RunsNeeded;
    $Run++
) {

    Write-Host ""
    Write-Host "======================================================"
    Write-Host " CODEX RUN $Run / $RunsNeeded"
    Write-Host "======================================================"
    Write-Host ""


    # --------------------------------------------------------
    # BEFORE
    # --------------------------------------------------------

    $Before =
        Get-CourseState


    Write-Host "BEFORE"
    Write-Host ""

    Show-State $Before


    if (Test-CourseComplete $Before) {

        Write-Host ""
        Write-Host "Course COMPLETE."

        break
    }


    # Không được vượt checkpoint ban đầu

    if (
        $Before.LastCompleted -ge
        $TargetCheckpoint
    ) {

        Write-Host ""
        Write-Host "Checkpoint $TargetCheckpoint đã đạt."
        Write-Host "STOP."

        break
    }


    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    $Timestamp =
        Get-Date `
            -Format "yyyy-MM-dd_HH-mm-ss"


    $LessonNumber =
        $Before.NextLesson


    $LogFile =
        Join-Path `
            $LogFolder `
            (
                "lesson_{0:D3}_{1}.txt" `
                -f `
                $LessonNumber,
                $Timestamp
            )


    Write-Host ""
    Write-Host "----------------------------------------------"
    Write-Host "PROMPT:"
    Write-Host ""
    Write-Host $Prompt
    Write-Host "----------------------------------------------"
    Write-Host ""


    # --------------------------------------------------------
    # CODEX EXEC - REALTIME
    # --------------------------------------------------------

    codex exec `
        --skip-git-repo-check `
        --sandbox workspace-write `
        $Prompt `
        2>&1 |
        Tee-Object `
            -FilePath $LogFile


    $ExitCode =
        $LASTEXITCODE


    Write-Host ""
    Write-Host "Codex Exit Code: $ExitCode"


    # --------------------------------------------------------
    # CODEX ERROR
    # --------------------------------------------------------

    if ($ExitCode -ne 0) {

        Write-Host ""
        Write-Host "======================================================"
        Write-Host " CODEX ERROR"
        Write-Host "======================================================"

        Write-Host ""
        Write-Host "Automation STOP."
        Write-Host ""

        Write-Host "Log:"
        Write-Host $LogFile

        break
    }


    Start-Sleep `
        -Seconds 1


    # --------------------------------------------------------
    # AFTER
    # --------------------------------------------------------

    $After =
        Get-CourseState


    Write-Host ""
    Write-Host "AFTER"
    Write-Host ""

    Show-State $After


    # --------------------------------------------------------
    # PROGRESS CHECK
    # --------------------------------------------------------

    $Progress =
        Test-StateProgress `
            $Before `
            $After


    if (-not $Progress) {

        Write-Host ""
        Write-Host "======================================================"
        Write-Host " NO PROGRESS DETECTED"
        Write-Host "======================================================"

        Write-Host ""
        Write-Host "COURSE_STATE.md không thay đổi."
        Write-Host ""
        Write-Host "Automation STOP để tránh tốn usage."
        Write-Host ""

        Write-Host "Log:"
        Write-Host $LogFile

        break
    }


    # --------------------------------------------------------
    # COURSE COMPLETE
    # --------------------------------------------------------

    if (Test-CourseComplete $After) {

        Write-Host ""
        Write-Host "======================================================"
        Write-Host " COURSE COMPLETE"
        Write-Host "======================================================"

        break
    }


    # --------------------------------------------------------
    # CHECKPOINT REACHED
    # --------------------------------------------------------

    if (
        $After.LastCompleted -ge
        $TargetCheckpoint
    ) {

        Write-Host ""
        Write-Host "======================================================"
        Write-Host " CHECKPOINT $TargetCheckpoint REACHED"
        Write-Host "======================================================"

        Write-Host ""
        Write-Host "Đã hoàn thành Bài $TargetCheckpoint."
        Write-Host "Checkpoint phải đã được Codex thực hiện."
        Write-Host ""
        Write-Host "Automation STOP."

        break
    }


    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    Write-Host ""
    Write-Host "RUN SUCCESS"
    Write-Host ""

    Write-Host "Completed:"
    Write-Host $After.LastCompleted

    Write-Host ""

    Write-Host "Next:"
    Write-Host $After.NextLessonRaw

    Write-Host ""

    Write-Host "Log:"
    Write-Host $LogFile


    # --------------------------------------------------------
    # DELAY
    # --------------------------------------------------------

    Write-Host ""
    Write-Host "Next lesson in $DelaySeconds seconds..."

    Start-Sleep `
        -Seconds $DelaySeconds
}


# ============================================================
# END
# ============================================================

Write-Host ""
Write-Host "======================================================"
Write-Host " AUTOMATION FINISHED"
Write-Host "======================================================"
Write-Host ""

$FinalState =
    Get-CourseState

Show-State $FinalState

Write-Host ""
Write-Host "Logs:"
Write-Host $LogFolder
Write-Host ""