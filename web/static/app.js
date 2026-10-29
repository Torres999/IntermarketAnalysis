const palette = ["#4da3ff", "#ffb347", "#77dd77", "#ff6961", "#b19cd9", "#f472b6", "#34d399", "#a78bfa"];

let seriesCatalog = [];

const GROUP_ORDER = [
  ["equity_spot", "现货指数"],
  ["equity_future", "股指期货"],
  ["commodity", "大宗商品主连"],
  ["commodity_index", "大宗综合"],
  ["bond_yield", "债券收益率"],
  ["bond_price", "债券价格"],
  ["fx_index", "人民币汇率指数"],
];

const PRESETS = {
  broad: {
    panel: 1,
    ids: ["csi300", "sse_composite", "chinext", "szse_component"],
    normalize: true,
  },
  style: {
    panel: 1,
    ids: ["sse50", "csi300", "csi500", "csi1000"],
    normalize: true,
  },
  if_pair: {
    panel: 1,
    ids: ["future_if", "csi300"],
    normalize: true,
  },
  three_leg: {
    panel: 1,
    ids: ["csi300", "cn10y", "rmb_cfets"],
    normalize: true,
  },
  four_leg: {
    panel: 1,
    ids: ["csi300", "cn10y", "rmb_cfets", "nh_commodity"],
    normalize: true,
  },
};

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
  if (!el) return;
  if (!text) {
    el.textContent = "";
    el.className = "status-line hidden";
    return;
  }
  el.textContent = text;
  el.className = "status-line" + (level ? ` ${level}` : "");
}

function setChartLoadStatus(text, level = "") {
  const el = document.getElementById("chartLoadStatus");
  if (!el) return;
  el.textContent = text || "";
  el.className = "chart-load-status" + (level ? ` ${level}` : "");
}

function setPanelStatus(panel, text, level = "") {
  const el = document.getElementById(panel.panelStatusId);
  if (!el) return;
  if (!text) {
    el.textContent = "";
    el.className = "panel-status panel-status--quiet";
    el.setAttribute("aria-hidden", "true");
    return;
  }
  el.textContent = text;
  el.className =
    "panel-status" + (level ? ` ${level}` : "") + (level === "warn" ? "" : " panel-status--quiet");
  el.setAttribute("aria-hidden", level === "warn" ? "false" : "true");
}

function showEmpty(panel, show) {
  document.getElementById(panel.emptyHintId).classList.toggle("hidden", !show);
}

function useNormalizedScale() {
  return document.getElementById("normalizeScale")?.checked !== false;
}

function setSelection(panelIndex, ids) {
  const select = document.getElementById(panels[panelIndex].seriesSelectId);
  const want = new Set(ids);
  for (const opt of select.options) {
    opt.selected = want.has(opt.value);
  }
}

async function loadSeries() {
  const resp = await fetch("/api/series");
  if (!resp.ok) throw new Error("无法加载指标列表");
  const payload = await resp.json();
  seriesCatalog = payload.series || [];

  for (const panel of panels) {
    const select = document.getElementById(panel.seriesSelectId);
    select.innerHTML = "";
    for (const [key, label] of GROUP_ORDER) {
      const items = seriesCatalog.filter((s) => s.asset_class === key);
      if (!items.length) continue;
      const group = document.createElement("optgroup");
      group.label = label;
      for (const item of items) {
        const opt = document.createElement("option");
        opt.value = item.id;
        opt.textContent = `${item.name}${item.unit ? ` (${item.unit})` : ""}`;
        group.appendChild(opt);
      }
      select.appendChild(group);
    }
  }
}

function selectedSeriesIds(panel) {
  const select = document.getElementById(panel.seriesSelectId);
  return Array.from(select.selectedOptions).map((o) => o.value);
}

function indexBase100(values, labels) {
  const first = labels.find((d) => values.has(d));
  if (!first) return labels.map(() => null);
  const base = values.get(first);
  if (!base) return labels.map(() => null);
  return labels.map((d) => {
    const v = values.get(d);
    return v == null ? null : (v / base) * 100;
  });
}

