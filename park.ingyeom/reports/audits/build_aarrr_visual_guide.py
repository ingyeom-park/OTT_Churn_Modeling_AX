"""
build_aarrr_visual_guide.py
출력: park.ingyeom/aarrr_visual_guide.html
"""
from pathlib import Path

HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>AARRR 심층 분석 — 100원딜 OTT 이탈 예측</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0f1117; --card: #1a1d27; --border: #2a2d3e;
    --text: #e2e8f0; --muted: #94a3b8; --accent: #6366f1;
    --green: #22c55e; --red: #ef4444; --yellow: #f59e0b;
    --blue: #3b82f6; --purple: #a855f7; --teal: #14b8a6;
    --orange: #f97316;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Noto Sans KR', -apple-system, sans-serif; display: flex; min-height: 100vh; }

  /* ── Sidebar ── */
  nav#sidebar {
    width: 240px; min-height: 100vh; background: var(--card);
    border-right: 1px solid var(--border); padding: 24px 0;
    position: sticky; top: 0; height: 100vh; overflow-y: auto;
    flex-shrink: 0;
  }
  nav#sidebar h2 { font-size: 13px; color: var(--muted); padding: 0 20px 12px; letter-spacing: .08em; text-transform: uppercase; }
  nav#sidebar a {
    display: flex; align-items: center; gap: 8px;
    padding: 9px 20px; color: var(--muted); text-decoration: none;
    font-size: 13px; transition: all .15s; border-left: 3px solid transparent;
  }
  nav#sidebar a:hover, nav#sidebar a.active {
    color: var(--text); background: rgba(99,102,241,.12); border-left-color: var(--accent);
  }
  nav#sidebar .nav-stage { font-size: 10px; padding: 4px 20px; color: #4b5563; letter-spacing: .1em; margin-top: 8px; }

  /* ── Main ── */
  main { flex: 1; padding: 40px; max-width: 1100px; }
  section { margin-bottom: 64px; scroll-margin-top: 24px; }
  h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
  h2 { font-size: 20px; font-weight: 700; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
  h3 { font-size: 15px; font-weight: 600; margin-bottom: 12px; color: var(--muted); }
  p { line-height: 1.7; color: var(--muted); margin-bottom: 12px; font-size: 14px; }

  .hero-meta { font-size: 13px; color: var(--muted); margin-top: 6px; }
  .badge { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
  .badge-info { background: rgba(59,130,246,.2); color: var(--blue); }
  .badge-warn { background: rgba(245,158,11,.2); color: var(--yellow); }
  .badge-danger { background: rgba(239,68,68,.2); color: var(--red); }
  .badge-ok { background: rgba(34,197,94,.2); color: var(--green); }

  /* ── Cards ── */
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }

  /* ── KPI ── */
  .kpi-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px; text-align: center; }
  .kpi-num { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
  .kpi-label { font-size: 12px; color: var(--muted); }

  /* ── Funnel ── */
  .funnel-wrap { display: flex; flex-direction: column; align-items: center; gap: 0; }
  .funnel-step {
    display: flex; align-items: center; width: 100%; max-width: 680px;
    margin-bottom: 0; position: relative;
  }
  .funnel-bar {
    height: 56px; border-radius: 6px; display: flex; align-items: center;
    padding: 0 20px; font-weight: 700; font-size: 15px; color: #fff;
    transition: width .3s; min-width: 120px;
  }
  .funnel-info { margin-left: 16px; }
  .funnel-info .fi-label { font-size: 14px; font-weight: 600; }
  .funnel-info .fi-sub { font-size: 12px; color: var(--muted); }
  .funnel-arrow {
    text-align: center; width: 100%; max-width: 680px;
    color: var(--muted); font-size: 12px; padding: 4px 0 4px 60px;
    display: flex; align-items: center; gap: 8px;
  }

  /* ── Table ── */
  .tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
  .tbl th { background: #1e2130; color: var(--muted); font-weight: 600; padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }
  .tbl td { padding: 10px 14px; border-bottom: 1px solid #1e2130; }
  .tbl tr:hover td { background: rgba(255,255,255,.02); }

  /* ── Highlight box ── */
  .info-box { border-left: 3px solid var(--accent); background: rgba(99,102,241,.08); border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 16px 0; }
  .warn-box { border-left: 3px solid var(--yellow); background: rgba(245,158,11,.08); border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 16px 0; }
  .danger-box { border-left: 3px solid var(--red); background: rgba(239,68,68,.08); border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 16px 0; }

  canvas { max-height: 320px; }
  .chart-wrap { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }

  /* ── Variable chip (인라인 변수 설명) ── */
  .var {
    display: inline-flex; align-items: center; gap: 4px;
    background: rgba(99,102,241,.13); border: 1px solid rgba(99,102,241,.3);
    border-radius: 6px; padding: 2px 8px; font-size: 12px;
    font-family: 'Courier New', monospace; color: #a5b4fc;
    position: relative; cursor: default;
    white-space: nowrap;
  }
  .var .vdesc {
    display: none; position: absolute; left: 0; top: calc(100% + 6px);
    background: #1e2130; border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 12px; z-index: 100;
    font-size: 12px; font-family: -apple-system, sans-serif;
    color: var(--text); width: max-content; max-width: 260px;
    line-height: 1.6; white-space: normal;
    box-shadow: 0 4px 16px rgba(0,0,0,.4);
  }
  .var:hover .vdesc { display: block; }
  body.light-mode .var {
    background: rgba(66,99,235,.08); border-color: rgba(66,99,235,.25); color: #4263eb;
  }
  body.light-mode .var .vdesc { background: #fff; color: #212529; box-shadow: 0 4px 16px rgba(0,0,0,.15); }

  /* ── Stage header ── */
  .stage-header {
    display: flex; align-items: center; gap: 14px; margin-bottom: 24px;
  }
  .stage-icon {
    width: 48px; height: 48px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; flex-shrink: 0;
  }
  .stage-title h2 { border-bottom: none; margin-bottom: 4px; padding-bottom: 0; }
  .stage-title p { margin-bottom: 0; font-size: 13px; }

  .two-col-chart { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }

  @media (max-width: 900px) {
    nav#sidebar { display: none; }
    .grid-2, .grid-3, .grid-4, .two-col-chart { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<!-- ══════════════ SIDEBAR ══════════════ -->
<nav id="sidebar">
  <h2>AARRR 분석</h2>
  <a href="#overview">개요 & 데이터 범위</a>
  <a href="#funnel">AARRR 깔때기 전체</a>
  <div class="nav-stage">ACQUISITION</div>
  <a href="#acquisition">Acquisition — 유입</a>
  <div class="nav-stage">ACTIVATION</div>
  <a href="#activation">Activation — 초기 행동</a>
  <div class="nav-stage">RETENTION</div>
  <a href="#retention">Retention — 유지</a>
  <a href="#retention-decay">W1→W2→W3 감쇠</a>
  <a href="#retention-promo">프로모션 × Retention</a>
  <div class="nav-stage">REFERRAL</div>
  <a href="#referral">Referral — 설계 가능</a>
  <div class="nav-stage">REVENUE</div>
  <a href="#revenue">Revenue — 재구매</a>
  <a href="#cohort2x2">2×2 코호트 분석</a>
  <div class="nav-stage">심화</div>
  <a href="#promo-compare">프로모션 집단 비교</a>
  <a href="#smd-chart">SMD 시각화</a>
  <a href="#caution">해석 주의사항</a>
  <div class="nav-stage">용어</div>
  <a href="#glossary">변수 용어 사전</a>
</nav>

<!-- ══════════════ MAIN ══════════════ -->
<main>

<!-- ① 개요 -->
<section id="overview">
  <h1>AARRR 심층 분석</h1>
  <p class="hero-meta">100원딜 OTT 이탈 예측 프로젝트 — park.ingyeom | 데이터 기준: 06x 생성 데이터셋, day0~20 관측창</p>

  <div class="info-box" style="margin-top:20px;">
    <strong>분석 단위 주의</strong> — 모든 수치는 subscription-event row 기준입니다. USER_KEY는 구독 이벤트마다 반복될 수 있어 row 수 ≠ 고유 고객 수입니다. "고객 수"로 표현하지 않습니다.
  </div>

  <div class="grid-4" style="margin-top:24px;">
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--blue)">23,343</div>
      <div class="kpi-label">전체 subscription-event rows</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--green)">71.6%</div>
      <div class="kpi-label">전체 재구매율 (Revenue proxy)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--red)">28.4%</div>
      <div class="kpi-label">전체 이탈 proxy율</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--purple)">51.2%</div>
      <div class="kpi-label">프로모션(100원딜) 비율</div>
    </div>
  </div>

  <div class="grid-3" style="margin-top:20px;">
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--accent)">76</div>
      <div class="kpi-label">expanded_no_payment_device 피처 수 (15x)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--teal)">0.8787</div>
      <div class="kpi-label">LightGBM OOF AUC (15x)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--orange)">day0~20</div>
      <div class="kpi-label">관측창 (day21+ 행동 미사용)</div>
    </div>
  </div>

  <div style="margin-top:28px;">
    <h3>AARRR 단계별 데이터 가용성</h3>
    <table class="tbl">
      <thead><tr><th>AARRR 단계</th><th>데이터 가용성</th><th>주요 피처</th><th>피처 수</th></tr></thead>
      <tbody>
        <tr>
          <td><span class="badge badge-ok">Acquisition</span></td>
          <td>is_promotion (scope-conditional), 가입 맥락</td>
          <td>
            <span class="var">is_promotion<span class="vdesc">100원딜 프로모션으로 가입했는지 여부 (1=프로모션, 0=일반)</span></span>
            <span class="var">reg_hour<span class="vdesc">가입한 시간대 (아침/오후/저녁/밤으로 구분)</span></span>
            <span class="var">is_basic/premium/standard<span class="vdesc">구독 플랜 종류 (베이직·스탠다드·프리미엄)</span></span>
          </td>
          <td>13</td>
        </tr>
        <tr>
          <td><span class="badge badge-ok">Activation</span></td>
          <td>W1 시청 행동, cold start</td>
          <td>
            <span class="var">is_cold_start_3d_fixed<span class="vdesc">가입 후 3일 내에 첫 시청이 없으면 1 (초기 습관 미형성 신호)</span></span>
            <span class="var">is_cold_start_7d_fixed<span class="vdesc">가입 후 7일 내에 첫 시청이 없으면 1 (1주차 비활성)</span></span>
            <span class="var">is_only_w1<span class="vdesc">1주차(day0~6)에만 시청하고 이후 활동 없음</span></span>
            <span class="var">watch_time_min_w1<span class="vdesc">1주차 총 시청시간 (분)</span></span>
          </td>
          <td>6</td>
        </tr>
        <tr>
          <td><span class="badge badge-ok">Retention</span></td>
          <td>W1~W3 주차별 + 집계 행동</td>
          <td>
            <span class="var">watch_time_min_w2/w3<span class="vdesc">2·3주차 시청시간 (분). W1 대비 감소 폭이 이탈 예측의 핵심 신호</span></span>
            <span class="var">diff_between_w3_w2<span class="vdesc">3주차 - 2주차 시청시간 차이. 음수면 감쇠 중</span></span>
            <span class="var">retention_w3_ratio<span class="vdesc">3주차 시청 유지율 (%)</span></span>
            <span class="var">recency<span class="vdesc">마지막 시청일로부터 관측 종료까지 경과 일수. 클수록 오래 안 봤다는 의미</span></span>
          </td>
          <td>39</td>
        </tr>
        <tr><td><span class="badge badge-warn">Referral</span></td><td style="color:var(--yellow)">데이터 없음 — 직접 측정 불가</td><td>—</td><td>0</td></tr>
        <tr>
          <td><span class="badge badge-ok">Revenue</span></td>
          <td>is_repurchase (타겟 proxy)</td>
          <td>
            <span class="var">is_repurchase<span class="vdesc">관측창(day0~20) 이후 구독을 갱신했으면 1, 안 했으면 0. 이 프로젝트의 예측 대상(타겟)이며 피처로 쓰지 않음</span></span>
          </td>
          <td>—</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

