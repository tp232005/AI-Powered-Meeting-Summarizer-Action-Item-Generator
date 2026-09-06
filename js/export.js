/* Export Module */
const Export = (() => {

  const download = (content, filename, mime) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([content], {type: mime}));
    a.download = filename; a.click();
    URL.revokeObjectURL(a.href);
  };

  const toMarkdown = (result, title) => {
    const d = new Date(result.timestamp).toLocaleString();
    let md = `# Meeting Summary: ${title}\n**Date:** ${d}\n\n---\n\n`;
    md += `## 📋 Summary\n${result.summary}\n\n`;
    md += `## 🔑 Key Points\n`;
    result.keyPoints.forEach(p => { md += `- ${p}\n`; });
    md += `\n## ✅ Action Items\n`;
    result.actionItems.forEach(a => {
      md += `- **[${a.priority.toUpperCase()}]** ${a.text}\n  - Assignee: ${a.assignee} | Deadline: ${a.deadline}\n`;
    });
    md += `\n## 🎯 Decisions Made\n`;
    result.decisions.forEach(d => { md += `- ${d}\n`; });
    md += `\n## 📊 Meeting Stats\n`;
    md += `- Words: ${result.stats.wordCount} | Sentences: ${result.stats.sentenceCount}\n`;
    md += `- Estimated Duration: ~${result.stats.estimatedDuration} minutes\n`;
    md += `- Speakers Detected: ${result.stats.speakerCount}\n`;
    md += `- Overall Sentiment: ${result.sentiment.label}\n`;
    if (result.hasSpeakers) {
      md += `\n## 👥 Participants\n`;
      Object.entries(result.speakerSentiments).forEach(([name,s]) => {
        md += `- **${name}**: ${s.count} utterances | Sentiment: ${s.label}\n`;
      });
    }
    md += `\n## 🏷️ Top Keywords\n`;
    md += result.keywords.slice(0,10).map(k=>`\`${k.word}\``).join(', ') + '\n';
    return md;
  };

  const toJSON = (result, title) => {
    return JSON.stringify({title, ...result}, null, 2);
  };

  const icsEscape = value => String(value || '')
    .replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,')
    .replace(/\r?\n/g, '\\n');

  const toICSDate = (value, fallback) => {
    const text = String(value || '').trim();
    const parsed = new Date(text);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed.toISOString().slice(0, 10).replace(/-/g, '');
    }
    const match = text.match(/(?:^|\s)(\d{1,2})[/. -](\d{1,2})(?:[/. -](\d{2,4}))?/);
    if (match) {
      const year = match[3] ? (match[3].length === 2 ? '20' + match[3] : match[3]) : fallback.getFullYear();
      return `${year}${match[2].padStart(2, '0')}${match[1].padStart(2, '0')}`;
    }
    return fallback.toISOString().slice(0, 10).replace(/-/g, '');
  };

  const toCalendar = (result, title) => {
    const meetingDate = new Date(result.timestamp || Date.now());
    const events = (result.actionItems || []).map((item, index) => {
      const date = toICSDate(item.deadline, meetingDate);
      const nextDate = new Date(`${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}T00:00:00`);
      nextDate.setDate(nextDate.getDate() + 1);
      const end = nextDate.toISOString().slice(0, 10).replace(/-/g, '');
      const summary = `[${item.priority || 'low'}] ${item.text || 'Action item'}`;
      const description = `Assignee: ${item.assignee || 'Not specified'}\nDeadline: ${item.deadline || 'Not specified'}\nSource meeting: ${title}`;
      return [
        'BEGIN:VEVENT', `UID:meetmind-${Date.now()}-${index}@meetmind`, `DTSTAMP:${new Date().toISOString().replace(/[-:.]/g, '').slice(0, 15)}Z`,
        `DTSTART;VALUE=DATE:${date}`, `DTEND;VALUE=DATE:${end}`, `SUMMARY:${icsEscape(summary)}`,
        `DESCRIPTION:${icsEscape(description)}`, 'END:VEVENT'
      ].join('\r\n');
    });
    return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//MeetMind//Meeting Actions//EN', 'CALSCALE:GREGORIAN', ...events, 'END:VCALENDAR'].join('\r\n') + '\r\n';
  };

  const toPrintHTML = (result, title) => {
    const d = new Date(result.timestamp).toLocaleString();
    return `<!DOCTYPE html><html><head><title>${title}</title>
    <style>body{font-family:Arial,sans-serif;margin:40px;color:#222;line-height:1.6}
    h1{color:#6d28d9}h2{color:#7c3aed;border-bottom:1px solid #ddd;padding-bottom:6px}
    .chip{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;margin:2px}
    .high{background:#fee2e2;color:#dc2626}.medium{background:#fef3c7;color:#d97706}
    .low{background:#d1fae5;color:#065f46}.tag{background:#ede9fe;color:#6d28d9}</style>
    </head><body>
    <h1>Meeting Summary: ${title}</h1><p><em>${d}</em></p><hr>
    <h2>Summary</h2><p>${result.summary}</p>
    <h2>Key Points</h2><ul>${result.keyPoints.map(p=>`<li>${p}</li>`).join('')}</ul>
    <h2>Action Items</h2><ul>${result.actionItems.map(a=>`<li>
      <span class="chip ${a.priority}">${a.priority.toUpperCase()}</span>
      ${a.text}<br><small>Assignee: <b>${a.assignee}</b> | Deadline: ${a.deadline}</small>
    </li>`).join('')}</ul>
    <h2>Decisions Made</h2><ul>${result.decisions.map(d=>`<li>${d}</li>`).join('')}</ul>
    <h2>Top Keywords</h2>${result.keywords.slice(0,10).map(k=>`<span class="chip tag">${k.word}</span>`).join('')}
    </body></html>`;
  };

  const exportMarkdown = (result, title) => download(toMarkdown(result,title), `meeting-${Date.now()}.md`, 'text/markdown');
  const exportJSON = (result, title) => download(toJSON(result,title), `meeting-${Date.now()}.json`, 'application/json');
  const exportCalendar = (result, title) => download(toCalendar(result, title), `meeting-actions-${Date.now()}.ics`, 'text/calendar');

  const exportPDF = (result, title) => {
    const html = toPrintHTML(result, title);
    const w = window.open('', '_blank');
    w.document.write(html);
    w.document.close();
    setTimeout(() => w.print(), 400);
  };

  const copyToClipboard = async (result, title) => {
    const text = toMarkdown(result, title);
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      return false;
    }
  };

  return {exportMarkdown, exportJSON, exportPDF, exportCalendar, copyToClipboard};
})();
