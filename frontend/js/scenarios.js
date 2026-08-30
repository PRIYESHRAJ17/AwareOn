import { api } from "./api.js";
import { state } from "./state.js";


/* ============================================================
   AWAREON SCENARIO LAB
   LEVEL 42 — SCENARIO → MAP INTEGRATION
   ============================================================ */


const n = (
    value,
    decimals = 2
) => {

    const number =
        Number(value);

    return Number.isFinite(number)
        ? number.toFixed(decimals)
        : "—";
};


const esc = (
    value
) => {

    return String(
        value ?? ""
    )
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
};


const scenarios = [
    {
        pct: 0,
        name: "BASELINE",
        short: "0%",
        hint: "Current conditions"
    },

    {
        pct: 25,
        name: "RAINFALL_PLUS_25_PERCENT",
        short: "+25%",
        hint: "Moderate shock"
    },

    {
        pct: 50,
        name: "RAINFALL_PLUS_50_PERCENT",
        short: "+50%",
        hint: "Strong shock"
    },

    {
        pct: 100,
        name: "RAINFALL_PLUS_100_PERCENT",
        short: "+100%",
        hint: "Extreme shock"
    }
];


let activeRequest = null;

let scenarioMapRequest = null;


/* ============================================================
   SCENARIO MAP VISUAL STATE
   ============================================================ */

const originalStyles =
    new WeakMap();


function rememberOriginalStyle(
    layer
) {

    if (
        !layer ||
        originalStyles.has(layer)
    ) {

        return;
    }


    const options =
        layer.options
        ||
        {};


    originalStyles.set(
        layer,
        {
            color:
                options.color,

            weight:
                options.weight,

            opacity:
                options.opacity,

            fillColor:
                options.fillColor,

            fillOpacity:
                options.fillOpacity,

            dashArray:
                options.dashArray
        }
    );
}


function restoreLayerStyle(
    layer
) {

    const original =
        originalStyles.get(
            layer
        );


    if (
        !original
    ) {

        return;
    }


    layer.setStyle(
        original
    );
}


/* ============================================================
   CLEAR SCENARIO MAP
   ============================================================ */

function clearScenarioMapHighlight() {

    const riskLayer =
        state.riskLayer;


    if (
        !riskLayer
    ) {

        return;
    }


    riskLayer.eachLayer(
        layer => {

            restoreLayerStyle(
                layer
            );

        }
    );


    state.scenarioHighlightedCells =
        [];


    state.scenarioMapData =
        null;


    window.dispatchEvent(
        new CustomEvent(
            "awareon:scenario-map-cleared"
        )
    );
}


/* ============================================================
   APPLY SCENARIO TO MAP
   ============================================================ */

function applyScenarioMap(
    mapData
) {

    const riskLayer =
        state.riskLayer;


    if (
        !riskLayer
    ) {

        console.warn(
            "AwareOn risk layer is not ready for scenario highlighting."
        );

        /*
         * Keep the data so the next map interaction can
         * retry without another API request.
         */

        state.scenarioMapData =
            mapData;


        return;
    }


    const cells =
        mapData.cells
        ||
        [];


    const cellLookup =
        new Map();


    for (
        const cell
        of cells
    ) {

        const id =
            String(
                cell?.cell_id
                ??
                ""
            );


        if (
            id
        ) {

            cellLookup.set(
                id,
                cell
            );
        }
    }


    const highlighted = [];


    /*
     * First restore every risk cell.
     */

    riskLayer.eachLayer(
        layer => {

            restoreLayerStyle(
                layer
            );
        }
    );


    /*
     * Highlight only cells that actually
     * change category.
     */

    riskLayer.eachLayer(
        layer => {

            const cellId =
                String(
                    layer
                        ?.feature
                        ?.properties
                        ?.cell_id
                    ??
                    ""
                );


            const scenarioCell =
                cellLookup.get(
                    cellId
                );


            if (
                !scenarioCell
            ) {

                return;
            }


            rememberOriginalStyle(
                layer
            );


            if (
                scenarioCell.category_change
                >
                0
            ) {

                layer.setStyle(
                    {
                        color:
                            "#0f172a",

                        weight:
                            2.8,

                        opacity:
                            1,

                        fillColor:
                            "#f59e0b",

                        fillOpacity:
                            0.78,

                        dashArray:
                            "5 3"
                    }
                );


                highlighted.push(
                    {
                        layer,
                        data:
                            scenarioCell
                    }
                );

            } else if (
                scenarioCell.risk_change
                >=
                5
            ) {

                layer.setStyle(
                    {
                        color:
                            "#334155",

                        weight:
                            2,

                        opacity:
                            0.9,

                        fillColor:
                            "#fbbf24",

                        fillOpacity:
                            0.42,

                        dashArray:
                            "4 4"
                    }
                );

            }
        }
    );


    state.scenarioHighlightedCells =
        highlighted;


    state.scenarioMapData =
        mapData;


    /*
     * Bring the affected cells above the regular
     * risk-cell rendering.
     */

    for (
        const item
        of highlighted
    ) {

        if (
            typeof item.layer.bringToFront
            ===
            "function"
        ) {

            item.layer.bringToFront();
        }
    }


    window.dispatchEvent(
        new CustomEvent(
            "awareon:scenario-map-applied",
            {
                detail:
                    {
                        mapData,
                        highlighted
                    }
            }
        )
    );


    console.log(
        "AwareOn scenario map applied:",
        {
            scenario:
                mapData.scenario,

            cells:
                mapData.cell_count,

            escalating:
                mapData.escalating_cells,

            highlighted:
                highlighted.length
        }
    );
}


