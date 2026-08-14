"""
Startup validation for player availability (injuries, suspensions, transfers).

Sources FPL bootstrap-static API and persists status to the local database
before the fantasy engine builds recommended squads.
"""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

import psycopg2
from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

FPL_BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

STATUS_INJURED = {"i"}
STATUS_SUSPENDED = {"s"}
STATUS_UNAVAILABLE = {"u", "n"}
STATUS_DOUBTFUL = {"d"}

FPL_TEAM_TO_DISPLAY = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton & Hove Albion",
    "Burnley": "Burnley",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Leeds": "Leeds United",
    "Liverpool": "Liverpool",
    "Man City": "Manchester City",
    "Man Utd": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Spurs": "Tottenham Hotspur",
    "Sunderland": "Sunderland",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
    "Ipswich": "Ipswich Town",
    "Leicester": "Leicester City",
    "Luton": "Luton Town",
    "Sheffield Utd": "Sheffield United",
    "Southampton": "Southampton",
}


def normalize_name(name: str) -> str:
    if not name:
        return ""
    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]", "", text.lower())
    return text


def ensure_player_status_schema(conn) -> list[str]:
    warnings: list[str] = []
    with conn.cursor() as cur:
        for stmt in (
            "ALTER TABLE players ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE",
            "ALTER TABLE players ADD COLUMN IF NOT EXISTS is_transferred_out BOOLEAN DEFAULT FALSE",
            "ALTER TABLE players ADD COLUMN IF NOT EXISTS unavailable_reason VARCHAR(255)",
            "ALTER TABLE players ADD COLUMN IF NOT EXISTS status_checked_at TIMESTAMP WITH TIME ZONE",
        ):
            try:
                cur.execute(stmt)
            except Exception as exc:
                conn.rollback()
                warnings.append(f"players schema: {exc}")

        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fantasy_player_status (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    player_name VARCHAR(255) NOT NULL,
                    team_name VARCHAR(255) NOT NULL,
                    fpl_id INT,
                    status_code CHAR(1) DEFAULT 'a',
                    is_injured BOOLEAN DEFAULT FALSE,
                    is_suspended BOOLEAN DEFAULT FALSE,
                    is_banned BOOLEAN DEFAULT FALSE,
                    is_transferred BOOLEAN DEFAULT FALSE,
                    current_team VARCHAR(255),
                    news TEXT,
                    chance_this_round INT,
                    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(player_name, team_name)
                );
            """)
        except Exception as exc:
            conn.rollback()
            warnings.append(f"fantasy_player_status: {exc}")
    conn.commit()
    return warnings


def fetch_fpl_data() -> dict[str, Any] | None:
    try:
        response = requests.get(FPL_BOOTSTRAP_URL, impersonate="chrome", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("FPL bootstrap fetch failed: %s", exc)
        return None


def build_fpl_team_map(teams: list[dict]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for team in teams:
        short = team.get("short_name") or team.get("name", "")
        display = FPL_TEAM_TO_DISPLAY.get(short, team.get("name", short))
        mapping[int(team["id"])] = display
    return mapping


def build_fpl_lookup(elements: list[dict]) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for element in elements:
        full_name = f"{element.get('first_name', '')} {element.get('second_name', '')}".strip()
        keys = {
            normalize_name(full_name),
            normalize_name(element.get("web_name", "")),
        }
        for part in full_name.split():
            keys.add(normalize_name(part))
        for key in keys:
            if key:
                lookup[key] = element
    return lookup


def match_fpl_element(name: str, lookup: dict[str, dict]) -> dict | None:
    norm = normalize_name(name)
    if norm in lookup:
        return lookup[norm]

    for key, element in lookup.items():
        if key and (norm.endswith(key) or key.endswith(norm)):
            return element

    last = normalize_name(name.split()[-1]) if name.split() else ""
    if last and last in lookup:
        return lookup[last]

    return None


def classify_fpl_status(element: dict) -> dict[str, Any]:
    code = (element.get("status") or "a").lower()
    news = (element.get("news") or "").strip()
    chance = element.get("chance_of_playing_this_round")

    is_injured = code in STATUS_INJURED
    is_suspended = code in STATUS_SUSPENDED
    is_banned = is_suspended and any(
        word in news.lower() for word in ("ban", "banned", "suspension", "sent off", "red card")
    )
    is_unavailable = code in STATUS_UNAVAILABLE

    if code in STATUS_DOUBTFUL and chance is not None and chance <= 25:
        is_injured = True

    reason_parts = []
    if news:
        reason_parts.append(news)
    elif is_banned:
        reason_parts.append("Suspended (ban)")
    elif is_suspended:
        reason_parts.append("Suspended")
    elif is_injured:
        reason_parts.append("Injured")
    elif is_unavailable:
        reason_parts.append("Unavailable")

    return {
        "status_code": code,
        "is_injured": is_injured or (code in STATUS_DOUBTFUL and not is_suspended),
        "is_suspended": is_suspended,
        "is_banned": is_banned,
        "is_unavailable": is_unavailable,
        "news": news,
        "chance_this_round": chance,
        "reason": " — ".join(reason_parts) if reason_parts else "",
    }


def get_db_connection():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    return psycopg2.connect(
        f"dbname=fpredict_db user={db_user} password={db_password} host=localhost"
    )


def load_curated_fantasy_names() -> list[tuple[str, str]]:
    from src.fantasy.engine import FALLBACK_PLAYERS

    seen: set[str] = set()
    players: list[tuple[str, str]] = []
    for raw in FALLBACK_PLAYERS:
        key = f"{raw['name']}|{raw['team']}"
        if key in seen:
            continue
        seen.add(key)
        players.append((raw["name"], raw["team"]))
    return players


def validate_players_on_startup() -> dict[str, Any]:
    logger.info("Running player availability validation (injuries / transfers / bans)...")
    summary = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source": "fpl_bootstrap",
        "matched": 0,
        "injured": 0,
        "suspended": 0,
        "transferred": 0,
        "updated_db_players": 0,
        "ready": False,
        "errors": [],
    }

    try:
        conn = get_db_connection()
        schema_warnings = ensure_player_status_schema(conn)
        summary["errors"].extend(schema_warnings)
    except Exception as exc:
        logger.warning("Player status DB connection failed: %s", exc)
        summary["errors"].append(str(exc))
        summary["ready"] = True
        return summary

    fpl_data = fetch_fpl_data()
    if not fpl_data:
        summary["errors"].append("FPL API unavailable — using last known player status.")
        summary["ready"] = True
        conn.close()
        return summary

    team_map = build_fpl_team_map(fpl_data.get("teams", []))
    lookup = build_fpl_lookup(fpl_data.get("elements", []))
    checked_at = datetime.now(timezone.utc)
    active_teams = set(team_map.values())

    try:
        with conn.cursor() as cur:
            for player_name, team_name in load_curated_fantasy_names():
                element = match_fpl_element(player_name, lookup)
                if not element:
                    continue

                summary["matched"] += 1
                fpl_team = team_map.get(int(element["team"]), "")
                status = classify_fpl_status(element)

                is_transferred = False
                if fpl_team and fpl_team != team_name:
                    if fpl_team not in active_teams:
                        is_transferred = True

                if status["is_injured"]:
                    summary["injured"] += 1
                if status["is_suspended"] or status["is_banned"]:
                    summary["suspended"] += 1
                if is_transferred:
                    summary["transferred"] += 1

                cur.execute("""
                    INSERT INTO fantasy_player_status (
                        player_name, team_name, fpl_id, status_code,
                        is_injured, is_suspended, is_banned, is_transferred,
                        current_team, news, chance_this_round, checked_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_name, team_name) DO UPDATE SET
                        fpl_id = EXCLUDED.fpl_id,
                        status_code = EXCLUDED.status_code,
                        is_injured = EXCLUDED.is_injured,
                        is_suspended = EXCLUDED.is_suspended,
                        is_banned = EXCLUDED.is_banned,
                        is_transferred = EXCLUDED.is_transferred,
                        current_team = EXCLUDED.current_team,
                        news = EXCLUDED.news,
                        chance_this_round = EXCLUDED.chance_this_round,
                        checked_at = EXCLUDED.checked_at
                """, (
                    player_name,
                    team_name,
                    element.get("id"),
                    status["status_code"],
                    status["is_injured"],
                    status["is_suspended"],
                    status["is_banned"],
                    is_transferred,
                    fpl_team or team_name,
                    status["news"] or None,
                    status["chance_this_round"],
                    checked_at,
                ))

        conn.commit()

        try:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        UPDATE players SET
                            is_injured = FALSE,
                            is_suspended = FALSE,
                            is_transferred_out = FALSE,
                            unavailable_reason = NULL
                    """)
                except Exception as exc:
                    conn.rollback()
                    summary["errors"].append(f"players reset skipped: {exc}")

                try:
                    cur.execute("""
                        SELECT p.id, p.name, t.team_name
                        FROM players p
                        JOIN teams t ON p.team_id = t.id
                    """)
                    db_rows = cur.fetchall()
                except Exception as exc:
                    conn.rollback()
                    db_rows = []
                    summary["errors"].append(f"players sync skipped: {exc}")

                for player_id, name, team_name in db_rows:
                    if not name or str(name).strip().lower() == "nan":
                        continue
                    element = match_fpl_element(str(name), lookup)
                    if not element:
                        continue

                    fpl_team = team_map.get(int(element["team"]), "")
                    status = classify_fpl_status(element)
                    is_transferred = bool(
                        fpl_team and fpl_team != team_name and fpl_team not in active_teams
                    )
                    if fpl_team and fpl_team != team_name and fpl_team in active_teams:
                        cur.execute("SELECT id FROM teams WHERE team_name = %s LIMIT 1", (fpl_team,))
                        new_team = cur.fetchone()
                        if new_team:
                            cur.execute(
                                "UPDATE players SET team_id = %s WHERE id = %s",
                                (new_team[0], player_id),
                            )
                            is_transferred = False

                    reason = status["reason"]
                    if is_transferred:
                        reason = f"Transferred out of squad ({team_name} → {fpl_team or 'unknown'})"

                    cur.execute("""
                        UPDATE players SET
                            is_injured = %s,
                            is_suspended = %s,
                            is_transferred_out = %s,
                            unavailable_reason = %s,
                            status_checked_at = %s
                        WHERE id = %s
                    """, (
                        status["is_injured"],
                        status["is_suspended"] or status["is_banned"],
                        is_transferred,
                        reason or None,
                        checked_at,
                        player_id,
                    ))
                    summary["updated_db_players"] += 1

                conn.commit()
        except Exception as exc:
            conn.rollback()
            summary["errors"].append(f"players sync skipped: {exc}")

        summary["ready"] = True
        logger.info(
            "Player validation complete: matched=%s injured=%s suspended=%s transferred=%s",
            summary["matched"],
            summary["injured"],
            summary["suspended"],
            summary["transferred"],
        )
    except Exception as exc:
        conn.rollback()
        logger.warning("Player validation failed: %s", exc)
        summary["errors"].append(str(exc))
        summary["ready"] = True
    finally:
        conn.close()

    return summary


def load_fantasy_availability() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT player_name, team_name, is_injured, is_suspended,
                       is_banned, is_transferred, current_team, news, checked_at
                FROM fantasy_player_status
            """)
            for row in cur.fetchall():
                key = f"{row[0]}|{row[1]}"
                result[key] = {
                    "is_injured": bool(row[2]),
                    "is_suspended": bool(row[3]),
                    "is_banned": bool(row[4]),
                    "is_transferred": bool(row[5]),
                    "current_team": row[6],
                    "news": row[7],
                    "checked_at": row[8].isoformat() if row[8] else None,
                }
        conn.close()
    except Exception as exc:
        logger.debug("Could not load fantasy availability: %s", exc)
    return result
