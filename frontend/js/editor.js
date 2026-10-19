/**
 * editor.js - Monaco Editor wrapper with graceful fallback
 * Python Interactive Trainer
 */

(function (window) {
  'use strict';

  let monacoInstance = null;
  let monacoEditor = null;
  let fallbackTextarea = null;
  let isMonacoLoaded = false;
  let isInitialized = false;

  const runCallbacks = [];
  const submitCallbacks = [];
  const changeCallbacks = [];

  const CodeEditor = {
    /**
     * Initializes the Monaco Editor or activates the fallback textarea
     * @param {string} containerId - DOM ID of Monaco container
     * @param {string} fallbackId - DOM ID of textarea fallback
     * @param {string} initialCode - Initial code string
     * @returns {Promise<boolean>} Resolves to true when ready
     */
    init: function (containerId, fallbackId, initialCode) {
      const container = document.getElementById(containerId);
      fallbackTextarea = document.getElementById(fallbackId);
      const loadingOverlay = document.getElementById('editor-loading');

      initialCode = initialCode || '# Напишите ваш код на Python здесь\n';

      return new Promise((resolve) => {
        // Setup global hotkeys for Ctrl+Enter and Ctrl+Shift+Enter
        setupGlobalKeybindings();

        // Check if AMD loader (require) is available from CDN
        if (typeof window.require !== 'undefined') {
          try {
            window.require.config({
              paths: {
                vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs',
              },
            });

            // Set a timeout of 4.5 seconds to fallback gracefully if CDN hangs
            const loaderTimeout = setTimeout(() => {
              if (!isMonacoLoaded) {
                console.warn('[Editor] Monaco CDN load timed out, falling back to textarea.');
                activateFallback(initialCode);
                if (loadingOverlay) loadingOverlay.classList.add('hidden');
                resolve(false);
              }
            }, 4500);

            window.require(['vs/editor/editor.main'], function () {
              clearTimeout(loaderTimeout);
              monacoInstance = window.monaco;

              // Register custom dark theme matching the app aesthetic
              monacoInstance.editor.defineTheme('pytrainer-dark', {
                base: 'vs-dark',
                inherit: true,
                rules: [
                  { token: 'comment', foreground: '6272a4', fontStyle: 'italic' },
                  { token: 'keyword', foreground: 'ff79c6', fontStyle: 'bold' },
                  { token: 'string', foreground: 'f1fa8c' },
                  { token: 'number', foreground: 'bd93f9' },
                  { token: 'type', foreground: '8be9fd' },
                  { token: 'function', foreground: '50fa7b' },
                ],
                colors: {
                  'editor.background': '#131b2e',
                  'editor.foreground': '#f8fafc',
                  'editorCursor.foreground': '#38bdf8',
                  'editor.lineHighlightBackground': '#1b243b',
                  'editorLineNumber.foreground': '#4f5d73',
                  'editorLineNumber.activeForeground': '#38bdf8',
                  'editor.selectionBackground': '#2a3d66',
                  'editor.inactiveSelectionBackground': '#1f2d4a',
                },
              });

              monacoEditor = monacoInstance.editor.create(container, {
                value: initialCode,
                language: 'python',
                theme: 'pytrainer-dark',
                fontSize: 14,
                fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, 'Courier New', monospace",
                fontLigatures: true,
                lineHeight: 22,
                automaticLayout: true,
                tabSize: 4,
                insertSpaces: true,
                detectIndentation: false,
                wordWrap: 'on',
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                renderLineHighlight: 'all',
                cursorBlinking: 'smooth',
                cursorSmoothCaretAnimation: 'on',
                bracketPairColorization: { enabled: true },
                guides: {
                  bracketPairs: true,
                  indentation: true,
                },
                suggestOnTriggerCharacters: true,
                quickSuggestions: true,
                padding: { top: 12, bottom: 12 },
              });

              // Bind Monaco-level key shortcuts
              monacoEditor.addCommand(
                monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.Enter,
                function () {
                  CodeEditor.triggerRun();
                }
              );

              monacoEditor.addCommand(
                monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyMod.Shift | monacoInstance.KeyCode.Enter,
                function () {
                  CodeEditor.triggerSubmit();
                }
              );

              // Change listener
              monacoEditor.onDidChangeModelContent(() => {
                const code = monacoEditor.getValue();
                changeCallbacks.forEach((cb) => cb(code));
              });

              isMonacoLoaded = true;
              isInitialized = true;

              if (loadingOverlay) loadingOverlay.classList.add('hidden');
              resolve(true);
            });
          } catch (err) {
            console.error('[Editor] Error initializing Monaco:', err);
            activateFallback(initialCode);
            if (loadingOverlay) loadingOverlay.classList.add('hidden');
            resolve(false);
          }
        } else {
          // CDN loader script missing
          activateFallback(initialCode);
          if (loadingOverlay) loadingOverlay.classList.add('hidden');
          resolve(false);
        }
      });
    },

    /**
     * Returns current code in editor
     */
    getCode: function () {
      if (isMonacoLoaded && monacoEditor) {
        return monacoEditor.getValue();
      }
      if (fallbackTextarea) {
        return fallbackTextarea.value;
      }
      return '';
    },

    /**
     * Sets code in editor
     * @param {string} code
     */
    setCode: function (code) {
      code = code || '';
      if (isMonacoLoaded && monacoEditor) {
        monacoEditor.setValue(code);
      } else if (fallbackTextarea) {
        fallbackTextarea.value = code;
      }
    },

    /**
     * Focuses the active editor
     */
    focus: function () {
      if (isMonacoLoaded && monacoEditor) {
        monacoEditor.focus();
      } else if (fallbackTextarea) {
        fallbackTextarea.focus();
      }
    },

    /**
     * Recalculates layout dimensions
     */
    layout: function () {
      if (isMonacoLoaded && monacoEditor) {
        monacoEditor.layout();
      }
    },

    /**
     * Register Run handler
     */
    onRun: function (callback) {
      if (typeof callback === 'function') {
        runCallbacks.push(callback);
      }
    },

    /**
     * Register Submit handler
     */
    onSubmit: function (callback) {
      if (typeof callback === 'function') {
        submitCallbacks.push(callback);
      }
    },

    /**
     * Register content change handler
     */
    onChange: function (callback) {
      if (typeof callback === 'function') {
        changeCallbacks.push(callback);
      }
    },

    /**
     * Trigger Run handlers
     */
    triggerRun: function () {
      const code = CodeEditor.getCode();
      runCallbacks.forEach((cb) => cb(code));
    },

    /**
     * Trigger Submit handlers
     */
    triggerSubmit: function () {
      const code = CodeEditor.getCode();
      submitCallbacks.forEach((cb) => cb(code));
    },

    isReady: function () {
      return isInitialized;
    },
  };

  /**
   * Activates fallback plain textarea with Python tab support
   */
  function activateFallback(initialCode) {
    if (!fallbackTextarea) return;

    fallbackTextarea.classList.remove('hidden');
    fallbackTextarea.value = initialCode;

    // Handle Tab key insertion (4 spaces) and auto-indent
    fallbackTextarea.addEventListener('keydown', function (e) {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        const spaces = '    ';

        this.value = this.value.substring(0, start) + spaces + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;

        changeCallbacks.forEach((cb) => cb(this.value));
      }
    });

    fallbackTextarea.addEventListener('input', function () {
      changeCallbacks.forEach((cb) => cb(this.value));
    });

    isInitialized = true;
  }

  /**
   * Sets up global window key shortcuts
   */
  function setupGlobalKeybindings() {
    window.addEventListener('keydown', function (e) {
      const isCtrlOrCmd = e.ctrlKey || e.metaKey;

      if (isCtrlOrCmd && e.shiftKey && e.key === 'Enter') {
        e.preventDefault();
        CodeEditor.triggerSubmit();
      } else if (isCtrlOrCmd && !e.shiftKey && e.key === 'Enter') {
        e.preventDefault();
        CodeEditor.triggerRun();
      }
    });
  }

  // Window resize observer for Monaco
  window.addEventListener('resize', () => {
    CodeEditor.layout();
  });

  window.CodeEditor = CodeEditor;
})(window);
