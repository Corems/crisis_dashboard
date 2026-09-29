import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent.parent / "config" / "indicators.json"


def load_config() -> dict[str, dict]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return {item["fred_id"]: item for item in raw}


INDICATORS_CONFIG = load_config()


@dataclass
class ScoredIndicator:
    fred_id: str
    name: str
    category: str
    value: float
    previous_value: float | None
    weight: float
    score: float
    hint: dict
    update_frequency: str | None = None
    inverted: bool = False

    @property
    def delta(self) -> float | None:
        if self.previous_value is None:
            return None
        return round(self.value - self.previous_value, 4)


def normalize(value: float, low: float, high: float, inverted: bool) -> float:

    if high == low:
        return 0.0
    if not inverted:
        n = (value - low) / (high - low)
    else:
        n = (low - value) / (low - high) if low != high else 0.0
    return max(0.0, min(1.0, n))


def calculate_score(raw_indicators: list[dict[str, Any]]) -> tuple[list[ScoredIndicator], float]:

    scored = []
    total = 0.0

    for row in raw_indicators:
        fred_id = row["fred_id"]
        value = row["value"]
        weight = row["weight"]

        config = INDICATORS_CONFIG.get(fred_id)
        if config:
            low = config["threshold_low"]
            high = config["threshold_high"]
            inverted = config["inverted"]
            n = normalize(value, low, high, inverted)
            category = config.get("category", "")
            hint = config.get("hint", {})
        else:
            n = 0.5
            category = ""
            hint = {}

        score = round(weight * n, 2)
        total += score

        scored.append(
            ScoredIndicator(
                fred_id=fred_id,
                name=row["name"],
                category=category,
                value=value,
                previous_value=row.get("previous_value"),
                weight=weight,
                score=score,
                hint=hint,
                update_frequency=config.get("update_frequency") if config else None,
                inverted=config.get("inverted", False) if config else False,
            )
        )

    return scored, round(min(total, 100.0), 1)