<!-- ② 깔때기 -->
<section id="funnel">
  <h2>AARRR 깔때기 전체 흐름</h2>
  <p>이 프로젝트의 데이터는 이미 구독이 시작된 시점 이후를 관측합니다. 즉, "구독 시작 = 이미 통과된 단계"이며, 우리가 직접 관측하는 것은 <strong>Activation → Retention → Revenue</strong> 구간입니다.</p>

  <div class="warn-box">
    깔때기의 각 단계 수치는 row 수 기반의 관측 요약입니다. 단계 간 이탈은 "같은 row가 다음 단계 조건을 만족하지 못한 비율"로 정의합니다.
  </div>

  <div class="funnel-wrap" style="margin-top: 32px;">
    <!-- Acquisition -->
    <div class="funnel-step">
      <div class="funnel-bar" style="width:100%; background: linear-gradient(135deg,#6366f1,#8b5cf6);">
        Acquisition
      </div>
      <div class="funnel-info">
        <div class="fi-label">23,343 rows (100%)</div>
        <div class="fi-sub">프로모션 51.2% / 비프로모션 48.8%</div>
      </div>
    </div>
    <div class="funnel-arrow">
      <div style="flex:1;height:1px;background:var(--border);max-width:60px;"></div>
      ▼ cold_start_7d 미통과 35.7% → W1 시청 미시작 후보
    </div>
    <!-- Activation -->
    <div class="funnel-step">
      <div class="funnel-bar" style="width:87%; background: linear-gradient(135deg,#3b82f6,#06b6d4);">
        Activation
      </div>
      <div class="funnel-info">
        <div class="fi-label">~20,300 rows (87%)*</div>
        <div class="fi-sub">cold_start_7d 통과 기준 추정 | is_only_w1: 9.9%</div>
      </div>
    </div>
    <div class="funnel-arrow">
      <div style="flex:1;height:1px;background:var(--border);max-width:60px;"></div>
      ▼ W3 시청 없거나 감쇠 — Retention 이탈 발생
    </div>
    <!-- Retention -->
    <div class="funnel-step">
      <div class="funnel-bar" style="width:72%; background: linear-gradient(135deg,#14b8a6,#22c55e);">
        Retention
      </div>
      <div class="funnel-info">
        <div class="fi-label">관측창 내 W1~W3 유지 여부</div>
        <div class="fi-sub">is_w3_over_50pct: 28.4% | is_only_w3: 10.1%</div>
      </div>
    </div>
    <div class="funnel-arrow">
      <div style="flex:1;height:1px;background:var(--border);max-width:60px;"></div>
      ▼ Referral: 측정 불가 (데이터 없음)
    </div>
    <!-- Referral -->
    <div class="funnel-step">
      <div class="funnel-bar" style="width:55%; background: #2a2d3e; border: 2px dashed #4b5563; color: #6b7280;">
        Referral
      </div>
      <div class="funnel-info">
        <div class="fi-label" style="color:#6b7280;">측정 불가</div>
        <div class="fi-sub" style="color:#4b5563;">직접 측정 피처 0개</div>
      </div>
    </div>
    <div class="funnel-arrow">
      <div style="flex:1;height:1px;background:var(--border);max-width:60px;"></div>
      ▼ 관측창 이후 구독 갱신 여부 → Revenue proxy
    </div>
    <!-- Revenue -->
    <div class="funnel-step">
      <div class="funnel-bar" style="width:72%; background: linear-gradient(135deg,#f59e0b,#f97316);">
        Revenue
      </div>
      <div class="funnel-info">
        <div class="fi-label">재구매율 71.6%</div>
        <div class="fi-sub">16,702 / 23,343 rows | 이탈 proxy 28.4%</div>
      </div>
    </div>
  </div>
  <p style="margin-top:16px; font-size:12px;">* Activation row 수는 cold_start_7d_fixed 통과율(~64%)을 반전한 추정값입니다. 직접 집계값이 아닙니다.</p>

  <!-- Funnel Bar Chart -->
  <div class="chart-wrap" style="margin-top:28px;">
    <h3>AARRR 단계별 Row 구성 (관측 기준)</h3>
    <canvas id="chartFunnel"></canvas>
  </div>
</section>

<!-- ③ Acquisition -->
<section id="acquisition">
  <div class="stage-header">
    <div class="stage-icon" style="background:rgba(99,102,241,.2); color:var(--accent);">①</div>
    <div class="stage-title">
      <h2>Acquisition — 유입</h2>
      <p>누가, 어떻게 들어왔는가</p>
    </div>
  </div>

  <div class="info-box">
    <strong>is_promotion</strong>은 Acquisition 단계의 핵심 split key입니다. 단, 이것은 프로모션이 이탈을 "유발"했다는 인과 주장이 아니라, 두 집단이 다른 조건에서 유입되었다는 관측입니다.
  </div>

  <div class="grid-4" style="margin-top:20px;">
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--purple)">11,955</div>
      <div class="kpi-label">프로모션(100원딜) rows</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--blue)">11,388</div>
      <div class="kpi-label">비프로모션 rows</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--red)">67.4%</div>
      <div class="kpi-label">프로모션군 재구매율</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--green)">75.9%</div>
      <div class="kpi-label">비프로모션군 재구매율</div>
    </div>
  </div>

  <div class="two-col-chart">
    <div class="chart-wrap">
      <h3>프로모션 / 비프로모션 비율</h3>
      <canvas id="chartPromoSplit"></canvas>
    </div>
    <div class="chart-wrap">
      <h3>가입 시간대 분포 (프로모션 vs 비프로모션)</h3>
      <canvas id="chartRegHour"></canvas>
    </div>
  </div>

  <div class="chart-wrap" style="margin-top:20px;">
    <h3>플랜 구성 비교 (프로모션 vs 비프로모션)</h3>
    <canvas id="chartPlan"></canvas>
  </div>

  <div style="margin-top:20px;">
    <h3>결제 환경 비교 (Acquisition_context)</h3>
    <table class="tbl">
      <thead><tr><th>결제 환경</th><th>프로모션 비율</th><th>비프로모션 비율</th><th>차이</th><th>SMD</th></tr></thead>
      <tbody>
        <tr><td>payment_is_ios</td><td>0.0%</td><td>34.2%</td><td style="color:var(--red)">-34.2%p</td><td style="color:var(--red)">1.019 (매우 큰 차이)</td></tr>
        <tr><td>payment_is_mobile</td><td>22.5%</td><td>8.0%</td><td style="color:var(--green)">+14.6%p</td><td>0.414</td></tr>
        <tr><td>payment_is_pc</td><td>25.0%</td><td>13.4%</td><td style="color:var(--green)">+11.6%p</td><td>0.299</td></tr>
        <tr><td>payment_is_android</td><td>51.8%</td><td>41.7%</td><td style="color:var(--green)">+10.2%p</td><td>0.205</td></tr>
      </tbody>
    </table>
    <div class="warn-box" style="margin-top:12px;">
      <strong>payment_is_ios = 0.0%</strong> — 프로모션군에 iOS 결제 row가 전혀 없습니다. 이는 데이터 특성이며, "iOS 고객은 충성도가 높다"는 식의 인과 해석은 금지입니다. payment_is_* 는 결제 환경 proxy이지 시청 기기가 아닙니다.
    </div>
  </div>
</section>

<!-- ④ Activation -->
<section id="activation">
  <div class="stage-header">
    <div class="stage-icon" style="background:rgba(59,130,246,.2); color:var(--blue);">②</div>
    <div class="stage-title">
      <h2>Activation — 초기 행동</h2>
      <p>구독 후 실제로 서비스를 사용하기 시작했는가</p>
    </div>
  </div>

  <p>Activation은 "구독을 시작했지만 아직 습관이 형성되지 않은" 단계입니다. 이 프로젝트에서는 <strong>W1(day0~6) 시청 행동</strong>과 cold_start 여부로 측정합니다.</p>

  <div class="info-box" style="margin-top:0; margin-bottom:20px;">
    <strong>변수 설명</strong> (마우스를 올리면 상세 설명이 나옵니다)<br>
    <span class="var" style="margin-top:6px; display:inline-block;">is_cold_start_3d_fixed<span class="vdesc">가입 후 3일 안에 첫 시청이 없으면 1. "일단 결제만 하고 안 본 경우"를 잡는 초기 이탈 신호. _fixed는 원본 컬럼 명칭 충돌을 피하기 위해 붙인 suffix.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">is_cold_start_7d_fixed<span class="vdesc">가입 후 7일 안에 첫 시청이 없으면 1. 1주차 전체 비활성. 이 비율이 전체의 63~64%라는 것은 구독자 절반 이상이 첫 주를 건너뛰었다는 의미.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">is_only_w1<span class="vdesc">1주차(day0~6)에만 시청하고 2·3주차에는 아예 안 본 경우 1. 반짝 구경 후 이탈 패턴.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">watch_time_min_w1<span class="vdesc">1주차(day0~6) 동안의 총 시청시간(분). 평균 약 100분 — 영화 한 편 분량.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">watch_session_w1<span class="vdesc">1주차 총 시청 세션 수. 한 번 켜서 보면 1 세션.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">is_w1_over_50pct<span class="vdesc">전체 관측창(3주) 시청시간 중 1주차 비중이 50% 이상이면 1. 초반에 몰아보고 뒤로 갈수록 안 보는 패턴 감지.</span></span>
  </div>

  <div class="grid-4">
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--blue)">38.5%</div>
      <div class="kpi-label">3일 내 미시청 비율<br><span style="font-size:11px; color:var(--muted);">is_cold_start_3d_fixed | 비프로모션 38.9%</span></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--blue)">63.5%</div>
      <div class="kpi-label">7일 내 미시청 비율<br><span style="font-size:11px; color:var(--muted);">is_cold_start_7d_fixed | 비프로모션 64.1%</span></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--yellow)">9.7%</div>
      <div class="kpi-label">1주차만 보고 사라진 비율<br><span style="font-size:11px; color:var(--muted);">is_only_w1 | 비프로모션 10.1%</span></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--green)">~100분</div>
      <div class="kpi-label">1주차 평균 시청시간<br><span style="font-size:11px; color:var(--muted);">watch_time_min_w1 | 프로모션 100.4 / 비 99.9분</span></div>
    </div>
  </div>

  <div class="two-col-chart" style="margin-top:20px;">
    <div class="chart-wrap">
      <h3>초기 미시청 비율 비교 (프로모션 vs 비프로모션)</h3>
      <canvas id="chartColdStart"></canvas>
    </div>
    <div class="chart-wrap">
      <h3>W1 시청 패턴 비율</h3>
      <canvas id="chartW1Pattern"></canvas>
    </div>
  </div>

  <div class="info-box" style="margin-top:20px;">
    <strong>핵심 관찰</strong> — Activation 단계의 프로모션 vs 비프로모션 차이는 매우 작습니다 (SMD 최대 0.016). 두 집단이 "들어온 방식"은 달라도, "처음 시청을 시작하는 행동"은 거의 동일합니다. Activation 문제는 프로모션 여부보다 개인 행동 패턴에 더 크게 좌우됩니다.
  </div>
