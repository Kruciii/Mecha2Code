const API_URL = "http://9.160.9.128";
let accessToken = localStorage.getItem("mechacode_access_token");
let courses = [];
let tasks = [];
let taskProgress = new Map();
let selectedCourse = null;
let selectedTask = null;
let editor = null;

const templates = {
  54: `#include <iostream>
using namespace std;

int main() {
    // Napisz swoje rozwiązanie w C++
    return 0;
}`,
  71: `# Napisz swoje rozwiązanie w Pythonie
def main():
    pass

if __name__ == "__main__":
    main()`,
  62: `import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        // Napisz swoje rozwiązanie w Javie
    }
}`
};
const defaultCode = templates[54];
const getSelectedLanguageId = () => Number($("#language")?.value || 54);
const getLanguageMode = (id) => ({ 54: "cpp", 71: "python", 62: "java" }[id] || "cpp");
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
}[character]));
const parseMarkdownFallback = (text) => {
  if (!text) return "";
  let out = escapeHtml(text).replace(/\r\n/g, "\n");

  const codeBlocks = [];
  out = out.replace(/```(?:[a-zA-Z0-9_-]+)?\n([\s\S]*?)```/g, (_, code) => {
    const idx = codeBlocks.length;
    codeBlocks.push(`<pre><code>${code.trim()}</code></pre>`);
    return `%%%CODE_BLOCK_${idx}%%%`;
  });

  out = out.replace(/`([^`\n]+)`/g, "<code>$1</code>");
  out = out.replace(/^### (.*$)/gim, "\n<h3>$1</h3>\n");
  out = out.replace(/^## (.*$)/gim, "\n<h2>$1</h2>\n");
  out = out.replace(/^# (.*$)/gim, "\n<h1>$1</h1>\n");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>");
  out = out.replace(/^\s*\d+\.\s+(.*$)/gim, "<li>$1</li>");
  out = out.replace(/^\s*[-*]\s+(.*$)/gim, "<li>$1</li>");
  out = out.replace(/((?:<li>.*?<\/li>\s*)+)/gims, "\n<ul>$1</ul>\n");

  const blocks = out.split(/\n\s*\n/).map((chunk) => {
    const trimmed = chunk.trim();
    if (!trimmed) return "";
    if (trimmed.startsWith("<h") || trimmed.startsWith("<ul") || trimmed.startsWith("<ol") || trimmed.startsWith("%%%CODE_BLOCK_")) {
      return trimmed;
    }
    return `<p>${trimmed.replace(/\n/g, "<br>")}</p>`;
  }).filter(Boolean);

  let result = blocks.join("\n");
  codeBlocks.forEach((block, idx) => {
    result = result.replace(`%%%CODE_BLOCK_${idx}%%%`, block);
  });
  return result;
};

const renderMarkdown = (text) => {
  if (!text) return "";

  // 1. Chroń bloki kodu i kod inline przed parsowaniem LaTeX i Markdown
  const codeVault = [];
  let protectedText = String(text).replace(/(```[\s\S]*?```|`[^`\n]+`)/g, (match) => {
    const placeholder = `%%%CODE_VAULT_${codeVault.length}%%%`;
    codeVault.push(match);
    return placeholder;
  });

  // 2. Wyodrębnij wzory blokowe $$ ... $$
  const mathVault = [];
  protectedText = protectedText.replace(/\$\$([\s\S]+?)\$\$/g, (_, math) => {
    const placeholder = `%%%MATH_BLOCK_${mathVault.length}%%%`;
    mathVault.push({ math: math.trim(), display: true });
    return placeholder;
  });

  // 3. Wyodrębnij wzory inline $ ... $
  protectedText = protectedText.replace(/(?<!\\)\$([^\$\n]+?)(?<!\\)\$/g, (_, math) => {
    if (!math.trim()) return `$${math}$`;
    const placeholder = `%%%MATH_INLINE_${mathVault.length}%%%`;
    mathVault.push({ math: math.trim(), display: false });
    return placeholder;
  });

  // 4. Przywróć kod przed parsowaniem markdownu
  codeVault.forEach((code, idx) => {
    protectedText = protectedText.replace(`%%%CODE_VAULT_${idx}%%%`, code);
  });

  // 5. Sparsuj Markdown
  let html = "";
  try {
    const markedLib = window.marked;
    if (markedLib) {
      if (typeof markedLib.parse === "function") html = markedLib.parse(protectedText);
      else if (typeof markedLib === "function") html = markedLib(protectedText);
      else if (markedLib.marked && typeof markedLib.marked.parse === "function") html = markedLib.marked.parse(protectedText);
      else html = parseMarkdownFallback(protectedText);
    } else {
      html = parseMarkdownFallback(protectedText);
    }
  } catch (err) {
    console.warn("Marked.js error, using fallback:", err);
    html = parseMarkdownFallback(protectedText);
  }

  // 6. Renderuj wzory KaTeX
  const katexLib = window.katex || (typeof katex !== "undefined" ? katex : null);
  mathVault.forEach((item, idx) => {
    const targetPlaceholder = item.display ? `%%%MATH_BLOCK_${idx}%%%` : `%%%MATH_INLINE_${idx}%%%`;
    let renderedMath = "";
    if (katexLib && typeof katexLib.renderToString === "function") {
      try {
        renderedMath = katexLib.renderToString(item.math, {
          displayMode: item.display,
          throwOnError: false,
        });
      } catch (mathErr) {
        console.warn("KaTeX render error:", mathErr);
        renderedMath = `<span class="katex-fallback">${escapeHtml(item.math)}</span>`;
      }
    } else {
      renderedMath = `<span class="katex-fallback">${escapeHtml(item.math)}</span>`;
    }
    html = html.replace(targetPlaceholder, renderedMath);
  });

  return html;
};
const showAlert = (message, type = "success") => {
  const alert = $("#alert");
  alert.textContent = message;
  alert.className = `alert alert-${type}`;
  window.setTimeout(() => alert.classList.add("d-none"), 4500);
};
const request = async (path, options = {}) => {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch (err) {
    throw new Error(`Błąd sieci: nie można połączyć się z API (${err.message})`);
  }
  if (!response.ok) {
    let detail = `Błąd API (${response.status} ${response.statusText})`;
    try {
      const data = await response.json();
      if (data && data.detail) detail = data.detail;
    } catch (_) {
      try {
        const text = await response.text();
        if (text) detail = `${detail}: ${text.slice(0, 100)}`;
      } catch (_) {}
    }
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
  const rawTags = (task.tags || "łatwe").trim();
  $("#task-difficulty").textContent = rawTags.toUpperCase();
  let diffClass = "easy";
  const lowerTags = rawTags.toLowerCase();
  if (lowerTags.includes("trudn") || lowerTags.includes("hard")) {
    diffClass = "hard";
  } else if (lowerTags.includes("średn") || lowerTags.includes("sredn") || lowerTags.includes("medium")) {
    diffClass = "medium";
  }
  $("#task-difficulty").className = `difficulty ${diffClass}`;
  $("#task-description").innerHTML = renderMarkdown(task.description);
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

  // Wykryj język kursu z backendu
  const langMode = (course.language || (course.language_id === 71 || (course.title || "").toLowerCase().includes("python") ? "python" : "cpp")).toLowerCase();
  const langId = course.language_id || (langMode === "python" ? 71 : (langMode === "java" ? 62 : 54));

  // Zaktualizuj backing select i badge języka
  const langSelect = $("#language");
  if (langSelect) langSelect.value = String(langId);

  const langBadge = $("#current-language-badge");
  if (langBadge) {
    langBadge.textContent = langMode.toUpperCase();
    langBadge.className = `lang-badge lang-${langMode}`;
  }

  // Ustaw język i szablon w Monaco Editor
  if (editor) {
    const model = editor.getModel();
    if (model) {
      monaco.editor.setModelLanguage(model, langMode);
    }
    editor.setValue(templates[langId] || defaultCode);
  }

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
const setupLanguageIntelliSense = () => {
  // 1. Python IntelliSense & Type hints
  monaco.languages.registerCompletionItemProvider("python", {
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position);
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      };

      const suggestions = [
        // Typy wbudowane
        { label: "int", kind: monaco.languages.CompletionItemKind.Class, insertText: "int", detail: "class int(x=0)", documentation: "Typ liczby całkowitej o nieograniczonej precyzji.", range },
        { label: "float", kind: monaco.languages.CompletionItemKind.Class, insertText: "float", detail: "class float(x=0.0)", documentation: "Liczba zmiennoprzecinkowa podwójnej precyzji.", range },
        { label: "complex", kind: monaco.languages.CompletionItemKind.Class, insertText: "complex(${1:real}, ${2:imag})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "class complex(real=0, imag=0)", documentation: "Typ liczby zespolonej (np. 1 + 2j).", range },
        { label: "str", kind: monaco.languages.CompletionItemKind.Class, insertText: "str", detail: "class str(object='')", documentation: "Niemutowalny łańcuch znaków Unicode.", range },
        { label: "list", kind: monaco.languages.CompletionItemKind.Class, insertText: "list", detail: "class list[T]", documentation: "Wbudowana lista dynamiczna.", range },
        { label: "dict", kind: monaco.languages.CompletionItemKind.Class, insertText: "dict", detail: "class dict[K, V]", documentation: "Słownik par klucz-wartość (tablica asocjacyjna).", range },
        { label: "set", kind: monaco.languages.CompletionItemKind.Class, insertText: "set", detail: "class set[T]", documentation: "Zbiór unikalnych elementów.", range },
        { label: "tuple", kind: monaco.languages.CompletionItemKind.Class, insertText: "tuple", detail: "class tuple[T, ...]", documentation: "Niemutowalna krotka elementów.", range },
        { label: "bool", kind: monaco.languages.CompletionItemKind.Class, insertText: "bool", detail: "class bool(x=False)", documentation: "Wartość logiczna (True / False).", range },

        // Funkcje wbudowane
        { label: "print", kind: monaco.languages.CompletionItemKind.Function, insertText: "print(${1:value})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "print(*values, sep=' ', end='\\n')", documentation: "Wypisuje wartości do strumienia wyjściowego stdout.", range },
        { label: "input", kind: monaco.languages.CompletionItemKind.Function, insertText: "input(${1})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "input(prompt='') -> str", documentation: "Wczytuje linię ze standardowego wejścia stdin.", range },
        { label: "len", kind: monaco.languages.CompletionItemKind.Function, insertText: "len(${1:obj})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "len(obj) -> int", documentation: "Zwraca liczbę elementów w kolekcji.", range },
        { label: "range", kind: monaco.languages.CompletionItemKind.Function, insertText: "range(${1:stop})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "range(start=0, stop, step=1)", documentation: "Generuje sekwencję liczb całkowitych.", range },
        { label: "enumerate", kind: monaco.languages.CompletionItemKind.Function, insertText: "enumerate(${1:iterable})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "enumerate(iterable, start=0)", documentation: "Zwraca iterator par (indeks, element).", range },
        { label: "zip", kind: monaco.languages.CompletionItemKind.Function, insertText: "zip(${1:iter1}, ${2:iter2})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "zip(*iterables)", documentation: "Łączy odpowiadające sobie elementy z wielu kolekcji.", range },
        { label: "sorted", kind: monaco.languages.CompletionItemKind.Function, insertText: "sorted(${1:iterable})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "sorted(iterable, key=None, reverse=False)", documentation: "Zwraca nową posortowaną listę.", range },
        { label: "isinstance", kind: monaco.languages.CompletionItemKind.Function, insertText: "isinstance(${1:obj}, ${2:classinfo})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "isinstance(obj, classinfo) -> bool", documentation: "Sprawdza, czy obiekt jest instancją podanej klasy.", range },
        { label: "map", kind: monaco.languages.CompletionItemKind.Function, insertText: "map(${1:func}, ${2:iterable})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "map(func, *iterables)", documentation: "Stosuje funkcję do każdego elementu kolekcji.", range },
        { label: "sum", kind: monaco.languages.CompletionItemKind.Function, insertText: "sum(${1:iterable})", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "sum(iterable, start=0)", documentation: "Zwraca sumę elementów w kolekcji liczb.", range },

        // Snippety
        { label: "def", kind: monaco.languages.CompletionItemKind.Snippet, insertText: "def ${1:func_name}(${2:args}):\n    ${3:pass}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "Snippet: definicja funkcji", range },
        { label: "for", kind: monaco.languages.CompletionItemKind.Snippet, insertText: "for ${1:item} in ${2:iterable}:\n    ${3:pass}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "Snippet: pętla for", range },
        { label: "fori", kind: monaco.languages.CompletionItemKind.Snippet, insertText: "for ${1:i} in range(${2:n}):\n    ${3:pass}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "Snippet: pętla for i in range(n)", range },
        { label: "ifmain", kind: monaco.languages.CompletionItemKind.Snippet, insertText: 'if __name__ == "__main__":\n    ${1:main()}', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "Snippet: if __name__ == '__main__':", range },
        { label: "try", kind: monaco.languages.CompletionItemKind.Snippet, insertText: "try:\n    ${1:pass}\nexcept ${2:Exception} as ${3:e}:\n    ${4:pass}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "Snippet: blok try-except", range },
      ];
      return { suggestions };
    },
  });

  // Python Hover Docs
  monaco.languages.registerHoverProvider("python", {
    provideHover: (model, position) => {
      const word = model.getWordAtPosition(position);
      if (!word) return null;
      const docs = {
        int: "**class int(x=0)**\n\nWbudowany typ liczby całkowitej w Pythonie 3.",
        float: "**class float(x=0.0)**\n\nLiczba zmiennoprzecinkowa 64-bit IEEE 754.",
        complex: "**class complex(real=0, imag=0)**\n\nLiczba zespolona (`real + imag*j`). Posiada atrybuty `.real`, `.imag` oraz metodę `.conjugate()`.",
        str: "**class str(object='')**\n\nNiemutowalny ciąg znaków.",
        list: "**class list[T]**\n\nMutowalna lista dynamiczna (`.append()`, `.pop()`, `.sort()`).",
        dict: "**class dict[K, V]**\n\nSłownik klucz-wartość (`.keys()`, `.values()`, `.items()`).",
        set: "**class set[T]**\n\nZbiór unikalnych elementów (obsługuje `|`, `&`, `-`).",
        tuple: "**class tuple[T, ...]**\n\nNiemutowalna krotka.",
        print: "**print(*values, sep=' ', end='\\n')**\n\nWypisuje wartości do strumienia stdout.",
        input: "**input(prompt='') -> str**\n\nWczytuje linię tekstu ze standardowego wejścia stdin.",
        len: "**len(obj) -> int**\n\nZwraca liczbę elementów w obiekcie.",
        range: "**range(start=0, stop, step=1)**\n\nGeneruje sekwencję liczb.",
      };
      if (docs[word.word]) {
        return {
          range: new monaco.Range(position.lineNumber, word.startColumn, position.lineNumber, word.endColumn),
          contents: [{ value: docs[word.word] }],
        };
      }
      return null;
    },
  });

  // 2. C++ IntelliSense
  monaco.languages.registerCompletionItemProvider("cpp", {
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position);
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      };

      const suggestions = [
        { label: "cout", kind: monaco.languages.CompletionItemKind.Snippet, insertText: "cout << ${1:value} << endl;", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "std::cout << ... << endl;", range },
        { label: "cin", kind: monaco.languages.CompletionItemKind.Snippet, insertText: "cin >> ${1:var};", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "std::cin >> ...;", range },
        { label: "vector", kind: monaco.languages.CompletionItemKind.Class, insertText: "vector<${1:int}> ${2:v};", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "std::vector<T>", range },
        { label: "fori", kind: monaco.languages.CompletionItemKind.Snippet, insertText: "for (int ${1:i} = 0; ${1:i} < ${2:n}; ++${1:i}) {\n    ${3}\n}", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "for (int i = 0; i < n; ++i)", range },
        { label: "pair", kind: monaco.languages.CompletionItemKind.Class, insertText: "pair<${1:int}, ${2:int}>", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "std::pair<T1, T2>", range },
        { label: "map", kind: monaco.languages.CompletionItemKind.Class, insertText: "map<${1:string}, ${2:int}>", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "std::map<Key, Value>", range },
        { label: "sort", kind: monaco.languages.CompletionItemKind.Function, insertText: "sort(${1:v}.begin(), ${1:v}.end());", insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, detail: "std::sort(begin, end)", range },
      ];
      return { suggestions };
    },
  });
};

const createEditor = () => {
  window.MonacoEnvironment = {
    getWorkerUrl: function (workerId, label) {
      return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
        self.MonacoEnvironment = {
          baseUrl: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/'
        };
        importScripts('https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/base/worker/workerMain.js');
      `)}`;
    }
  };
  require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs" } });
  require(["vs/editor/editor.main"], () => {
    setupLanguageIntelliSense();

    const initialLangId = getSelectedLanguageId();
    const initialMode = getLanguageMode(initialLangId);

    editor = monaco.editor.create($("#source-code"), {
      value: templates[initialLangId] || defaultCode,
      language: initialMode,
      theme: "vs-dark",
      automaticLayout: true,
      minimap: { enabled: true },
      fontSize: 14,
      fontFamily: "'Fira Code', Consolas, Monaco, monospace",
      fontLigatures: true,
      scrollBeyondLastLine: false,
      tabSize: 4,
      wordWrap: "on",
      padding: { top: 14, bottom: 14 },
      // Opcje IDE / IntelliSense:
      quickSuggestions: { other: true, comments: false, strings: true },
      suggestOnTriggerCharacters: true,
      acceptSuggestionOnEnter: "on",
      tabCompletion: "on",
      parameterHints: { enabled: true },
      bracketPairColorization: { enabled: true },
      autoClosingBrackets: "always",
      autoClosingQuotes: "always",
      autoClosingOvertype: "always",
      matchBrackets: "always",
      renderLineHighlight: "all",
      cursorBlinking: "smooth",
      cursorSmoothCaretAnimation: "on",
      smoothScrolling: true,
      folding: true,
    });

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, submit);
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Space, () => {
      editor.trigger("", "editor.action.triggerSuggest", {});
    });

    // Synchronize if selectedCourse was loaded before Monaco finished loading
    if (selectedCourse) {
      const langMode = (selectedCourse.language || (selectedCourse.language_id === 71 || (selectedCourse.title || "").toLowerCase().includes("python") ? "python" : "cpp")).toLowerCase();
      const langId = selectedCourse.language_id || (langMode === "python" ? 71 : 54);
      monaco.editor.setModelLanguage(editor.getModel(), langMode);
      editor.setValue(templates[langId] || defaultCode);
      const langBadge = $("#current-language-badge");
      if (langBadge) {
        langBadge.textContent = langMode.toUpperCase();
        langBadge.className = `lang-badge lang-${langMode}`;
      }
    }
  });
};
const login = async (email, password) => {
  const body = new URLSearchParams({ username: email, password });
  let response;
  try {
    response = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
  } catch (err) {
    throw new Error(`Błąd połączenia z serwerem API (${err.message})`);
  }
  if (!response.ok) {
    let detail = `Błąd serwera (${response.status} ${response.statusText})`;
    try {
      const data = await response.json();
      if (data && data.detail) detail = data.detail;
    } catch (_) {
      try {
        const text = await response.text();
        if (text) detail = `${detail}: ${text.slice(0, 100)}`;
      } catch (_) {}
    }
    throw new Error(detail);
  }
  const data = await response.json();
  accessToken = data.access_token;
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

$("#show-register-btn")?.addEventListener("click", (e) => {
  e.preventDefault();
  $("#login-section")?.classList.add("d-none");
  $("#register-section")?.classList.remove("d-none");
  $("#login-error")?.classList.add("d-none");
  const success = $("#login-success");
  if (success) success.classList.add("d-none");
});

$("#show-login-btn")?.addEventListener("click", (e) => {
  e.preventDefault();
  $("#register-section")?.classList.add("d-none");
  $("#login-section")?.classList.remove("d-none");
  $("#login-error")?.classList.add("d-none");
  const success = $("#login-success");
  if (success) success.classList.add("d-none");
});

$("#register-page-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = $("#login-error");
  const success = $("#login-success");
  if (error) error.classList.add("d-none");
  if (success) success.classList.add("d-none");

  const email = $("#register-page-email").value.trim();
  const password = $("#register-page-password").value;
  const semester = Number($("#register-page-semester").value);
  const start_year = Number($("#register-page-start-year").value);
  const major = $("#register-page-major").value;
  const registration_secret = $("#register-page-secret").value.trim();

  try {
    const response = await fetch(`${API_URL}/users/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        semester,
        start_year,
        major,
        registration_secret,
      }),
    });

    if (!response.ok) {
      let detail = `Błąd rejestracji (${response.status})`;
      try {
        const data = await response.json();
        if (data && data.detail) {
          if (Array.isArray(data.detail)) {
            detail = data.detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
          } else {
            detail = data.detail;
          }
        }
      } catch (_) {}
      throw new Error(detail);
    }

    if (success) {
      success.textContent = "Konto zostało pomyślnie utworzone! Logowanie...";
      success.classList.remove("d-none");
    }

    // Automatyczne logowanie po rejestracji
    await login(email, password);
    if (success) success.classList.add("d-none");
    setAuthenticatedView(true);
    updateUserLabel();
    await loadCatalog();
  } catch (err) {
    if (error) {
      error.textContent = err.message;
      error.classList.remove("d-none");
    }
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
$("#reset-code").addEventListener("click", () => {
  if (editor) {
    const langId = getSelectedLanguageId();
    editor.setValue(templates[langId] || defaultCode);
  }
});
$("#language").addEventListener("change", () => {
  if (!editor) return;
  const langId = getSelectedLanguageId();
  const mode = getLanguageMode(langId);
  const model = editor.getModel();
  if (model) {
    monaco.editor.setModelLanguage(model, mode);
  }
  const currentVal = editor.getValue().trim();
  const isTemplate = Object.values(templates).some((tpl) => tpl.trim() === currentVal) || !currentVal;
  if (isTemplate) {
    editor.setValue(templates[langId] || "");
  }
});
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
