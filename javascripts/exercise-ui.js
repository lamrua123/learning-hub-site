(() => {
  "use strict";

  /*
   * Learning Hub V4.7B
   * Practice Dashboard + Exercise Workspace
   */

  const VERSION = "4.7B";

  const UI_ID = "lh-practice-dashboard-v47";
  const ACTIVE_KEY = "learningHubActiveExerciseV45";
  const LAST_KEY = "learningHubLastExerciseV47";

  let activeExerciseId = null;
  let sourceUrl = null;
  let saveTimer = null;

  function qs(selector, root = document) {
    return root.querySelector(selector);
  }

  function escapeHTML(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function readStorage(storage, key, fallback = null) {
    try {
      const raw = storage.getItem(key);
      if (!raw) return fallback;
      return JSON.parse(raw);
    } catch (_) {
      return fallback;
    }
  }

  function writeStorage(storage, key, value) {
    try {
      storage.setItem(key, JSON.stringify(value));
      return true;
    } catch (_) {
      return false;
    }
  }

  function engineReady() {
    return Boolean(
      window.LearningHubExercises &&
      typeof window.LearningHubExercises.getAll === "function"
    );
  }

  function ideReady() {
    return Boolean(
      window.LearningHubIDE &&
      typeof window.LearningHubIDE.open === "function"
    );
  }

  function isHomePage() {
    return Boolean(qs(".lh-home"));
  }

  function difficultyText(level) {
    const value = Math.max(
      1,
      Math.min(3, Number(level || 1))
    );

    return "★".repeat(value) + "☆".repeat(3 - value);
  }

  function chapterName(value) {
    const names = {
      foundations: "Foundations",
      conditions: "Conditions",
      loops: "Loops",
      functions: "Functions",
      collections: "Collections"
    };

    return names[value] || value || "Python";
  }

  /* =========================================================
     STYLE
     ========================================================= */

  function installStyle() {
    if (qs("#lh-exercise-ui-style")) return;

    const style = document.createElement("style");
    style.id = "lh-exercise-ui-style";

    style.textContent = `
      #${UI_ID} {
        margin: 42px 0;
      }

      #${UI_ID} .lh-practice-shell {
        padding: 22px;
        border: 1px solid var(--md-default-fg-color--lightest);
        border-radius: 16px;
        background: var(--md-default-bg-color);
        box-shadow: 0 8px 28px rgba(0,0,0,.055);
      }

      #${UI_ID} .lh-practice-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 24px;
      }

      #${UI_ID} .lh-practice-kicker {
        margin-bottom: 5px;
        color: #754ffe;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .1em;
      }

      #${UI_ID} h2 {
        margin: 0 0 7px;
        font-size: 24px;
      }

      #${UI_ID} .lh-practice-description {
        margin: 0;
        max-width: 620px;
        font-size: 13px;
        line-height: 1.65;
        opacity: .72;
      }

      #${UI_ID} .lh-practice-percent {
        flex: 0 0 auto;
        font-size: 30px;
        line-height: 1;
        font-weight: 800;
      }

      #${UI_ID} .lh-practice-progress-row {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        margin-top: 20px;
        font-size: 11px;
        font-weight: 700;
        opacity: .72;
      }

      #${UI_ID} .lh-practice-track {
        height: 7px;
        margin-top: 8px;
        overflow: hidden;
        border-radius: 999px;
        background: var(--md-default-fg-color--lightest);
      }

      #${UI_ID} .lh-practice-fill {
        height: 100%;
        border-radius: inherit;
        background: #754ffe;
        transition: width .3s ease;
      }

      #${UI_ID} .lh-practice-next {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 20px;
        align-items: center;
        margin-top: 20px;
        padding: 16px;
        border-radius: 11px;
        background: rgba(117,79,254,.055);
      }

      #${UI_ID} .lh-practice-next-label {
        margin-bottom: 4px;
        color: #754ffe;
        font-size: 9px;
        font-weight: 800;
        letter-spacing: .09em;
      }

      #${UI_ID} .lh-practice-next h3 {
        margin: 0 0 5px;
        font-size: 16px;
      }

      #${UI_ID} .lh-practice-meta {
        font-size: 11px;
        opacity: .66;
      }

      #${UI_ID} .lh-practice-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }

      #${UI_ID} button,
      .lh-ex-workspace button {
        font: inherit;
      }

      #${UI_ID} .lh-practice-button,
      .lh-ex-action {
        padding: 8px 11px;
        border: 1px solid var(--md-default-fg-color--lightest);
        border-radius: 7px;
        background: var(--md-default-bg-color);
        color: inherit;
        font-size: 11px;
        font-weight: 800;
        cursor: pointer;
      }

      #${UI_ID} .lh-practice-button.is-primary,
      .lh-ex-action.is-primary {
        border-color: #754ffe;
        background: #754ffe;
        color: #fff;
      }

      #${UI_ID} .lh-practice-complete {
        margin-top: 18px;
        padding: 15px;
        border-radius: 10px;
        background: rgba(40,180,110,.075);
        font-size: 12px;
        line-height: 1.6;
      }

      .lh-ex-workspace {
        margin: 0 0 12px;
        padding: 15px;
        border: 1px solid rgba(117,79,254,.24);
        border-radius: 10px;
        background: rgba(117,79,254,.055);
      }

      .lh-ex-workspace-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 18px;
      }

      .lh-ex-workspace-kicker {
        margin-bottom: 4px;
        color: #754ffe;
        font-size: 9px;
        font-weight: 800;
        letter-spacing: .09em;
      }

      .lh-ex-workspace h3 {
        margin: 0;
        font-size: 16px;
      }

      .lh-ex-workspace p {
        margin: 7px 0 0;
        font-size: 12px;
        line-height: 1.6;
        opacity: .76;
      }

      .lh-ex-workspace-meta {
        margin-top: 7px;
        font-size: 10px;
        opacity: .62;
      }

      .lh-ex-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        margin-top: 12px;
      }

      .lh-ex-result {
        display: none;
        margin-top: 10px;
        padding: 9px 10px;
        white-space: pre-wrap;
        border-radius: 7px;
        font-size: 12px;
        line-height: 1.55;
      }

      .lh-ex-result.is-visible {
        display: block;
      }

      .lh-ex-result.is-success {
        background: rgba(40,180,110,.11);
      }

      .lh-ex-result.is-error {
        background: rgba(220,70,70,.10);
      }

      .lh-ex-result.is-info {
        background: rgba(117,79,254,.08);
      }

      .lh-ex-save {
        margin-top: 8px;
        font-size: 10px;
        opacity: .6;
      }

      @media (max-width: 760px) {
        #${UI_ID} .lh-practice-head,
        #${UI_ID} .lh-practice-next,
        .lh-ex-workspace-head {
          display: flex;
          flex-direction: column;
          align-items: stretch;
        }

        #${UI_ID} .lh-practice-percent {
          font-size: 24px;
        }
      }
    `;

    document.head.appendChild(style);
  }

  /* =========================================================
     EXERCISE SELECTION
     ========================================================= */

  function getLastExerciseId() {
    const data = readStorage(
      localStorage,
      LAST_KEY,
      null
    );

    return data?.id || null;
  }

  function rememberExercise(id) {
    writeStorage(
      localStorage,
      LAST_KEY,
      {
        id,
        updatedAt: Date.now()
      }
    );
  }

  function getContinueExercise() {
    const exercises =
      window.LearningHubExercises.getAll();

    if (!exercises.length) return null;

    /*
     * Ưu tiên bài đang làm dở gần nhất.
     */

    const lastId = getLastExerciseId();

    if (lastId) {
      const last =
        window.LearningHubExercises.get(lastId);

      if (
        last &&
        !window.LearningHubExercises.isCompleted(lastId)
      ) {
        return last;
      }
    }

    /*
     * Nếu bài gần nhất đã hoàn thành:
     * lấy bài chưa hoàn thành đầu tiên.
     */

    const unfinished =
      exercises.find(
        exercise =>
          !window.LearningHubExercises.isCompleted(
            exercise.id
          )
      );

    if (unfinished) return unfinished;

    /*
     * Tất cả đã hoàn thành:
     * cho luyện lại bài gần nhất.
     */

    if (lastId) {
      const last =
        window.LearningHubExercises.get(lastId);

      if (last) return last;
    }

    return exercises[0];
  }

  /* =========================================================
     DASHBOARD
     ========================================================= */

  function renderDashboard() {
    if (
      !isHomePage() ||
      !engineReady()
    ) {
      return;
    }

    qs(`#${UI_ID}`)?.remove();

    const progress =
      window.LearningHubExercises.getProgress();

    const next =
      getContinueExercise();

    const section =
      document.createElement("section");

    section.id = UI_ID;

    const allDone =
      progress.total > 0 &&
      progress.completed === progress.total;

    section.innerHTML = `
      <div class="lh-practice-shell">

        <div class="lh-practice-head">
          <div>
            <div class="lh-practice-kicker">
              PYTHON PRACTICE
            </div>

            <h2>Luyện tập Python</h2>

            <p class="lh-practice-description">
              Viết code, chạy trực tiếp trong trình duyệt
              và nhận phản hồi ngay. Tiến độ được lưu trên
              thiết bị này.
            </p>
          </div>

          <div class="lh-practice-percent">
            ${progress.percent}%
          </div>
        </div>

        <div class="lh-practice-progress-row">
          <span>
            ${progress.completed} / ${progress.total}
            bài hoàn thành
          </span>

          <span>
            ${progress.total - progress.completed}
            bài còn lại
          </span>
        </div>

        <div class="lh-practice-track">
          <div
            class="lh-practice-fill"
            style="width:${progress.percent}%"
          ></div>
        </div>

        ${
          allDone
            ? `
              <div class="lh-practice-complete">
                <strong>🎉 Hoàn thành toàn bộ pack hiện tại.</strong><br>
                Bạn vẫn có thể luyện lại các bài đã làm.
              </div>
            `
            : ""
        }

        ${
          next
            ? `
              <div class="lh-practice-next">
                <div>
                  <div class="lh-practice-next-label">
                    ${
                      allDone
                        ? "LUYỆN LẠI"
                        : "TIẾP TỤC"
                    }
                  </div>

                  <h3>
                    🧩 ${escapeHTML(next.title)}
                  </h3>

                  <div class="lh-practice-meta">
                    ${escapeHTML(chapterName(next.chapter))}
                    · Độ khó ${difficultyText(next.difficulty)}
                  </div>
                </div>

                <div class="lh-practice-actions">
                  <button
                    type="button"
                    class="lh-practice-button is-primary"
                    data-practice-continue="${escapeHTML(next.id)}"
                  >
                    ▶ ${
                      allDone
                        ? "Luyện lại"
                        : "Tiếp tục thực hành"
                    }
                  </button>
                </div>
              </div>
            `
            : ""
        }

      </div>
    `;

    const lab = qs("#code-lab");

    if (lab) {
      lab.before(section);
    } else {
      qs(".lh-home")?.appendChild(section);
    }

    qs(
      "[data-practice-continue]",
      section
    )?.addEventListener(
      "click",
      event => {
        openExercise(
          event.currentTarget.dataset.practiceContinue
        );
      }
    );
  }

  /* =========================================================
     WORKSPACE
     ========================================================= */

  function removeWorkspace() {
    qs("#lh-exercise-workspace")?.remove();
  }

  function createWorkspace(exercise) {
    removeWorkspace();

    const lab = qs("#code-lab");
    if (!lab) return null;

    const state =
      window.LearningHubExercises.getState(
        exercise.id
      );

    const completed =
      window.LearningHubExercises.isCompleted(
        exercise.id
      );

    const box =
      document.createElement("div");

    box.id = "lh-exercise-workspace";
    box.className = "lh-ex-workspace";

    box.innerHTML = `
      <div class="lh-ex-workspace-head">
        <div>
          <div class="lh-ex-workspace-kicker">
            🧩 BÀI TẬP ĐANG LÀM
          </div>

          <h3>
            ${escapeHTML(exercise.title)}
          </h3>

          <p>
            ${escapeHTML(exercise.description)}
          </p>

          <div class="lh-ex-workspace-meta">
            ${escapeHTML(chapterName(exercise.chapter))}
            · Độ khó ${difficultyText(exercise.difficulty)}
            · Lần thử ${state?.attempts || 0}
            ${
              completed
                ? " · ✅ Đã hoàn thành"
                : ""
            }
          </div>
        </div>

        ${
          sourceUrl
            ? `
              <a
                class="lh-ex-action"
                href="${escapeHTML(sourceUrl)}"
              >
                ← Quay lại bài học
              </a>
            `
            : ""
        }
      </div>

      <div class="lh-ex-actions">
        <button
          type="button"
          class="lh-ex-action is-primary"
          data-ex-check
        >
          ▶ Chạy & kiểm tra
        </button>

        <button
          type="button"
          class="lh-ex-action"
          data-ex-hint
        >
          💡 Gợi ý
        </button>

        <button
          type="button"
          class="lh-ex-action"
          data-ex-reset
        >
          ↺ Làm lại
        </button>

        <button
          type="button"
          class="lh-ex-action"
          data-ex-close
        >
          ✕ Đóng
        </button>
      </div>

      <div
        class="lh-ex-result"
        data-ex-result
      ></div>

      <div
        class="lh-ex-save"
        data-ex-save
      >
        Code được tự động lưu
      </div>
    `;

    const shell =
      qs(".lh-ide-shell", lab);

    if (shell) {
      shell.before(box);
    } else {
      lab.prepend(box);
    }

    qs("[data-ex-check]", box)
      ?.addEventListener(
        "click",
        checkExercise
      );

    qs("[data-ex-hint]", box)
      ?.addEventListener(
        "click",
        showHint
      );

    qs("[data-ex-reset]", box)
      ?.addEventListener(
        "click",
        resetActiveExercise
      );

    qs("[data-ex-close]", box)
      ?.addEventListener(
        "click",
        closeExercise
      );

    return box;
  }

  /* =========================================================
     OPEN
     ========================================================= */

  function openExercise(
    id,
    options = {}
  ) {
    if (!engineReady()) return;

    const exercise =
      window.LearningHubExercises.get(id);

    if (!exercise) {
      console.error(
        "[Learning Hub] Exercise không tồn tại:",
        id
      );
      return;
    }

    activeExerciseId = id;

    sourceUrl =
      options.sourceUrl ||
      null;

    rememberExercise(id);

    writeStorage(
      sessionStorage,
      ACTIVE_KEY,
      {
        id,
        sourceUrl
      }
    );

    const openWhenReady =
      (attempt = 0) => {
        if (ideReady()) {
          const code =
            window.LearningHubExercises.getCode(id);

          window.LearningHubIDE.open({
            language: "python",
            code
          });

          createWorkspace(exercise);
          startAutosave();

          qs("#code-lab")?.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });

          return;
        }

        if (attempt >= 100) {
          console.error(
            "[Learning Hub] IDE chưa sẵn sàng."
          );
          return;
        }

        setTimeout(
          () =>
            openWhenReady(attempt + 1),
          100
        );
      };

    openWhenReady();
  }

  /* =========================================================
     AUTOSAVE
     ========================================================= */

  function startAutosave() {
    clearInterval(saveTimer);

    let previous =
      ideReady()
        ? window.LearningHubIDE.getCode?.() || ""
        : "";

    saveTimer = setInterval(
      () => {
        if (
          !activeExerciseId ||
          !ideReady() ||
          typeof window.LearningHubIDE.getCode !== "function"
        ) {
          return;
        }

        const code =
          window.LearningHubIDE.getCode();

        if (code === previous) {
          return;
        }

        const label =
          qs("[data-ex-save]");

        if (label) {
          label.textContent =
            "Đang lưu code...";
        }

        window.LearningHubExercises.saveCode(
          activeExerciseId,
          code
        );

        previous = code;

        if (label) {
          label.textContent =
            "✓ Code đã được lưu";
        }
      },
      650
    );
  }

  function saveCurrentCode() {
    if (
      !activeExerciseId ||
      !ideReady() ||
      typeof window.LearningHubIDE.getCode !== "function"
    ) {
      return;
    }

    window.LearningHubExercises.saveCode(
      activeExerciseId,
      window.LearningHubIDE.getCode()
    );
  }

  /* =========================================================
     OUTPUT
     ========================================================= */

  function getIDEOutput() {
    return (
      qs("#lh-code-output")
        ?.textContent || ""
    );
  }

  async function checkExercise() {
    if (
      !activeExerciseId ||
      !ideReady()
    ) {
      return;
    }

    saveCurrentCode();

    setResult(
      "Đang chạy Python và kiểm tra...",
      "info"
    );

    try {
      const result =
        window.LearningHubIDE.run();

      if (
        result &&
        typeof result.then === "function"
      ) {
        await result;
      }

      await new Promise(
        resolve =>
          setTimeout(resolve, 100)
      );

      const output =
        getIDEOutput();

      const evaluation =
        window.LearningHubExercises.evaluate(
          activeExerciseId,
          {
            output,
            error: null
          }
        );

      if (evaluation.passed) {
        setResult(
          "✅ " + evaluation.message,
          "success"
        );
      } else {
        const failed =
          evaluation.tests?.find(
            test => !test.passed
          );

        let message =
          "❌ " + evaluation.message;

        if (failed) {
          message +=
            "\n\nMong đợi: " +
            failed.expected +
            "\nNhận được: " +
            failed.actual;
        }

        setResult(
          message,
          "error"
        );
      }

      /*
       * Refresh dashboard progress,
       * nhưng không đụng IDE.
       */

      renderDashboard();

      const exercise =
        window.LearningHubExercises.get(
          activeExerciseId
        );

      if (exercise) {
        refreshWorkspaceMeta(exercise);
      }
    } catch (error) {
      setResult(
        "❌ Code đang có lỗi:\n" +
          String(
            error?.message || error
          ),
        "error"
      );
    }
  }

  function refreshWorkspaceMeta(exercise) {
    const oldResult =
      qs("[data-ex-result]")
        ?.textContent;

    const oldClass =
      qs("[data-ex-result]")
        ?.className;

    createWorkspace(exercise);

    if (oldResult) {
      const result =
        qs("[data-ex-result]");

      if (result) {
        result.textContent =
          oldResult;

        result.className =
          oldClass;
      }
    }
  }

  /* =========================================================
     HINT
     ========================================================= */

  function showHint() {
    if (!activeExerciseId) return;

    const hint =
      window.LearningHubExercises.getNextHint(
        activeExerciseId
      );

    if (!hint) {
      setResult(
        "Bài tập này chưa có gợi ý.",
        "info"
      );
      return;
    }

    setResult(
      `💡 Gợi ý ${hint.number}/${hint.total}\n\n${hint.hint}`,
      "info"
    );
  }

  /* =========================================================
     RESET
     ========================================================= */

  function resetActiveExercise() {
    if (!activeExerciseId) return;

    const exercise =
      window.LearningHubExercises.get(
        activeExerciseId
      );

    if (!exercise) return;

    const confirmed =
      window.confirm(
        "Làm lại bài tập từ đầu?\n\nCode hiện tại của bài này sẽ được đặt lại."
      );

    if (!confirmed) return;

    window.LearningHubExercises.reset(
      activeExerciseId
    );

    window.LearningHubIDE.open({
      language: "python",
      code: exercise.starterCode
    });

    createWorkspace(exercise);
    startAutosave();

    setResult(
      "↺ Code đã được đặt lại. Thành tích hoàn thành trước đây vẫn được giữ.",
      "info"
    );

    renderDashboard();
  }

  /* =========================================================
     CLOSE
     ========================================================= */

  function closeExercise() {
    saveCurrentCode();

    clearInterval(saveTimer);

    activeExerciseId = null;
    sourceUrl = null;

    try {
      sessionStorage.removeItem(
        ACTIVE_KEY
      );
    } catch (_) {
      // Ignore.
    }

    removeWorkspace();
    renderDashboard();
  }

  /* =========================================================
     RESULT
     ========================================================= */

  function setResult(
    message,
    type
  ) {
    const element =
      qs("[data-ex-result]");

    if (!element) return;

    element.className =
      `lh-ex-result is-visible is-${type}`;

    element.textContent =
      message;
  }

  /* =========================================================
     RESTORE SESSION
     ========================================================= */

  function restoreActiveExercise() {
    const saved =
      readStorage(
        sessionStorage,
        ACTIVE_KEY,
        null
      );

    /*
     * Tương thích V4.5B:
     * trước đây ACTIVE_KEY có thể chỉ chứa string.
     */

    const id =
      typeof saved === "string"
        ? saved
        : saved?.id;

    if (!id) return;

    const savedSource =
      typeof saved === "object"
        ? saved?.sourceUrl || null
        : null;

    const restore =
      (attempt = 0) => {
        if (
          engineReady() &&
          ideReady()
        ) {
          const exercise =
            window.LearningHubExercises.get(id);

          if (!exercise) {
            return;
          }

          activeExerciseId = id;
          sourceUrl = savedSource;

          rememberExercise(id);

          window.LearningHubIDE.open({
            language: "python",
            code:
              window.LearningHubExercises.getCode(
                id
              )
          });

          createWorkspace(exercise);
          startAutosave();

          return;
        }

        if (attempt >= 100) return;

        setTimeout(
          () =>
            restore(attempt + 1),
          100
        );
      };

    restore();
  }

  /* =========================================================
     PUBLIC API
     ========================================================= */

  window.LearningHubExerciseUI = {
    version: VERSION,

    open(
      id,
      options = {}
    ) {
      openExercise(
        id,
        options
      );
    },

    close() {
      closeExercise();
    },

    getActiveExerciseId() {
      return activeExerciseId;
    },

    refresh() {
      renderDashboard();
    }
  };

  /* =========================================================
     INIT
     ========================================================= */

  function init() {
    if (!isHomePage()) {
      return;
    }

    installStyle();

    const wait =
      (attempt = 0) => {
        if (engineReady()) {
          renderDashboard();
          restoreActiveExercise();
          return;
        }

        if (attempt >= 100) {
          console.error(
            "[Learning Hub] Exercise Engine chưa sẵn sàng."
          );
          return;
        }

        setTimeout(
          () => wait(attempt + 1),
          100
        );
      };

    wait();
  }

  /*
   * Lưu code khi rời trang.
   */

  window.addEventListener(
    "pagehide",
    saveCurrentCode
  );

  if (
    typeof document$ !== "undefined" &&
    document$?.subscribe
  ) {
    document$.subscribe(init);
  } else if (
    document.readyState === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      init
    );
  } else {
    init();
  }
})();