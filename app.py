"""
13U Team Manager Dashboard — Streamlit App (OBA Rules)
"""

import streamlit as st
import pandas as pd
import math
import os
from datetime import datetime, timedelta, date
from typing import Optional
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

POSITIONS = ["P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]
OBA_BASE_DISTANCE_FT = 75
OBA_MOUND_DISTANCE_FT = 50

# ─────────────────────────────────────────────────────────────
# PITCH COUNT RULES (Baseball Canada Section 4.4 / OBA 13U)
# ─────────────────────────────────────────────────────────────

OBA_PITCH_COUNT_13U = {
    (1, 30): 0,
    (31, 45): 1,
    (46, 60): 2,
    (61, 75): 3,
    (76, 85): 4,
}
OBA_MAX_PITCHES_DAY = 85
OBA_MAX_PITCHES_2DAY = 85
OBA_MAX_PITCHES_4DAY = 120
OBA_MAX_CONSECUTIVE_DAYS = 3

# ─────────────────────────────────────────────────────────────
# DRILL LIBRARY
# ─────────────────────────────────────────────────────────────

FOCUS_OPTIONS = [
    "Middle Infield Double Play Feeds and Turns",
    "Cut-offs",
    "1st & 3rd Defense",
    "Situational Baserunning",
    "General",
]

DRILL_LIBRARY = {
    "Defensive/Field Work": {
        "Middle Infield Double Play Feeds and Turns": [
            f"SS→2B feed (backhand flip, underhand, glove toss) at {OBA_BASE_DISTANCE_FT}ft base paths",
            f"2B→SS feed (inside pivot, outside pivot) with {OBA_BASE_DISTANCE_FT}ft throws",
            "Coach fungo ground balls with runner simulation",
            "Rapid-fire DP combo: field, feed, turn, throw to 1B",
        ],
        "Cut-offs": [
            "Relay alignment drill (OF to Cut to Home)",
            "Live cut-off reads: cut or let it go",
            "Outfield crow-hop to cutoff man accuracy",
            "Full diamond cutoff simulation with runners",
        ],
        "1st & 3rd Defense": [
            "Catcher pick-off plays (fake to 3B, throw to 1B)",
            "Pitcher wheel play",
            "Middle infield coverage reads",
            "Full team 1st and 3rd defensive walkthrough",
        ],
        "Situational Baserunning": [
            f"Secondary leads and reads off pitcher at {OBA_MOUND_DISTANCE_FT}ft",
            "Delayed steal timing drill",
            "Tag-up reads from all bases",
            f"First-to-third on single to RF ({OBA_BASE_DISTANCE_FT}ft bases)",
        ],
        "General": [
            "Ground ball rapid-fire (3-player rotation)",
            "Bare-hand drill for soft hands",
            "Pop fly communication drill",
            "Throwing accuracy ladder",
        ],
    },
    "Hitting/Cages": {
        "_default": [
            "Front toss (focus on line drives, opposite field)",
            "Tee work: inside/middle/outside pitch locations",
            "Live BP with situational hitting (move runner, sac bunt)",
            "Short-game station: bunts and slap hits",
        ],
    },
    "Bullpen/Conditioning": {
        "_default": [
            f"Long toss progression (60-90-120 ft, game mound at {OBA_MOUND_DISTANCE_FT}ft)",
            "Flat-ground bullpen: fastball command",
            "Band work and arm care routine",
            "Sprint/agility circuit: 60yd dash, pro agility, base turns",
        ],
    },
}

REP_RATES = {
    "Middle Infield Double Play Feeds and Turns": 18,
    "Cut-offs": 14,
    "1st & 3rd Defense": 12,
    "Situational Baserunning": 15,
    "General": 16,
    "Hitting/Cages": 12,
    "Bullpen/Conditioning": 10,
}

# ─────────────────────────────────────────────────────────────
# DATA PERSISTENCE
# ─────────────────────────────────────────────────────────────

def _load_roster() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "roster.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=["Player"] + POSITIONS + ["Games", "Innings_Sat"])


def _save_roster(df: pd.DataFrame):
    df.to_csv(os.path.join(DATA_DIR, "roster.csv"), index=False)


def _load_pitch_log() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "pitch_log.csv")
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["Date"])
    return pd.DataFrame({
        "Player": pd.Series(dtype="str"),
        "Date": pd.Series(dtype="datetime64[ns]"),
        "Pitches": pd.Series(dtype="int64"),
        "Rest_Days": pd.Series(dtype="int64"),
        "Available_Date": pd.Series(dtype="datetime64[ns]"),
    })


