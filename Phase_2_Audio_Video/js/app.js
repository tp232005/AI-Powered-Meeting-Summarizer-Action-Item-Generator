/* app.js — Main Application Orchestrator */
const App = (() => {
  let currentResult = null;
  let currentTitle = 'Untitled Meeting';
  let recordingActive = false;

  /* ── DOM Helpers ── */
  const $  = id => document.getElementById(id);
  const $$ = sel => document.querySelectorAll(sel);

  /* ── INIT ── */
  const init = () => {
    setupTabs();
    setupNav();
    setupAnalyzeButton();
    setupAudioControls();
    setupExportButtons();
    setupHistorySection();
    setupSampleButton();
    setupSettingsControls();
    renderHistory();
    renderAnalytics();
    showSection('home');
    Audio.initWaveform($('waveform-canvas'));
  };

  /* ── Navigation ── */
  const showSection = (id) => {
    $$('.section').forEach(s => s.classList.remove('active'));
    $$('.nav-item').forEach(n => n.classList.remove('active'));
    const sec = $(id + '-section');
    if (sec) sec.classList.add('active');
    const nav = $('[data-section="' + id + '"]');
    if (nav) nav.classList.add('active');
    if (id === 'history') renderHistory();
    if (id === 'analytics') renderAnalytics();
  };

  const setupNav = () => {
    $$('.nav-item').forEach(item => {
      item.addEventListener('click', () => showSection(item.dataset.section));
    });
  };

  /* ── Input Tabs ── */
  const setupTabs = () => {
    $$('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        $$('.tab-btn').forEach(b => b.classList.remove('active'));
        $$('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        $(btn.dataset.tab + '-panel').classList.add('active');
      });
    });
  };

  /* ── Sample Data ── */
  const setupSampleButton = () => {
    const btn = $('load-sample-btn');
    if (!btn) return;
    btn.addEventListener('click', async () => {
      try {
        const res = await fetch('samples/sample_meeting.txt');
        const text = await res.text();
        $('transcript-input').value = text;
        $('meeting-title-input').value = 'Q1 2025 Product Strategy Meeting';
        showToast('Sample transcript loaded!', 'success');
      } catch {
        $('transcript-input').value = `Sarah: Good morning everyone. Let's review the product roadmap for Q2.\nJames: The backend API refactoring will be done by March 28th. This may affect our launch.\nSarah: How much delay are we looking at James?\nJames: About two weeks worst case. I'll send the timeline by end of day today.\nPriya: We've started the pre-launch campaign. Delaying means missing Apple's feature window on April 10th.\nAlex: James, can we prioritize API work to meet April 5th?\nJames: Yes, I'll reassign two engineers from infrastructure.\nSarah: We've decided to prioritize API work for April 5th launch. James, coordinate with the team and report by Thursday.\nDavid: The new onboarding designs are ready. I'll share the Figma link with James today.\nAlex: David, prepare the UI presentation for the board on March 22nd.\nPriya: We need $50,000 for Q2 marketing. I need approval by end of this week.\nSarah: I'll confirm with finance and get back to you by Wednesday, Priya.\nAlex: I recommend we approve $30,000 for AI recommendation features.\nSarah: Agreed. James, please create a technical spec by next Friday.\nPriya: Let's schedule a launch readiness review for March 30th.\nSarah: Great. I'll send calendar invites for March 30th at 10 AM.`;
        $('meeting-title-input').value = 'Q1 2025 Product Strategy Meeting';
        showToast('Sample transcript loaded!', 'success');
      }
    });
  };

  /* ── Analyze ── */
  const setupAnalyzeButton = () => {
    $('analyze-btn').addEventListener('click', doAnalyze);
  };

  const doAnalyze = () => {
    const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab || 'text';
    let text = '';
    if (activeTab === 'text') {
      text = $('transcript-input').value.trim();
      if (!text) { showToast('Please paste a meeting transcript first.', 'error'); return; }
    } else {
      showToast('Please use text input or finish audio processing first.', 'info');
      return;
    }
    currentTitle = $('meeting-title-input')?.value?.trim() || 'Untitled Meeting';
    const summaryLen = parseInt($('summary-length')?.value || '5');
    runAnalysis(text, summaryLen);
  };

  const runAnalysis = (text, summaryLen = 5) => {
    $('analyze-btn').classList.add('loading');
    $('analyze-btn').disabled = true;

    setTimeout(() => {
      const result = NLP.analyze(text, summaryLen);
      $('analyze-btn').classList.remove('loading');
      $('analyze-btn').disabled = false;

      if (result.error) { showToast(result.error, 'error'); return; }
      currentResult = result;
      History.save(currentTitle, result);
      renderResults(result);
      showSection('results');
      showToast('Analysis complete!', 'success');
    }, 600);
  };

  /* ── Audio Controls ── */
  const setupAudioControls = () => {
    const recBtn = $('record-btn');
    const stopBtn = $('stop-btn');
    const fileInput = $('audio-file-input');
    const canvas = $('waveform-canvas');
    const statusEl = $('audio-status');

    if (recBtn) {
      recBtn.addEventListener('click', async () => {
        if (recordingActive) return;
        recordingActive = true;
        recBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        await Audio.startRecording(canvas, (status, msg) => {
          if (status === 'error') {
            showToast(msg || 'Microphone failed', 'error');
            recordingActive = false;
            recBtn.disabled = false;
          }
          if (statusEl) statusEl.textContent = status === 'recording' ? '🔴 Recording...' : '';
        });
      });
    }

    if (stopBtn) {
      stopBtn.disabled = true;
      stopBtn.addEventListener('click', () => {
        Audio.stopRecording(transcript => {
          $('transcript-input').value = transcript;
          const textTab = $('[data-tab="text"]');
          const textPanel = $('text-panel');
          $$('.tab-btn').forEach(b => b.classList.remove('active'));
          $$('.tab-panel').forEach(p => p.classList.remove('active'));
          if (textTab) textTab.classList.add('active');
          if (textPanel) textPanel.classList.add('active');
          if (statusEl) statusEl.textContent = '✅ Transcribed! Ready to analyze.';
          recordingActive = false;
          recBtn.disabled = false;
          stopBtn.disabled = true;
          Audio.initWaveform(canvas);
          showToast('Audio transcribed! Click Analyze.', 'success');
        });
      });
    }

    if (fileInput) {
      fileInput.addEventListener('change', e => {
        const file = e.target.files[0];
        if (!file) return;
        const label = $('file-label');
        if (label) label.textContent = file.name;
        Audio.handleFileUpload(file, canvas,
          transcript => {
            $('transcript-input').value = transcript;
            $$('.tab-btn').forEach(b => b.classList.remove('active'));
            $$('.tab-panel').forEach(p => p.classList.remove('active'));
            const t = $('[data-tab="text"]'), p = $('text-panel');
            if (t) t.classList.add('active'); if (p) p.classList.add('active');
            if (statusEl) statusEl.textContent = '✅ File processed! Ready to analyze.';
            showToast('Audio file processed! Click Analyze.', 'success');
          },
          (status, msg) => {
            if (statusEl) statusEl.textContent = status === 'error' ? '❌ ' + msg : status === 'processing' ? '⏳ Processing audio...' : '';
            if (status === 'error') showToast(msg, 'error');
          }
        );
      });
    }
  };

  /* ── Render Results ── */
  const renderResults = (r) => {
    $('result-title').textContent = currentTitle;

    // Stats bar
    $('stat-words').textContent = r.stats.wordCount.toLocaleString();
    $('stat-duration').textContent = r.stats.estimatedDuration + ' min';
    $('stat-speakers').textContent = r.stats.speakerCount || '-';
    $('stat-actions').textContent = r.actionItems.length;
    $('stat-decisions').textContent = r.decisions.length;
    $('stat-sentiment').textContent = r.sentiment.label;
    $('stat-sentiment').className = 'stat-value sentiment-' + r.sentiment.label;

    // Summary
    $('summary-text').textContent = r.summary;

    // Key Points
    const kpList = $('key-points-list');
    kpList.innerHTML = r.keyPoints.length
      ? r.keyPoints.map(p => `<li class="key-point-item"><span class="kp-icon">💡</span><span>${p}</span></li>`).join('')
      : '<li class="empty-state">No key points detected.</li>';

    // Action Items
    const aiList = $('action-items-list');
    aiList.innerHTML = r.actionItems.length
      ? r.actionItems.map((a, i) => `
        <div class="action-card priority-${a.priority}" data-id="${i}">
          <div class="action-header">
            <span class="priority-badge ${a.priority}">${a.priority}</span>
            <span class="action-status ${a.status}" onclick="App.toggleStatus(${i})">${a.status}</span>
          </div>
          <p class="action-text">${a.text}</p>
          <div class="action-meta">
            <span><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg> ${a.assignee}</span>
            <span><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> ${a.deadline}</span>
          </div>
        </div>`).join('')
      : '<div class="empty-state">No action items detected.</div>';

    // Decisions
    const decList = $('decisions-list');
    decList.innerHTML = r.decisions.length
      ? r.decisions.map(d => `<div class="decision-item"><span class="decision-icon">⚖️</span><p>${d}</p></div>`).join('')
      : '<div class="empty-state">No decisions detected.</div>';

    // Speakers
    const spkList = $('speakers-list');
    if (r.hasSpeakers) {
      const colors = ['#a78bfa','#38bdf8','#34d399','#fbbf24','#f472b6','#fb923c'];
      const names = Object.keys(r.speakers);
      spkList.innerHTML = names.map((name, i) => {
        const s = r.speakerSentiments[name];
        const count = r.speakers[name].length;
        const initials = name.split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
        return `<div class="speaker-card">
          <div class="speaker-avatar" style="background:${colors[i%colors.length]}22;color:${colors[i%colors.length]}">${initials}</div>
          <div class="speaker-info">
            <div class="speaker-name">${name}</div>
            <div class="speaker-meta">${count} utterances · <span class="sentiment-${s?.label||'neutral'}">${s?.label||'neutral'}</span></div>
          </div>
        </div>`;
      }).join('');
    } else {
      spkList.innerHTML = '<div class="empty-state">No speakers detected. Use "Name: text" format.</div>';
    }

    // Keywords
    const kwCloud = $('keywords-cloud');
    kwCloud.innerHTML = r.keywords.slice(0,25).map((k,i) => {
      const size = Math.max(12, Math.min(24, k.count * 3 + 12));
      const opacity = 0.5 + (i/25)*0.5;
      const colors = ['#a78bfa','#38bdf8','#34d399','#fbbf24','#f472b6'];
      return `<span class="keyword-tag" style="font-size:${size}px;opacity:${opacity};background:${colors[i%5]}1a;color:${colors[i%5]}">${k.word}</span>`;
    }).join('');

    // Readability
    const rd = r.readability;
    $('readability-label').textContent = rd.label;
    $('readability-score').textContent = rd.score + '/100';

    // Topics
    const topicList = $('topics-list');
    topicList.innerHTML = r.topics.map((t,i)=>`
      <div class="topic-item">
        <div class="topic-header">
          <span class="topic-num">${i+1}</span>
          <span class="topic-name">${t.topic}</span>
          <span class="topic-count">${t.sentences.length} sentences</span>
        </div>
        <p class="topic-preview">${t.sentences[0]?.slice(0,120)}...</p>
      </div>`).join('');

    // Canvases
    setTimeout(() => {
      const wc = $('wordcloud-canvas');
      if (wc) Viz.drawWordCloud(wc, r.keywords);
      const sc = $('sentiment-canvas');
      if (sc && r.hasSpeakers) Viz.drawSentimentChart(sc, r.speakerSentiments);
      const tl = $('timeline-canvas');
      if (tl) Viz.drawTimeline(tl, r.topics);

      // Score rings
      const actionDensity = Math.min(r.actionItems.length / 10, 1);
      const engagementScore = Math.min(r.stats.speakerCount / 5, 1);
      const clarityScore = r.readability.score / 100;
      if ($('ring-action')) Viz.drawRing($('ring-action'), actionDensity*100, 100, '#a78bfa', 'Actions');
      if ($('ring-engagement')) Viz.drawRing($('ring-engagement'), engagementScore*100, 100, '#38bdf8', 'Engagement');
      if ($('ring-clarity')) Viz.drawRing($('ring-clarity'), clarityScore*100, 100, '#34d399', 'Clarity');
    }, 100);
  };

  /* ── Toggle Action Status ── */
  const toggleStatus = (idx) => {
    if (!currentResult) return;
    const a = currentResult.actionItems[idx];
    if (!a) return;
    a.status = a.status === 'pending' ? 'done' : 'pending';
    renderResults(currentResult);
  };

  /* ── Export ── */
  const setupExportButtons = () => {
    const guard = () => { if (!currentResult) { showToast('Please analyze a meeting first.', 'error'); return false; } return true; };
    const btn = (id, fn) => { const el=$(id); if(el) el.addEventListener('click', fn); };
    btn('export-md-btn',  () => guard() && Export.exportMarkdown(currentResult, currentTitle));
    btn('export-json-btn',() => guard() && Export.exportJSON(currentResult, currentTitle));
    btn('export-pdf-btn', () => guard() && Export.exportPDF(currentResult, currentTitle));
    btn('export-ics-btn', () => guard() && Export.exportCalendar(currentResult, currentTitle));
    btn('copy-btn', async () => {
      if (!guard()) return;
      const ok = await Export.copyToClipboard(currentResult, currentTitle);
      showToast(ok ? 'Copied to clipboard!' : 'Copy failed — try manual select.', ok ? 'success' : 'error');
    });
  };

  /* ── History ── */
  const setupHistorySection = () => {
    $('clear-history-btn')?.addEventListener('click', () => {
      if (confirm('Clear all meeting history?')) { History.clear(); renderHistory(); showToast('History cleared.', 'info'); }
    });
    $('history-search')?.addEventListener('input', e => renderHistory(e.target.value));
  };

  const renderHistory = (query = '') => {
    const list = $('history-list');
    if (!list) return;
    let entries = History.getAll();
    if (query) entries = entries.filter(e => e.title.toLowerCase().includes(query.toLowerCase()) || e.summary.toLowerCase().includes(query.toLowerCase()));
    if (!entries.length) {
      list.innerHTML = '<div class="empty-state-big"><div class="empty-icon">📋</div><p>No meetings saved yet.<br>Analyze your first meeting to see history here.</p></div>';
      return;
    }
    list.innerHTML = entries.map(e => `
      <div class="history-card" onclick="App.loadFromHistory('${e.id}')">
        <div class="history-header">
          <span class="history-title">${e.title}</span>
          <span class="history-date">${new Date(e.timestamp).toLocaleString()}</span>
        </div>
        <p class="history-preview">${e.summary}</p>
        <div class="history-tags">
          <span class="htag">📝 ${e.actionCount} actions</span>
          <span class="htag">⚖️ ${e.decisionCount} decisions</span>
          <span class="htag sentiment-${e.sentiment}">● ${e.sentiment}</span>
        </div>
        <button class="del-btn" onclick="event.stopPropagation();App.deleteHistory('${e.id}')">✕</button>
      </div>`).join('');
  };

  const loadFromHistory = (id) => {
    const entry = History.get(id);
    if (!entry) return;
    currentResult = entry.result;
    currentTitle = entry.title;
    renderResults(entry.result);
    showSection('results');
  };

  const deleteHistory = (id) => {
    History.remove(id);
    renderHistory($('history-search')?.value || '');
    showToast('Deleted.', 'info');
  };

  /* ── Analytics ── */
  const renderAnalytics = () => {
    const st = History.getStats();
    const container = $('analytics-content');
    if (!container) return;
    if (!st) {
      container.innerHTML = '<div class="empty-state-big"><div class="empty-icon">📊</div><p>No data yet. Analyze some meetings to see insights here.</p></div>';
      return;
    }
    container.innerHTML = `
      <div class="analytics-grid">
        <div class="analytics-card"><div class="ac-num">${st.total}</div><div class="ac-label">Meetings Analyzed</div></div>
        <div class="analytics-card accent-purple"><div class="ac-num">${st.totalActions}</div><div class="ac-label">Total Action Items</div></div>
        <div class="analytics-card accent-teal"><div class="ac-num">${st.totalDecisions}</div><div class="ac-label">Total Decisions</div></div>
        <div class="analytics-card accent-gold"><div class="ac-num">${st.avgWordCount.toLocaleString()}</div><div class="ac-label">Avg Words / Meeting</div></div>
      </div>
      <div class="sentiment-breakdown">
        <h3>Sentiment Distribution</h3>
        <div class="sentiment-bars">
          ${['positive','neutral','negative'].map(s => {
            const count = st.sentiments[s]||0;
            const pct = st.total ? Math.round((count/st.total)*100) : 0;
            return `<div class="sbar"><span class="sbar-label sentiment-${s}">${s}</span>
              <div class="sbar-track"><div class="sbar-fill ${s}" style="width:${pct}%"></div></div>
              <span class="sbar-pct">${pct}%</span></div>`;
          }).join('')}
        </div>
      </div>`;
  };

  /* ── Settings ── */
  const setupSettingsControls = () => {
    const themeToggle = $('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('change', () => {
        document.body.classList.toggle('light-mode', themeToggle.checked);
      });
    }
  };

  /* ── Toast ── */
  const showToast = (msg, type = 'info') => {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = {success:'✅', error:'❌', info:'ℹ️', warning:'⚠️'};
    toast.innerHTML = `<span>${icons[type]||'ℹ️'}</span><span>${msg}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 3500);
  };

  document.addEventListener('DOMContentLoaded', init);
  return {toggleStatus, loadFromHistory, deleteHistory, showSection, showToast};
})();