</section>

<!-- ⑤ Retention -->
<section id="retention">
  <div class="stage-header">
    <div class="stage-icon" style="background:rgba(20,184,166,.2); color:var(--teal);">③</div>
    <div class="stage-title">
      <h2>Retention — 유지</h2>
      <p>구독 기간 내 얼마나 지속적으로 사용했는가</p>
    </div>
  </div>

  <p>Retention은 이 프로젝트에서 <strong>가장 많은 피처(39개)</strong>를 보유한 단계입니다. W1→W2→W3 주차별 시청량 변화가 이탈 예측의 핵심 신호입니다.</p>

  <div class="info-box" style="margin-bottom:20px;">
    <strong>주요 Retention 변수 설명</strong><br>
    <span class="var" style="margin-top:6px; display:inline-block;">watch_time_min_w2 / w3<span class="vdesc">2주차(day7~13), 3주차(day14~20) 총 시청시간(분). W1 대비 얼마나 줄었는지가 이탈 예측의 핵심.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">diff_between_w3_w2<span class="vdesc">3주차 시청시간 - 2주차 시청시간. 음수면 감쇠 중, 양수면 회복 중.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">retention_w2_ratio / w3_ratio<span class="vdesc">2·3주차 시청 유지율(%). 전체 관측 일수 중 해당 주차에 시청한 날의 비율.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">recency<span class="vdesc">마지막으로 시청한 날부터 관측창 끝(day20)까지 경과일. 클수록 "오래전에 마지막으로 봤다" = 이탈 위험.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">is_only_w2 / is_only_w3<span class="vdesc">2주차 또는 3주차에만 시청하고 나머지 주차는 아예 안 본 경우. 시청이 특정 주에 쏠린 비정상 패턴.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">max_inactive_gap_days<span class="vdesc">관측창 내 가장 긴 연속 비시청 기간(일). 며칠씩 안 보는 공백이 있는지 포착.</span></span>
    <span class="var" style="margin-top:6px; display:inline-block;">avg_gap_w3_watch_days<span class="vdesc">3주차 내 시청일 사이 평균 간격(일). 클수록 드문드문 봤다는 의미.</span></span>
  </div>

  <div class="grid-4">
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--teal)">39</div>
      <div class="kpi-label">Retention 피처 수 (expanded)<br><span style="font-size:11px; color:var(--muted);">시청행동 관련 변수가 가장 많은 단계</span></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--green)">28.4%</div>
      <div class="kpi-label">3주차 시청 비중 50% 이상<br><span style="font-size:11px; color:var(--muted);">is_w3_over_50pct — 후반부 집중 시청자</span></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--yellow)">10.1%</div>
      <div class="kpi-label">3주차에만 시청<br><span style="font-size:11px; color:var(--muted);">is_only_w3 — 프로모션군 소폭 높음</span></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--red)">7.7%</div>
      <div class="kpi-label">2주차에만 시청<br><span style="font-size:11px; color:var(--muted);">is_only_w2 — 프로모션군 소폭 낮음</span></div>
    </div>
  </div>
</section>

<!-- ⑥ Retention Decay -->
<section id="retention-decay">
  <h2>W1 → W2 → W3 시청 감쇠</h2>
  <p>7개 세그먼트의 주차별 평균 시청시간입니다. 세그먼트는 17x 설계 기준이며, row-level subscription-event 분석입니다.</p>

  <!-- 범례 독립 박스 — 색: 빨주노초파남보, 포인트 모양 구분 -->
  <div style="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:16px;">
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <svg width="20" height="14" viewBox="0 0 20 14"><line x1="0" y1="7" x2="20" y2="7" stroke="#ef4444" stroke-width="2.5"/><circle cx="10" cy="7" r="5" fill="#ef4444" stroke="#0f1117" stroke-width="1.5"/></svg>
      <span style="color:#ef4444;font-weight:700;">① 위험-W3소멸</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <svg width="20" height="14" viewBox="0 0 20 14"><line x1="0" y1="7" x2="20" y2="7" stroke="#f97316" stroke-width="2.5"/><rect x="5" y="2" width="10" height="10" fill="#f97316" stroke="#0f1117" stroke-width="1.5"/></svg>
      <span style="color:#f97316;font-weight:700;">② 위험-초반만시청</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <svg width="20" height="14" viewBox="0 0 20 14"><line x1="0" y1="7" x2="20" y2="7" stroke="#eab308" stroke-width="2.5"/><polygon points="10,1 18,13 2,13" fill="#eab308" stroke="#0f1117" stroke-width="1.5"/></svg>
      <span style="color:#eab308;font-weight:700;">③ 위험-전체비활성</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <svg width="20" height="14" viewBox="0 0 20 14"><line x1="0" y1="7" x2="20" y2="7" stroke="#22c55e" stroke-width="2.5"/><polygon points="10,1 18,7 10,13 2,7" fill="#22c55e" stroke="#0f1117" stroke-width="1.5"/></svg>
      <span style="color:#22c55e;font-weight:700;">④ 중간-W3급감</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <svg width="20" height="14" viewBox="0 0 20 14"><line x1="0" y1="7" x2="20" y2="7" stroke="#3b82f6" stroke-width="2.5"/><polygon points="10,1 12,6 18,6 13,10 15,15 10,11 5,15 7,10 2,6 8,6" fill="#3b82f6" stroke="#0f1117" stroke-width="1"/></svg>
      <span style="color:#3b82f6;font-weight:700;">⑤ 콘텐츠취향-증가</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <svg width="20" height="14" viewBox="0 0 20 14"><line x1="0" y1="7" x2="20" y2="7" stroke="#6366f1" stroke-width="2.5"/><polygon points="10,1 17,4 17,10 10,13 3,10 3,4" fill="#6366f1" stroke="#0f1117" stroke-width="1.5"/></svg>
      <span style="color:#6366f1;font-weight:700;">⑥ 안정-고활성</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <svg width="20" height="14" viewBox="0 0 20 14"><line x1="0" y1="7" x2="20" y2="7" stroke="#a855f7" stroke-width="2.5"/><line x1="6" y1="3" x2="14" y2="11" stroke="#a855f7" stroke-width="3" stroke-linecap="round"/><line x1="14" y1="3" x2="6" y2="11" stroke="#a855f7" stroke-width="3" stroke-linecap="round"/></svg>
      <span style="color:#a855f7;font-weight:700;">⑦ 일반관찰</span>
    </div>
  </div>

  <div class="chart-wrap">
    <h3>세그먼트별 W1→W2→W3 평균 시청시간 (분) — 수치 라인에 직접 표시</h3>
    <canvas id="chartWatchDecay" style="max-height:440px;"></canvas>
  </div>

  <div style="margin-top:24px;">
    <h3>세그먼트 상세 수치 (전체 평균 대비 비율 포함)</h3>
    <table class="tbl">
      <thead>
        <tr>
          <th>#</th><th>세그먼트 (설명)</th><th>W1 (분)</th><th>W2 (분)</th><th>W3 (분)</th><th>W1→W3 변화</th><th>패턴</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="color:#ef4444;font-weight:700;font-size:16px;">①</td>
          <td><strong>high_risk_week3_inactive_or_drop</strong><br>
          <span style="font-size:12px;color:var(--muted);">(3주차에 시청이 멈추거나 급감 — rows 16.4%, 이탈률 73.3%)</span></td>
          <td>89.3<br><span style="font-size:11px;color:var(--muted);">전체평균의 89%</span></td>
          <td>31.5<br><span style="font-size:11px;color:var(--muted);">전체평균의 32%</span></td>
          <td style="color:#ef4444;">6.6<br><span style="font-size:11px;">전체평균의 7%</span></td>
          <td style="color:#ef4444;font-weight:700;">−82.7분<br><span style="font-size:11px;">(−92.6%)</span></td>
          <td style="color:#ef4444;">급감쇠</td>
        </tr>
        <tr>
          <td style="color:#f97316;font-weight:700;font-size:16px;">②</td>
          <td><strong>high_risk_only_w1_or_cold_start_weak</strong><br>
          <span style="font-size:12px;color:var(--muted);">(1주차만 보거나 초기 습관 미형성 — rows 1.1%, 소규모, 이탈률 69.8%)</span></td>
          <td>114.1<br><span style="font-size:11px;color:var(--muted);">전체평균의 114%</span></td>
          <td style="color:#ef4444;">25.4<br><span style="font-size:11px;">전체평균의 25%</span></td>
          <td>44.3<br><span style="font-size:11px;color:var(--muted);">전체평균의 44%</span></td>
          <td style="color:#f59e0b;font-weight:700;">−69.8분<br><span style="font-size:11px;">(−61.2%)</span></td>
          <td style="color:#f59e0b;">W2 바닥 후 반등</td>
        </tr>
        <tr>
          <td style="color:#eab308;font-weight:700;font-size:16px;">③</td>
          <td><strong>high_risk_low_activity</strong><br>
          <span style="font-size:12px;color:var(--muted);">(관측창 내내 시청 거의 없음 — rows 2.2%, 이탈률 76.5%)</span></td>
          <td>0.0<br><span style="font-size:11px;color:var(--muted);">—</span></td>
          <td>0.0<br><span style="font-size:11px;color:var(--muted);">—</span></td>
          <td>19.0<br><span style="font-size:11px;color:var(--muted);">전체평균의 19%</span></td>
          <td style="color:#eab308;font-weight:700;">+19.0분<br><span style="font-size:11px;">(W1=0이라 비율 미산출)</span></td>
          <td style="color:#eab308;">전반 비활성</td>
        </tr>
        <tr>
          <td style="color:#22c55e;font-weight:700;font-size:16px;">④</td>
          <td><strong>medium_risk_retention_decay</strong><br>
          <span style="font-size:12px;color:var(--muted);">(W1·W2 활발, W3 급감 — rows 13.8%, 이탈률 35.8%)</span></td>
          <td>139.6<br><span style="font-size:11px;color:var(--muted);">전체평균의 139%</span></td>
          <td>137.8<br><span style="font-size:11px;color:var(--muted);">전체평균의 140%</span></td>
          <td style="color:#22c55e;">33.0<br><span style="font-size:11px;">전체평균의 33%</span></td>
          <td style="color:#22c55e;font-weight:700;">−106.6분<br><span style="font-size:11px;">(−76.4%)</span></td>
          <td style="color:#22c55e;">W3 급감</td>
        </tr>
        <tr>
          <td style="color:#3b82f6;font-weight:700;font-size:16px;">⑤</td>
          <td><strong>content_preference_target_candidate</strong><br>
          <span style="font-size:12px;color:var(--muted);">(콘텐츠 취향 뚜렷, 시청 꾸준히 증가 — rows 26.8%, 이탈률 9.5%)</span></td>
          <td>119.5<br><span style="font-size:11px;color:var(--muted);">전체평균의 119%</span></td>
          <td>132.9<br><span style="font-size:11px;color:var(--muted);">전체평균의 135%</span></td>
          <td style="color:#3b82f6;">175.1<br><span style="font-size:11px;">전체평균의 175%</span></td>
          <td style="color:#3b82f6;font-weight:700;">+55.6분<br><span style="font-size:11px;">(+46.5%)</span></td>
          <td style="color:#3b82f6;">증가 추세</td>
        </tr>
        <tr>
          <td style="color:#6366f1;font-weight:700;font-size:16px;">⑥</td>
          <td><strong>stable_retained_user</strong><br>
          <span style="font-size:12px;color:var(--muted);">(재구매율 98.9%, W3에 시청 집중 — rows 5.3%, 이탈률 1.7%)</span></td>
          <td>154.7<br><span style="font-size:11px;color:var(--muted);">전체평균의 154%</span></td>
          <td style="color:#eab308;">37.2<br><span style="font-size:11px;">전체평균의 38%</span></td>
          <td style="color:#6366f1;">280.9<br><span style="font-size:11px;">전체평균의 281%</span></td>
          <td style="color:#6366f1;font-weight:700;">+126.2분<br><span style="font-size:11px;">(+81.6%)</span></td>
          <td style="color:#6366f1;">고활성 (W3 집중)</td>
        </tr>
        <tr>
          <td style="color:#a855f7;font-weight:700;font-size:16px;">⑦</td>
          <td><strong>general_observation</strong><br>
          <span style="font-size:12px;color:var(--muted);">(특정 패턴 미해당 일반 그룹 — rows 34.2%, 전체에서 가장 큰 비중)</span></td>
          <td>71.9<br><span style="font-size:11px;color:var(--muted);">전체평균의 72%</span></td>
          <td>104.3<br><span style="font-size:11px;color:var(--muted);">전체평균의 106%</span></td>
          <td>88.7<br><span style="font-size:11px;color:var(--muted);">전체평균의 89%</span></td>
          <td style="color:#a855f7;font-weight:700;">+16.8분<br><span style="font-size:11px;">(+23.4%)</span></td>
          <td style="color:#a855f7;">중간 수준 유지</td>
        </tr>
      </tbody>
    </table>
    <p style="font-size:12px;margin-top:8px;color:var(--muted);">* 전체평균 기준: W1 약 100분, W2 약 98분, W3 약 99분 (전체 rows 기준)</p>
  </div>

  <div class="chart-wrap" style="margin-top:24px;">
    <h3>W1/W2/W3 시청시간 — 프로모션 vs 비프로모션 (차이 표시)</h3>
    <canvas id="chartWeekCompare"></canvas>
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px;">
    <div class="kpi-card">
      <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">W1 시청시간</div>
      <div style="font-size:13px;font-weight:700;">프로모션 <span style="color:#a855f7;">100.4분</span></div>
      <div style="font-size:13px;font-weight:700;">비프로모션 <span style="color:#3b82f6;">99.9분</span></div>
      <div style="font-size:12px;margin-top:4px;">차이: <span style="color:#22c55e;font-weight:600;">+0.5분 (+0.5%)</span></div>
    </div>
    <div class="kpi-card">
      <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">W2 시청시간</div>
      <div style="font-size:13px;font-weight:700;">프로모션 <span style="color:#a855f7;">98.1분</span></div>
      <div style="font-size:13px;font-weight:700;">비프로모션 <span style="color:#3b82f6;">97.6분</span></div>
      <div style="font-size:12px;margin-top:4px;">차이: <span style="color:#22c55e;font-weight:600;">+0.5분 (+0.5%)</span></div>
    </div>
    <div class="kpi-card">
      <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">W3 시청시간</div>
      <div style="font-size:13px;font-weight:700;">프로모션 <span style="color:#a855f7;">99.1분</span></div>
      <div style="font-size:13px;font-weight:700;">비프로모션 <span style="color:#3b82f6;">98.5분</span></div>
      <div style="font-size:12px;margin-top:4px;">차이: <span style="color:#22c55e;font-weight:600;">+0.6분 (+0.6%)</span></div>
    </div>
  </div>
  <div class="info-box" style="margin-top:12px;">
    W1/W2/W3 시청시간의 프로모션·비프로모션 차이는 0.5~0.6분으로 <strong>사실상 동일</strong>합니다. 두 집단의 관측창 내 시청 행동은 거의 구별되지 않습니다.
  </div>