/* ============================================================
   LOAD SCENARIO MAP
   ============================================================ */

async function loadScenarioMap(
    pct
) {

    if (
        scenarioMapRequest
    ) {

        scenarioMapRequest =
            null;
    }


    const request =
        api.scenarioMap(
            pct
        );


    scenarioMapRequest =
        request;


    try {

        const mapData =
            await request;


        if (
            scenarioMapRequest !==
            request
        ) {

            return null;
        }


        if (
            !mapData.supported
        ) {

            throw new Error(
                "Scenario map is not supported for this rainfall level."
            );
        }


        applyScenarioMap(
            mapData
        );


        return mapData;

    } finally {

        if (
            scenarioMapRequest ===
            request
        ) {

            scenarioMapRequest =
                null;
        }
    }
}


/* ============================================================
   INITIALIZE
   ============================================================ */

export async function initScenarios() {

    state.scenarioHighlightedCells =
        [];

    state.scenarioMapData =
        null;


    const summary =
        await api.scenarioSummary();


    state.scenarioSummary =
        summary;


    const container =
        document.getElementById(
            "scenario-options"
        );


    if (
        !container
    ) {

        return;
    }


    container.innerHTML =
        scenarios
            .map(
                scenario =>
                    `
                    <button
                        class="scenario-option"
                        type="button"
                        data-pct="${
                            scenario.pct
                        }"
                    >

                        <strong>
                            ${esc(
                                scenario.short
                            )}
                        </strong>

                        <span>
                            ${esc(
                                scenario.hint
                            )}
                        </span>

                    </button>
                    `
            )
            .join("");


    container
        .querySelectorAll(
            ".scenario-option"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        selectScenario(
                            Number(
                                button.dataset.pct
                            )
                        );
                    }
                );
            }
        );


    /*
     * Baseline is rendered from the existing summary.
     *
     * No simulation POST and no scenario-map request
     * are required for baseline startup.
     */

    state.selectedScenario =
        0;


    markSelectedScenario(
        0
    );


    const baseline =
        summary
            ?.scenarios
            ?.find(
                item =>
                    Number(
                        item
                            ?.rainfall_change_percent
                    ) === 0
            );


    render(
        baseline
    );


    /*
     * Load baseline map state once the risk layer exists.
     */

    if (
        state.riskLayer
    ) {

        try {

            await loadScenarioMap(
                0
            );

        } catch (
            error
        ) {

            console.warn(
                "Baseline scenario map unavailable:",
                error
            );
        }
    }
}


/* ============================================================
   SELECT SCENARIO
   ============================================================ */

async function selectScenario(
    pct
) {

    state.selectedScenario =
        pct;


    markSelectedScenario(
        pct
    );


    const row =
        state
            .scenarioSummary
            ?.scenarios
            ?.find(
                scenario =>
                    Number(
                        scenario
                            ?.rainfall_change_percent
                    ) === pct
            );


    render(
        row
    );


    /*
     * 1. Load spatial scenario intelligence.
     *
     * This is the Level 42 connection.
     */

    try {

        await loadScenarioMap(
            pct
        );

    } catch (
        error
    ) {

        console.error(
            "Scenario map failed:",
            error
        );


        window.dispatchEvent(
            new CustomEvent(
                "awareon:scenario-map-error",
                {
                    detail:
                        {
                            pct,
                            error
                        }
                }
            )
        );
    }


    /*
     * 2. For non-baseline scenarios, also request
     * the simulation result so the existing Scenario
     * result event continues to work.
     */

    if (
        pct === 0
    ) {

        window.dispatchEvent(
            new CustomEvent(
                "awareon:scenario",
                {
                    detail:
                        {
                            pct,
                            row,
                            result:
                                {
                                    supported:
                                        true,

                                    scenario:
                                        "BASELINE",

                                    rainfall_change_percent:
                                        0,

                                    records:
                                        []
                                }
                        }
                }
            )
        );


        return;
    }


    if (
        activeRequest
    ) {

        activeRequest =
            null;
    }


    const request =
        api.scenarioSimulate(
            pct
        );


    activeRequest =
        request;


    try {

        const result =
            await request;


        if (
            activeRequest !==
            request
        ) {

            return;
        }


        state.scenarioRecords =
            result.records ||
            [];


        window.dispatchEvent(
            new CustomEvent(
                "awareon:scenario",
                {
                    detail:
                        {
                            pct,
                            row,
                            result
                        }
                }
            )
        );

    } catch (
        error
    ) {

        if (
            activeRequest !==
            request
        ) {

            return;
        }


        window.dispatchEvent(
            new CustomEvent(
                "awareon:scenario",
                {
                    detail:
                        {
                            pct,
                            row,
                            result:
                                null,
                            error
                        }
                }
            )
        );

    } finally {

        if (
            activeRequest ===
            request
        ) {

            activeRequest =
                null;
        }
    }
}


