/**
 * app.js - Main Application Logic & State Management
 * Python Interactive Trainer
 */

(function () {
  'use strict';

  // Application State
  const state = {
    topics: [],
    tasks: [],
    currentTopicId: null,
    currentTaskId: null,
    currentTask: null,
    taskFilterDifficulty: 'all',
    taskSearchQuery: '',
    progress: {
      total_tasks: 0,
      completed_tasks: 0,
      percentage: 0,
      completed_ids: [],
    },
    isRunning: false,
    isTesting: false,
    isBottomCollapsed: false,
    draftSaveTimeout: null,
  };

  // API Client
  const API = {
    async getTopics() {
      const res = await fetch('/api/topics');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    },

    async getTasks(topicId = null) {
      const url = topicId ? `/api/tasks?topic_id=${encodeURIComponent(topicId)}` : '/api/tasks';
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    },

    async getTask(taskId) {
      const res = await fetch(`/api/tasks/${encodeURIComponent(taskId)}`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    },

    async runCode(code) {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    },

    async testSolution(taskId, code) {
      const res = await fetch(`/api/test/${encodeURIComponent(taskId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    },

    async getProgress() {
      const res = await fetch('/api/progress');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    },

    async resetProgress() {
      const res = await fetch('/api/progress/reset', {
        method: 'POST',
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    },
  };

  // DOM Elements Cache
  const elements = {};

  function cacheDOMElements() {
    elements.topicSelect = document.getElementById('topic-select');
    elements.progressText = document.getElementById('progress-text');
    elements.progressFill = document.getElementById('progress-fill');
    elements.btnResetProgress = document.getElementById('btn-reset-progress');

    // Left Panel Tabs
    elements.tabBtnTheory = document.getElementById('tab-btn-theory');
    elements.tabBtnHint = document.getElementById('tab-btn-hint');
    elements.tabBtnTasks = document.getElementById('tab-btn-tasks');
    elements.paneTheory = document.getElementById('pane-theory');
    elements.paneHint = document.getElementById('pane-hint');
    elements.paneTasks = document.getElementById('pane-tasks');
    elements.badgeTasksCount = document.getElementById('badge-tasks-count');

    // Task View
    elements.taskTitle = document.getElementById('task-title');
    elements.taskTopicBadge = document.getElementById('task-topic-badge');
    elements.taskDifficultyBadge = document.getElementById('task-difficulty-badge');
    elements.taskStatusBadge = document.getElementById('task-status-badge');
    elements.theoryContent = document.getElementById('theory-content');
    elements.btnPrevTask = document.getElementById('btn-prev-task');
    elements.btnNextTask = document.getElementById('btn-next-task');
    elements.taskNavCounter = document.getElementById('task-nav-counter');

    // Hint View
    elements.hintActionBox = document.getElementById('hint-action-box');
    elements.btnRevealHint = document.getElementById('btn-reveal-hint');
    elements.hintRevealedBox = document.getElementById('hint-revealed-box');
    elements.hintTextContent = document.getElementById('hint-text-content');

    // Tasks List View
    elements.tasksSearch = document.getElementById('tasks-search');
    elements.difficultyFilters = document.getElementById('difficulty-filters');
    elements.tasksList = document.getElementById('tasks-list');

    // Toolbar & Editor
    elements.toolbarTaskId = document.getElementById('toolbar-task-id');
    elements.autosaveStatus = document.getElementById('autosave-status');
    elements.btnResetCode = document.getElementById('btn-reset-code');
    elements.btnCopyCode = document.getElementById('btn-copy-code');
    elements.btnRunCode = document.getElementById('btn-run-code');
    elements.btnSubmitCode = document.getElementById('btn-submit-code');

    // Bottom Panel
    elements.panelBottom = document.getElementById('panel-bottom');
    elements.tabBtnConsole = document.getElementById('tab-btn-console');
    elements.tabBtnTests = document.getElementById('tab-btn-tests');
    elements.paneConsole = document.getElementById('pane-console');
    elements.paneTests = document.getElementById('pane-tests');
    elements.consoleStatusBadge = document.getElementById('console-status-badge');
    elements.testsScoreBadge = document.getElementById('tests-score-badge');
    elements.executionTimeBadge = document.getElementById('execution-time-badge');
    elements.btnClearOutput = document.getElementById('btn-clear-output');
    elements.btnToggleBottom = document.getElementById('btn-toggle-bottom-panel');
    elements.terminalView = document.getElementById('terminal-view');
    elements.testResultsView = document.getElementById('test-results-view');

    // Resizers
    elements.panelLeft = document.getElementById('panel-left');
    elements.resizerHorizontal = document.getElementById('resizer-horizontal');
    elements.resizerVertical = document.getElementById('resizer-vertical');

    // Modals
    elements.modalCelebration = document.getElementById('modal-celebration');
    elements.celebrationTaskTitle = document.getElementById('celebration-task-title');
    elements.statTestsCount = document.getElementById('stat-tests-count');
    elements.btnCelebrationNext = document.getElementById('btn-celebration-next');
    elements.btnCelebrationStay = document.getElementById('btn-celebration-stay');

    elements.modalResetConfirm = document.getElementById('modal-reset-confirm');
    elements.btnConfirmReset = document.getElementById('btn-confirm-reset');
    elements.btnCancelReset = document.getElementById('btn-cancel-reset');

    elements.toastContainer = document.getElementById('toast-container');
  }

  // App Initialization
  async function init() {
    cacheDOMElements();
    setupSplitters();
    setupTabSwitchers();
    setupEventListeners();

    // Initialize code editor
    await window.CodeEditor.init('monaco-editor', 'code-fallback', '');

    // Setup editor callbacks
    window.CodeEditor.onRun(() => handleRunCode());
    window.CodeEditor.onSubmit(() => handleSubmitSolution());
    window.CodeEditor.onChange((newCode) => handleCodeChange(newCode));

    // Load initial data from server
    await loadInitialData();
  }

  /**
   * Load Topics, Tasks, and Progress
   */
  async function loadInitialData() {
    try {
      const [topics, tasks, progress] = await Promise.all([
        API.getTopics().catch(() => []),
        API.getTasks().catch(() => []),
        API.getProgress().catch(() => ({ total_tasks: 0, completed_tasks: 0, percentage: 0, completed_ids: [] })),
      ]);

      state.topics = topics || [];
      state.tasks = tasks || [];
      state.progress = progress || { total_tasks: 0, completed_tasks: 0, percentage: 0, completed_ids: [] };

      renderTopicSelector();
      renderProgressBar();
      renderTasksList();

      // Determine task to load
      let targetTaskId = null;
      const savedTaskId = localStorage.getItem('pytrainer_last_task');
      if (savedTaskId && state.tasks.some((t) => t.id === savedTaskId)) {
        targetTaskId = savedTaskId;
      } else if (state.tasks.length > 0) {
        targetTaskId = state.tasks[0].id;
      }

      if (targetTaskId) {
        await loadTask(targetTaskId);
      } else {
        renderEmptyState();
      }
    } catch (err) {
      console.error('Error loading initial data:', err);
      showToast('Ошибка загрузки данных с сервера', 'error');
    }
  }

  /**
   * Render topic dropdown options
   */
  function renderTopicSelector() {
    if (!elements.topicSelect) return;
    elements.topicSelect.innerHTML = '';

    const allOpt = document.createElement('option');
    allOpt.value = '';
    allOpt.textContent = `Все темы (${state.tasks.length} задач)`;
    elements.topicSelect.appendChild(allOpt);

    state.topics.forEach((topic) => {
      const opt = document.createElement('option');
      opt.value = topic.id;
      opt.textContent = `${topic.title} (${topic.tasks_count || 0})`;
      elements.topicSelect.appendChild(opt);
    });

    if (state.currentTopicId) {
      elements.topicSelect.value = state.currentTopicId;
    }
  }

  /**
   * Update progress bar and text
   */
  function renderProgressBar() {
    const total = state.progress.total_tasks || state.tasks.length || 0;
    const completed = state.progress.completed_tasks || 0;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

    if (elements.progressText) {
      elements.progressText.textContent = `${completed} / ${total} (${pct}%)`;
    }
    if (elements.progressFill) {
      elements.progressFill.style.width = `${pct}%`;
    }
    if (elements.badgeTasksCount) {
      elements.badgeTasksCount.textContent = `${completed}/${total}`;
    }
  }

  /**
   * Render tasks tree in "Список задач" tab
   */
  function renderTasksList() {
    if (!elements.tasksList) return;

    let filtered = state.tasks.slice();

    // Filter by topic
    if (state.currentTopicId) {
      filtered = filtered.filter((t) => t.topic_id === state.currentTopicId);
    }

    // Filter by difficulty
    if (state.taskFilterDifficulty !== 'all') {
      filtered = filtered.filter((t) => t.difficulty === state.taskFilterDifficulty);
    }

    // Filter by search query
    if (state.taskSearchQuery.trim()) {
      const q = state.taskSearchQuery.trim().toLowerCase();
      filtered = filtered.filter(
        (t) => t.title.toLowerCase().includes(q) || t.id.toLowerCase().includes(q)
      );
    }

    if (filtered.length === 0) {
      elements.tasksList.innerHTML = `
        <div class="loading-state">
          <p class="text-muted">Задачи не найдены</p>
        </div>
      `;
      return;
    }

    // Group tasks by topic
    const grouped = {};
    filtered.forEach((task) => {
      const topicId = task.topic_id || 'other';
      if (!grouped[topicId]) {
        grouped[topicId] = [];
      }
      grouped[topicId].push(task);
    });

    let html = '';
    const completedSet = new Set(state.progress.completed_ids || []);

    Object.keys(grouped).forEach((topicId) => {
      const topicObj = state.topics.find((t) => t.id === topicId) || {
        title: topicId,
      };
      const topicTasks = grouped[topicId];
      const completedInGroup = topicTasks.filter((t) => completedSet.has(t.id) || t.completed).length;

      html += `
        <div class="topic-group" data-topic-id="${escapeHtml(topicId)}">
          <div class="topic-group-header">
            <div class="topic-group-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-sm topic-chevron">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
              <span>${escapeHtml(topicObj.title)}</span>
            </div>
            <span class="badge badge-pill">${completedInGroup}/${topicTasks.length}</span>
          </div>
          <div class="topic-group-tasks">
      `;

      topicTasks.forEach((task) => {
        const isCompleted = completedSet.has(task.id) || task.completed;
        const isActive = task.id === state.currentTaskId;
        const diffBadgeClass =
          task.difficulty === 'easy'
            ? 'badge-easy'
            : task.difficulty === 'hard'
            ? 'badge-hard'
            : 'badge-medium';
        const diffLabel =
          task.difficulty === 'easy'
            ? 'Легко'
            : task.difficulty === 'hard'
            ? 'Сложно'
            : 'Средне';

        html += `
          <div class="task-item-row ${isActive ? 'active' : ''}" data-task-id="${escapeHtml(task.id)}">
            <div class="task-item-left">
              ${
                isCompleted
                  ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="task-item-status-icon completed"><polyline points="20 6 9 17 4 12"/></svg>`
                  : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="task-item-status-icon uncompleted"><circle cx="12" cy="12" r="9"/></svg>`
              }
              <span class="task-item-name" title="${escapeHtml(task.title)}">${escapeHtml(task.title)}</span>
            </div>
            <span class="badge ${diffBadgeClass}">${diffLabel}</span>
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;
    });

    elements.tasksList.innerHTML = html;

    // Attach click handlers
    elements.tasksList.querySelectorAll('.topic-group-header').forEach((header) => {
      header.addEventListener('click', () => {
        const group = header.closest('.topic-group');
        group.classList.toggle('collapsed');
      });
    });

    elements.tasksList.querySelectorAll('.task-item-row').forEach((row) => {
      row.addEventListener('click', () => {
        const taskId = row.getAttribute('data-task-id');
        if (taskId && taskId !== state.currentTaskId) {
          loadTask(taskId);
          // Switch to theory tab on task select
          switchLeftTab('theory');
        }
      });
    });
  }

  /**
   * Load and render specific task by ID
   */
  async function loadTask(taskId) {
    if (!taskId) return;
    state.currentTaskId = taskId;
    localStorage.setItem('pytrainer_last_task', taskId);

    // Update active highlight in tasks list
    if (elements.tasksList) {
      elements.tasksList.querySelectorAll('.task-item-row').forEach((row) => {
        if (row.getAttribute('data-task-id') === taskId) {
          row.classList.add('active');
        } else {
          row.classList.remove('active');
        }
      });
    }

    try {
      const task = await API.getTask(taskId);
      state.currentTask = task;

      // Update Toolbar title & Topic
      const topicObj = state.topics.find((t) => t.id === task.topic_id);
      const topicTitle = topicObj ? topicObj.title : task.topic_id || 'Python';

      if (elements.taskTopicBadge) elements.taskTopicBadge.textContent = topicTitle;
      if (elements.taskTitle) elements.taskTitle.textContent = task.title;
      if (elements.toolbarTaskId) elements.toolbarTaskId.textContent = `${task.id}.py`;

      // Difficulty badge
      if (elements.taskDifficultyBadge) {
        elements.taskDifficultyBadge.className = 'badge badge-difficulty';
        if (task.difficulty === 'easy') {
          elements.taskDifficultyBadge.classList.add('badge-easy');
          elements.taskDifficultyBadge.textContent = 'Легкая';
        } else if (task.difficulty === 'hard') {
          elements.taskDifficultyBadge.classList.add('badge-hard');
          elements.taskDifficultyBadge.textContent = 'Сложная';
        } else {
          elements.taskDifficultyBadge.classList.add('badge-medium');
          elements.taskDifficultyBadge.textContent = 'Средняя';
        }
      }

      // Status badge
      const isCompleted =
        task.completed || (state.progress.completed_ids && state.progress.completed_ids.includes(task.id));
      if (elements.taskStatusBadge) {
        if (isCompleted) {
          elements.taskStatusBadge.className = 'badge badge-completed';
          elements.taskStatusBadge.textContent = '✓ Решена';
        } else {
          elements.taskStatusBadge.className = 'badge badge-uncompleted';
          elements.taskStatusBadge.textContent = 'Не решена';
        }
      }

      // Render Theory & Instructions
      renderTheoryContent(task);

      // Render Hint
      renderHintContent(task);

      // Update Navigation buttons
      updateTaskNavigation();

      // Determine initial code for editor:
      // 1. LocalStorage draft
      // 2. User solution from backend (if any)
      // 3. Starter code
      const draft = localStorage.getItem(`pytrainer_draft_${task.id}`);
      let codeToSet = '';
      if (draft !== null && draft !== undefined && draft.trim().length > 0) {
        codeToSet = draft;
      } else if (task.user_solution) {
        codeToSet = task.user_solution;
      } else {
        codeToSet = task.starter_code || '# Напишите ваше решение здесь\n';
      }

      window.CodeEditor.setCode(codeToSet);
      setAutosaveStatus('saved');

      // Clear any previous test results view
      resetOutputTabsPlaceholder();
    } catch (err) {
      console.error('Failed to load task:', err);
      showToast('Ошибка при загрузке задания', 'error');
    }
  }

  /**
   * Render Markdown for Theory & Instructions
   */
  function renderTheoryContent(task) {
    if (!elements.theoryContent) return;

    let contentHtml = '';

    // Theory section
    if (task.theory) {
      contentHtml += `
        <div class="theory-section">
          <h2>Теория</h2>
          <div class="markdown-text">${renderMarkdown(task.theory)}</div>
        </div>
      `;
    }

    // Instructions section
    if (task.instructions) {
      contentHtml += `
        <div class="instructions-section">
          <h2>Задание</h2>
          <div class="markdown-text">${renderMarkdown(task.instructions)}</div>
        </div>
      `;
    }

    elements.theoryContent.innerHTML = contentHtml;

    // Apply syntax highlighting to code blocks in theory
    if (window.hljs) {
      elements.theoryContent.querySelectorAll('pre code').forEach((block) => {
        window.hljs.highlightElement(block);
      });
    }
  }

  /**
   * Render Hint Tab
   */
  function renderHintContent(task) {
    // Reset hint state to collapsed
    if (elements.hintActionBox) elements.hintActionBox.classList.remove('hidden');
    if (elements.hintRevealedBox) elements.hintRevealedBox.classList.add('hidden');

    if (elements.hintTextContent) {
      if (task.hint && task.hint.trim()) {
        elements.hintTextContent.innerHTML = renderMarkdown(task.hint);
        if (window.hljs) {
          elements.hintTextContent.querySelectorAll('pre code').forEach((block) => {
            window.hljs.highlightElement(block);
          });
        }
      } else {
        elements.hintTextContent.innerHTML = '<p class="text-muted">Для этой задачи подсказок нет. Вы точно справитесь самостоятельно!</p>';
      }
    }
  }

  /**
   * Update Next / Prev buttons in theory pane
   */
  function updateTaskNavigation() {
    const list = state.tasks;
    const currentIndex = list.findIndex((t) => t.id === state.currentTaskId);

    if (elements.taskNavCounter) {
      if (currentIndex >= 0) {
        elements.taskNavCounter.textContent = `${currentIndex + 1} из ${list.length}`;
      } else {
        elements.taskNavCounter.textContent = `0 из ${list.length}`;
      }
    }

    if (elements.btnPrevTask) {
      elements.btnPrevTask.disabled = currentIndex <= 0;
    }
    if (elements.btnNextTask) {
      elements.btnNextTask.disabled = currentIndex === -1 || currentIndex >= list.length - 1;
    }
  }

  /**
   * Handle Code Change (Autosave to localStorage)
   */
  function handleCodeChange(code) {
    if (!state.currentTaskId) return;

    setAutosaveStatus('unsaved');

    clearTimeout(state.draftSaveTimeout);
    state.draftSaveTimeout = setTimeout(() => {
      try {
        localStorage.setItem(`pytrainer_draft_${state.currentTaskId}`, code);
        setAutosaveStatus('saved');
      } catch (e) {
        console.warn('LocalStorage save error:', e);
      }
    }, 600);
  }

  function setAutosaveStatus(status) {
    if (!elements.autosaveStatus) return;
    if (status === 'saved') {
      elements.autosaveStatus.classList.remove('unsaved');
      const label = elements.autosaveStatus.querySelector('.status-label');
      if (label) label.textContent = 'Сохранено';
    } else {
      elements.autosaveStatus.classList.add('unsaved');
      const label = elements.autosaveStatus.querySelector('.status-label');
      if (label) label.textContent = 'Сохранение...';
    }
  }

  /**
   * Handle Run Code (Quick Execution)
   */
  async function handleRunCode() {
    if (state.isRunning) return;
    const code = window.CodeEditor.getCode();

    state.isRunning = true;
    updateRunButtonsState(true);

    // Switch to console tab and ensure panel is open
    switchBottomTab('console');
    expandBottomPanel();

    if (elements.terminalView) {
      elements.terminalView.innerHTML = `
        <div class="loading-state" style="padding: 20px 0;">
          <div class="spinner"></div>
          <span>Выполнение кода в песочнице...</span>
        </div>
      `;
    }

    const startTime = performance.now();

    try {
      const result = await API.runCode(code);
      const elapsed = Math.round(result.execution_time_ms || (performance.now() - startTime));

      if (elements.executionTimeBadge) {
        elements.executionTimeBadge.textContent = `${elapsed} мс`;
        elements.executionTimeBadge.classList.remove('hidden');
      }

      if (elements.consoleStatusBadge) {
        elements.consoleStatusBadge.classList.remove('hidden');
        if (result.exit_code === 0 && !result.stderr) {
          elements.consoleStatusBadge.className = 'status-indicator-badge';
          elements.consoleStatusBadge.textContent = 'OK';
        } else {
          elements.consoleStatusBadge.className = 'status-indicator-badge';
          elements.consoleStatusBadge.style.background = 'var(--danger-bg)';
          elements.consoleStatusBadge.style.color = 'var(--danger)';
          elements.consoleStatusBadge.style.borderColor = 'var(--danger-border)';
          elements.consoleStatusBadge.textContent = `Exit ${result.exit_code || 1}`;
        }
      }

      renderTerminalOutput(result);
    } catch (err) {
      console.error('Run error:', err);
      if (elements.terminalView) {
        elements.terminalView.innerHTML = `
          <div class="term-stderr">Ошибка при обращении к серверу выполнения: ${escapeHtml(err.message)}</div>
        `;
      }
    } finally {
      state.isRunning = false;
      updateRunButtonsState(false);
    }
  }

  /**
   * Render Terminal Output from Run API
   */
  function renderTerminalOutput(result) {
    if (!elements.terminalView) return;

    let outputHtml = '';

    if (result.stdout && result.stdout.length > 0) {
      outputHtml += `<div class="term-stdout">${escapeHtml(result.stdout)}</div>`;
    }

    if (result.stderr && result.stderr.length > 0) {
      outputHtml += `<div class="term-stderr">${escapeHtml(result.stderr)}</div>`;
    }

    if (!result.stdout && !result.stderr) {
      outputHtml += `<div class="text-muted">Программа выполнилась без вывода в консоль.</div>`;
    }

    outputHtml += `
      <div class="term-meta">Код завершения: ${result.exit_code !== undefined ? result.exit_code : 0} | Время: ${result.execution_time_ms || 0} мс</div>
    `;

    elements.terminalView.innerHTML = outputHtml;
  }

  /**
   * Handle Submit Solution (Automated Tests)
   */
  async function handleSubmitSolution() {
    if (state.isTesting || !state.currentTaskId) return;
    const code = window.CodeEditor.getCode();

    state.isTesting = true;
    updateRunButtonsState(true);

    // Switch to tests tab and ensure panel is open
    switchBottomTab('tests');
    expandBottomPanel();

    if (elements.testResultsView) {
      elements.testResultsView.innerHTML = `
        <div class="loading-state" style="padding: 30px 0;">
          <div class="spinner"></div>
          <span>Запуск автоматических тестов проверки решения...</span>
        </div>
      `;
    }

    try {
      const result = await API.testSolution(state.currentTaskId, code);
      renderTestResults(result);

      if (result.passed) {
        // Solution Passed!
        handleTaskCompletion(result);
      }
    } catch (err) {
      console.error('Test error:', err);
      if (elements.testResultsView) {
        elements.testResultsView.innerHTML = `
          <div class="test-card-message">Ошибка при проверке тестов: ${escapeHtml(err.message)}</div>
        `;
      }
    } finally {
      state.isTesting = false;
      updateRunButtonsState(false);
    }
  }

  /**
   * Render Test Results list
   */
  function renderTestResults(result) {
    if (!elements.testResultsView) return;

    const total = result.total_tests || 0;
    const passed = result.passed_tests || 0;
    const isSuccess = result.passed;

    // Update Score Badge in bottom tab
    if (elements.testsScoreBadge) {
      elements.testsScoreBadge.classList.remove('hidden');
      elements.testsScoreBadge.textContent = `${passed}/${total}`;
      elements.testsScoreBadge.style.background = isSuccess ? 'var(--success)' : 'var(--danger)';
    }

    let html = `
      <div class="tests-summary-card ${isSuccess ? 'passed' : 'failed'}">
        <div style="display:flex; align-items:center; gap:8px;">
          ${
            isSuccess
              ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="icon"><polyline points="20 6 9 17 4 12"/></svg>`
              : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`
          }
          <strong>${isSuccess ? 'Все тесты пройдены!' : 'Решение не прошло все тесты'}</strong>
        </div>
        <div>
          <span>Пройдено тестов: <strong>${passed} из ${total}</strong> (${result.score || 0}%)</span>
        </div>
      </div>
    `;

    // Render output if any
    if (result.stderr && result.stderr.trim()) {
      html += `
        <div class="test-card-message" style="margin-bottom: 12px;">
          <strong>Ошибка выполнения теста:</strong>
          <pre style="margin-top:4px;">${escapeHtml(result.stderr)}</pre>
        </div>
      `;
    }

    // Render each test case card
    if (result.test_results && result.test_results.length > 0) {
      html += `<div class="test-cards-list">`;
      result.test_results.forEach((test, idx) => {
        const testName = test.test_name || `Тест #${idx + 1}`;
        const testPassed = test.passed;

        html += `
          <div class="test-card">
            <div class="test-card-header">
              <div class="test-card-title">
                ${
                  testPassed
                    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="icon-sm text-success"><polyline points="20 6 9 17 4 12"/></svg>`
                    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-sm text-danger"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`
                }
                <span>${escapeHtml(testName)}</span>
              </div>
              <span class="badge ${testPassed ? 'badge-easy' : 'badge-hard'}">
                ${testPassed ? 'Пройден' : 'Ошибка'}
              </span>
            </div>
            <div class="test-card-body">
              ${
                test.expected !== undefined
                  ? `
                <div class="test-io-row">
                  <span class="test-io-label">Ожидалось:</span>
                  <span class="test-io-val match">${escapeHtml(formatTestVal(test.expected))}</span>
                </div>
              `
                  : ''
              }
              ${
                test.actual !== undefined
                  ? `
                <div class="test-io-row">
                  <span class="test-io-label">Получено:</span>
                  <span class="test-io-val ${testPassed ? 'match' : 'mismatch'}">${escapeHtml(formatTestVal(test.actual))}</span>
                </div>
              `
                  : ''
              }
              ${
                test.message
                  ? `
                <div class="test-card-message">${escapeHtml(test.message)}</div>
              `
                  : ''
              }
            </div>
          </div>
        `;
      });
      html += `</div>`;
    }

    elements.testResultsView.innerHTML = html;
  }

  function formatTestVal(val) {
    if (val === null || val === undefined) return '';
    if (typeof val === 'object') {
      try {
        return JSON.stringify(val);
      } catch (e) {
        return String(val);
      }
    }
    return String(val);
  }

  /**
   * Action when task is successfully solved
   */
  async function handleTaskCompletion(result) {
    // Fire Confetti!
    triggerConfetti();

    // Update local state progress
    if (!state.progress.completed_ids) state.progress.completed_ids = [];
    if (!state.progress.completed_ids.includes(state.currentTaskId)) {
      state.progress.completed_ids.push(state.currentTaskId);
      state.progress.completed_tasks = state.progress.completed_ids.length;
    }

    // Update task status badge
    if (elements.taskStatusBadge) {
      elements.taskStatusBadge.className = 'badge badge-completed';
      elements.taskStatusBadge.textContent = '✓ Решена';
    }

    // Refresh progress bar and sidebar
    renderProgressBar();
    renderTasksList();

    // Show celebration modal
    showCelebrationModal(result);
  }

  /**
   * Confetti Celebration Effect
   */
  function triggerConfetti() {
    if (typeof window.confetti === 'function') {
      window.confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#10b981', '#38bdf8', '#818cf8', '#fbbf24'],
      });
      setTimeout(() => {
        window.confetti({
          particleCount: 50,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
        });
        window.confetti({
          particleCount: 50,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
        });
      }, 250);
    }
  }

  /**
   * Show celebration modal
   */
  function showCelebrationModal(result) {
    if (!elements.modalCelebration) return;

    if (elements.celebrationTaskTitle && state.currentTask) {
      elements.celebrationTaskTitle.textContent = `Задача «${state.currentTask.title}» успешно зачтена!`;
    }

    if (elements.statTestsCount) {
      elements.statTestsCount.textContent = `${result.passed_tests || 0} / ${result.total_tests || 0}`;
    }

    // Disable next button if on last task
    const currentIndex = state.tasks.findIndex((t) => t.id === state.currentTaskId);
    const hasNext = currentIndex >= 0 && currentIndex < state.tasks.length - 1;
    if (elements.btnCelebrationNext) {
      elements.btnCelebrationNext.style.display = hasNext ? 'inline-flex' : 'none';
    }

    elements.modalCelebration.classList.remove('hidden');
  }

  function hideCelebrationModal() {
    if (elements.modalCelebration) {
      elements.modalCelebration.classList.add('hidden');
    }
  }

  /**
   * Setup Tab Switchers
   */
  function setupTabSwitchers() {
    // Left panel tabs
    if (elements.tabBtnTheory) {
      elements.tabBtnTheory.addEventListener('click', () => switchLeftTab('theory'));
    }
    if (elements.tabBtnHint) {
      elements.tabBtnHint.addEventListener('click', () => switchLeftTab('hint'));
    }
    if (elements.tabBtnTasks) {
      elements.tabBtnTasks.addEventListener('click', () => switchLeftTab('tasks'));
    }

    // Bottom panel tabs
    if (elements.tabBtnConsole) {
      elements.tabBtnConsole.addEventListener('click', () => switchBottomTab('console'));
    }
    if (elements.tabBtnTests) {
      elements.tabBtnTests.addEventListener('click', () => switchBottomTab('tests'));
    }
  }

  function switchLeftTab(tabName) {
    [elements.tabBtnTheory, elements.tabBtnHint, elements.tabBtnTasks].forEach((btn) => {
      if (btn) btn.classList.remove('active');
    });
    [elements.paneTheory, elements.paneHint, elements.paneTasks].forEach((pane) => {
      if (pane) pane.classList.remove('active');
    });

    if (tabName === 'theory') {
      if (elements.tabBtnTheory) elements.tabBtnTheory.classList.add('active');
      if (elements.paneTheory) elements.paneTheory.classList.add('active');
    } else if (tabName === 'hint') {
      if (elements.tabBtnHint) elements.tabBtnHint.classList.add('active');
      if (elements.paneHint) elements.paneHint.classList.add('active');
    } else if (tabName === 'tasks') {
      if (elements.tabBtnTasks) elements.tabBtnTasks.classList.add('active');
      if (elements.paneTasks) elements.paneTasks.classList.add('active');
    }
  }

  function switchBottomTab(tabName) {
    if (elements.tabBtnConsole) elements.tabBtnConsole.classList.remove('active');
    if (elements.tabBtnTests) elements.tabBtnTests.classList.remove('active');
    if (elements.paneConsole) elements.paneConsole.classList.remove('active');
    if (elements.paneTests) elements.paneTests.classList.remove('active');

    if (tabName === 'console') {
      if (elements.tabBtnConsole) elements.tabBtnConsole.classList.add('active');
      if (elements.paneConsole) elements.paneConsole.classList.add('active');
    } else if (tabName === 'tests') {
      if (elements.tabBtnTests) elements.tabBtnTests.classList.add('active');
      if (elements.paneTests) elements.paneTests.classList.add('active');
    }
  }

  function expandBottomPanel() {
    if (elements.panelBottom) {
      elements.panelBottom.classList.remove('collapsed');
      state.isBottomCollapsed = false;
      window.CodeEditor.layout();
    }
  }

  function toggleBottomPanel() {
    if (!elements.panelBottom) return;
    elements.panelBottom.classList.toggle('collapsed');
    state.isBottomCollapsed = elements.panelBottom.classList.contains('collapsed');
    window.CodeEditor.layout();
  }

  /**
   * Setup Event Listeners
   */
  function setupEventListeners() {
    // Topic select
    if (elements.topicSelect) {
      elements.topicSelect.addEventListener('change', (e) => {
        state.currentTopicId = e.target.value || null;
        renderTasksList();
      });
    }

    // Search tasks
    if (elements.tasksSearch) {
      elements.tasksSearch.addEventListener('input', (e) => {
        state.taskSearchQuery = e.target.value;
        renderTasksList();
      });
    }

    // Difficulty filter pills
    if (elements.difficultyFilters) {
      elements.difficultyFilters.querySelectorAll('.filter-pill').forEach((btn) => {
        btn.addEventListener('click', () => {
          elements.difficultyFilters.querySelectorAll('.filter-pill').forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
          state.taskFilterDifficulty = btn.getAttribute('data-filter') || 'all';
          renderTasksList();
        });
      });
    }

    // Reveal Hint Button
    if (elements.btnRevealHint) {
      elements.btnRevealHint.addEventListener('click', () => {
        if (elements.hintActionBox) elements.hintActionBox.classList.add('hidden');
        if (elements.hintRevealedBox) elements.hintRevealedBox.classList.remove('hidden');
      });
    }

    // Reset Code Button
    if (elements.btnResetCode) {
      elements.btnResetCode.addEventListener('click', () => {
        if (!state.currentTask) return;
        const confirmReset = window.confirm('Сбросить код решения к начальному шаблону?');
        if (confirmReset) {
          localStorage.removeItem(`pytrainer_draft_${state.currentTask.id}`);
          window.CodeEditor.setCode(state.currentTask.starter_code || '# Напишите ваше решение здесь\n');
          setAutosaveStatus('saved');
          showToast('Код сброшен к начальному состоянию', 'info');
        }
      });
    }

    // Copy Code Button
    if (elements.btnCopyCode) {
      elements.btnCopyCode.addEventListener('click', async () => {
        const code = window.CodeEditor.getCode();
        try {
          await navigator.clipboard.writeText(code);
          showToast('Код скопирован в буфер обмена', 'success');
        } catch (e) {
          showToast('Не удалось скопировать код', 'error');
        }
      });
    }

    // Run & Submit Buttons
    if (elements.btnRunCode) {
      elements.btnRunCode.addEventListener('click', () => handleRunCode());
    }
    if (elements.btnSubmitCode) {
      elements.btnSubmitCode.addEventListener('click', () => handleSubmitSolution());
    }

    // Clear Output Button
    if (elements.btnClearOutput) {
      elements.btnClearOutput.addEventListener('click', () => {
        resetOutputTabsPlaceholder();
      });
    }

    // Toggle Bottom Panel
    if (elements.btnToggleBottom) {
      elements.btnToggleBottom.addEventListener('click', () => toggleBottomPanel());
    }

    // Prev / Next Task Buttons
    if (elements.btnPrevTask) {
      elements.btnPrevTask.addEventListener('click', () => navigateTask(-1));
    }
    if (elements.btnNextTask) {
      elements.btnNextTask.addEventListener('click', () => navigateTask(1));
    }

    // Celebration Modal Buttons
    if (elements.btnCelebrationStay) {
      elements.btnCelebrationStay.addEventListener('click', () => hideCelebrationModal());
    }
    if (elements.btnCelebrationNext) {
      elements.btnCelebrationNext.addEventListener('click', () => {
        hideCelebrationModal();
        navigateTask(1);
      });
    }

    // Reset Progress Modal
    if (elements.btnResetProgress) {
      elements.btnResetProgress.addEventListener('click', () => {
        if (elements.modalResetConfirm) elements.modalResetConfirm.classList.remove('hidden');
      });
    }
    if (elements.btnCancelReset) {
      elements.btnCancelReset.addEventListener('click', () => {
        if (elements.modalResetConfirm) elements.modalResetConfirm.classList.add('hidden');
      });
    }
    if (elements.btnConfirmReset) {
      elements.btnConfirmReset.addEventListener('click', async () => {
        if (elements.modalResetConfirm) elements.modalResetConfirm.classList.add('hidden');
        await handleResetAllProgress();
      });
    }

    // Close modals on Esc
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        hideCelebrationModal();
        if (elements.modalResetConfirm) elements.modalResetConfirm.classList.add('hidden');
      }
    });
  }

  /**
   * Reset All Progress
   */
  async function handleResetAllProgress() {
    try {
      await API.resetProgress();

      // Clear local drafts
      Object.keys(localStorage).forEach((key) => {
        if (key.startsWith('pytrainer_draft_') || key === 'pytrainer_last_task') {
          localStorage.removeItem(key);
        }
      });

      state.progress = {
        total_tasks: state.tasks.length,
        completed_tasks: 0,
        percentage: 0,
        completed_ids: [],
      };

      renderProgressBar();
      renderTasksList();

      if (state.currentTaskId) {
        await loadTask(state.currentTaskId);
      }

      showToast('Весь прогресс успешно сброшен', 'success');
    } catch (err) {
      console.error('Reset error:', err);
      showToast('Не удалось сбросить прогресс', 'error');
    }
  }

  /**
   * Navigate to next/prev task
   */
  function navigateTask(direction) {
    const list = state.tasks;
    const currentIndex = list.findIndex((t) => t.id === state.currentTaskId);
    const newIndex = currentIndex + direction;

    if (newIndex >= 0 && newIndex < list.length) {
      loadTask(list[newIndex].id);
      switchLeftTab('theory');
    }
  }

  /**
   * Update button states when executing/testing
   */
  function updateRunButtonsState(isLoading) {
    if (elements.btnRunCode) elements.btnRunCode.disabled = isLoading;
    if (elements.btnSubmitCode) elements.btnSubmitCode.disabled = isLoading;
  }

  /**
   * Reset placeholders in console and tests
   */
  function resetOutputTabsPlaceholder() {
    if (elements.terminalView) {
      elements.terminalView.innerHTML = `
        <div class="terminal-placeholder">
          <p>Нажмите <kbd>Ctrl+Enter</kbd> или кнопку <strong>«Запустить»</strong> для выполнения кода.</p>
          <p class="text-muted">Вывод функций <code>print()</code> и ошибки выполнения отобразятся здесь.</p>
        </div>
      `;
    }
    if (elements.testResultsView) {
      elements.testResultsView.innerHTML = `
        <div class="terminal-placeholder">
          <p>Нажмите <kbd>Ctrl+Shift+Enter</kbd> или кнопку <strong>«Проверить решение»</strong>.</p>
          <p class="text-muted">Система запустит автоматические тесты и покажет результаты проверки.</p>
        </div>
      `;
    }
    if (elements.executionTimeBadge) elements.executionTimeBadge.classList.add('hidden');
    if (elements.consoleStatusBadge) elements.consoleStatusBadge.classList.add('hidden');
    if (elements.testsScoreBadge) elements.testsScoreBadge.classList.add('hidden');
  }

  function renderEmptyState() {
    if (elements.theoryContent) {
      elements.theoryContent.innerHTML = `
        <div class="loading-state">
          <p>Нет доступных задач. Пожалуйста, добавьте задачи в каталог content/tasks.</p>
        </div>
      `;
    }
  }

  /**
   * Setup Draggable Splitters
   */
  function setupSplitters() {
    const resizerH = elements.resizerHorizontal;
    const panelL = elements.panelLeft;
    const resizerV = elements.resizerVertical;
    const panelB = elements.panelBottom;

    // Restore saved panel sizes from localStorage
    const savedLeftWidth = localStorage.getItem('pytrainer_panel_left_width');
    if (savedLeftWidth && panelL) {
      panelL.style.width = savedLeftWidth;
    }

    const savedBottomHeight = localStorage.getItem('pytrainer_panel_bottom_height');
    if (savedBottomHeight && panelB) {
      panelB.style.height = savedBottomHeight;
    }

    // Horizontal Splitter (Left vs Right)
    if (resizerH && panelL) {
      let isDragging = false;

      resizerH.addEventListener('mousedown', (e) => {
        isDragging = true;
        resizerH.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
      });

      window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const containerWidth = document.querySelector('.ide-container').clientWidth;
        const newWidth = Math.max(280, Math.min(e.clientX, containerWidth - 360));
        const pct = ((newWidth / containerWidth) * 100).toFixed(1) + '%';
        panelL.style.width = pct;
        window.CodeEditor.layout();
      });

      window.addEventListener('mouseup', () => {
        if (isDragging) {
          isDragging = false;
          resizerH.classList.remove('dragging');
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          localStorage.setItem('pytrainer_panel_left_width', panelL.style.width);
          window.CodeEditor.layout();
        }
      });
    }

    // Vertical Splitter (Editor vs Bottom Panel)
    if (resizerV && panelB) {
      let isDragging = false;

      resizerV.addEventListener('mousedown', (e) => {
        isDragging = true;
        resizerV.classList.add('dragging');
        document.body.style.cursor = 'row-resize';
        document.body.style.userSelect = 'none';
      });

      window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const containerHeight = document.querySelector('.ide-container').clientHeight;
        const rightPanelTop = document.querySelector('.panel-right').getBoundingClientRect().top;
        const newHeight = containerHeight - (e.clientY - rightPanelTop);
        const clampedHeight = Math.max(40, Math.min(newHeight, containerHeight - 120));
        panelB.style.height = `${clampedHeight}px`;
        window.CodeEditor.layout();
      });

      window.addEventListener('mouseup', () => {
        if (isDragging) {
          isDragging = false;
          resizerV.classList.remove('dragging');
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          localStorage.setItem('pytrainer_panel_bottom_height', panelB.style.height);
          window.CodeEditor.layout();
        }
      });
    }
  }

  /**
   * Toast notification helper
   */
  function showToast(message, type = 'info') {
    if (!elements.toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let iconSvg = '';
    if (type === 'success') {
      iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="icon-sm text-success"><polyline points="20 6 9 17 4 12"/></svg>`;
    } else if (type === 'error') {
      iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-sm text-danger"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
    } else {
      iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-sm text-accent"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    }

    toast.innerHTML = `${iconSvg}<span>${escapeHtml(message)}</span>`;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 250);
    }, 3200);
  }

  /**
   * Markdown rendering with fallback
   */
  function renderMarkdown(md) {
    if (!md) return '';
    if (window.marked && typeof window.marked.parse === 'function') {
      try {
        return window.marked.parse(md);
      } catch (e) {
        console.warn('Marked parse error:', e);
      }
    }

    // Minimal markdown fallback parser
    return escapeHtml(md)
      .replace(/```python([\s\S]*?)```/g, '<pre><code class="language-python">$1</code></pre>')
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>');
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Initialize application on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
