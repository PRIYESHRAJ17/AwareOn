from __future__ import annotations

from typing import Any

import pandas as pd


DEFAULT_SOURCE = (
    "data/processed/weather/era5_environment_timeseries.csv"
)


def _num(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_change(
    recent: float,
    baseline: float,
) -> float:
    if baseline == 0:
        return 0.0

    return (
        (recent - baseline)
        /
        abs(baseline)
    ) * 100.0


def _direction(
    change: float,
) -> str:
    if change >= 10.0:
        return "INCREASING"

    if change <= -10.0:
        return "DECREASING"

    return "STABLE"


def build_multiscale_temporal_intelligence(
    source: str = DEFAULT_SOURCE,
) -> dict[str, Any]:

    df = pd.read_csv(
        source,
        parse_dates=["valid_time"],
    )

    if df.empty:
        raise ValueError(
            "Temporal dataset is empty."
        )

    required = {
        "valid_time",
        "precip_mm",
        "swvl1",
        "swvl2",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "Missing columns: "
            +
            ", ".join(
                sorted(missing)
            )
        )

    df = (
        df.sort_values("valid_time")
        .reset_index(drop=True)
    )

    df["soil_mean"] = (
        df["swvl1"]
        +
        df["swvl2"]
    ) / 2.0

    df["rain_24h"] = (
        df["precip_mm"]
        .rolling(
            24,
            min_periods=1,
        )
        .sum()
    )

    latest = df["valid_time"].max()

    windows = [
        ("7D", 7),
        ("30D", 30),
        ("90D", 90),
        ("365D", 365),
    ]

    results = []

    for label, days in windows:

        recent_start = (
            latest
            -
            pd.Timedelta(
                days=days
            )
        )

        baseline_start = (
            recent_start
            -
            pd.Timedelta(
                days=days
            )
        )

        recent = df[
            df["valid_time"] >= recent_start
        ]

        baseline = df[
            (
                df["valid_time"] >= baseline_start
            )
            &
            (
                df["valid_time"] < recent_start
            )
        ]

        if recent.empty or baseline.empty:
            continue

        recent_rain = float(
            recent["rain_24h"].mean()
        )

        baseline_rain = float(
            baseline["rain_24h"].mean()
        )

        recent_soil = float(
            recent["soil_mean"].mean()
        )

        baseline_soil = float(
            baseline["soil_mean"].mean()
        )

        rain_change = _safe_change(
            recent_rain,
            baseline_rain,
        )

        soil_change = _safe_change(
            recent_soil,
            baseline_soil,
        )

        composite_change = (
            rain_change * 0.75
            +
            soil_change * 0.25
        )

        results.append(
            {
                "window":
                    label,

                "days":
                    days,

                "rain_change_percent":
                    rain_change,

                "soil_change_percent":
                    soil_change,

                "composite_change_percent":
                    composite_change,

                "direction":
                    _direction(
                        composite_change
                    ),

                "recent_observations":
                    int(
                        len(recent)
                    ),

                "baseline_observations":
                    int(
                        len(baseline)
                    ),
            }
        )

    if not results:
        raise ValueError(
            "Could not construct temporal windows."
        )

    increasing = sum(
        1
        for item in results
        if item["direction"] == "INCREASING"
    )

    decreasing = sum(
        1
        for item in results
        if item["direction"] == "DECREASING"
    )

    stable = sum(
        1
        for item in results
        if item["direction"] == "STABLE"
    )

    if increasing >= 3:
        overall = "MULTISCALE_INCREASING"

    elif decreasing >= 3:
        overall = "MULTISCALE_DECREASING"

    elif stable >= 3:
        overall = "MULTISCALE_STABLE"

    elif increasing > decreasing:
        overall = "MIXED_WITH_INCREASING_BIAS"

    elif decreasing > increasing:
        overall = "MIXED_WITH_DECREASING_BIAS"

    else:
        overall = "MIXED"

    direction_set = {
        item["direction"]
        for item in results
    }

    if len(direction_set) == 1:
        agreement = "STRONG"

    elif len(direction_set) == 2:
        agreement = "PARTIAL"

    else:
        agreement = "DIVERGENT"

    shortest = min(
        results,
        key=lambda item: item["days"],
    )

    longest = max(
        results,
        key=lambda item: item["days"],
    )

    short_change = _num(
        shortest[
            "composite_change_percent"
        ]
    )

    long_change = _num(
        longest[
            "composite_change_percent"
        ]
    )

    if (
        short_change > 10.0
        and
        long_change <= 10.0
    ):
        timescale_pattern = (
            "SHORT_TERM_EMERGENCE"
        )

    elif (
        short_change <= 10.0
        and
        long_change > 10.0
    ):
        timescale_pattern = (
            "LONG_TERM_PRESSURE"
        )

    elif (
        short_change > 10.0
        and
        long_change > 10.0
    ):
        timescale_pattern = (
            "PERSISTENT_MULTISCALE_PRESSURE"
        )

    elif (
        short_change < -10.0
        and
        long_change < -10.0
    ):
        timescale_pattern = (
            "MULTISCALE_DECLINE"
        )

    else:
        timescale_pattern = (
            "STABLE_OR_MIXED"
        )

    if agreement == "STRONG":
        confidence = "HIGH"

    elif agreement == "PARTIAL":
        confidence = "MODERATE"

    else:
        confidence = "LIMITED"

    return {
        "engine":
            "AWAREON_MULTISCALE_TEMPORAL_INTELLIGENCE",

        "version":
            "1.0",

        "status":
            "READY",

        "overall":
            overall,

        "agreement":
            agreement,

        "timescale_pattern":
            timescale_pattern,

        "confidence":
            confidence,

        "windows":
            results,

        "summary":
            {
                "increasing_windows":
                    increasing,

                "decreasing_windows":
                    decreasing,

                "stable_windows":
                    stable,

                "window_count":
                    len(results),
            },

        "interpretation":
            (
                f"Temporal behavior is {overall.lower()} "
                f"across {len(results)} timescales with "
                f"{agreement.lower()} directional agreement. "
                f"The dominant pattern is "
                f"{timescale_pattern.lower()}."
            ),
    }
