/* Visualizations Module */
const Viz = (() => {

  /* ── Word Cloud ── */
  const drawWordCloud = (canvas, keywords) => {
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    if (!keywords || !keywords.length) return;
    const max = keywords[0].count;
    const colors = ['#a78bfa','#38bdf8','#34d399','#fbbf24','#f472b6','#fb923c','#818cf8'];
    const placed = [];
    keywords.slice(0, 40).forEach((kw, i) => {
      const size = Math.max(12, Math.min(52, (kw.count / max) * 50 + 12));
      ctx.font = `bold ${size}px Inter, sans-serif`;
      const tw = ctx.measureText(kw.word).width;
      let x, y, tries = 0, ok = false;
      while (tries < 200 && !ok) {
        x = tw/2 + 10 + Math.random() * (W - tw - 20);
        y = size + 10 + Math.random() * (H - size - 20);
        ok = !placed.some(p => Math.abs(p.x - x) < p.w/2 + tw/2 + 4 && Math.abs(p.y - y) < p.h/2 + size/2 + 4);
        tries++;
      }
      if (ok) {
        placed.push({x, y, w: tw, h: size});
        ctx.fillStyle = colors[i % colors.length];
        ctx.globalAlpha = 0.85 + (kw.count / max) * 0.15;
        ctx.fillText(kw.word, x - tw/2, y);
      }
    });
    ctx.globalAlpha = 1;
  };

  /* ── Sentiment Bar Chart ── */
  const drawSentimentChart = (canvas, speakerSentiments) => {
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    const names = Object.keys(speakerSentiments);
    if (!names.length) return;
    const pad = {l:50, r:20, t:20, b:60};
    const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;
    const bw = Math.min(60, cw / names.length - 10);
    const gap = cw / names.length;

    // Axes
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    [0, 25, 50, 75, 100].forEach(v => {
      const y = pad.t + ch - (v/100)*ch;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l+cw, y); ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.font = '10px Inter';
      ctx.fillText(v+'%', pad.l - 28, y + 4);
    });

    names.forEach((name, i) => {
      const d = speakerSentiments[name];
      const total = Math.max(d.total, 1);
      const posH = (d.pos / total) * ch;
      const negH = (d.neg / total) * ch;
      const x = pad.l + i * gap + gap/2 - bw/2;

      // Positive bar
      const grad = ctx.createLinearGradient(0, pad.t+ch-posH, 0, pad.t+ch);
      grad.addColorStop(0, '#34d399'); grad.addColorStop(1, '#059669');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.roundRect(x, pad.t+ch-posH, bw*0.45, posH, [4,4,0,0]);
      ctx.fill();

      // Negative bar
      const grad2 = ctx.createLinearGradient(0, pad.t+ch-negH, 0, pad.t+ch);
      grad2.addColorStop(0, '#f87171'); grad2.addColorStop(1, '#dc2626');
      ctx.fillStyle = grad2;
      ctx.beginPath();
      ctx.roundRect(x+bw*0.5, pad.t+ch-negH, bw*0.45, negH, [4,4,0,0]);
      ctx.fill();

      // Label
      ctx.fillStyle = 'rgba(255,255,255,0.7)';
      ctx.font = '10px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(name.split(' ')[0], x+bw/2, H - pad.b + 15);
      ctx.textAlign = 'left';
    });

    // Legend
    ctx.font = '10px Inter';
    [['#34d399','Positive'], ['#f87171','Negative']].forEach(([c,l], i) => {
      ctx.fillStyle = c; ctx.fillRect(pad.l + i*80, H-18, 10, 10);
      ctx.fillStyle = 'rgba(255,255,255,0.6)'; ctx.fillText(l, pad.l+12+i*80, H-9);
    });
  };

  /* ── Donut / Score Ring ── */
  const drawRing = (canvas, value, max, color, label) => {
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    const cx = W/2, cy = H/2, r = Math.min(W,H)*0.38;
    const angle = (value / max) * 2 * Math.PI;
    // Track
    ctx.beginPath(); ctx.arc(cx,cy,r,0,2*Math.PI);
    ctx.strokeStyle='rgba(255,255,255,0.08)'; ctx.lineWidth=10; ctx.stroke();
    // Fill
    const g = ctx.createLinearGradient(cx-r,cy-r,cx+r,cy+r);
    g.addColorStop(0,color); g.addColorStop(1,color+'99');
    ctx.beginPath(); ctx.arc(cx,cy,r,-Math.PI/2,-Math.PI/2+angle);
    ctx.strokeStyle=g; ctx.lineWidth=10; ctx.lineCap='round'; ctx.stroke();
    // Text
    ctx.fillStyle='#fff'; ctx.font=`bold ${Math.round(W*0.18)}px Inter`;
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(Math.round((value/max)*100)+'%', cx, cy-8);
    ctx.font=`${Math.round(W*0.09)}px Inter`;
    ctx.fillStyle='rgba(255,255,255,0.5)'; ctx.fillText(label, cx, cy+14);
    ctx.textBaseline='alphabetic';
  };

  /* ── Topic Timeline ── */
  const drawTimeline = (canvas, topics) => {
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    if (!topics || !topics.length) return;
    const colors = ['#a78bfa','#38bdf8','#34d399','#fbbf24','#f472b6','#fb923c'];
    const bh = Math.min(36, (H - 20) / topics.length - 6);
    const total = topics.reduce((a,t)=>a+t.sentences.length,0);
    let x = 40;
    topics.forEach((t, i) => {
      const bw = Math.max(4, ((t.sentences.length / total) * (W - 60)));
      const y = 10 + i * (bh + 6);
      ctx.fillStyle = colors[i % colors.length] + '33';
      ctx.beginPath(); ctx.roundRect(x, y, bw, bh, 4); ctx.fill();
      ctx.fillStyle = colors[i % colors.length];
      ctx.beginPath(); ctx.roundRect(x, y, 4, bh, [4,0,0,4]); ctx.fill();
      ctx.font = '11px Inter'; ctx.fillStyle='rgba(255,255,255,0.8)';
      ctx.fillText(t.topic.substring(0,28), x+10, y+bh/2+4);
    });
  };

  return {drawWordCloud, drawSentimentChart, drawRing, drawTimeline};
})();
