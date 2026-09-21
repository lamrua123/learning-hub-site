(() => {
  "use strict";

  /* =========================================================
     LEARNING HUB V4.3
     ========================================================= */

  const STORAGE_PROGRESS = "learningHubProgressV41";
  const STORAGE_LAST = "learningHubLastLessonV41";
  const STORAGE_CODE_PREFIX = "learningHubCodeV43:";

  const PYODIDE_VERSION = "0.27.7";
  const PYODIDE_BASE =
    `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

  const MONACO_VERSION = "0.52.2";
  const MONACO_BASE =
    `https://cdn.jsdelivr.net/npm/monaco-editor@${MONACO_VERSION}/min/vs`;

  /* =========================================================
     COURSES
     ========================================================= */

  const COURSES =
  Array.isArray(
    window.LEARNING_HUB_COURSES
  )
    ? window.LEARNING_HUB_COURSES
    : [];

  /* =========================================================
     DEFAULT CODE
     ========================================================= */

  const CODE_EXAMPLES = {
    python: `name = "Learning Hub"
coins = 0

for i in range(5):
    coins += 1
    print(f"Coins: {coins}")

print("Hello from", name)`,

    csharp: `using System;

public class Program
{
    public static void Main()
    {
        int coins = 0;

        for (int i = 0; i < 5; i++)
        {
            coins++;
            Console.WriteLine($"Coins: {coins}");
        }
    }
}`
  };

  /* =========================================================
     RUNTIME STATE
     ========================================================= */

  let pyodideInstance = null;
  let loadingPython = null;

  let monacoEditor = null;
  let monacoLoading = null;
  let monacoReady = false;

  let currentLanguage = "python";
  let saveTimer = null;

  /* =========================================================
     HELPERS
     ========================================================= */

  function qs(selector, root = document) {
    return root.querySelector(selector);
  }

  function qsa(selector, root = document) {
    return Array.from(
      root.querySelectorAll(selector)
    );
  }

  function cleanText(value) {
    return (value || "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function safeDecode(value) {
    try {
      return decodeURIComponent(value);
    } catch (_) {
      return value;
    }
  }

  function readJSON(key, fallback = {}) {
    try {
      const raw =
        localStorage.getItem(key);

      if (!raw) {
        return fallback;
      }

      return JSON.parse(raw);
    } catch (_) {
      return fallback;
    }
  }

  function writeJSON(key, value) {
    try {
      localStorage.setItem(
        key,
        JSON.stringify(value)
      );
    } catch (_) {
      // localStorage unavailable.
    }
  }

  function isHomePage() {
    return Boolean(
      qs(".lh-home")
    );
  }

  /* =========================================================
     SITE URL
     ========================================================= */

  function getSiteBaseUrl() {
    const logo =
      qs("a.md-header__button.md-logo");

    if (logo?.href) {
      let url = logo.href;

      if (!url.endsWith("/")) {
        url += "/";
      }

      return url;
    }

    const pathname =
      window.location.pathname;

    const marker =
      "/learning-hub-site/";

    const index =
      pathname.indexOf(marker);

    if (index >= 0) {
      return (
        window.location.origin +
        pathname.slice(
          0,
          index + marker.length
        )
      );
    }

    return (
      window.location.origin + "/"
    );
  }

  function makeCourseUrl(path) {
    try {
      return new URL(
        path,
        getSiteBaseUrl()
      ).href;
    } catch (_) {
      return (
        getSiteBaseUrl() +
        encodeURI(path)
      );
    }
  }

  /* =========================================================
     FIX MARKDOWN LINKS
     ========================================================= */

  function fixMarkdownLinks() {
    qsa("a[href]").forEach(link => {
      const href =
        link.getAttribute("href");

      if (!href) return;

      if (
        href.startsWith("http://") ||
        href.startsWith("https://") ||
        href.startsWith("mailto:") ||
        href.startsWith("tel:") ||
        href.startsWith("#") ||
        href.startsWith("javascript:")
      ) {
        return;
      }

      const hashIndex =
        href.indexOf("#");

      const path =
        hashIndex >= 0
          ? href.slice(0, hashIndex)
          : href;

      const hash =
        hashIndex >= 0
          ? href.slice(hashIndex)
          : "";

      if (
        path
          .toLowerCase()
          .endsWith(".md")
      ) {
        link.setAttribute(
          "href",
          path.slice(0, -3) +
            "/" +
            hash
        );
      }
    });
  }

  /* =========================================================
     CURRENT COURSE
     ========================================================= */

  function getCurrentCourse() {
    const pathname =
      safeDecode(
        window.location.pathname
      ).toLowerCase();

    return (
      COURSES.find(course =>
        pathname.includes(
          course.match.toLowerCase()
        )
      ) || null
    );
  }

  /* =========================================================
     LESSON NUMBER
     ========================================================= */

  function extractLessonNumber(title) {
    if (!title) {
      return null;
    }

    const patterns = [
      /\bBÀI\s*0*(\d+)/i,
      /\bBAI\s*0*(\d+)/i,
      /\bLESSON\s*0*(\d+)/i,
      /^\s*0*(\d{1,3})\s*[-—–]/i
    ];

    for (const pattern of patterns) {
      const match =
        title.match(pattern);

      if (!match) continue;

      const value =
        Number(match[1]);

      if (
        Number.isFinite(value) &&
        value > 0
      ) {
        return value;
      }
    }

    const pathname =
      safeDecode(
        window.location.pathname
      );

    const parts =
      pathname
        .split("/")
        .filter(Boolean);

    const last =
      parts[
        parts.length - 1
      ] || "";

    const match =
      last.match(
        /(?:BÀI|BAI|LESSON)[\s_-]*0*(\d+)/i
      ) ||
      last.match(
        /^0*(\d{1,3})[\s_-]/i
      );

    if (!match) {
      return null;
    }

    const value =
      Number(match[1]);

    return (
      Number.isFinite(value) &&
      value > 0
    )
      ? value
      : null;
  }

  /* =========================================================
     LESSON PAGE
     ========================================================= */

  function setupLessonPage() {
    const container =
      qs(".md-content__inner");

    if (!container) return;

    const heading =
      qs("h1", container);

    if (!heading) return;

    container.classList.add(
      "learning-lesson"
    );

    heading.classList.add(
      "learning-lesson-title"
    );

    setupBreadcrumb(
      container,
      heading
    );

    setupLessonMeta(
      container,
      heading
    );

    saveCurrentLesson(
      cleanText(
        heading.textContent
      )
    );
  }

  function setupBreadcrumb(
    container,
    heading
  ) {
    if (
      qs(
        ".learning-breadcrumb",
        container
      )
    ) {
      return;
    }

    const activeLinks =
      qsa(
        ".md-sidebar--primary .md-nav__link--active"
      );

    const headingText =
      cleanText(
        heading.textContent
      );

    const pieces =
      activeLinks
        .map(link =>
          cleanText(
            link.textContent
          )
        )
        .filter(Boolean)
        .filter(
          text =>
            text !== headingText
        );

    if (!pieces.length) {
      const course =
        getCurrentCourse();

      if (course) {
        pieces.push(
          course.title
        );
      }
    }

    if (!pieces.length) return;

    const breadcrumb =
      document.createElement(
        "div"
      );

    breadcrumb.className =
      "learning-breadcrumb";

    breadcrumb.textContent =
      pieces.join(" › ");

    heading.before(
      breadcrumb
    );
  }

  function setupLessonMeta(
    container,
    heading
  ) {
    if (
      qs(
        ".learning-meta",
        container
      )
    ) {
      return;
    }

    const meta =
      document.createElement(
        "div"
      );

    meta.className =
      "learning-meta";

    meta.innerHTML = `
      <span class="learning-meta-item">
        📖 Bài học
      </span>

      <span class="learning-meta-item">
        🎯 Theo lộ trình
      </span>

      <span class="learning-meta-item">
        ✓ Tự lưu tiến độ
      </span>
    `;

    heading.after(meta);
  }

  /* =========================================================
     SAVE LESSON
     ========================================================= */

  function saveCurrentLesson(title) {
    const course =
      getCurrentCourse();

    if (!course) return;

    const lessonNumber =
      extractLessonNumber(title);

    const progress =
      readJSON(
        STORAGE_PROGRESS,
        {}
      );

    const previous =
      progress[course.key] || {
        maxLesson: 0,
        total: course.total
      };

    if (
      lessonNumber !== null
    ) {
      previous.maxLesson =
        Math.max(
          Number(
            previous.maxLesson ||
              0
          ),
          lessonNumber
        );
    }

    previous.total =
      course.total;

    previous.lastTitle =
      title;

    previous.lastUrl =
      window.location.href;

    previous.updatedAt =
      Date.now();

    progress[course.key] =
      previous;

    writeJSON(
      STORAGE_PROGRESS,
      progress
    );

    writeJSON(
      STORAGE_LAST,
      {
        course:
          course.title,

        courseKey:
          course.key,

        title,

        url:
          window.location.href,

        updatedAt:
          Date.now()
      }
    );
  }

  /* =========================================================
     COURSE PROGRESS
     ========================================================= */

  function renderCourseProgress() {
    const progress =
      readJSON(
        STORAGE_PROGRESS,
        {}
      );

    qsa(
      ".lh-course-card[data-course]"
    ).forEach(card => {
      const key =
        card.dataset.course;

      const item =
        progress[key];

      const total =
        Number(
          card.dataset.total ||
            item?.total ||
            0
        );

      let done =
        Number(
          item?.maxLesson ||
            0
        );

      if (
        total > 0 &&
        done > total
      ) {
        done = total;
      }

      const percent =
        total > 0
          ? Math.round(
              (done / total) *
                100
            )
          : 0;

      const bar =
        qs(
          ".lh-progress-bar",
          card
        );

      const count =
        qs(
          "[data-progress-count]",
          card
        );

      const percentage =
        qs(
          "[data-progress-percent]",
          card
        );

      const action =
        qs(
          "[data-course-action]",
          card
        );

      if (bar) {
        bar.style.width =
          `${percent}%`;
      }

      if (
        count &&
        done > 0
      ) {
        count.textContent =
          `${done} / ${total} bài`;
      }

      if (percentage) {
        percentage.textContent =
          `${percent}%`;
      }

      if (item?.lastUrl) {
        card.href =
          item.lastUrl;

        if (action) {
          action.textContent =
            "Tiếp tục học →";
        }
      } else if (action) {
        action.textContent =
          "Bắt đầu →";
      }
    });
  }

  /* =========================================================
     CONTINUE LEARNING
     ========================================================= */

  function setupContinueLearning() {
    const box =
      qs("#lh-continue");

    if (!box) return;

    const last =
      readJSON(
        STORAGE_LAST,
        null
      );

    if (
      !last ||
      !last.title ||
      !last.url
    ) {
      box.classList.remove(
        "is-visible"
      );

      return;
    }

    const title =
      qs(
        "[data-last-title]",
        box
      );

    const course =
      qs(
        "[data-last-course]",
        box
      );

    const link =
      qs(
        "[data-last-link]",
        box
      );

    if (title) {
      title.textContent =
        last.title;
    }

    if (course) {
      course.textContent =
        last.course || "";
    }

    if (link) {
      link.href =
        last.url;
    }

    box.classList.add(
      "is-visible"
    );
  }

  function escapeHTML(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


function renderHomeCourses() {
  const grid =
    qs("#lh-course-grid");

  if (!grid) return;

  const totalLabel =
    qs("#lh-course-total");

  if (totalLabel) {
    totalLabel.textContent =
      `${COURSES.length} khóa học`;
  }

  const heroStats =
    qsa(
      ".lh-preview-stats strong"
    );

  if (heroStats[0]) {
    heroStats[0].textContent =
      String(COURSES.length);
  }

  const coverClasses = [
    "lh-cover-purple",
    "lh-cover-orange",
    "lh-cover-red",
    "lh-cover-blue",
    "lh-cover-cyan",
    "lh-cover-indigo",
    "lh-cover-green",
    "lh-cover-yellow",
    "lh-cover-pink",
    "lh-cover-teal",
  ];

  grid.innerHTML = "";

  COURSES.forEach(
    (course, index) => {

      if (!course.start) {
        return;
      }

      const card =
        document.createElement(
          "a"
        );

      card.className =
        "lh-course-card";

      card.dataset.course =
        course.key;

      card.dataset.total =
        String(
          course.total || 0
        );

      card.href =
  makeCourseUrl(
    course.start
      .replace(/\.md$/i, "/")
  );

      const tags =
        Array.isArray(course.tags)
          ? course.tags
          : [];

      const tagHTML =
        tags
          .slice(0, 2)
          .map(
            tag =>
              `<span>${escapeHTML(tag)}</span>`
          )
          .join("");

      const total =
        Number(
          course.total || 0
        );

      const unit =
        course.unit || "bài";

      const coverClass =
        coverClasses[
          index %
          coverClasses.length
        ];

      card.innerHTML = `
        <div class="lh-course-cover ${coverClass}">

          <div class="lh-course-symbol">
            ${escapeHTML(
              course.symbol || "LH"
            )}
          </div>

          <span>
            ${escapeHTML(
              course.category ||
              "COURSE"
            )}
          </span>

        </div>

        <div class="lh-course-content">

          <div class="lh-course-tags">
            ${tagHTML}
          </div>

          <h3>
            ${escapeHTML(
              course.title
            )}
          </h3>

          <p>
            ${escapeHTML(
              course.description ||
              "Khóa học theo lộ trình trong Learning Hub."
            )}
          </p>

          <div class="lh-course-progress">

            <div class="lh-progress-label">

              <span data-progress-count>
                0 / ${total} ${escapeHTML(unit)}
              </span>

              <strong data-progress-percent>
                0%
              </strong>

            </div>

            <div class="lh-progress-track">
              <div class="lh-progress-bar"></div>
            </div>

          </div>

          <div class="lh-course-footer">

            <span>
              ${total} ${escapeHTML(unit)}
            </span>

            <strong data-course-action>
              Bắt đầu →
            </strong>

          </div>

        </div>
      `;

      grid.appendChild(card);
    }
  );
}

  /* =========================================================
     HOMEPAGE
     ========================================================= */

  function setupHomePage() {
  document.body.classList.add(
    "lh-home-page"
  );

  renderHomeCourses();
  renderCourseProgress();
  setupContinueLearning();
}

  /* =========================================================
     IDE STORAGE
     ========================================================= */

  function codeStorageKey(language) {
    return (
      STORAGE_CODE_PREFIX +
      language
    );
  }

  function loadSavedCode(language) {
    try {
      const saved =
        localStorage.getItem(
          codeStorageKey(language)
        );

      if (
        saved !== null &&
        saved.trim() !== ""
      ) {
        return saved;
      }
    } catch (_) {
      // Ignore.
    }

    return (
      CODE_EXAMPLES[language] ||
      ""
    );
  }

  function saveCodeNow() {
    const code =
      getEditorValue();

    try {
      localStorage.setItem(
        codeStorageKey(
          currentLanguage
        ),
        code
      );

      setSaveState(
        "Đã lưu"
      );

      setUnsaved(false);
    } catch (_) {
      setSaveState(
        "Không thể lưu"
      );
    }
  }

  function scheduleSave() {
    setSaveState(
      "Đang lưu..."
    );

    setUnsaved(true);

    clearTimeout(
      saveTimer
    );

    saveTimer =
      window.setTimeout(
        saveCodeNow,
        450
      );
  }

  /* =========================================================
     IDE UI
     ========================================================= */

  function setLabStatus(
    message,
    type = ""
  ) {
    const status =
      qs("#lh-lab-status");

    if (!status) return;

    status.textContent =
      message;

    status.className =
      "lh-lab-status";

    if (type) {
      status.classList.add(
        type
      );
    }
  }

  function setRuntimeState(
    message,
    state = "ready"
  ) {
    const element =
      qs("#lh-runtime-state");

    if (!element) return;

    element.textContent =
      message;

    if (state === "error") {
      element.style.color =
        "#ff6b7d";
    } else if (
      state === "working"
    ) {
      element.style.color =
        "#f0b84b";
    } else {
      element.style.color =
        "#58c892";
    }
  }

  function setSaveState(text) {
    const element =
      qs("#lh-save-state");

    if (element) {
      element.textContent =
        text;
    }
  }

  function setUnsaved(value) {
    const indicator =
      qs(
        "#lh-unsaved-indicator"
      );

    if (indicator) {
      indicator.hidden =
        !value;
    }
  }

  function setEditorState(text) {
    const element =
      qs("#lh-editor-state");

    if (element) {
      element.textContent =
        text;
    }
  }

  function setCodeOutput(message) {
    const output =
      qs("#lh-code-output");

    if (output) {
      output.textContent =
        message;
    }
  }

  /* =========================================================
     EDITOR ACCESS
     ========================================================= */

  function getEditorValue() {
    if (
      monacoReady &&
      monacoEditor
    ) {
      return (
        monacoEditor.getValue()
      );
    }

    return (
      qs("#lh-code-editor")
        ?.value ||
      ""
    );
  }

  function setEditorValue(value) {
    if (
      monacoReady &&
      monacoEditor
    ) {
      monacoEditor.setValue(
        value
      );

      return;
    }

    const fallback =
      qs("#lh-code-editor");

    if (fallback) {
      fallback.value =
        value;
    }
  }

  /* =========================================================
     LOAD SCRIPT
     ========================================================= */

  function loadExternalScript(
    src,
    id
  ) {
    return new Promise(
      (resolve, reject) => {
        const existing =
          document.getElementById(
            id
          );

        if (existing) {
          if (
            existing.dataset.loaded ===
            "true"
          ) {
            resolve();
            return;
          }

          existing.addEventListener(
            "load",
            resolve,
            { once: true }
          );

          existing.addEventListener(
            "error",
            reject,
            { once: true }
          );

          return;
        }

        const script =
          document.createElement(
            "script"
          );

        script.id = id;
        script.src = src;
        script.async = true;

        script.onload = () => {
          script.dataset.loaded =
            "true";

          resolve();
        };

        script.onerror = () => {
          reject(
            new Error(
              `Không tải được ${src}`
            )
          );
        };

        document.head.appendChild(
          script
        );
      }
    );
  }

  /* =========================================================
     MONACO
     ========================================================= */

  function getMonacoTheme() {
    const scheme =
      document.documentElement
        .getAttribute(
          "data-md-color-scheme"
        );

    return scheme === "slate"
      ? "vs-dark"
      : "vs-dark";
  }

  function monacoLanguage(language) {
    return language === "csharp"
      ? "csharp"
      : "python";
  }

  async function loadMonaco() {
    if (
      window.monaco?.editor
    ) {
      return window.monaco;
    }

    if (monacoLoading) {
      return monacoLoading;
    }

    monacoLoading =
      (async () => {
        setEditorState(
          "Đang tải Monaco..."
        );

        await loadExternalScript(
          `${MONACO_BASE}/loader.js`,
          "lh-monaco-loader"
        );

        if (
          !window.require
        ) {
          throw new Error(
            "Monaco loader không khả dụng."
          );
        }

        window.require.config({
          paths: {
            vs: MONACO_BASE
          }
        });

        return new Promise(
          (resolve, reject) => {
            window.require(
              ["vs/editor/editor.main"],
              () => {
                resolve(
                  window.monaco
                );
              },
              error => {
                reject(error);
              }
            );
          }
        );
      })();

    try {
      return await monacoLoading;
    } catch (error) {
      monacoLoading = null;
      throw error;
    }
  }

  async function setupMonaco() {
    const container =
      qs("#lh-monaco-editor");

    const fallback =
      qs("#lh-code-editor");

    if (
      !container ||
      !fallback
    ) {
      return;
    }

    try {
      const monaco =
        await loadMonaco();

      /*
        User có thể đã đổi language
        trong lúc Monaco đang tải.
      */

      const initialCode =
        fallback.value ||
        loadSavedCode(
          currentLanguage
        );

      monacoEditor =
        monaco.editor.create(
          container,
          {
            value:
              initialCode,

            language:
              monacoLanguage(
                currentLanguage
              ),

            theme:
              getMonacoTheme(),

            automaticLayout:
              true,

            fontSize:
              14,

            lineHeight:
              23,

            fontFamily:
              "Cascadia Code, JetBrains Mono, Consolas, monospace",

            fontLigatures:
              true,

            minimap: {
              enabled:
                false
            },

            scrollBeyondLastLine:
              false,

            smoothScrolling:
              true,

            wordWrap:
              "off",

            tabSize:
              4,

            insertSpaces:
              true,

            detectIndentation:
              false,

            formatOnPaste:
              true,

            formatOnType:
              true,

            bracketPairColorization: {
              enabled:
                true
            },

            guides: {
              bracketPairs:
                true,

              indentation:
                true
            },

            padding: {
              top:
                12,

              bottom:
                12
            },

            renderLineHighlight:
              "line",

            cursorBlinking:
              "smooth",

            cursorSmoothCaretAnimation:
              "on",

            quickSuggestions:
              true,

            suggestOnTriggerCharacters:
              true
          }
        );

      monacoReady =
        true;

      fallback.style.display =
        "none";

      container.style.display =
        "block";

      setEditorState(
        "Monaco Ready"
      );

      monacoEditor.onDidChangeModelContent(
        () => {
          scheduleSave();
        }
      );

      /*
        Ctrl + Enter
      */

      monacoEditor.addCommand(
        monaco.KeyMod.CtrlCmd |
          monaco.KeyCode.Enter,

        () => {
          runCurrentCode();
        }
      );

      /*
        Ctrl + S
      */

      monacoEditor.addCommand(
        monaco.KeyMod.CtrlCmd |
          monaco.KeyCode.KeyS,

        () => {
          saveCodeNow();
        }
      );
    } catch (error) {
      console.warn(
        "Monaco unavailable, using fallback editor.",
        error
      );

      monacoReady =
        false;

      container.style.display =
        "none";

      fallback.style.display =
        "block";

      setEditorState(
        "Fallback Editor"
      );

      setLabStatus(
        "Monaco không tải được — đang dùng editor dự phòng"
      );
    }
  }

  /* =========================================================
     PYODIDE
     ========================================================= */

  async function getPythonRuntime() {
    if (pyodideInstance) {
      return pyodideInstance;
    }

    if (loadingPython) {
      return loadingPython;
    }

    loadingPython =
      (async () => {
        setLabStatus(
          "Đang tải Python..."
        );

        setRuntimeState(
          "● Loading Python",
          "working"
        );

        if (
          typeof window.loadPyodide !==
          "function"
        ) {
          await loadExternalScript(
            PYODIDE_BASE +
              "pyodide.js",

            "lh-pyodide-loader"
          );
        }

        if (
          typeof window.loadPyodide !==
          "function"
        ) {
          throw new Error(
            "Không tìm thấy loadPyodide."
          );
        }

        const runtime =
          await window.loadPyodide({
            indexURL:
              PYODIDE_BASE
          });

        pyodideInstance =
          runtime;

        setLabStatus(
          "Python sẵn sàng",
          "is-ready"
        );

        setRuntimeState(
          "● Python Ready"
        );

        return runtime;
      })();

    try {
      return await loadingPython;
    } catch (error) {
      loadingPython = null;

      setLabStatus(
        "Không tải được Python",
        "is-error"
      );

      setRuntimeState(
        "● Python Error",
        "error"
      );

      throw error;
    }
  }

  /* =========================================================
     RUN PYTHON
     ========================================================= */

  async function runPython(code) {
    const button =
      qs("#lh-run-code");

    if (!code.trim()) {
      setCodeOutput(
        "Editor đang trống."
      );

      return;
    }

    if (button) {
      button.disabled =
        true;

      button.textContent =
        "Đang chạy...";
    }

    setRuntimeState(
      "● Running",
      "working"
    );

    setCodeOutput(
      "Đang chuẩn bị Python..."
    );

    try {
      const pyodide =
        await getPythonRuntime();

      let output = "";

      pyodide.setStdout({
        batched(text) {
          output +=
            text + "\n";

          setCodeOutput(
            output
          );
        }
      });

      pyodide.setStderr({
        batched(text) {
          output +=
            text + "\n";

          setCodeOutput(
            output
          );
        }
      });

      output = "";

      setCodeOutput(
        "Đang chạy..."
      );

      const result =
        await pyodide.runPythonAsync(
          code
        );

      if (
        !output.trim()
      ) {
        if (
          result !== undefined &&
          result !== null
        ) {
          setCodeOutput(
            String(result)
          );
        } else {
          setCodeOutput(
            "✓ Chương trình chạy thành công."
          );
        }
      }

      setLabStatus(
        "Python sẵn sàng",
        "is-ready"
      );

      setRuntimeState(
        "● Python Ready"
      );
    } catch (error) {
      console.error(
        "Learning Hub Python:",
        error
      );

      setCodeOutput(
        "LỖI PYTHON\n\n" +
          (
            error?.message ||
            String(error)
          )
      );

      setLabStatus(
        "Python gặp lỗi",
        "is-error"
      );

      setRuntimeState(
        "● Error",
        "error"
      );
    } finally {
      if (button) {
        button.disabled =
          false;

        button.textContent =
          "▶ Chạy";
      }
    }
  }

  /* =========================================================
     C# RUNNER
     ========================================================= */

  function runCSharp() {
    const runner =
      qs("#lh-csharp-runner");

    const frame =
      qs("#lh-csharp-frame");

    if (
      !runner ||
      !frame
    ) {
      setCodeOutput(
        "Không tìm thấy C# Runner."
      );

      return;
    }

    if (
      !frame.getAttribute("src")
    ) {
      frame.setAttribute(
        "src",
        "https://dotnetfiddle.net/Widget/CsConsCore"
      );
    }

    runner.hidden =
      false;

    setCodeOutput(
`C# Console Runner đã mở bên dưới.

Editor phía trên dùng để luyện và lưu code C#.

Lưu ý:

C# thuần:
✓ variable
✓ if / else
✓ loop
✓ method
✓ class
✓ array
✓ List
✓ Console.WriteLine

Unity API:
• MonoBehaviour
• GameObject
• Transform
• Rigidbody
• Input
• ParticleSystem

cần Unity Editor để chạy đầy đủ.`
    );

    setLabStatus(
      "C# Practice",
      "is-ready"
    );

    setRuntimeState(
      "● C# Practice"
    );

    window.setTimeout(
      () => {
        runner.scrollIntoView({
          behavior:
            "smooth",

          block:
            "start"
        });
      },
      80
    );
  }

  /* =========================================================
     RUN CURRENT LANGUAGE
     ========================================================= */

  async function runCurrentCode() {
    const code =
      getEditorValue();

    saveCodeNow();

    if (
      currentLanguage ===
      "python"
    ) {
      await runPython(code);
      return;
    }

    runCSharp();
  }

  /* =========================================================
     LANGUAGE
     ========================================================= */

  function updateLanguageUI() {
    const filename =
      qs("#lh-code-filename");

    const icon =
      qs(
        "#lh-file-language-icon"
      );

    const statusLanguage =
      qs(
        "#lh-status-language"
      );

    if (
      currentLanguage ===
      "python"
    ) {
      if (filename) {
        filename.textContent =
          "main.py";
      }

      if (icon) {
        icon.textContent =
          "Py";
      }

      if (statusLanguage) {
        statusLanguage.textContent =
          "Python";
      }

      setLabStatus(
        pyodideInstance
          ? "Python sẵn sàng"
          : "Python runtime sẽ tải khi cần",

        pyodideInstance
          ? "is-ready"
          : ""
      );

      setRuntimeState(
        pyodideInstance
          ? "● Python Ready"
          : "● Ready"
      );
    } else {
      if (filename) {
        filename.textContent =
          "Program.cs";
      }

      if (icon) {
        icon.textContent =
          "C#";
      }

      if (statusLanguage) {
        statusLanguage.textContent =
          "C#";
      }

      setLabStatus(
        "C# Practice"
      );

      setRuntimeState(
        "● C# Practice"
      );
    }
  }

  function changeLanguage() {
    /*
      Lưu code language hiện tại
      trước khi chuyển.
    */

    if (
      monacoReady ||
      qs("#lh-code-editor")
    ) {
      saveCodeNow();
    }

    currentLanguage =
      qs("#lh-language")
        ?.value ||
      "python";

    const code =
      loadSavedCode(
        currentLanguage
      );

    if (
      monacoReady &&
      monacoEditor &&
      window.monaco
    ) {
      const model =
        monacoEditor.getModel();

      if (model) {
        window.monaco.editor
          .setModelLanguage(
            model,
            monacoLanguage(
              currentLanguage
            )
          );
      }
    }

    setEditorValue(code);

    updateLanguageUI();

    const runner =
      qs("#lh-csharp-runner");

    if (runner) {
      runner.hidden =
        true;
    }

    setCodeOutput(
      'Nhấn "Chạy" hoặc Ctrl + Enter để chạy chương trình.'
    );

    setSaveState(
      "Đã lưu"
    );

    setUnsaved(false);
  }

  /* =========================================================
     RESET
     ========================================================= */

  function resetCurrentCode() {
    const code =
      CODE_EXAMPLES[
        currentLanguage
      ] || "";

    setEditorValue(code);

    saveCodeNow();

    setCodeOutput(
      "Đã khôi phục code mẫu."
    );

    setLabStatus(
      "Đã Reset",
      "is-ready"
    );
  }

  /* =========================================================
     COPY
     ========================================================= */

  async function copyCurrentCode() {
    const code =
      getEditorValue();

    try {
      await navigator.clipboard
        .writeText(code);

      setLabStatus(
        "Đã copy code",
        "is-ready"
      );
    } catch (_) {
      const fallback =
        qs("#lh-code-editor");

      if (!fallback) return;

      fallback.value =
        code;

      fallback.style.display =
        "block";

      fallback.focus();
      fallback.select();

      try {
        document.execCommand(
          "copy"
        );

        setLabStatus(
          "Đã copy code",
          "is-ready"
        );
      } catch (_) {
        setLabStatus(
          "Không copy được code",
          "is-error"
        );
      }

      if (monacoReady) {
        fallback.style.display =
          "none";
      }
    }
  }

  /* =========================================================
     FALLBACK EDITOR
     ========================================================= */

  function setupFallbackEditor() {
    const fallback =
      qs("#lh-code-editor");

    if (!fallback) return;

    fallback.value =
      loadSavedCode(
        currentLanguage
      );

    fallback.addEventListener(
      "input",
      scheduleSave
    );

    fallback.addEventListener(
      "keydown",
      event => {
        /*
          TAB
        */

        if (
          event.key === "Tab"
        ) {
          event.preventDefault();

          const start =
            fallback.selectionStart;

          const end =
            fallback.selectionEnd;

          fallback.value =
            fallback.value.substring(
              0,
              start
            ) +
            "    " +
            fallback.value.substring(
              end
            );

          fallback.selectionStart =
            fallback.selectionEnd =
              start + 4;

          scheduleSave();

          return;
        }

        /*
          Ctrl + Enter
        */

        if (
          event.key === "Enter" &&
          (
            event.ctrlKey ||
            event.metaKey
          )
        ) {
          event.preventDefault();

          runCurrentCode();
        }

        /*
          Ctrl + S
        */

        if (
          event.key.toLowerCase() ===
            "s" &&
          (
            event.ctrlKey ||
            event.metaKey
          )
        ) {
          event.preventDefault();

          saveCodeNow();
        }
      }
    );
  }

  /* =========================================================
     EXERCISE BRIDGE
     ========================================================= */

  function installExerciseBridge() {
    /*
      API này chuẩn bị cho V4.4.

      Sau này một lesson có thể gọi:

      window.LearningHubIDE.open({
        language: "python",
        code: "for i in range(10):\\n    print(i)"
      });

      IDE sẽ nhận code trực tiếp.
    */

    window.LearningHubIDE = {
      open(options = {}) {
        const language =
          options.language ===
          "csharp"
            ? "csharp"
            : "python";

        const selector =
          qs("#lh-language");

        if (selector) {
          selector.value =
            language;
        }

        /*
          Không gọi changeLanguage()
          trước vì nó sẽ load saved code.
        */

        currentLanguage =
          language;

        updateLanguageUI();

        if (
          monacoReady &&
          monacoEditor &&
          window.monaco
        ) {
          const model =
            monacoEditor.getModel();

          if (model) {
            window.monaco.editor
              .setModelLanguage(
                model,
                monacoLanguage(
                  language
                )
              );
          }
        }

        if (
          typeof options.code ===
            "string"
        ) {
          setEditorValue(
            options.code
          );

          scheduleSave();
        }

        const lab =
          qs("#code-lab");

        if (lab) {
          lab.scrollIntoView({
            behavior:
              "smooth",

            block:
              "start"
          });
        }

        window.setTimeout(
          () => {
            monacoEditor?.focus();
          },
          450
        );
      },

      getCode() {
        return getEditorValue();
      },

      run() {
        return runCurrentCode();
      },

      reset() {
        resetCurrentCode();
      }
    };
  }

  /* =========================================================
     CODE LAB SETUP
     ========================================================= */

  function setupCodeLab() {
    const fallback =
      qs("#lh-code-editor");

    if (!fallback) {
      return;
    }

    if (
      fallback.dataset.ready ===
      "true"
    ) {
      return;
    }

    fallback.dataset.ready =
      "true";

    currentLanguage =
      qs("#lh-language")
        ?.value ||
      "python";

    setupFallbackEditor();

    updateLanguageUI();

    /* LANGUAGE */

    qs("#lh-language")
      ?.addEventListener(
        "change",
        changeLanguage
      );

    /* RUN */

    qs("#lh-run-code")
      ?.addEventListener(
        "click",
        runCurrentCode
      );

    /* RESET */

    qs("#lh-reset-code")
      ?.addEventListener(
        "click",
        resetCurrentCode
      );

    /* COPY */

    qs("#lh-copy-code")
      ?.addEventListener(
        "click",
        copyCurrentCode
      );

    /* CLEAR OUTPUT */

    qs("#lh-clear-output")
      ?.addEventListener(
        "click",
        () => {
          setCodeOutput(
            ""
          );

          setRuntimeState(
            "● Ready"
          );
        }
      );

    /* CLOSE C# */

    qs("#lh-close-csharp-runner")
      ?.addEventListener(
        "click",
        () => {
          const runner =
            qs(
              "#lh-csharp-runner"
            );

          if (runner) {
            runner.hidden =
              true;
          }
        }
      );

    installExerciseBridge();

    /*
      Monaco tải sau.
      Nếu CDN lỗi, fallback vẫn chạy.
    */

    setupMonaco();
  }

  /* =========================================================
     CATALOG
     ========================================================= */

  function setupCatalog() {
    const header =
      qs(".md-header__inner");

    if (!header) return;

    if (
      qs(
        ".lh-catalog",
        header
      )
    ) {
      return;
    }

    const wrapper =
      document.createElement(
        "div"
      );

    wrapper.className =
      "lh-catalog";

    const button =
      document.createElement(
        "button"
      );

    button.type =
      "button";

    button.className =
      "lh-catalog-button";

    button.setAttribute(
      "aria-expanded",
      "false"
    );

    button.setAttribute(
      "aria-haspopup",
      "true"
    );

    button.textContent =
      "☰ Danh mục";

    const menu =
      document.createElement(
        "div"
      );

    menu.className =
      "lh-catalog-menu";

    menu.hidden =
      true;

    const title =
      document.createElement(
        "div"
      );

    title.className =
      "lh-catalog-menu-title";

    title.textContent =
      "Khóa học";

    const links =
      document.createElement(
        "div"
      );

    links.className =
      "lh-catalog-links";

    /*
 * Danh mục được lấy trực tiếp từ navigation của MkDocs.
 *
 * Nhờ vậy khóa học mới chỉ cần được build_nav.py
 * thêm vào mkdocs.yml là tự xuất hiện ở đây.
 */

const primaryNav =
  qs(".md-sidebar--primary");

const navItems =
  primaryNav
    ? qsa(
        ".md-nav--primary > .md-nav__list > .md-nav__item",
        primaryNav
      )
    : [];

const addedCourses =
  new Set();

navItems.forEach(item => {
  const navLink =
    qs(":scope > .md-nav__link", item);

  const navLabel =
    qs(":scope > label.md-nav__link", item);

  const title =
    cleanText(
      navLink?.textContent ||
      navLabel?.textContent ||
      ""
    );

  if (
    !title ||
    title.toLowerCase() ===
      "trang chủ"
  ) {
    return;
  }

  /*
   * Tìm link bài học đầu tiên bên trong khóa.
   *
   * Một số course root của MkDocs chỉ là label
   * chứ không có URL riêng.
   */

  const firstLessonLink =
    qs(
      ".md-nav__list a.md-nav__link[href]",
      item
    );

  const href =
    navLink?.matches?.(
      "a[href]"
    )
      ? navLink.href
      : firstLessonLink?.href;

  if (!href) {
    return;
  }

  const signature =
    `${title}|${href}`;

  if (
    addedCourses.has(signature)
  ) {
    return;
  }

  addedCourses.add(signature);

  const link =
    document.createElement(
      "a"
    );

  link.href = href;
  link.textContent = title;

  links.appendChild(link);
});


/*
 * Fallback:
 *
 * Nếu vì lý do nào đó sidebar MkDocs chưa tồn tại,
 * dùng COURSES cũ để menu vẫn hoạt động.
 */

if (!links.children.length) {
  COURSES.forEach(course => {
    const link =
      document.createElement(
        "a"
      );

    link.href =
      makeCourseUrl(
        course.start
      );

    link.textContent =
      course.title;

    links.appendChild(link);
  });
}

    menu.append(
      title,
      links
    );

    button.addEventListener(
      "click",
      event => {
        event.stopPropagation();

        const open =
          menu.hidden;

        menu.hidden =
          !open;

        button.setAttribute(
          "aria-expanded",
          String(open)
        );
      }
    );

    menu.addEventListener(
      "click",
      event => {
        event.stopPropagation();
      }
    );

    document.addEventListener(
      "click",
      event => {
        if (
          wrapper.contains(
            event.target
          )
        ) {
          return;
        }

        menu.hidden =
          true;

        button.setAttribute(
          "aria-expanded",
          "false"
        );
      }
    );

    document.addEventListener(
      "keydown",
      event => {
        if (
          event.key !== "Escape" ||
          menu.hidden
        ) {
          return;
        }

        menu.hidden =
          true;

        button.setAttribute(
          "aria-expanded",
          "false"
        );

        button.focus();
      }
    );

    wrapper.append(
      button,
      menu
    );

    const search =
      qs(
        ".md-search",
        header
      );

    if (search) {
      header.insertBefore(
        wrapper,
        search
      );
    } else {
      header.appendChild(
        wrapper
      );
    }
  }

  /* =========================================================
     PAGE MODE
     ========================================================= */

  function setupPageMode() {
    if (isHomePage()) {
      setupHomePage();
      return;
    }

    document.body.classList.remove(
      "lh-home-page"
    );

    setupLessonPage();
  }

  /* =========================================================
     INIT
     ========================================================= */

  function initLearningHub() {
    document.body.classList.add(
      "learning-hub"
    );

    fixMarkdownLinks();

    setupPageMode();

    setupCatalog();

    setupCodeLab();
  }

  /* =========================================================
     MKDOCS MATERIAL
     ========================================================= */

  if (
    typeof document$ !==
      "undefined" &&
    document$?.subscribe
  ) {
    document$.subscribe(
      () => {
        initLearningHub();
      }
    );
  } else if (
    document.readyState ===
    "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      initLearningHub
    );
  } else {
    initLearningHub();
  }
})();