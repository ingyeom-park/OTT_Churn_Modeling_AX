"""
patch_darkmode.py
4개 HTML 파일에 다크/라이트 모드 토글 버튼을 추가한다.
"""
from pathlib import Path
import re

# ── 공통 토글 CSS (</style> 바로 앞에 삽입) ──────────────────────────────
TOGGLE_CSS = """
  /* ── Dark/Light mode toggle ── */
  #theme-toggle {
    position: fixed; top: 14px; right: 18px; z-index: 9999;
    background: var(--toggle-bg, rgba(255,255,255,0.12));
    border: 1px solid var(--toggle-border, rgba(255,255,255,0.2));
    border-radius: 999px; padding: 6px 14px;
    cursor: pointer; font-size: 13px; font-weight: 600;
    color: var(--toggle-text, #e2e8f0);
    display: flex; align-items: center; gap: 6px;
    transition: background .2s, color .2s, border-color .2s;
    backdrop-filter: blur(8px);
    box-shadow: 0 2px 8px rgba(0,0,0,.25);
    font-family: inherit;
  }
  #theme-toggle:hover { opacity: .85; }
  body.light-mode #theme-toggle {
    background: rgba(0,0,0,0.06);
    border-color: rgba(0,0,0,0.15);
    color: #1a1d27;
  }
"""