def _save_pitch_log(df: pd.DataFrame):
    df.to_csv(os.path.join(DATA_DIR, "pitch_log.csv"), index=False)


# ─────────────────────────────────────────────────────────────
# MODULE 1: PRACTICE ARCHITECT
# ─────────────────────────────────────────────────────────────

def _efficiency_score(players: int, coaches: int) -> int:
    ratio = players / max(coaches, 1)
    if ratio <= 4:
        return 95
    elif ratio <= 5:
        return 85
    elif ratio <= 6:
        return 75
    elif ratio <= 8:
        return 60
    else:
        return max(30, 100 - int(ratio * 8))


def _get_drills(category: str, focus: str) -> list[str]:
    cat = DRILL_LIBRARY.get(category, {})
    if focus in cat:
        return cat[focus]
    if "_default" in cat:
        return cat["_default"]
    return cat.get("General", ["Drill TBD"])


def _split_groups(players: int, coaches: int) -> list[tuple[str, int]]:
    labels = ["Alpha", "Beta", "Gamma", "Delta", "Echo"]
    groups = min(coaches, 5)
    groups = max(groups, 2)
    sizes = []
    base = players // groups
    remainder = players % groups
    for i in range(groups):
        sizes.append(base + (1 if i < remainder else 0))
    return [(labels[i], sizes[i]) for i in range(groups)]


def generate_practice(duration_minutes, num_players, num_coaches, primary_focus):
    group_info = _split_groups(num_players, num_coaches)
    group_labels = [f"{name} ({size}p)" for name, size in group_info]
    num_groups = len(group_labels)

    warmup_time = 10
    cooldown_time = 5
    transition_time = 3
    available = duration_minutes - warmup_time - cooldown_time
    num_rotations = 3
    rotation_minutes = (available - (transition_time * (num_rotations - 1))) // num_rotations

    station_names = ["Defensive/Field Work", "Hitting/Cages", "Bullpen/Conditioning"]

    def _fmt(m):
        return f"{m // 60}:{m % 60:02d}"

    rows = []
    current = 0

    row = {"Time Block": f"{_fmt(0)} – {_fmt(warmup_time)}", "Minutes": warmup_time, "Activity": "Dynamic Warm-Up & Throwing Progression"}
    for g in group_labels:
        row[g] = "Together"
    rows.append(row)
    current += warmup_time

    for rot in range(num_rotations):
        start = current
        end = current + rotation_minutes
        row = {"Time Block": f"{_fmt(start)} – {_fmt(end)}", "Minutes": rotation_minutes, "Activity": f"Rotation {rot + 1}"}
        for gi, g in enumerate(group_labels):
            station_idx = (gi + rot) % len(station_names)
            row[g] = station_names[station_idx]
        rows.append(row)
        current = end

        if rot < num_rotations - 1:
            ts, te = current, current + transition_time
            row = {"Time Block": f"{_fmt(ts)} – {_fmt(te)}", "Minutes": transition_time, "Activity": "Transition / Water"}
            for g in group_labels:
                row[g] = "Hustle to next station"
            rows.append(row)
            current = te

    row = {"Time Block": f"{_fmt(current)} – {_fmt(duration_minutes)}", "Minutes": duration_minutes - current, "Activity": "Cool-Down & Recap"}
    for g in group_labels:
        row[g] = "Together"
    rows.append(row)

    cheat_sheet = {}
    for sn in station_names:
        drills = _get_drills(sn, primary_focus)
        per_drill = rotation_minutes // max(len(drills), 1)
        cheat_sheet[sn] = {"drills": drills, "minutes_per_drill": per_drill}

    focus_rep_rate = REP_RATES.get(primary_focus, 14)
    reps_per_hour = focus_rep_rate * 4
    reps_per_player = round(focus_rep_rate * (rotation_minutes / 15))
    efficiency = _efficiency_score(num_players, num_coaches)

    return {
        "schedule": pd.DataFrame(rows),
        "cheat_sheet": cheat_sheet,
        "reps_per_hour": reps_per_hour,
        "reps_per_player": reps_per_player,
        "efficiency": efficiency,
        "rotation_minutes": rotation_minutes,
        "groups": group_labels,
    }


