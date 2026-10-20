const API_URL = "http://localhost:8000";
let accessToken = localStorage.getItem("mechacode_access_token");
let tasks = [];
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
  document.querySelectorAll(".task-item").forEach((item) => item.classList.toggle("active", Number(item.dataset.id) === task.id));
};
const renderTasks = () => {
  $("#task-count").textContent = tasks.length;
  $("#task-list").innerHTML = tasks.length ? tasks.map((task, index) => `<div class="task-item ${index === 0 ? "active" : ""}" data-id="${task.id}"><span class="task-number">${index + 1}</span><span>${escapeHtml(task.title)}</span><span class="task-status">○</span></div>`).join("") : '<div class="loading">Brak zadań w bazie.</div>';
  document.querySelectorAll(".task-item").forEach((item) => item.addEventListener("click", () => selectTask(tasks.find((task) => task.id === Number(item.dataset.id)))));
  if (tasks[0]) selectTask(tasks[0]);
};
const loadTasks = async () => { try { tasks = await request("/tasks/"); renderTasks(); } catch (error) { $("#task-list").innerHTML = `<div class="loading">Nie można pobrać zadań.</div>`; showAlert(error.message, "danger"); } };
const submit = async () => {
  if (!selectedTask) return showAlert("Najpierw wybierz zadanie.", "warning");
  try {
    if (!editor) return showAlert("Edytor kodu jeszcze się ładuje.", "warning");
    const submission = await request("/submissions/", { method:"POST", body:JSON.stringify({ task_id:selectedTask.id, language_id:Number($("#language").value), source_code:editor.getValue() }) });
    showAlert("Rozwiązanie jest sprawdzane...");
    pollSubmission(submission.id);
  } catch (error) { showAlert(error.message, "danger"); }
};
const pollSubmission = async (submissionId, attempt = 0) => {
  if (attempt >= 30) return showAlert("Sprawdzanie trwa zbyt długo. Sprawdź historię później.", "warning");
  try {
    const submission = await request(`/submissions/${submissionId}`);
    if ([1, 2].includes(submission.status_id)) {
      window.setTimeout(() => pollSubmission(submissionId, attempt + 1), 1500);
      return;
    }
    const message = `${submission.score}% (${submission.passed_tests}/${submission.total_tests} testów)`;
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
  } catch (error) { showAlert(error.message, "danger"); }
});
$("#logout-button").addEventListener("click", () => {
  accessToken = null; localStorage.removeItem("mechacode_access_token");
  $("#login-form").classList.remove("d-none"); $("#logout-button").classList.add("d-none");
});
if (accessToken) { $("#login-form").classList.add("d-none"); $("#logout-button").classList.remove("d-none"); }
$("#submit-button").addEventListener("click", submit);
$("#run-button").addEventListener("click", () => showAlert("Uruchamianie kodu będzie dostępne po podłączeniu Judge0.", "info"));
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
