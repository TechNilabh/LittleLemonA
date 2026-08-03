document.addEventListener('DOMContentLoaded', () => {

  // -------------------------------------------------------------------------
  // 1. Hero Animated Background — Index page only
  // -------------------------------------------------------------------------
  const heroCanvas = document.getElementById('heroBgCanvas');
  if (heroCanvas) {
    const ctx = heroCanvas.getContext('2d');
    let step = 0;

    function resizeCanvas() {
      heroCanvas.width  = heroCanvas.offsetWidth;
      heroCanvas.height = heroCanvas.offsetHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    function getPoints(w, h) {
      return [
        { x: 0,        y: h * 0.70 },
        { x: w * 0.12, y: h * 0.60 },
        { x: w * 0.25, y: h * 0.40 },
        { x: w * 0.38, y: h * 0.55 },
        { x: w * 0.52, y: h * 0.28 },
        { x: w * 0.65, y: h * 0.45 },
        { x: w * 0.80, y: h * 0.20 },
        { x: w,        y: h * 0.30 },
      ];
    }

    function drawHeroBg() {
      const w = heroCanvas.width;
      const h = heroCanvas.height;
      if (w === 0 || h === 0) { requestAnimationFrame(drawHeroBg); return; }

      ctx.clearRect(0, 0, w, h);

      // Faint grid
      ctx.strokeStyle = 'rgba(38, 42, 54, 0.5)';
      ctx.lineWidth = 1;
      const gridSize = 44;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
      }

      // Animated curve — recompute points each frame so resize is instant
      const pts = getPoints(w, h);

      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 1; i < pts.length; i++) {
        const cx = (pts[i - 1].x + pts[i].x) / 2;
        const cy = (pts[i - 1].y + pts[i].y) / 2;
        ctx.quadraticCurveTo(pts[i - 1].x, pts[i - 1].y, cx, cy);
      }
      ctx.strokeStyle = 'rgba(124, 58, 237, 0.30)';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Pulsing nodes
      pts.forEach((p, idx) => {
        const r = Math.sin(step * 1.2 + idx * 0.8) * 2.5 + 4;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(124, 58, 237, 0.55)';
        ctx.fill();
      });

      step += 0.025;
      requestAnimationFrame(drawHeroBg);
    }
    drawHeroBg();
  }

  // -------------------------------------------------------------------------
  // 2. Chart.js Dashboard — dashboard page only
  // -------------------------------------------------------------------------
  const dataHolder = document.getElementById('statsDataHolder');
  if (!dataHolder) return;  // Not on dashboard page

  let ratingLabels, ratingValues, tagLabels, tagValues, diffLabels, diffValues;
  try {
    ratingLabels = JSON.parse(dataHolder.getAttribute('data-rating-labels') || '[]');
    ratingValues = JSON.parse(dataHolder.getAttribute('data-rating-values') || '[]');
    tagLabels    = JSON.parse(dataHolder.getAttribute('data-tag-labels')    || '[]');
    tagValues    = JSON.parse(dataHolder.getAttribute('data-tag-values')    || '[]');
    diffLabels   = JSON.parse(dataHolder.getAttribute('data-diff-labels')   || '[]');
    diffValues   = JSON.parse(dataHolder.getAttribute('data-diff-values')   || '[]');
  } catch (e) {
    console.error('[CPInsight] Failed to parse chart data from data-* attributes:', e);
    return;
  }

  // Shared defaults
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'JetBrains Mono', monospace";
  Chart.defaults.font.size = 11;

  const GRID_COLOR  = '#262a36';
  const ACCENT      = '#7c3aed';
  const ACCENT_FILL = 'rgba(124, 58, 237, 0.10)';

  // -- Rating History (Line) ------------------------------------------------
  const ratingCanvas = document.getElementById('ratingChart');
  if (ratingCanvas) {
    if (ratingValues.length > 0) {
      new Chart(ratingCanvas, {
        type: 'line',
        data: {
          labels: ratingLabels,
          datasets: [{
            label: 'Rating',
            data: ratingValues,
            borderColor: ACCENT,
            backgroundColor: ACCENT_FILL,
            borderWidth: 2,
            fill: true,
            tension: 0.15,
            pointBackgroundColor: ACCENT,
            pointRadius: 4,
            pointHoverRadius: 7,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: GRID_COLOR } },
            y: { grid: { color: GRID_COLOR } },
          },
        },
      });
    } else {
      // Empty state message inside the canvas area
      const ctx2 = ratingCanvas.getContext('2d');
      ctx2.fillStyle = '#64748b';
      ctx2.font = "14px 'JetBrains Mono', monospace";
      ctx2.textAlign = 'center';
      ctx2.fillText('No contest history yet', ratingCanvas.offsetWidth / 2, 120);
    }
  }

  // -- Top Tags (Horizontal Bar) --------------------------------------------
  const tagsCanvas = document.getElementById('tagsChart');
  if (tagsCanvas) {
    if (tagValues.length > 0) {
      new Chart(tagsCanvas, {
        type: 'bar',
        data: {
          labels: tagLabels,
          datasets: [{
            label: 'Problems Solved',
            data: tagValues,
            backgroundColor: ACCENT,
            borderColor: ACCENT,
            borderWidth: 1,
            borderRadius: 2,
          }],
        },
        options: {
          indexAxis: 'y',           // horizontal bars — easier to read tag names
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: GRID_COLOR } },
            y: { grid: { display: false } },
          },
        },
      });
    } else {
      const ctx2 = tagsCanvas.getContext('2d');
      ctx2.fillStyle = '#64748b';
      ctx2.font = "13px 'JetBrains Mono', monospace";
      ctx2.textAlign = 'center';
      ctx2.fillText('No solved problems yet', tagsCanvas.offsetWidth / 2, 100);
    }
  }

  // -- Difficulty Distribution (Doughnut) -----------------------------------
  const diffCanvas = document.getElementById('diffChart');
  if (diffCanvas) {
    const hasData = diffValues.some(v => v > 0);
    if (hasData) {
      new Chart(diffCanvas, {
        type: 'doughnut',
        data: {
          labels: diffLabels,
          datasets: [{
            data: diffValues,
            backgroundColor: ['#94a3b8', '#47cf73', '#03a9f4', '#aa00aa', '#f44336'],
            borderWidth: 2,
            borderColor: '#161922',
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: { boxWidth: 12, padding: 12, color: '#94a3b8' },
            },
          },
        },
      });
    } else {
      const ctx2 = diffCanvas.getContext('2d');
      ctx2.fillStyle = '#64748b';
      ctx2.font = "13px 'JetBrains Mono', monospace";
      ctx2.textAlign = 'center';
      ctx2.fillText('No rated problems yet', diffCanvas.offsetWidth / 2, 100);
    }
  }

});
