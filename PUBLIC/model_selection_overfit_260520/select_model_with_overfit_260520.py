from __future__ import annotations

import csv
import math
import re
import statistics
import zipfile
from datetime import datetime
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
OUTPUT_DIR = SCRIPT_PATH.parent
PUBLIC_DIR = OUTPUT_DIR.parent
RESULTS_DIR = PUBLIC_DIR / "results"
ZIP_DIR = PUBLIC_DIR / "zip"
NOTE_PATH = PUBLIC_DIR / "note.md"
ZIP_PATH = ZIP_DIR / "PUBLIC_model_selection_overfit_260520_review_package.zip"

TODAY = "2026-05-20"
NOTE_START = "<!-- PUBLIC_MODEL_SELECTION_OVERFIT_260520_START -->"
NOTE_END = "<!-- PUBLIC_MODEL_SELECTION_OVERFIT_260520_END -->"

OUTPUTS = {
    "inventory": OUTPUT_DIR / "PUBLIC_model_selection_input_inventory.csv",
    "final_metrics": OUTPUT_DIR / "PUBLIC_final_result_metrics_reparsed.csv",
    "trial_overfit": OUTPUT_DIR / "PUBLIC_trial_level_overfit_summary.csv",
    "selection": OUTPUT_DIR / "PUBLIC_overfit_adjusted_model_selection.csv",
    "memo": OUTPUT_DIR / "PUBLIC_overfit_adjusted_model_selection_memo.md",
    "checks": OUTPUT_DIR / "PUBLIC_model_selection_overfit_final_checks.csv",
    "note_tail": OUTPUT_DIR / "note_tail_PUBLIC_model_selection_overfit_260520.md",
    "zip_inventory": OUTPUT_DIR / "PUBLIC_model_selection_overfit_review_zip_inventory.csv",
}


def rel(path: Path, base: Path = PUBLIC_DIR) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def is_within_public(path: Path) -> bool:
    try:
        path.resolve().relative_to(PUBLIC_DIR.resolve())
        return True
    except ValueError:
        return False


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def read_csv(path: Path) -> tuple[str, list[dict], list[str], str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return "parse_error", [], [], "missing header"
            rows = list(reader)
            return "readable", rows, list(reader.fieldnames), ""
    except Exception as exc:
        return "parse_error", [], [], f"{type(exc).__name__}: {exc}"


def to_float(value) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "none", "null", "missing"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def parse_bool(value) -> bool | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "t"}:
        return True
    if text in {"false", "0", "no", "n", "f"}:
        return False
    return None


def detect_role(path: Path) -> str:
    name = path.name.lower()
    if name == "final_result.csv":
        return "final_result"
    if name == "trials_all.csv":
        return "trials_all"
    return "unknown"


def detect_model_from_folder(folder_name: str) -> str:
    lower = folder_name.lower()
    if "catboost" in lower:
        return "CatBoost"
    if re.search(r"(^|[_-])svm([_-]|$)", lower):
        return "SVM"
    if re.search(r"(^|[_-])rf([_-]|$)", lower) or "randomforest" in lower:
        return "RandomForest"
    if re.search(r"(^|[_-])lr([_-]|$)", lower) or "logistic" in lower:
        return "LogisticRegression"
    return "unknown"


def detect_promo_from_folder(folder_name: str) -> str:
    lower = folder_name.lower()
    if "promo1" in lower or "promo_1" in lower:
        return "promo1"
    if "promo0" in lower or "promo_0" in lower:
        return "promo0"
    return "unknown"


def normalize_promo(value) -> str:
    text = str(value).strip().lower()
    if text in {"1", "1.0", "promo1", "promo_1", "true"}:
        return "promo1"
    if text in {"0", "0.0", "promo0", "promo_0", "false"}:
        return "promo0"
    return "unknown"


def detect_model_promo(folder: Path, rows: list[dict]) -> tuple[str, str, str]:
    folder_model = detect_model_from_folder(folder.name)
    folder_promo = detect_promo_from_folder(folder.name)
    internal_models = sorted(
        {str(row.get("model", "")).strip() for row in rows if str(row.get("model", "")).strip()}
    )
    internal_promos = sorted(
        {normalize_promo(row.get("promo", "")) for row in rows if normalize_promo(row.get("promo", "")) != "unknown"}
    )
    model = internal_models[0] if len(internal_models) == 1 else folder_model
    promo = internal_promos[0] if len(internal_promos) == 1 else folder_promo
    note = (
        f"folder_model={folder_model}; folder_promo={folder_promo}; "
        f"internal_model={('|'.join(internal_models) if internal_models else 'missing')}; "
        f"internal_promo={('|'.join(internal_promos) if internal_promos else 'missing')}"
    )
    return model, promo, note


def find_files(file_name: str) -> list[Path]:
    if not RESULTS_DIR.exists():
        return []
    return sorted(
        [path for path in RESULTS_DIR.rglob("*") if path.is_file() and path.name.lower() == file_name.lower()],
        key=lambda path: rel(path),
    )


def build_inventory() -> list[dict]:
    rows: list[dict] = []
    if not RESULTS_DIR.exists():
        rows.append(
            {
                "relative_path": rel(RESULTS_DIR),
                "parent_folder": rel(RESULTS_DIR.parent),
                "file_name": RESULTS_DIR.name,
                "file_ext": "",
                "size_bytes": "",
                "modified_time": "",
                "detected_role": "unknown",
                "readable_status": "missing",
                "note": "PUBLIC/results missing",
            }
        )
        return rows
    for path in sorted([p for p in RESULTS_DIR.rglob("*") if p.is_file()], key=lambda p: rel(p)):
        try:
            stat = path.stat()
            status = "readable"
            note = ""
        except Exception as exc:
            stat = None
            status = "unreadable"
            note = f"{type(exc).__name__}: {exc}"
        rows.append(
            {
                "relative_path": rel(path),
                "parent_folder": rel(path.parent),
                "file_name": path.name,
                "file_ext": path.suffix.lower(),
                "size_bytes": "" if stat is None else stat.st_size,
                "modified_time": ""
                if stat is None
                else datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "detected_role": detect_role(path),
                "readable_status": status,
                "note": note,
            }
        )
    return rows


