"""patch_decay_chart.py — chartWatchDecay JS 교체 (수치 상시 표시, 색 강화, 범례 제거)"""
content = open('park.ingyeom/reports/audits/build_aarrr_visual_guide.py', encoding='utf-8').read()

OLD_CHART = """// 7. Watch decay by segment
new Chart(C('chartWatchDecay'), {
  type: 'line',
  data: {
    labels: ['W1 (day0~6)', 'W2 (day7~13)', 'W3 (day14~20)'],
    datasets: [
      { label: '①high_risk_week3_inactive', data: [89.3, 31.5, 6.6], borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,.15)', tension: .3, fill: false },
      { label: '②high_risk_only_w1_cold', data: [114.1, 25.4, 44.3], borderColor: '#f97316', backgroundColor: 'rgba(249,115,22,.15)', tension: .3, fill: false },
      { label: '③high_risk_low_activity', data: [0.0, 0.04, 19.0], borderColor: '#dc2626', backgroundColor: 'rgba(220,38,38,.15)', tension: .3, fill: false, borderDash: [5,4] },
      { label: '④medium_risk_decay', data: [139.6, 137.8, 33.0], borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,.15)', tension: .3, fill: false },
      { label: '⑤content_preference', data: [119.5, 132.9, 175.1], borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,.15)', tension: .3, fill: false },
      { label: '⑥stable_retained', data: [154.7, 37.2, 280.9], borderColor: '#14b8a6', backgroundColor: 'rgba(20,184,166,.15)', tension: .3, fill: false },
      { label: '⑦general_observation', data: [71.9, 104.3, 88.7], borderColor: '#94a3b8', backgroundColor: 'rgba(148,163,184,.15)', tension: .3, fill: false }
    ]
  },
  options: {
    ...baseOpts(),
    plugins: { legend: { labels: { color: '#e2e8f0', font: { size: 11 } } } },
    scales: {
      x: { grid: GRID, ticks: TICK },
      y: { grid: GRID, ticks: { ...TICK, callback: v => v + '분' }, title: { display: true, text: '평균 시청시간 (분)', color: '#94a3b8' } }
    }
  }
});"""

NEW_CHART = """// 7. Watch decay by segment — 수치 상시 표시, 범례 제거, 색 강화
const decayData = [
  { label: '① 위험-W3소멸', data: [89.3, 31.5, 6.6],   color: '#ef4444', dash: [] },
  { label: '② 위험-초반만', data: [114.1, 25.4, 44.3],  color: '#f97316', dash: [] },
  { label: '③ 위험-비활성', data: [0.0, 0.04, 19.0],    color: '#dc2626', dash: [6,4] },
  { label: '④ 중간-W3급감', data: [139.6, 137.8, 33.0], color: '#f59e0b', dash: [] },
  { label: '⑤ 콘텐츠증가',  data: [119.5, 132.9, 175.1],color: '#22c55e', dash: [] },
  { label: '⑥ 안정-고활성', data: [154.7, 37.2, 280.9], color: '#14b8a6', dash: [] },
  { label: '⑦ 일반관찰',    data: [71.9, 104.3, 88.7],  color: '#94a3b8', dash: [] },
];

// 수치 상시 표시 커스텀 플러그인
const decayLabelPlugin = {
  id: 'decayLabel',
  afterDatasetsDraw(chart) {
    const ctx = chart.ctx;
    chart.data.datasets.forEach((ds, di) => {
      const meta = chart.getDatasetMeta(di);
      meta.data.forEach((pt, pi) => {
        const val = ds.data[pi];
        if (val === null || val === undefined) return;
        ctx.save();
        ctx.font = 'bold 12px sans-serif';
        ctx.fillStyle = ds.borderColor;
        ctx.textAlign = 'center';
        // 값 표시 위치: 라인 위쪽, 겹침 방지를 위해 짝수 인덱스는 위, 홀수 아래
        const offset = (di % 2 === 0) ? -18 : 14;
        ctx.fillText(val.toFixed(1) + '분', pt.x, pt.y + offset);
        ctx.restore();
      });
    });
  }
};

new Chart(C('chartWatchDecay'), {
  type: 'line',
  plugins: [decayLabelPlugin],
  data: {
    labels: ['W1 (day0~6)', 'W2 (day7~13)', 'W3 (day14~20)'],
    datasets: decayData.map(d => ({
      label: d.label,
      data: d.data,
      borderColor: d.color,
      backgroundColor: d.color + '22',
      borderWidth: 3,
      borderDash: d.dash,
      pointRadius: 7,
      pointHoverRadius: 10,
      pointBackgroundColor: d.color,
      pointBorderColor: '#0f1117',
      pointBorderWidth: 2,
      tension: 0.2,
      fill: false,
    }))
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false },  // 범례 비활성 — 위에 독립 범례 박스 사용
      tooltip: {
        callbacks: {
          label: ctx => {
            const v = ctx.parsed.y;
            const avg = [100, 98, 99][ctx.dataIndex];
            const pct = avg > 0 ? ((v / avg) * 100).toFixed(0) : '—';
            return ` ${ctx.dataset.label}: ${v}분 (전체평균의 ${pct}%)`;
          }
        }
      }
    },
    scales: {
      x: { grid: GRID, ticks: TICK },
      y: {
        grid: GRID,
        ticks: { ...TICK, callback: v => v + '분' },
        title: { display: true, text: '평균 시청시간 (분)', color: '#94a3b8' },
        min: 0
      }
    }
  }
});"""

if OLD_CHART in content:
    content = content.replace(OLD_CHART, NEW_CHART, 1)
    open('park.ingyeom/reports/audits/build_aarrr_visual_guide.py', 'w', encoding='utf-8').write(content)
    print("Chart replaced OK")
else:
    # try finding by unique anchor
    idx = content.find("// 7. Watch decay by segment")
    print(f"Anchor found at: {idx}")
    if idx != -1:
        end_idx = content.find("});", idx) + 3
        old_block = content[idx:end_idx]
        print("Old block preview:", old_block[:100].encode('ascii','replace').decode())
        content = content[:idx] + NEW_CHART + content[end_idx:]
        open('park.ingyeom/reports/audits/build_aarrr_visual_guide.py', 'w', encoding='utf-8').write(content)
        print("Chart replaced via anchor OK")
    else:
        print("FAILED — anchor not found")
