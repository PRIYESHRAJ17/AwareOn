# Level 20 — Final E2E QA

Run the backend first, then the frontend.

## Automated endpoint checks

The helper at `scripts/level20_e2e.py` checks health, risk, regional intelligence, scenario intelligence, and out-of-domain behavior.

```bash
python scripts/level20_e2e.py
```

## Browser acceptance checklist

- [ ] Command Center loads without console errors.
- [ ] Risk map loads and is interactive.
- [ ] Zoomed-out risk cells aggregate into readable clusters with counts.
- [ ] Clicking a cluster zooms smoothly.
- [ ] Clicking an individual risk cell opens a quick popup.
- [ ] Popup can open deep cell intelligence.
- [ ] Incident markers remain interactive.
- [ ] History and exposure layers remain selectable.
- [ ] Search locates a known cell/incident.
- [ ] Intelligence shows AO thinking animation while waiting.
- [ ] Thinking animation disappears when the response arrives.
- [ ] Intelligence response can show evidence metadata.
- [ ] Conversational summary works in the same browser session.
- [ ] Scenario Lab loads and changes map context.
- [ ] Drawer can collapse and restore the map-first canvas.
- [ ] No permanent bottom status bar consumes the map.
- [ ] Typography is readable at normal desktop scale.
- [ ] Responsive behavior remains usable below 900px.

Levels 21–22 remain outside this package scope.
