from pathlib import Path

import pandas as pd


# repository.py
# AwareOn/
#   backend/app/services/repository.py
#
# parents[0] -> services
# parents[1] -> app
# parents[2] -> backend
# parents[3] -> AwareOn
#
# Therefore project root is parents[3].

ROOT = Path(__file__).resolve().parents[3]

INTELLIGENCE_DIR = (
    ROOT / "data" / "processed" / "intelligence"
)


class DataRepository:

    def __init__(
        self,
        data_dir: Path = INTELLIGENCE_DIR,
    ):
        self.data_dir = Path(data_dir)

    def load_csv(
        self,
        filename: str,
    ) -> pd.DataFrame:

        path = self.data_dir / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Data file not found: {path}"
            )

        return pd.read_csv(path)

    def find_cell(
        self,
        filename: str,
        cell_id: str,
    ) -> dict | None:

        df = self.load_csv(filename)

        matches = df[
            df["cell_id"].astype(str)
            == str(cell_id)
        ]

        if matches.empty:
            return None

        return matches.iloc[0].to_dict()


repository = DataRepository()
