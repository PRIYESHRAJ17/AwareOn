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
                        aria-label="${
                            esc(
                                scenario.pct === 0
                                    ? "Baseline scenario"
                                    : `Rainfall plus ${scenario.pct} percent scenario`
                            )
                        }"
                    >

                        <strong>
                            ${esc(
                                scenario.short
                            )}
                        </strong>

                        <span>
                            ${esc(
                                scenario.pct === 0
                                    ? "Reference conditions"
                                    : scenario.hint
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



function renderCellScenarioContext(payload, pct){
    const record = payload?.scenarios?.find(item => Number(item?.rainfall_change_percent) === Number(pct)) || payload?.scenarios?.[0];
    if(!record) return false;
    const baseline = payload.scenarios.find(item => Number(item?.rainfall_change_percent) === 0) || record;
    const container = document.getElementById("scenario-readout");
    if(!container) return true;
    const rainfall = Number(record.rainfall_change_percent||0);
    const meanRisk = Number(record.risk_score||0);
    const baselineRisk = Number(baseline.risk_score||0);
    const delta = Number(record.risk_score_change||0);
    const transition = `${baseline.risk_category||"—"} → ${record.risk_category||"—"}`;
    container.innerHTML = `<div class="scenario-result"><div class="scenario-result-head"><div><span class="scenario-kicker">SELECTED CELL SCENARIO</span><h3>Cell ${esc(payload.cell_id)}</h3><p>Precomputed cell-level counterfactual for rainfall +${rainfall.toFixed(0)}%.</p></div><span class="scenario-status-badge scenario-positive">${esc(record.risk_category||"SUPPORTED")}</span></div><div class="scenario-primary"><div class="scenario-primary-main"><span>Risk score</span><strong>${n(meanRisk)}</strong><small>selected cell</small></div><div class="scenario-delta-panel scenario-positive"><span>Change from baseline</span><strong>${delta>=0?"+":""}${n(delta)}</strong><small>${esc(transition)}</small></div></div><div class="scenario-metrics-grid"><article class="scenario-metric-card"><span>Rainfall</span><strong>+${rainfall.toFixed(0)}%</strong><small>supported state</small></article><article class="scenario-metric-card"><span>Baseline</span><strong>${n(baselineRisk)}</strong><small>current cell risk</small></article><article class="scenario-metric-card"><span>Category change</span><strong>${Number(record.category_change||0)>0?"Yes":"No"}</strong><small>${esc(transition)}</small></article><article class="scenario-metric-card"><span>Data state</span><strong>PRECOMPUTED</strong><small>no interpolation</small></article></div><div class="scenario-comparison"><div class="scenario-comparison-head"><div><span class="scenario-kicker">CELL RESPONSE</span><strong>Baseline → selected</strong></div><span>${n(baselineRisk)} → ${n(meanRisk)}</span></div><div class="scenario-comparison-track"><div class="scenario-comparison-baseline"><span></span></div><div class="scenario-comparison-current scenario-positive" style="width:${Math.max(4,Math.min(100,meanRisk))}%"><span></span></div></div><div class="scenario-comparison-labels"><span>Baseline ${n(baselineRisk)}</span><span>Selected ${n(meanRisk)}</span></div></div><div class="scenario-decision-card"><div class="scenario-decision-icon">→</div><div><span class="scenario-kicker">DECISION READOUT</span><strong>${esc(record.escalates?"This cell escalates under the selected scenario.":"This cell does not change category under the selected scenario.")}</strong><p>Cell-level scenario analysis is restricted to the supported precomputed states.</p></div></div>${scenarioInsightMarkup({scopeLabel:`Cell ${payload.cell_id}`,rainfall,baselineRisk,selectedRisk:meanRisk,delta,trigger:record.rainfall_trigger_score,triggerCategory:record.trigger_category||"UNCLASSIFIED",escalating:Number(record.escalates||0),newHigh:Number(record.escalates?1:0),newExtreme:Number(record.risk_category==="EXTREME"&&baseline.risk_category!=="EXTREME"?1:0),maxRisk:meanRisk,maxChange:delta,interpretation:record.escalates?"The selected cell moves into a higher category under the tested rainfall state.":"The selected cell remains in the same risk category under the tested rainfall state.",categoryTransition:transition})}</div>`;
    return true;
}

export async function refreshScenarioContext(){
    const cellId = state.selectedCell?.cell_id ? String(state.selectedCell.cell_id) : null;
    const banner = document.getElementById("scenario-context-banner");
    state.scenarioScopeCellId = cellId;
    if(banner) banner.textContent = cellId ? `Selected cell · ${cellId} · supported states: 0%, +25%, +50%, +100% · precomputed counterfactuals` : "Regional scenario scope · supported states: 0%, +25%, +50%, +100% · precomputed/modelled comparison";
    if(!cellId || !state.scenarioSummary) return;
    try{
        const payload = await api.scenarioCell(cellId);
        state.scenarioCellPayload = payload;
        renderCellScenarioContext(payload, Number(state.selectedScenario||0));
    }catch(error){
        if(document.getElementById("scenario-readout")) document.getElementById("scenario-readout").innerHTML = `<div class="scenario-empty-state"><strong>Cell scenario unavailable</strong><p>${esc(error.message||"No supported cell scenario is available.")}</p></div>`;
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

    if (state.selectedCell?.cell_id) {
        try {
            const payload = await api.scenarioCell(String(state.selectedCell.cell_id));
            state.scenarioCellPayload = payload;
            renderCellScenarioContext(payload, pct);
            window.dispatchEvent(new CustomEvent("awareon:scenario", {detail:{pct, result:{supported:true, cell_id:state.selectedCell.cell_id, cell_specific:true}}}));
            return;
        } catch (error) {
            console.warn("Cell scenario unavailable:", error);
        }
    }

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
            <div class="scenario-empty-state">
                <div class="scenario-empty-icon">◌</div>
                <strong>Scenario data unavailable</strong>
                <p>
                    No generated counterfactual is available for this selection.
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


    const rainfallPct =
        Number(
            row.rainfall_change_percent
        ) || 0;


    const baselineRisk =
        Number(
            baseline
                ?.mean_risk_score
        );


    const meanRisk =
        Number(
            row.mean_risk_score
        );


    const meanChange =
        Number(
            row.mean_risk_change
        );


    const calculatedDelta =
        Number.isFinite(
            meanRisk
        ) &&
        Number.isFinite(
            baselineRisk
        )
            ? meanRisk - baselineRisk
            : meanChange;


    const trigger =
        Number(
            row.rainfall_trigger_score
        );


    const maxChange =
        Number(
            row.max_risk_change
        );


    const maxRisk =
        Number(
            row.max_risk_score
        );


    const escalating =
        Number(
            row.escalating_cells
        ) || 0;


    const newHigh =
        Number(
            row.new_high_or_extreme
        ) || 0;


    const newExtreme =
        Number(
            row.new_extreme_cells
        ) || 0;


    const isBaseline =
        rainfallPct === 0;


    const directionClass =
        calculatedDelta > 0
            ? "scenario-positive"
            : calculatedDelta < 0
                ? "scenario-negative"
                : "scenario-neutral";


    const directionLabel =
        calculatedDelta > 0
            ? "Risk increases"
            : calculatedDelta < 0
                ? "Risk decreases"
                : "No mean-risk change";


    const scenarioLabel =
        isBaseline
            ? "Current baseline"
            : `Rainfall +${rainfallPct.toFixed(0)}%`;


    const scenarioName =
        rainfallPct === 0
            ? "Baseline conditions"
            : rainfallPct === 25
                ? "Moderate rainfall shock"
                : rainfallPct === 50
                    ? "Strong rainfall shock"
                    : "Extreme rainfall shock";


    const triggerCategory =
        row.trigger_category
        ||
        "UNCLASSIFIED";


    const transitionText =
        isBaseline
            ? "Reference state"
            : escalating > 0
                ? `${escalating.toLocaleString()} cells escalate`
                : "No category escalation detected";


    const interpretation =
        isBaseline
            ? "This is AwareOn's reference state. Other scenarios are compared against this condition."
            : escalating > 0
                ? `${escalating.toLocaleString()} modelled cells move into a higher risk category under this tested rainfall condition.`
                : "The tested rainfall increase raises the modelled risk surface without producing category transitions.";


    container.innerHTML =
        `
        <div class="scenario-result">

            <div class="scenario-result-head">

                <div>
                    <span class="scenario-kicker">
                        SELECTED COUNTERFACTUAL
                    </span>

                    <h3>
                        ${esc(
                            scenarioLabel
                        )}
                    </h3>

                    <p>
                        ${esc(
                            scenarioName
                        )}
                    </p>
                </div>

                <div class="scenario-status-badge ${directionClass}">
                    <span></span>
                    ${esc(
                        directionLabel
                    )}
                </div>

            </div>


            <div class="scenario-primary">

                <div class="scenario-primary-main">

                    <span>
                        MEAN RISK SCORE
                    </span>

                    <strong>
                        ${n(
                            row.mean_risk_score
                        )}
                    </strong>

                    <small>
                        ${esc(
                            transitionText
                        )}
                    </small>

                </div>


                <div class="scenario-delta-panel ${directionClass}">

                    <span>
                        CHANGE FROM BASELINE
                    </span>

                    <strong>
                        ${
                            calculatedDelta > 0
                                ? "+"
                                : ""
                        }${n(
                            calculatedDelta
                        )}
                    </strong>

                    <small>
                        risk-score points
                    </small>

                </div>

            </div>


            <div class="scenario-metrics-grid">

                <article class="scenario-metric-card">

                    <span>Escalating cells</span>

                    <strong>
                        ${escalating.toLocaleString()}
                    </strong>

                    <small>
                        category transitions
                    </small>

                </article>


                <article class="scenario-metric-card">

                    <span>New HIGH+</span>

                    <strong>
                        ${newHigh.toLocaleString()}
                    </strong>

                    <small>
                        newly elevated cells
                    </small>

                </article>


                <article class="scenario-metric-card">

                    <span>New EXTREME</span>

                    <strong>
                        ${newExtreme.toLocaleString()}
                    </strong>

                    <small>
                        newly extreme cells
                    </small>

                </article>


                <article class="scenario-metric-card">

                    <span>Max risk</span>

                    <strong>
                        ${n(
                            maxRisk
                        )}
                    </strong>

                    <small>
                        highest modelled score
                    </small>

                </article>

            </div>


            <div class="scenario-driver-card">

                <div class="scenario-driver-head">

                    <div>
                        <span class="scenario-kicker">
                            RAINFALL RESPONSE
                        </span>

                        <strong>
                            Trigger signal
                        </strong>
                    </div>

                    <b>
                        ${n(
                            trigger
                        )}
                    </b>

                </div>


                <div class="scenario-trigger-track">

                    <div
                        class="scenario-trigger-fill"
                        style="width:${Math.max(
                            0,
                            Math.min(
                                100,
                                Number.isFinite(
                                    trigger
                                )
                                    ? trigger
                                    : 0
                            )
                        )}%"
                    ></div>

                </div>


                <div class="scenario-driver-meta">

                    <span>
                        ${esc(
                            triggerCategory
                        )}
                    </span>

                    <span>
                        Rainfall +${rainfallPct.toFixed(0)}%
                    </span>

                </div>

            </div>


            <div class="scenario-comparison">

                <div class="scenario-comparison-head">

                    <div>
                        <span class="scenario-kicker">
                            BASELINE COMPARISON
                        </span>

                        <strong>
                            Mean risk trajectory
                        </strong>
                    </div>

                    <span>
                        ${n(
                            baselineRisk
                        )}
                        →
                        ${n(
                            meanRisk
                        )}
                    </span>

                </div>


                <div class="scenario-comparison-track">

                    <div class="scenario-comparison-baseline">
                        <span></span>
                    </div>

                    <div
                        class="scenario-comparison-current ${directionClass}"
                        style="width:${Math.max(
                            4,
                            Math.min(
                                100,
                                Number.isFinite(
                                    meanRisk
                                )
                                    ? meanRisk
                                    : 0
                            )
                        )}%"
                    >
                        <span></span>
                    </div>

                </div>


                <div class="scenario-comparison-labels">

                    <span>
                        Baseline ${n(
                            baselineRisk
                        )}
                    </span>

                    <span>
                        Selected ${n(
                            meanRisk
                        )}
                    </span>

                </div>

            </div>


            <div class="scenario-decision-card">

                <div class="scenario-decision-icon">
                    →
                </div>

                <div>

                    <span class="scenario-kicker">
                        DECISION READOUT
                    </span>

                    <strong>
                        ${esc(
                            transitionText
                        )}
                    </strong>

                    <p>
                        ${esc(
                            interpretation
                        )}
                    </p>

                </div>

            </div>

            ${scenarioInsightMarkup({scopeLabel:"Regional scenario scope",rainfall:rainfallPct,baselineRisk,selectedRisk:meanRisk,delta:calculatedDelta,trigger,triggerCategory,escalating,newHigh,newExtreme,maxRisk,maxChange,interpretation,categoryTransition:transitionText})}

            <div class="scenario-footer">

                <span>
                    Rainfall
                    <b>
                        +${rainfallPct.toFixed(0)}%
                    </b>
                </span>

                <span>
                    Max change
                    <b>
                        ${
                            Number.isFinite(
                                maxChange
                            )
                                ? `${maxChange >= 0 ? "+" : ""}${n(maxChange)}`
                                : "—"
                        }
                    </b>
                </span>

                <span>
                    Data state
                    <b>
                        PRECOMPUTED
                    </b>
                </span>

            </div>

        </div>
        `;
}



/* ============================================================
   RICHER SCENARIO DETAIL SECTIONS
   ============================================================ */

function scenarioInsightMarkup({
    scopeLabel,
    rainfall,
    baselineRisk,
    selectedRisk,
    delta,
    trigger,
    triggerCategory,
    escalating,
    newHigh,
    newExtreme,
    maxRisk,
    maxChange,
    interpretation,
    categoryTransition,
}) {
    const scoreMovement = Number.isFinite(Number(delta))
        ? `${Number(delta) >= 0 ? "+" : ""}${n(delta)}`
        : "—";

    const peakChange = Number.isFinite(Number(maxChange))
        ? `${Number(maxChange) >= 0 ? "+" : ""}${n(maxChange)}`
        : scoreMovement;

    return `
      <div class="scenario-detail-grid16">
        <article class="scenario-detail-card16">
          <span class="scenario-kicker">SCENARIO PROFILE</span>
          <h4>${esc(scopeLabel)}</h4>
          <div class="scenario-detail-list16">
            <div><span>Rainfall state</span><b>+${Number(rainfall || 0).toFixed(0)}%</b></div>
            <div><span>Baseline risk</span><b>${n(baselineRisk)}</b></div>
            <div><span>Selected risk</span><b>${n(selectedRisk)}</b></div>
            <div><span>Mean movement</span><b>${scoreMovement}</b></div>
          </div>
        </article>

        <article class="scenario-detail-card16">
          <span class="scenario-kicker">SPATIAL IMPACT</span>
          <h4>What changes across the modelled surface</h4>
          <div class="scenario-detail-list16">
            <div><span>Escalating cells</span><b>${Number(escalating || 0).toLocaleString()}</b></div>
            <div><span>New HIGH+</span><b>${Number(newHigh || 0).toLocaleString()}</b></div>
            <div><span>New EXTREME</span><b>${Number(newExtreme || 0).toLocaleString()}</b></div>
            <div><span>Peak change</span><b>${peakChange}</b></div>
          </div>
        </article>
      </div>

      <div class="scenario-interpretation16">
        <div class="scenario-interpretation-head16">
          <div>
            <span class="scenario-kicker">HOW TO READ THIS</span>
            <strong>${esc(categoryTransition)}</strong>
          </div>
          <span class="scenario-state-chip16">TRIGGER · ${n(trigger)} · ${esc(triggerCategory)}</span>
        </div>
        <p>${esc(interpretation)}</p>
        <div class="scenario-read-grid16">
          <span><b>1</b> Compare against the baseline.</span>
          <span><b>2</b> Watch category transitions and spatial concentration.</span>
          <span><b>3</b> Treat the result as modelled evidence, not an observed event.</span>
        </div>
      </div>

      <div class="scenario-guardrail16">
        <strong>MODEL STATE</strong>
        <p>This Scenario Lab uses AwareOn's supported precomputed/modelled states. It does not interpolate unsupported rainfall levels and it does not replace current official warnings or field verification.</p>
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
