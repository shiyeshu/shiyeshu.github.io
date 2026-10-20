/* 松鼠A的博客 · 文章编写器前端逻辑（无框架、无 CDN 依赖） */
(function () {
  'use strict';

  var $ = function (sel) { return document.querySelector(sel); };
  var els = {
    title: $('#title'),
    date: $('#date'),
    category: $('#category'),
    adoptCategory: $('#adopt-category'),
    tagChips: $('#tag-chips'),
    tagInput: $('#tag-input'),
    tagSuggest: $('#tag-suggest'),
    draft: $('#draft'),
    editor: $('#editor'),
    editorWrap: $('#editor-wrap'),
    dropOverlay: $('#drop-overlay'),
    preview: $('#preview'),
    suggestInfo: $('#suggest-info'),
    statWords: $('#stat-words'),
    statFile: $('#stat-file'),
    statState: $('#stat-state'),
    btnSave: $('#btn-save'),
    btnPublish: $('#btn-publish')
  };

  var state = {
    tags: [],
    suggestion: null,
    dirty: false,
    saving: false,
    uploading: 0
  };

  var LS_KEY = 'sshuo-writer-draft-v1';
  var UPLOAD_PLACEHOLDER = '![图片上传中…]()';

  function pad2(n) { return String(n).padStart(2, '0'); }
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
  }

  function setState(text, kind) {
    els.statState.textContent = text;
    els.statState.className = 'state' + (kind ? ' ' + kind : '');
  }

  /* ---------- slug：与 server.py 的 slugify 保持一致的近似实现 ---------- */
  function slugify(title) {
    var s = (title || '').trim();
    if (!s) return 'untitled';
    s = s.replace(/[\\/:*?"<>|\r\n\t]+/g, '-');
    s = s.replace(/\s+/g, ' ').replace(/^[ .\-_]+|[ .\-_]+$/g, '');
    return s || 'untitled';
  }

  /* ---------- 预览 ---------- */
  if (window.marked && typeof window.marked.parse === 'function') {
    try {
      window.marked.use({ gfm: true, breaks: true });
    } catch (e) { /* 老版本 marked 忽略选项 */ }
  }
  function fallbackMarkdown(text) {
    // marked 缺失时的极简兜底渲染（仅保证可读）
    var esc = function (s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    };
    var html = esc(text || '');
    html = html.replace(/^###### (.*)$/gm, '<h6>$1</h6>')
      .replace(/^##### (.*)$/gm, '<h5>$1</h5>')
      .replace(/^#### (.*)$/gm, '<h4>$1</h4>')
      .replace(/^### (.*)$/gm, '<h3>$1</h3>')
      .replace(/^## (.*)$/gm, '<h2>$1</h2>')
      .replace(/^# (.*)$/gm, '<h1>$1</h1>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img alt="$1" src="$2">')
      .replace(/\[([^\]]*)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    return html.split(/\n{2,}/).map(function (b) {
      return /^<(h\d|img|ul|ol|pre|blockquote|table)/.test(b.trim()) ? b : '<p>' + b.replace(/\n/g, '<br>') + '</p>';
    }).join('\n');
  }
  function renderPreview() {
    var text = els.editor.value;
    var html;
    try {
      html = (window.marked && window.marked.parse) ? window.marked.parse(text) : fallbackMarkdown(text);
    } catch (e) {
      html = fallbackMarkdown(text);
    }
    els.preview.innerHTML = html || '<p style="color:#94a3b8">（预览区：开始输入正文后这里会实时渲染）</p>';
  }

  /* ---------- 字数 ---------- */
  function updateWordCount() {
    var text = els.editor.value;
    var chars = text.replace(/\s/g, '').length;
    var lines = text ? text.split('\n').length : 0;
    els.statWords.textContent = '字数 ' + chars + ' · 行数 ' + lines;
  }

  /* ---------- 标签 ---------- */
  function renderTags(suggested) {
    els.tagChips.innerHTML = '';
    state.tags.forEach(function (tag, i) {
      var chip = document.createElement('span');
      chip.className = 'chip';
      chip.appendChild(document.createTextNode(tag));
      var x = document.createElement('span');
      x.className = 'x';
      x.textContent = '×';
      x.title = '删除标签';
      x.addEventListener('click', function () { state.tags.splice(i, 1); renderTags(suggested); markDirty(); });
      chip.appendChild(x);
      els.tagChips.appendChild(chip);
    });
    els.tagSuggest.innerHTML = '';
    (suggested || []).forEach(function (tag) {
      if (state.tags.indexOf(tag) !== -1) return;
      var chip = document.createElement('span');
      chip.className = 'chip';
      chip.textContent = '+ ' + tag;
      chip.title = '点击添加推荐标签';
      chip.addEventListener('click', function () {
        if (state.tags.indexOf(tag) === -1) state.tags.push(tag);
        renderTags(suggested);
        markDirty();
      });
      els.tagSuggest.appendChild(chip);
    });
  }
  function addTagFromInput() {
    var raw = els.tagInput.value.trim();
    if (!raw) return;
    raw.split(/[,，\s]+/).forEach(function (t) {
      t = t.trim();
      if (t && state.tags.indexOf(t) === -1) state.tags.push(t);
    });
    els.tagInput.value = '';
    renderTags(state.suggestion ? state.suggestion.tags : []);
    markDirty();
  }

  /* ---------- 智能推荐 ---------- */
  var suggestTimer = null;
  function scheduleSuggest() {
    if (suggestTimer) clearTimeout(suggestTimer);
    suggestTimer = setTimeout(runSuggest, 600);
  }
  function runSuggest() {
    var title = els.title.value.trim();
    var body = els.editor.value;
    if (!title && !body.trim()) {
      els.suggestInfo.textContent = '智能推荐：等待输入…';
      els.adoptCategory.classList.add('hidden');
      renderTags([]);
      return;
    }
    fetch('/api/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title, body: body })
    }).then(function (r) { return r.json(); }).then(function (data) {
      if (!data || !data.category) return;
      state.suggestion = data;
      var autoMode = els.category.value === 'auto';
      els.suggestInfo.textContent = '智能推荐：' + data.category +
        ' · 标签 ' + (data.tags || []).join(' / ') + (autoMode ? '' : '（已手动选分类）');
      els.adoptCategory.textContent = '采纳推荐分类：' + data.category;
      els.adoptCategory.classList.toggle('hidden', !autoMode);
      renderTags(data.tags || []);
      updateDirtyState();
    }).catch(function (err) {
      els.suggestInfo.textContent = '推荐服务不可用：' + err.message;
    });
  }
  els.adoptCategory.addEventListener('click', function () {
    if (!state.suggestion) return;
    els.category.value = state.suggestion.category;
    runSuggest();
    markDirty();
  });
  els.category.addEventListener('change', function () {
    if (state.suggestion) runSuggest();
    markDirty();
  });
  els.title.addEventListener('input', function () { markDirty(); scheduleSuggest(); });
  els.editor.addEventListener('input', function () { markDirty(); renderPreview(); updateWordCount(); scheduleSuggest(); scheduleLocalDraft(); });
  els.tagInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ',' || e.key === '，') { e.preventDefault(); addTagFromInput(); }
  });
  els.tagInput.addEventListener('blur', addTagFromInput);

  /* ---------- 脏标记 / 本地草稿 ---------- */
  function markDirty() {
    state.dirty = true;
    updateDirtyState();
  }
  function updateDirtyState() {
    if (state.uploading > 0) {
      setState('图片上传中…', 'busy');
      return;
    }
    setState(state.dirty ? '有未保存的更改' : '已保存', state.dirty ? '' : 'ok');
  }
  var draftTimer = null;
  function scheduleLocalDraft() {
    if (draftTimer) clearTimeout(draftTimer);
    draftTimer = setTimeout(function () {
      try {
        localStorage.setItem(LS_KEY, JSON.stringify({
          title: els.title.value,
          body: els.editor.value,
          category: els.category.value,
          tags: state.tags,
          date: els.date.value,
          draft: els.draft.checked,
          savedAt: Date.now()
        }));
        if (state.dirty) setState('草稿已自动保存（浏览器本地）');
      } catch (e) { /* 忽略隐私模式限制 */ }
    }, 2000);
  }
  function restoreLocalDraft() {
    var raw;
    try { raw = localStorage.getItem(LS_KEY); } catch (e) { return false; }
    if (!raw) return false;
    var d;
    try { d = JSON.parse(raw); } catch (e) { return false; }
    if (!d || (!d.title && !d.body)) return false;
    els.title.value = d.title || '';
    els.editor.value = d.body || '';
    els.category.value = d.category || 'auto';
    els.date.value = d.date || today();
    els.draft.checked = !!d.draft;
    state.tags = Array.isArray(d.tags) ? d.tags : [];
    renderTags([]);
    renderPreview();
    updateWordCount();
    setState('已恢复上次本地草稿');
    return true;
  }

  /* ---------- 图片上传 ---------- */
  function insertAtCursor(text) {
    var ta = els.editor;
    var start = ta.selectionStart || 0;
    var end = ta.selectionEnd || 0;
    ta.value = ta.value.slice(0, start) + text + ta.value.slice(end);
    var pos = start + text.length;
    ta.selectionStart = ta.selectionEnd = pos;
    ta.focus();
    markDirty();
    renderPreview();
    updateWordCount();
  }
  function uploadImage(file) {
    state.uploading++;
    updateDirtyState();
    insertAtCursor(UPLOAD_PLACEHOLDER);
    var slug = slugify(els.title.value);
    return fetch('/api/upload', {
      method: 'POST',
      headers: {
        'Content-Type': file.type || 'application/octet-stream',
        'X-Filename': encodeURIComponent(file.name || 'pasted.png'),
        'X-Slug': encodeURIComponent(slug)
      },
      body: file
    }).then(function (r) { return r.json(); }).then(function (data) {
      state.uploading--;
      if (!data || !data.ok) throw new Error((data && data.error) || '上传失败');
      var md = '![' + (file.name && !/^image\./.test(file.name) ? file.name.replace(/\.[^.]+$/, '') : '截图') + '](' + data.url + ')';
      els.editor.value = els.editor.value.replace(UPLOAD_PLACEHOLDER, md);
      renderPreview();
      setState('图片已保存：' + data.relative, 'ok');
      markDirty();
      updateDirtyState();
      return data;
    }).catch(function (err) {
      state.uploading--;
      els.editor.value = els.editor.value.replace(UPLOAD_PLACEHOLDER, '');
      setState('图片上传失败：' + err.message, 'err');
      updateDirtyState();
      throw err;
    });
  }

  // 粘贴截图
  document.addEventListener('paste', function (e) {
    var items = (e.clipboardData && e.clipboardData.items) ? Array.prototype.slice.call(e.clipboardData.items) : [];
    var imgItem = items.filter(function (it) { return it.type && it.type.indexOf('image/') === 0; })[0];
    if (!imgItem) return;
    var file = imgItem.getAsFile();
    if (!file) return;
    e.preventDefault();
    uploadImage(file).catch(function () { /* 状态栏已提示 */ });
  });

  // 拖拽图片
  var dragDepth = 0;
  els.editorWrap.addEventListener('dragenter', function (e) {
    if (e.dataTransfer && Array.prototype.some.call(e.dataTransfer.types || [], function (t) { return t === 'Files'; })) {
      e.preventDefault();
      dragDepth++;
      els.dropOverlay.classList.remove('hidden');
    }
  });
  els.editorWrap.addEventListener('dragover', function (e) { e.preventDefault(); });
  els.editorWrap.addEventListener('dragleave', function (e) {
    e.preventDefault();
    dragDepth = Math.max(0, dragDepth - 1);
    if (!dragDepth) els.dropOverlay.classList.add('hidden');
  });
  els.editorWrap.addEventListener('drop', function (e) {
    e.preventDefault();
    dragDepth = 0;
    els.dropOverlay.classList.add('hidden');
    var files = (e.dataTransfer && e.dataTransfer.files) ? Array.prototype.slice.call(e.dataTransfer.files) : [];
    var img = files.filter(function (f) { return f.type && f.type.indexOf('image/') === 0; })[0];
    if (img) uploadImage(img).catch(function () { /* 已提示 */ });
  });

  /* ---------- 保存 ---------- */
  function savePost() {
    if (state.saving) return;
    var title = els.title.value.trim();
    var body = els.editor.value;
    if (!title) { setState('保存失败：请先填写标题', 'err'); els.title.focus(); return; }
    if (!body.trim()) { setState('保存失败：正文不能为空', 'err'); els.editor.focus(); return; }
    state.saving = true;
    els.btnSave.disabled = true;
    setState('正在保存…', 'busy');
    fetch('/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title,
        date: els.date.value || today(),
        category: els.category.value,
        tags: state.tags,
        body: body,
        draft: els.draft.checked
      })
    }).then(function (r) { return r.json(); }).then(function (data) {
      state.saving = false;
      els.btnSave.disabled = false;
      if (!data || !data.ok) throw new Error((data && data.error) || '保存失败');
      state.dirty = false;
      if (data.category) els.category.value = data.category;
      if (Array.isArray(data.tags) && data.tags.length) { state.tags = data.tags; renderTags([]); }
      els.statFile.textContent = data.relative;
      els.statFile.title = data.path;
      setState('已保存 · ' + data.relative, 'ok');
      try { localStorage.removeItem(LS_KEY); } catch (e) { /* ignore */ }
      updateDirtyState();
      window.__lastSaved = data;
    }).catch(function (err) {
      state.saving = false;
      els.btnSave.disabled = false;
      setState('保存失败：' + err.message, 'err');
    });
  }
  els.btnSave.addEventListener('click', savePost);

  /* ---------- 构建并发布 ---------- */
  els.btnPublish.addEventListener('click', function () {
    var ok = window.confirm('即将执行 deploy.ps1：构建 Hugo 站点并推送到 gh-pages 分支。\n确定现在发布吗？');
    if (!ok) return;
    els.btnPublish.disabled = true;
    setState('正在构建并发布…（可能需要 1-2 分钟）', 'busy');
    fetch('/api/publish', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        els.btnPublish.disabled = false;
        var tail = (data.output || '').trim().split('\n').slice(-8).join('\n');
        setState(data.ok ? '发布成功' : ('发布失败（exit ' + data.code + '）'), data.ok ? 'ok' : 'err');
        window.alert((data.ok ? '✅ 发布成功\n\n' : '❌ 发布失败\n\n') + tail);
      })
      .catch(function (err) {
        els.btnPublish.disabled = false;
        setState('发布失败：' + err.message, 'err');
      });
  });

  /* ---------- 快捷键 / Tab ---------- */
  document.addEventListener('keydown', function (e) {
    var mod = e.ctrlKey || e.metaKey;
    if (mod && (e.key === 's' || e.key === 'S')) {
      e.preventDefault();
      savePost();
    }
  });
  els.editor.addEventListener('keydown', function (e) {
    if (e.key === 'Tab') {
      e.preventDefault();
      insertAtCursor('  ');
    }
  });

  /* ---------- 初始化 ---------- */
  function init() {
    els.date.value = today();
    renderTags([]);
    renderPreview();
    updateWordCount();
    var restored = restoreLocalDraft();
    if (!restored) setState('就绪');
    fetch('/api/health').then(function (r) { return r.json(); }).then(function (h) {
      if (h && h.ok) {
        setState('就绪 · 站点：' + h.site + ' · 已有文章 ' + h.posts + ' 篇');
      }
    }).catch(function () { /* 忽略 */ });
    scheduleSuggest();
  }
  init();
})();
