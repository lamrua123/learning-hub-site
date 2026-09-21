(() => {
  "use strict";

  /*
   * Learning Hub V4.7C
   * Automatic Lesson → Exercise Bridge
   *
   * Không cần chèn:
   * <!-- exercise: ... -->
   *
   * Hệ thống tự:
   * 1. nhận diện lesson Python hiện tại
   * 2. lấy số bài từ URL
   * 3. tìm exercise có lessonNumber tương ứng
   * 4. render Practice section cuối bài
   *
   * Marker thủ công cũ vẫn được hỗ trợ để tương thích.
   */

  const VERSION = "4.7C";

  const TRANSFER_KEY =
    "learningHubLessonExerciseV45";

  const STYLE_ID =
    "lh-lesson-exercise-style-v47";

  const AUTO_SECTION_ID =
    "lh-auto-exercises-v47";

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

  function escapeHTML(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function isPythonLesson() {
    const path = decodeURIComponent(
      window.location.pathname
    ).toLowerCase();

    return path.includes("/python/");
  }

  function isHomePage() {
    return Boolean(qs(".lh-home"));
  }

  function getArticle() {
    return (
      qs(".md-content__inner") ||
      qs("article")
    );
  }

  function engineReady() {
    return Boolean(
      window.LearningHubExercises &&
      typeof window.LearningHubExercises.getAll ===
        "function"
    );
  }

  function uiReady() {
    return Boolean(
      window.LearningHubExerciseUI &&
      typeof window.LearningHubExerciseUI.open ===
        "function"
    );
  }

  /* =========================================================
     LESSON NUMBER
     ========================================================= */

  function getLessonNumber() {
    const decoded = decodeURIComponent(
      window.location.pathname
    );

    /*
     * MkDocs URL ví dụ:
     *
     * /Python/
     * 03 - Input va phep toan/
     * 004 - Phep toan .../
     *
     * Tìm segment bắt đầu bằng 3 chữ số.
     */

    const segments =
      decoded
        .split("/")
        .filter(Boolean);

    for (
      let index = segments.length - 1;
      index >= 0;
      index--
    ) {
      const match =
        segments[index].match(
          /^(\d{3})(?:\s|-|$)/
        );

      if (match) {
        return match[1];
      }
    }

    return null;
  }

  /* =========================================================
     STYLE
     ========================================================= */

  function installStyle() {
    if (qs(`#${STYLE_ID}`)) return;

    const style =
      document.createElement("style");

    style.id = STYLE_ID;

    style.textContent = `
      #${AUTO_SECTION_ID} {
        margin: 42px 0 28px;
        padding-top: 28px;
        border-top: 1px solid
          var(--md-default-fg-color--lightest);
      }

      #${AUTO_SECTION_ID} .lh-le-head {
        margin-bottom: 16px;
      }

      #${AUTO_SECTION_ID} .lh-le-kicker {
        margin-bottom: 5px;
        color: #754ffe;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .1em;
      }

      #${AUTO_SECTION_ID} h2 {
        margin: 0 0 6px;
        font-size: 22px;
      }

      #${AUTO_SECTION_ID} .lh-le-intro {
        margin: 0;
        max-width: 680px;
        font-size: 13px;
        line-height: 1.65;
        opacity: .7;
      }

      #${AUTO_SECTION_ID} .lh-le-grid {
        display: grid;
        grid-template-columns:
          repeat(2, minmax(0, 1fr));
        gap: 10px;
      }

      #${AUTO_SECTION_ID} .lh-le-card {
        display: flex;
        flex-direction: column;
        min-width: 0;
        padding: 15px;
        border: 1px solid
          var(--md-default-fg-color--lightest);
        border-radius: 11px;
        background:
          var(--md-default-bg-color);
      }

      #${AUTO_SECTION_ID}
      .lh-le-card.is-complete {
        border-color:
          rgba(40, 180, 110, .32);
      }

      #${AUTO_SECTION_ID}
      .lh-le-card-top {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
      }

      #${AUTO_SECTION_ID}
      .lh-le-number {
        color: #754ffe;
        font-size: 9px;
        font-weight: 800;
        letter-spacing: .08em;
      }

      #${AUTO_SECTION_ID}
      .lh-le-status {
        flex: 0 0 auto;
        font-size: 10px;
        font-weight: 700;
        opacity: .72;
      }

      #${AUTO_SECTION_ID} h3 {
        margin: 7px 0 6px;
        font-size: 15px;
      }

      #${AUTO_SECTION_ID}
      .lh-le-description {
        flex: 1;
        margin: 0;
        font-size: 12px;
        line-height: 1.6;
        opacity: .72;
      }

      #${AUTO_SECTION_ID}
      .lh-le-meta {
        margin-top: 11px;
        font-size: 10px;
        opacity: .58;
      }

      #${AUTO_SECTION_ID}
      .lh-le-button {
        width: 100%;
        margin-top: 12px;
        padding: 8px 10px;
        border: 1px solid #754ffe;
        border-radius: 7px;
        background: #754ffe;
        color: #fff;
        font: inherit;
        font-size: 11px;
        font-weight: 800;
        cursor: pointer;
      }

      #${AUTO_SECTION_ID}
      .lh-le-button:hover {
        filter: brightness(1.06);
      }

      @media (max-width: 700px) {
        #${AUTO_SECTION_ID}
        .lh-le-grid {
          grid-template-columns: 1fr;
        }
      }
    `;

    document.head.appendChild(style);
  }

  /* =========================================================
     EXERCISE MAPPING
     ========================================================= */

  function getExercisesForLesson(
    lessonNumber
  ) {
    if (!engineReady()) {
      return [];
    }

    return window.LearningHubExercises
      .getAll()
      .filter(
        exercise =>
          String(
            exercise.lessonNumber || ""
          ).padStart(3, "0") ===
          lessonNumber
      );
  }

  /* =========================================================
     RENDER
     ========================================================= */

  function renderAutoExercises() {
    if (
      !isPythonLesson() ||
      isHomePage() ||
      !engineReady()
    ) {
      return;
    }

    const article =
      getArticle();

    if (!article) return;

    qs(`#${AUTO_SECTION_ID}`)?.remove();

    const lessonNumber =
      getLessonNumber();

    if (!lessonNumber) {
      return;
    }

    const exercises =
      getExercisesForLesson(
        lessonNumber
      );

    /*
     * Lesson chưa có exercise:
     * không render gì.
     */

    if (!exercises.length) {
      return;
    }

    installStyle();

    const section =
      document.createElement("section");

    section.id =
      AUTO_SECTION_ID;

    const cards =
      exercises
        .map(
          (exercise, index) => {
            const completed =
              window.LearningHubExercises
                .isCompleted(
                  exercise.id
                );

            const state =
              window.LearningHubExercises
                .getState(
                  exercise.id
                );

            const difficulty =
              Math.max(
                1,
                Math.min(
                  3,
                  Number(
                    exercise.difficulty || 1
                  )
                )
              );

            return `
              <article
                class="
                  lh-le-card
                  ${
                    completed
                      ? "is-complete"
                      : ""
                  }
                "
              >
                <div class="lh-le-card-top">
                  <div class="lh-le-number">
                    EXERCISE ${index + 1}
                  </div>

                  <div class="lh-le-status">
                    ${
                      completed
                        ? "✅ Hoàn thành"
                        : state?.attempts
                          ? `Đã thử ${state.attempts} lần`
                          : "Chưa làm"
                    }
                  </div>
                </div>

                <h3>
                  ${escapeHTML(
                    exercise.title
                  )}
                </h3>

                <p class="lh-le-description">
                  ${escapeHTML(
                    exercise.description
                  )}
                </p>

                <div class="lh-le-meta">
                  Python
                  · Độ khó
                  ${"★".repeat(difficulty)}
                  ${"☆".repeat(
                    3 - difficulty
                  )}
                </div>

                <button
                  type="button"
                  class="lh-le-button"
                  data-lh-exercise-id="${
                    escapeHTML(
                      exercise.id
                    )
                  }"
                >
                  ${
                    completed
                      ? "↺ Luyện lại"
                      : state?.attempts
                        ? "▶ Tiếp tục bài tập"
                        : "▶ Bắt đầu thực hành"
                  }
                </button>
              </article>
            `;
          }
        )
        .join("");

    section.innerHTML = `
      <div class="lh-le-head">
        <div class="lh-le-kicker">
          THỰC HÀNH
        </div>

        <h2>
          🧩 Bài tập của bài học này
        </h2>

        <p class="lh-le-intro">
          Thử tự viết code trước khi xem gợi ý.
          Code và tiến độ của bạn sẽ được tự động lưu.
        </p>
      </div>

      <div class="lh-le-grid">
        ${cards}
      </div>
    `;

    article.appendChild(section);

    qsa(
      "[data-lh-exercise-id]",
      section
    ).forEach(button => {
      button.addEventListener(
        "click",
        () => {
          openExerciseFromLesson(
            button.dataset.lhExerciseId
          );
        }
      );
    });
  }

  /* =========================================================
     OPEN EXERCISE
     ========================================================= */

  function openExerciseFromLesson(id) {
    const payload = {
      exerciseId: id,
      sourceUrl:
        window.location.href,
      createdAt:
        Date.now()
    };

    try {
      sessionStorage.setItem(
        TRANSFER_KEY,
        JSON.stringify(payload)
      );
    } catch (_) {
      // Ignore storage failure.
    }

    const home =
      getHomeUrl();

    window.location.href =
      `${home}#code-lab`;
  }

  function getHomeUrl() {
    const logo =
      qs(".md-header__button.md-logo");

    if (logo?.href) {
      return logo.href;
    }

    /*
     * GitHub Pages fallback.
     */

    const marker =
      "/learning-hub-site/";

    const path =
      window.location.pathname;

    const index =
      path.indexOf(marker);

    if (index >= 0) {
      return (
        window.location.origin +
        path.slice(
          0,
          index + marker.length
        )
      );
    }

    return (
      window.location.origin + "/"
    );
  }

  /* =========================================================
     HOMEPAGE TRANSFER
     ========================================================= */

  function consumeTransfer() {
    if (!isHomePage()) return;

    let payload = null;

    try {
      payload =
        JSON.parse(
          sessionStorage.getItem(
            TRANSFER_KEY
          ) || "null"
        );
    } catch (_) {
      payload = null;
    }

    if (
      !payload?.exerciseId
    ) {
      return;
    }

    /*
     * Xóa trước để refresh không tự mở
     * exercise mãi mãi.
     */

    try {
      sessionStorage.removeItem(
        TRANSFER_KEY
      );
    } catch (_) {
      // Ignore.
    }

    const open =
      (attempt = 0) => {
        if (uiReady()) {
          window.LearningHubExerciseUI.open(
            payload.exerciseId,
            {
              sourceUrl:
                payload.sourceUrl || null
            }
          );

          return;
        }

        if (attempt >= 100) {
          console.error(
            "[Learning Hub] Exercise UI chưa sẵn sàng."
          );
          return;
        }

        setTimeout(
          () =>
            open(attempt + 1),
          100
        );
      };

    open();
  }

  /* =========================================================
     LEGACY MANUAL MARKERS
     ========================================================= */

  function renderLegacyMarkers() {
    if (
      !isPythonLesson() ||
      !engineReady()
    ) {
      return;
    }

    const article =
      getArticle();

    if (!article) return;

    const walker =
      document.createTreeWalker(
        article,
        NodeFilter.SHOW_COMMENT
      );

    const comments = [];

    while (walker.nextNode()) {
      comments.push(
        walker.currentNode
      );
    }

    comments.forEach(comment => {
      const match =
        comment.nodeValue?.match(
          /exercise\s*:\s*([a-zA-Z0-9_-]+)/i
        );

      if (!match) return;

      const id =
        match[1];

      /*
       * Nếu exercise này đã được auto-render
       * bằng lessonNumber thì xóa marker cũ
       * để tránh duplicate.
       */

      const lessonNumber =
        getLessonNumber();

      const autoExercises =
        lessonNumber
          ? getExercisesForLesson(
              lessonNumber
            )
          : [];

      const alreadyAutomatic =
        autoExercises.some(
          exercise =>
            exercise.id === id
        );

      if (alreadyAutomatic) {
        comment.remove();
        return;
      }

      const exercise =
        window.LearningHubExercises.get(
          id
        );

      if (!exercise) return;

      /*
       * Marker legacy vẫn hoạt động,
       * nhưng chỉ tạo button nhỏ.
       */

      const wrapper =
        document.createElement("div");

      wrapper.style.margin =
        "18px 0";

      wrapper.innerHTML = `
        <button
          type="button"
          class="lh-le-button"
          data-legacy-exercise="${
            escapeHTML(id)
          }"
          style="
            width:auto;
            padding:9px 13px;
          "
        >
          🧩 ${escapeHTML(
            exercise.title
          )}
        </button>
      `;

      comment.replaceWith(
        wrapper
      );

      qs(
        "[data-legacy-exercise]",
        wrapper
      )?.addEventListener(
        "click",
        () =>
          openExerciseFromLesson(id)
      );
    });
  }

  /* =========================================================
     INIT
     ========================================================= */

  function init() {
    if (
      !isPythonLesson() &&
      !isHomePage()
    ) {
      return;
    }

    const wait =
      (attempt = 0) => {
        if (engineReady()) {
          if (isPythonLesson()) {
            renderAutoExercises();
            renderLegacyMarkers();
          }

          if (isHomePage()) {
            consumeTransfer();
          }

          return;
        }

        if (attempt >= 100) {
          console.error(
            "[Learning Hub] Exercise Engine chưa sẵn sàng."
          );
          return;
        }

        setTimeout(
          () =>
            wait(attempt + 1),
          100
        );
      };

    wait();
  }

  window.LearningHubLessonExercises = {
    version: VERSION,
    getLessonNumber,
    render: renderAutoExercises
  };

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