function buildAlignedSeries(ids, data, normalize) {
  const dateSet = new Set();
  for (const id of ids) {
    for (const p of data[id] || []) dateSet.add(p.date);
  }
  const labels = Array.from(dateSet).sort();
  const datasets = ids.map((id, idx) => {
    const meta = seriesCatalog.find((s) => s.id === id);
    const map = new Map((data[id] || []).map((p) => [p.date, p.value]));
    const raw = labels.map((d) => (map.has(d) ? map.get(d) : null));
    const seriesData = normalize ? indexBase100(map, labels) : raw;
    return {
      label: meta ? meta.name : id,
      data: seriesData,
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
    tooltip: { mode: "index", intersect: false },
  },
};

async function loadChart(panel, seriesIds = null) {
  if (typeof Chart === "undefined") {
    setHeaderStatus("Chart.js 未加载", "warn");
    setPanelStatus(panel, "Chart.js 未加载", "warn");
    showEmpty(panel, true);
    return null;
  }

  const from = document.getElementById(panel.fromDateId).value;
  const to = document.getElementById(panel.toDateId).value;
  const ids =
    seriesIds && seriesIds.length
      ? seriesIds
      : selectedSeriesIds(panel);
  if (!ids.length) {
    setPanelStatus(panel, "请至少选择一个指标", "warn");
    showEmpty(panel, true);
    return null;
  }

  const params = new URLSearchParams();
  ids.forEach((id) => params.append("series", id));
  if (from) params.set("from", from);
  if (to) params.set("to", to);

  const resp = await fetch(`/api/data?${params.toString()}`);
  if (!resp.ok) throw new Error("无法加载序列数据");
  const payload = await resp.json();
  const data = payload.data || {};
  const total = countPoints(ids, data);
  const normalize = useNormalizedScale();
  const { labels, datasets } = buildAlignedSeries(ids, data, normalize);

  showEmpty(panel, total === 0);
  if (total === 0) {
    if (panel.chart) panel.chart.destroy();
    panel.chart = null;
    setPanelStatus(panel, "当前区间无数据", "warn");
    return null;
  }

  const ctx = document.getElementById(panel.chartCanvasId);
  if (panel.chart) panel.chart.destroy();
  panel.chart = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: chartOptions,
  });

  attachChartSyncHandlers(panel);
  setPanelStatus(panel, "", "");

  if (panel === panels[0]) {
    loadAnalysisSummary(from, to).catch(() => {});
  }

  const mode = normalize ? "归一化" : "原始点位";
  return `${mode} · ${total} 点 · ${from || "…"} 至 ${to || "…"}`;
}

const REGIME_LABEL = {
  aligned_risk_on: "三腿偏 risk-on（同步）",
  aligned_risk_off: "三腿偏 risk-off（同步）",
  decoupled: "三腿脱钩（宜降预期）",
  unknown: "数据不足",
};

async function loadAnalysisSummary(from, to) {
  const el = document.getElementById("analysisSummary");
  if (!el) return;
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const resp = await fetch(`/api/analysis/summary?${params.toString()}`);
  if (!resp.ok) {
    el.textContent = "分析 API 不可用，请先运行 scrape 填充新序列。";
    return;
  }
  const body = await resp.json();
  const sync = body.four_leg_sync || body.three_leg_sync || {};
  const regime = REGIME_LABEL[sync.regime] || sync.regime || "—";
  const smt = (body.index_smt_events || [])[0];
  const smtText = smt
    ? `最近指数 SMT：${smt.date} ${smt.kind}（${smt.leader}）`
    : "最近无明显宽基 SMT 事件";
  const spread = (body.future_spot_spreads || []).find((s) => s.future === "future_if");
  const spreadText =
    spread && spread.status === "ok" && spread.spread_change_vs_prior != null
      ? `IF–CSI300 价差 20d 变化：${spread.spread_change_vs_prior.toFixed(2)}`
      : "IF–CSI300 期现：数据待抓取";
  const missing = (body.missing_series || []).length
    ? `缺失序列：${body.missing_series.join(", ")}`
    : "";
  el.textContent = [regime, smtText, spreadText, missing].filter(Boolean).join(" · ");
}

