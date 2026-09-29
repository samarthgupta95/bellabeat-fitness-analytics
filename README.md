# Bellabeat Fitness Analytics (Streamlit dashboard)

Fitbit tracker data, 33 users, 12 Apr to 12 May 2016. Five pages under one header:
Activity, Sleep, Body Metrics, SQL Analysis, Findings & Recommendations.
The sidebar holds only the title and filters (users, date range, exclude device-not-worn days).

## Folder layout
```
app.py
requirements.txt
.streamlit/config.toml      dark theme
data/                       activity_clean.csv, sleep_clean.csv, weight_clean.csv
```

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Data
The app finds the CSVs in `data/` by keyword in the file name (`activity`, `sleep`, `weight`).
Columns used: Id, Date, TotalSteps, TotalDistance, Very/Fairly/LightlyActiveMinutes, SedentaryMinutes,
Calories, DeviceNotWorn (activity); TotalSleepRecords, TotalMinutesAsleep, TotalTimeInBed (sleep);
WeightKg, BMI, IsManualReport (weight).

## Definitions
- Device not worn: the DeviceNotWorn flag from the cleaned file (a zero-step day)
- Activity level by daily steps: Sedentary under 5k, Lightly Active 5k-7.5k, Fairly Active 7.5k-10k, Very Active 10k+
- Sedentary share: sedentary minutes / (sedentary + total active minutes), worn days
- Sleep bands: under 7h, 7-9h, over 9h. Efficiency = minutes asleep / minutes in bed
- WHO proxy (SQL preset): 150 min a week, about 21.4 very + fairly active minutes a day

## SQL Analysis page
Part 1: dropdown of 17 preset analyses. It shows the SQL, runs it, and can copy it into the editor.
Part 2: free SELECT editor. Queries run on an in-memory SQLite copy of three tables
(daily_activity, sleep_day, weight_log). Only SELECT/WITH is accepted, SQLite blocks any write,
PRAGMA or ATTACH at the engine level, runaway queries are stopped, and results are capped at 1,000 rows.
The SQLite dialect differs slightly from the PostgreSQL file used for pgAdmin.

## Deploy on Streamlit Cloud
Push this folder to GitHub (keep `data/`), then point Streamlit Cloud at `app.py`.
