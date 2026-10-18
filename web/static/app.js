const palette = ["#4da3ff", "#ffb347", "#77dd77", "#ff6961", "#b19cd9"];

let seriesCatalog = [];

/** 竖线对齐到同一屏幕 X（两图左右边距一致时上下重合） */
const syncCrosshair = { active: false, anchorX: null };

const panels = [
  {
    fromDateId: "fromDate1",
    toDateId: "toDate1",
    seriesSelectId: "seriesSelect1",
    applyBtnId: "applyBtn1",
    chartCanvasId: "marketChart1",
    emptyHintId: "emptyHint1",
    panelStatusId: "panelStatus1",
    chart: null,
  },
  {
    fromDateId: "fromDate2",
    toDateId: "toDate2",
    seriesSelectId: "seriesSelect2",
    applyBtnId: "applyBtn2",
    chartCanvasId: "marketChart2",
    emptyHintId: "emptyHint2",
    panelStatusId: "panelStatus2",
    chart: null,
  },
];

const syncCrosshairPlugin = {
  id: "syncCrosshair",
  afterDatasetsDraw(chart) {
    if (!syncCrosshair.active || syncCrosshair.anchorX == null) return;
    const drawX = canvasXFromClient(chart, syncCrosshair.anchorX);
    const { top, bottom } = chart.chartArea;
    if (bottom <= top) return;
    if (drawX < 0 || drawX > chart.width) return;

    const ctx = chart.ctx;
    ctx.save();
    ctx.strokeStyle = "rgba(186, 198, 218, 0.92)";
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(drawX, top);
    ctx.lineTo(drawX, bottom);
    ctx.stroke();
    ctx.restore();
  },
};

if (typeof Chart !== "undefined") {
  Chart.register(syncCrosshairPlugin);
}

function canvasXFromClient(chart, clientX) {
  const canvas = chart.canvas;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width) return 0;
  return ((clientX - rect.left) / rect.width) * chart.width;
}

function redrawSyncCrosshair() {
  for (const panel of panels) {
    if (panel.chart) panel.chart.update("none");
  }
}

function clearSyncCrosshair() {
  syncCrosshair.active = false;
  syncCrosshair.anchorX = null;
  redrawSyncCrosshair();
}

function isPointerOverAnyChart() {
  return panels.some((p) => {
    const wrap = document.getElementById(p.chartCanvasId)?.closest(".chart-wrap");
    return Boolean(wrap?.matches(":hover"));
  });
}

function attachChartSyncHandlers(panel) {
  const canvas = document.getElementById(panel.chartCanvasId);
  const wrap = canvas?.closest(".chart-wrap");
  if (!wrap || wrap.dataset.syncBound === "1") return;
  wrap.dataset.syncBound = "1";

  wrap.addEventListener("mouseenter", () => {
    syncCrosshair.active = true;
    if (syncCrosshair.anchorX != null) redrawSyncCrosshair();
  });

  wrap.addEventListener("mouseleave", () => {
    window.requestAnimationFrame(() => {
      if (!isPointerOverAnyChart()) clearSyncCrosshair();
    });
  });

  wrap.addEventListener("mousemove", (event) => {
    if (!panel.chart) return;
    syncCrosshair.active = true;
    const x = event.clientX;
    if (syncCrosshair.anchorX !== x) {
      syncCrosshair.anchorX = x;
      redrawSyncCrosshair();
    }
  });
}

function setHeaderStatus(text, level = "") {
  const el = document.getElementById("statusLine");
  el.textContent = text;
  el.className = "status-line" + (level ? ` ${level}` : "");
}

function setPanelStatus(panel, text, level = "") {
  const el = document.getElementById(panel.panelStatusId);
  el.textContent = text;
  el.className = "panel-status" + (level ? ` ${level}` : "");
}

function showEmpty(panel, show) {
  document.getElementById(panel.emptyHintId).classList.toggle("hidden", !show);
}

async function loadSeries() {
  const resp = await fetch("/api/series");
  if (!resp.ok) throw new Error("无法加载指标列表");
  const payload = await resp.json();
  seriesCatalog = payload.series || [];
  for (const panel of panels) {
    const select = document.getElementById(panel.seriesSelectId);
    select.innerHTML = "";
    for (const item of seriesCatalog) {
      const opt = document.createElement("option");
      opt.value = item.id;
      opt.textContent = `${item.name}${item.unit ? ` (${item.unit})` : ""}`;
      opt.selected = true;
      select.appendChild(opt);
    }
  }
}