# ─────────────────────────────────────────────────────────────
# MODULE 2: LINEUP
# ─────────────────────────────────────────────────────────────

def suggest_lineup(roster_df, innings, locked, force_outfield, designated_pitchers):
    players = roster_df["Player"].tolist()
    num_players = len(players)
    designated_pitchers = set(designated_pitchers or [])

    max_sit_per_player = math.ceil(
        (innings * max(num_players - 9, 0)) / num_players
    ) if num_players > 9 else 0

    sit_counts = {p: 0 for p in players}
    innings_sat_season = roster_df.set_index("Player")["Innings_Sat"].to_dict()
    exposure = roster_df.set_index("Player")[POSITIONS].to_dict(orient="index")

    of_positions = ["LF", "CF", "RF"]
    lineup = []

    for inn in range(innings):
        assignment = {}
        for p, pos in locked.items():
            if p in players and pos in POSITIONS:
                assignment[pos] = p

        available = [p for p in players if p not in assignment.values()]

        for p in force_outfield:
            if p in available and not any(assignment.get(op) == p for op in of_positions):
                of_open = [op for op in of_positions if op not in assignment]
                if of_open:
                    best_of = min(of_open, key=lambda pos: exposure.get(p, {}).get(pos, 0))
                    assignment[best_of] = p
                    available.remove(p)

        if num_players > 9:
            bench_needed = max(num_players - 9, 0)
            sit_candidates = sorted(
                [p for p in available if sit_counts[p] < max_sit_per_player],
                key=lambda p: (sit_counts[p], innings_sat_season.get(p, 0)),
            )
            sitting = sit_candidates[:bench_needed]
            for p in sitting:
                sit_counts[p] += 1
            available = [p for p in available if p not in sitting]

        for pos in POSITIONS:
            if pos in assignment:
                continue
            candidates = [p for p in available if p not in assignment.values()]
            if pos == "C":
                non_pitcher_candidates = [p for p in candidates if p not in designated_pitchers]
                if non_pitcher_candidates:
                    candidates = non_pitcher_candidates
            if not candidates:
                break
            candidates.sort(key=lambda p: exposure.get(p, {}).get(pos, 0))
            assignment[pos] = candidates[0]

        inning_row = {"Inning": inn + 1}
        for pos in POSITIONS:
            inning_row[pos] = assignment.get(pos, "—")
        benched = [p for p in players if p not in assignment.values()]
        inning_row["BN"] = ", ".join(benched) if benched else "—"
        lineup.append(inning_row)

        for pos, p in assignment.items():
            if p in exposure:
                exposure[p][pos] = exposure[p].get(pos, 0) + 1

    return pd.DataFrame(lineup)


# ─────────────────────────────────────────────────────────────
# MODULE 3: PITCH COUNT
# ─────────────────────────────────────────────────────────────

