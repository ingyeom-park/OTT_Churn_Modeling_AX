import json, os

ROOT = "c:/Code/ott-churn-prediction/PUBLIC"

CONFIGS = [
    {"idx": "01", "model": "catboost", "promo": 0},
    {"idx": "02", "model": "catboost", "promo": 1},
    {"idx": "03", "model": "svm",      "promo": 0},
    {"idx": "04", "model": "svm",      "promo": 1},
    {"idx": "05", "model": "rf",       "promo": 0},
    {"idx": "06", "model": "rf",       "promo": 1},
    {"idx": "07", "model": "lr",       "promo": 0},
    {"idx": "08", "model": "lr",       "promo": 1},
]

MODEL_NAMES = {
    "catboost": "CatBoost",
    "svm":      "SVM",
    "rf":       "RandomForest",
    "lr":       "LogisticRegression",
}

# build_model 함수 내부 코드 (들여쓰기 없이)
SEARCH_SPACES = {
    "catboost": [
        "from catboost import CatBoostClassifier",
        "params = {",
        '    "iterations":    trial.suggest_int("iterations", 100, 1000),',
        '    "depth":         trial.suggest_int("depth", 3, 8),',
        '    "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),',
        '    "l2_leaf_reg":   trial.suggest_float("l2_leaf_reg", 1e-2, 10.0, log=True),',
        '    "border_count":  trial.suggest_int("border_count", 32, 255),',
        "}",
        'model = CatBoostClassifier(**params, loss_function="Logloss", eval_metric="AUC",',
        '                           random_seed=42, verbose=False, allow_writing_files=False)',
        "return model",
    ],
    "svm": [
        "from sklearn.svm import SVC",
        "from sklearn.pipeline import Pipeline",
        "from sklearn.preprocessing import StandardScaler",
        'kernel = trial.suggest_categorical("kernel", ["rbf", "poly"])',
        "params = {",
        '    "C":      trial.suggest_float("C", 1e-2, 100.0, log=True),',
        '    "gamma":  trial.suggest_float("gamma", 1e-4, 1.0, log=True),',
        '    "kernel": kernel,',
        "}",
        'if kernel == "poly":',
        '    params["degree"] = trial.suggest_int("degree", 2, 4)',
        "model = Pipeline([",
        '    ("scaler", StandardScaler()),',
        '    ("svc", SVC(probability=True, random_state=42, **params)),',
        "])",
        "return model",
    ],
    "rf": [
        "from sklearn.ensemble import RandomForestClassifier",
        "params = {",
        '    "n_estimators":     trial.suggest_int("n_estimators", 100, 800),',
        '    "max_depth":        trial.suggest_int("max_depth", 3, 20),',
        '    "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 30),',
        '    "max_features":     trial.suggest_categorical("max_features", ["sqrt", "log2", 0.5]),',
        "}",
        "model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)",
        "return model",
    ],
    "lr": [
        "from sklearn.linear_model import LogisticRegression",
        "from sklearn.pipeline import Pipeline",
        "from sklearn.preprocessing import StandardScaler",
        'penalty = trial.suggest_categorical("penalty", ["l1", "l2"])',
        "params = {",
        '    "C":        trial.suggest_float("C", 1e-3, 100.0, log=True),',
        '    "penalty":  penalty,',
        '    "solver":   "liblinear",',
        '    "max_iter": 2000,',
        "}",
        "model = Pipeline([",
        '    ("scaler", StandardScaler()),',
        '    ("lr", LogisticRegression(random_state=42, **params)),',
        "])",
        "return model",
    ],
}


