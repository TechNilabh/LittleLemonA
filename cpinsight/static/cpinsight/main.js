document.addEventListener('DOMContentLoaded', () => {
  // 1. Hero Animated Background Line Graph (Index page)
  const heroCanvas = document.getElementById('heroBgCanvas');
  if (heroCanvas) {
    const ctx = heroCanvas.getContext('2d');
    let width = (heroCanvas.width = heroCanvas.offsetWidth);
    let height = (heroCanvas.height = heroCanvas.offsetHeight);

    window.addEventListener('resize', () => {
      width = heroCanvas.width = heroCanvas.offsetWidth;
      height = heroCanvas.height = heroCanvas.offsetHeight;
    });

    let step = 0;
    const points = [
      { x: 0, y: height * 0.7 },
      { x: width * 0.15, y: height * 0.65 },
      { x: width * 0.3, y: height * 0.4 },
      { x: width * 0.45, y: height * 0.55 },
      { x: width * 0.6, y: height * 0.3 },
      { x: width * 0.75, y: height * 0.45 },
      { x: width * 0.9, y: height * 0.2 },
      { x: width, y: height * 0.25 }
    ];

    function drawHeroBg() {
      ctx.clearRect(0, 0, width, height);

      // Grid background lines
      ctx.strokeStyle = 'rgba(38, 42, 54, 0.4)';
      ctx.lineWidth = 1;
      const gridSize = 40;

      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Animated Line
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const cx = (points[i - 1].x + points[i].x) / 2;
        const cy = (points[i - 1].y + points[i].y) / 2;
        ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, cx, cy);
      }

      ctx.strokeStyle = 'rgba(124, 58, 237, 0.35)';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Glowing pulse nodes
      points.forEach((p, idx) => {
        const pulse = Math.sin(step + idx) * 3 + 4;
        ctx.beginPath();
        ctx.arc(p.x, p.y, pulse, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(124, 58, 237, 0.6)';
        ctx.fill();
      });

      step += 0.03;
      requestAnimationFrame(drawHeroBg);
    }
    drawHeroBg();
  }

  // 2. Chart.js Dashboard Renderers
  const chartContainers = document.querySelectorAll('[data-ratings]');
  if (chartContainers.length > 0) {
    const container = chartContainers[0];

    try {
      const ratingLabels = JSON.parse(container.getAttribute('data-rating-labels') || '[]');
      const ratingValues = JSON.parse(container.getAttribute('data-rating-values') || '[]');
      const tagLabels = JSON.parse(container.getAttribute('data-tag-labels') || '[]');
      const tagValues = JSON.parse(container.getAttribute('data-tag-values') || '[]');
      const diffLabels = JSON.parse(container.getAttribute('data-diff-labels') || '[]');
      const diffValues = JSON.parse(container.getAttribute('data-diff-values') || '[]');

      // Common brutalist chart styling
      Chart.defaults.color = '#94a3b8';
      Chart.defaults.font.family = "'JetBrains Mono', monospace";
      Chart.defaults.font.size = 11;

      // Rating History Line Chart
      const ratingCtx = document.getElementById('ratingChart');
      if (ratingCtx && ratingValues.length > 0) {
        new Chart(ratingCtx, {
          type: 'line',
          data: {
            labels: ratingLabels,
            datasets: [{
              label: 'Rating',
              data: ratingValues,
              borderColor: '#7c3aed',
              backgroundColor: 'rgba(124, 58, 237, 0.1)',
              borderWidth: 2,
              fill: true,
              tension: 0.1,
              pointBackgroundColor: '#7c3aed',
              pointRadius: 3,
              pointHoverRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              x: { grid: { color: '#262a36' } },
              y: { grid: { color: '#262a36' } }
            }
          }
        });
      }

      // Tags Bar Chart
      const tagsCtx = document.getElementById('tagsChart');
      if (tagsCtx && tagValues.length > 0) {
        new Chart(tagsCtx, {
          type: 'bar',
          data: {
            labels: tagLabels,
            datasets: [{
              label: 'Solved',
              data: tagValues,
              backgroundColor: '#7c3aed',
              borderColor: '#7c3aed',
              borderWidth: 1,
              borderRadius: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              x: { grid: { display: false } },
              y: { grid: { color: '#262a36' } }
            }
          }
        });
      }

      // Difficulty Donut Chart
      const diffCtx = document.getElementById('diffChart');
      if (diffCtx && diffValues.length > 0) {
        new Chart(diffCtx, {
          type: 'doughnut',
          data: {
            labels: diffLabels,
            datasets: [{
              data: diffValues,
              backgroundColor: [
                '#94a3b8',
                '#47cf73',
                '#03a9f4',
                '#aa00aa',
                '#f44336'
              ],
              borderWidth: 2,
              borderColor: '#161922'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'right',
                labels: { boxWidth: 12, padding: 15 }
              }
            }
          }
        });
      }
    } catch (e) {
      console.error('Failed to parse chart data JSON', e);
    }
  }
});