</section>

<!-- ⑦ Retention × Promo -->
<section id="retention-promo">
  <h2>프로모션 × Retention 비교</h2>

  <p>Retention 피처들에서 프로모션 vs 비프로모션 간 표준화 평균 차이(SMD)는 전반적으로 매우 작습니다 (평균 SMD ≈ 0.008). 두 집단의 관측창 내 시청 행동은 통계적으로 거의 동일합니다.</p>

  <div class="chart-wrap">
    <h3>주요 Retention 피처 프로모션 vs 비프로모션 비교</h3>
    <canvas id="chartRetentionCompare"></canvas>
  </div>

  <div class="info-box" style="margin-top:20px;">
    <strong>핵심 발견</strong> — 프로모션 vs 비프로모션의 Retention(주차별 시청 행동) 차이는 미미합니다. 두 집단이 재구매율에서 8.7%p 차이나는 것은 Retention 행동 차이가 아닌, Acquisition 단계의 구조적 차이(연령대, 결제 환경, 가입 의도 등)에서 비롯될 가능성이 큽니다. 단, 이는 관측 기반 추론이며 인과 검증이 아닙니다.
  </div>
</section>

<!-- ⑧ Referral -->
<section id="referral">
  <div class="stage-header">
    <div class="stage-icon" style="background:rgba(75,85,99,.3); color:#6b7280;">④</div>
    <div class="stage-title">
      <h2>Referral — 현재 공백, 그러나 설계 가능</h2>
      <p>데이터는 없지만, 이 프로젝트가 만든 세그먼트로 Referral을 설계할 수 있습니다</p>
    </div>
  </div>

  <div class="danger-box">
    <strong>현재 데이터 Referral 피처 수: 0개</strong><br>
    07x AARRR 매핑 명시: "Referral has no directly observed feature in this dataset." — View_History, Membership, Movie_Master 어디에도 추천/공유 로그가 없습니다.
  </div>

  <div class="info-box" style="margin-top:20px;">
    <strong>그러나 Referral은 포기할 단계가 아닙니다.</strong><br>
    이탈 예측 모델이 고위험 세그먼트를 식별했고, 이 세그먼트를 기반으로 <strong>"이탈 전 친구 추천 유도"</strong> 메커니즘을 설계할 수 있습니다. Retention이 무너지기 전에 Referral을 끼워넣는 전략입니다.
  </div>

  <!-- 글로벌 사례 -->
  <h3 style="margin-top:28px;">글로벌 OTT/구독 서비스 Referral 사례</h3>
  <div class="grid-3" style="margin-top:12px;">
    <div class="card">
      <div style="font-size:20px; margin-bottom:8px;">🎵</div>
      <div style="font-weight:700; margin-bottom:6px;">Spotify</div>
      <div style="font-size:13px; color:var(--muted); line-height:1.7;">
        초기 론칭 시 <strong>초대장 5개 제한</strong>으로 희소성 유발.<br>
        이후 <strong>양방향 보상</strong> 도입: 추천인 1개월 무료 + 신규 가입자 2개월 무료.<br>
        결과: 바이럴 가입이 전체 신규의 상당 비중 차지.
      </div>
    </div>
    <div class="card">
      <div style="font-size:20px; margin-bottom:8px;">📦</div>
      <div style="font-weight:700; margin-bottom:6px;">Dropbox</div>
      <div style="font-size:13px; color:var(--muted); line-height:1.7;">
        추천인·수신인 <strong>양측 모두 용량 추가</strong> 보상.<br>
        가입자 수 15개월 만에 <strong>3,900% 성장</strong>.<br>
        CAC(고객 획득 비용)를 광고비 대비 대폭 절감.
      </div>
    </div>
    <div class="card">
      <div style="font-size:20px; margin-bottom:8px;">🎬</div>
      <div style="font-weight:700; margin-bottom:6px;">Netflix (초기)</div>
      <div style="font-size:13px; color:var(--muted); line-height:1.7;">
        DVD 시절 <strong>"친구 초대 시 1개월 무료"</strong> 운영.<br>
        브랜드 인지도 상승 후 프로그램 중단 — 브랜드 파워만으로 성장 가능한 시점에 종료.<br>
        초기 성장에 결정적 기여.
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:16px; border-color:rgba(34,197,94,.3);">
    <div style="font-weight:700; margin-bottom:6px; color:var(--green);">왓챠 (국내 사례)</div>
    <div style="font-size:13px; color:var(--muted); line-height:1.7;">
      친구 추천 링크로 가입 시 <strong>추가 2주 무료 체험</strong> 제공 (기본 2주 → 총 1개월).<br>
      단방향 보상(가입자만) → 양방향으로 개선하면 추천 동기 강화 가능.
    </div>
  </div>

  <!-- 이 프로젝트에서의 Referral 설계 제안 -->
  <h3 style="margin-top:32px;">이 프로젝트 기반 Referral 설계 후보</h3>
  <p>100원딜 구독자의 이탈 위험을 줄이면서 동시에 신규 유입을 만드는 구조입니다.</p>

  <div class="card" style="margin-top:16px; border-color:rgba(99,102,241,.4); padding:28px;">
    <div style="font-size:18px; font-weight:700; margin-bottom:16px; color:var(--accent);">
      제안: "100원딜 친구 초대" 프로그램
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
      <div>
        <div style="font-size:12px; color:var(--muted); margin-bottom:8px; text-transform:uppercase; letter-spacing:.08em;">기본 구조</div>
        <div style="font-size:14px; line-height:2; color:var(--text);">
          ① 기존 구독자가 카카오톡/SNS로 <strong>전용 초대 링크</strong> 발송<br>
          ② 친구가 링크로 가입 + 100원딜 구독 완료<br>
          ③ <strong>추천인: 다음 달 100원딜 1개월 추가</strong><br>
          ④ <strong>수신인: 첫 달 100원 (기존과 동일) + 2주 연장</strong>
        </div>
      </div>
      <div>
        <div style="font-size:12px; color:var(--muted); margin-bottom:8px; text-transform:uppercase; letter-spacing:.08em;">세그먼트 타겟팅</div>
        <div style="font-size:14px; line-height:2; color:var(--text);">
          <span style="color:var(--green);">stable_retained_user</span> — 가장 만족도 높음, 추천 동기 충분<br>
          <span style="color:var(--teal);">content_preference_target</span> — 콘텐츠 취향 명확, 비슷한 친구 추천 가능성<br>
          <span style="color:var(--yellow);">medium_risk_decay</span> — 이탈 전 추천 참여로 재engagement 유도<br>
          <span style="color:var(--red);">high_risk 세그먼트</span> — 추천보다 re-entry 메시지 우선
        </div>
      </div>
    </div>
  </div>

  <!-- Referral × AARRR 연결 -->
  <h3 style="margin-top:28px;">Referral이 다른 AARRR 단계에 미치는 효과</h3>
  <div class="chart-wrap" style="margin-top:12px;">
    <h3>Referral 프로그램의 AARRR 단계별 기대 효과</h3>
    <canvas id="chartReferralEffect"></canvas>
  </div>

  <div style="margin-top:20px;">
    <table class="tbl">
      <thead><tr><th>AARRR 단계</th><th>Referral 연계 효과</th><th>측정 지표 후보</th></tr></thead>
      <tbody>
        <tr><td><span class="badge badge-info">Acquisition</span></td><td>추천 링크를 통한 신규 유입 — CAC 절감</td><td>추천 전환율, 추천 유입 신규 row 수</td></tr>
        <tr><td><span class="badge badge-info">Activation</span></td><td>추천으로 온 신규 유저는 지인의 검증을 거쳐 초기 이탈률 낮음</td><td>cold_start_3d/7d 통과율 비교 (추천 vs 일반)</td></tr>
        <tr><td><span class="badge badge-ok">Retention</span></td><td>추천인(기존 구독자)은 리워드를 위해 구독 유지 동기 강화</td><td>추천인의 W2/W3 시청 변화, retention_w3_ratio</td></tr>
        <tr><td><span class="badge badge-warn">Referral</span></td><td>K-factor(1명이 평균 몇 명 초대) 측정 시작</td><td>K-factor, 바이럴 계수, 초대 링크 클릭률</td></tr>
        <tr><td><span class="badge badge-ok">Revenue</span></td><td>추천인 이탈 방어 + 신규 재구매 후보 확보</td><td>추천인 재구매율 vs 비추천인, LTV 차이</td></tr>
      </tbody>
    </table>
  </div>

  <!-- 데이터 수집 로드맵 -->
  <h3 style="margin-top:28px;">Referral 측정을 위한 데이터 수집 로드맵</h3>
  <table class="tbl">
    <thead><tr><th>필요 데이터</th><th>측정 가능 지표</th><th>현재 상태</th><th>우선순위</th></tr></thead>
    <tbody>
      <tr><td>초대 링크 발송/클릭 로그</td><td>초대 전환율, K-factor</td><td style="color:var(--red)">없음</td><td>★★★</td></tr>
      <tr><td>추천인-수신인 매핑 테이블</td><td>추천 네트워크 분석</td><td style="color:var(--red)">없음</td><td>★★★</td></tr>
      <tr><td>카카오/SNS 공유 로그</td><td>채널별 바이럴 효과</td><td style="color:var(--red)">없음</td><td>★★</td></tr>
      <tr><td>추천인 구독 변화 이력</td><td>추천 전후 Retention 비교</td><td style="color:var(--yellow)">부분 가능 (is_repurchase)</td><td>★★</td></tr>
    </tbody>
  </table>

  <div class="warn-box" style="margin-top:16px;">
    <strong>A/B test 설계 필요</strong> — 추천 프로그램 도입 시, 세그먼트별(stable vs medium_risk) 효과가 다를 수 있습니다. 세그먼트를 A/B test 단위로 활용하는 것이 이 프로젝트의 분석과 직접 연결되는 후속 단계입니다.
  </div>
