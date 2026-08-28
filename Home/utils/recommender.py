"""Explainable constraint-based property recommendations.

Location and budget are hard constraints: they decide which rows are eligible.
The remaining fields are optional preferences used only to rank eligible rows.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


PREFERENCE_WEIGHTS = {
    "property_type": 15,
    "bedrooms": 15,
    "bathrooms": 10,
    "min_area": 10,
    "furnishing_type": 10,
    "luxury_category": 5,
    "floor_category": 5,
    "balcony": 5,
    "servant_room": 3,
    "store_room": 2,
}

FURNISHING_LABELS = {0: "Unfurnished", 1: "Semi-Furnished", 2: "Furnished"}


def _text(value: Any) -> str:
    return str(value).strip().lower()


def _number(value: Any) -> float | None:
    if pd.isna(value):
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else None


def _same(value: Any, target: Any) -> bool:
    return _text(value) == _text(target)


def sector_options(df: pd.DataFrame) -> list[str]:
    values = {_text(v) for v in df["sector"].dropna()}

    def sort_key(value: str) -> tuple[int, Any]:
        match = re.search(r"\d+", value)
        return (int(match.group()), value) if match else (9999, value)

    return sorted(values, key=sort_key)


def format_price(price_cr: float) -> str:
    return f"₹{price_cr:,.2f} Cr"


def display_furnishing(value: Any) -> str:
    number = _number(value)
    return FURNISHING_LABELS.get(int(number), "Not specified") if number is not None else str(value)


def _preference_match(row: pd.Series, name: str, target: Any) -> tuple[float, str | None, str | None]:
    """Return normalized match score plus an honest reason and trade-off."""
    if name == "property_type":
        match = _same(row[name], target)
        return float(match), f"{str(target).title()} preference matched" if match else None, None if match else f"Property type is {row[name]}"
    if name == "bedrooms":
        actual = _number(row["bedRoom"])
        match = actual is not None and (actual >= 4 if target == "4+" else actual == float(target))
        return float(match), f"{target} bedroom preference matched" if match else None, None if match else f"Bedrooms: {actual:g}" if actual is not None else "Bedroom count unavailable"
    if name == "bathrooms":
        actual = _number(row["bathroom"])
        match = actual is not None and actual >= float(target)
        return float(match), f"At least {target} bathrooms" if match else None, None if match else f"Bathrooms: {actual:g}" if actual is not None else "Bathroom count unavailable"
    if name == "min_area":
        actual = _number(row["built_up_area"])
        if actual is None:
            return 0.0, None, "Built-up area unavailable"
        score = min(actual / float(target), 1.0)
        return score, f"Built-up area {actual:,.0f} sq.ft." if actual >= float(target) else None, None if actual >= float(target) else f"Area is {actual:,.0f} sq.ft."
    if name == "furnishing_type":
        match = _number(row[name]) == float(target)
        return float(match), f"{FURNISHING_LABELS.get(int(float(target)), target)} furnishing matched" if match else None, None if match else f"Furnishing: {display_furnishing(row[name])}"
    if name in {"luxury_category", "floor_category"}:
        match = _same(row[name], target)
        return float(match), f"{str(target).title()} {name.replace('_', ' ')} matched" if match else None, None if match else f"{name.replace('_', ' ').title()}: {row[name]}"
    if name == "balcony":
        actual = _number(row[name])
        match = actual is not None and actual >= float(target)
        return float(match), f"At least {target} balconies" if match else None, None if match else f"Balconies: {row[name]}"
    if name in {"servant_room", "store_room"}:
        column = "servant room" if name == "servant_room" else "store room"
        actual = _number(row[column]) or 0
        match = actual >= float(target)
        label = "Servant room" if name == "servant_room" else "Store room"
        return float(match), f"{label} available" if match else None, None if match else f"{label} not available"
    return 0.0, None, None


def recommend_properties(
    df: pd.DataFrame,
    sector: str,
    max_budget: float,
    preferences: dict[str, Any] | None = None,
    limit: int = 10,
    sort_by: str = "Best Match",
) -> pd.DataFrame:
    """Filter hard constraints, then rank candidates using active preferences."""
    preferences = {k: v for k, v in (preferences or {}).items() if v not in (None, "Any", "")}
    work = df.copy()
    work["_price"] = pd.to_numeric(work["price"], errors="coerce")

    # Hard constraints. No relaxed row can enter the exact result set.
    candidates = work[
        work["sector"].map(_text).eq(_text(sector))
        & work["_price"].le(float(max_budget))
    ].copy()
    if candidates.empty:
        return candidates.assign(match_score=pd.Series(dtype=float))

    active_weights = {"location": 25, "budget": 20}
    active_weights.update({key: PREFERENCE_WEIGHTS[key] for key in preferences if key in PREFERENCE_WEIGHTS})
    total_weight = sum(active_weights.values())

    rows = []
    for index, row in candidates.iterrows():
        budget_utilization = min(max(row["_price"] / float(max_budget), 0), 1)
        points = {"location": 25.0, "budget": 20.0 * budget_utilization}
        reasons = ["Within maximum budget", "Preferred location matched"]
        tradeoffs: list[str] = []
        for name, target in preferences.items():
            if name not in PREFERENCE_WEIGHTS:
                continue
            match_score, reason, tradeoff = _preference_match(row, name, target)
            points[name] = PREFERENCE_WEIGHTS[name] * match_score
            if reason:
                reasons.append(reason)
            if tradeoff:
                tradeoffs.append(tradeoff)

        result = row.to_dict()
        result.update(
            match_score=round(sum(points.values()) / total_weight * 100, 1),
            budget_utilization=round(budget_utilization * 100, 1),
            score_breakdown={key: round(value / active_weights[key] * 100, 1) for key, value in points.items()},
            match_reasons=reasons,
            tradeoffs=tradeoffs,
            _index=index,
        )
        rows.append(result)

    ranked = pd.DataFrame(rows)
    if sort_by == "Lowest Price":
        ranked = ranked.sort_values(["_price", "match_score"], ascending=[True, False])
    elif sort_by == "Largest Area":
        ranked = ranked.assign(_area=pd.to_numeric(ranked["built_up_area"], errors="coerce")).sort_values(["_area", "match_score"], ascending=[False, False])
    elif sort_by == "Most Bedrooms":
        ranked = ranked.assign(_bedrooms=ranked["bedRoom"].map(_number)).sort_values(["_bedrooms", "match_score"], ascending=[False, False])
    elif sort_by == "Best Budget Fit":
        ranked = ranked.assign(_budget_gap=(float(max_budget) - ranked["_price"]).abs()).sort_values(["_budget_gap", "match_score"], ascending=[True, False])
    else:
        ranked = ranked.sort_values(["match_score", "_price"], ascending=[False, True])
    return ranked.head(limit).reset_index(drop=True)


def alternative_properties(df: pd.DataFrame, sector: str, max_budget: float, limit: int = 3) -> dict[str, pd.DataFrame]:
    """Return explicitly relaxed suggestions for the no-exact-match state."""
    work = df.copy()
    work["_price"] = pd.to_numeric(work["price"], errors="coerce")
    same_sector = work[work["sector"].map(_text).eq(_text(sector))]
    return {
        "same_sector_over_budget": same_sector[same_sector["_price"] > max_budget].sort_values("_price").head(limit),
        "other_sector_within_budget": work[
            ~work["sector"].map(_text).eq(_text(sector)) & work["_price"].le(max_budget)
        ].sort_values("_price").head(limit),
    }


if __name__ == "__main__":
    # ponytail: one small smoke check protects the hard-constraint boundary.
    sample = pd.DataFrame(
        {"sector": ["sector 92", "sector 92", "sector 90"], "price": [1.2, 1.8, 1.0], "bedRoom": [3, 2, 3], "bathroom": [2, 2, 2], "built_up_area": [1500, 1200, 1400], "property_type": ["flat"] * 3, "furnishing_type": [0] * 3, "luxury_category": ["High"] * 3, "floor_category": ["Mid Floor"] * 3, "balcony": [2] * 3, "servant room": [0] * 3, "store room": [0] * 3}
    )
    assert len(recommend_properties(sample, "sector 92", 1.5)) == 1