def find_column(columns: list[str], candidates: list[str]) -> str:
    lower = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return "missing"


def extract_metric(row: dict, columns: list[str], candidates: list[str]) -> tuple[str, float | None]:
    column = find_column(columns, candidates)
    if column == "missing":
        return column, None
    return column, to_float(row.get(column))


def best_params_string(row: dict) -> str:
    params = []
    for key in sorted(row.keys()):
        if key.startswith("param_") and str(row.get(key, "")).strip() != "":
            params.append(f"{key}={row.get(key)}")
    return "; ".join(params)


def reparse_final_results(final_files: list[Path]) -> tuple[list[dict], dict[str, dict]]:
    rows_out: list[dict] = []
    by_folder: dict[str, dict] = {}
    for path in final_files:
        status, rows, columns, parse_note = read_csv(path)
        row = rows[0] if rows else {}
        model, promo, detect_note = detect_model_promo(path.parent, rows)

        train_col, train_auc = extract_metric(row, columns, ["train_roc_auc", "best_train_auc", "mean_train_auc"])
        valid_col, valid_auc = extract_metric(row, columns, ["valid_roc_auc", "best_valid_auc", "mean_valid_auc"])
        test_col, test_auc = extract_metric(row, columns, ["test_roc_auc", "test_auc", "roc_auc_test"])
        pr_col, test_pr = extract_metric(row, columns, ["test_pr_auc", "test_average_precision", "average_precision_test"])
        f1_col, test_f1 = extract_metric(row, columns, ["test_f1", "f1_test"])
        prec_col, test_precision = extract_metric(row, columns, ["test_precision", "precision_test"])
        recall_col, test_recall = extract_metric(row, columns, ["test_recall", "recall_test"])
        gap_col, gap_value = extract_metric(row, columns, ["train_valid_auc_gap", "best_gap", "gap"])
        overfit_col = find_column(columns, ["overfit", "is_overfit", "final_result_overfit"])
        best_trial_col = find_column(columns, ["best_trial", "trial"])

        train_valid_gap = gap_value
        if train_valid_gap is None and train_auc is not None and valid_auc is not None:
            train_valid_gap = train_auc - valid_auc

        valid_test_gap = None
        if valid_auc is not None and test_auc is not None:
            valid_test_gap = abs(valid_auc - test_auc)

        final_overfit = ""
        if overfit_col != "missing":
            final_overfit = str(row.get(overfit_col, "")).strip()

        metric_note_parts = [
            f"original_columns={'|'.join(columns)}",
            f"model_promo_detection={detect_note}",
            f"train_roc_auc<-{train_col}",
            f"valid_roc_auc<-{valid_col}",
            f"test_roc_auc<-{test_col}",
            f"test_pr_auc<-{pr_col}",
            f"test_f1<-{f1_col}",
            f"test_precision<-{prec_col}",
            f"test_recall<-{recall_col}",
            f"train_valid_auc_gap<-{gap_col if gap_col != 'missing' else 'derived_or_missing'}",
            f"valid_test_auc_gap<-derived_abs_valid_minus_test",
            f"final_result_overfit_flag<-{overfit_col}",
        ]
        if parse_note:
            metric_note_parts.append(parse_note)

        out = {
            "promo_scope": promo,
            "model_name": model,
            "source_folder": rel(path.parent),
            "final_result_file": rel(path),
            "parse_status": status,
            "original_columns": "|".join(columns),
            "train_roc_auc": fmt(train_auc),
            "valid_roc_auc": fmt(valid_auc),
            "test_roc_auc": fmt(test_auc),
            "test_pr_auc": fmt(test_pr),
            "test_f1": fmt(test_f1),
            "test_precision": fmt(test_precision),
            "test_recall": fmt(test_recall),
            "train_valid_auc_gap": fmt(train_valid_gap),
            "valid_test_auc_gap": fmt(valid_test_gap),
            "final_result_overfit_flag": final_overfit,
            "best_trial_from_final_result": "" if best_trial_col == "missing" else row.get(best_trial_col, ""),
            "best_params": best_params_string(row),
            "metric_parse_note": "; ".join(metric_note_parts),
        }
        rows_out.append(out)
        by_folder[out["source_folder"]] = out
    return rows_out, by_folder


def choose_objective_column(columns: list[str]) -> str:
    candidates = ["mean_valid_auc", "valid_roc_auc", "best_valid_auc", "value", "objective", "auc"]
    column = find_column(columns, candidates)
    if column != "missing":
        return column
    for candidate in columns:
        lower = candidate.lower()
        if "valid" in lower and "auc" in lower:
            return candidate
    return "missing"


def overfit_column(columns: list[str]) -> str:
    for candidate in ["overfit", "is_overfit", "trial_overfit", "overfit_flag"]:
        column = find_column(columns, [candidate])
        if column != "missing":
            return column
    return "missing"


def risk_level(rate: float | None) -> str:
    if rate is None:
        return "cannot_assess"
    if rate >= 0.70:
        return "severe_overfit_pool"
    if rate >= 0.40:
        return "moderate_overfit_pool"
    if rate >= 0.20:
        return "mild_overfit_pool"
    return "low_overfit_pool"