</section>

<!-- ⑨ Revenue -->
<section id="revenue">
  <div class="stage-header">
    <div class="stage-icon" style="background:rgba(245,158,11,.2); color:var(--yellow);">⑤</div>
    <div class="stage-title">
      <h2>Revenue — 재구매 (이탈 proxy)</h2>
      <p>관측창 이후 구독을 갱신했는가</p>
    </div>
  </div>

  <div class="warn-box">
    <strong><span class="var">is_repurchase<span class="vdesc">관측창(day0~20) 이후 구독을 다음 달에도 갱신했으면 1, 해지했으면 0. 이 값이 0이면 "이탈"로 간주. 예측 타겟이므로 모델 피처로 쓰지 않음. Revenue의 직접 매출액이 아니라 "재구매 여부"라는 대리 지표(proxy)임.</span></span>는 타겟 변수이지 피처가 아닙니다.</strong> Revenue proxy로만 사용되며, "Revenue가 발생했다"는 직접 매출 지표가 아닙니다.
  </div>

  <div class="grid-4" style="margin-top:20px;">
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--green)">16,702</div>
      <div class="kpi-label">재구매(is_repurchase=1) rows</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--red)">6,641</div>
      <div class="kpi-label">이탈(is_repurchase=0) rows</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--green)">71.6%</div>
      <div class="kpi-label">전체 재구매율</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-num" style="color:var(--red)">28.4%</div>
      <div class="kpi-label">전체 이탈 proxy율</div>
    </div>
  </div>

  <div class="two-col-chart" style="margin-top:24px;">
    <div class="chart-wrap">
      <h3>전체 재구매 vs 이탈 분포</h3>
      <canvas id="chartRevenueDist"></canvas>
    </div>
    <div class="chart-wrap">
      <h3>프로모션 여부별 재구매율</h3>
      <canvas id="chartRevenueByPromo"></canvas>
    </div>
  </div>
</section>

<!-- ⑩ 2x2 코호트 -->
<section id="cohort2x2">
  <h2>2×2 코호트 분석 (프로모션 × 재구매)</h2>
  <p>전체 데이터를 프로모션 여부 × 재구매 여부로 4개 코호트로 분류한 결과입니다.</p>

  <div class="grid-4">
    <div class="kpi-card" style="border-color: rgba(99,102,241,.4);">
      <div style="font-size:11px; color:var(--accent); margin-bottom:8px;">프로모션 × 재구매</div>
      <div class="kpi-num" style="color:var(--accent)">8,037</div>
      <div class="kpi-label">rows (34.8%)</div>
    </div>
    <div class="kpi-card" style="border-color: rgba(239,68,68,.4);">
      <div style="font-size:11px; color:var(--red); margin-bottom:8px;">프로모션 × 이탈</div>
      <div class="kpi-num" style="color:var(--red)">3,867</div>
      <div class="kpi-label">rows (16.8%)</div>
    </div>
    <div class="kpi-card" style="border-color: rgba(34,197,94,.4);">
      <div style="font-size:11px; color:var(--green); margin-bottom:8px;">비프로모션 × 재구매</div>
      <div class="kpi-num" style="color:var(--green)">8,520</div>
      <div class="kpi-label">rows (36.9%)</div>
    </div>
    <div class="kpi-card" style="border-color: rgba(245,158,11,.4);">
      <div style="font-size:11px; color:var(--yellow); margin-bottom:8px;">비프로모션 × 이탈</div>
      <div class="kpi-num" style="color:var(--yellow)">2,655</div>
      <div class="kpi-label">rows (11.5%)</div>
    </div>
  </div>

  <div class="chart-wrap" style="margin-top:24px;">
    <h3>2×2 코호트 구성 비율</h3>
    <canvas id="chartCohort2x2"></canvas>
  </div>

  <div style="margin-top:24px;">
    <h3>코호트 내 비율 해석</h3>
    <table class="tbl">
      <thead><tr><th>비교 관점</th><th>수치</th><th>해석</th></tr></thead>
      <tbody>
        <tr><td>프로모션군 내 재구매율</td><td>67.5%</td><td>프로모션군의 2/3가 재구매</td></tr>
        <tr><td>비프로모션군 내 재구매율</td><td>76.2%</td><td>비프로모션군은 3/4 이상 재구매</td></tr>
        <tr><td>재구매자 중 프로모션 비율</td><td>48.5%</td><td>재구매자의 절반 가량이 프로모션 유입</td></tr>
        <tr><td>이탈자 중 프로모션 비율</td><td>59.3%</td><td>이탈자의 약 60%가 프로모션 유입</td></tr>
        <tr><td>집단 간 재구매율 차이</td><td>8.7%p</td><td>관측된 차이 (인과 아님)</td></tr>
      </tbody>
    </table>
  </div>

  <div class="info-box" style="margin-top:16px;">
    재구매자 중 프로모션 비율(48.5%)과 이탈자 중 프로모션 비율(59.3%)의 차이는, 프로모션 유입 row가 이탈 pool에서 상대적으로 더 큰 비중을 차지한다는 관측입니다. 원인 분석을 위해서는 집단 구성(연령, 결제 환경 등)의 기저 차이를 통제해야 합니다.
  </div>
</section>