function selectedSeriesIds(panel) {
  const select = document.getElementById(panel.seriesSelectId);
  return Array.from(select.selectedOptions).map((o) => o.value);
}

function buildAlignedSeries(ids, data) {
  const dateSet = new Set();
  for (const id of ids) {
    for (const p of data[id] || []) dateSet.add(p.date);
  }
  const labels = Array.from(dateSet).sort();
  const datasets = ids.map((id, idx) => {
    const meta = seriesCatalog.find((s) => s.id === id);
    const map = new Map((data[id] || []).map((p) => [p.date, p.value]));
    return {
      label: meta ? meta.name : id,
      data: labels.map((d) => (map.has(d) ? map.get(d) : null)),
      borderColor: palette[idx % palette.length],
      backgroundColor: palette[idx % palette.length] + "33",
      spanGaps: true,
      tension: 0.15,
      pointRadius: labels.length > 120 ? 0 : 2,
      borderWidth: 2,
      fill: false,
    };
  });
  return { labels, datasets };
}

function countPoints(ids, data) {
  let n = 0;
  for (const id of ids) n += (data[id] || []).length;
  return n;
}

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index", intersect: false },
  scales: {
    x: {
      ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 14 },
      grid: { color: "rgba(148,163,184,0.12)" },
    },
    y: {
      beginAtZero: false,
      grid: { color: "rgba(148,163,184,0.12)" },
    },
  },
  plugins: {
    legend: {
      position: "bottom",
      labels: { color: "#cbd5e1", boxWidth: 12, padding: 16 },
    },
    tooltip: {
      mode: "index",
      intersect: false,
    },
  },
};

async function loadChart(panel) {
  if (typeof Chart === "undefined") {
    setHeaderStatus("Chart.js 未加载，请检查 /static/chart.umd.min.js", "warn");
    setPanelStatus(panel, "Chart.js 未加载", "warn");
    showEmpty(panel, true);
    return;
  }

  const from = document.getElementById(panel.fromDateId).value;
  const to = document.getElementById(panel.toDateId).value;
  const ids = selectedSeriesIds(panel);
  if (!ids.length) {
    setPanelStatus(panel, "请至少选择一个指标", "warn");
    showEmpty(panel, true);
    return;
  }

  setPanelStatus(panel, "正在加载数据…");
  const params = new URLSearchParams();
  ids.forEach((id) => params.append("series", id));
  if (from) params.set("from", from);
  if (to) params.set("to", to);

  const resp = await fetch(`/api/data?${params.toString()}`);
  if (!resp.ok) throw new Error("无法加载序列数据");
  const payload = await resp.json();
  const data = payload.data || {};
  const total = countPoints(ids, data);
  const { labels, datasets } = buildAlignedSeries(ids, data);

  showEmpty(panel, total === 0);
  if (total === 0) {
    if (panel.chart) panel.chart.destroy();
    panel.chart = null;
    setPanelStatus(panel, "当前区间无数据", "warn");
    return;
  }

  const ctx = document.getElementById(panel.chartCanvasId);
  if (panel.chart) panel.chart.destroy();
  panel.chart = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: chartOptions,
  });

  attachChartSyncHandlers(panel);

  const msg = `已加载 ${total} 个数据点 · ${from || "…"} 至 ${to || "…"}`;
  setPanelStatus(panel, msg, "ok");
  setHeaderStatus(msg, "ok");
}

function setDefaultDates(panel) {
  const to = new Date();
  const from = new Date();
  from.setFullYear(from.getFullYear() - 5);
  document.getElementById(panel.toDateId).value = to.toISOString().slice(0, 10);
  document.getElementById(panel.fromDateId).value = from.toISOString().slice(0, 10);
}

for (const panel of panels) {
  document.getElementById(panel.applyBtnId).addEventListener("click", () => {
    loadChart(panel).catch((err) => {
      setPanelStatus(panel, err.message || "加载失败", "warn");
      setHeaderStatus(err.message || "加载失败", "warn");
    });
  });
  attachChartSyncHandlers(panel);
}

(async function init() {
  try {
    for (const panel of panels) setDefaultDates(panel);
    await loadSeries();
    await Promise.all(panels.map((panel) => loadChart(panel)));
    setHeaderStatus("两个图表已就绪", "ok");
  } catch (err) {
    setHeaderStatus(err.message || "初始化失败", "warn");
    for (const panel of panels) showEmpty(panel, true);
  }
})();
