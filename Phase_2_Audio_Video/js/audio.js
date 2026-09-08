/* Audio Module - Web Audio API + Simulated STT */
const Audio = (() => {
  let mediaRecorder = null, chunks = [], stream = null, animFrame = null;

  const DEMO_TRANSCRIPT = `Sarah: Good morning everyone, let's get started with today's product review meeting.
James: Thanks Sarah. I want to begin by flagging that the backend API refactoring will be completed by March 28th.
Sarah: That's important, James. How does this affect our launch timeline?
James: We may need to push by about two weeks. I'll send a detailed timeline to everyone by end of day today.
Priya: From a marketing perspective, we've already started the pre-launch campaign. Delaying would mean missing the Apple feature window closing on April 10th.
Alex: James, can we prioritize the API work this sprint to meet the April 5th target?
James: Yes, I'll reassign two engineers from infrastructure. We should be fine.
Sarah: Great. We've decided to prioritize API work to meet April 5th. James please coordinate with the team and report back by Thursday.
David: The new onboarding flow designs are ready. I'll share the Figma prototype with James today.
Alex: David, please also prepare the new UI presentation for the board meeting on March 22nd.
David: Absolutely, I'll have it ready by March 20th to allow time for review.
Priya: We should allocate at least $50,000 for the Q2 marketing budget. I need approval by end of this week.
Sarah: I'll take that to finance today and confirm with you by Wednesday, Priya.
Alex: I propose we set aside $30,000 for AI-powered recommendation features. The competitive landscape demands it.
Sarah: Agreed. Let's approve the $30,000 AI budget. James, please create a technical spec for the recommendation engine by next Friday.
Alex: Also ensure all key user events are tracked before the April 5th launch.
Priya: We should schedule a launch readiness review for March 30th to identify final blockers.
Sarah: Great idea. I'll send calendar invites for March 30th at 10 AM. Let's reconvene then.`;

  const initWaveform = (canvas) => {
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(167,139,250,0.3)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let x = 0; x < W; x++) {
      const y = H/2 + Math.sin(x * 0.05) * 3;
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  };

  const animateWaveform = (canvas, analyser) => {
    if (!analyser) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const buf = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      animFrame = requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(buf);
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = '#a78bfa';
      ctx.lineWidth = 2;
      ctx.beginPath();
      const step = W / buf.length;
      buf.forEach((v, i) => {
        const y = (v / 128) * H/2;
        i === 0 ? ctx.moveTo(0, y) : ctx.lineTo(i * step, y);
      });
      ctx.stroke();
    };
    draw();
  };

  const startRecording = async (canvas, onStatus) => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({audio: true});
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      const src = audioCtx.createMediaStreamSource(stream);
      src.connect(analyser);
      animateWaveform(canvas, analyser);
      chunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = e => chunks.push(e.data);
      mediaRecorder.start();
      onStatus('recording');
    } catch (e) {
      onStatus('error', e.message || 'Microphone access denied.');
    }
  };

  const stopRecording = (onComplete) => {
    if (!mediaRecorder) return;
    cancelAnimationFrame(animFrame);
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      // Simulate STT with demo transcript
      setTimeout(() => onComplete(DEMO_TRANSCRIPT), 800);
    };
    mediaRecorder.stop();
  };

  const handleFileUpload = (file, canvas, onComplete, onStatus) => {
    if (!file) return;
    const validTypes = ['audio/mp3','audio/mpeg','audio/wav','audio/ogg','audio/m4a','audio/mp4','video/mp4'];
    if (!validTypes.some(t => file.type.includes(t.split('/')[1])) && !file.name.match(/\.(mp3|wav|ogg|m4a|mp4)$/i)) {
      onStatus('error', 'Unsupported file format. Please use MP3, WAV, OGG, or M4A.');
      return;
    }
    onStatus('processing');
    // Draw simulated waveform
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    let t = 0;
    const sim = setInterval(() => {
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < W; x++) {
        const y = H/2 + Math.sin(x*0.04+t)*20*Math.random() + Math.sin(x*0.1+t*2)*10;
        x===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
      }
      ctx.stroke();
      t += 0.15;
    }, 50);
    setTimeout(() => {
      clearInterval(sim);
      onComplete(DEMO_TRANSCRIPT + '\n\n[Uploaded file: ' + file.name + ']');
    }, 2500);
  };

  return {startRecording, stopRecording, handleFileUpload, initWaveform};
})();
