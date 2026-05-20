# 15_oof_score_or_sensitivity_260520

## stage_name
15_oof_score_or_sensitivity_260520

## stage_status
placeholder_created_blocked_until_model_candidate

## expected_inputs
A fitted candidate model and locked score orientation.

## expected_outputs
OOF score table or sensitivity audit outputs.

## why_this_stage_exists
This stage checks score behavior before interpretation and segmentation.

## what_must_not_be_done_here
Do not skip score-direction checks. Verify churn_risk = 1 - repurchase_score before downstream use.

## next_stage
16_SHAP_candidate_interpretation_260520


## Pipeline guardrail

This folder represents a PUBLIC pipeline stage placeholder or working area.
The existence of this folder does not mean the stage has been executed.
Stage execution requires explicit notebook execution, outputs, final checks, README, note update, and review zip.
Do not treat placeholder folders as completed analysis.

## 파이프라인 가드레일

이 폴더는 PUBLIC 파이프라인 단계의 placeholder 또는 작업 위치이다.
이 폴더가 존재한다고 해서 해당 단계가 실행 완료되었다는 뜻은 아니다.
단계 완료는 노트북 실행, 산출물 생성, final_checks, README, note 업데이트, review zip이 모두 갖춰졌을 때만 말할 수 있다.
placeholder 폴더를 완료된 분석으로 해석하지 않는다.