def _oba_rest_days(pitches: int) -> int:
    for (lo, hi), days in OBA_PITCH_COUNT_13U.items():
        if lo <= pitches <= hi:
            return days
    return 4 if pitches > OBA_MAX_PITCHES_DAY else 0


def log_pitches(player, pitches, game_date):
    df = _load_pitch_log()
    dt = pd.Timestamp(game_date)
    rest = _oba_rest_days(pitches)
    available = dt + timedelta(days=rest + 1)

    warnings = []
    if pitches > OBA_MAX_PITCHES_DAY:
        warnings.append(f"VIOLATION: {pitches} pitches exceeds daily max of {OBA_MAX_PITCHES_DAY}.")

    player_log = df[df["Player"] == player].sort_values("Date")

    same_day = player_log[player_log["Date"] == dt]
    if not same_day.empty:
        day_total = same_day["Pitches"].sum() + pitches
        if day_total > OBA_MAX_PITCHES_DAY:
            warnings.append(f"VIOLATION: {day_total} pitches today (max {OBA_MAX_PITCHES_DAY}).")

    yesterday = dt - timedelta(days=1)
    prev_day = player_log[player_log["Date"] == yesterday]
    if not prev_day.empty:
        two_day = prev_day["Pitches"].sum() + pitches
        if two_day > OBA_MAX_PITCHES_2DAY:
            warnings.append(f"WARNING: {two_day} pitches over 2 days (max {OBA_MAX_PITCHES_2DAY}).")

    four_day_start = dt - timedelta(days=3)
    four_day_log = player_log[(player_log["Date"] >= four_day_start) & (player_log["Date"] <= dt)]
    if not four_day_log.empty:
        four_total = four_day_log["Pitches"].sum() + pitches
        if four_total > OBA_MAX_PITCHES_4DAY:
            warnings.append(f"WARNING: {four_total} pitches over 4 days (max {OBA_MAX_PITCHES_4DAY}).")

    recent_dates = sorted(player_log["Date"].unique())
    consecutive = 0
    check = dt - timedelta(days=1)
    while pd.Timestamp(check) in [pd.Timestamp(d) for d in recent_dates]:
        consecutive += 1
        check -= timedelta(days=1)

    if consecutive >= 2:
        two_day_p = player_log[
            player_log["Date"].isin([dt - timedelta(days=1), dt - timedelta(days=2)])
        ]["Pitches"].sum()
        if two_day_p > 30:
            warnings.append(f"VIOLATION: 3rd consecutive day, prior 2 days = {two_day_p} pitches (max 30).")
    if consecutive >= 3:
        warnings.append("VIOLATION: 4+ consecutive pitching days (prohibited).")

    new_row = pd.DataFrame([{
        "Player": player, "Date": dt, "Pitches": pitches,
        "Rest_Days": rest, "Available_Date": available,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    _save_pitch_log(df)

    return {"rest_days": rest, "available": available.strftime("%Y-%m-%d"), "warnings": warnings}


def pitcher_status(check_date):
    df = _load_pitch_log()
    if df.empty:
        return pd.DataFrame()

    target = pd.Timestamp(check_date)
    latest = df.sort_values("Date").groupby("Player").last().reset_index()

    rows = []
    for _, row in latest.iterrows():
        player = row["Player"]
        avail = pd.Timestamp(row["Available_Date"])
        player_log = df[df["Player"] == player].sort_values("Date")

        two_day_start = target - timedelta(days=1)
        two_day_total = int(player_log[
            (player_log["Date"] >= two_day_start) & (player_log["Date"] <= target)
        ]["Pitches"].sum())

        four_day_start = target - timedelta(days=3)
        four_day_total = int(player_log[
            (player_log["Date"] >= four_day_start) & (player_log["Date"] <= target)
        ]["Pitches"].sum())

        consecutive = 0
        check = target - timedelta(days=1)
        all_dates = set(pd.Timestamp(d) for d in player_log["Date"].unique())
        while pd.Timestamp(check) in all_dates:
            consecutive += 1
            check -= timedelta(days=1)

        if target >= avail:
            if consecutive >= 3:
                status, detail = "RED", "4th consecutive day (prohibited)"
            elif consecutive >= 2:
                first_2 = int(player_log[
                    player_log["Date"].isin([target - timedelta(days=1), target - timedelta(days=2)])
                ]["Pitches"].sum())
                if first_2 > 30:
                    status, detail = "RED", f"3rd consecutive day, prior 2 days = {first_2} (max 30)"
                else:
                    cap = min(OBA_MAX_PITCHES_2DAY - two_day_total, OBA_MAX_PITCHES_4DAY - four_day_total, 30 - first_2)
                    status, detail = "YELLOW", f"3rd consecutive day, max {cap} pitches"
            else:
                cap = min(OBA_MAX_PITCHES_2DAY - two_day_total, OBA_MAX_PITCHES_4DAY - four_day_total, OBA_MAX_PITCHES_DAY)
                status, detail = "GREEN", f"Available, max {cap} pitches"
        elif (avail - target).days == 1:
            status, detail = "YELLOW", f"Bullpen only, pitching available {avail.strftime('%m/%d')}"
        else:
            status, detail = "RED", f"No throwing, available {avail.strftime('%m/%d')} ({(avail - target).days} days rest left)"

        rows.append({
            "Player": player,
            "Last Outing": row["Date"].strftime("%Y-%m-%d"),
            "Pitches": int(row["Pitches"]),
            "Rest Days": int(row["Rest_Days"]),
            "Available": avail.strftime("%Y-%m-%d"),
            "Status": status,
            "Detail": detail,
            "2-Day Total": two_day_total,
            "4-Day Total": four_day_total,
            "Consec Days": consecutive,
        })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# STREAMLIT APP
# ─────────────────────────────────────────────────────────────

TEAM_NAME = "Kingsville Knights"
TEAM_DIVISION = "13U"
TEAM_LOCATION = "Kingsville, Ontario"
TEAM_PRIMARY = "#124297"
TEAM_LIGHT = "#3B7DDD"
TEAM_DARK = "#111827"

st.set_page_config(
    page_title=f"{TEAM_NAME} {TEAM_DIVISION} Dashboard",
    page_icon="⚔️",
    layout="wide",
)

st.markdown(f"""
<style>
    .stApp > header {{
        background-color: {TEAM_DARK};
    }}
    div[data-testid="stMetric"] {{
        background-color: {TEAM_DARK};
        border: 1px solid {TEAM_PRIMARY};
        border-radius: 8px;
        padding: 12px 16px;
    }}
    div[data-testid="stMetric"] label {{
        color: {TEAM_LIGHT} !important;
    }}
    button[data-baseweb="tab"] {{
        font-weight: 600;
    }}
    .knights-banner {{
        background: linear-gradient(135deg, #050A15 0%, {TEAM_DARK} 40%, {TEAM_PRIMARY}22 100%);
        border: 2px solid {TEAM_PRIMARY};
        border-radius: 12px;
        padding: 28px 32px;
        margin-bottom: 24px;
        text-align: center;
        position: relative;
    }}
    .knights-banner .banner-content {{
        display: inline-block;
    }}
    .knights-banner .logo-img {{
        height: 80px;
        vertical-align: middle;
        margin-right: 16px;
        filter: drop-shadow(0 0 8px rgba(18, 66, 151, 0.5));
    }}
    .knights-banner h1 {{
        color: #FFFFFF;
        font-size: 2.4em;
        margin: 0;
        letter-spacing: 2px;
        text-transform: uppercase;
        display: inline;
        vertical-align: middle;
    }}
    .knights-banner h1 .blue {{
        color: {TEAM_LIGHT};
    }}
    .knights-banner .subtitle {{
        color: #C8D6E8;
        font-size: 1.1em;
        margin-top: 8px;
        opacity: 0.9;
    }}
    .knights-banner .rules {{
        color: #7B8FA8;
        font-size: 0.85em;
        margin-top: 8px;
    }}
    h2 {{
        color: {TEAM_LIGHT} !important;
        border-bottom: 2px solid {TEAM_PRIMARY};
        padding-bottom: 6px;
    }}
    details summary span {{
        font-weight: 600;
    }}
    .knights-footer {{
        text-align: center;
        padding: 16px;
        color: #4A5568;
        font-size: 0.8em;
        border-top: 1px solid #1E2A3A;
        margin-top: 40px;
    }}
    .knights-footer::after {{
        content: "🐱";
        position: fixed;
        bottom: 12px;
        right: 18px;
        font-size: 1.4em;
        opacity: 0.07;
        transition: opacity 0.3s, transform 0.3s;
        cursor: default;
        z-index: 999;
    }}
    .knights-footer:hover::after {{
        opacity: 0.85;
        transform: scale(1.4);
    }}
</style>
""", unsafe_allow_html=True)

import base64
_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
_logo_b64 = ""
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as f:
        _logo_b64 = base64.b64encode(f.read()).decode()

_logo_html = f'<img src="data:image/png;base64,{{_logo_b64}}" class="logo-img" alt="Knights">' if _logo_b64 else ""

st.markdown(f"""
<div class="knights-banner">
    <div class="banner-content">
        {_logo_html}
        <h1><span class="blue">{TEAM_NAME}</span></h1>
    </div>
    <div class="subtitle">{TEAM_DIVISION} Team Manager Dashboard</div>
    <div class="rules">OBA / Baseball Canada Rules &nbsp;&bull;&nbsp; 75ft bases &nbsp;&bull;&nbsp; 50ft mound &nbsp;&bull;&nbsp; 7 innings &nbsp;&bull;&nbsp; 85 pitch max</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚔️ Practice Architect", "⚔️ Lineup & Positions", "⚔️ Pitch Count"])

# ── TAB 1: PRACTICE ARCHITECT ──────────────────────────────

with tab1:
    st.header("Knights Practice Plan Generator")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        duration = st.selectbox("Duration (min)", [60, 75, 90, 105, 120], index=2)
    with col2:
        players = st.number_input("Players", min_value=6, max_value=20, value=12)
    with col3:
        coaches = st.number_input("Coaches", min_value=1, max_value=6, value=3)
    with col4:
        focus = st.selectbox("Primary Focus", FOCUS_OPTIONS)

    if st.button("Generate Practice Plan", type="primary", key="gen_practice"):
        result = generate_practice(duration, players, coaches, focus)

        m1, m2, m3 = st.columns(3)
        m1.metric("Efficiency Score", f"{result['efficiency']}/100")
        m2.metric("Reps/Hour (primary)", result["reps_per_hour"])
        m3.metric("Reps/Player (session)", result["reps_per_player"])

        st.subheader("Schedule")
        st.dataframe(result["schedule"], use_container_width=True, hide_index=True)

        st.subheader("Coach's Cheat Sheet")
        for station, info in result["cheat_sheet"].items():
            with st.expander(f"{station} ({info['minutes_per_drill']} min per drill)"):
                for i, drill in enumerate(info["drills"], 1):
                    st.markdown(f"**{i}.** {drill}")

# ── TAB 2: LINEUP & POSITIONS ──────────────────────────────

with tab2:
    st.header("Knights Lineup & Position Tracker")

    roster_df = _load_roster()
    has_roster = not roster_df.empty

    with st.expander("Manage Roster", expanded=not has_roster):
        st.markdown("Enter Knights player names, one per line.")
        default_names = "\n".join(roster_df["Player"].tolist()) if has_roster else "Player 1\nPlayer 2\nPlayer 3"
        names_input = st.text_area("Players", value=default_names, height=200, key="roster_input")

        if st.button("Save Roster", key="save_roster"):
            names = [n.strip() for n in names_input.strip().split("\n") if n.strip()]
            if len(names) >= 9:
                new_df = pd.DataFrame({"Player": names})
                for pos in POSITIONS:
                    new_df[pos] = 0
                new_df["Games"] = 0
                new_df["Innings_Sat"] = 0

                if has_roster:
                    old = roster_df.set_index("Player")
                    for idx, row in new_df.iterrows():
                        if row["Player"] in old.index:
                            for col in POSITIONS + ["Games", "Innings_Sat"]:
                                new_df.loc[idx, col] = old.loc[row["Player"], col]

                _save_roster(new_df)
                st.success(f"Roster saved: {len(names)} players")
                st.rerun()
            else:
                st.error("Need at least 9 players.")

    roster_df = _load_roster()
    if not roster_df.empty:
        st.subheader("Current Innings Matrix")
        st.dataframe(roster_df, use_container_width=True, hide_index=True)

        st.subheader("Generate Lineup")
        player_list = roster_df["Player"].tolist()

        col_a, col_b = st.columns(2)
        with col_a:
            locked_catcher = st.selectbox("Lock Catcher", ["(none)"] + player_list, key="lock_c")
            force_of = st.multiselect("Force to Outfield", player_list, key="force_of")
        with col_b:
            designated_p = st.multiselect("Designated Pitchers (cannot catch)", player_list, key="desig_p")
            num_innings = st.number_input("Innings", min_value=1, max_value=9, value=7, key="inn")

        locked = {}
        if locked_catcher != "(none)":
            locked[locked_catcher] = "C"

        if st.button("Generate Lineup", type="primary", key="gen_lineup"):
            lineup = suggest_lineup(roster_df, num_innings, locked, force_of, designated_p)
            st.dataframe(lineup, use_container_width=True, hide_index=True)

            if designated_p:
                st.info(f"OBA Rule: {', '.join(designated_p)} blocked from catching (pitcher cannot catch same day, Section 4.4(j)).")

        st.divider()
        st.subheader("Update Stats After a Game")
        st.markdown("Enter innings played per position for each player who played.")

        with st.form("game_update"):
            game_log = {}
            sat_list = []

            for player in player_list:
                with st.expander(player):
                    cols = st.columns(5)
                    player_positions = {}
                    for i, pos in enumerate(POSITIONS):
                        val = cols[i % 5].number_input(pos, min_value=0, max_value=9, value=0, key=f"gu_{player}_{pos}")
                        if val > 0:
                            player_positions[pos] = val
                    did_sit = st.checkbox("Sat an inning", key=f"sat_{player}")
                    if player_positions:
                        game_log[player] = player_positions
                    if did_sit:
                        sat_list.append(player)

            submitted = st.form_submit_button("Save Game Stats", type="primary")
            if submitted:
                if game_log:
                    df = _load_roster()
                    pitchers = {p for p, pos in game_log.items() if pos.get("P", 0) > 0}
                    catchers = {p for p, pos in game_log.items() if pos.get("C", 0) > 0}
                    violations = pitchers & catchers
                    if violations:
                        st.error(f"OBA VIOLATION: {', '.join(violations)} played both P and C. A pitcher cannot catch the same day (Section 4.4(j)).")

                    for player, positions in game_log.items():
                        mask = df["Player"] == player
                        if not mask.any():
                            continue
                        for pos, innings in positions.items():
                            if pos in POSITIONS:
                                df.loc[mask, pos] += innings
                        df.loc[mask, "Games"] += 1
                    for p in sat_list:
                        df.loc[df["Player"] == p, "Innings_Sat"] += 1
                    _save_roster(df)
                    st.success("Game stats saved.")
                    st.rerun()
                else:
                    st.warning("No innings entered.")

# ── TAB 3: PITCH COUNT ─────────────────────────────────────

with tab3:
    st.header("Knights Pitch Count & Recovery Monitor")

    col_rules, col_input = st.columns([1, 2])

    with col_rules:
        st.subheader("OBA 13U Rules")
        rules_df = pd.DataFrame({
            "Pitches": ["1-30", "31-45", "46-60", "61-75", "76-85"],
            "Rest": ["None", "1 day", "2 days", "3 days", "4 days"],
        })
        st.table(rules_df)
        st.markdown(f"""
- **Daily max:** {OBA_MAX_PITCHES_DAY}
- **2-day max:** {OBA_MAX_PITCHES_2DAY}
- **4-day max:** {OBA_MAX_PITCHES_4DAY}
- **Max consecutive days:** {OBA_MAX_CONSECUTIVE_DAYS}
- **Pitcher cannot catch same day**
""")

    with col_input:
        st.subheader("Log Pitches")
        roster_df = _load_roster()
        pitcher_options = roster_df["Player"].tolist() if not roster_df.empty else []

        if pitcher_options:
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                pitch_player = st.selectbox("Pitcher", pitcher_options, key="pitch_player")
            with p_col2:
                pitch_count = st.number_input("Pitches Thrown", min_value=1, max_value=120, value=40, key="pitch_count")
            with p_col3:
                pitch_date = st.date_input("Game Date", value=date.today(), key="pitch_date")

            if st.button("Log Pitches", type="primary", key="log_pitch"):
                result = log_pitches(pitch_player, pitch_count, pitch_date.strftime("%Y-%m-%d"))
                if result["warnings"]:
                    for w in result["warnings"]:
                        st.error(w)
                else:
                    st.success(f"{pitch_player}: {pitch_count} pitches logged. {result['rest_days']} rest days required. Available {result['available']}.")
        else:
            st.info("Set up your roster in the Lineup tab first.")

    st.divider()
    st.subheader("Pitcher Availability")

    check_dt = st.date_input("Check availability for date", value=date.today(), key="check_date")

    if st.button("Check Availability", type="primary", key="check_avail"):
        status = pitcher_status(check_dt.strftime("%Y-%m-%d"))
        if status.empty:
            st.info("No pitch data logged yet.")
        else:
            for _, row in status.iterrows():
                if row["Status"] == "GREEN":
                    st.success(f"**{row['Player']}** — {row['Detail']}  \n{row['Pitches']} pitches on {row['Last Outing']} | 2-day: {row['2-Day Total']}/{OBA_MAX_PITCHES_2DAY} | 4-day: {row['4-Day Total']}/{OBA_MAX_PITCHES_4DAY}")
                elif row["Status"] == "YELLOW":
                    st.warning(f"**{row['Player']}** — {row['Detail']}  \n{row['Pitches']} pitches on {row['Last Outing']} | 2-day: {row['2-Day Total']}/{OBA_MAX_PITCHES_2DAY} | 4-day: {row['4-Day Total']}/{OBA_MAX_PITCHES_4DAY}")
                else:
                    st.error(f"**{row['Player']}** — {row['Detail']}  \n{row['Pitches']} pitches on {row['Last Outing']} | 2-day: {row['2-Day Total']}/{OBA_MAX_PITCHES_2DAY} | 4-day: {row['4-Day Total']}/{OBA_MAX_PITCHES_4DAY}")

    pitch_log = _load_pitch_log()
    if not pitch_log.empty:
        st.divider()
        st.subheader("Full Pitch Log")
        st.dataframe(pitch_log.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)

# ── FOOTER ────────────────────────────────────────────────────

st.markdown(f"""
<div class="knights-footer">
    ⚔️ {TEAM_NAME} &nbsp;&bull;&nbsp; {TEAM_LOCATION} &nbsp;&bull;&nbsp; {TEAM_DIVISION} OBA
    <br>
    Built for coaches, by coaches. All rules per Baseball Canada Section 4.4.
</div>
""", unsafe_allow_html=True)