# ── 공통 토글 JS (</body> 바로 앞에 삽입) ────────────────────────────────
TOGGLE_JS = """
<script>
(function(){
  const btn = document.createElement('button');
  btn.id = 'theme-toggle';
  btn.innerHTML = '☀️ 라이트';
  document.body.appendChild(btn);

  const STORAGE_KEY = 'ott-theme';
  const saved = localStorage.getItem(STORAGE_KEY);

  function applyTheme(mode) {
    if (mode === 'light') {
      document.body.classList.add('light-mode');
      btn.innerHTML = '🌙 다크';
      localStorage.setItem(STORAGE_KEY, 'light');
    } else {
      document.body.classList.remove('light-mode');
      btn.innerHTML = '☀️ 라이트';
      localStorage.setItem(STORAGE_KEY, 'dark');
    }
  }

  // 저장된 설정 복원
  if (saved === 'light') applyTheme('light');

  btn.addEventListener('click', function(){
    const isLight = document.body.classList.contains('light-mode');
    applyTheme(isLight ? 'dark' : 'light');
  });
})();
</script>
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 파일별 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 각 파일의 현재 :root와 추가할 light-mode 오버라이드 CSS
FILE_CONFIGS = {
    "park.ingyeom/aarrr_visual_guide.html": {
        "base": "dark",   # 기본이 다크
        "light_override": """
  /* Light mode overrides */
  body.light-mode {
    --bg: #f8f9fa; --card: #ffffff; --border: #dee2e6;
    --text: #212529; --muted: #6c757d; --accent: #4263eb;
    --green: #2f9e44; --red: #c92a2a; --yellow: #e67700;
    --blue: #1971c2; --purple: #7048e8; --teal: #0c8599;
    --orange: #d9480f;
  }
  body.light-mode nav#sidebar { background: #ffffff; border-color: #dee2e6; }
  body.light-mode nav#sidebar a { color: #6c757d; }
  body.light-mode nav#sidebar a:hover,
  body.light-mode nav#sidebar a.active { color: #212529; background: rgba(66,99,235,.08); }
  body.light-mode .card,
  body.light-mode .chart-wrap,
  body.light-mode .kpi-card { background: #ffffff; border-color: #dee2e6; }
  body.light-mode .info-box { background: rgba(66,99,235,.07); border-color: #4263eb; }
  body.light-mode .warn-box { background: rgba(230,119,0,.07); border-color: #e67700; }
  body.light-mode .danger-box { background: rgba(201,42,42,.07); border-color: #c92a2a; }
  body.light-mode .tbl th { background: #f1f3f5; color: #495057; }
  body.light-mode .tbl td { border-color: #e9ecef; }
  body.light-mode .badge-info { background: rgba(25,113,194,.12); color: #1971c2; }
  body.light-mode .badge-ok { background: rgba(47,158,68,.12); color: #2f9e44; }
  body.light-mode .badge-warn { background: rgba(230,119,0,.12); color: #e67700; }
  body.light-mode .badge-danger { background: rgba(201,42,42,.12); color: #c92a2a; }
  body.light-mode .funnel-bar[style*="background: #2a2d3e"] { background: #e9ecef !important; }
  body.light-mode .nav-stage { color: #adb5bd; }
"""
    },
    "park.ingyeom/segment_visual_guide.html": {
        "base": "dark",
        "light_override": """
  /* Light mode overrides */
  body.light-mode {
    --bg: #f8f9fa; --card: #ffffff; --border: #dee2e6;
    --text: #212529; --muted: #6c757d; --accent: #4263eb;
    --green: #2f9e44; --red: #c92a2a; --yellow: #e67700;
    --blue: #1971c2; --purple: #7048e8; --teal: #0c8599;
    --orange: #d9480f;
  }
  body.light-mode nav#sidebar { background: #ffffff; border-color: #dee2e6; }
  body.light-mode nav#sidebar a { color: #6c757d; }
  body.light-mode nav#sidebar a:hover,
  body.light-mode nav#sidebar a.active { color: #212529; background: rgba(66,99,235,.08); }
  body.light-mode .card,
  body.light-mode .chart-wrap,
  body.light-mode .kpi-card { background: #ffffff; border-color: #dee2e6; }
  body.light-mode .info-box { background: rgba(66,99,235,.07); border-color: #4263eb; }
  body.light-mode .warn-box { background: rgba(230,119,0,.07); border-color: #e67700; }
  body.light-mode .danger-box { background: rgba(201,42,42,.07); border-color: #c92a2a; }
  body.light-mode .tbl th { background: #f1f3f5; color: #495057; }
  body.light-mode .tbl td { border-color: #e9ecef; }
  body.light-mode .nav-stage { color: #adb5bd; }
  body.light-mode .rule-box { background: #f1f3f5; border-color: #dee2e6; color: #495057; }
"""
    },
    "park.ingyeom/shap_visual_guide.html": {
        "base": "light",  # 기본이 라이트
        "light_override": """
  /* Dark mode overrides */
  body.dark-mode {
    --bg: #0f1117; --surface: #1a1d27; --surface2: #1e2130;
    --text: #e2e8f0; --text2: #94a3b8; --muted: #6b7280;
    --border: #2a2d3e; --warn: #f59e0b; --danger: #ef4444;
  }
  body.dark-mode nav { background: var(--surface); border-color: var(--border); }
  body.dark-mode .card, body.dark-mode .box { background: var(--surface); border-color: var(--border); }
  body.dark-mode table th { background: var(--surface2); }
  body.dark-mode table td { border-color: var(--surface2); }
"""
    },
    "park.ingyeom/project_guide_v2.html": {
        "base": "light",
        "light_override": """
  /* Dark mode overrides */
  body.dark-mode {
    --bg: #0f1117; --surface: #1a1d27; --surface2: #1e2130;
    --border: #2a2d3e; --text: #e2e8f0; --text2: #94a3b8; --text3: #6b7280;
    --accent: #6366f1; --accent2: #818cf8;
    --danger: #ef4444; --warn: #f59e0b; --success: #22c55e;
    --tag-bg: rgba(99,102,241,.15); --tag-text: #a5b4fc;
    --warn-bg: rgba(245,158,11,.1); --warn-text: #fcd34d;
    --danger-bg: rgba(239,68,68,.1); --danger-text: #fca5a5;
  }
  body.dark-mode .sidebar { background: var(--surface); border-color: var(--border); }
  body.dark-mode .sidebar a { color: var(--text3); }
  body.dark-mode .sidebar a:hover,
  body.dark-mode .sidebar a.active { color: var(--text); background: rgba(99,102,241,.12); }
  body.dark-mode .card,
  body.dark-mode .section-card { background: var(--surface); border-color: var(--border); }
  body.dark-mode table th { background: var(--surface2); color: var(--text2); }
  body.dark-mode table td { border-color: var(--surface2); }
  body.dark-mode code { background: var(--surface2); color: #a5b4fc; }
  body.dark-mode pre { background: var(--surface2); }
"""
    },
}


def patch_file(path_str, config):
    path = Path(path_str)
    html = path.read_text(encoding="utf-8")
    base = config["base"]
    override_css = config["light_override"]

    # 1) </style> 직전에 토글 CSS + 라이트/다크 오버라이드 삽입
    if TOGGLE_CSS.strip() in html:
        print(f"  SKIP (already patched): {path_str}")
        return

    html = html.replace("</style>", TOGGLE_CSS + override_css + "\n</style>", 1)

    # 2) 라이트 기반 파일은 <body>에 class 없음, 다크 기반도 없음 — 그냥 JS로 제어
    #    라이트 기반 파일은 JS에서 기본을 dark로 토글하도록 버튼 텍스트 변경
    if base == "light":
        # 기본이 라이트 → 버튼 초기 텍스트 "🌙 다크", 클릭 시 dark-mode 추가
        js = TOGGLE_JS.replace(
            "btn.innerHTML = '☀️ 라이트';",
            "btn.innerHTML = '🌙 다크';"
        ).replace(
            "if (saved === 'light') applyTheme('light');",
            "if (saved === 'dark') applyTheme('dark'); else applyTheme('light');"
        ).replace(
            # applyTheme light = remove light-mode class, dark = add dark-mode
            "document.body.classList.add('light-mode');\n      btn.innerHTML = '🌙 다크';",
            "document.body.classList.remove('dark-mode');\n      btn.innerHTML = '🌙 다크';"
        ).replace(
            "document.body.classList.remove('light-mode');\n      btn.innerHTML = '☀️ 라이트';",
            "document.body.classList.add('dark-mode');\n      btn.innerHTML = '☀️ 라이트';"
        ).replace(
            "const isLight = document.body.classList.contains('light-mode');",
            "const isLight = !document.body.classList.contains('dark-mode');"
        ).replace(
            "applyTheme(isLight ? 'dark' : 'light');",
            "applyTheme(isLight ? 'dark' : 'light');"
        )
    else:
        js = TOGGLE_JS  # 다크 기반 파일은 그대로

    # 3) </body> 직전에 JS 삽입
    html = html.replace("</body>", js + "\n</body>", 1)

    path.write_text(html, encoding="utf-8")
    print(f"  PATCHED: {path_str} ({path.stat().st_size:,} bytes)")


print("=== 다크/라이트 모드 토글 패치 시작 ===")
for path_str, config in FILE_CONFIGS.items():
    patch_file(path_str, config)
print("=== 완료 ===")
