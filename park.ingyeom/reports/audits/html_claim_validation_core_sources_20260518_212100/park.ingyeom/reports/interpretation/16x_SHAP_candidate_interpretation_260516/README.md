# 16x_SHAP_candidate_interpretation_payment_removed_retry_260516

## Retry reason
The previous 16x retry is recorded as failed because payment_is_* remained in SHAP input. This retry deletes the failed active 16x outputs and rebuilds 16x from the 15x expanded_no_payment_device feature list.

## Hard gate
Before any model fit, SHAP calculation, or figure generation, 16x_payment_removed_input_gate.csv checks that payment_is_mobile, payment_is_pc, payment_is_android, and payment_is_ios are absent from SHAP input. Expected feature counts are 76 / 75 / 75 / 75 for overall_with_promotion, overall_without_promotion, promotion_only, and nonpromotion_only.

Gate status: PASS  
Final status: PASS  
Stop reason: 

## Interpretation limits
payment_device is a payment device or payment environment proxy, not a viewing device. SHAP is model explanation, not causal effect. 17x segmentation must not use payment/auth/demographic proxy as representative rules.
