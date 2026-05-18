"""patch_decay.py — retention-decay 섹션 교체"""
content = open('park.ingyeom/reports/audits/build_aarrr_visual_guide.py', encoding='utf-8').read()

# 교체 대상: chartWatchDecay 캔버스부터 chartWeekCompare 섹션 끝까지
START = '  <div class="chart-wrap">\n    <h3>세그먼트별 W1→W2→W3 평균 시청시간 (분)</h3>\n    <canvas id="chartWatchDecay"'
END_MARKER = '    <canvas id="chartWeekCompare"></canvas>\n  </div>'

idx_start = content.find(START)
idx_end = content.find(END_MARKER) + len(END_MARKER)

print(f"Start idx: {idx_start}, End idx: {idx_end}")
if idx_start == -1:
    print("START not found! Trying ascii search...")
    # Try finding by unique ASCII anchor
    idx_start = content.find('chartWatchDecay" style="max-height:380px;"')
    print(f"Fallback start: {idx_start}")

old_block = content[idx_start:idx_end]
print("OLD block length:", len(old_block))
print("OLD block preview:", old_block[:80].encode('ascii','replace').decode())

NEW = '''  <!-- 범례 독립 박스 -->
  <div style="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:16px;">
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <span style="display:inline-block;width:28px;height:3px;background:#ef4444;border-radius:2px;"></span>
      <span style="color:#ef4444;font-weight:700;">① 위험-W3소멸</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <span style="display:inline-block;width:28px;height:3px;background:#f97316;border-radius:2px;"></span>
      <span style="color:#f97316;font-weight:700;">② 위험-초반만시청</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <span style="display:inline-block;width:28px;height:0;border-top:3px dotted #dc2626;"></span>
      <span style="color:#dc2626;font-weight:700;">③ 위험-전체비활성</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <span style="display:inline-block;width:28px;height:3px;background:#f59e0b;border-radius:2px;"></span>
      <span style="color:#f59e0b;font-weight:700;">④ 중간-W3급감</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <span style="display:inline-block;width:28px;height:3px;background:#22c55e;border-radius:2px;"></span>
      <span style="color:#22c55e;font-weight:700;">⑤ 콘텐츠취향-증가</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <span style="display:inline-block;width:28px;height:3px;background:#14b8a6;border-radius:2px;"></span>
      <span style="color:#14b8a6;font-weight:700;">⑥ 안정-고활성</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;">
      <span style="display:inline-block;width:28px;height:3px;background:#94a3b8;border-radius:2px;"></span>
      <span style="color:#94a3b8;font-weight:700;">⑦ 일반관찰</span>
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
          <td style="color:#dc2626;font-weight:700;font-size:16px;">③</td>
          <td><strong>high_risk_low_activity</strong><br>
          <span style="font-size:12px;color:var(--muted);">(관측창 내내 시청 거의 없음 — rows 2.2%, 이탈률 76.5%)</span></td>
          <td>0.0<br><span style="font-size:11px;color:var(--muted);">—</span></td>
          <td>0.0<br><span style="font-size:11px;color:var(--muted);">—</span></td>
          <td>19.0<br><span style="font-size:11px;color:var(--muted);">전체평균의 19%</span></td>
          <td style="color:#dc2626;font-weight:700;">+19.0분<br><span style="font-size:11px;">(W1=0이라 비율 미산출)</span></td>
          <td style="color:#dc2626;">전반 비활성</td>
        </tr>
        <tr>
          <td style="color:#f59e0b;font-weight:700;font-size:16px;">④</td>
          <td><strong>medium_risk_retention_decay</strong><br>
          <span style="font-size:12px;color:var(--muted);">(W1·W2 활발, W3 급감 — rows 13.8%, 이탈률 35.8%)</span></td>
          <td>139.6<br><span style="font-size:11px;color:var(--muted);">전체평균의 139%</span></td>
          <td>137.8<br><span style="font-size:11px;color:var(--muted);">전체평균의 140%</span></td>
          <td style="color:#f59e0b;">33.0<br><span style="font-size:11px;">전체평균의 33%</span></td>
          <td style="color:#f59e0b;font-weight:700;">−106.6분<br><span style="font-size:11px;">(−76.4%)</span></td>
          <td style="color:#f59e0b;">W3 급감</td>
        </tr>
        <tr>
          <td style="color:#22c55e;font-weight:700;font-size:16px;">⑤</td>
          <td><strong>content_preference_target_candidate</strong><br>
          <span style="font-size:12px;color:var(--muted);">(콘텐츠 취향 뚜렷, 시청 꾸준히 증가 — rows 26.8%, 이탈률 9.5%)</span></td>
          <td>119.5<br><span style="font-size:11px;color:var(--muted);">전체평균의 119%</span></td>
          <td>132.9<br><span style="font-size:11px;color:var(--muted);">전체평균의 135%</span></td>
          <td style="color:#22c55e;">175.1<br><span style="font-size:11px;">전체평균의 175%</span></td>
          <td style="color:#22c55e;font-weight:700;">+55.6분<br><span style="font-size:11px;">(+46.5%)</span></td>
          <td style="color:#22c55e;">증가 추세</td>
        </tr>
        <tr>
          <td style="color:#14b8a6;font-weight:700;font-size:16px;">⑥</td>
          <td><strong>stable_retained_user</strong><br>
          <span style="font-size:12px;color:var(--muted);">(재구매율 98.9%, W3에 시청 집중 — rows 5.3%, 이탈률 1.7%)</span></td>
          <td>154.7<br><span style="font-size:11px;color:var(--muted);">전체평균의 154%</span></td>
          <td style="color:#f59e0b;">37.2<br><span style="font-size:11px;">전체평균의 38%</span></td>
          <td style="color:#14b8a6;">280.9<br><span style="font-size:11px;">전체평균의 281%</span></td>
          <td style="color:#14b8a6;font-weight:700;">+126.2분<br><span style="font-size:11px;">(+81.6%)</span></td>
          <td style="color:#14b8a6;">고활성 (W3 집중)</td>
        </tr>
        <tr>
          <td style="color:#94a3b8;font-weight:700;font-size:16px;">⑦</td>
          <td><strong>general_observation</strong><br>
          <span style="font-size:12px;color:var(--muted);">(특정 패턴 미해당 일반 그룹 — rows 34.2%, 전체에서 가장 큰 비중)</span></td>
          <td>71.9<br><span style="font-size:11px;color:var(--muted);">전체평균의 72%</span></td>
          <td>104.3<br><span style="font-size:11px;color:var(--muted);">전체평균의 106%</span></td>
          <td>88.7<br><span style="font-size:11px;color:var(--muted);">전체평균의 89%</span></td>
          <td style="color:#94a3b8;font-weight:700;">+16.8분<br><span style="font-size:11px;">(+23.4%)</span></td>
          <td style="color:#94a3b8;">중간 수준 유지</td>
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
  </div>'''

new_content = content[:idx_start] + NEW + content[idx_end:]
open('park.ingyeom/reports/audits/build_aarrr_visual_guide.py', 'w', encoding='utf-8').write(new_content)
print(f"DONE. New file size: {len(new_content):,} chars")