<!-- ⑪ 프로모션 집단 비교 -->
<section id="promo-compare">
  <h2>프로모션 집단 심층 비교</h2>
  <p>두 집단에서 가장 큰 차이를 보이는 변수들입니다. SMD(표준화 평균 차이)가 클수록 집단 간 구성 차이가 큽니다.</p>

  <div class="warn-box">
    이 비교는 집단 특성 기술(descriptive) 목적입니다. SMD가 크다고 해서 해당 변수가 이탈의 원인이라고 말할 수 없습니다.
  </div>

  <table class="tbl" style="margin-top:16px;">
    <thead><tr><th>변수</th><th>AARRR 단계</th><th>SMD</th><th>프로모션</th><th>비프로모션</th><th>주의</th></tr></thead>
    <tbody>
      <tr><td>is_user_verified</td><td>Needs_user_review</td><td style="color:var(--red)">1.323</td><td>100%</td><td>53.3%</td><td><span class="badge badge-warn">해석 주의</span></td></tr>
      <tr><td>payment_is_ios</td><td>Acquisition_context</td><td style="color:var(--red)">1.019</td><td>0.0%</td><td>34.2%</td><td><span class="badge badge-warn">proxy</span></td></tr>
      <tr><td>age_group</td><td>Needs_user_review</td><td style="color:var(--yellow)">0.437</td><td>평균 29.5세</td><td>평균 34.1세</td><td><span class="badge badge-warn">해석 주의</span></td></tr>
      <tr><td>is_female</td><td>Needs_user_review</td><td style="color:var(--yellow)">0.351</td><td>61.9%</td><td>44.6%</td><td><span class="badge badge-warn">해석 주의</span></td></tr>
      <tr><td>is_premium</td><td>Acquisition_context</td><td style="color:var(--yellow)">0.351</td><td>22.5%</td><td>9.8%</td><td>context only</td></tr>
      <tr><td>is_churn_prevented</td><td>Retention_context</td><td style="color:var(--yellow)">0.127</td><td>15.6%</td><td>20.5%</td><td>historical proxy</td></tr>
      <tr><td>is_basic</td><td>Acquisition_context</td><td>0.112</td><td>60.4%</td><td>65.8%</td><td>context only</td></tr>
    </tbody>
  </table>

  <div class="danger-box" style="margin-top:16px;">
    <strong>is_user_verified, age_group, is_female, is_male</strong>는 <code>Needs_user_review</code> 태그가 붙은 변수입니다. 이 변수들의 AARRR 단계 귀속 자체가 불확실하며, 집단 특성 기술 이상의 해석(예: "젊은 프로모션 고객은 이탈한다")은 금지입니다.
  </div>
</section>

<!-- ⑫ SMD 시각화 -->
<section id="smd-chart">
  <h2>AARRR 단계별 SMD 분포</h2>
  <p>각 AARRR 단계의 평균 SMD(표준화 평균 차이)입니다. 값이 클수록 프로모션 vs 비프로모션 간 그 단계의 피처 구성 차이가 큽니다.</p>

  <div class="chart-wrap">
    <h3>AARRR 단계별 평균 절대 SMD (expanded_feature_set 기준)</h3>
    <canvas id="chartSMD"></canvas>
  </div>

  <div class="info-box" style="margin-top:20px;">
    <strong>해석 요약</strong>
    <ul style="margin-top:8px; padding-left:20px; color:var(--muted); font-size:14px; line-height:2;">
      <li>Needs_user_review (0.604): 가장 큰 차이 — 그러나 해석 주의 변수들</li>
      <li>Acquisition_context (0.263): 결제 환경/가입 맥락이 뚜렷하게 다름 (특히 iOS)</li>
      <li>Retention_context (0.016): 콘텐츠 취향 차이는 작음</li>
      <li>Activation (0.008): Activation 행동 차이는 거의 없음</li>
      <li>Retention (0.008): 관측창 내 시청 행동 차이도 미미함</li>
    </ul>
  </div>
</section>

<!-- ⑬ 해석 주의사항 -->
<section id="caution">
  <h2>해석 주의사항</h2>

  <table class="tbl">
    <thead><tr><th>금지 표현 (Unsafe)</th><th>권장 표현 (Safe)</th></tr></thead>
    <tbody>
      <tr><td style="color:var(--red)">고객 수 ○○명</td><td style="color:var(--green)">subscription-event rows ○○개</td></tr>
      <tr><td style="color:var(--red)">iOS 고객은 충성도가 높다</td><td style="color:var(--green)">비프로모션 rows에서 iOS 결제 환경 비율이 34.2%로 관측됨</td></tr>
      <tr><td style="color:var(--red)">100원딜이 이탈을 유발했다</td><td style="color:var(--green)">프로모션군에서 재구매율이 8.7%p 낮게 관측됨 (관측 차이)</td></tr>
      <tr><td style="color:var(--red)">SHAP이 원인이다</td><td style="color:var(--green)">모델이 해당 피처를 중요하게 학습했음 (모델 설명)</td></tr>
      <tr><td style="color:var(--red)">이 고객은 이탈한다</td><td style="color:var(--green)">이 row의 churn_risk 점수가 높음 (이탈 위험 후보)</td></tr>
      <tr><td style="color:var(--red)">4주차 행동을 보고 판단했다</td><td style="color:var(--green)">day0~20 관측창 내 행동 신호 기준</td></tr>
      <tr><td style="color:var(--red)">이 세그먼트가 최종 고객 유형이다</td><td style="color:var(--green)">provisional representative segment (사용자 승인 전)</td></tr>
    </tbody>
  </table>

  <div class="card" style="margin-top:24px;">
    <h3 style="margin-bottom:16px;">오픈 리스크</h3>
    <table class="tbl">
      <thead><tr><th>리스크</th><th>핸들링</th></tr></thead>
      <tbody>
        <tr><td>segment 이름은 provisional</td><td>사용자 승인 전 final customer type으로 부르지 않는다</td></tr>
        <tr><td>제언은 campaign candidate</td><td>A/B test 전 최종 정책으로 쓰지 않는다</td></tr>
        <tr><td>SHAP은 인과 아님</td><td>model explanation으로만 사용한다</td></tr>
        <tr><td>100원딜 효과는 인과 아님</td><td>관측된 집단 차이로만 말한다</td></tr>
        <tr><td>row-level 분석</td><td>고객 수 또는 unique customer 수로 말하지 않는다</td></tr>
        <tr><td>payment/auth/demographic proxy caution</td><td>제언 근거로 직접 사용하지 않는다</td></tr>
        <tr><td>genre/content mapping caveat</td><td>Movie_Master category mapping 기준 proxy</td></tr>
        <tr><td>day21 이후 행동 미사용</td><td>leakage 방지 설계, 이후 행동으로 사후 판단하지 않는다</td></tr>
        <tr><td>Referral 미측정</td><td>데이터 공백으로 명시, 추가 데이터 수집 필요</td></tr>
        <tr><td>A/B test 필요</td><td>운영 효과는 실험으로 검증해야 한다</td></tr>
      </tbody>
    </table>
  </div>
</section>

<!-- ⑭ 용어 사전 -->
<section id="glossary">
  <h2>변수 용어 사전</h2>
  <p>이 프로젝트에 등장하는 주요 변수명을 한국어로 설명합니다. 변수명은 개발자가 코드에서 쓰는 이름이고, 한국어 설명은 그게 실제로 무슨 뜻인지를 씁니다.</p>

  <h3 style="margin-top:24px;">Acquisition 단계</h3>
  <table class="tbl">
    <thead><tr><th>변수명</th><th>한국어 설명</th><th>값 범위</th></tr></thead>
    <tbody>
      <tr><td><code style="color:#a5b4fc;">is_promotion</code></td><td>100원딜 프로모션으로 가입했는지 여부</td><td>0 (일반) / 1 (100원딜)</td></tr>
      <tr><td><code style="color:#a5b4fc;">is_basic / is_standard / is_premium</code></td><td>가입한 구독 플랜 종류 (베이직·스탠다드·프리미엄)</td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">payment_is_ios / android / mobile / pc</code></td><td>결제가 이루어진 환경 (iOS 앱스토어, 안드로이드, 모바일웹, PC). <strong>시청 기기가 아님</strong></td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">reg_hour_morning / afternoon / evening / night</code></td><td>가입(회원가입)한 시간대. 아침(morning), 오후(afternoon), 저녁(evening), 밤(night)</td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">reg_is_weekend</code></td><td>주말에 가입했는지 여부</td><td>0 또는 1</td></tr>
    </tbody>
  </table>

  <h3 style="margin-top:24px;">Activation 단계</h3>
  <table class="tbl">
    <thead><tr><th>변수명</th><th>한국어 설명</th><th>값 범위</th></tr></thead>
    <tbody>
      <tr><td><code style="color:#a5b4fc;">is_cold_start_3d_fixed</code></td><td>가입 후 3일 이내에 첫 시청이 없으면 1. "일단 결제만 하고 안 본 상태" 감지. <em>_fixed는 원본 컬럼명과 충돌을 피하려고 붙인 suffix</em></td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">is_cold_start_7d_fixed</code></td><td>가입 후 7일(1주일) 이내에 첫 시청이 없으면 1. 1주차 전체 비활성 신호</td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">is_only_w1</code></td><td>1주차(day0~6)에만 시청하고 2·3주차에는 아예 안 본 경우 1. "반짝 체험 후 이탈" 패턴</td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">is_w1_over_50pct</code></td><td>전체 3주 시청시간 중 1주차 비중이 50% 이상이면 1. 초반 몰아보기 패턴</td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">watch_time_min_w1</code></td><td>1주차(day0~6) 총 시청시간(분)</td><td>0 이상 실수</td></tr>
      <tr><td><code style="color:#a5b4fc;">watch_session_w1</code></td><td>1주차 총 시청 세션 수. 한 번 재생 = 1 세션</td><td>0 이상 정수</td></tr>
    </tbody>
  </table>

  <h3 style="margin-top:24px;">Retention 단계</h3>
  <table class="tbl">
    <thead><tr><th>변수명</th><th>한국어 설명</th><th>값 범위</th></tr></thead>
    <tbody>
      <tr><td><code style="color:#a5b4fc;">watch_time_min_w2 / w3</code></td><td>2주차(day7~13), 3주차(day14~20) 총 시청시간(분). W1 대비 감소 폭이 이탈 예측의 핵심 신호</td><td>0 이상 실수</td></tr>
      <tr><td><code style="color:#a5b4fc;">diff_between_w2_w1</code></td><td>2주차 시청시간 - 1주차 시청시간. 음수면 2주차에 덜 봤다는 뜻</td><td>음수~양수</td></tr>
      <tr><td><code style="color:#a5b4fc;">diff_between_w3_w2</code></td><td>3주차 시청시간 - 2주차 시청시간. 음수면 3주차에 더 줄었다는 뜻</td><td>음수~양수</td></tr>
      <tr><td><code style="color:#a5b4fc;">diff_between_w3_w1</code></td><td>3주차 시청시간 - 1주차 시청시간. 전체 감쇠 폭</td><td>음수~양수</td></tr>
      <tr><td><code style="color:#a5b4fc;">retention_w2_ratio / w3_ratio</code></td><td>2·3주차 시청 유지율(%). 전체 관측일 중 해당 주차에 시청한 날의 비율</td><td>0~100</td></tr>
      <tr><td><code style="color:#a5b4fc;">recency</code></td><td>마지막 시청일부터 관측 종료일(day20)까지의 경과일. 클수록 오래 전에 마지막으로 봤다 = 이탈 위험</td><td>0~20 정수</td></tr>
      <tr><td><code style="color:#a5b4fc;">is_only_w2 / is_only_w3</code></td><td>2주차 또는 3주차에만 시청하고 나머지는 아예 안 본 경우 1</td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">max_inactive_gap_days</code></td><td>관측창(3주) 내 가장 긴 연속 비시청 기간(일)</td><td>0 이상 정수</td></tr>
      <tr><td><code style="color:#a5b4fc;">avg_gap_w3_watch_days</code></td><td>3주차 내 시청일 사이 평균 간격(일). 클수록 드문드문 본 것</td><td>0 이상 실수</td></tr>
      <tr><td><code style="color:#a5b4fc;">watch_ratio_under_1m / under_5m</code></td><td>1분 이하 / 5분 이하 시청 비율. 높으면 "켰다가 바로 끈" 경우가 많다는 뜻</td><td>0~1</td></tr>
      <tr><td><code style="color:#a5b4fc;">active_ratio</code></td><td>전체 관측일(20일) 중 시청한 날의 비율</td><td>0~1</td></tr>
      <tr><td><code style="color:#a5b4fc;">is_churn_prevented</code></td><td>과거에 이탈 방지 혜택(예: 할인 연장)을 받은 이력이 있으면 1. 현재 이탈 여부가 아님</td><td>0 또는 1</td></tr>
    </tbody>
  </table>

  <h3 style="margin-top:24px;">Revenue 단계 / 타겟</h3>
  <table class="tbl">
    <thead><tr><th>변수명</th><th>한국어 설명</th><th>값 범위</th></tr></thead>
    <tbody>
      <tr><td><code style="color:#a5b4fc;">is_repurchase</code></td><td>관측창(day0~20) 이후 구독을 갱신했으면 1, 해지했으면 0. 이 프로젝트의 <strong>예측 타겟</strong>. 피처로 쓰지 않음</td><td>0 또는 1</td></tr>
      <tr><td><code style="color:#a5b4fc;">repurchase_score</code></td><td>모델이 예측한 재구매 확률(0~1). 15x LightGBM OOF 예측값</td><td>0~1 실수</td></tr>
      <tr><td><code style="color:#a5b4fc;">churn_risk</code></td><td>이탈 위험 점수. = 1 - repurchase_score. 1에 가까울수록 이탈 위험 높음</td><td>0~1 실수</td></tr>
    </tbody>
  </table>

  <h3 style="margin-top:24px;">기타 개념어</h3>
  <table class="tbl">
    <thead><tr><th>용어</th><th>설명</th></tr></thead>
    <tbody>
      <tr><td><strong>subscription-event row</strong></td><td>분석 단위. USER_KEY(사용자) × 구독 이벤트 조합. 한 사람이 여러 번 구독하면 여러 row가 생김. "고객 수"와 다름</td></tr>
      <tr><td><strong>관측창 (observation window)</strong></td><td>day0(구독 시작일)부터 day20까지 20일간의 행동만 피처로 사용. day21 이후 행동은 미래 정보라 사용 안 함</td></tr>
      <tr><td><strong>OOF (Out-Of-Fold)</strong></td><td>교차검증에서 각 fold의 검증 데이터에 대한 예측값. 데이터 누수 없이 전체 데이터에 대한 예측값을 만드는 방법</td></tr>
      <tr><td><strong>AUC</strong></td><td>모델 성능 지표. 0.5=랜덤, 1.0=완벽. 이 프로젝트 모델은 0.8787 (꽤 높은 편)</td></tr>
      <tr><td><strong>SMD (표준화 평균 차이)</strong></td><td>두 집단 간 차이를 표준편차 단위로 나타낸 값. 0.1 미만=작은 차이, 0.3 이상=큰 차이</td></tr>
      <tr><td><strong>proxy</strong></td><td>직접 측정이 어려운 것을 대신 나타내는 변수. 예: is_repurchase는 실제 매출이 아니라 재구매 여부로 Revenue를 대신 측정</td></tr>
      <tr><td><strong>provisional segment</strong></td><td>임시로 만든 세그먼트. 데이터 기반 패턴이지만 아직 사용자(팀) 승인 전이라 "최종 고객 유형"이라고 부르면 안 됨</td></tr>
      <tr><td><strong>W1 / W2 / W3</strong></td><td>관측창을 7일씩 나눈 주차. W1=day0~6, W2=day7~13, W3=day14~20</td></tr>
    </tbody>
  </table>