def make_nb(cfg):
    idx    = cfg["idx"]
    model  = cfg["model"]
    promo  = cfg["promo"]
    mname  = MODEL_NAMES[model]
    fname  = f"FINAL_promo_{promo}.csv"
    nbname = f"{idx}_{model}_promo{promo}.ipynb"
    ss     = SEARCH_SPACES[model]

    cells = []

    def md(src):
        cells.append({"cell_type": "markdown", "metadata": {}, "source": src})

    def code(lines):
        src = "\n".join(lines)
        cells.append({
            "cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [],
            "source": src,
        })

    # ── 0. 제목 ────────────────────────────────────────────────────────────────
    md("\n".join([
        f"# {idx}. {mname} — promo{promo}",
        "",
        f"- 데이터: `PUBLIC/FINAL_promo_{promo}.csv`",
        f"- 모델: {mname}",
        "- HPT: Optuna n_trials=200, 최적화 기준 = mean_valid_roc_auc",
        "- CV: StratifiedKFold n_splits=5, random_state=42",
        "- 과적합 기준: train_auc - valid_auc > 0.03 → overfit=True",
        "- 최적 파라미터 선택: overfit=False 중 mean_valid_auc 최고",
        "- 평가 지표: ROC-AUC, PR-AUC, F1, Precision, Recall",
        "- 산출물: `trials_all.csv`, `final_result.csv`",
    ]))

    # ── 1. imports & 설정 ──────────────────────────────────────────────────────
    code([
        "import warnings",
        "warnings.filterwarnings('ignore')",
        "",
        "import numpy as np",
        "import pandas as pd",
        "from pathlib import Path",
        "",
        "from sklearn.model_selection import StratifiedKFold, train_test_split",
        "from sklearn.metrics import (",
        "    roc_auc_score, average_precision_score,",
        "    f1_score, precision_score, recall_score,",
        ")",
        "import optuna",
        "optuna.logging.set_verbosity(optuna.logging.WARNING)",
        "",
        "RANDOM_STATE = 42",
        "N_TRIALS     = 200",
        "N_SPLITS     = 5",
        "OVERFIT_GAP  = 0.03",
        "TEST_SIZE    = 0.2",
        f"PROMO        = {promo}",
        "",
        f'ROOT    = Path(r"{ROOT}")',
        f'DATA    = ROOT / "{fname}"',
        f'OUT_DIR = ROOT / "results" / "{idx}_{model}_promo{promo}"',
        "OUT_DIR.mkdir(parents=True, exist_ok=True)",
        'print("출력 폴더:", OUT_DIR)',
    ])

    # ── 2. 데이터 로드 및 분리 ─────────────────────────────────────────────────
    code([
        "df = pd.read_csv(DATA)",
        'print(f"데이터 shape: {df.shape}")',
        "print(f\"is_repurchase 분포:\\n{df['is_repurchase'].value_counts()}\")",
        "",
        "TARGET    = 'is_repurchase'",
        "DROP_COLS = ['USER_KEY', TARGET]",
        "FEATURES  = [c for c in df.columns if c not in DROP_COLS]",
        "",
        "X = df[FEATURES].values",
        "y = df[TARGET].values",
        'print(f"\\n피처 수: {len(FEATURES)}")',
        'print(f"샘플 수: {len(y)}")',
        "",
        "X_tv, X_test, y_tv, y_test = train_test_split(",
        "    X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE",
        ")",
        'print(f"\\ntrain_valid: {X_tv.shape[0]}행  |  test: {X_test.shape[0]}행")',
        'print(f"train_valid 양성률: {y_tv.mean():.4f}")',
        'print(f"test 양성률:        {y_test.mean():.4f}")',
    ])

    # ── 3. build_model 함수 ────────────────────────────────────────────────────
    build_lines = ["def build_model(trial):"]
    for line in ss:
        build_lines.append("    " + line)
    code(build_lines)

    # ── 4. Optuna objective ────────────────────────────────────────────────────
    code([
        "def objective(trial):",
        "    model = build_model(trial)",
        "    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)",
        "    train_aucs, valid_aucs = [], []",
        "",
        "    for tr_idx, va_idx in skf.split(X_tv, y_tv):",
        "        X_tr, X_va = X_tv[tr_idx], X_tv[va_idx]",
        "        y_tr, y_va = y_tv[tr_idx], y_tv[va_idx]",
        "        model.fit(X_tr, y_tr)",
        "        train_aucs.append(roc_auc_score(y_tr, model.predict_proba(X_tr)[:, 1]))",
        "        valid_aucs.append(roc_auc_score(y_va, model.predict_proba(X_va)[:, 1]))",
        "",
        "    mean_train = float(np.mean(train_aucs))",
        "    mean_valid = float(np.mean(valid_aucs))",
        "    gap        = mean_train - mean_valid",
        "",
        "    trial.set_user_attr('mean_train_auc', mean_train)",
        "    trial.set_user_attr('mean_valid_auc', mean_valid)",
        "    trial.set_user_attr('gap',            gap)",
        "    trial.set_user_attr('overfit',        gap > OVERFIT_GAP)",
        "    return mean_valid",
        "",
        "study = optuna.create_study(",
        "    direction='maximize',",
        "    sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE)",
        ")",
        "study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)",
        'print("Optuna 완료")',
    ])

    # ── 5. trials_all.csv 저장 ─────────────────────────────────────────────────
    code([
        "rows = []",
        "for t in study.trials:",
        "    row = {",
        "        'trial':          t.number,",
        "        'mean_valid_auc': t.user_attrs.get('mean_valid_auc', float('nan')),",
        "        'mean_train_auc': t.user_attrs.get('mean_train_auc', float('nan')),",
        "        'gap':            t.user_attrs.get('gap',            float('nan')),",
        "        'overfit':        t.user_attrs.get('overfit',        float('nan')),",
        "    }",
        "    row.update(t.params)",
        "    rows.append(row)",
        "",
        "trials_df = pd.DataFrame(rows).sort_values('mean_valid_auc', ascending=False)",
        "trials_df.to_csv(OUT_DIR / 'trials_all.csv', index=False, encoding='utf-8-sig')",
        'print(f"전체 trials: {len(trials_df)}개")',
        "print(f\"과적합(gap>0.03): {int(trials_df['overfit'].sum())}개\")",
        'print("\\n상위 10 trials:")',
        "print(trials_df.head(10)[['trial','mean_valid_auc','mean_train_auc','gap','overfit']].to_string(index=False))",
    ])

    # ── 6. 최적 파라미터 선택 ──────────────────────────────────────────────────
    code([
        "non_overfit = trials_df[trials_df['overfit'] == False]",
        "if len(non_overfit) == 0:",
        "    print('⚠️  과적합이 아닌 trial 없음 → 전체 중 최고 valid AUC 선택')",
        "    best_row = trials_df.iloc[0]",
        "else:",
        "    best_row = non_overfit.sort_values('mean_valid_auc', ascending=False).iloc[0]",
        "",
        "param_cols  = [c for c in trials_df.columns",
        "               if c not in ['trial','mean_valid_auc','mean_train_auc','gap','overfit']]",
        "best_params = best_row[param_cols].to_dict()",
        "",
        'print(f"\\n최적 trial: {int(best_row[\'trial\'])}")',
        'print(f"mean_valid_auc: {best_row[\'mean_valid_auc\']:.4f}")',
        'print(f"gap: {best_row[\'gap\']:.4f}  |  overfit: {best_row[\'overfit\']}")',
        "print('파라미터:', best_params)",
    ])

    # ── 7. 최종 모델 학습 및 test 평가 ────────────────────────────────────────
    code([
        "class _FakeTrial:",
        "    def __init__(self, p): self._p = p",
        "    def suggest_int(self, n, *a, **k):         return int(self._p[n])",
        "    def suggest_float(self, n, *a, **k):       return float(self._p[n])",
        "    def suggest_categorical(self, n, *a, **k): return self._p[n]",
        "",
        "final_model = build_model(_FakeTrial(best_params))",
        "final_model.fit(X_tv, y_tv)",
        "",
        "p_test = final_model.predict_proba(X_test)[:, 1]",
        "y_pred = (p_test >= 0.5).astype(int)",
        "",
        "final_result = {",
        f"    'model':          '{mname}',",
        f"    'promo':          {promo},",
        "    'best_trial':     int(best_row['trial']),",
        "    'best_valid_auc': float(best_row['mean_valid_auc']),",
        "    'best_train_auc': float(best_row['mean_train_auc']),",
        "    'best_gap':       float(best_row['gap']),",
        "    'overfit':        bool(best_row['overfit']),",
        "    'test_roc_auc':   float(roc_auc_score(y_test, p_test)),",
        "    'test_pr_auc':    float(average_precision_score(y_test, p_test)),",
        "    'test_f1':        float(f1_score(y_test, y_pred)),",
        "    'test_precision': float(precision_score(y_test, y_pred)),",
        "    'test_recall':    float(recall_score(y_test, y_pred)),",
        "    'test_n':         int(len(y_test)),",
        "    **{f'param_{k}': v for k, v in best_params.items()},",
        "}",
        "",
        "pd.DataFrame([final_result]).to_csv(",
        "    OUT_DIR / 'final_result.csv', index=False, encoding='utf-8-sig'",
        ")",
        "print('=== 최종 결과 ===')",
        "for k, v in final_result.items():",
        "    print(f'  {k}: {v}')",
        'print(f"\\n산출물 위치: {OUT_DIR}")',
    ])

    nb = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "cells": cells,
    }
    return nb, nbname


for cfg in CONFIGS:
    nb, nbname = make_nb(cfg)
    out_path = os.path.join(ROOT, "notebooks", nbname)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f"생성: {nbname}")

print("\n완료: 8개 노트북 생성")
