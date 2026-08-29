# Model Comparison — Telecom Churn Prediction

Champion model: **xgboost**  
Test ROC-AUC: **0.8404**  
Test F1: **0.6349**  
Optimised threshold: **0.335**

| Model | ROC-AUC (CV) | PR-AUC | F1 | Accuracy | Train (s) |
|---|---|---|---|---|---|
| Xgboost | 0.8502 | 0.6469 | 0.5785 | 0.7972 | 2.7 |
| Catboost | 0.8500 | 0.6490 | 0.6233 | 0.7662 | 12.0 |
| Random Forest | 0.8496 | 0.6481 | 0.6126 | 0.7911 | 11.1 |
| Lightgbm | 0.8491 | 0.6329 | 0.5987 | 0.7643 | 7.7 |
| Logistic Regression | 0.8456 | 0.6564 | 0.6302 | 0.7500 | 0.4 |
| Gradient Boosting | 0.8428 | 0.6517 | 0.5778 | 0.7968 | 22.6 |
| Svm | 0.8262 | 0.5871 | 0.6015 | 0.7892 | 30.0 |
| Decision Tree | 0.8051 | 0.6010 | 0.5955 | 0.7259 | 0.2 |

## Notes
- Out-of-fold metrics from 5-fold stratified cross-validation.
- Threshold tuned to maximise F1 on the validation split.
- Tuned parameters for the champion: `{'max_depth': 3, 'learning_rate': 0.015551366603042033, 'n_estimators': 349, 'subsample': 0.7461913171534129, 'colsample_bytree': 0.6946136576305346, 'min_child_weight': 1, 'scale_pos_weight': 1.0869108316311331}`.