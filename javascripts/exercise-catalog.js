(() => {
  "use strict";

  /*
   * Learning Hub V4.6A
   * Exercise Content Catalog
   *
   * File này chỉ quản lý DATA.
   * Không render UI.
   * Không chạy Python.
   * Không chấm bài.
   */

  const exercises = new Map();

  function validateBasic(exercise) {
    if (!exercise || typeof exercise !== "object") {
      throw new Error("Exercise phải là object.");
    }

    if (!exercise.id) {
      throw new Error("Exercise thiếu id.");
    }

    if (!exercise.language) {
      throw new Error(
        `Exercise "${exercise.id}" thiếu language.`
      );
    }

    if (!exercise.title) {
      throw new Error(
        `Exercise "${exercise.id}" thiếu title.`
      );
    }

    if (typeof exercise.starterCode !== "string") {
      throw new Error(
        `Exercise "${exercise.id}" thiếu starterCode.`
      );
    }

    if (
      !Array.isArray(exercise.tests) ||
      exercise.tests.length === 0
    ) {
      throw new Error(
        `Exercise "${exercise.id}" chưa có tests.`
      );
    }
  }

  function register(exercise) {
    validateBasic(exercise);

    if (exercises.has(exercise.id)) {
      throw new Error(
        `Exercise ID bị trùng: ${exercise.id}`
      );
    }

    exercises.set(
      exercise.id,
      Object.freeze({
        ...exercise
      })
    );

    return exercise.id;
  }

  function registerMany(items) {
    if (!Array.isArray(items)) {
      throw new Error(
        "registerMany() cần một array."
      );
    }

    items.forEach(register);
  }

  function get(id) {
    return exercises.get(id) || null;
  }

  function getAll() {
    return Array.from(
      exercises.values()
    );
  }

  function has(id) {
    return exercises.has(id);
  }

  function count() {
    return exercises.size;
  }

  function getByLanguage(language) {
    return getAll().filter(
      exercise =>
        exercise.language === language
    );
  }

  function getByLesson(lessonId) {
    return getAll().filter(
      exercise =>
        exercise.lessonId === lessonId
    );
  }

  function getByChapter(chapter) {
    return getAll().filter(
      exercise =>
        exercise.chapter === chapter
    );
  }

  function getStats() {
    const all = getAll();

    const languages = {};

    all.forEach(exercise => {
      const language =
        exercise.language || "unknown";

      languages[language] =
        (languages[language] || 0) + 1;
    });

    return {
      total: all.length,
      languages
    };
  }

  window.LearningHubExerciseCatalog = {
    register,
    registerMany,
    get,
    getAll,
    has,
    count,
    getByLanguage,
    getByLesson,
    getByChapter,
    getStats
  };

  window.dispatchEvent(
    new CustomEvent(
      "learninghub:exercise-catalog-ready"
    )
  );
})();