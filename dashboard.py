"""
Team Manager Dashboard — 13U Baseball (OBA / Baseball Ontario Rules)
====================================================================
Module 1: Dynamic Practice Architect
Module 2: Developmental Lineup & Position Tracker
Module 3: Pitch Count & Recovery Monitor

Rule authority: Baseball Canada Section 4.4 as adopted by Baseball Ontario (OBA).
Field: 75ft bases, 50ft mound. 7-inning games. Max 85 pitches/day.
"""

import pandas as pd
import math
import os
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

POSITIONS = ["P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]
BENCH = "BN"

# OBA 13U field dimensions (used in drill descriptions)
OBA_BASE_DISTANCE_FT = 75
OBA_MOUND_DISTANCE_FT = 50

# OBA mercy rule thresholds
OBA_MERCY = {3: 18, 4: 15, 5: 10}

# ─────────────────────────────────────────────────────────────
# MODULE 1: Dynamic Practice Architect
# ─────────────────────────────────────────────────────────────

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


def _split_groups(players: int, coaches: int) -> list[str]:
    labels = ["Alpha", "Beta", "Gamma", "Delta", "Echo"]
    groups = min(coaches, 5)
    groups = max(groups, 2)
    sizes = []
    base = players // groups
    remainder = players % groups
    for i in range(groups):
        sizes.append(base + (1 if i < remainder else 0))
    return [f"{labels[i]} ({sizes[i]}p)" for i in range(groups)]


def generate_practice(
    duration_minutes: int = 90,
    num_players: int = 12,
    num_coaches: int = 3,
    primary_focus: str = "Middle Infield Double Play Feeds and Turns",
) -> dict:
    """Generate a minute-by-minute practice plan (OBA 13U)."""

    groups = _split_groups(num_players, num_coaches)
    num_groups = len(groups)

    warmup_time = 10
    cooldown_time = 5
    transition_time = 3
    available = duration_minutes - warmup_time - cooldown_time

    num_rotations = 3
    rotation_minutes = (available - (transition_time * (num_rotations - 1))) // num_rotations

    station_names = ["Defensive/Field Work", "Hitting/Cages", "Bullpen/Conditioning"]

    def _fmt(minutes: int) -> str:
        return f"{minutes // 60}:{minutes % 60:02d}"

    schedule_rows = []
    current_time = 0

    schedule_rows.append({
        "Time Block": f"{_fmt(0)} – {_fmt(warmup_time)}",
        "Minutes": warmup_time,
        "Activity": "Dynamic Warm-Up & Throwing Progression",
        "Coach Lead": "All Coaches",
        **{g: "Together" for g in groups},
    })
    current_time += warmup_time

    for rot in range(num_rotations):
        start = current_time
        end = current_time + rotation_minutes

        row = {
            "Time Block": f"{_fmt(start)} – {_fmt(end)}",
            "Minutes": rotation_minutes,
            "Activity": f"Rotation {rot + 1}",
            "Coach Lead": "",
        }

        for gi, g in enumerate(groups):
            station_idx = (gi + rot) % len(station_names)
            station = station_names[station_idx]
            coach_num = (station_idx % num_coaches) + 1
            row[g] = station
            if not row["Coach Lead"]:
                row["Coach Lead"] = f"Coach {coach_num} leads {station}"
            else:
                row["Coach Lead"] += f" | C{(station_idx % num_coaches) + 1}→{station[:10]}"

        schedule_rows.append(row)
        current_time = end

        if rot < num_rotations - 1:
            t_start = current_time
            t_end = current_time + transition_time
            schedule_rows.append({
                "Time Block": f"{_fmt(t_start)} – {_fmt(t_end)}",
                "Minutes": transition_time,
                "Activity": "Transition / Water Break",
                "Coach Lead": "—",
                **{g: "Hustle to next station" for g in groups},
            })
            current_time = t_end

    end_time = duration_minutes
    schedule_rows.append({
        "Time Block": f"{_fmt(current_time)} – {_fmt(end_time)}",
        "Minutes": end_time - current_time,
        "Activity": "Team Cool-Down & Recap",
        "Coach Lead": "Head Coach",
        **{g: "Together" for g in groups},
    })

    cheat_sheet = {}
    for sn in station_names:
        drills = _get_drills(sn, primary_focus)
        per_drill = rotation_minutes // max(len(drills), 1)
        cheat_sheet[sn] = {
            "drills": drills,
            "minutes_per_drill": per_drill,
            "setup": _station_setup(sn, primary_focus, num_players // num_groups),
        }

    focus_rep_rate = REP_RATES.get(primary_focus, 14)
    field_minutes = rotation_minutes
    reps_per_player = focus_rep_rate * (field_minutes / 15)
    reps_per_hour = focus_rep_rate * 4

    efficiency = _efficiency_score(num_players, num_coaches)

    return {
        "schedule": pd.DataFrame(schedule_rows),
        "cheat_sheet": cheat_sheet,
        "reps_per_hour": reps_per_hour,
        "reps_per_player_session": round(reps_per_player),
        "efficiency_score": efficiency,
        "meta": {
            "duration": duration_minutes,
            "players": num_players,
            "coaches": num_coaches,
            "focus": primary_focus,
            "groups": groups,
            "rotation_minutes": rotation_minutes,
            "rules": "OBA / Baseball Canada 13U",
            "field": f"{OBA_BASE_DISTANCE_FT}ft bases, {OBA_MOUND_DISTANCE_FT}ft mound",
        },
    }


def _station_setup(station: str, focus: str, group_size: int) -> str:
    setups = {
        "Defensive/Field Work": (
            f"Setup: {group_size} players rotate through fielding positions. "
            f"Coach hits fungos. Players not fielding shag or act as runners. "
            f"Max 3 in any line. Focus: {focus}. "
            f"OBA field: {OBA_BASE_DISTANCE_FT}ft bases, {OBA_MOUND_DISTANCE_FT}ft mound."
        ),
        "Hitting/Cages": (
            f"Setup: Split {group_size} players across 2 stations (tee + front toss). "
            f"Hitter gets 8 swings then rotates to shagger. Zero idle time."
        ),
        "Bullpen/Conditioning": (
            f"Setup: {group_size} players pair up. Alternate between long toss/flat ground "
            f"and conditioning circuit. 2-min work / 1-min transition. "
            f"OBA NOTE: Track all bullpen pitches toward daily/weekly limits (max 85/day)."
        ),
    }
    return setups.get(station, "Setup TBD")


def print_practice(result: dict):
    """Pretty-print a practice plan."""
    meta = result["meta"]
    print("=" * 80)
    print(f"  PRACTICE PLAN — {meta['duration']} min | {meta['players']} players | {meta['coaches']} coaches")
    print(f"  Focus: {meta['focus']}")
    print(f"  Rules: {meta['rules']} | Field: {meta['field']}")
    print(f"  Groups: {', '.join(meta['groups'])}")
    print("=" * 80)

    df = result["schedule"]
    print("\n## SCHEDULE\n")
    print(df.to_string(index=False))

    print("\n\n## COACH'S CHEAT SHEET\n")
    for station, info in result["cheat_sheet"].items():
        print(f"### {station} ({info['minutes_per_drill']} min per drill)")
        print(f"    {info['setup']}")
        for i, drill in enumerate(info["drills"], 1):
            print(f"    {i}. {drill}")
        print()

    print("## EFFICIENCY METRICS\n")
    print(f"  Efficiency Score: {result['efficiency_score']}/100")
    print(f"  Est. Reps/Hour (primary skill): {result['reps_per_hour']}")
    print(f"  Est. Reps/Player this session: {result['reps_per_player_session']}")
    print()


# ─────────────────────────────────────────────────────────────
# MODULE 2: Developmental Lineup & Position Tracker
# ─────────────────────────────────────────────────────────────
# OBA 13U: 7-inning games, standard 9-player lineup (optional EP for 10th bat).
# No mandatory position rotation, but this tool enforces developmental rotation.
# Pitcher cannot catch same day (Baseball Canada 4.4(j)).

def _load_roster() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "roster.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=["Player"] + POSITIONS + ["Games", "Innings_Sat"])


def _save_roster(df: pd.DataFrame):
    df.to_csv(os.path.join(DATA_DIR, "roster.csv"), index=False)


def initialize_roster(players: list[str]) -> pd.DataFrame:
    """Create a fresh roster with zero innings everywhere."""
    rows = []
    for p in players:
        row = {"Player": p, "Games": 0, "Innings_Sat": 0}
        for pos in POSITIONS:
            row[pos] = 0
        rows.append(row)
    df = pd.DataFrame(rows)
    _save_roster(df)
    return df


def get_roster() -> pd.DataFrame:
    return _load_roster()


def update_season_stats(
    game_log: dict[str, dict[str, int]],
    sat_players: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Update after a game.
    game_log: {player_name: {position: innings_played, ...}, ...}
    sat_players: list of players who sat an inning this game.
    """
    df = _load_roster()

    pitchers_today = set()
    catchers_today = set()
    for player, positions in game_log.items():
        if positions.get("P", 0) > 0:
            pitchers_today.add(player)
        if positions.get("C", 0) > 0:
            catchers_today.add(player)

    violations = pitchers_today & catchers_today
    if violations:
        print(f"  OBA VIOLATION: {', '.join(violations)} played both P and C in the same game.")
        print(f"  Rule: A player who pitches cannot catch the remainder of that calendar day (Baseball Canada 4.4(j)).")

    for player, positions in game_log.items():
        mask = df["Player"] == player
        if not mask.any():
            continue
        for pos, innings in positions.items():
            if pos in POSITIONS:
                df.loc[mask, pos] += innings
        df.loc[mask, "Games"] += 1

    if sat_players:
        for p in sat_players:
            mask = df["Player"] == p
            df.loc[mask, "Innings_Sat"] += 1

    _save_roster(df)
    return df


def suggest_lineup(
    innings: int = 7,
    locked: Optional[dict[str, str]] = None,
    force_outfield: Optional[list[str]] = None,
    designated_pitchers: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Suggest a developmental lineup for the next game (OBA 13U, 7 innings).

    locked: {player: position} for non-negotiable assignments (e.g., your only catcher).
    force_outfield: players who MUST play OF this game (rotation rule).
    designated_pitchers: players expected to pitch this game. These players will NOT
                         be assigned to catch (OBA rule: pitcher cannot catch same day).

    Returns a DataFrame: rows = innings, columns = positions + BENCH.
    """
    df = _load_roster()
    if df.empty:
        raise ValueError("No roster loaded. Call initialize_roster() first.")

    players = df["Player"].tolist()
    num_players = len(players)
    locked = locked or {}
    force_outfield = force_outfield or []
    designated_pitchers = set(designated_pitchers or [])

    for p, pos in locked.items():
        if pos == "C" and p in designated_pitchers:
            print(f"  OBA WARNING: {p} is locked at C but also listed as a designated pitcher.")
            print(f"  Rule: A player who pitches cannot catch the same day (Baseball Canada 4.4(j)).")
        if pos == "P" and p in [lp for lp, lpos in locked.items() if lpos == "C"]:
            print(f"  OBA WARNING: {p} is locked at both P and C. This violates Baseball Canada 4.4(j).")

    max_sit_per_player = math.ceil(
        (innings * max(num_players - 9, 0)) / num_players
    ) if num_players > 9 else 0

    sit_counts = {p: 0 for p in players}
    innings_sat_season = df.set_index("Player")["Innings_Sat"].to_dict()
    exposure = df.set_index("Player")[POSITIONS].to_dict(orient="index")

    of_positions = ["LF", "CF", "RF"]

    lineup = []
    for inn in range(innings):
        assignment = {}

        for p, pos in locked.items():
            if p in players and pos in POSITIONS:
                assignment[pos] = p

        available = [p for p in players if p not in assignment.values()]

        for p in force_outfield:
            if p in available and not any(
                assignment.get(op) == p for op in of_positions
            ):
                of_open = [op for op in of_positions if op not in assignment]
                if of_open:
                    best_of = min(of_open, key=lambda pos: exposure.get(p, {}).get(pos, 0))
                    assignment[best_of] = p
                    available.remove(p)

        if num_players > 9:
            bench_this_inning = max(num_players - 9, 0)
            already_assigned = len(assignment)
            need_to_sit = bench_this_inning

            sit_candidates = sorted(
                [p for p in available if sit_counts[p] < max_sit_per_player],
                key=lambda p: (sit_counts[p], innings_sat_season.get(p, 0)),
            )
            sitting = sit_candidates[:need_to_sit]
            for p in sitting:
                sit_counts[p] += 1
            available = [p for p in available if p not in sitting]

        for pos in POSITIONS:
            if pos in assignment:
                continue
            candidates = [p for p in available if p not in assignment.values()]

            if pos == "C":
                candidates = [p for p in candidates if p not in designated_pitchers]
                if not candidates:
                    candidates = [p for p in available if p not in assignment.values()]

            if not candidates:
                break
            candidates.sort(key=lambda p: exposure.get(p, {}).get(pos, 0))
            best = candidates[0]
            assignment[pos] = best

        inning_row = {"Inning": inn + 1}
        for pos in POSITIONS:
            inning_row[pos] = assignment.get(pos, "—")
        benched = [p for p in players if p not in assignment.values()]
        inning_row[BENCH] = ", ".join(benched) if benched else "—"
        lineup.append(inning_row)

        for pos, p in assignment.items():
            if p in exposure:
                exposure[p][pos] = exposure[p].get(pos, 0) + 1

    lineup_df = pd.DataFrame(lineup)

    _validate_pitcher_catcher_rule(lineup_df, designated_pitchers)

    return lineup_df


def _validate_pitcher_catcher_rule(lineup_df: pd.DataFrame, designated_pitchers: set):
    """Flag if any designated pitcher ended up catching in the suggested lineup."""
    for _, row in lineup_df.iterrows():
        catcher = row.get("C", "—")
        pitcher = row.get("P", "—")
        if catcher in designated_pitchers:
            print(f"  OBA CONFLICT (Inning {row['Inning']}): {catcher} is catching but is a designated pitcher.")
        if pitcher != "—" and pitcher in [row.get("C", "—")]:
            pass


def print_lineup(lineup_df: pd.DataFrame):
    print("=" * 100)
    print("  SUGGESTED LINEUP (Developmental Rotation, OBA 13U)")
    print("  Rule: Pitcher cannot catch same day (Baseball Canada 4.4(j))")
    print("  Rule: No player sits twice until everyone has sat once")
    print("=" * 100)
    print()
    print(lineup_df.to_string(index=False))
    print()


# ─────────────────────────────────────────────────────────────
# MODULE 3: Pitch Count & Recovery Monitor
# ─────────────────────────────────────────────────────────────
# Baseball Canada Section 4.4 / OBA 13U Boys rules:
#   Daily max: 85 pitches
#   2-day max: 85 pitches (cumulative across 2 consecutive calendar days)
#   4-day max: 120 pitches (cumulative across 4 consecutive calendar days)
#   Cannot pitch 4 consecutive days.
#   3 consecutive days only if first 2 days combined <= 30 pitches.

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


def _load_pitch_log() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "pitch_log.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["Date"])
        return df
    return pd.DataFrame({
        "Player": pd.Series(dtype="str"),
        "Date": pd.Series(dtype="datetime64[ns]"),
        "Pitches": pd.Series(dtype="int64"),
        "Rest_Days": pd.Series(dtype="int64"),
        "Available_Date": pd.Series(dtype="datetime64[ns]"),
    })


def _save_pitch_log(df: pd.DataFrame):
    df.to_csv(os.path.join(DATA_DIR, "pitch_log.csv"), index=False)


def _oba_rest_days(pitches: int) -> int:
    """OBA/Baseball Canada 13U rest day calculation based on last outing's pitch count."""
    for (lo, hi), days in OBA_PITCH_COUNT_13U.items():
        if lo <= pitches <= hi:
            return days
    if pitches > OBA_MAX_PITCHES_DAY:
        return 4
    return 0


def log_pitches(player: str, pitches: int, game_date: Optional[str] = None) -> dict:
    """
    Log pitches thrown by a player. Returns rest info and OBA compliance warnings.
    Rest is based on the pitches thrown on the last day pitched (not cumulative).
    """
    df = _load_pitch_log()
    date = pd.Timestamp(game_date) if game_date else pd.Timestamp(datetime.today().date())
    rest = _oba_rest_days(pitches)
    available = date + timedelta(days=rest + 1)

    warnings = []

    if pitches > OBA_MAX_PITCHES_DAY:
        warnings.append(
            f"VIOLATION: {player} threw {pitches} pitches, exceeding the OBA 13U daily max of {OBA_MAX_PITCHES_DAY}."
        )

    player_log = df[df["Player"] == player].sort_values("Date")

    same_day = player_log[player_log["Date"] == date]
    if not same_day.empty:
        day_total = same_day["Pitches"].sum() + pitches
        if day_total > OBA_MAX_PITCHES_DAY:
            warnings.append(
                f"VIOLATION: {player} has thrown {day_total} pitches today (max {OBA_MAX_PITCHES_DAY})."
            )

    yesterday = date - timedelta(days=1)
    prev_day = player_log[player_log["Date"] == yesterday]
    if not prev_day.empty:
        two_day_total = prev_day["Pitches"].sum() + pitches
        if two_day_total > OBA_MAX_PITCHES_2DAY:
            warnings.append(
                f"WARNING: {player} has thrown {two_day_total} pitches over 2 consecutive days (max {OBA_MAX_PITCHES_2DAY})."
            )

    four_day_start = date - timedelta(days=3)
    four_day_log = player_log[(player_log["Date"] >= four_day_start) & (player_log["Date"] <= date)]
    if not four_day_log.empty:
        four_day_total = four_day_log["Pitches"].sum() + pitches
        if four_day_total > OBA_MAX_PITCHES_4DAY:
            warnings.append(
                f"WARNING: {player} has thrown {four_day_total} pitches over 4 consecutive days (max {OBA_MAX_PITCHES_4DAY})."
            )

    recent_dates = sorted(player_log["Date"].unique())
    consecutive = 0
    check = date - timedelta(days=1)
    while pd.Timestamp(check) in [pd.Timestamp(d) for d in recent_dates]:
        consecutive += 1
        check -= timedelta(days=1)

    if consecutive >= 2:
        two_day_pitches = player_log[
            player_log["Date"].isin([date - timedelta(days=1), date - timedelta(days=2)])
        ]["Pitches"].sum()
        if two_day_pitches > 30:
            warnings.append(
                f"VIOLATION: {player} pitching 3rd consecutive day but first 2 days totaled {two_day_pitches} pitches (max 30 to pitch 3rd day)."
            )
        if consecutive >= 3:
            warnings.append(
                f"VIOLATION: {player} would be pitching 4+ consecutive days. OBA prohibits pitching 4 consecutive days."
            )

    new_row = pd.DataFrame([{
        "Player": player,
        "Date": date,
        "Pitches": pitches,
        "Rest_Days": rest,
        "Available_Date": available,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    _save_pitch_log(df)

    result = {
        "player": player,
        "pitches": pitches,
        "rest_days_required": rest,
        "available_date": available.strftime("%Y-%m-%d"),
        "warnings": warnings,
    }

    if warnings:
        for w in warnings:
            print(f"  ** {w}")

    return result


def pitcher_status(check_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get Green/Yellow/Red status for all pitchers on a given date.
    Also checks multi-day cumulative limits per OBA rules.
    """
    df = _load_pitch_log()
    if df.empty:
        return pd.DataFrame(columns=[
            "Player", "Last_Outing", "Pitches", "Rest_Days",
            "Available_Date", "Status", "Status_Detail",
            "2Day_Total", "4Day_Total", "Consec_Days",
        ])

    target = pd.Timestamp(check_date) if check_date else pd.Timestamp(datetime.today().date())
    latest = df.sort_values("Date").groupby("Player").last().reset_index()

    rows = []
    for _, row in latest.iterrows():
        player = row["Player"]
        avail = pd.Timestamp(row["Available_Date"])
        days_since = (target - row["Date"]).days

        player_log = df[df["Player"] == player].sort_values("Date")

        two_day_start = target - timedelta(days=1)
        two_day_total = player_log[
            (player_log["Date"] >= two_day_start) & (player_log["Date"] <= target)
        ]["Pitches"].sum()

        four_day_start = target - timedelta(days=3)
        four_day_total = player_log[
            (player_log["Date"] >= four_day_start) & (player_log["Date"] <= target)
        ]["Pitches"].sum()

        consecutive = 0
        check = target - timedelta(days=1)
        all_dates = set(pd.Timestamp(d) for d in player_log["Date"].unique())
        while pd.Timestamp(check) in all_dates:
            consecutive += 1
            check -= timedelta(days=1)

        remaining_today = OBA_MAX_PITCHES_DAY
        remaining_2day = OBA_MAX_PITCHES_2DAY - int(two_day_total)
        remaining_4day = OBA_MAX_PITCHES_4DAY - int(four_day_total)

        if target >= avail:
            if consecutive >= 3:
                status = "RED"
                detail = "No pitching: would be 4th consecutive day (OBA prohibited)"
            elif consecutive >= 2:
                first_2_days = player_log[
                    player_log["Date"].isin([target - timedelta(days=1), target - timedelta(days=2)])
                ]["Pitches"].sum()
                if first_2_days > 30:
                    status = "RED"
                    detail = f"No pitching: 3rd consecutive day, prior 2 days = {int(first_2_days)} pitches (max 30)"
                else:
                    status = "YELLOW"
                    detail = f"3rd consecutive day, prior 2 days = {int(first_2_days)}/30 pitches. Max {min(remaining_2day, remaining_4day, 30 - int(first_2_days))} pitches today"
            elif remaining_2day <= 0 or remaining_4day <= 0:
                status = "RED"
                detail = f"Cumulative limit reached (2-day: {int(two_day_total)}/{OBA_MAX_PITCHES_2DAY}, 4-day: {int(four_day_total)}/{OBA_MAX_PITCHES_4DAY})"
            elif days_since >= 4:
                status = "GREEN"
                detail = f"Full go, well rested. Available: {min(remaining_2day, remaining_4day, OBA_MAX_PITCHES_DAY)} pitches"
            else:
                max_available = min(remaining_2day, remaining_4day, OBA_MAX_PITCHES_DAY)
                status = "GREEN"
                detail = f"Available. Max {max_available} pitches (2-day: {int(two_day_total)}/{OBA_MAX_PITCHES_2DAY}, 4-day: {int(four_day_total)}/{OBA_MAX_PITCHES_4DAY})"
        elif (avail - target).days == 1:
            status = "YELLOW"
            detail = f"Bullpen only, available to pitch {avail.strftime('%m/%d')}"
        else:
            status = "RED"
            detail = f"No throwing, available {avail.strftime('%m/%d')} ({(avail - target).days} days rest remaining)"

        rows.append({
            "Player": player,
            "Last_Outing": row["Date"].strftime("%Y-%m-%d"),
            "Pitches": int(row["Pitches"]),
            "Rest_Days": int(row["Rest_Days"]),
            "Available_Date": avail.strftime("%Y-%m-%d"),
            "Status": status,
            "Status_Detail": detail,
            "2Day_Total": int(two_day_total),
            "4Day_Total": int(four_day_total),
            "Consec_Days": consecutive,
        })

    return pd.DataFrame(rows)


def print_pitcher_status(status_df: pd.DataFrame):
    print("=" * 100)
    print("  PITCHER AVAILABILITY REPORT (OBA / Baseball Canada 13U Rules)")
    print("=" * 100)
    print()
    for _, row in status_df.iterrows():
        icon = {"GREEN": "[GO] ", "YELLOW": "[BP] ", "RED": "[NO] "}[row["Status"]]
        print(f"  {icon} {row['Player']:15s} | {row['Pitches']:3d} pitches on {row['Last_Outing']} | {row['Status_Detail']}")
        print(f"       {'':15s} | Consec days: {row['Consec_Days']} | 2-day: {row['2Day_Total']}/{OBA_MAX_PITCHES_2DAY} | 4-day: {row['4Day_Total']}/{OBA_MAX_PITCHES_4DAY}")
    print()
    print("  OBA 13U Pitch Count Rules (Baseball Canada Section 4.4):")
    print(f"  Daily max: {OBA_MAX_PITCHES_DAY} pitches")
    print(f"  2-day cumulative max: {OBA_MAX_PITCHES_2DAY} pitches")
    print(f"  4-day cumulative max: {OBA_MAX_PITCHES_4DAY} pitches")
    print(f"  Max consecutive pitching days: {OBA_MAX_CONSECUTIVE_DAYS} (only if first 2 days total <= 30 pitches)")
    print(f"  Cannot pitch 4 consecutive days (absolute)")
    print()
    print("  Rest schedule:")
    for (lo, hi), days in OBA_PITCH_COUNT_13U.items():
        label = f"{days} day{'s' if days != 1 else ''}" if days > 0 else "None"
        print(f"    {lo:3d}-{hi:3d} pitches: {label}")
    print()
    print("  Pitcher cannot catch the same calendar day (Section 4.4(j))")
    print(f"  Mercy rule: 18 runs after 3 inn, 15 after 4, 10 after 5")
    print()


# ─────────────────────────────────────────────────────────────
# DEMO / EXAMPLE RUNNER
# ─────────────────────────────────────────────────────────────

def run_demo():
    """Run the full demo with OBA rules."""

    print("\n" + "=" * 80)
    print("  DEMO 1: Practice Plan (OBA 13U)")
    print("  90 min | 12 players | 3 coaches")
    print("  Focus: Middle Infield Double Play Feeds and Turns")
    print("=" * 80 + "\n")

    result = generate_practice(
        duration_minutes=90,
        num_players=12,
        num_coaches=3,
        primary_focus="Middle Infield Double Play Feeds and Turns",
    )
    print_practice(result)

    print("\n" + "=" * 80)
    print("  DEMO 2: Developmental Lineup Suggestion (OBA 13U)")
    print("  12 players, 3 heavy SS/P kids forced to outfield")
    print("  Marcus and Devon are designated pitchers (cannot catch)")
    print("=" * 80 + "\n")

    roster = [
        "Marcus", "Devon", "Jaylen",
        "Tyler", "Noah", "Ethan",
        "Carlos", "Aiden", "Bryce",
        "Liam", "Mason", "Kai",
    ]
    df = initialize_roster(roster)
    df.loc[df["Player"] == "Marcus", ["SS", "P"]] = [12, 10]
    df.loc[df["Player"] == "Devon", ["SS", "P"]] = [11, 8]
    df.loc[df["Player"] == "Jaylen", ["P", "SS"]] = [10, 11]

    df.loc[df["Player"] == "Tyler", ["C"]] = 14
    df.loc[df["Player"] == "Noah", ["1B"]] = 10
    df.loc[df["Player"] == "Ethan", ["2B", "3B"]] = [8, 6]
    df.loc[df["Player"] == "Carlos", ["LF", "CF"]] = [7, 5]
    df.loc[df["Player"] == "Aiden", ["RF", "LF"]] = [9, 4]
    df.loc[df["Player"] == "Bryce", ["3B", "1B"]] = [7, 6]
    df.loc[df["Player"] == "Liam", ["CF", "RF"]] = [6, 8]
    df.loc[df["Player"] == "Mason", ["2B", "SS"]] = [5, 3]
    df.loc[df["Player"] == "Kai", ["LF", "RF"]] = [4, 3]

    df.loc[df["Player"] == "Marcus", "Games"] = 6
    df.loc[df["Player"] == "Devon", "Games"] = 6
    df.loc[df["Player"] == "Jaylen", "Games"] = 6
    df.loc[df["Player"] == "Tyler", "Games"] = 6

    _save_roster(df)

    print("Current Innings-Played Matrix:")
    print(df.to_string(index=False))
    print()

    lineup = suggest_lineup(
        innings=7,
        locked={"Tyler": "C"},
        force_outfield=["Marcus", "Devon", "Jaylen"],
        designated_pitchers=["Marcus", "Devon"],
    )
    print_lineup(lineup)

    exposure_before = df.set_index("Player")[POSITIONS]
    print("Key Rotation Insight:")
    for p in ["Marcus", "Devon", "Jaylen"]:
        row = exposure_before.loc[p]
        of_innings = row["LF"] + row["CF"] + row["RF"]
        if_innings = row["SS"] + row["P"]
        print(f"  {p}: {int(if_innings)} innings at SS/P, {int(of_innings)} innings in OF (before this game)")
    print(f"  Algorithm forces these 3 to LF/CF/RF to balance exposure.")
    print(f"  Marcus and Devon blocked from catching (OBA: pitcher cannot catch same day).\n")

    print("\n" + "=" * 80)
    print("  DEMO 3: Pitch Count & Recovery Monitor (OBA 13U)")
    print("=" * 80 + "\n")

    log_pitches("Marcus", 72, "2026-05-12")
    log_pitches("Devon", 45, "2026-05-13")
    log_pitches("Jaylen", 20, "2026-05-11")
    log_pitches("Tyler", 82, "2026-05-10")

    status = pitcher_status("2026-05-14")
    print_pitcher_status(status)


if __name__ == "__main__":
    run_demo()
