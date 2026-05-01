# West Bengal 2026 Prediction Model

This project builds a working, end-to-end baseline prediction model using the available 2021 Assembly data and 2019/2024 Lok Sabha results. It outputs seat-level winner probabilities for 2026.

## What This Model Does
- Trains a multiclass classifier to predict the winning party per seat.
- Produces seat-level probabilities for each party class.
- Supports optional PC-to-AC mapping to inject Lok Sabha signals per seat.

## Inputs
Required:
- data/raw/IndiaVotes_AC__West_Bengal_2021.csv
- data/raw/IndiaVotes_LS_WB_2019.csv
- data/raw/IndiaVotes_LS_WB_2024.csv

Optional:
- data/raw/pc_to_ac_mapping.csv
- data/raw/West_Bengal_Election_2026_All_Parties_List.csv

### pc_to_ac_mapping.csv format
```
AC_Number,PC_Name
1,Cooch Behar
2,Cooch Behar
...
```
If this file is missing, the Lok Sabha features are applied as statewide averages and the model still runs.

## Run The Pipeline
1) Build processed features
```
"c:/Users/ss211/Documents/Projects/Election Prediction model/.venv/Scripts/python.exe" -m src.data.build_processed
```

2) Train the model
```
"c:/Users/ss211/Documents/Projects/Election Prediction model/.venv/Scripts/python.exe" -m src.model.train_model
```

3) Generate 2026 predictions
```
"c:/Users/ss211/Documents/Projects/Election Prediction model/.venv/Scripts/python.exe" -m src.model.predict_2026
```

4) Calibrate with swing + exit-poll priors + candidate list
```
"c:/Users/ss211/Documents/Projects/Election Prediction model/.venv/Scripts/python.exe" -m src.model.calibrate_2026
```

## Frontend (Streamlit)
```
"c:/Users/ss211/Documents/Projects/Election Prediction model/.venv/Scripts/python.exe" -m pip install -r requirements.txt
"c:/Users/ss211/Documents/Projects/Election Prediction model/.venv/Scripts/python.exe" -m streamlit run streamlit_app.py
```

## Outputs
- outputs/wb_2026_predictions.csv
- outputs/wb_2026_winner_list.csv
- outputs/wb_2026_party_tally.csv
- outputs/wb_2026_calibrated.csv
- outputs/wb_2026_calibrated_tally.csv
- outputs/wb_2026_flip_risk.csv
- outputs/wb_2026_powerbi_dataset.csv
- outputs/wb_2026_exit_polls.csv
- outputs/training_metrics.json

## Notes
- This baseline predicts winning party probabilities, not full vote share distributions. To model vote share, provide seat-level party vote share histories as an additional dataset.
- Candidate affidavit features can be merged later through data/raw/candidate_profile_features.csv and additional feature engineering if you supply those files.