</section>

</main>

<script>
const C = (id) => document.getElementById(id);
const DARK = '#1a1d27';
const GRID = { color: 'rgba(255,255,255,0.06)' };
const TICK = { color: '#94a3b8', font: { size: 11 } };
const baseOpts = (title) => ({
  responsive: true,
  plugins: {
    legend: { labels: { color: '#e2e8f0', font: { size: 12 } } },
    title: title ? { display: true, text: title, color: '#94a3b8', font: { size: 12 } } : { display: false }
  },
  scales: {
    x: { grid: GRID, ticks: TICK },
    y: { grid: GRID, ticks: TICK }
  }
});

// 1. Funnel bar chart
new Chart(C('chartFunnel'), {
  type: 'bar',
  data: {
    labels: ['Acquisition\n(전체)', 'Activation\n(cold_start_7d 통과)', 'Retention\n(W3 시청 있음)', 'Referral\n(측정불가)', 'Revenue\n(재구매)'],
    datasets: [{
      label: 'row 수 (추정 포함)',
      data: [23343, 14979, 13060, 0, 16702],
      backgroundColor: ['rgba(99,102,241,0.8)', 'rgba(59,130,246,0.8)', 'rgba(20,184,166,0.8)', 'rgba(75,85,99,0.4)', 'rgba(245,158,11,0.8)'],
      borderRadius: 6
    }]
  },
  options: {
    ...baseOpts(),
    plugins: { legend: { display: false } }
  }
});

// 2. Promo split doughnut
new Chart(C('chartPromoSplit'), {
  type: 'doughnut',
  data: {
    labels: ['프로모션 (100원딜)', '비프로모션'],
    datasets: [{ data: [11955, 11388], backgroundColor: ['rgba(168,85,247,0.8)', 'rgba(59,130,246,0.8)'], borderWidth: 0 }]
  },
  options: { responsive: true, plugins: { legend: { labels: { color: '#e2e8f0' } } } }
});

// 3. Reg hour grouped bar
new Chart(C('chartRegHour'), {
  type: 'bar',
  data: {
    labels: ['아침 (morning)', '오후 (afternoon)', '저녁 (evening)', '밤 (night)'],
    datasets: [
      { label: '프로모션', data: [14.6, 24.7, 43.1, 17.6], backgroundColor: 'rgba(168,85,247,0.7)', borderRadius: 4 },
      { label: '비프로모션', data: [24.1, 23.2, 33.9, 18.8], backgroundColor: 'rgba(59,130,246,0.7)', borderRadius: 4 }
    ]
  },
  options: { ...baseOpts(), scales: { x: { grid: GRID, ticks: TICK }, y: { grid: GRID, ticks: { ...TICK, callback: v => v + '%' }, max: 50 } } }
});

// 4. Plan comparison
new Chart(C('chartPlan'), {
  type: 'bar',
  data: {
    labels: ['Basic', 'Standard', 'Premium'],
    datasets: [
      { label: '프로모션', data: [60.4, 17.1, 22.5], backgroundColor: 'rgba(168,85,247,0.7)', borderRadius: 4 },
      { label: '비프로모션', data: [65.8, 24.4, 9.8], backgroundColor: 'rgba(59,130,246,0.7)', borderRadius: 4 }
    ]
  },
  options: {
    ...baseOpts(),
    scales: { x: { grid: GRID, ticks: TICK }, y: { grid: GRID, ticks: { ...TICK, callback: v => v + '%' }, max: 80 } }
  }
});

// 5. Cold start
new Chart(C('chartColdStart'), {
  type: 'bar',
  data: {
    labels: ['cold_start_3d', 'cold_start_7d'],
    datasets: [
      { label: '프로모션', data: [38.5, 63.5], backgroundColor: 'rgba(168,85,247,0.7)', borderRadius: 4 },
      { label: '비프로모션', data: [38.9, 64.1], backgroundColor: 'rgba(59,130,246,0.7)', borderRadius: 4 }
    ]
  },
  options: {
    ...baseOpts(),
    scales: { x: { grid: GRID, ticks: TICK }, y: { grid: GRID, ticks: { ...TICK, callback: v => v + '%' }, max: 80 } }
  }
});

// 6. W1 Pattern
new Chart(C('chartW1Pattern'), {
  type: 'bar',
  data: {
    labels: ['is_only_w1', 'is_w1_over_50pct', 'is_only_w2', 'is_only_w3', 'is_w3_over_50pct'],
    datasets: [
      { label: '프로모션', data: [9.7, 29.1, 7.7, 10.3, 28.4], backgroundColor: 'rgba(168,85,247,0.7)', borderRadius: 4 },
      { label: '비프로모션', data: [10.1, 29.3, 8.3, 9.7, 28.3], backgroundColor: 'rgba(59,130,246,0.7)', borderRadius: 4 }
    ]
  },
  options: {
    ...baseOpts(),
    scales: { x: { grid: GRID, ticks: TICK }, y: { grid: GRID, ticks: { ...TICK, callback: v => v + '%' }, max: 40 } }
  }
});

// 7. Watch decay by segment — 7색 완전 분리, 겹침 방지 오프셋, 포인트 모양 구분
// 색: 빨·주·노·초·파·남·보 (절대 겹치지 않음)
const decayData = [
  { label: '① 위험-W3소멸', data: [89.3,  31.5,  6.6  ], color: '#ef4444' },  // 빨
  { label: '② 위험-초반만', data: [114.1, 25.4,  44.3 ], color: '#f97316' },  // 주
  { label: '③ 위험-비활성', data: [0.0,   0.04,  19.0 ], color: '#eab308' },  // 노
  { label: '④ 중간-W3급감', data: [139.6, 137.8, 33.0 ], color: '#22c55e' },  // 초
  { label: '⑤ 콘텐츠증가',  data: [119.5, 132.9, 175.1], color: '#3b82f6' },  // 파
  { label: '⑥ 안정-고활성', data: [154.7, 37.2,  280.9], color: '#6366f1' },  // 남
  { label: '⑦ 일반관찰',    data: [71.9,  104.3, 88.7 ], color: '#a855f7' },  // 보
];

// W1에서 값 순서대로 y오프셋 배정 (겹침 방지)
// 값 기준 정렬: 0.0, 71.9, 89.3, 114.1, 119.5, 139.6, 154.7
// 오프셋: 세그먼트 인덱스별로 사전에 지정 (W1기준 내림차순)
// di: 0=89.3(빨), 1=114.1(주), 2=0.0(노), 3=139.6(초), 4=119.5(파), 5=154.7(남), 6=71.9(보)
// W1 y순서(높은값=위): 남⑥>초④>파⑤>주②>빨①>보⑦>노③
const W1_OFFSETS = [-14, -14, 16, 16, -14, -28, 28];  // di별 W1 전용 오프셋
// W2 y순서: 초④≈파⑤>보⑦>빨①>주②>남⑥>노③
const W2_OFFSETS = [-28, 16, 28, -14, -14, 16, -14];
// W3 y순서: 남⑥>파⑤>보⑦>주②>초④>빨①>노③
const W3_OFFSETS = [16, -28, 16, 16, -14, -14, -14];
const ALL_OFFSETS = [W1_OFFSETS, W2_OFFSETS, W3_OFFSETS];

