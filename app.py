"""Bellabeat Fitness Analytics
Streamlit dashboard on Fitbit tracker data (33 users, 12 Apr - 12 May 2016).

Pages: Activity | Sleep | Body Metrics | SQL Analysis | Findings & Recommendations
Data:  three cleaned daily-level CSVs (activity, sleep, weight) inside ./data
"""
import itertools
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Bellabeat Fitness Analytics",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Palette + styling
# ----------------------------------------------------------------------------
TEXT, MUTED = "#F4F1FF", "#A79FC7"
CORAL, AMBER, MINT, VIOLET, SKY = "#FF6B81", "#FFB84D", "#3DDC97", "#8B7CFF", "#4CC9F0"
COLORWAY = [VIOLET, CORAL, MINT, AMBER, SKY]
GRID = "rgba(255,255,255,.07)"
FONT = "Plus Jakarta Sans, sans-serif"

LEVELS = ["Sedentary", "Lightly Active", "Fairly Active", "Very Active"]
LEVEL_COLORS = [CORAL, AMBER, SKY, MINT]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
.stApp {
    background:
        radial-gradient(900px 480px at 92% -8%, rgba(139,124,255,.20), transparent 60%),
        radial-gradient(800px 420px at -8% 4%, rgba(255,107,129,.13), transparent 60%),
        #0F0B1E;
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px; }
section[data-testid="stSidebar"] { background: #130E26; border-right: 1px solid rgba(255,255,255,.07); }

.side-brand { font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:1.5rem; line-height:1.15;
    background: linear-gradient(90deg,#8B7CFF,#FF6B81); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.side-sub { color:#A79FC7; font-size:.82rem; margin:.4rem 0 .6rem 0; line-height:1.45; }
.side-head { font-family:'Plus Jakarta Sans',sans-serif; font-weight:700; font-size:1.05rem; margin:.6rem 0 .2rem 0; color:#fff; }

.hero { position:relative; overflow:hidden; border-radius:22px; padding:30px 34px 26px 34px; margin-bottom:10px;
    background: linear-gradient(120deg, #3B2A8C 0%, #7B3FA8 45%, #E2536F 100%);
    box-shadow: 0 18px 50px rgba(139,124,255,.22); }
.hero::after { content:""; position:absolute; right:-70px; top:-90px; width:330px; height:330px; border-radius:50%;
    background: rgba(255,255,255,.08); }
.hero::before { content:""; position:absolute; right:130px; bottom:-120px; width:220px; height:220px; border-radius:50%;
    background: rgba(255,184,77,.16); }
.hero-eyebrow { font-family:'Plus Jakarta Sans',sans-serif; font-size:.74rem; letter-spacing:.18em; font-weight:700; color:#FFD9E0; }
.hero-title { font-family:'Plus Jakarta Sans',sans-serif; font-size:2.4rem; font-weight:800; color:#fff; margin:.25rem 0 .35rem; line-height:1.1; }
.hero-text { color:#F1E9FF; font-size:1rem; max-width:780px; margin:0 0 .95rem 0; position:relative; z-index:1; }
.chip { display:inline-block; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.24); color:#fff;
    font-size:.8rem; padding:4px 13px; border-radius:999px; margin:0 8px 6px 0; position:relative; z-index:1; }

.stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid rgba(255,255,255,.08); }
.stTabs [data-baseweb="tab"] { height:48px; padding:0 20px; border-radius:12px 12px 0 0; color:#A79FC7; font-weight:600; }
.stTabs [aria-selected="true"] { color:#fff; background:rgba(139,124,255,.14); }
.stTabs [data-baseweb="tab-highlight"] { background:linear-gradient(90deg,#8B7CFF,#FF6B81); height:3px; }

.sec-title { font-family:'Plus Jakarta Sans',sans-serif; font-size:1.3rem; font-weight:800; margin:1.3rem 0 .1rem 0; color:#fff; }
.sec-sub { color:#A79FC7; font-size:.9rem; margin-bottom:.7rem; }

.kpi { background:linear-gradient(160deg,#1E1839,#171230); border:1px solid rgba(255,255,255,.07);
    border-left:4px solid var(--accent); border-radius:16px; padding:15px 18px; height:124px; margin-bottom:14px;
    transition:transform .15s ease, box-shadow .15s ease; }
.kpi:hover { transform:translateY(-3px); box-shadow:0 10px 26px rgba(0,0,0,.35); }
.kpi-label { font-size:.7rem; letter-spacing:.09em; text-transform:uppercase; color:#A79FC7; font-weight:700; }
.kpi-value { font-family:'Plus Jakarta Sans',sans-serif; font-size:1.9rem; font-weight:800; color:#fff; line-height:1.2; margin:.22rem 0 .1rem 0; }
.kpi-sub { font-size:.78rem; color:#8F86B5; }

[class*="st-key-card_"] { background:#171230; border:1px solid rgba(255,255,255,.07) !important; border-radius:18px; padding:6px 10px; }

.find { background:linear-gradient(160deg,#1E1839,#171230); border:1px solid rgba(255,255,255,.07); border-radius:16px;
    padding:16px 18px; height:100%; }
.find-num { font-family:'Plus Jakarta Sans',sans-serif; font-size:1.7rem; font-weight:800; color:var(--accent); }
.find-txt { color:#DCD6F5; font-size:.9rem; line-height:1.5; margin-top:.15rem; }
.rec { background:linear-gradient(160deg,#1E1839,#171230); border:1px solid rgba(255,255,255,.07);
    border-top:4px solid var(--accent); border-radius:16px; padding:16px 20px; margin-bottom:14px; }
.rec-title { font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:1.05rem; color:#fff; margin-bottom:.35rem; }
.rec-tag { font-size:.68rem; letter-spacing:.1em; text-transform:uppercase; font-weight:700; color:var(--accent); }
.rec-body { color:#DCD6F5; font-size:.9rem; line-height:1.55; }
.lim-box { border:1px solid rgba(255,184,77,.5); background:rgba(255,184,77,.07); border-radius:16px; padding:16px 20px; }
.lim-title { font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; color:#FFB84D; margin-bottom:.4rem; }
.lim-box ul { margin:0; padding-left:1.15rem; color:#EDE7FF; font-size:.9rem; line-height:1.55; }
.insight { background:rgba(139,124,255,.10); border-left:4px solid #8B7CFF; padding:13px 18px; border-radius:10px;
    margin:6px 0 18px 0; font-size:.93rem; color:#E4DFFA; line-height:1.55; }
.insight.sleep { background:rgba(255,107,129,.09); border-left-color:#FF6B81; }
.insight.body { background:rgba(61,220,151,.09); border-left-color:#3DDC97; }
.find { min-height:172px; margin-bottom:14px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

_card_ids = itertools.count()


def card():
    return st.container(border=True, key=f"card_{next(_card_ids)}")


def show(fig):
    with card():
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def style(fig, title, xt=None, yt=None, h=370, legend=False):
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.01, font=dict(size=15, color=TEXT)),
        height=h,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family=FONT, size=12),
        margin=dict(l=8, r=8, t=58, b=8),
        showlegend=legend,
        legend=dict(orientation="h", y=-0.22, x=0, title=None),
        colorway=COLORWAY,
        bargap=0.12,
    )
    fig.update_xaxes(title_text=xt, gridcolor=GRID, zeroline=False, linecolor="rgba(255,255,255,.15)")
    fig.update_yaxes(title_text=yt, gridcolor=GRID, zeroline=False)
    return fig


def kpis(items):
    """items: list of (label, value, sub, accent). Renders one row of KPI cards."""
    cols = st.columns(len(items))
    for col, (label, value, sub, accent) in zip(cols, items):
        col.markdown(
            f'<div class="kpi" style="--accent:{accent}"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )


def insight(text, kind=""):
    st.markdown(f'<div class="insight {kind}">{text}</div>', unsafe_allow_html=True)


def section(title, sub=""):
    st.markdown(f'<div class="sec-title">{title}</div><div class="sec-sub">{sub}</div>', unsafe_allow_html=True)


def n0(x):
    return "n/a" if pd.isna(x) else f"{x:,.0f}"


def n1(x):
    return "n/a" if pd.isna(x) else f"{x:,.1f}"


def pct(x):
    return "n/a" if pd.isna(x) else f"{x:.1f}%"


def fmt_d(d):
    return f"{d.day} {d:%b %Y}"


# ----------------------------------------------------------------------------
# Data loading (finds the CSVs by keyword and matches columns loosely)
# ----------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent / "data"


def _norm(c):
    return re.sub(r"[^a-z0-9]", "", str(c).lower())


def _dt(series):
    return pd.to_datetime(series, errors="coerce", format="mixed")


def _pick(keyword):
    if not DATA_DIR.exists():
        return None
    files = [p for p in DATA_DIR.glob("*.csv") if keyword in p.name.lower().replace("_", "")]
    if not files:
        return None
    return max(files, key=lambda p: (("clean" in p.name.lower()) * 2 + ("daily" in p.name.lower()), -len(p.name)))


def _col(raw, *names, required=True):
    lookup = {_norm(c): c for c in raw.columns}
    for n in names:
        if _norm(n) in lookup:
            return raw[lookup[_norm(n)]]
    if required:
        raise KeyError(f"Column like '{names[0]}' not found. Columns present: {list(raw.columns)}")
    return None


def _flag(series):
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "1.0", "yes"]).astype(int)


@st.cache_data(show_spinner="Loading data...")
def load_data():
    fa, fs, fw = _pick("activity"), _pick("sleep"), _pick("weight")
    missing = [n for n, f in (("daily activity", fa), ("sleep", fs), ("weight", fw)) if f is None]
    if missing:
        raise FileNotFoundError("Missing CSV in the data folder for: " + ", ".join(missing))
    ra, rs, rw = pd.read_csv(fa), pd.read_csv(fs), pd.read_csv(fw)

    # --- activity
    dist = _col(ra, "TotalDistance", "Distance", required=False)
    nw = _col(ra, "DeviceNotWorn", required=False)
    steps = pd.to_numeric(_col(ra, "TotalSteps", "Steps"))
    act = pd.DataFrame({
        "Id": pd.to_numeric(_col(ra, "Id", "user_id")).astype("int64"),
        "Date": _dt(_col(ra, "Date", "ActivityDate")).dt.normalize(),
        "TotalSteps": steps,
        "TotalDistance": pd.to_numeric(dist) if dist is not None else np.nan,
        "VeryActiveMinutes": pd.to_numeric(_col(ra, "VeryActiveMinutes")),
        "FairlyActiveMinutes": pd.to_numeric(_col(ra, "FairlyActiveMinutes")),
        "LightlyActiveMinutes": pd.to_numeric(_col(ra, "LightlyActiveMinutes")),
        "SedentaryMinutes": pd.to_numeric(_col(ra, "SedentaryMinutes")),
        "Calories": pd.to_numeric(_col(ra, "Calories")),
        # your cleaned file flags not-worn days (zero-step days); fall back to that rule if the column is absent
        "DeviceNotWorn": _flag(nw) if nw is not None else (steps == 0).astype(int),
    }).dropna(subset=["Date"]).drop_duplicates(["Id", "Date"]).reset_index(drop=True)
    act["TotalActiveMinutes"] = act.VeryActiveMinutes + act.FairlyActiveMinutes + act.LightlyActiveMinutes
    act["ModVigMinutes"] = act.VeryActiveMinutes + act.FairlyActiveMinutes
    act["Weekday"] = act.Date.dt.day_name()
    act["WeekdayNum"] = act.Date.dt.dayofweek
    act["DayType"] = np.where(act.WeekdayNum >= 5, "Weekend", "Weekday")
    act["ActivityLevel"] = pd.cut(act.TotalSteps, [-1, 4999, 7499, 9999, np.inf], labels=LEVELS).astype(str)

    # --- sleep
    rec = _col(rs, "TotalSleepRecords", "SleepRecords", required=False)
    slp = pd.DataFrame({
        "Id": pd.to_numeric(_col(rs, "Id", "user_id")).astype("int64"),
        "Date": _dt(_col(rs, "Date", "SleepDay", "SleepDate")).dt.normalize(),
        "TotalSleepRecords": pd.to_numeric(rec) if rec is not None else 1,
        "MinutesAsleep": pd.to_numeric(_col(rs, "TotalMinutesAsleep", "MinutesAsleep")),
        "TimeInBed": pd.to_numeric(_col(rs, "TotalTimeInBed", "TimeInBed")),
    }).dropna(subset=["Date"]).drop_duplicates(["Id", "Date"]).reset_index(drop=True)
    slp["Weekday"] = slp.Date.dt.day_name()
    slp["WeekdayNum"] = slp.Date.dt.dayofweek
    slp["DayType"] = np.where(slp.WeekdayNum >= 5, "Weekend", "Weekday")
    slp["SleepHours"] = (slp.MinutesAsleep / 60).round(2)
    slp["SleepEfficiency"] = (100 * slp.MinutesAsleep / slp.TimeInBed).round(1)
    slp["MinutesAwakeInBed"] = slp.TimeInBed - slp.MinutesAsleep

    # --- weight
    kg = _col(rw, "WeightKg", "Weight_Kg", required=False)
    if kg is None:
        kg = pd.to_numeric(_col(rw, "WeightPounds", "Weight_Pounds")) * 0.45359237
    manual = _col(rw, "IsManualReport", required=False)
    wgt = pd.DataFrame({
        "Id": pd.to_numeric(_col(rw, "Id", "user_id")).astype("int64"),
        "Date": _dt(_col(rw, "Date", "WeightDate")).dt.normalize(),
        "WeightKg": pd.to_numeric(kg).round(1),
        "BMI": pd.to_numeric(_col(rw, "BMI")).round(1),
        "IsManualReport": _flag(manual) if manual is not None else 0,
    }).dropna(subset=["Date"]).reset_index(drop=True)

    return {"daily_activity": act, "sleep_day": slp, "weight_log": wgt}


# ----------------------------------------------------------------------------
# Read-only SQL sandbox (in-memory SQLite, SELECT only)
# ----------------------------------------------------------------------------
_ALLOWED_ACTIONS = {21, 20, 31, 33}  # SELECT, READ, FUNCTION, RECURSIVE


def _authorizer(action, *_):
    return 0 if action in _ALLOWED_ACTIONS else 1  # 0 = OK, 1 = DENY


def _make_conn(tables):
    conn = sqlite3.connect(":memory:")
    for name, df in tables.items():
        d = df.copy()
        for c in d.columns:
            if pd.api.types.is_datetime64_any_dtype(d[c]):
                d[c] = d[c].dt.strftime("%Y-%m-%d")
        d.to_sql(name, conn, index=False)
    conn.set_authorizer(_authorizer)
    return conn


def _clean_sql(q):
    q = re.sub(r"--[^\n]*", "", q)
    q = re.sub(r"/\*.*?\*/", "", q, flags=re.S)
    q = q.strip().rstrip(";").strip()
    if not q:
        raise ValueError("Type a query first.")
    if not re.match(r"(?is)^(select|with)\b", q):
        raise ValueError("Only SELECT queries are allowed here (the sandbox is read-only).")
    return q


def execute(tables, sql, limit=1000):
    """Returns dict(df, truncated, err)."""
    conn = None
    try:
        q = _clean_sql(sql)
        conn = _make_conn(tables)
        ticks = {"n": 0}

        def guard():
            ticks["n"] += 1
            return 1 if ticks["n"] > 3000 else 0

        conn.set_progress_handler(guard, 1000)
        cur = conn.execute(q)
        rows = cur.fetchmany(limit + 1)
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return {"df": df.head(limit), "truncated": len(df) > limit, "err": None}
    except sqlite3.Warning:
        return {"df": None, "truncated": False, "err": "Run one statement at a time."}
    except sqlite3.DatabaseError as e:
        msg = str(e)
        if "not authorized" in msg or "interrupted" in msg:
            msg = "That query was blocked or ran too long. Only simple, read-only SELECT queries are allowed."
        return {"df": None, "truncated": False, "err": f"SQL error: {msg}"}
    except Exception as e:  # noqa: BLE001
        return {"df": None, "truncated": False, "err": str(e)}
    finally:
        if conn is not None:
            conn.close()


PRESETS = [
    {"label": "Overview: rows, users and date span per table",
     "about": "Sanity check of what each table holds.",
     "sql": """SELECT 'daily_activity' AS table_name, COUNT(*) AS row_count, COUNT(DISTINCT Id) AS users,
       MIN(Date) AS first_date, MAX(Date) AS last_date FROM daily_activity
UNION ALL
SELECT 'sleep_day', COUNT(*), COUNT(DISTINCT Id), MIN(Date), MAX(Date) FROM sleep_day
UNION ALL
SELECT 'weight_log', COUNT(*), COUNT(DISTINCT Id), MIN(Date), MAX(Date) FROM weight_log;"""},
    {"label": "Data quality: device-not-worn days per user",
     "about": "A day is flagged as not worn when the tracker recorded zero steps. Shows who has the most such days.",
     "sql": """SELECT Id, COUNT(*) AS days_logged, SUM(DeviceNotWorn) AS not_worn_days,
       ROUND(100.0 * SUM(DeviceNotWorn) / COUNT(*), 1) AS not_worn_pct
FROM daily_activity
GROUP BY Id
HAVING not_worn_days > 0
ORDER BY not_worn_pct DESC;"""},
    {"label": "Data quality: logging consistency segments",
     "about": "Groups users by how many days they logged activity in the window.",
     "sql": """SELECT CASE WHEN days >= 28 THEN '1. Consistent (28+ days)'
            WHEN days >= 15 THEN '2. Moderate (15-27 days)'
            ELSE '3. Occasional (under 15 days)' END AS engagement_segment,
       COUNT(*) AS users
FROM (SELECT Id, COUNT(*) AS days FROM daily_activity GROUP BY Id)
GROUP BY engagement_segment
ORDER BY engagement_segment;"""},
    {"label": "Activity: average steps and calories per user",
     "about": "Worn days only, sorted from most to least active.",
     "sql": """SELECT Id, COUNT(*) AS days_worn, ROUND(AVG(TotalSteps)) AS avg_steps,
       ROUND(AVG(Calories)) AS avg_calories,
       ROUND(AVG(SedentaryMinutes) / 60.0, 1) AS avg_sedentary_hrs
FROM daily_activity
WHERE DeviceNotWorn = 0
GROUP BY Id
ORDER BY avg_steps DESC;"""},
    {"label": "Activity: sedentary share of tracked time",
     "about": "Sedentary minutes as a share of sedentary plus active minutes, worn days only.",
     "sql": """SELECT COUNT(*) AS days_worn,
       ROUND(AVG(SedentaryMinutes) / 60.0, 1) AS avg_sedentary_hrs,
       ROUND(AVG(TotalActiveMinutes)) AS avg_active_min,
       ROUND(100.0 * SUM(SedentaryMinutes) / SUM(SedentaryMinutes + TotalActiveMinutes), 1) AS sedentary_pct_of_tracked
FROM daily_activity
WHERE DeviceNotWorn = 0;"""},
    {"label": "Activity: steps and calories by weekday",
     "about": "Which days of the week are busiest.",
     "sql": """SELECT Weekday, ROUND(AVG(TotalSteps)) AS avg_steps, ROUND(AVG(Calories)) AS avg_calories,
       ROUND(AVG(ModVigMinutes), 1) AS avg_mod_vig_min
FROM daily_activity
WHERE DeviceNotWorn = 0
GROUP BY Weekday
ORDER BY WeekdayNum;"""},
    {"label": "Activity: weekday vs weekend",
     "about": "Weekend means Saturday and Sunday.",
     "sql": """SELECT DayType, COUNT(*) AS days, ROUND(AVG(TotalSteps)) AS avg_steps,
       ROUND(AVG(Calories)) AS avg_calories
FROM daily_activity
WHERE DeviceNotWorn = 0
GROUP BY DayType;"""},
    {"label": "Activity: share of days by activity level",
     "about": "Steps bands: under 5k Sedentary, 5k-7.5k Lightly Active, 7.5k-10k Fairly Active, 10k+ Very Active.",
     "sql": """SELECT ActivityLevel, COUNT(*) AS days,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM daily_activity WHERE DeviceNotWorn = 0), 1) AS pct_of_days
FROM daily_activity
WHERE DeviceNotWorn = 0
GROUP BY ActivityLevel
ORDER BY MIN(TotalSteps);"""},
    {"label": "Activity: days meeting the WHO activity guideline (per user)",
     "about": "WHO suggests 150 moderate-to-vigorous minutes a week, about 21.4 a day. Uses very + fairly active minutes as the proxy.",
     "sql": """SELECT Id, COUNT(*) AS days_worn, SUM(ModVigMinutes >= 21.4) AS days_meeting_target,
       ROUND(100.0 * SUM(ModVigMinutes >= 21.4) / COUNT(*), 1) AS pct_days_meeting
FROM daily_activity
WHERE DeviceNotWorn = 0
GROUP BY Id
ORDER BY pct_days_meeting DESC;"""},
    {"label": "Sleep: average hours and efficiency per user",
     "about": "Sleep efficiency = minutes asleep / minutes in bed.",
     "sql": """SELECT Id, COUNT(*) AS nights, ROUND(AVG(SleepHours), 2) AS avg_sleep_hrs,
       ROUND(AVG(SleepEfficiency), 1) AS avg_efficiency_pct,
       ROUND(AVG(MinutesAwakeInBed)) AS avg_min_awake_in_bed
FROM sleep_day
GROUP BY Id
ORDER BY avg_efficiency_pct;"""},
    {"label": "Sleep: nights under 7 hours (per user)",
     "about": "Share of each user's nights below the common 7-hour adult recommendation.",
     "sql": """SELECT Id, COUNT(*) AS nights, SUM(MinutesAsleep < 420) AS nights_under_7h,
       ROUND(100.0 * SUM(MinutesAsleep < 420) / COUNT(*), 1) AS pct_under_7h
FROM sleep_day
GROUP BY Id
ORDER BY pct_under_7h DESC;"""},
    {"label": "Sleep: weekday vs weekend",
     "about": "Do weekends look different from weekdays?",
     "sql": """SELECT DayType, COUNT(*) AS nights, ROUND(AVG(SleepHours), 2) AS avg_sleep_hrs,
       ROUND(AVG(SleepEfficiency), 1) AS avg_efficiency_pct
FROM sleep_day
GROUP BY DayType;"""},
    {"label": "Sleep vs activity: sleep by same-day step band",
     "about": "Joins activity and sleep on user and date. This shows an association, not cause and effect.",
     "sql": """SELECT CASE WHEN a.TotalSteps < 5000 THEN '1. Under 5,000 steps'
            WHEN a.TotalSteps < 10000 THEN '2. 5,000 to 9,999 steps'
            ELSE '3. 10,000+ steps' END AS step_band,
       COUNT(*) AS nights, ROUND(AVG(s.SleepHours), 2) AS avg_sleep_hrs,
       ROUND(AVG(s.SleepEfficiency), 1) AS avg_efficiency_pct
FROM daily_activity a
JOIN sleep_day s ON s.Id = a.Id AND s.Date = a.Date
WHERE a.DeviceNotWorn = 0
GROUP BY step_band
ORDER BY step_band;"""},
    {"label": "Body: BMI category of each user's latest weigh-in",
     "about": "Uses a window function to pick the most recent log per user.",
     "sql": """WITH latest AS (
  SELECT Id, BMI, ROW_NUMBER() OVER (PARTITION BY Id ORDER BY Date DESC) AS rn
  FROM weight_log
)
SELECT CASE WHEN BMI < 18.5 THEN 'Underweight' WHEN BMI < 25 THEN 'Normal'
            WHEN BMI < 30 THEN 'Overweight' ELSE 'Obese' END AS bmi_category,
       COUNT(*) AS users
FROM latest
WHERE rn = 1
GROUP BY bmi_category
ORDER BY MIN(BMI);"""},
    {"label": "Body: weight change per user (first vs last log)",
     "about": "Only users with at least two weigh-ins can show a change.",
     "sql": """WITH ranked AS (
  SELECT Id, WeightKg,
         ROW_NUMBER() OVER (PARTITION BY Id ORDER BY Date) AS rn_first,
         ROW_NUMBER() OVER (PARTITION BY Id ORDER BY Date DESC) AS rn_last
  FROM weight_log
)
SELECT f.Id, f.WeightKg AS first_kg, l.WeightKg AS last_kg,
       ROUND(l.WeightKg - f.WeightKg, 1) AS change_kg
FROM ranked f
JOIN ranked l ON l.Id = f.Id AND f.rn_first = 1 AND l.rn_last = 1 AND l.rn_first > 1
ORDER BY change_kg;"""},
    {"label": "Body: manual vs auto-synced weight entries",
     "about": "How much of the weight data depends on users typing it in.",
     "sql": """SELECT CASE WHEN IsManualReport = 1 THEN 'Manual entry' ELSE 'Auto-synced' END AS log_type,
       COUNT(*) AS entries,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM weight_log), 1) AS pct_of_entries
FROM weight_log
GROUP BY log_type;"""},
    {"label": "Adoption: users per tracked feature",
     "about": "How many of the users actually used each part of the device.",
     "sql": """SELECT 'Activity tracking' AS feature, COUNT(DISTINCT Id) AS users FROM daily_activity
UNION ALL
SELECT 'Sleep tracking', COUNT(DISTINCT Id) FROM sleep_day
UNION ALL
SELECT 'Weight logging', COUNT(DISTINCT Id) FROM weight_log;"""},
]

DEFAULT_SQL = """SELECT Weekday, ROUND(AVG(Calories)) AS avg_calories
FROM daily_activity
WHERE DeviceNotWorn = 0
GROUP BY Weekday
ORDER BY WeekdayNum;"""


def _copy_to_editor(sql):
    st.session_state["custom_sql"] = sql
    st.toast("SQL copied to the custom editor below")


def show_result(res, key):
    if res["err"]:
        st.error(res["err"])
        return
    df = res["df"]
    st.dataframe(df, width="stretch", hide_index=True)
    note = f"{len(df):,} row(s)" + (" (first 1,000 shown)" if res["truncated"] else "")
    st.caption(note)
    st.download_button("Download result as CSV", df.to_csv(index=False).encode(), f"{key}.csv", "text/csv", key=f"dl_{key}")


# ----------------------------------------------------------------------------
# Load data (or explain what is missing)
# ----------------------------------------------------------------------------
try:
    TABLES = load_data()
except Exception as err:  # noqa: BLE001
    st.error(f"Could not load the data. {err}")
    st.markdown(
        "Put the three cleaned CSVs (activity, sleep, weight) inside the `data/` folder next to `app.py`, "
        "then reload. File names only need to contain `activity`, `sleep` and `weight`."
    )
    st.stop()

ACT, SLP, WGT = TABLES["daily_activity"], TABLES["sleep_day"], TABLES["weight_log"]
USERS_ALL = sorted(ACT.Id.unique())
N_USERS = len(USERS_ALL)
DMIN, DMAX = ACT.Date.min().date(), ACT.Date.max().date()
SPAN = f"{fmt_d(pd.Timestamp(DMIN))} to {fmt_d(pd.Timestamp(DMAX))}"

# ----------------------------------------------------------------------------
# Sidebar: title + filters only
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="side-brand">Bellabeat<br>Fitness Analytics</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-sub">Fitbit tracker data<br>{SPAN} · {N_USERS} users</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-head">Filters</div>', unsafe_allow_html=True)
    sel_users = st.multiselect("Users", USERS_ALL, placeholder="All users (pick to narrow)",
                               help="Leave empty to include everyone.")
    d0, d1 = st.slider("Date range", DMIN, DMAX, (DMIN, DMAX), format="DD MMM YYYY")
    excl_not_worn = st.toggle("Exclude device-not-worn days", value=True,
                              help="Days flagged in the cleaned data as not worn (zero steps recorded).")
    users_in = sel_users or USERS_ALL
    st.markdown(f"**{len(users_in)} of {N_USERS}** users in view")
    st.caption("Filters apply to Activity, Sleep and Body Metrics. SQL Analysis and Findings always use the full dataset.")

t0, t1 = pd.Timestamp(d0), pd.Timestamp(d1)
a_all = ACT[ACT.Id.isin(users_in) & ACT.Date.between(t0, t1)]
a = a_all[a_all.DeviceNotWorn == 0] if excl_not_worn else a_all
s = SLP[SLP.Id.isin(users_in) & SLP.Date.between(t0, t1)]
w = WGT[WGT.Id.isin(users_in) & WGT.Date.between(t0, t1)]

# ----------------------------------------------------------------------------
# Header (hero), then the page navigator directly under it
# ----------------------------------------------------------------------------
st.markdown(
    f"""<div class="hero">
    <div class="hero-eyebrow">BELLABEAT · SMART-DEVICE USAGE ANALYSIS</div>
    <div class="hero-title">Bellabeat Fitness Analytics</div>
    <div class="hero-text">How do people really use their fitness trackers? A look at activity, sleep and body metrics
    from {N_USERS} Fitbit users, to find product and marketing opportunities.</div>
    <span class="chip">👥 {N_USERS} users</span>
    <span class="chip">📅 {SPAN}</span>
    <span class="chip">🧩 Activity · Sleep · Body metrics</span>
    </div>""",
    unsafe_allow_html=True,
)

tab_act, tab_slp, tab_body, tab_sql, tab_find = st.tabs(
    ["🏃 Activity", "😴 Sleep", "⚖️ Body Metrics", "🧮 SQL Analysis", "✅ Findings & Recommendations"]
)

# ============================================================================
# 1. ACTIVITY
# ============================================================================
with tab_act:
    if a.empty:
        st.warning("No activity records match the current filters.")
    else:
        section("User activity", "How much people move, how hard they work, and how consistently they wear the tracker.")
        basis = "worn days only" if excl_not_worn else "all logged days"
        not_worn_pct = 100 * a_all.DeviceNotWorn.mean()
        sed_share = 100 * a.SedentaryMinutes.sum() / (a.SedentaryMinutes.sum() + a.TotalActiveMinutes.sum())
        kpis([
            ("Users in view", f"{a.Id.nunique()}", f"of {N_USERS} total", VIOLET),
            ("Avg daily steps", n0(a.TotalSteps.mean()), basis, CORAL),
            ("Avg distance", f"{n1(a.TotalDistance.mean())} km", f"per day, {basis}", SKY),
            ("Avg calories burned", n0(a.Calories.mean()), f"per day, {basis}", AMBER),
        ])
        kpis([
            ("Sedentary share", pct(sed_share), "of tracked time (sedentary + active)", CORAL),
            ("Avg active minutes", f"{n0(a.TotalActiveMinutes.mean())} min", "all intensities, per day", MINT),
            ("Days with 10k+ steps", pct(100 * (a.TotalSteps >= 10000).mean()), "of days in view", VIOLET),
            ("Device-not-worn days", pct(not_worn_pct), "of all logged days", AMBER),
        ])

        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(a, x="TotalSteps", nbins=25, color_discrete_sequence=[VIOLET])
            fig.add_vline(x=a.TotalSteps.mean(), line_dash="dash", line_color=AMBER,
                          annotation_text=f"Mean {a.TotalSteps.mean():,.0f}", annotation_font_color=AMBER)
            show(style(fig, "Daily steps distribution", "Steps per day", "Number of user-days"))
        with c2:
            lv = a.ActivityLevel.value_counts(normalize=True).reindex(LEVELS).fillna(0) * 100
            fig = go.Figure(go.Bar(x=lv.index, y=lv.values, marker_color=LEVEL_COLORS,
                                   text=[f"{v:.1f}%" for v in lv.values], textposition="outside", cliponaxis=False))
            show(style(fig, "Share of days by activity level", "Activity level (Sedentary <5k, Lightly 5k-7.5k, Fairly 7.5k-10k, Very 10k+ steps)",
                       "% of days"))

        insight("Sedentary minutes make up the large majority of the average tracked day, far outweighing any active "
                "category. This is the clearest activity-side product opportunity: nudging users out of long "
                "sedentary stretches, not just celebrating high-step days.")

        c1, c2 = st.columns(2)
        with c1:
            wk = a.groupby("DayType")[["TotalSteps", "Calories"]].mean().reindex(["Weekday", "Weekend"]).dropna().reset_index()
            fig = go.Figure(go.Bar(x=wk.DayType, y=wk.TotalSteps, marker_color=[VIOLET, CORAL][: len(wk)],
                                   text=[f"{v:,.0f} steps" for v in wk.TotalSteps], textposition="outside",
                                   cliponaxis=False, customdata=wk.Calories,
                                   hovertemplate="%{x}<br>%{y:,.0f} steps<br>%{customdata:,.0f} calories<extra></extra>"))
            show(style(fig, "Average steps: weekday vs weekend", "Type of day", "Average steps per day"))
        with c2:
            if len(users_in) == 1:
                base = a[a.Id == users_in[0]].sort_values("Date")
                tr = base[["Date", "TotalSteps"]]
                ttl = f"7-day rolling average steps: user {users_in[0]}"
            else:
                tr = a.groupby("Date").TotalSteps.mean().reset_index()
                ttl = "7-day rolling average steps: all users in view"
            tr = tr.assign(roll7=tr.TotalSteps.rolling(7, min_periods=1).mean())
            fig = go.Figure()
            fig.add_scatter(x=tr.Date, y=tr.TotalSteps, mode="lines+markers", name="Daily",
                            line=dict(color=SKY, width=1.5), marker=dict(size=4), opacity=0.55)
            fig.add_scatter(x=tr.Date, y=tr.roll7, mode="lines", name="7-day rolling average",
                            line=dict(color=AMBER, width=3))
            show(style(fig, ttl, "Date", "Steps per day", legend=True))

        c1, c2 = st.columns(2)
        with c1:
            fig = px.scatter(a, x="TotalSteps", y="Calories", opacity=0.55, color_discrete_sequence=[CORAL])
            ok = a[["TotalSteps", "Calories"]].dropna()
            ttl = "Steps vs calories burned"
            if len(ok) > 2:
                m, b = np.polyfit(ok.TotalSteps, ok.Calories, 1)
                xs = np.array([ok.TotalSteps.min(), ok.TotalSteps.max()])
                fig.add_scatter(x=xs, y=m * xs + b, mode="lines", line=dict(color=AMBER, width=3), name="Trend")
                ttl += f" (r = {np.corrcoef(ok.TotalSteps, ok.Calories)[0, 1]:.2f})"
            show(style(fig, ttl, "Steps per day", "Calories per day"))
        with c2:
            mins = pd.Series({"Very active": a.VeryActiveMinutes.mean(), "Fairly active": a.FairlyActiveMinutes.mean(),
                              "Lightly active": a.LightlyActiveMinutes.mean()})
            fig = go.Figure(go.Pie(labels=mins.index, values=mins.values, hole=0.58, sort=False,
                                   marker=dict(colors=[CORAL, AMBER, SKY]), textinfo="label+percent"))
            show(style(fig, "Where active minutes come from (average per day)"))

        st.markdown('<div class="sec-title">Activity leaderboard</div>', unsafe_allow_html=True)
        lb = (a.groupby("Id").agg(days_logged=("TotalSteps", "count"), avg_steps=("TotalSteps", "mean"),
                                  avg_calories=("Calories", "mean"))
              .round(0).sort_values("avg_steps", ascending=False).reset_index())
        st.dataframe(lb, width="stretch", hide_index=True)

# ============================================================================
# 2. SLEEP
# ============================================================================
with tab_slp:
    if s.empty:
        st.warning("No sleep records match the current filters.")
    else:
        section("Sleep patterns", "How long people sleep, how well they sleep, and who tracks sleep at all.")
        insight(f"Only {SLP.Id.nunique()} of {N_USERS} users log sleep at all. Findings here describe that subset, "
                "not the full user base.", "sleep")
        kpis([
            ("Users with sleep data", f"{s.Id.nunique()}", f"of {len(users_in)} users in view", VIOLET),
            ("Nights logged", f"{len(s):,}", f"{len(s) / s.Id.nunique():.1f} per user", SKY),
            ("Avg sleep", f"{n1(s.SleepHours.mean())} h", "asleep per night", MINT),
            ("Avg time in bed", f"{n1(s.TimeInBed.mean() / 60)} h", "per night", AMBER),
        ])
        kpis([
            ("Sleep efficiency", pct(s.SleepEfficiency.mean()), "minutes asleep / minutes in bed", MINT),
            ("Awake in bed", f"{n0(s.MinutesAwakeInBed.mean())} min", "avg per night", CORAL),
            ("Nights under 7 h", pct(100 * (s.MinutesAsleep < 420).mean()), "below the adult recommendation", CORAL),
            ("Nights with multiple records", pct(100 * (s.TotalSleepRecords > 1).mean()), "naps or split sleep", VIOLET),
        ])

        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(s, x="SleepHours", nbins=20, color_discrete_sequence=[VIOLET])
            fig.add_vrect(x0=7, x1=9, fillcolor=MINT, opacity=0.13, line_width=0,
                          annotation_text="7-9 h recommended", annotation_position="top left",
                          annotation_font_color=MINT)
            show(style(fig, "Hours asleep per night", "Hours asleep", "Number of nights"))
        with c2:
            labs = ["Below recommended (<7h)", "Recommended (7-9h)", "Above recommended (>9h)"]
            band = pd.cut(s.MinutesAsleep, [-1, 419, 540, 10**5], labels=labs)
            bc = band.value_counts(normalize=True).reindex(labs).fillna(0) * 100
            fig = go.Figure(go.Bar(x=bc.index, y=bc.values, marker_color=[CORAL, MINT, AMBER],
                                   text=[f"{v:.1f}%" for v in bc.values], textposition="outside", cliponaxis=False))
            show(style(fig, "Share of nights by sleep adequacy", "Sleep adequacy band", "% of nights"))

        insight("Average sleep efficiency is high, meaning time in bed is mostly spent actually asleep. The real gap is "
                "sleep duration, not efficiency: a notable share of nights fall short of the recommended 7 hours. "
                "A product nudging bedtime, rather than sleep quality, targets the actual gap.", "sleep")

        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(s, x="SleepEfficiency", nbins=20, color_discrete_sequence=[SKY])
            show(style(fig, "Sleep efficiency distribution", "Sleep efficiency (%)", "Number of nights"))
        with c2:
            fig = px.scatter(s, x="TimeInBed", y="MinutesAsleep", opacity=0.6, color="SleepEfficiency",
                             color_continuous_scale=[CORAL, AMBER, MINT])
            lim = [0, max(s.TimeInBed.max(), s.MinutesAsleep.max()) * 1.03]
            fig.add_scatter(x=lim, y=lim, mode="lines", line=dict(color="rgba(255,255,255,.5)", dash="dot"),
                            showlegend=False)
            fig.update_coloraxes(colorbar_title="Efficiency %")
            show(style(fig, "Time in bed vs time actually asleep (dotted = perfect efficiency)",
                       "Minutes in bed", "Minutes asleep"))

        c1, c2 = st.columns(2)
        with c1:
            pu = s.groupby("Id").SleepHours.mean().sort_values().reset_index()
            pu["Id"] = pu.Id.astype(str)
            fig = go.Figure(go.Bar(y=pu.Id, x=pu.SleepHours, orientation="h",
                                   marker_color=[CORAL if v < 7 else MINT for v in pu.SleepHours]))
            fig.add_vline(x=7, line_dash="dot", line_color=TEXT)
            fig.update_yaxes(type="category")
            show(style(fig, "Average sleep per user (coral = under 7 h)", "Hours asleep per night", "User ID",
                       h=max(370, 22 * len(pu) + 110)))
        with c2:
            m = a.merge(s, on=["Id", "Date"], how="inner")
            if len(m) >= 3:
                m["Band"] = pd.cut(m.TotalSteps, [-1, 4999, 9999, np.inf],
                                   labels=["Under 5k steps", "5k to 10k steps", "10k+ steps"])
                bs = m.groupby("Band", observed=True).agg(h=("SleepHours", "mean"), n=("SleepHours", "size")).reset_index()
                fig = go.Figure(go.Bar(x=bs.Band.astype(str), y=bs.h, marker_color=[CORAL, AMBER, MINT][: len(bs)],
                                       text=[f"{v:.2f} h (n={n})" for v, n in zip(bs.h, bs.n)],
                                       textposition="outside", cliponaxis=False))
                show(style(fig, "Sleep by same-day step count (association only)", "Steps that day",
                           "Average hours asleep"))
            else:
                st.info("Not enough overlapping activity and sleep days in the current filters.")

        st.markdown('<div class="sec-title">Lowest sleep efficiency (with nights logged)</div>', unsafe_allow_html=True)
        b5 = (s.groupby("Id").agg(nights_logged=("SleepEfficiency", "count"), avg_hours_asleep=("SleepHours", "mean"),
                                  avg_sleep_efficiency=("SleepEfficiency", "mean"))
              .round(1).sort_values("avg_sleep_efficiency").head(5).reset_index())
        st.dataframe(b5, width="stretch", hide_index=True)

# ============================================================================
# 3. BODY METRICS
# ============================================================================
with tab_body:
    if w.empty:
        st.warning("No weight records match the current filters (only a few users logged weight).")
    else:
        section("Body metrics", "Weight and BMI logs. Only a small group of users used this feature, so read it as directional.")
        insight(f"Only {WGT.Id.nunique()} of {N_USERS} users log weight, mostly manually rather than via a synced scale. "
                "Treat any finding here as directional, not representative.", "body")
        w = w.sort_values(["Id", "Date"])
        per = w.groupby("Id").agg(logs=("WeightKg", "size"), first_kg=("WeightKg", "first"),
                                  last_kg=("WeightKg", "last"), bmi_mean=("BMI", "mean")).reset_index()
        per["change_kg"] = (per.last_kg - per.first_kg).round(1)
        multi = per[per.logs >= 2]
        kpis([
            ("Users who logged weight", f"{w.Id.nunique()}", f"of {len(users_in)} users in view", VIOLET),
            ("Weigh-ins logged", f"{len(w):,}", f"{len(w) / w.Id.nunique():.1f} per user", SKY),
            ("Avg weight", f"{n1(w.WeightKg.mean())} kg", "across all entries", AMBER),
            ("Avg BMI", n1(w.BMI.mean()), "across all entries", CORAL),
        ])
        kpis([
            ("Normal BMI entries", pct(100 * w.BMI.between(18.5, 24.99).mean()), "BMI 18.5 to 24.9", MINT),
            ("Overweight or above", pct(100 * (w.BMI >= 25).mean()), "BMI 25 and over", CORAL),
            ("Manual entries", pct(100 * w.IsManualReport.mean()), "typed in, not auto-synced", AMBER),
            ("Avg weight change", (f"{multi.change_kg.mean():+.1f} kg" if len(multi) else "n/a"),
             (f"first to last log, {len(multi)} users with 2+ logs" if len(multi) else "needs 2+ logs per user"), VIOLET),
        ])

        CATS = ["Underweight", "Normal", "Overweight", "Obese"]
        CAT_COL = {"Underweight": SKY, "Normal": MINT, "Overweight": AMBER, "Obese": CORAL}
        c1, c2 = st.columns(2)
        with c1:
            bu = per[["Id", "bmi_mean"]].copy()
            bu["Category"] = pd.cut(bu.bmi_mean, [0, 18.5, 25, 30, 100], labels=CATS, right=False).astype(str)
            bu = bu.sort_values("bmi_mean")
            bu["User"] = bu.Id.astype(str)
            fig = px.bar(bu, x="User", y="bmi_mean", color="Category", color_discrete_map=CAT_COL,
                         category_orders={"Category": CATS})
            fig.update_xaxes(type="category")
            show(style(fig, "Average BMI by user", "User ID", "Average BMI", legend=True))
        with c2:
            mc = w.IsManualReport.map({1: "Manual", 0: "Automatic"}).value_counts()
            fig = go.Figure(go.Pie(labels=mc.index, values=mc.values, hole=0.58,
                                   marker=dict(colors=[AMBER if l == "Manual" else SKY for l in mc.index]),
                                   textinfo="label+percent+value"))
            show(style(fig, "Manual vs automatic weight entries"))

        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(w, x="BMI", nbins=15, color_discrete_sequence=[VIOLET])
            fig.add_vrect(x0=18.5, x1=24.9, fillcolor=MINT, opacity=0.13, line_width=0,
                          annotation_text="Normal range", annotation_position="top left", annotation_font_color=MINT)
            show(style(fig, "BMI distribution of all weigh-ins", "BMI", "Number of weigh-ins"))
        with c2:
            traj = w[w.Id.isin(multi.Id)].copy()
            if len(traj):
                traj["User"] = traj.Id.astype(str)
                fig = px.line(traj, x="Date", y="WeightKg", color="User", markers=True)
                show(style(fig, "Weight over time (users with 2+ logs)", "Date", "Weight (kg)", legend=True))
            else:
                st.info("No user in view has two or more weigh-ins.")

        c1, c2 = st.columns(2)
        with c1:
            if len(multi):
                mm = multi.sort_values("change_kg")
                fig = go.Figure(go.Bar(x=mm.Id.astype(str), y=mm.change_kg,
                                       marker_color=[MINT if v <= 0 else CORAL for v in mm.change_kg],
                                       text=[f"{v:+.1f}" for v in mm.change_kg], textposition="outside",
                                       cliponaxis=False))
                fig.update_xaxes(type="category")
                show(style(fig, "Weight change, first vs last log (users with 2+ logs)", "User ID", "Change (kg)"))
            else:
                st.info("Weight change needs at least two logs per user.")
        with c2:
            with card():
                st.markdown("**Weight change table (first vs last log)**")
                st.dataframe(per[["Id", "logs", "first_kg", "last_kg", "change_kg"]].sort_values("change_kg"),
                             width="stretch", hide_index=True, height=290)
                st.caption("Users with a single log show a change of 0 because there is nothing to compare.")

# ============================================================================
# 4. SQL ANALYSIS
# ============================================================================
with tab_sql:
    section("SQL analysis", "Run read-only SQL against the cleaned tables. Nothing you type can change the data.")
    tc = pd.DataFrame({
        "Table": list(TABLES),
        "Rows": [len(d) for d in TABLES.values()],
        "Columns": [", ".join(d.columns) for d in TABLES.values()],
    })
    with st.expander("Table reference (names and columns)"):
        st.dataframe(tc, width="stretch", hide_index=True)
        st.caption("Dates are stored as text (YYYY-MM-DD). DeviceNotWorn = 1 marks a zero-step day. "
                   "ModVigMinutes = very + fairly active minutes. TotalActiveMinutes includes lightly active.")

    st.markdown("##### Part 1: Analysis library")
    labels = [p["label"] for p in PRESETS]
    choice = st.selectbox("Choose an analysis", labels, key="preset_choice")
    p = PRESETS[labels.index(choice)]
    st.caption(p["about"])
    st.code(p["sql"], language="sql")
    b1, b2, _sp = st.columns([1, 1.5, 4])
    if b1.button("Run analysis", type="primary", key="run_preset"):
        st.session_state["preset_out"] = (choice, execute(TABLES, p["sql"]))
    b2.button("Copy to custom editor", key="copy_preset", on_click=_copy_to_editor, args=(p["sql"],))
    out = st.session_state.get("preset_out")
    if out and out[0] == choice:
        show_result(out[1], "analysis_result")

    st.divider()
    st.markdown("##### Part 2: Custom SQL")
    st.caption("Write any SELECT (joins, CTEs and window functions work). Results are capped at 1,000 rows.")
    st.session_state.setdefault("custom_sql", DEFAULT_SQL)
    st.text_area("Write your own SELECT query", key="custom_sql", height=170)
    if st.button("Run query", type="primary", key="run_custom"):
        st.session_state["custom_out"] = execute(TABLES, st.session_state["custom_sql"])
    if st.session_state.get("custom_out"):
        show_result(st.session_state["custom_out"], "custom_result")

# ============================================================================
# 5. FINDINGS & RECOMMENDATIONS (full dataset, so the numbers stay fixed)
# ============================================================================
with tab_find:
    fa = ACT[ACT.DeviceNotWorn == 0]
    sed_all = 100 * fa.SedentaryMinutes.sum() / (fa.SedentaryMinutes.sum() + fa.TotalActiveMinutes.sum())
    nw_user = ACT.groupby("Id").DeviceNotWorn.mean() * 100
    n_bad, nw_max = int((nw_user > 20).sum()), nw_user.max()
    n_sleep, n_wt = SLP.Id.nunique(), WGT.Id.nunique()
    under7 = 100 * (SLP.MinutesAsleep < 420).mean()
    eff = SLP.SleepEfficiency.mean()
    manual = 100 * WGT.IsManualReport.mean()
    wl = WGT.sort_values("Date").groupby("Id").agg(n=("WeightKg", "size"), f=("WeightKg", "first"), l=("WeightKg", "last"))
    wm = wl[wl.n >= 2]
    flat_down = int(((wm.l - wm.f) <= 0.1).sum())
    dt_a = fa.groupby("DayType")[["TotalSteps", "Calories"]].mean()
    dt_s = SLP.groupby("DayType").SleepHours.mean()
    sleep_gap_min = abs(dt_s.get("Weekend", np.nan) - dt_s.get("Weekday", np.nan)) * 60

    def fcard(tag, accent, title, body):
        return (f'<div class="find" style="--accent:{accent}"><div class="rec-tag">{tag}</div>'
                f'<div class="rec-title">{title}</div><div class="find-txt">{body}</div></div>')

    section("Key findings", "Numbers below use the full dataset and do not change with the sidebar filters.")
    f1, f2 = st.columns(2)
    f1.markdown(fcard("Headline", CORAL, "Sedentary time dominates the average day",
                      f"Across all users, sedentary minutes make up about {sed_all:.0f}% of tracked time "
                      f"(sedentary plus active minutes), far outweighing any active category. This is the clearest "
                      f"single pattern in the data."), unsafe_allow_html=True)
    f2.markdown(fcard("Data quality", AMBER, "Pillars have very different coverage",
                      f"All {N_USERS} users log activity, but only about {100 * n_sleep / N_USERS:.0f}% log sleep and just "
                      f"{100 * n_wt / N_USERS:.0f}% log weight. Sleep and body-metric findings describe a self-selected "
                      f"subset, not the full base."), unsafe_allow_html=True)
    f3, f4 = st.columns(2)
    f3.markdown(fcard("Activity insight", SKY, "Device wear is inconsistent for a meaningful minority",
                      f"{n_bad} of {N_USERS} users have the device unworn on more than a fifth of logged days, with one "
                      f"user missing data on {nw_max:.0f}% of days. Any activity average should be read alongside "
                      f"wear rate."), unsafe_allow_html=True)
    f4.markdown(fcard("Sleep insight", VIOLET, "The sleep gap is duration, not quality",
                      f"Average sleep efficiency is {eff:.0f}%, meaning time in bed is mostly spent asleep. Even so, "
                      f"{under7:.0f}% of nights fall short of the 7-hour minimum recommended for adults."),
                unsafe_allow_html=True)
    f5, f6 = st.columns(2)
    f5.markdown(fcard("Product opportunity", MINT, "Weight logging is the weakest-adopted feature",
                      f"Only {n_wt} of {N_USERS} users log weight at all, and {manual:.0f}% of entries are typed in "
                      f"manually rather than synced. Of the {len(wm)} users with two or more logs, {flat_down} show a "
                      f"flat or declining trend."), unsafe_allow_html=True)
    f6.markdown(fcard("Sample caveat", AMBER, "Weekday and weekend activity is nearly identical",
                      f"Average steps ({dt_a.TotalSteps.get('Weekday', np.nan):,.0f} vs {dt_a.TotalSteps.get('Weekend', np.nan):,.0f}) "
                      f"and calories barely shift between weekdays and weekends, while sleep differs by about "
                      f"{sleep_gap_min:.0f} minutes. Day-of-week personalization is unlikely to move outcomes on its own."),
                unsafe_allow_html=True)

    section("Business recommendations", "Each one follows from a finding above. These are patterns in the data, not proven causes.")
    r1, r2 = st.columns(2)
    r1.markdown(fcard("Activity", CORAL, "Target sedentary time, not just step counts",
                      "Since sedentary minutes dominate the day for nearly everyone, a periodic move reminder during "
                      "long inactive stretches is likely to reach more users than a step-count leaderboard."),
                unsafe_allow_html=True)
    r2.markdown(fcard("Sleep", VIOLET, "Nudge bedtime, not sleep quality",
                      "Because efficiency is already high but duration is short for many nights, a bedtime reminder or "
                      "wind-down prompt addresses the actual gap better than a sleep-quality feature would."),
                unsafe_allow_html=True)
    r3, r4 = st.columns(2)
    r3.markdown(fcard("Data quality", SKY, "Improve device-wear compliance before trusting activity averages",
                      f"With {n_bad} users missing a fifth or more of their tracked days, a simple wear reminder or a "
                      f"visible streak indicator could materially improve data completeness."),
                unsafe_allow_html=True)
    r4.markdown(fcard("Body", MINT, "Treat weight logging as an adoption problem, not an insight problem",
                      "The bottleneck for body metrics is that almost nobody logs weight, not what the data shows once "
                      "they do. Smart-scale integration or lighter manual entry is worth testing before investing "
                      "further in weight-trend features."), unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.15, 1])
    with c1:
        fun = pd.DataFrame({"Feature": ["Activity tracking", "Sleep tracking", "Weight logging"],
                            "Users": [N_USERS, n_sleep, n_wt]})
        fig = go.Figure(go.Bar(x=fun.Users, y=fun.Feature, orientation="h", marker_color=[VIOLET, SKY, AMBER],
                               text=[f"{u} users ({100 * u / N_USERS:.0f}%)" for u in fun.Users],
                               textposition="inside", insidetextanchor="start"))
        fig.update_yaxes(autorange="reversed")
        show(style(fig, "Feature adoption: how many users used each part of the device", "Number of users", None, h=300))
    with c2:
        st.markdown(
            f"""<div class="lim-box"><div class="lim-title">Limitations and biases</div><ul>
            <li>Small, non-random sample: {N_USERS} users, only {n_sleep} with sleep data and {n_wt} with weight logs, so results describe this group, not all Bellabeat customers.</li>
            <li>One month of 2016 data with no age, sex or fitness goals, and only self-selected Fitbit owners, so seasonal and selection bias are possible.</li>
            <li>Findings show association, not causation, and not-worn days and manual weight entries add measurement noise.</li>
            </ul></div>""",
            unsafe_allow_html=True,
        )
