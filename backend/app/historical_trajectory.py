from __future__ import annotations

from typing import Any

import pandas as pd


DEFAULT_SOURCE = (
    "data/processed/weather/era5_environment_timeseries.csv"
)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _trajectory_band(
    change: float,
    volatility_change: float,
) -> str:
    if change >= 25.0:
        if volatility_change >= 20.0:
            return "RAPIDLY_RISING_VOLATILE"
        return "RAPIDLY_RISING"

    if change >= 10.0:
        if volatility_change >= 20.0:
            return "RISING_VOLATILE"
        return "GRADUALLY_RISING"

    if change <= -25.0:
        return "RAPIDLY_DECLINING"

    if change <= -10.0:
        return "DECLINING"

    if volatility_change >= 30.0:
        return "VOLATILE"

    return "STABLE"


def build_historical_trajectory(
    source: str = DEFAULT_SOURCE,
    recent_days: int = 365,
    baseline_years: int = 5,
) -> dict[str, Any]:

    if recent_days <= 0:
        raise ValueError(
            "recent_days must be greater than 0."
        )

    if baseline_years <= 0:
        raise ValueError(
            "baseline_years must be greater than 0."
        )

    df = pd.read_csv(
        source,
        parse_dates=["valid_time"],
    )

    if df.empty:
        raise ValueError(
            "Historical ERA5 dataset is empty."
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
            "Historical dataset is missing columns: "
            + ", ".join(sorted(missing))
        )

    df = (
        df.sort_values("valid_time")
        .reset_index(drop=True)
    )

    df["soil_mean"] = (
        df["swvl1"] + df["swvl2"]
    ) / 2.0

    df["rainfall_24h"] = (
        df["precip_mm"]
        .rolling(24, min_periods=1)
        .sum()
    )

    df["rainfall_72h"] = (
        df["precip_mm"]
        .rolling(72, min_periods=1)
        .sum()
    )

    df["rainfall_7d"] = (
        df["precip_mm"]
        .rolling(24 * 7, min_periods=1)
        .sum()
    )

    latest_time = df["valid_time"].max()

    recent_start = (
        latest_time
        - pd.Timedelta(days=recent_days)
    )

    baseline_start = (
        latest_time
        - pd.DateOffset(years=baseline_years)
    )

    recent = df[
        df["valid_time"] >= recent_start
    ].copy()

    baseline = df[
        df["valid_time"] >= baseline_start
    ].copy()

    if recent.empty:
        raise ValueError(
            "Recent historical window is empty."
        )

    if baseline.empty:
        raise ValueError(
            "Historical baseline window is empty."
        )

    recent_rain = float(
        recent["rainfall_24h"].mean()
    )

    baseline_rain = float(
        baseline["rainfall_24h"].mean()
    )

    recent_72 = float(
        recent["rainfall_72h"].mean()
    )

    baseline_72 = float(
        baseline["rainfall_72h"].mean()
    )

    recent_7d = float(
        recent["rainfall_7d"].mean()
    )

    baseline_7d = float(
        baseline["rainfall_7d"].mean()
    )

    recent_soil = float(
        recent["soil_mean"].mean()
    )

    baseline_soil = float(
        baseline["soil_mean"].mean()
    )

    rain_change_pct = (
        _safe_div(
            recent_rain - baseline_rain,
            abs(baseline_rain),
        )
        * 100.0
    )

    rain_72_change_pct = (
        _safe_div(
            recent_72 - baseline_72,
            abs(baseline_72),
        )
        * 100.0
    )

    rain_7d_change_pct = (
        _safe_div(
            recent_7d - baseline_7d,
            abs(baseline_7d),
        )
        * 100.0
    )

    soil_change_pct = (
        _safe_div(
            recent_soil - baseline_soil,
            abs(baseline_soil),
        )
        * 100.0
    )

    recent_volatility = _num(
        recent["rainfall_24h"].std()
    )

    baseline_volatility = _num(
        baseline["rainfall_24h"].std()
    )

    volatility_change_pct = (
        _safe_div(
            recent_volatility
            - baseline_volatility,
            abs(baseline_volatility),
        )
        * 100.0
    )

    high_threshold = float(
        recent["rainfall_24h"].quantile(0.90)
    )

    extreme_threshold = float(
        recent["rainfall_24h"].quantile(0.99)
    )

    high_events = int(
        (
            recent["rainfall_24h"]
            >= high_threshold
        ).sum()
    )

    extreme_events = int(
        (
            recent["rainfall_24h"]
            >= extreme_threshold
        ).sum()
    )

    combined_change = (
        rain_change_pct * 0.45
        + rain_72_change_pct * 0.25
        + rain_7d_change_pct * 0.20
        + soil_change_pct * 0.10
    )

    change_signal = max(
        0.0,
        min(
            100.0,
            50.0 + combined_change,
        ),
    )

    volatility_signal = max(
        0.0,
        min(
            100.0,
            50.0 + volatility_change_pct,
        ),
    )

    trajectory_score = (
        change_signal * 0.70
        + volatility_signal * 0.30
    )

    trajectory = _trajectory_band(
        combined_change,
        max(
            0.0,
            volatility_change_pct,
        ),
    )

    if trajectory in {
        "RAPIDLY_RISING",
        "RAPIDLY_RISING_VOLATILE",
    }:
        trajectory_category = "EXTREME"

    elif trajectory in {
        "GRADUALLY_RISING",
        "RISING_VOLATILE",
    }:
        trajectory_category = "HIGH"

    elif trajectory in {
        "VOLATILE",
        "DECLINING",
    }:
        trajectory_category = "MODERATE"

    else:
        trajectory_category = "LOW"

    if combined_change > 10.0:
        direction = "INCREASING"
    elif combined_change < -10.0:
        direction = "DECREASING"

    else:
        direction = "STABLE"

    # --------------------------------------------------------
    # Signal evidence and data quality are separate.
    # Zero change signals means STABLE conditions, not
    # insufficient historical evidence.
    # --------------------------------------------------------

    signal_values = [
        abs(rain_change_pct),
        abs(rain_72_change_pct),
        abs(rain_7d_change_pct),
        abs(soil_change_pct),
        abs(volatility_change_pct),
    ]

    signal_points = sum(
        1
        for value in signal_values
        if value > 0.0
    )

    signal_coverage = (
        signal_points / 5.0
    )

    total_years = (
        (
            df["valid_time"].max()
            - df["valid_time"].min()
        ).total_seconds()
        /
        (365.25 * 24.0 * 3600.0)
    )

    expected_recent = max(
        1,
        recent_days * 24,
    )

    recent_completeness = min(
        1.0,
        len(recent) / expected_recent,
    )

    expected_baseline = max(
        1.0,
        baseline_years
        * 365.25
        * 24.0,
    )

    baseline_completeness = min(
        1.0,
        len(baseline) / expected_baseline,
    )

    temporal_coverage_score = min(
        1.0,
        total_years
        /
        max(
            1.0,
            float(baseline_years),
        ),
    )

    data_quality_score = (
        0.45 * temporal_coverage_score
        + 0.30 * recent_completeness
        + 0.25 * baseline_completeness
    )

    confidence_score = (
        data_quality_score * 100.0
    )

    if confidence_score >= 85.0:
        confidence_band = "HIGH"

    elif confidence_score >= 65.0:
        confidence_band = "MODERATE"

    else:
        confidence_band = "LIMITED"

    if data_quality_score >= 0.85:
        data_quality_band = "VERY_STRONG"

    elif data_quality_score >= 0.65:
        data_quality_band = "STRONG"

    elif data_quality_score >= 0.45:
        data_quality_band = "MODERATE"

    else:
        data_quality_band = "LIMITED"

    interpretation_parts = [
        (
            f"Recent {recent_days}-day environmental "
            f"conditions are {trajectory.lower()} "
            "relative to the historical baseline."
        ),
        (
            f"Composite historical change is "
            f"{combined_change:.2f}%."
        ),
        (
            f"The historical record spans approximately "
            f"{total_years:.1f} years with "
            f"{len(df):,} observations."
        ),
        (
            f"Historical data quality is "
            f"{data_quality_band.lower()}."
        ),
    ]

    if high_events > 0:
        interpretation_parts.append(
            (
                f"The recent window contains "
                f"{high_events} upper-tail "
                "24-hour rainfall observations."
            )
        )

    if extreme_events > 0:
        interpretation_parts.append(
            (
                f"{extreme_events} observations are "
                "in the recent extreme rainfall tail."
            )
        )

    latitude = None
    longitude = None

    if "latitude" in df.columns:
        latitude = float(
            df["latitude"].iloc[0]
        )

    if "longitude" in df.columns:
        longitude = float(
            df["longitude"].iloc[0]
        )

    return {
        "source": source,

        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },

        "coverage": {
            "start": str(
                df["valid_time"].min()
            ),
            "end": str(
                df["valid_time"].max()
            ),
            "observations": int(
                len(df)
            ),
            "baseline_observations": int(
                len(baseline)
            ),
            "recent_observations": int(
                len(recent)
            ),
            "approximate_years": round(
                total_years,
                3,
            ),
            "recent_completeness": round(
                recent_completeness,
                4,
            ),
            "baseline_completeness": round(
                baseline_completeness,
                4,
            ),
        },

        "windows": {
            "recent_days": recent_days,
            "baseline_years": baseline_years,
        },

        "direction": direction,

        "trajectory": trajectory,

        "trajectory_category":
            trajectory_category,

        "trajectory_score":
            round(
                trajectory_score,
                4,
            ),

        "recent_vs_baseline": {
            "rain_24h_change_percent":
                rain_change_pct,
            "rain_72h_change_percent":
                rain_72_change_pct,
            "rain_7d_change_percent":
                rain_7d_change_pct,
            "soil_change_percent":
                soil_change_pct,
            "volatility_change_percent":
                volatility_change_pct,
        },

        "recent_conditions": {
            "mean_rain_24h":
                recent_rain,
            "mean_rain_72h":
                recent_72,
            "mean_rain_7d":
                recent_7d,
            "mean_soil":
                recent_soil,
            "high_tail_observations":
                high_events,
            "extreme_tail_observations":
                extreme_events,
        },

        "baseline_conditions": {
            "mean_rain_24h":
                baseline_rain,
            "mean_rain_72h":
                baseline_72,
            "mean_rain_7d":
                baseline_7d,
            "mean_soil":
                baseline_soil,
            "rainfall_volatility":
                baseline_volatility,
        },

        "evidence": {
            "supported_signals":
                signal_points,
            "total_signals":
                5,
            "coverage":
                signal_coverage,
            "data_quality_score":
                round(
                    data_quality_score,
                    4,
                ),
            "data_quality_band":
                data_quality_band,
        },

        "confidence": {
            "score":
                round(
                    confidence_score,
                    4,
                ),
            "band":
                confidence_band,
            "basis":
                "historical_data_quality_and_coverage",
        },

        "interpretation":
            " ".join(
                interpretation_parts
            ),

        "methodology": {
            "historical_comparison":
                (
                    "Recent environmental conditions "
                    "are compared with a rolling "
                    f"{baseline_years}-year baseline."
                ),

            "trajectory_basis":
                (
                    "Rainfall accumulation, soil moisture, "
                    "and environmental volatility."
                ),

            "confidence_basis":
                (
                    "Historical duration, recent completeness, "
                    "and baseline completeness. Confidence "
                    "does not require the environment to be changing."
                ),

            "spatial_scope":
                (
                    "The available ERA5 source point; not a "
                    "direct measurement for every 100 m risk cell."
                ),
        },
    }