// 포인트 모양 커스텀 (pointStyle 대신 canvas로)
const POINT_DRAWERS = [
  (ctx, x, y, r, color) => { // ① 빨 — 원
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI*2);
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = '#0f1117'; ctx.lineWidth = 2; ctx.stroke();
  },
  (ctx, x, y, r, color) => { // ② 주 — 사각
    ctx.beginPath(); ctx.rect(x-r, y-r, r*2, r*2);
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = '#0f1117'; ctx.lineWidth = 2; ctx.stroke();
  },
  (ctx, x, y, r, color) => { // ③ 노 — 삼각
    ctx.beginPath(); ctx.moveTo(x, y-r); ctx.lineTo(x+r, y+r); ctx.lineTo(x-r, y+r); ctx.closePath();
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = '#0f1117'; ctx.lineWidth = 2; ctx.stroke();
  },
  (ctx, x, y, r, color) => { // ④ 초 — 마름모
    ctx.beginPath(); ctx.moveTo(x, y-r); ctx.lineTo(x+r, y); ctx.lineTo(x, y+r); ctx.lineTo(x-r, y); ctx.closePath();
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = '#0f1117'; ctx.lineWidth = 2; ctx.stroke();
  },
  (ctx, x, y, r, color) => { // ⑤ 파 — 별(★)
    ctx.save(); ctx.translate(x, y);
    ctx.beginPath();
    for(let i=0; i<5; i++){
      const a = (i*4*Math.PI/5) - Math.PI/2;
      const b = (i*4*Math.PI/5 + 2*Math.PI/5) - Math.PI/2;
      i===0 ? ctx.moveTo(r*Math.cos(a), r*Math.sin(a)) : ctx.lineTo(r*Math.cos(a), r*Math.sin(a));
      ctx.lineTo((r*0.45)*Math.cos(b), (r*0.45)*Math.sin(b));
    }
    ctx.closePath();
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = '#0f1117'; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.restore();
  },
  (ctx, x, y, r, color) => { // ⑥ 남 — 육각
    ctx.save(); ctx.translate(x, y);
    ctx.beginPath();
    for(let i=0; i<6; i++){ const a=i*Math.PI/3 - Math.PI/6; i===0?ctx.moveTo(r*Math.cos(a),r*Math.sin(a)):ctx.lineTo(r*Math.cos(a),r*Math.sin(a)); }
    ctx.closePath();
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = '#0f1117'; ctx.lineWidth = 2; ctx.stroke();
    ctx.restore();
  },
  (ctx, x, y, r, color) => { // ⑦ 보 — X(십자)
    ctx.save(); ctx.translate(x, y); ctx.rotate(Math.PI/4);
    ctx.strokeStyle = color; ctx.lineWidth = r*0.7;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-r,0); ctx.lineTo(r,0); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0,-r); ctx.lineTo(0,r); ctx.stroke();
    ctx.restore();
  },
];

const decayPlugin = {
  id: 'decayPlugin',
  afterDatasetsDraw(chart) {
    const ctx2 = chart.ctx;
    chart.data.datasets.forEach((ds, di) => {
      const meta = chart.getDatasetMeta(di);
      const color = ds.borderColor;
      const R = 7;
      meta.data.forEach((pt, pi) => {
        const val = ds.data[pi];
        if (val === null || val === undefined) return;

        // 포인트 직접 그리기
        ctx2.save();
        POINT_DRAWERS[di](ctx2, pt.x, pt.y, R, color);
        ctx2.restore();

        // 수치 라벨
        const offset = ALL_OFFSETS[pi][di];
        ctx2.save();
        ctx2.font = 'bold 11px sans-serif';
        ctx2.fillStyle = color;
        ctx2.textAlign = 'center';
        ctx2.textBaseline = 'middle';
        ctx2.fillText(val < 1 ? '0분' : val.toFixed(1) + '분', pt.x, pt.y + offset);
        ctx2.restore();
      });
    });
  }
};

new Chart(C('chartWatchDecay'), {
  type: 'line',
  plugins: [decayPlugin],
  data: {
    labels: ['W1 (day0~6)', 'W2 (day7~13)', 'W3 (day14~20)'],
    datasets: decayData.map((d, di) => ({
      label: d.label,
      data: d.data,
      borderColor: d.color,
      backgroundColor: 'transparent',
      borderWidth: 2.5,
      pointRadius: 0,        // 기본 포인트 끄고 플러그인이 직접 그림
      pointHoverRadius: 0,
      tension: 0.15,
      fill: false,
    }))
  },
  options: {
    responsive: true,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => {
            const v = ctx.parsed.y;
            const avg = [100, 98, 99][ctx.dataIndex];
            const pct = avg > 0 ? ((v / avg) * 100).toFixed(0) : '—';
            return ` ${ctx.dataset.label}: ${v < 1 ? '0' : v.toFixed(1)}분 (전체평균의 ${pct}%)`;
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
});

// 8. Weekly watch compare promo vs nonpromo
new Chart(C('chartWeekCompare'), {
  type: 'bar',
  data: {
    labels: ['W1', 'W2', 'W3'],
    datasets: [
      { label: '프로모션', data: [100.4, 98.1, 99.1], backgroundColor: 'rgba(168,85,247,0.7)', borderRadius: 4 },
      { label: '비프로모션', data: [99.9, 97.6, 98.5], backgroundColor: 'rgba(59,130,246,0.7)', borderRadius: 4 }
    ]
  },
  options: {
    ...baseOpts(),
    scales: {
      x: { grid: GRID, ticks: TICK },
      y: { grid: GRID, ticks: { ...TICK, callback: v => v + '분' }, min: 90, max: 110 }
    }
  }
});

// 9. Retention key features compare
new Chart(C('chartRetentionCompare'), {
  type: 'bar',
  data: {
    labels: ['watch_time_w1', 'watch_time_w2', 'watch_time_w3', 'total_watch_time', 'watch_days', 'active_ratio'],
    datasets: [
      { label: '프로모션 평균', data: [100.4, 98.1, 99.1, 297.6, 3.58, 0.170], backgroundColor: 'rgba(168,85,247,0.7)', borderRadius: 4 },
      { label: '비프로모션 평균', data: [99.9, 97.6, 98.5, 296.0, 3.53, 0.168], backgroundColor: 'rgba(59,130,246,0.7)', borderRadius: 4 }
    ]
  },
  options: { ...baseOpts() }
});

// 10. Revenue doughnut
new Chart(C('chartRevenueDist'), {
  type: 'doughnut',
  data: {
    labels: ['재구매 (71.6%)', '이탈 (28.4%)'],
    datasets: [{ data: [16702, 6641], backgroundColor: ['rgba(34,197,94,0.8)', 'rgba(239,68,68,0.8)'], borderWidth: 0 }]
  },
  options: { responsive: true, plugins: { legend: { labels: { color: '#e2e8f0' } } } }
});

// 11. Revenue by promo grouped
new Chart(C('chartRevenueByPromo'), {
  type: 'bar',
  data: {
    labels: ['프로모션', '비프로모션'],
    datasets: [
      { label: '재구매율', data: [67.4, 75.9], backgroundColor: ['rgba(168,85,247,0.8)', 'rgba(59,130,246,0.8)'], borderRadius: 6 }
    ]
  },
  options: {
    ...baseOpts(),
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: GRID, ticks: TICK },
      y: { grid: GRID, ticks: { ...TICK, callback: v => v + '%' }, min: 0, max: 100 }
    }
  }
});

// 12. 2x2 cohort
new Chart(C('chartCohort2x2'), {
  type: 'bar',
  data: {
    labels: ['프로모션×재구매', '프로모션×이탈', '비프로모션×재구매', '비프로모션×이탈'],
    datasets: [{
      label: 'row 수',
      data: [8037, 3867, 8520, 2655],
      backgroundColor: ['rgba(99,102,241,0.8)', 'rgba(239,68,68,0.8)', 'rgba(34,197,94,0.8)', 'rgba(245,158,11,0.8)'],
      borderRadius: 6
    }]
  },
  options: {
    ...baseOpts(),
    plugins: { legend: { display: false } }
  }
});

// 13. SMD by AARRR stage
new Chart(C('chartSMD'), {
  type: 'bar',
  data: {
    labels: ['Needs_user_review', 'Acquisition_context', 'Retention_context', 'Retention', 'Activation'],
    datasets: [{
      label: '평균 절대 SMD',
      data: [0.604, 0.263, 0.016, 0.008, 0.008],
      backgroundColor: ['rgba(239,68,68,0.8)', 'rgba(245,158,11,0.8)', 'rgba(59,130,246,0.7)', 'rgba(20,184,166,0.7)', 'rgba(59,130,246,0.7)'],
      borderRadius: 6
    }]
  },
  options: {
    ...baseOpts(),
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: GRID, ticks: TICK, title: { display: true, text: 'avg |SMD|', color: '#94a3b8' } },
      y: { grid: GRID, ticks: TICK }
    }
  }
});

// 14. Referral effect radar/bar
new Chart(C('chartReferralEffect'), {
  type: 'bar',
  data: {
    labels: ['Acquisition\n(CAC 절감)', 'Activation\n(초기 이탈 방어)', 'Retention\n(추천인 유지 동기)', 'Referral\n(K-factor 확보)', 'Revenue\n(이탈 방어+신규)'],
    datasets: [{
      label: '기대 효과 강도 (추정, 1~5)',
      data: [4, 3, 4, 5, 3],
      backgroundColor: [
        'rgba(99,102,241,0.8)', 'rgba(59,130,246,0.8)',
        'rgba(20,184,166,0.8)', 'rgba(168,85,247,0.8)',
        'rgba(245,158,11,0.8)'
      ],
      borderRadius: 6
    }]
  },
  options: {
    ...baseOpts(),
    plugins: { legend: { display: false },
      tooltip: { callbacks: { label: ctx => `기대 강도: ${ctx.parsed.y}/5` } }
    },
    scales: {
      x: { grid: GRID, ticks: TICK },
      y: { grid: GRID, ticks: TICK, min: 0, max: 5,
           title: { display: true, text: '기대 효과 강도 (추정)', color: '#94a3b8' } }
    }
  }
});

// Sidebar active state
const sections = document.querySelectorAll('section');
const links = document.querySelectorAll('#sidebar a');
const obs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      links.forEach(l => l.classList.remove('active'));
      const active = document.querySelector('#sidebar a[href="#' + e.target.id + '"]');
      if (active) active.classList.add('active');
    }
  });
}, { threshold: 0.3 });
sections.forEach(s => obs.observe(s));
</script>
</body>
</html>
"""

out = Path("park.ingyeom/aarrr_visual_guide.html")
out.write_text(HTML, encoding="utf-8")
print(f"완료: {out}")
print(f"파일 크기: {out.stat().st_size:,} bytes")
