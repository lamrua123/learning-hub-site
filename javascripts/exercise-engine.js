(() => {
  "use strict";

  /*
   * =========================================================
   * LEARNING HUB V4.6B
   * EXERCISE ENGINE
   * =========================================================
   *
   * DATA:
   * LearningHubExerciseCatalog
   *
   * ENGINE:
   * - state
   * - autosave data
   * - hints
   * - grading
   * - completion
   * - progress
   *
   * Không chứa exercise hard-code.
   */

  const VERSION = "4.6B";

  const STORAGE_PREFIX =
    "learningHubExerciseV45:";

  const COMPLETION_KEY =
    "learningHubExerciseCompletionV45";

  /* =========================================================
     CATALOG
     ========================================================= */

  function getCatalog() {
    return (
      window.LearningHubExerciseCatalog ||
      null
    );
  }

  function catalogReady() {
    const catalog = getCatalog();

    return Boolean(
      catalog &&
      typeof catalog.get === "function" &&
      typeof catalog.getAll === "function"
    );
  }

  function clone(value) {
    if (value == null) {
      return value;
    }

    return JSON.parse(
      JSON.stringify(value)
    );
  }

  function getExercise(id) {
    const catalog = getCatalog();

    if (!catalog) {
      return null;
    }

    return clone(
      catalog.get(id)
    );
  }

  function getAllExercises() {
    const catalog = getCatalog();

    if (!catalog) {
      return [];
    }

    return catalog
      .getAll()
      .map(clone);
  }

  /* =========================================================
     STORAGE
     ========================================================= */

  function storageKey(id) {
    return STORAGE_PREFIX + id;
  }

  function readJSON(
    key,
    fallback = null
  ) {
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

  function writeJSON(
    key,
    value
  ) {
    try {
      localStorage.setItem(
        key,
        JSON.stringify(value)
      );

      return true;
    } catch (_) {
      return false;
    }
  }

  /* =========================================================
     OUTPUT
     ========================================================= */

  function normalizeOutput(value) {
    return String(value ?? "")
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      .trim();
  }

  /* =========================================================
     DEFAULT STATE
     ========================================================= */

  function createDefaultState(
    exercise
  ) {
    return {
      id: exercise.id,

      code:
        exercise.starterCode,

      hintIndex: 0,

      attempts: 0,

      completed: false,

      lastOutput: "",

      lastResult: null,

      startedAt:
        Date.now(),

      updatedAt:
        Date.now(),

      completedAt: null
    };
  }

  /* =========================================================
     STATE
     ========================================================= */

  function getState(id) {
    const exercise =
      getExercise(id);

    if (!exercise) {
      return null;
    }

    const defaults =
      createDefaultState(
        exercise
      );

    const saved =
      readJSON(
        storageKey(id),
        null
      );

    if (!saved) {
      return defaults;
    }

    return {
      ...defaults,
      ...saved,
      id
    };
  }

  function saveState(
    id,
    patch
  ) {
    const exercise =
      getExercise(id);

    if (!exercise) {
      return false;
    }

    const current =
      getState(id);

    if (!current) {
      return false;
    }

    const next = {
      ...current,
      ...patch,

      id,

      updatedAt:
        Date.now()
    };

    return writeJSON(
      storageKey(id),
      next
    );
  }

  /* =========================================================
     CODE
     ========================================================= */

  function getCode(id) {
    return (
      getState(id)?.code ??
      ""
    );
  }

  function saveCode(
    id,
    code
  ) {
    return saveState(
      id,
      {
        code:
          String(code ?? "")
      }
    );
  }

  /* =========================================================
     RESET
     ========================================================= */

  function resetExercise(id) {
    const exercise =
      getExercise(id);

    if (!exercise) {
      return false;
    }

    /*
     * Reset workspace của exercise.
     *
     * Completion global được giữ lại:
     * người học đã từng hoàn thành bài
     * thì thành tích đó không bị mất
     * chỉ vì họ muốn luyện lại.
     */

    const state =
      createDefaultState(
        exercise
      );

    return writeJSON(
      storageKey(id),
      state
    );
  }

  /* =========================================================
     HINTS
     ========================================================= */

  function getNextHint(id) {
    const exercise =
      getExercise(id);

    const state =
      getState(id);

    if (
      !exercise ||
      !state
    ) {
      return null;
    }

    const hints =
      Array.isArray(
        exercise.hints
      )
        ? exercise.hints
        : [];

    if (!hints.length) {
      return null;
    }

    const rawIndex =
      Number(
        state.hintIndex || 0
      );

    /*
     * Khi đã xem hết hint:
     * trả lại hint cuối cùng,
     * không tăng index vô hạn.
     */

    const index =
      Math.min(
        rawIndex,
        hints.length - 1
      );

    const hint =
      hints[index];

    const nextIndex =
      Math.min(
        index + 1,
        hints.length
      );

    saveState(
      id,
      {
        hintIndex:
          nextIndex
      }
    );

    return {
      hint,

      index,

      number:
        index + 1,

      total:
        hints.length,

      hasMore:
        nextIndex <
        hints.length
    };
  }

  /* =========================================================
     TEST — OUTPUT
     ========================================================= */

  function checkOutputTest(
    test,
    output
  ) {
    const actual =
      normalizeOutput(
        output
      );

    const expected =
      normalizeOutput(
        test.expected
      );

    return {
      passed:
        actual === expected,

      type:
        "output",

      label:
        test.label ||
        "Kiểm tra output",

      expected,

      actual
    };
  }

  /* =========================================================
     TEST DISPATCHER
     ========================================================= */

  function runTest(
    test,
    execution
  ) {
    if (
      test.type ===
      "output"
    ) {
      return checkOutputTest(
        test,
        execution.output
      );
    }

    return {
      passed: false,

      type:
        test.type ||
        "unknown",

      label:
        test.label ||
        "Test không hỗ trợ",

      expected:
        test.expected ?? "",

      actual: "",

      error:
        `Exercise Engine chưa hỗ trợ test type "${test.type}".`
    };
  }

  /* =========================================================
     EVALUATE
     ========================================================= */

  function evaluate(
    id,
    execution = {}
  ) {
    const exercise =
      getExercise(id);

    const state =
      getState(id);

    if (
      !exercise ||
      !state
    ) {
      return {
        passed: false,

        error:
          "Không tìm thấy bài tập."
      };
    }

    const output =
      execution.output ?? "";

    const runtimeError =
      execution.error ?? null;

    /*
     * Runtime error.
     */

    if (runtimeError) {
      const result = {
        passed: false,

        runtimeError:
          String(runtimeError),

        tests: [],

        message:
          "Chương trình đang có lỗi khi chạy."
      };

      saveState(
        id,
        {
          attempts:
            state.attempts + 1,

          lastOutput:
            output,

          lastResult:
            result
        }
      );

      return result;
    }

    const tests =
      Array.isArray(
        exercise.tests
      )
        ? exercise.tests
        : [];

    const results =
      tests.map(test =>
        runTest(
          test,
          {
            output,
            error:
              runtimeError
          }
        )
      );

    const passed =
      results.length > 0 &&
      results.every(
        result =>
          result.passed
      );

    const result = {
      passed,

      runtimeError: null,

      tests:
        results,

      message:
        passed
          ? "Chính xác! Bạn đã hoàn thành bài tập."
          : "Chưa đúng. Hãy xem kết quả và thử lại."
    };

    const patch = {
      attempts:
        state.attempts + 1,

      lastOutput:
        output,

      lastResult:
        result
    };

    if (passed) {
      patch.completed =
        true;

      /*
       * Chỉ ghi thời gian hoàn thành
       * lần đầu.
       */

      patch.completedAt =
        state.completedAt ||
        Date.now();
    }

    saveState(
      id,
      patch
    );

    if (passed) {
      markCompleted(id);
    }

    return result;
  }

  /* =========================================================
     COMPLETION
     ========================================================= */

  function getCompletionData() {
    return (
      readJSON(
        COMPLETION_KEY,
        {}
      ) || {}
    );
  }

  function markCompleted(id) {
    const data =
      getCompletionData();

    if (!data[id]) {
      data[id] = {
        completed: true,

        completedAt:
          Date.now()
      };

      writeJSON(
        COMPLETION_KEY,
        data
      );
    }

    return true;
  }

  function isCompleted(id) {
    const data =
      getCompletionData();

    return Boolean(
      data[id]?.completed
    );
  }

  /* =========================================================
     PROGRESS
     ========================================================= */

  function getProgress() {
    const exercises =
      getAllExercises();

    const total =
      exercises.length;

    const completed =
      exercises.filter(
        exercise =>
          isCompleted(
            exercise.id
          )
      ).length;

    return {
      completed,

      total,

      percent:
        total > 0
          ? Math.round(
              (
                completed /
                total
              ) * 100
            )
          : 0
    };
  }

  /* =========================================================
     FILTERS
     ========================================================= */

  function getByLanguage(
    language
  ) {
    return getAllExercises()
      .filter(
        exercise =>
          exercise.language ===
          language
      );
  }

  function getByChapter(
    chapter
  ) {
    return getAllExercises()
      .filter(
        exercise =>
          exercise.chapter ===
          chapter
      );
  }

  function getByLesson(
    lessonId
  ) {
    return getAllExercises()
      .filter(
        exercise =>
          exercise.lessonId ===
          lessonId
      );
  }

  /* =========================================================
     VALIDATION
     ========================================================= */

  function validateExercise(
    exercise
  ) {
    const errors = [];

    if (!exercise?.id) {
      errors.push(
        "Thiếu id."
      );
    }

    if (
      exercise?.language !==
      "python"
    ) {
      errors.push(
        "Hiện tại Exercise Engine chỉ hỗ trợ Python."
      );
    }

    if (!exercise?.title) {
      errors.push(
        "Thiếu title."
      );
    }

    if (
      typeof exercise?.description !==
      "string"
    ) {
      errors.push(
        "Thiếu description."
      );
    }

    if (
      typeof exercise?.starterCode !==
      "string"
    ) {
      errors.push(
        "Thiếu starterCode."
      );
    }

    if (
      !Array.isArray(
        exercise?.tests
      ) ||
      exercise.tests.length ===
        0
    ) {
      errors.push(
        "Bài tập chưa có test."
      );
    }

    if (
      Array.isArray(
        exercise?.tests
      )
    ) {
      exercise.tests.forEach(
        (test, index) => {
          if (!test?.type) {
            errors.push(
              `Test ${index + 1} thiếu type.`
            );
          }

          if (
            test?.type ===
              "output" &&
            test.expected ===
              undefined
          ) {
            errors.push(
              `Output test ${index + 1} thiếu expected.`
            );
          }
        }
      );
    }

    return {
      valid:
        errors.length === 0,

      errors
    };
  }

  function validateAll() {
    return getAllExercises()
      .map(exercise => ({
        id:
          exercise.id,

        ...validateExercise(
          exercise
        )
      }));
  }

  /* =========================================================
     DIAGNOSTICS
     ========================================================= */

  function diagnostics() {
    const exercises =
      getAllExercises();

    const validation =
      validateAll();

    return {
      version:
        VERSION,

      catalogReady:
        catalogReady(),

      exerciseCount:
        exercises.length,

      invalidExercises:
        validation.filter(
          result =>
            !result.valid
        ),

      progress:
        getProgress()
    };
  }

  /* =========================================================
     PUBLIC API
     ========================================================= */

  window.LearningHubExercises = {
    version:
      VERSION,

    get:
      getExercise,

    getAll:
      getAllExercises,

    getByLanguage,

    getByChapter,

    getByLesson,

    getState,

    getCode,

    saveCode,

    reset:
      resetExercise,

    getNextHint,

    evaluate,

    isCompleted,

    getProgress,

    validate:
      validateExercise,

    validateAll,

    diagnostics
  };

  /* =========================================================
     READY
     ========================================================= */

  if (!catalogReady()) {
    console.error(
      "[Learning Hub] Exercise Catalog chưa sẵn sàng. Kiểm tra thứ tự extra_javascript trong mkdocs.yml."
    );
  }

  window.dispatchEvent(
    new CustomEvent(
      "learninghub:exercises-ready",
      {
        detail: {
          version:
            VERSION,

          count:
            getAllExercises().length
        }
      }
    )
  );
})();