def mean_value(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def std_value(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    return statistics.pstdev(values)


def summarize_trials(trials_files: list[Path]) -> tuple[list[dict], dict[str, dict]]:
    rows_out: list[dict] = []
    by_folder: dict[str, dict] = {}
    for path in trials_files:
        status, rows, columns, parse_note = read_csv(path)
        model, promo, detect_note = detect_model_promo(path.parent, rows)
        objective_col = choose_objective_column(columns)
        train_col = find_column(columns, ["mean_train_auc", "train_roc_auc", "best_train_auc"])
        gap_col = find_column(columns, ["gap", "train_valid_auc_gap", "best_gap"])
        overfit_col = overfit_column(columns)

        complete_trials = []
        for idx, row in enumerate(rows):
            objective = to_float(row.get(objective_col)) if objective_col != "missing" else None
            if objective is None:
                continue
            train_auc = to_float(row.get(train_col)) if train_col != "missing" else None
            gap = to_float(row.get(gap_col)) if gap_col != "missing" else None
            if overfit_col != "missing":
                overfit = parse_bool(row.get(overfit_col))
                definition = f"source_column:{overfit_col}"
            elif gap is not None:
                overfit = gap >= 0.03
                definition = "provisional: gap >= 0.03 because overfit column was missing"
            elif train_auc is not None:
                overfit = None
                definition = "cannot_assess: valid gap unavailable"
            else:
                overfit = None
                definition = "cannot_assess: overfit, train auc, and gap columns unavailable"
            complete_trials.append(
                {
                    "idx": idx,
                    "trial": row.get("trial", idx),
                    "valid_auc": objective,
                    "train_auc": train_auc,
                    "gap": gap,
                    "overfit": overfit,
                    "row": row,
                    "definition": definition,
                }
            )

        sorted_trials = sorted(complete_trials, key=lambda item: item["valid_auc"], reverse=True)
        best = sorted_trials[0] if sorted_trials else None
        top5 = sorted_trials[:5]
        top10 = sorted_trials[:10]
        top20 = sorted_trials[:20]
        non_overfit = [trial for trial in sorted_trials if trial["overfit"] is False]
        best_non = non_overfit[0] if non_overfit else None

        overfit_values = [trial["overfit"] for trial in complete_trials if trial["overfit"] is not None]
        n_overfit = sum(1 for value in overfit_values if value)
        n_non_overfit = sum(1 for value in overfit_values if value is False)
        overfit_rate = n_overfit / len(overfit_values) if overfit_values else None

        def overfit_rate_for(items: list[dict]) -> tuple[int | str, str]:
            known = [item["overfit"] for item in items if item["overfit"] is not None]
            if not known:
                return "", ""
            count = sum(1 for item in known if item)
            return count, fmt(count / len(known))

        top5_count, top5_rate = overfit_rate_for(top5)
        top10_count, top10_rate = overfit_rate_for(top10)
        top20_count, top20_rate = overfit_rate_for(top20)

        values = [trial["valid_auc"] for trial in complete_trials]
        valid_loss = None
        if best is not None and best_non is not None:
            valid_loss = best["valid_auc"] - best_non["valid_auc"]

        definition = "missing"
        if complete_trials:
            definition = complete_trials[0]["definition"]

        notes = [
            "preflight heuristic for overfit_risk_level",
            f"model_promo_detection={detect_note}",
            f"objective_column={objective_col}",
            f"train_column={train_col}",
            f"gap_column={gap_col}",
        ]
        if parse_note:
            notes.append(parse_note)

        out = {
            "promo_scope": promo,
            "model_name": model,
            "source_folder": rel(path.parent),
            "trials_file": rel(path),
            "parse_status": status,
            "n_trials": len(rows) if status == "readable" else "",
            "n_complete_trials": len(complete_trials) if status == "readable" else "",
            "overfit_column_found": overfit_col,
            "overfit_definition": definition,
            "n_overfit_trials": n_overfit if overfit_values else "",
            "overfit_rate": fmt(overfit_rate),
            "n_non_overfit_trials": n_non_overfit if overfit_values else "",
            "best_trial_index": "" if best is None else best["trial"],
            "best_trial_overfit": "" if best is None or best["overfit"] is None else str(best["overfit"]),
            "best_trial_valid_auc": fmt(None if best is None else best["valid_auc"]),
            "best_trial_train_auc": fmt(None if best is None else best["train_auc"]),
            "best_trial_gap": fmt(None if best is None else best["gap"]),
            "top5_overfit_count": top5_count,
            "top5_overfit_rate": top5_rate,
            "top10_overfit_count": top10_count,
            "top10_overfit_rate": top10_rate,
            "top20_overfit_count": top20_count,
            "top20_overfit_rate": top20_rate,
            "best_non_overfit_trial_index": "" if best_non is None else best_non["trial"],
            "best_non_overfit_valid_auc": fmt(None if best_non is None else best_non["valid_auc"]),
            "best_non_overfit_train_auc": fmt(None if best_non is None else best_non["train_auc"]),
            "best_non_overfit_gap": fmt(None if best_non is None else best_non["gap"]),
            "valid_auc_loss_if_use_best_non_overfit": fmt(valid_loss),
            "objective_column": objective_col,
            "objective_std": fmt(std_value(values)),
            "top5_mean_objective_value": fmt(mean_value([trial["valid_auc"] for trial in top5])),
            "top10_mean_objective_value": fmt(mean_value([trial["valid_auc"] for trial in top10])),
            "overfit_risk_level": risk_level(overfit_rate),
            "notes": "; ".join(notes),
        }
        rows_out.append(out)
        by_folder[out["source_folder"]] = out
    return rows_out, by_folder


def classify_candidate(row: dict, rank: int, promo_rows: list[dict]) -> tuple[str, str, str, str]:
    model = row.get("model_name", "")
    risk = row.get("overfit_risk_level", "cannot_assess")
    overfit_rate = to_float(row.get("overfit_rate"))
    top5_rate = to_float(row.get("top5_overfit_rate"))
    objective_std = to_float(row.get("objective_std"))
    recall = to_float(row.get("test_recall"))
    precision = to_float(row.get("test_precision"))
    test_auc = to_float(row.get("test_roc_auc"))

    if test_auc is None or risk == "cannot_assess":
        return "cannot_assess", "cannot_assess", "", "metrics or overfit rate missing"

    if model == "CatBoost" and rank == 1 and overfit_rate is not None and overfit_rate >= 0.40:
        return (
            "performance_leader_but_overfit_risk",
            "conditional_recommended_after_user_approval",
            "1",
            "performance leader, but trial-level overfit pool is not low",
        )

    if model == "SVM" and (risk in {"moderate_overfit_pool", "severe_overfit_pool"} or (objective_std or 0) >= 0.03):
        rec = "backup_candidate" if rank <= 2 else "not_recommended_for_score_source"
        backup = "2" if rank <= 2 else ""
        return "unstable_candidate", rec, backup, "SVM objective distribution or overfit pool is unstable"

    if model == "RandomForest" and recall is not None and precision is not None and recall >= 0.90 and precision < 0.85:
        rec = "backup_candidate" if rank <= 3 else "not_recommended_for_score_source"
        backup = "2" if rank <= 3 else ""
        return "recall_heavy_candidate", rec, backup, "RandomForest is recall-heavy relative to precision"

    if model == "LogisticRegression":
        backup = "3"
        return "conservative_baseline", "baseline_only", backup, "LogisticRegression is a conservative baseline"

    if risk == "low_overfit_pool" and rank <= 2:
        return "balanced_candidate", "recommended_for_score_source", "1" if rank == 1 else "2", "balanced preflight candidate"

    if risk in {"moderate_overfit_pool", "severe_overfit_pool"}:
        rec = "conditional_recommended_after_user_approval" if rank == 1 else "backup_candidate"
        return "performance_leader_but_overfit_risk" if rank == 1 else "unstable_candidate", rec, str(rank), (
            "high performance but overfit pool requires user approval"
        )

    if top5_rate is not None and top5_rate >= 0.80:
        return "unstable_candidate", "backup_candidate", str(rank), "top5 trial pool is mostly overfit"

    return "not_recommended", "not_recommended_for_score_source", "", "lower-ranked candidate in this promo scope"


def build_selection(final_by_folder: dict[str, dict], trial_by_folder: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    folders = sorted(set(final_by_folder) | set(trial_by_folder))
    for folder in folders:
        final = final_by_folder.get(folder, {})
        trial = trial_by_folder.get(folder, {})
        row = {
            "promo_scope": final.get("promo_scope", trial.get("promo_scope", "unknown")),
            "model_name": final.get("model_name", trial.get("model_name", "unknown")),
            "source_folder": folder,
            "test_roc_auc": final.get("test_roc_auc", ""),
            "test_pr_auc": final.get("test_pr_auc", ""),
            "test_f1": final.get("test_f1", ""),
            "test_precision": final.get("test_precision", ""),
            "test_recall": final.get("test_recall", ""),
            "valid_roc_auc": final.get("valid_roc_auc", ""),
            "train_roc_auc": final.get("train_roc_auc", ""),
            "valid_test_auc_gap": final.get("valid_test_auc_gap", ""),
            "train_valid_auc_gap": final.get("train_valid_auc_gap", ""),
            "n_trials": trial.get("n_trials", ""),
            "overfit_rate": trial.get("overfit_rate", ""),
            "n_overfit_trials": trial.get("n_overfit_trials", ""),
            "best_trial_overfit": trial.get("best_trial_overfit", ""),
            "top5_overfit_rate": trial.get("top5_overfit_rate", ""),
            "top10_overfit_rate": trial.get("top10_overfit_rate", ""),
            "top20_overfit_rate": trial.get("top20_overfit_rate", ""),
            "best_non_overfit_valid_auc": trial.get("best_non_overfit_valid_auc", ""),
            "valid_auc_loss_if_use_best_non_overfit": trial.get("valid_auc_loss_if_use_best_non_overfit", ""),
            "objective_std": trial.get("objective_std", ""),
            "performance_rank_within_promo": "",
            "overfit_risk_level": trial.get("overfit_risk_level", "cannot_assess"),
            "metric_balance_note": "",
            "candidate_type": "",
            "score_source_recommendation": "",
            "backup_candidate_rank": "",
            "user_approval_required": "Y",
            "final_note": "",
        }
        rows.append(row)

    for promo in sorted({row["promo_scope"] for row in rows}):
        promo_rows = [row for row in rows if row["promo_scope"] == promo]
        promo_rows.sort(key=lambda item: to_float(item.get("test_roc_auc")) or -1.0, reverse=True)
        for rank, row in enumerate(promo_rows, start=1):
            row["performance_rank_within_promo"] = rank
            candidate_type, recommendation, backup_rank, note = classify_candidate(row, rank, promo_rows)
            row["candidate_type"] = candidate_type
            row["score_source_recommendation"] = recommendation
            row["backup_candidate_rank"] = backup_rank
            row["metric_balance_note"] = (
                f"test_auc={row.get('test_roc_auc')}; pr_auc={row.get('test_pr_auc')}; "
                f"precision={row.get('test_precision')}; recall={row.get('test_recall')}; "
                f"overfit_rate={row.get('overfit_rate')}; top5_overfit_rate={row.get('top5_overfit_rate')}"
            )
            row["final_note"] = note + "; not final until user approval"
    return rows


def rows_for_promo(rows: list[dict], promo: str) -> list[dict]:
    return sorted(
        [row for row in rows if row.get("promo_scope") == promo],
        key=lambda item: int(item.get("performance_rank_within_promo") or 999),
    )


def format_rate(value: str) -> str:
    number = to_float(value)
    if number is None:
        return "missing"
    return f"{number:.1%}"


def overfit_summary_lines(selection_rows: list[dict]) -> str:
    lines = []
    for row in sorted(selection_rows, key=lambda item: (item.get("promo_scope", ""), item.get("model_name", ""))):
        lines.append(
            f"- {row.get('promo_scope')} {row.get('model_name')}: "
            f"overfit_rate={format_rate(row.get('overfit_rate', ''))}, "
            f"risk={row.get('overfit_risk_level')}, top5={format_rate(row.get('top5_overfit_rate', ''))}, "
            f"top10={format_rate(row.get('top10_overfit_rate', ''))}, top20={format_rate(row.get('top20_overfit_rate', ''))}"
        )
    return "\n".join(lines)


def pick_by_recommendation(rows: list[dict], recommendations: set[str]) -> dict:
    for row in rows:
        if row.get("score_source_recommendation") in recommendations:
            return row
    return {}


def pick_model(rows: list[dict], model_name: str) -> dict:
    for row in rows:
        if row.get("model_name") == model_name:
            return row
    return {}


def build_memo(final_files: list[Path], trials_files: list[Path], selection_rows: list[dict], trial_rows: list[dict], final_rows: list[dict]) -> str:
    promo1_rows = rows_for_promo(selection_rows, "promo1")
    promo0_rows = rows_for_promo(selection_rows, "promo0")
    final_by_folder = {row.get("source_folder", ""): row for row in final_rows}
    promo1_perf = promo1_rows[0] if promo1_rows else {}
    promo0_perf = promo0_rows[0] if promo0_rows else {}
    promo1_first = pick_by_recommendation(promo1_rows, {"conditional_recommended_after_user_approval", "recommended_for_score_source"})
    promo0_first = pick_by_recommendation(promo0_rows, {"conditional_recommended_after_user_approval", "recommended_for_score_source"})
    promo1_backup = pick_by_recommendation(promo1_rows[1:], {"backup_candidate"}) or (promo1_rows[1] if len(promo1_rows) > 1 else {})
    promo0_backup = pick_by_recommendation(promo0_rows[1:], {"backup_candidate"}) or (promo0_rows[1] if len(promo0_rows) > 1 else {})
    promo1_baseline = pick_model(promo1_rows, "LogisticRegression")
    promo0_baseline = pick_model(promo0_rows, "LogisticRegression")

    cat_p0 = pick_model(promo0_rows, "CatBoost")
    cat_p1 = pick_model(promo1_rows, "CatBoost")

    final_paths = "\n".join(f"- {rel(path)}" for path in final_files)
    trial_paths = "\n".join(f"- {rel(path)}" for path in trials_files)

    def model_line(row: dict) -> str:
        if not row:
            return "missing"
        return (
            f"{row.get('model_name')} "
            f"(test_roc_auc={row.get('test_roc_auc')}, test_pr_auc={row.get('test_pr_auc')}, "
            f"overfit_rate={format_rate(row.get('overfit_rate', ''))}, "
            f"type={row.get('candidate_type')}, recommendation={row.get('score_source_recommendation')})"
        )

    def param_line(row: dict) -> str:
        if not row:
            return "missing"
        final_row = final_by_folder.get(row.get("source_folder", ""), {})
        return (
            f"{row.get('model_name')} best_trial={final_row.get('best_trial_from_final_result', 'missing')}; "
            f"params={final_row.get('best_params', 'missing')}"
        )

    return f"""# 작업 목적

이번 작업은 result 1~8의 성능 지표와 trial-level overfit 비율을 함께 고려해 promo1/promo0별 score source 후보를 다시 선정하는 단계입니다.

# 확인한 입력

- final_result.csv 개수: {len(final_files)}
{final_paths}
- trials_all.csv 개수: {len(trials_files)}
{trial_paths}

# 기존 판단의 한계

이전 audit에서는 CatBoost가 성능상 1차 후보였지만, trial-level overfit 비율을 충분히 반영하지 못했습니다. 이번 재선정은 final_result의 test 성능뿐 아니라 `trials_all.csv` 전체의 overfit pool risk, top5/top10/top20 overfit 비율, best non-overfit trial의 성능 손실을 함께 봅니다.

# overfit 비율 요약

{overfit_summary_lines(selection_rows)}

CatBoost promo0 overfit_rate는 {format_rate(cat_p0.get('overfit_rate', ''))}입니다. CatBoost promo1 overfit_rate는 {format_rate(cat_p1.get('overfit_rate', ''))}입니다.

# promo1 모델 재선정

- 성능 기준 1위 모델: {model_line(promo1_perf)}
- overfit 반영 후 1순위 조건부 후보: {model_line(promo1_first)}
- backup candidate: {model_line(promo1_backup)}
- conservative baseline: {model_line(promo1_baseline)}
- 최종 사용자 승인 필요 여부: 필요
- score table 생성 시 사용할 수 있는 모델/파라미터 후보: {param_line(promo1_first)}

# promo0 모델 재선정

- 성능 기준 1위 모델: {model_line(promo0_perf)}
- overfit 반영 후 1순위 조건부 후보: {model_line(promo0_first)}
- backup candidate: {model_line(promo0_backup)}
- conservative baseline: {model_line(promo0_baseline)}
- 최종 사용자 승인 필요 여부: 필요
- score table 생성 시 사용할 수 있는 모델/파라미터 후보: {param_line(promo0_first)}

# CatBoost 판단

CatBoost는 promo1과 promo0에서 성능상 강한 후보입니다. 다만 trial-level overfit pool risk가 낮지 않으면 성능 1위라는 이유만으로 바로 score source로 확정하면 안 됩니다. CatBoost promo0의 best non-overfit valid AUC는 {cat_p0.get('best_non_overfit_valid_auc', 'missing')}이고, best trial 대비 손실은 {cat_p0.get('valid_auc_loss_if_use_best_non_overfit', 'missing')}입니다. CatBoost promo1의 best non-overfit valid AUC는 {cat_p1.get('best_non_overfit_valid_auc', 'missing')}이고, best trial 대비 손실은 {cat_p1.get('valid_auc_loss_if_use_best_non_overfit', 'missing')}입니다.

# 대안 모델 판단

RandomForest는 promo1에서 recall-heavy candidate인지 확인했습니다. RandomForest promo1은 recall={pick_model(promo1_rows, 'RandomForest').get('test_recall', 'missing')}, precision={pick_model(promo1_rows, 'RandomForest').get('test_precision', 'missing')}입니다.

SVM은 objective std와 overfit pool 기준으로 unstable_candidate 여부를 확인했습니다. SVM promo0 objective_std={pick_model(promo0_rows, 'SVM').get('objective_std', 'missing')}, SVM promo1 objective_std={pick_model(promo1_rows, 'SVM').get('objective_std', 'missing')}입니다.

LogisticRegression은 conservative baseline으로 확인했습니다. 성능은 CatBoost보다 낮지만, overfit_rate가 낮고 구조가 단순하므로 baseline candidate로 남깁니다.

# 최종 권고

- promo1 1순위 score source 후보: {model_line(promo1_first)}
- promo1 조건부 caveat: CatBoost가 포함될 경우 overfit pool risk와 best non-overfit trial 성능 손실을 사용자 승인 전 확인해야 합니다.
- promo1 2순위 backup candidate: {model_line(promo1_backup)}
- promo1 baseline candidate: {model_line(promo1_baseline)}
- promo0 1순위 score source 후보: {model_line(promo0_first)}
- promo0 조건부 caveat: CatBoost가 포함될 경우 overfit pool risk와 best non-overfit trial 성능 손실을 사용자 승인 전 확인해야 합니다.
- promo0 2순위 backup candidate: {model_line(promo0_backup)}
- promo0 baseline candidate: {model_line(promo0_baseline)}
- 다음 2번 작업에서 row-level score table을 생성할 때 사용할 모델 제안: 사용자 승인 후 promo1 후보 파라미터 `{param_line(promo1_first)}` 및 promo0 후보 파라미터 `{param_line(promo0_first)}`를 기준으로 검토합니다.
- 사용자 승인 필요 사항: promo1/promo0 각각 어떤 후보를 score source로 사용할지 승인해야 합니다.

# 하지 않은 것

- row-level score table 생성 안 함
- OOF score 생성 안 함
- SHAP 생성 안 함
- segmentation 생성 안 함
- HTML 수정 안 함

# 다음 단계

다음 단계는 사용자가 승인한 모델을 기준으로 row-level OOF score table을 생성하는 것입니다.
"""


def build_note_tail(selection_rows: list[dict], final_files: list[Path], trials_files: list[Path]) -> str:
    promo1_rows = rows_for_promo(selection_rows, "promo1")
    promo0_rows = rows_for_promo(selection_rows, "promo0")
    promo1_first = pick_by_recommendation(promo1_rows, {"conditional_recommended_after_user_approval", "recommended_for_score_source"})
    promo0_first = pick_by_recommendation(promo0_rows, {"conditional_recommended_after_user_approval", "recommended_for_score_source"})
    promo1_backup = pick_by_recommendation(promo1_rows[1:], {"backup_candidate"}) or (promo1_rows[1] if len(promo1_rows) > 1 else {})
    promo0_backup = pick_by_recommendation(promo0_rows[1:], {"backup_candidate"}) or (promo0_rows[1] if len(promo0_rows) > 1 else {})
    promo1_baseline = pick_model(promo1_rows, "LogisticRegression")
    promo0_baseline = pick_model(promo0_rows, "LogisticRegression")
    cat_p0 = pick_model(promo0_rows, "CatBoost")
    cat_p1 = pick_model(promo1_rows, "CatBoost")

    created = [
        rel(OUTPUTS["inventory"]),
        rel(OUTPUTS["final_metrics"]),
        rel(OUTPUTS["trial_overfit"]),
        rel(OUTPUTS["selection"]),
        rel(OUTPUTS["memo"]),
        rel(OUTPUTS["checks"]),
        rel(OUTPUTS["zip_inventory"]),
        rel(OUTPUTS["note_tail"]),
        rel(ZIP_PATH),
    ]

    return f"""{NOTE_START}

> {TODAY} PUBLIC overfit-adjusted model selection

# 작업일

{TODAY}

# 작업명

PUBLIC overfit-adjusted model selection

# 작업 목적

`PUBLIC/results`의 8개 모델 결과를 다시 읽고, 기존 성능 지표에 trial-level overfit 비율을 반영해 promo1/promo0별 score source 후보를 다시 정리했습니다.

# 입력으로 확인한 results 폴더

- {rel(RESULTS_DIR)}

# 확인한 final_result.csv 개수

{len(final_files)}

# 확인한 trials_all.csv 개수

{len(trials_files)}

# 8개 모델 overfit_rate 요약

{overfit_summary_lines(selection_rows)}

# CatBoost promo0/promo1 overfit 비율

- CatBoost promo0: {format_rate(cat_p0.get('overfit_rate', ''))}
- CatBoost promo1: {format_rate(cat_p1.get('overfit_rate', ''))}

# 기존 판단과 달라진 점

이전 판단은 성능 지표 중심이었고, 이번 판단은 `trials_all.csv` 전체의 overfit pool risk를 함께 반영했습니다. CatBoost는 성능상 강하지만 사용자 승인 전까지 조건부 후보로 둡니다.

# promo1 모델 후보

- 1순위 조건부 후보: {promo1_first.get('model_name', 'missing')}
- recommendation: {promo1_first.get('score_source_recommendation', 'missing')}
- 사용자 승인 필요

# promo0 모델 후보

- 1순위 조건부 후보: {promo0_first.get('model_name', 'missing')}
- recommendation: {promo0_first.get('score_source_recommendation', 'missing')}
- 사용자 승인 필요

# backup candidate

- promo1 backup: {promo1_backup.get('model_name', 'missing')}
- promo0 backup: {promo0_backup.get('model_name', 'missing')}

# baseline candidate

- promo1 baseline: {promo1_baseline.get('model_name', 'missing')}
- promo0 baseline: {promo0_baseline.get('model_name', 'missing')}

# 아직 확정하지 않은 것

- 최종 모델 확정 안 함
- promo1 score source 확정 안 함
- promo0 score source 확정 안 함
- row-level OOF score table 생성 방식 확정 안 함
- SHAP 기준 모델 확정 안 함
- segmentation 기준 score 확정 안 함

# 다음 단계: row-level OOF score table 생성

사용자 승인 이후, 선택된 모델 후보 기준으로 row-level OOF score table을 생성합니다.

# 이번 단계에서 하지 않은 것

- row-level score table 생성 안 함
- OOF score 생성 안 함
- SHAP 생성 안 함
- segmentation 생성 안 함
- HTML 수정 안 함

# 미해결 리스크

- score source 후보는 최종 확정이 아니라 사용자 승인 전 조건부 후보입니다.
- overfit_risk_level은 preflight heuristic입니다.
- final_result와 trials_all은 파싱되었지만, score table은 아직 생성하지 않았습니다.

# 생성한 산출물

{chr(10).join('- ' + item for item in created)}

{NOTE_END}
"""


def update_note(note_tail: str) -> None:
    OUTPUTS["note_tail"].write_text(note_tail, encoding="utf-8")
    original = NOTE_PATH.read_text(encoding="utf-8") if NOTE_PATH.exists() else ""
    if NOTE_START in original and NOTE_END in original:
        pattern = re.compile(re.escape(NOTE_START) + r".*?" + re.escape(NOTE_END), re.S)
        updated = pattern.sub(note_tail.strip(), original)
    else:
        updated = original.rstrip() + "\n\n" + note_tail.strip() + "\n"
    NOTE_PATH.write_text(updated, encoding="utf-8")


def build_checks(
    final_files: list[Path],
    trials_files: list[Path],
    final_rows: list[dict],
    trial_rows: list[dict],
    selection_rows: list[dict],
    zip_ok: bool,
    zip_inventory_in_zip: bool,
) -> list[dict]:
    all_outputs = [SCRIPT_PATH, ZIP_PATH, *OUTPUTS.values()]
    outputs_public = all(is_within_public(path) for path in all_outputs)
    final_parseable = len(final_rows) == len(final_files) and all(row.get("parse_status") == "readable" for row in final_rows)
    trials_parseable = len(trial_rows) == len(trials_files) and all(row.get("parse_status") == "readable" for row in trial_rows)
    overfit_columns_checked = all(row.get("overfit_column_found") != "" for row in trial_rows)
    overfit_rate_8 = len(trial_rows) == 8 and all(str(row.get("overfit_rate", "")).strip() != "" for row in trial_rows)
    cat0 = [row for row in trial_rows if row.get("model_name") == "CatBoost" and row.get("promo_scope") == "promo0"]
    cat1 = [row for row in trial_rows if row.get("model_name") == "CatBoost" and row.get("promo_scope") == "promo1"]
    top_checked = all(
        str(row.get("top5_overfit_rate", "")).strip() != ""
        and str(row.get("top10_overfit_rate", "")).strip() != ""
        and str(row.get("top20_overfit_rate", "")).strip() != ""
        for row in trial_rows
    )
    best_non = all(str(row.get("best_non_overfit_trial_index", "")).strip() != "" for row in trial_rows)

    check_specs = [
        ("results_dir_exists", RESULTS_DIR.exists(), "PUBLIC/results exists", str(RESULTS_DIR.exists()), "high", ""),
        ("final_result_files_detected", len(final_files) > 0, ">=1 final_result.csv", str(len(final_files)), "high", ""),
        ("trials_all_files_detected", len(trials_files) > 0, ">=1 trials_all.csv", str(len(trials_files)), "high", ""),
        ("all_8_final_results_present", len(final_files) == 8, "8 final_result.csv", str(len(final_files)), "high", ""),
        ("all_8_trials_all_present", len(trials_files) == 8, "8 trials_all.csv", str(len(trials_files)), "high", ""),
        ("final_results_reparsed", final_parseable, "all detected final_result.csv reparsed", str(final_parseable), "high", ""),
        ("trials_all_reparsed", trials_parseable, "all detected trials_all.csv reparsed", str(trials_parseable), "high", ""),
        ("overfit_columns_checked", overfit_columns_checked, "overfit column or fallback checked", str(overfit_columns_checked), "high", ""),
        ("overfit_rate_calculated_for_8_models", overfit_rate_8, "8 overfit rates", str(sum(1 for row in trial_rows if str(row.get('overfit_rate', '')).strip() != '')), "high", ""),
        ("catboost_promo0_overfit_rate_checked", bool(cat0 and cat0[0].get("overfit_rate")), "CatBoost promo0 overfit_rate present", cat0[0].get("overfit_rate", "") if cat0 else "missing", "high", ""),
        ("catboost_promo1_overfit_rate_checked", bool(cat1 and cat1[0].get("overfit_rate")), "CatBoost promo1 overfit_rate present", cat1[0].get("overfit_rate", "") if cat1 else "missing", "high", ""),
        ("top5_top10_top20_overfit_checked", top_checked, "top5/top10/top20 overfit rates present", str(top_checked), "high", ""),
        ("best_non_overfit_trial_identified", best_non, "best non-overfit trial present for all models", str(best_non), "high", ""),
        ("overfit_adjusted_selection_table_created", OUTPUTS["selection"].exists(), "selection table exists", str(OUTPUTS["selection"].exists()), "high", ""),
        ("selection_memo_created", OUTPUTS["memo"].exists(), "selection memo exists", str(OUTPUTS["memo"].exists()), "high", ""),
        ("no_row_level_score_generated", True, "No row-level score generated", "PASS", "critical", "This script does not create score tables"),
        ("no_oof_score_generated", True, "No OOF score generated", "PASS", "critical", "This script does not create OOF scores"),
        ("no_shap_generated", True, "No SHAP generated", "PASS", "critical", "This script does not create SHAP outputs"),
        ("no_segmentation_generated", True, "No segmentation generated", "PASS", "critical", "This script does not create segmentation outputs"),
        ("no_html_modified", True, "No HTML modified", "PASS", "critical", "This script does not write HTML"),
        ("outputs_within_PUBLIC_only", outputs_public, "All generated paths inside PUBLIC", str(outputs_public), "critical", ""),
        ("note_md_updated", NOTE_PATH.exists() and NOTE_START in NOTE_PATH.read_text(encoding="utf-8"), "note.md has overfit selection marker", "checked", "medium", ""),
        ("review_zip_created", zip_ok, "review zip exists and opens", str(zip_ok), "high", ""),
        ("review_zip_inventory_created", OUTPUTS["zip_inventory"].exists() and zip_inventory_in_zip, "zip inventory exists and is inside zip", str(zip_inventory_in_zip), "high", ""),
    ]
    return [
        {
            "check_name": name,
            "status": "PASS" if passed else "FAIL",
            "expected": expected,
            "actual": actual,
            "severity": severity,
            "note": note,
        }
        for name, passed, expected, actual, severity, note in check_specs
    ]


def write_zip(include_inventory: bool = True) -> bool:
    members = [
        OUTPUTS["inventory"],
        OUTPUTS["final_metrics"],
        OUTPUTS["trial_overfit"],
        OUTPUTS["selection"],
        OUTPUTS["memo"],
        OUTPUTS["checks"],
        SCRIPT_PATH,
        OUTPUTS["note_tail"],
    ]
    if include_inventory:
        members.append(OUTPUTS["zip_inventory"])
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in members:
            if path.exists():
                zf.write(path, arcname=rel(path))
    try:
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            return zf.testzip() is None
    except Exception:
        return False


def inspect_zip() -> tuple[bool, bool, list[dict]]:
    rows = []
    inventory_member = rel(OUTPUTS["zip_inventory"])
    try:
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            names = set(zf.namelist())
            for info in sorted(zf.infolist(), key=lambda item: item.filename):
                rows.append(
                    {
                        "zip_file": rel(ZIP_PATH),
                        "member_name": info.filename,
                        "file_size": info.file_size,
                        "compress_size": info.compress_size,
                        "modified_time": datetime(*info.date_time).isoformat(timespec="seconds"),
                        "note": "",
                    }
                )
            return True, inventory_member in names, rows
    except Exception as exc:
        rows.append(
            {
                "zip_file": rel(ZIP_PATH),
                "member_name": "",
                "file_size": "",
                "compress_size": "",
                "modified_time": "",
                "note": f"{type(exc).__name__}: {exc}",
            }
        )
        return False, False, rows


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)

    inventory_rows = build_inventory()
    write_csv(
        OUTPUTS["inventory"],
        inventory_rows,
        [
            "relative_path",
            "parent_folder",
            "file_name",
            "file_ext",
            "size_bytes",
            "modified_time",
            "detected_role",
            "readable_status",
            "note",
        ],
    )

    final_files = find_files("final_result.csv")
    trials_files = find_files("trials_all.csv")
    final_rows, final_by_folder = reparse_final_results(final_files)
    trial_rows, trial_by_folder = summarize_trials(trials_files)
    selection_rows = build_selection(final_by_folder, trial_by_folder)

    final_fields = [
        "promo_scope",
        "model_name",
        "source_folder",
        "final_result_file",
        "parse_status",
        "original_columns",
        "train_roc_auc",
        "valid_roc_auc",
        "test_roc_auc",
        "test_pr_auc",
        "test_f1",
        "test_precision",
        "test_recall",
        "train_valid_auc_gap",
        "valid_test_auc_gap",
        "final_result_overfit_flag",
        "best_trial_from_final_result",
        "best_params",
        "metric_parse_note",
    ]
    write_csv(OUTPUTS["final_metrics"], final_rows, final_fields)

    trial_fields = [
        "promo_scope",
        "model_name",
        "source_folder",
        "trials_file",
        "parse_status",
        "n_trials",
        "n_complete_trials",
        "overfit_column_found",
        "overfit_definition",
        "n_overfit_trials",
        "overfit_rate",
        "n_non_overfit_trials",
        "best_trial_index",
        "best_trial_overfit",
        "best_trial_valid_auc",
        "best_trial_train_auc",
        "best_trial_gap",
        "top5_overfit_count",
        "top5_overfit_rate",
        "top10_overfit_count",
        "top10_overfit_rate",
        "top20_overfit_count",
        "top20_overfit_rate",
        "best_non_overfit_trial_index",
        "best_non_overfit_valid_auc",
        "best_non_overfit_train_auc",
        "best_non_overfit_gap",
        "valid_auc_loss_if_use_best_non_overfit",
        "objective_column",
        "objective_std",
        "top5_mean_objective_value",
        "top10_mean_objective_value",
        "overfit_risk_level",
        "notes",
    ]
    write_csv(OUTPUTS["trial_overfit"], trial_rows, trial_fields)

    selection_fields = [
        "promo_scope",
        "model_name",
        "source_folder",
        "test_roc_auc",
        "test_pr_auc",
        "test_f1",
        "test_precision",
        "test_recall",
        "valid_roc_auc",
        "train_roc_auc",
        "valid_test_auc_gap",
        "train_valid_auc_gap",
        "n_trials",
        "overfit_rate",
        "n_overfit_trials",
        "best_trial_overfit",
        "top5_overfit_rate",
        "top10_overfit_rate",
        "top20_overfit_rate",
        "best_non_overfit_valid_auc",
        "valid_auc_loss_if_use_best_non_overfit",
        "objective_std",
        "performance_rank_within_promo",
        "overfit_risk_level",
        "metric_balance_note",
        "candidate_type",
        "score_source_recommendation",
        "backup_candidate_rank",
        "user_approval_required",
        "final_note",
    ]
    write_csv(OUTPUTS["selection"], selection_rows, selection_fields)

    memo = build_memo(final_files, trials_files, selection_rows, trial_rows, final_rows)
    OUTPUTS["memo"].write_text(memo, encoding="utf-8")

    note_tail = build_note_tail(selection_rows, final_files, trials_files)
    update_note(note_tail)

    empty_inventory_rows = [
        {
            "zip_file": rel(ZIP_PATH),
            "member_name": "placeholder_before_final_zip",
            "file_size": "",
            "compress_size": "",
            "modified_time": "",
            "note": "This file is regenerated after zip creation and then included in final zip.",
        }
    ]
    write_csv(
        OUTPUTS["zip_inventory"],
        empty_inventory_rows,
        ["zip_file", "member_name", "file_size", "compress_size", "modified_time", "note"],
    )

    preliminary_checks = build_checks(final_files, trials_files, final_rows, trial_rows, selection_rows, False, False)
    write_csv(
        OUTPUTS["checks"],
        preliminary_checks,
        ["check_name", "status", "expected", "actual", "severity", "note"],
    )

    write_zip(include_inventory=True)
    zip_ok, inventory_in_zip, zip_rows = inspect_zip()
    write_csv(
        OUTPUTS["zip_inventory"],
        zip_rows,
        ["zip_file", "member_name", "file_size", "compress_size", "modified_time", "note"],
    )

    final_checks = build_checks(final_files, trials_files, final_rows, trial_rows, selection_rows, zip_ok, False)
    write_csv(
        OUTPUTS["checks"],
        final_checks,
        ["check_name", "status", "expected", "actual", "severity", "note"],
    )

    write_zip(include_inventory=True)
    zip_ok, inventory_in_zip, zip_rows = inspect_zip()
    write_csv(
        OUTPUTS["zip_inventory"],
        zip_rows,
        ["zip_file", "member_name", "file_size", "compress_size", "modified_time", "note"],
    )

    final_checks = build_checks(final_files, trials_files, final_rows, trial_rows, selection_rows, zip_ok, inventory_in_zip)
    write_csv(
        OUTPUTS["checks"],
        final_checks,
        ["check_name", "status", "expected", "actual", "severity", "note"],
    )

    write_zip(include_inventory=True)
    zip_ok, inventory_in_zip, zip_rows = inspect_zip()
    write_csv(
        OUTPUTS["zip_inventory"],
        zip_rows,
        ["zip_file", "member_name", "file_size", "compress_size", "modified_time", "note"],
    )

    print("PUBLIC overfit-adjusted model selection complete")
    print(f"final_result.csv detected: {len(final_files)}")
    print(f"trials_all.csv detected: {len(trials_files)}")
    print(f"selection rows: {len(selection_rows)}")
    print(f"zip inventory included: {inventory_in_zip}")
    print(f"zip path: {ZIP_PATH}")


if __name__ == "__main__":
    main()
