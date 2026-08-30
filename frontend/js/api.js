const API_BASE = "http://127.0.0.1:8000";


/* ============================================================
   GENERIC JSON REQUEST
   ============================================================ */

export async function getJson(
    path,
    options = {}
) {

    const response =
        await fetch(
            `${API_BASE}${path}`,
            options
        );


    if (
        !response.ok
    ) {

        let detail =
            `${response.status} ${response.statusText}`;


        try {

            const body =
                await response.json();


            detail =
                body?.detail
                ||
                detail;

        } catch {
            /* Keep the HTTP error text. */
        }


        throw new Error(
            detail
        );
    }


    return response.json();
}


/* ============================================================
   AWAREON API
   ============================================================ */

export const api = {

    base:
        API_BASE,


    /* ----------------------------------------------------------
       SYSTEM
       ---------------------------------------------------------- */

    health:
        () =>
            getJson(
                "/health"
            ),


    /* ----------------------------------------------------------
       RISK
       ---------------------------------------------------------- */

    risk:
        () =>
            getJson(
                "/api/v1/risk"
            ),


    assessment:
        cellId =>
            getJson(
                `/api/v1/assessment/${encodeURIComponent(
                    cellId
                )}`
            ),


    alerts:
        () =>
            getJson(
                "/api/v1/alerts"
            ),


    /* ----------------------------------------------------------
       GIS
       ---------------------------------------------------------- */

    incidents:
        () =>
            getJson(
                "/api/v1/gis/priority-incidents"
            ),


    riskLayer:
        () =>
            getJson(
                "/api/v1/gis/risk-layer"
            ),


    exposureLayer:
        () =>
            getJson(
                "/api/v1/gis/exposure-layer"
            ),


    historicalLayer:
        () =>
            getJson(
                "/api/v1/gis/historical-hotspots"
            ),


    boundary:
        () =>
            getJson(
                "/api/v1/gis/boundary"
            ),


    nearby:
        (
            latitude,
            longitude,
            radiusMeters = 5000
        ) =>
            getJson(
                `/api/v1/gis/nearby?latitude=${encodeURIComponent(
                    latitude
                )}&longitude=${encodeURIComponent(
                    longitude
                )}&radius_m=${encodeURIComponent(
                    radiusMeters
                )}`
            ),


    /* ----------------------------------------------------------
       SCENARIOS
       ---------------------------------------------------------- */

    scenarioSummary:
        () =>
            getJson(
                "/api/v1/scenario/summary"
            ),


    scenarioCell:
        cellId =>
            getJson(
                `/api/v1/scenario/${encodeURIComponent(
                    cellId
                )}`
            ),


    scenarioSimulate:
        pct =>
            getJson(
                "/api/v1/scenario/simulate",
                {
                    method:
                        "POST",

                    headers:
                        {
                            "Content-Type":
                                "application/json"
                        },

                    body:
                        JSON.stringify(
                            {
                                rainfall_change_percent:
                                    Number(
                                        pct
                                    )
                            }
                        )
                }
            ),


    /* ----------------------------------------------------------
       LEVEL 41
       SCENARIO → MAP INTELLIGENCE
       ---------------------------------------------------------- */

    scenarioMap:
        rainfallChangePercent =>
            getJson(
                `/api/v1/scenario/map/${encodeURIComponent(
                    Number(
                        rainfallChangePercent
                    )
                )}`
            )
};
