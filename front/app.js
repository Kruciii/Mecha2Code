const API_URL = "http://9.160.9.128"; //lokalnie http://localhost:8000
let accessToken = localStorage.getItem("mechacode_access_token");
let tasks = [];
let taskProgress = new Map();
let selectedTask = null;
let editor = null;
const defaultCode = `#include <iostream>
using namespace std;

int main() {
    // Napisz swoje rozwiązanie tutaj
    return 0;
}`;
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;" }[character]));
const showAlert = (message, type = "success") => {
  const alert = $("#alert"); alert.textContent = message; alert.className = `alert alert-${type}`;
  window.setTimeout(() => alert.classList.add("d-none"), 4500);
};
const renderSubmissionResult = (submission) => {
  const status = $("#result-status");
  const summary = $("#result-summary");
  const tests = $("#test-results");
  const pending = [1, 2].includes(submission.status_id);
  status.className = `result-status ${pending ? "pending" : submission.status_id === 3 ? "accepted" : "failed"}`;
  status.textContent = pending ? "Sprawdzanie..." : submission.status_id === 3 ? "Accepted" : "Niepoprawne";
  summary.textContent = pending
    ? `Sprawdzono ${submission.test_results?.filter((test) => ![1, 2].includes(test.status_id)).length || 0}/${submission.total_tests} testów`
    : `${submission.score ?? 0}% (${submission.passed_tests}/${submission.total_tests} testów)`;
  tests.innerHTML = (submission.test_results || []).map((test, index) => {
    const testClass = [1, 2].includes(test.status_id) ? "pending" : test.passed ? "passed" : "failed";
    return `<span class="test-dot ${testClass}" title="Test ${index + 1}">${test.passed ? "✓" : [1, 2].includes(test.status_id) ? "…" : "×"}</span>`;
  }).join("");
};
const resetSubmissionResult = () => {
  $("#result-status").className = "result-status error";
  $("#result-status").textContent = "Brak zgłoszenia";
  $("#result-summary").textContent = "Wyślij rozwiązanie, aby zobaczyć wynik.";
  $("#test-results").innerHTML = "";
};
const taskStatus = (progress) => {
  if (!progress) return { className: "not-started", label: "○", title: "Nie rozpoczęto" };
  if ([1, 2].includes(progress.status_id)) {
    return {
      className: "pending",
      label: `${progress.passed_tests}/${progress.total_tests}`,
      title: `Sprawdzanie: ${progress.passed_tests}/${progress.total_tests} testów`,
    };
  }
  if (progress.status_id === 3) {
    return {
      className: "accepted",
      label: "✓",
      title: `Poprawnie: ${progress.passed_tests}/${progress.total_tests} testów`,
    };
  }
  return {
    className: "failed",
    label: `${progress.passed_tests}/${progress.total_tests}`,
    title: `Niepoprawne: ${progress.passed_tests}/${progress.total_tests} testów`,
  };
};
const renderTaskProgress = () => {
  document.querySelectorAll(".task-item").forEach((item) => {
    const progress = taskProgress.get(Number(item.dataset.id));
    const indicator = item.querySelector(".task-status");
    if (!indicator) return;
    const status = taskStatus(progress);
    indicator.className = `task-status ${status.className}`;
    indicator.textContent = status.label;
    indicator.title = status.title;
  });
};
const request = async (path, options = {}) => {
  const headers = { "Content-Type":"application/json", ...(options.headers || {}) };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) { let detail = `Błąd API (${response.status})`; try { detail = (await response.json()).detail || detail; } catch (_) {} throw new Error(detail); }
  return response.json();
};
const languageFromValue = () => ({ "54":"cpp", "71":"python", "62":"java" })[$("#language").value] || "cpp";
const createEditor = () => {
  require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs" } });
  require(["vs/editor/editor.main"], () => {
    editor = monaco.editor.create($("#source-code"), {
      value: defaultCode,
      language: languageFromValue(),
      theme: "vs-dark",
      automaticLayout: true,
      minimap: { enabled: true },
      fontSize: 14,
      fontFamily: "Consolas, Monaco, monospace",
      scrollBeyondLastLine: false,
      tabSize: 4,
      wordWrap: "on",
      padding: { top: 14, bottom: 14 },
    });
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, submit);
  });
};
const selectTask = (task) => {
  selectedTask = task; $("#task-title").textContent = task.title; $("#task-description").innerHTML = `<p>${escapeHtml(task.description)}</p>`;
  $("#task-example").textContent = "Wejście: dane testowe\nWyjście: oczekiwany wynik";
  const progress = taskProgress.get(task.id);
  if (progress?.submission_id) {
    request(`/submissions/${progress.submission_id}`)
      .then(renderSubmissionResult)
      .catch(() => resetSubmissionResult());
  } else {
    resetSubmissionResult();
  }
  document.querySelectorAll(".task-item").forEach((item) => item.classList.toggle("active", Number(item.dataset.id) === task.id));
};
const renderTasks = () => {
  $("#task-count").textContent = tasks.length;
  $("#task-list").innerHTML = tasks.length ? tasks.map((task, index) => {
    const status = taskStatus(taskProgress.get(task.id));
    return `<div class="task-item ${index === 0 ? "active" : ""}" data-id="${task.id}"><span class="task-number">${index + 1}</span><span>${escapeHtml(task.title)}</span><span class="task-status ${status.className}" title="${status.title}">${status.label}</span></div>`;
  }).join("") : '<div class="loading">Brak zadań w bazie.</div>';
  document.querySelectorAll(".task-item").forEach((item) => item.addEventListener("click", () => selectTask(tasks.find((task) => task.id === Number(item.dataset.id)))));
  if (tasks[0]) selectTask(tasks[0]);
};
const loadProgress = async () => {
  if (!accessToken) return;
  try {
    const progress = await request("/tasks/progress/");
    taskProgress = new Map(progress.map((item) => [item.task_id, item]));
    renderTasks();
    renderTaskProgress();
  } catch (error) {
    if (error.message.includes("401")) return;
    showAlert(`Nie udało się pobrać postępu: ${error.message}`, "danger");
  }
};
const loadTasks = async () => {
  try {
    tasks = await request("/tasks/");
    renderTasks();
    await loadProgress();
  } catch (error) {
    $("#task-list").innerHTML = `<div class="loading">Nie można pobrać zadań.</div>`;
    showAlert(error.message, "danger");
  }
};
const submit = async () => {
  if (!selectedTask) return showAlert("Najpierw wybierz zadanie.", "warning");
  try {
    if (!editor) return showAlert("Edytor kodu jeszcze się ładuje.", "warning");
    const submission = await request("/submissions/", { method:"POST", body:JSON.stringify({ task_id:selectedTask.id, language_id:Number($("#language").value), source_code:editor.getValue() }) });
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
    if ([1, 2].includes(submission.status_id)) {
      window.setTimeout(() => pollSubmission(submissionId, attempt + 1), 1500);
      return;
    }
    const message = `${submission.score}% (${submission.passed_tests}/${submission.total_tests} testów)`;
    taskProgress.set(submission.task_id, submission);
    renderTaskProgress();
    showAlert(submission.status_id === 3 ? `Accepted: ${message}` : `Niepoprawne rozwiązanie: ${message}`, submission.status_id === 3 ? "success" : "danger");
  } catch (error) { showAlert(`Nie udało się pobrać wyniku: ${error.message}`, "danger"); }
};
$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = new URLSearchParams({ username:$("#login-email").value, password:$("#login-password").value });
  try {
    const response = await fetch(`${API_URL}/login`, { method:"POST", headers:{"Content-Type":"application/x-www-form-urlencoded"}, body });
    if (!response.ok) throw new Error((await response.json()).detail || "Logowanie nie powiodło się.");
    accessToken = (await response.json()).access_token;
    localStorage.setItem("mechacode_access_token", accessToken);
    $("#login-form").classList.add("d-none"); $("#logout-button").classList.remove("d-none");
    showAlert("Zalogowano.");
    await loadProgress();
  } catch (error) { showAlert(error.message, "danger"); }
});
$("#logout-button").addEventListener("click", () => {
  accessToken = null; localStorage.removeItem("mechacode_access_token");
  $("#login-form").classList.remove("d-none"); $("#logout-button").classList.add("d-none");
});
if (accessToken) { $("#login-form").classList.add("d-none"); $("#logout-button").classList.remove("d-none"); }
$("#submit-button").addEventListener("click", submit);
$("#refresh-button").addEventListener("click", loadTasks);
$("#reset-code").addEventListener("click", () => { if (editor) editor.setValue(defaultCode); });
$("#language").addEventListener("change", () => {
  if (editor) monaco.editor.setModelLanguage(editor.getModel(), languageFromValue());
});
$("#theme-button").addEventListener("click", () => {
  document.body.classList.toggle("light-editor");
  if (editor) monaco.editor.setTheme(document.body.classList.contains("light-editor") ? "vs" : "vs-dark");
});
createEditor();
loadTasks();
