const API_URL = "http://9.160.9.128";
let accessToken = localStorage.getItem("mechacode_access_token");
let courses = [];
let tasks = [];
let taskProgress = new Map();
let selectedCourse = null;
let selectedTask = null;
let editor = null;

const defaultCode = `#include <iostream>
using namespace std;

int main() {
    // Napisz swoje rozwiązanie tutaj
    return 0;
}`;
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
}[character]));
const showAlert = (message, type = "success") => {
  const alert = $("#alert");
  alert.textContent = message;
  alert.className = `alert alert-${type}`;
  window.setTimeout(() => alert.classList.add("d-none"), 4500);
};
const request = async (path, options = {}) => {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let detail = `Błąd API (${response.status})`;
    try { detail = (await response.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return response.json();
};
const setAuthenticatedView = (authenticated) => {
  $("#login-screen").classList.toggle("d-none", authenticated);
  $("#app-view").classList.toggle("d-none", !authenticated);
};
const updateUserLabel = () => {
  if (!accessToken) {
    $("#user-label").textContent = "";
    return;
  }
  try {
    const payload = JSON.parse(atob(accessToken.split(".")[1]));
    $("#user-label").textContent = payload.email || "Użytkownik";
  } catch (_) {
    $("#user-label").textContent = "Użytkownik";
  }
};
const renderSubmissionResult = (submission) => {
  const pending = [1, 2].includes(submission.status_id);
  const status = $("#result-status");
  status.className = `result-status ${pending ? "pending" : submission.status_id === 3 ? "accepted" : "failed"}`;
  status.textContent = pending ? "Sprawdzanie..." : submission.status_id === 3 ? "Accepted" : "Niepoprawne";
  $("#result-summary").textContent = pending
    ? `Sprawdzono ${(submission.test_results || []).filter((test) => ![1, 2].includes(test.status_id)).length}/${submission.total_tests} testów`
    : `${submission.score ?? 0}% (${submission.passed_tests}/${submission.total_tests} testów)`;
  $("#test-results").innerHTML = (submission.test_results || []).map((test, index) => {
    const waiting = [1, 2].includes(test.status_id);
    const testClass = waiting ? "pending" : test.passed ? "passed" : "failed";
    return `<span class="test-dot ${testClass}" title="Test ${index + 1}">${test.passed ? "✓" : waiting ? "…" : "×"}</span>`;
  }).join("");
};
const resetSubmissionResult = () => {
  $("#result-status").className = "result-status error";
  $("#result-status").textContent = "Brak zgłoszenia";
  $("#result-summary").textContent = "Wyślij rozwiązanie, aby zobaczyć wynik.";
  $("#test-results").innerHTML = "";
};
const progressStatus = (progress) => {
  if (!progress) return { className: "not-started", label: "○", title: "Nie rozpoczęto" };
  if ([1, 2].includes(progress.status_id)) return {
    className: "pending", label: `${progress.passed_tests}/${progress.total_tests}`,
    title: `Sprawdzanie: ${progress.passed_tests}/${progress.total_tests} testów`,
  };
  if (progress.status_id === 3) return {
    className: "accepted", label: "✓",
    title: `Poprawnie: ${progress.passed_tests}/${progress.total_tests} testów`,
  };
  return {
    className: "failed", label: `${progress.passed_tests}/${progress.total_tests}`,
    title: `Niepoprawne: ${progress.passed_tests}/${progress.total_tests} testów`,
  };
};
const renderTaskProgress = () => {
  document.querySelectorAll(".task-item").forEach((item) => {
    const indicator = item.querySelector(".task-status");
    const status = progressStatus(taskProgress.get(Number(item.dataset.id)));
    indicator.className = `task-status ${status.className}`;
    indicator.textContent = status.label;
    indicator.title = status.title;
  });
};
const allCourseTasks = (course) => course.modules.flatMap((module) => module.tasks);
const selectTask = async (task) => {
  selectedTask = task;
  $("#course-overview").classList.add("d-none");
  $(".split-view").classList.add("visible");
  $("#task-title").textContent = task.title;
  $("#task-description").innerHTML = `<p>${escapeHtml(task.description)}</p>`;
  $("#task-example").textContent = "Wejście: dane testowe\nWyjście: oczekiwany wynik";
  document.querySelectorAll(".task-item").forEach((item) => item.classList.toggle("active", Number(item.dataset.id) === task.id));
  const progress = taskProgress.get(task.id);
  if (progress?.submission_id) {
    try { renderSubmissionResult(await request(`/submissions/${progress.submission_id}`)); }
    catch (_) { resetSubmissionResult(); }
  } else resetSubmissionResult();
};
const renderCourseTasks = (course) => {
  const modules = course.modules.map((module) => `
    <div class="module-group">
      <div class="module-title">${escapeHtml(module.title)}</div>
      ${module.tasks.map((task) => {
        const status = progressStatus(taskProgress.get(task.id));
        return `<div class="task-item" data-id="${task.id}">
          <span class="task-number">${module.tasks.indexOf(task) + 1}</span>
          <span>${escapeHtml(task.title)}</span>
          <span class="task-status ${status.className}" title="${status.title}">${status.label}</span>
        </div>`;
      }).join("")}
    </div>`).join("");
  $("#course-list").innerHTML = modules || '<div class="loading">Ten kurs nie ma jeszcze zadań.</div>';
  document.querySelectorAll(".task-item").forEach((item) => item.addEventListener("click", () => {
    selectTask(allCourseTasks(course).find((task) => task.id === Number(item.dataset.id)));
  }));
};
const selectCourse = (course) => {
  selectedCourse = course;
  $("#course-overview").classList.add("d-none");
  $(".split-view").classList.add("visible");
  renderCourseTasks(course);
  const firstTask = allCourseTasks(course)[0];
  if (firstTask) selectTask(firstTask);
};
const renderCourses = () => {
  $("#course-count").textContent = courses.length;
  $("#course-list").innerHTML = courses.map((course) => `
    <button class="course-nav-item" data-course-id="${course.id}">
      <span class="course-nav-icon">⌘</span><span>${escapeHtml(course.title)}</span>
    </button>`).join("");
  document.querySelectorAll(".course-nav-item").forEach((item) => item.addEventListener("click", () => {
    selectCourse(courses.find((course) => course.id === Number(item.dataset.courseId)));
  }));
  $("#course-cards").innerHTML = courses.map((course) => {
    const courseTasks = allCourseTasks(course);
    const solved = courseTasks.filter((task) => taskProgress.get(task.id)?.status_id === 3).length;
    return `<button class="course-card" data-course-id="${course.id}">
      <span class="course-icon">⌘</span>
      <span class="course-card-content"><strong>${escapeHtml(course.title)}</strong>
      <small>${escapeHtml(course.description || "Praktyczny kurs programowania")}</small>
      <span class="course-progress">${solved}/${courseTasks.length} zadań ukończonych</span></span>
      <span class="course-arrow">→</span>
    </button>`;
  }).join("");
  document.querySelectorAll(".course-card").forEach((card) => card.addEventListener("click", () => {
    selectCourse(courses.find((course) => course.id === Number(card.dataset.courseId)));
  }));
  if (selectedCourse) renderCourseTasks(selectedCourse);
};
const loadProgress = async () => {
  if (!accessToken) return;
  const progress = await request("/tasks/progress/");
  taskProgress = new Map(progress.map((item) => [item.task_id, item]));
};
const loadCatalog = async () => {
  courses = await request("/courses/catalog/");
  tasks = courses.flatMap(allCourseTasks);
  await loadProgress();
  renderCourses();
  if (selectedCourse) renderCourseTasks(selectedCourse);
};
const submit = async () => {
  if (!selectedTask) return showAlert("Najpierw wybierz zadanie.", "warning");
  try {
    if (!editor) return showAlert("Edytor kodu jeszcze się ładuje.", "warning");
    const submission = await request("/submissions/", {
      method: "POST",
      body: JSON.stringify({ task_id: selectedTask.id, language_id: Number($("#language").value), source_code: editor.getValue() }),
    });
    taskProgress.set(selectedTask.id, submission);
    renderTaskProgress();
    renderSubmissionResult(submission);
    showAlert("Rozwiązanie jest sprawdzane...");
    pollSubmission(submission.id);
  } catch (error) { showAlert(error.message, "danger"); }
};
const pollSubmission = async (submissionId, attempt = 0) => {
  if (attempt >= 30) return showAlert("Sprawdzanie trwa zbyt długo. Sprawdź historię później.", "warning");
  try {
    const submission = await request(`/submissions/${submissionId}`);
    renderSubmissionResult(submission);
    taskProgress.set(submission.task_id, submission);
    renderTaskProgress();
    renderCourses();
    if ([1, 2].includes(submission.status_id)) {
      window.setTimeout(() => pollSubmission(submissionId, attempt + 1), 1500);
      return;
    }
    const message = `${submission.score}% (${submission.passed_tests}/${submission.total_tests} testów)`;
    showAlert(submission.status_id === 3 ? `Accepted: ${message}` : `Niepoprawne rozwiązanie: ${message}`, submission.status_id === 3 ? "success" : "danger");
  } catch (error) { showAlert(`Nie udało się pobrać wyniku: ${error.message}`, "danger"); }
};
const createEditor = () => {
  require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs" } });
  require(["vs/editor/editor.main"], () => {
    editor = monaco.editor.create($("#source-code"), {
      value: defaultCode, language: "cpp", theme: "vs-dark", automaticLayout: true,
      minimap: { enabled: true }, fontSize: 14, fontFamily: "Consolas, Monaco, monospace",
      scrollBeyondLastLine: false, tabSize: 4, wordWrap: "on", padding: { top: 14, bottom: 14 },
    });
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, submit);
  });
};
const login = async (email, password) => {
  const body = new URLSearchParams({ username: email, password });
  const response = await fetch(`${API_URL}/login`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
  if (!response.ok) throw new Error((await response.json()).detail || "Logowanie nie powiodło się.");
  accessToken = (await response.json()).access_token;
  localStorage.setItem("mechacode_access_token", accessToken);
};
$("#login-page-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = $("#login-error");
  try {
    await login($("#login-page-email").value, $("#login-page-password").value);
    error.classList.add("d-none");
    setAuthenticatedView(true);
    updateUserLabel();
    await loadCatalog();
  } catch (exception) {
    error.textContent = exception.message;
    error.classList.remove("d-none");
  }
});
$("#logout-button").addEventListener("click", () => {
  accessToken = null;
  localStorage.removeItem("mechacode_access_token");
  updateUserLabel();
  setAuthenticatedView(false);
});
$("#back-to-courses").addEventListener("click", () => {
  $(".split-view").classList.remove("visible");
  $("#course-overview").classList.remove("d-none");
  selectedCourse = null;
  selectedTask = null;
  renderCourses();
});
$("#submit-button").addEventListener("click", submit);
$("#reset-code").addEventListener("click", () => { if (editor) editor.setValue(defaultCode); });
$("#theme-button").addEventListener("click", () => {
  document.body.classList.toggle("light-editor");
  if (editor) monaco.editor.setTheme(document.body.classList.contains("light-editor") ? "vs" : "vs-dark");
});
createEditor();
if (accessToken) {
  updateUserLabel();
  setAuthenticatedView(true);
  loadCatalog().catch(() => { accessToken = null; localStorage.removeItem("mechacode_access_token"); setAuthenticatedView(false); });
} else setAuthenticatedView(false);
