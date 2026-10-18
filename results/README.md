# results/

Frozen figure tables written by `03_gold.ipynb`. Population for all tables: the analysis set (Germany in
the territorial scope, content posted 2025-01-01 to 2025-06-30), TikTok and X.

- `t01a_decision_visibility_coded.csv` — Table 1a, coded `decision_visibility` — denominator: `platform_total` (all statements of the platform; a statement counts once per value)
- `t01b_provision_account_coded.csv` — Table 1b, coded service and account measures — denominator: `platform_total`
- `t01c_free_text_classification.csv` — Appendix A, classification of free-text measures — denominator: `platform_total`
- `t01d_measure_types.csv` — Table 1d, measure types after classification — denominator: `platform_total`
- `t01d2_action_classes.csv` — Table 1d (second part), action classes within measure types — denominator: `platform_total`
- `t02_automation_crosstab.csv` — Table 2, automation, detection × decision — denominator: `platform_total`
- `t03_tiktok_automation_by_content_type.csv` — Table 3, automation by `content_type`, TikTok — denominator: `n_rows` (statements per content type; a statement counts once per type)
- `t03b_content_types_by_platform.csv` — Table 3b, content types per platform — denominator: `platform_total` (all statements of the platform; a statement counts once per type)
- `t04a_granularity_means.csv` — Table 4 (means), granularity per platform — denominator: `n_rows` (statements per platform)
- `t04b_fill_rates.csv` — Table 4 (fill rates), fill rate of each optional attribute — denominator: `rows_tiktok`, `rows_x`
- `t04c_decision_facts.csv` — Table 4c, `decision_facts` per platform (ten most frequent values, distinct counts before and after normalisation; read from `silver.analysis_*`) — denominator: `platform_total` (all statements of the platform)
- `t05_weekly_election_share.csv` — Table 5, weekly election share — denominator: `n_total` (statements per platform and week)
- `t06_period_summary.csv` — Table 6, period summary — denominator: `n_total` (statements per platform and period)
- `t06b_independent_campaign_window.csv` — Table 6b, period summary with the independently defined campaign window (dissolution of the Bundestag to polling day; 2025-01-01 to 2025-02-23 within the data), TikTok — denominator: `n_total` (statements per period)
- `t06c_daily_share_jan_13_27.csv` — Table 6c, daily share of the category, TikTok, 2025-01-13 to 2025-01-27 — denominator: `n_total` (statements per day)
- `t07_weekly_automation_share.csv` — Table 7, weekly automation share — denominator: `n_total` (statements per platform and week)
- `t08_weekly_granularity.csv` — Table 8, weekly mean granularity — denominator: `n_total` (statements per platform and week)
- `t09_tiktok_daily_jan_mar.csv` — Table 9, TikTok daily series, 2025-01-01 to 2025-03-31 — denominator: `n_total` (statements per day)
- `t10_automation_by_category.csv` — Table 10, automation by category — denominator: `n_rows` (statements per platform and category)
- `t11_tiktok_granularity_by_automation.csv` — Table 11, granularity by automation status, TikTok — denominator: `n_rows` (statements per period and automation status)
- `t11b_tiktok_granularity_distribution.csv` — Table 11 (distribution), full distribution of both granularity counts — counts only, no shares
- `t12_election_by_content_type.csv` — Table 12, election-category statements by content type and period — denominators: `n_election_period` for `share_of_election_category`, `n_type` for `election_share_within_type`
- `t13a_measure_types_by_period.csv` — Table 13 (a), measure types by period — denominator: `period_total` (statements per group and period)
- `t13b_visibility_actions_by_period.csv` — Table 13 (b), visibility action classes by period — denominator: `visibility_total` (visibility statements per group and period)
- `tB_x_submission_pause.csv` — Appendix B, X submission pause 2025-03-25 to 2025-04-15 — counts only, no shares
- `t14a_de_only_period_summary.csv` — Table 14a, period summary, Germany-only TikTok statements — denominator: `n_total` (Germany-only statements per period)
- `t14b_de_only_weekly.csv` — Table 14b, weekly series, Germany-only TikTok statements — denominator: `n_total` (Germany-only statements per week)
- `t14c_de_only_content_types.csv` — Table 14c, content types of the Germany-only statements — denominators: `subset_total` for `share_of_subset`, `category_total` for `share_of_category` (a statement counts once per type)
- `t14d_de_only_automation.csv` — Table 14d, fully automated decisions per period, Germany-only TikTok statements — denominator: `n_total` (Germany-only statements per period)

## figures/

Written by `04_figures.ipynb` from the tables above, each as PNG (300 dpi) and SVG.

- `figure1_tiktok_weekly_series` — Figure 1, weekly series, TikTok — from t05, t07, t08
- `figure2_tiktok_automation` — Figure 2, fully automated decisions on TikTok by category and content type — from t10, t03
- `figure3_hardest_measure` — Figure 3, hardest measure per statement, TikTok and X — from t01d, t01d2
- `figure4_fill_rates` — Figure 4, fill rate of each optional field, TikTok and X — from t04b
- `figure5_category_within_image` — Figure 5, share of the category within TikTok image statements by period — from t12
