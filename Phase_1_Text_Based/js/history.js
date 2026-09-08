/* History Module - LocalStorage based meeting archive */
const History = (() => {
  const KEY = 'meeting_summarizer_history';

  const getAll = () => {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); }
    catch { return []; }
  };

  const save = (title, result) => {
    const all = getAll();
    const entry = {
      id: Date.now().toString(),
      title: title || `Meeting ${new Date().toLocaleDateString()}`,
      timestamp: result.timestamp || new Date().toISOString(),
      summary: result.summary?.slice(0,200) + '...',
      actionCount: result.actionItems?.length || 0,
      decisionCount: result.decisions?.length || 0,
      speakerCount: result.stats?.speakerCount || 0,
      sentiment: result.sentiment?.label || 'neutral',
      wordCount: result.stats?.wordCount || 0,
      result
    };
    all.unshift(entry);
    if (all.length > 50) all.splice(50);
    localStorage.setItem(KEY, JSON.stringify(all));
    return entry;
  };

  const remove = (id) => {
    const all = getAll().filter(e => e.id !== id);
    localStorage.setItem(KEY, JSON.stringify(all));
  };

  const get = (id) => getAll().find(e => e.id === id);

  const clear = () => localStorage.removeItem(KEY);

  const getStats = () => {
    const all = getAll();
    if (!all.length) return null;
    const sentiments = {positive:0, negative:0, neutral:0};
    all.forEach(e => sentiments[e.sentiment] = (sentiments[e.sentiment]||0)+1);
    return {
      total: all.length,
      totalActions: all.reduce((a,e)=>a+e.actionCount,0),
      totalDecisions: all.reduce((a,e)=>a+e.decisionCount,0),
      avgWordCount: Math.round(all.reduce((a,e)=>a+e.wordCount,0)/all.length),
      sentiments,
      mostRecent: all[0]
    };
  };

  return {getAll, save, remove, get, clear, getStats};
})();
