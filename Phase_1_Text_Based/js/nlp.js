/* NLP Engine - Meeting Summarizer */
const NLP = (() => {
  const STOP = new Set(['i','me','my','we','our','you','your','he','him','his','she','her','it','its','they','them','their','what','which','who','whom','this','that','these','those','am','is','are','was','were','be','been','being','have','has','had','do','does','did','a','an','the','and','but','if','or','as','of','at','by','for','with','about','to','from','in','out','on','so','than','very','will','just','now','also','would','could','may','said','know','think','want','going','okay','good','great','yeah','yes']);

  const POS_WORDS = new Set(['good','great','excellent','fantastic','wonderful','amazing','awesome','perfect','outstanding','brilliant','happy','positive','success','successful','achieve','accomplished','approve','approved','agree','agreed','confirmed','finalized','completed','done','ready','excited','confident','efficient','effective','innovative','valuable','helpful','clear','productive','progress','opportunity','growth','improve','improved','support','priority','solution','resolved','fixed']);
  const NEG_WORDS = new Set(['bad','poor','terrible','horrible','awful','negative','failure','failed','problem','issue','concern','worry','worried','delay','delayed','blocking','blocked','stuck','difficult','challenge','challenging','confused','unclear','uncertain','risk','risky','critical','urgent','behind','missed','mistake','error','bug','broken','missing','incomplete','unfinished','overdue','late','slow','expensive','conflict','disagree','reject','rejected','denied']);

  const tokenize = t => t.toLowerCase().replace(/[^a-z0-9\s]/g,' ').split(/\s+/).filter(w=>w.length>1);
  const getSentences = t => t.match(/[^.!?]+[.!?]*/g)?.map(s=>s.trim()).filter(s=>s.length>10)||[];
  const cap = s => s.charAt(0).toUpperCase()+s.slice(1);

  const wordFreq = tokens => {
    const f={};
    tokens.forEach(w=>{ if(!STOP.has(w)) f[w]=(f[w]||0)+1; });
    return f;
  };

  const jaccard = (a,b) => {
    const sa=new Set(tokenize(a)), sb=new Set(tokenize(b));
    const inter=[...sa].filter(x=>sb.has(x)).length;
    const uni=new Set([...sa,...sb]).size;
    return uni?inter/uni:0;
  };

  /* TF-IDF Summarization */
  const summarize = (text, n=5) => {
    const sents=getSentences(text);
    if(sents.length<=n) return sents;
    const allToks=sents.map(s=>tokenize(s));
    const N=sents.length;
    const df={};
    allToks.forEach(toks=>{ new Set(toks).forEach(t=>{ df[t]=(df[t]||0)+1; }); });
    const idf=t=>Math.log((N+1)/((df[t]||0)+1))+1;
    const scored=sents.map((s,i)=>{
      const toks=allToks[i], tf=wordFreq(toks), total=toks.length||1;
      let sc=0;
      Object.entries(tf).forEach(([t,c])=>{ sc+=(c/total)*idf(t); });
      const pos= i===0||i===N-1?1.3:i<N*0.2?1.15:1.0;
      const len= toks.length<5?0.5:toks.length>40?0.8:1.0;
      return {s,sc:sc*pos*len,i};
    });
    return scored.sort((a,b)=>b.sc-a.sc).slice(0,n).sort((a,b)=>a.i-b.i).map(x=>x.s);
  };

  /* Keyword Extraction */
  const keywords = (text, top=20) => {
    const toks=tokenize(text).filter(w=>!STOP.has(w)&&w.length>3);
    const f=wordFreq(toks);
    return Object.entries(f).sort((a,b)=>b[1]-a[1]).slice(0,top).map(([word,count])=>({word,count}));
  };

  /* Speaker Parsing */
  const parseSpeakers = text => {
    const lines=text.split('\n').map(l=>l.trim()).filter(Boolean);
    const speakers={}, utterances=[];
    const pats=[/^([A-Z][a-zA-Z\s]{1,20}):\s*(.+)/, /^\[([A-Z][a-zA-Z\s]{1,20})\]\s*(.+)/, /^([A-Z][a-zA-Z\s]{1,20})\s*[-–]\s*(.+)/];
    lines.forEach(line=>{
      let matched=false;
      for(const p of pats){
        const m=line.match(p);
        if(m){
          const spk=m[1].trim(), sp=m[2].trim();
          if(!speakers[spk]) speakers[spk]=[];
          speakers[spk].push(sp);
          utterances.push({speaker:spk,speech:sp});
          matched=true; break;
        }
      }
      if(!matched&&utterances.length>0){
        const last=utterances[utterances.length-1];
        last.speech+=' '+line;
        speakers[last.speaker][speakers[last.speaker].length-1]+=' '+line;
      }
    });
    return {speakers,utterances};
  };

  /* Sentiment */
  const sentiment = text => {
    const toks=tokenize(text);
    let pos=0,neg=0;
    toks.forEach(w=>{ if(POS_WORDS.has(w))pos++; if(NEG_WORDS.has(w))neg++; });
    const sc=(pos-neg)/Math.max(toks.length,1);
    return {pos,neg,score:sc,label:sc>0.02?'positive':sc<-0.02?'negative':'neutral',total:toks.length};
  };

  const speakerSentiments = spks => {
    const r={};
    Object.entries(spks).forEach(([n,speeches])=>{ r[n]={...sentiment(speeches.join(' ')),count:speeches.length}; });
    return r;
  };

  /* Action Items */
  const actionItems = (text, spks) => {
    const sents=getSentences(text);
    const pats=[
      /\b(will|shall|must|needs? to|going to|plan to)\s+[^.!?]{5,80}/i,
      /\b(action item|follow.?up|task|assigned to)\s*[:–]?\s*[^.!?]{5,80}/i,
      /\b(please|can you|could you)\s+[^.!?]{5,80}/i,
      /\b(complete|finish|deliver|submit|send|prepare|create|build|implement|review|approve|schedule|coordinate)\s+[^.!?]{3,80}/i
    ];
    const deadPat=/\b(by\s+)?(monday|tuesday|wednesday|thursday|friday|eod|tomorrow|next\s+\w+|march\s+\d{1,2}|april\s+\d{1,2}|may\s+\d{1,2}|end\s+of\s+\w+|\d{1,2}(?:st|nd|rd|th)?)/i;
    const items=[];
    sents.forEach(sent=>{
      if(!pats.some(p=>p.test(sent))||sent.split(' ').length<5) return;
      const dm=sent.match(deadPat);
      const deadline=dm?cap(dm[0].replace(/^by\s*/i,'').trim()):'Not specified';
      let assignee='Team';
      for(const name of Object.keys(spks)){
        if(new RegExp(`\\b${name.split(' ')[0]}\\b`,'i').test(sent)){ assignee=name; break; }
      }
      const priority=/\b(urgent|critical|immediately|asap|must)\b/i.test(sent)?'high':/\b(soon|this week)\b/i.test(sent)?'medium':'low';
      items.push({text:sent.trim(),assignee,deadline,priority,status:'pending'});
    });
    return items.filter((item,i,arr)=>!arr.slice(0,i).some(u=>jaccard(u.text,item.text)>0.7));
  };

  /* Decisions */
  const decisions = text => {
    const sents=getSentences(text);
    const pats=[
      /\b(decided|decision|agreed|agreement|approved|confirmed|resolved|concluded|determined|consensus)\b/i,
      /\b(we('?ve)?\s+(decided|agreed|approved|confirmed))\b/i,
      /\b(going forward|final decision|we will (proceed|move forward|go ahead))\b/i
    ];
    return [...new Set(sents.filter(s=>pats.some(p=>p.test(s))).map(s=>s.trim()))];
  };

  /* Key Points */
  const keyPoints = (text, n=7) => {
    const sents=getSentences(text);
    const importPats=[
      /\b(important|critical|key|main|primary|major|significant|essential)\b/i,
      /\b(note that|important to|highlight)\b/i,
      /\b(agenda|objective|goal|target|milestone|deadline|priority)\b/i,
      /\b(issue|problem|concern|risk|blocker)\b/i,
      /\b(update|status|progress|result|outcome)\b/i
    ];
    return sents.map(s=>({s,sc:importPats.filter(p=>p.test(s)).length*2+tokenize(s).filter(w=>!STOP.has(w)).length*0.1}))
      .sort((a,b)=>b.sc-a.sc).slice(0,n).map(x=>x.s.trim()).filter(s=>s.length>20);
  };

  /* Topic Segmentation */
  const segmentTopics = text => {
    const sents=getSentences(text);
    if(sents.length<4) return [{topic:'General Discussion',sentences:sents}];
    const win=Math.max(3,Math.floor(sents.length/8));
    const segs=[]; let cur=[], prevKW=new Set();
    sents.forEach((s,i)=>{
      const toks=tokenize(s).filter(w=>!STOP.has(w));
      const kw=new Set(toks.slice(0,5));
      const overlap=[...kw].filter(k=>prevKW.has(k)).length;
      const sim=prevKW.size?overlap/prevKW.size:0;
      if(i>0&&sim<0.15&&cur.length>=win){
        const top=keywords(cur.join(' '),3).map(k=>cap(k.word)).join(' / ');
        segs.push({topic:top||'Discussion',sentences:cur});
        cur=[];
      }
      cur.push(s); prevKW=kw;
    });
    if(cur.length>0){
      const top=keywords(cur.join(' '),3).map(k=>cap(k.word)).join(' / ');
      segs.push({topic:top||'Closing',sentences:cur});
    }
    return segs;
  };

  /* Stats */
  const stats = (text, utterances) => {
    const words=tokenize(text), sents=getSentences(text);
    return {
      wordCount:words.length, sentenceCount:sents.length,
      speakerCount:utterances?new Set(utterances.map(u=>u.speaker)).size:0,
      utteranceCount:utterances?utterances.length:0,
      estimatedDuration:Math.round(words.length/130),
      avgSentLen:Math.round(words.length/Math.max(sents.length,1))
    };
  };

  /* Syllable count for readability */
  const syllables = w => {
    w=w.toLowerCase().replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/,'').replace(/^y/,'');
    return Math.max(1,(w.match(/[aeiouy]{1,2}/g)||[]).length);
  };

  const readability = text => {
    const words=tokenize(text), sents=getSentences(text);
    const sy=words.reduce((a,w)=>a+syllables(w),0);
    const fk=206.835-(1.015*words.length/Math.max(sents.length,1))-(84.6*sy/Math.max(words.length,1));
    const s=Math.max(0,Math.min(100,Math.round(fk)));
    return {score:s,label:s>70?'Easy':s>50?'Moderate':'Complex'};
  };

  /* Main analyze */
  const analyze = (text, summaryLen=5) => {
    if(!text||text.trim().length<50) return {error:'Text too short. Please provide a longer transcript.'};
    const {speakers,utterances}=parseSpeakers(text);
    const has=Object.keys(speakers).length>0;
    const bodyText=has?utterances.map(u=>u.speech).join(' '):text;
    const sumSents=summarize(text,summaryLen);
    return {
      summary:sumSents.join(' '), summarySentences:sumSents,
      keywords:keywords(bodyText), keyPoints:keyPoints(text),
      actionItems:actionItems(text,speakers), decisions:decisions(text),
      topics:segmentTopics(text), speakers, utterances,
      sentiment:sentiment(bodyText), speakerSentiments:speakerSentiments(speakers),
      readability:readability(text), stats:stats(text,utterances),
      hasSpeakers:has, timestamp:new Date().toISOString()
    };
  };

  return {analyze};
})();
