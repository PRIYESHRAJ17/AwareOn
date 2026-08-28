from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

GT_DIR = ROOT / "data/processed/ground_truth"

POS = GT_DIR / "positive_cells.csv"
NEG = GT_DIR / "negative_cells.csv"

TRAIN = GT_DIR / "ground_truth_train.csv"
VAL = GT_DIR / "ground_truth_validation.csv"
TEST = GT_DIR / "ground_truth_test.csv"

EVENTS = GT_DIR / "dated_landslide_events.csv"


def load(path):
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


positive = load(POS)
negative = load(NEG)
train = load(TRAIN)
validation = load(VAL)
test = load(TEST)
events = load(EVENTS)


# ------------------------------------------------------------
# Basic validation
# ------------------------------------------------------------

assert len(positive) > 0
assert len(negative) > 0

assert set(positive["label"].unique()) == {1}
assert set(negative["label"].unique()) == {0}

assert set(train["label"].unique()) <= {0, 1}
assert set(validation["label"].unique()) <= {0, 1}
assert set(test["label"].unique()) <= {0, 1}


# ------------------------------------------------------------
# Check duplicate cell IDs across splits
# ------------------------------------------------------------

train_ids = set(train["cell_id"])
val_ids = set(validation["cell_id"])
test_ids = set(test["cell_id"])

train_val_overlap = train_ids & val_ids
train_test_overlap = train_ids & test_ids
val_test_overlap = val_ids & test_ids

assert not train_val_overlap
assert not train_test_overlap
assert not val_test_overlap


# ------------------------------------------------------------
# Check expected balance
# ------------------------------------------------------------

assert len(positive) == len(negative)


# ------------------------------------------------------------
# Event checks
# ------------------------------------------------------------

assert len(events) > 0
assert events["event_date"].notna().all()


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print("\n========================================")
print("GROUND-TRUTH VALIDATION")
print("========================================")

print(f"Positive cells:       {len(positive)}")
print(f"Negative cells:       {len(negative)}")
print(f"Total static samples: {len(positive) + len(negative)}")

print("\nSpatial split:")
print(
    f"Train:       {len(train)} "
    f"(positive={int(train['label'].sum())}, "
    f"negative={int((train['label'] == 0).sum())})"
)

print(
    f"Validation:  {len(validation)} "
    f"(positive={int(validation['label'].sum())}, "
    f"negative={int((validation['label'] == 0).sum())})"
)

print(
    f"Test:        {len(test)} "
    f"(positive={int(test['label'].sum())}, "
    f"negative={int((test['label'] == 0).sum())})"
)

print("\nSplit overlaps:")
print("Train ∩ Validation:", len(train_val_overlap))
print("Train ∩ Test:", len(train_test_overlap))
print("Validation ∩ Test:", len(val_test_overlap))

print("\nDated events:")
print("Events:", len(events))
print("Date range:", events["event_date"].min(), "to", events["event_date"].max())

print("\nVALIDATION PASSED ✅")