function setDefaultDates(panel) {
  const to = new Date();
  const from = new Date();
  from.setFullYear(from.getFullYear() - 5);
  document.getElementById(panel.toDateId).value = to.toISOString().slice(0, 10);
  document.getElementById(panel.fromDateId).value = from.toISOString().slice(0, 10);
}

function syncDatesFromPanel1() {
  const from = document.getElementById(panels[0].fromDateId).value;
  const to = document.getElementById(panels[0].toDateId).value;
  document.getElementById(panels[1].fromDateId).value = from;
  document.getElementById(panels[1].toDateId).value = to;
}

/** Mirror panel 1 selection onto both charts (presets / first load). */
async function applySyncedCharts(seriesIds, { showLoadSummary = false } = {}) {
  syncDatesFromPanel1();
  setSelection(0, seriesIds);
  setSelection(1, seriesIds);
  const [summary] = await Promise.all([
    loadChart(panels[0], seriesIds),
    loadChart(panels[1], seriesIds),
  ]);
  if (showLoadSummary && summary) {
    setChartLoadStatus(summary, "ok");
  }
}

async function applyPreset(name, { showLoadSummary = false } = {}) {
  const preset = PRESETS[name];
  if (!preset) return;
  if (preset.normalize != null) {
    document.getElementById("normalizeScale").checked = preset.normalize;
  }
  const missing = preset.ids.filter(
    (id) => !seriesCatalog.some((s) => s.id === id),
  );
  if (missing.length) {
    const msg = `预设含未知指标：${missing.join(", ")}`;
    setPanelStatus(panels[0], msg, "warn");
    setPanelStatus(panels[1], msg, "warn");
    if (showLoadSummary) setChartLoadStatus(msg, "warn");
  }
  try {
    await applySyncedCharts(preset.ids, { showLoadSummary });
  } catch (err) {
    const message = err.message || "加载失败";
    setPanelStatus(panels[0], message, "warn");
    setPanelStatus(panels[1], message, "warn");
    if (showLoadSummary) setChartLoadStatus(message, "warn");
  }
}

for (const panel of panels) {
  document.getElementById(panel.applyBtnId).addEventListener("click", () => {
    loadChart(panel).catch((err) => {
      setPanelStatus(panel, err.message || "加载失败", "warn");
    });
  });
  attachChartSyncHandlers(panel);
}

document.getElementById("normalizeScale")?.addEventListener("change", async () => {
  const statusEl = document.getElementById("chartLoadStatus");
  const refreshSummary = Boolean(statusEl?.textContent?.trim());
  try {
    const ids0 = selectedSeriesIds(panels[0]);
    const ids1 = selectedSeriesIds(panels[1]);
    if (ids0.length && JSON.stringify(ids0) === JSON.stringify(ids1)) {
      await applySyncedCharts(ids0, { showLoadSummary: refreshSummary });
      return;
    }
    const results = await Promise.all(
      panels.filter((p) => p.chart).map((p) => loadChart(p)),
    );
    if (refreshSummary && results[0]) {
      setChartLoadStatus(results[0], "ok");
    }
  } catch {
    /* ignore */
  }
});

for (const btn of document.querySelectorAll(".preset-btn")) {
  btn.addEventListener("click", () =>
    applyPreset(btn.dataset.preset, { showLoadSummary: true }),
  );
}

(async function init() {
  try {
    setChartLoadStatus("", "");
    setHeaderStatus("", "");
    for (const panel of panels) setDefaultDates(panel);
    await loadSeries();
    await applySyncedCharts(PRESETS.broad.ids);
  } catch (err) {
    setHeaderStatus(err.message || "初始化失败", "warn");
    for (const panel of panels) showEmpty(panel, true);
  }
})();