/* ============================================================
   SELECTED BUTTON
   ============================================================ */

function markSelectedScenario(
    pct
) {

    document
        .querySelectorAll(
            ".scenario-option"
        )
        .forEach(
            button => {

                button.classList.toggle(
                    "active",
                    Number(
                        button.dataset.pct
                    ) === pct
                );
            }
        );
}


/* ============================================================
   SCENARIO READOUT
   ============================================================ */

function render(
    row
) {

    const container =
        document.getElementById(
            "scenario-readout"
        );


    if (
        !container
    ) {

        return;
    }


    if (
        !row
    ) {

        container.innerHTML =
            `
            <div class="assessment empty">

                <div class="empty-symbol">
                    ◌
                </div>

                <p>
                    No scenario data.
                </p>

            </div>
            `;


        return;
    }


    const baseline =
        state
            .scenarioSummary
            ?.scenarios
            ?.find(
                item =>
                    Number(
                        item
                            ?.rainfall_change_percent
                    ) === 0
            );


    const delta =
        Number(
            row.mean_risk_score
        )
        -
        Number(
            baseline
                ?.mean_risk_score
            ||
            0
        );


    container.innerHTML =
        `
        <div
            class="section-title-row"
        >

            <div>

                <span class="eyebrow">
                    SCENARIO OUTCOME
                </span>

                <h2>
                    ${esc(
                        row.scenario
                    )}
                </h2>

            </div>

            <span class="state-chip">
                ${esc(
                    row.trigger_category
                    ||
                    "SCENARIO"
                )}
            </span>

        </div>


        <div
            class="scenario-grid"
        >

            <div
                class="scenario-stat"
            >

                <span>
                    Mean risk
                </span>

                <strong>
                    ${n(
                        row.mean_risk_score
                    )}
                </strong>

                <em>
                    ${Number(
                        row.mean_risk_change
                        ||
                        0
                    ) === 0
                        ? "Baseline"
                        : "from baseline"
                    }
                </em>

            </div>


            <div
                class="scenario-stat"
            >

                <span>
                    Mean change
                </span>

                <strong
                    class="${
                        delta > 0
                            ? "delta-up"
                            : "delta-flat"
                    }"
                >

                    ${
                        delta >= 0
                            ? "+"
                            : ""
                    }${n(
                        delta
                    )}

                </strong>

                <em>
                    vs baseline
                </em>

            </div>


            <div
                class="scenario-stat"
            >

                <span>
                    Escalating cells
                </span>

                <strong>
                    ${row.escalating_cells ?? "—"}
                </strong>

                <em>
                    category transitions
                </em>

            </div>


            <div
                class="scenario-stat"
            >

                <span>
                    New HIGH+
                </span>

                <strong>
                    ${row.new_high_or_extreme ?? "—"}
                </strong>

                <em>
                    newly elevated cells
                </em>

            </div>


            <div
                class="scenario-stat"
            >

                <span>
                    New EXTREME
                </span>

                <strong>
                    ${row.new_extreme_cells ?? "—"}
                </strong>

                <em>
                    newly extreme cells
                </em>

            </div>


            <div
                class="scenario-stat"
            >

                <span>
                    Trigger
                </span>

                <strong>
                    ${n(
                        row.rainfall_trigger_score
                    )}
                </strong>

                <em>
                    ${esc(
                        row.trigger_category
                        ||
                        "UNKNOWN"
                    )}
                </em>

            </div>

        </div>


        <div
            class="scenario-footer"
        >

            <span>
                Rainfall change
                <b>
                    ${Number(
                        row.rainfall_change_percent
                    ).toFixed(0)}%
                </b>
            </span>

            <span>
                Max change
                <b>
                    +${n(
                        row.max_risk_change
                    )}
                </b>
            </span>

        </div>
        `;
}


/* ============================================================
   PUBLIC DEBUG HELPER
   ============================================================ */

window.awareonScenarioDebug =
    () => {

        return {
            selectedScenario:
                state.selectedScenario,

            mapData:
                state.scenarioMapData,

            highlightedCells:
                state
                    .scenarioHighlightedCells
                    ?.length
                ||
                0,

            riskLayerReady:
                Boolean(
                    state.riskLayer
                )
        };
    };
