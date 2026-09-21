(() => {
  "use strict";

  /*
   * Learning Hub V4.4C
   *
   * Code block Python/C#
   *        ↓
   * Learning IDE
   *        ↓
   * Autosave riêng từng bài + từng code block
   *        ↓
   * Quay lại bài
   *        ↓
   * Mở lại → tiếp tục code cũ
   */

  const BUTTON_CLASS = "lh-code-practice-button";
  const WRAPPER_CLASS = "lh-code-practice-wrapper";

  const TRANSFER_KEY = "learningHubCodeTransferV44";
  const PRACTICE_PREFIX = "learningHubPracticeV44:";

  let practiceSaveTimer = null;

  function qs(selector, root = document) {
    return root.querySelector(selector);
  }

  function qsa(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
  }

  function safeDecode(value) {
    try {
      return decodeURIComponent(value);
    } catch (_) {
      return value;
    }
  }

  function getSiteBaseUrl() {
    const logo = qs("a.md-header__button.md-logo");

    if (logo?.href) {
      let url = logo.href;

      if (!url.endsWith("/")) {
        url += "/";
      }

      return url;
    }

    const pathname = window.location.pathname;
    const marker = "/learning-hub-site/";
    const index = pathname.indexOf(marker);

    if (index >= 0) {
      return (
        window.location.origin +
        pathname.slice(0, index + marker.length)
      );
    }

    return window.location.origin + "/";
  }

  function getCurrentCourseLanguage() {
    const path = safeDecode(
      window.location.pathname
    ).toLowerCase();

    if (path.includes("/python/")) {
      return "python";
    }

    if (
      path.includes(
        "/c sharp unity, game/"
      )
    ) {
      return "csharp";
    }

    return null;
  }

  function detectLanguageFromClass(code) {
    const className = Array.from(code.classList)
      .join(" ")
      .toLowerCase();

    if (
      className.includes("language-python") ||
      className.includes("language-py")
    ) {
      return "python";
    }

    if (
      className.includes("language-csharp") ||
      className.includes("language-cs") ||
      className.includes("language-c#")
    ) {
      return "csharp";
    }

    return null;
  }

  function looksLikePython(text) {
    if (!text) return false;

    const signals = [
      /\bprint\s*\(/,
      /\bdef\s+[A-Za-z_]\w*\s*\(/,
      /\bfor\s+\w+\s+in\s+/,
      /\bwhile\s+.+:/,
      /\bif\s+.+:/,
      /\belif\s+.+:/,
      /\bimport\s+[A-Za-z_]/,
      /\bfrom\s+[A-Za-z_.]+\s+import\s+/,
      /\bclass\s+[A-Za-z_]\w*\s*[:(]/
    ];

    return signals.some(pattern =>
      pattern.test(text)
    );
  }

  function looksLikeCSharp(text) {
    if (!text) return false;

    const signals = [
      /\busing\s+System\s*;/,
      /\bConsole\.WriteLine\s*\(/,
      /\bpublic\s+class\s+[A-Za-z_]\w*/,
      /\bstatic\s+void\s+Main\s*\(/,
      /\bvoid\s+[A-Za-z_]\w*\s*\(/,
      /\bint\s+[A-Za-z_]\w*\s*[=;]/,
      /\bstring\s+[A-Za-z_]\w*\s*[=;]/,
      /\bDebug\.Log\s*\(/,
      /\bMonoBehaviour\b/,
      /\bGameObject\b/,
      /\bTransform\b/
    ];

    return signals.some(pattern =>
      pattern.test(text)
    );
  }

  function detectCodeLanguage(code, courseLanguage) {
    const explicit = detectLanguageFromClass(code);

    if (explicit) {
      return explicit === courseLanguage
        ? explicit
        : null;
    }

    const text = code.textContent || "";

    if (
      courseLanguage === "python" &&
      looksLikePython(text)
    ) {
      return "python";
    }

    if (
      courseLanguage === "csharp" &&
      looksLikeCSharp(text)
    ) {
      return "csharp";
    }

    return null;
  }

  function getLessonTitle() {
    return (
      qs(".md-content__inner h1")
        ?.textContent
        ?.trim() ||
      document.title ||
      "Bài học"
    );
  }

  function getLessonId() {
    return safeDecode(window.location.pathname)
      .replace(/\/+$/, "")
      .toLowerCase();
  }

  /*
   * Một bài có thể có nhiều code block.
   * blockIndex giúp mỗi block có save riêng.
   */

  function getPracticeStorageKey(blockIndex) {
    return (
      PRACTICE_PREFIX +
      encodeURIComponent(getLessonId()) +
      ":" +
      blockIndex
    );
  }

  function readSavedPractice(storageKey) {
    try {
      const raw = localStorage.getItem(storageKey);

      if (!raw) {
        return null;
      }

      const value = JSON.parse(raw);

      if (
        !value ||
        typeof value.code !== "string"
      ) {
        return null;
      }

      return value;
    } catch (_) {
      return null;
    }
  }

  function savePractice(storageKey, data) {
    try {
      localStorage.setItem(
        storageKey,
        JSON.stringify({
          ...data,
          updatedAt: Date.now()
        })
      );

      return true;
    } catch (_) {
      return false;
    }
  }

  function openCodeInIDE(
    language,
    originalCode,
    blockIndex
  ) {
    const storageKey =
      getPracticeStorageKey(blockIndex);

    const previous =
      readSavedPractice(storageKey);

    /*
     * Nếu từng luyện block này:
     * mở code đã sửa.
     *
     * Nếu chưa:
     * dùng code gốc từ bài học.
     */

    const code =
      previous?.code || originalCode;

    const payload = {
      language,
      code,
      originalCode,
      blockIndex,
      storageKey,
      lessonId: getLessonId(),
      lessonTitle: getLessonTitle(),
      sourceUrl: window.location.href,
      createdAt: Date.now()
    };

    try {
      sessionStorage.setItem(
        TRANSFER_KEY,
        JSON.stringify(payload)
      );
    } catch (error) {
      console.error(
        "Không thể chuyển code sang IDE:",
        error
      );

      return;
    }

    const home = new URL(getSiteBaseUrl());

    home.hash = "code-lab";

    window.location.href = home.href;
  }

  function createButton(
    language,
    codeElement,
    blockIndex
  ) {
    const button =
      document.createElement("button");

    button.type = "button";
    button.className = BUTTON_CLASS;
    button.dataset.language = language;

    const storageKey =
      getPracticeStorageKey(blockIndex);

    const saved =
      readSavedPractice(storageKey);

    button.innerHTML = saved
      ? "💻&nbsp; Tiếp tục IDE"
      : "💻&nbsp; Thực hành IDE";

    button.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();

      const originalCode =
        codeElement.textContent || "";

      if (!originalCode.trim()) {
        button.innerHTML = "⚠ Không có code";

        window.setTimeout(() => {
          button.innerHTML =
            "💻&nbsp; Thực hành IDE";
        }, 1200);

        return;
      }

      button.innerHTML = "Đang mở IDE...";

      openCodeInIDE(
        language,
        originalCode,
        blockIndex
      );
    });

    return button;
  }

  function installStyle() {
    if (
      document.getElementById(
        "lh-code-practice-style"
      )
    ) {
      return;
    }

    const style =
      document.createElement("style");

    style.id = "lh-code-practice-style";

    style.textContent = `
      .${WRAPPER_CLASS} {
        position: relative;
      }

      .${BUTTON_CLASS} {
        position: absolute;
        z-index: 4;
        top: 8px;
        right: 8px;

        min-height: 28px;
        padding: 4px 9px;

        border:
          1px solid
          rgba(117, 79, 254, 0.45);

        border-radius: 6px;

        background:
          rgba(25, 25, 35, 0.92);

        color: #fff;

        font: inherit;
        font-size: 11px;
        font-weight: 700;
        line-height: 1;

        cursor: pointer;
        opacity: 0.72;

        box-shadow:
          0 3px 10px
          rgba(0, 0, 0, 0.14);

        transition:
          opacity 120ms ease,
          transform 120ms ease,
          background 120ms ease;
      }

      .${WRAPPER_CLASS}:hover
      .${BUTTON_CLASS},
      .${BUTTON_CLASS}:focus-visible {
        opacity: 1;
      }

      .${BUTTON_CLASS}:hover {
        background: #754ffe;
        transform: translateY(-1px);
      }

      .${BUTTON_CLASS}:active {
        transform: none;
      }

      @media (max-width: 600px) {
        .${BUTTON_CLASS} {
          top: 6px;
          right: 6px;
          padding: 4px 7px;
          font-size: 10px;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .${BUTTON_CLASS} {
          transition: none;
        }
      }
    `;

    document.head.appendChild(style);
  }

  function decorateCodeBlock(
    pre,
    code,
    language,
    blockIndex
  ) {
    if (
      pre.dataset.lhPracticeReady ===
      "true"
    ) {
      return;
    }

    pre.dataset.lhPracticeReady = "true";

    const highlight =
      pre.closest(".highlight");

    const wrapper =
      highlight || pre;

    wrapper.classList.add(
      WRAPPER_CLASS
    );

    if (
      qs(`.${BUTTON_CLASS}`, wrapper)
    ) {
      return;
    }

    wrapper.appendChild(
      createButton(
        language,
        code,
        blockIndex
      )
    );
  }

  function scanCodeBlocks() {
    const language =
      getCurrentCourseLanguage();

    if (!language) {
      return;
    }

    const article =
      qs(".md-content__inner");

    if (!article) {
      return;
    }

    installStyle();

    const blocks =
      qsa("pre code", article);

    blocks.forEach((code, index) => {
      const pre =
        code.closest("pre");

      if (!pre) {
        return;
      }

      const detected =
        detectCodeLanguage(
          code,
          language
        );

      if (!detected) {
        return;
      }

      decorateCodeBlock(
        pre,
        code,
        detected,
        index
      );
    });
  }

  function isHomePage() {
    return Boolean(qs(".lh-home"));
  }

  function readTransfer() {
    try {
      const raw =
        sessionStorage.getItem(
          TRANSFER_KEY
        );

      if (!raw) {
        return null;
      }

      return JSON.parse(raw);
    } catch (_) {
      return null;
    }
  }

  function clearTransfer() {
    try {
      sessionStorage.removeItem(
        TRANSFER_KEY
      );
    } catch (_) {
      // Ignore.
    }
  }

  function waitForIDE(callback, attempt = 0) {
    if (
      window.LearningHubIDE &&
      typeof window.LearningHubIDE.open ===
        "function"
    ) {
      callback();
      return;
    }

    if (attempt >= 100) {
      console.error(
        "LearningHubIDE API không sẵn sàng."
      );

      return;
    }

    window.setTimeout(() => {
      waitForIDE(
        callback,
        attempt + 1
      );
    }, 100);
  }

  function showPracticeBanner(payload) {
    const lab =
      qs("#code-lab");

    if (!lab) return;

    qs(
      "#lh-practice-context",
      lab
    )?.remove();

    const banner =
      document.createElement("div");

    banner.id =
      "lh-practice-context";

    banner.style.cssText = `
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;

      margin:0 0 12px;
      padding:10px 12px;

      border:
        1px solid
        rgba(117,79,254,.22);

      border-radius:8px;

      background:
        rgba(117,79,254,.07);
    `;

    const info =
      document.createElement("div");

    info.style.cssText =
      "min-width:0;";

    const label =
      document.createElement("div");

    label.textContent =
      "ĐANG THỰC HÀNH";

    label.style.cssText = `
      margin-bottom:3px;
      color:#754ffe;
      font-size:10px;
      font-weight:800;
      letter-spacing:.08em;
    `;

    const title =
      document.createElement("strong");

    title.textContent =
      payload.lessonTitle ||
      "Bài học";

    title.style.cssText = `
      display:block;
      overflow:hidden;
      text-overflow:ellipsis;
      white-space:nowrap;
      font-size:13px;
    `;

    const status =
      document.createElement("small");

    status.id =
      "lh-practice-save-state";

    status.textContent =
      "Code của bài này được lưu riêng";

    status.style.cssText = `
      display:block;
      margin-top:3px;
      opacity:.7;
      font-size:10px;
    `;

    info.append(
      label,
      title,
      status
    );

    const back =
      document.createElement("a");

    back.href =
      payload.sourceUrl || "#";

    back.textContent =
      "← Quay lại bài học";

    back.style.cssText = `
      flex:0 0 auto;
      font-size:12px;
      font-weight:700;
      text-decoration:none;
    `;

    banner.append(
      info,
      back
    );

    const shell =
      qs(".lh-ide-shell", lab);

    if (shell) {
      shell.before(banner);
    } else {
      lab.prepend(banner);
    }
  }

  function setPracticeSaveState(text) {
    const element =
      qs("#lh-practice-save-state");

    if (element) {
      element.textContent = text;
    }
  }

  /*
   * V4.3 expose:
   *
   * LearningHubIDE.getCode()
   *
   * nên V4.4C có thể autosave
   * mà không sửa learning-hub.js.
   */

  function startPracticeAutosave(payload) {
    if (!payload.storageKey) {
      return;
    }

    let lastSavedCode =
      payload.code;

    /*
     * Lưu ngay trạng thái ban đầu.
     */

    savePractice(
      payload.storageKey,
      {
        code: payload.code,
        language: payload.language,
        lessonId: payload.lessonId,
        lessonTitle: payload.lessonTitle,
        sourceUrl: payload.sourceUrl,
        blockIndex: payload.blockIndex
      }
    );

    clearInterval(
      practiceSaveTimer
    );

    practiceSaveTimer =
      window.setInterval(() => {
        if (
          !window.LearningHubIDE ||
          typeof window.LearningHubIDE.getCode !==
            "function"
        ) {
          return;
        }

        const currentCode =
          window.LearningHubIDE.getCode();

        if (
          currentCode === lastSavedCode
        ) {
          return;
        }

        setPracticeSaveState(
          "Đang lưu..."
        );

        const success =
          savePractice(
            payload.storageKey,
            {
              code: currentCode,
              language: payload.language,
              lessonId: payload.lessonId,
              lessonTitle: payload.lessonTitle,
              sourceUrl: payload.sourceUrl,
              blockIndex: payload.blockIndex
            }
          );

        if (success) {
          lastSavedCode =
            currentCode;

          setPracticeSaveState(
            "✓ Đã lưu code của bài này"
          );
        } else {
          setPracticeSaveState(
            "⚠ Không thể lưu code"
          );
        }
      }, 700);

    /*
     * Save lần cuối trước khi rời trang.
     */

    const finalSave = () => {
      if (
        window.LearningHubIDE &&
        typeof window.LearningHubIDE.getCode ===
          "function"
      ) {
        const code =
          window.LearningHubIDE.getCode();

        savePractice(
          payload.storageKey,
          {
            code,
            language: payload.language,
            lessonId: payload.lessonId,
            lessonTitle: payload.lessonTitle,
            sourceUrl: payload.sourceUrl,
            blockIndex: payload.blockIndex
          }
        );
      }

      clearInterval(
        practiceSaveTimer
      );
    };

    window.addEventListener(
      "pagehide",
      finalSave,
      { once: true }
    );
  }

  function receiveCodeInIDE() {
    if (!isHomePage()) {
      return;
    }

    const payload =
      readTransfer();

    if (
      !payload ||
      !payload.code ||
      !payload.language
    ) {
      return;
    }

    clearTransfer();

    waitForIDE(() => {
      window.LearningHubIDE.open({
        language:
          payload.language,

        code:
          payload.code
      });

      showPracticeBanner(
        payload
      );

      startPracticeAutosave(
        payload
      );

      const lab =
        qs("#code-lab");

      if (lab) {
        window.setTimeout(() => {
          lab.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });
        }, 150);
      }
    });
  }

  function init() {
    window.setTimeout(
      scanCodeBlocks,
      80
    );

    window.setTimeout(
      receiveCodeInIDE,
      100
    );
  }

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