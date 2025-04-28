import json
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import matplotlib.pyplot as plt


class DataAnalyzer:
    REQUIRED_COLS = {
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "next_action",
        "current_cash",
        "current_position",
    }

    def __init__(self, csv_path: str | Path, *, encoding: str = "utf-8") -> None:
        self.csv_path = Path(csv_path).expanduser()
        self.df = self._load_data(encoding)
        self._prepare()

    # ------------------------------------------------------------------ #
    # I/O helpers
    # ------------------------------------------------------------------ #
    def _load_data(self, encoding: str) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise FileNotFoundError(self.csv_path)
        df = pd.read_csv(self.csv_path, encoding=encoding)
        missing = self.REQUIRED_COLS.difference(df.columns)
        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)} in {self.csv_path}"
            )
        return df

    # ------------------------------------------------------------------ #
    # Pre‑processing
    # ------------------------------------------------------------------ #
    def _prepare(self) -> None:
        self.df["datetime"] = pd.to_datetime(self.df["datetime"], utc=False)
        self.df.sort_values("datetime", inplace=True, ignore_index=True)

        # Convenience labels
        self.df["action_label"] = (
            self.df["next_action"]
            .map({1: "BUY", 0: "HOLD", -1: "SELL"})
            .astype("category")
        )

        # Account equity in quote currency
        self.df["total_asset_value"] = (
            self.df["current_cash"] + self.df["current_position"] * self.df["close"]
        )

    # ------------------------------------------------------------------ #
    # Descriptive statistics
    # ------------------------------------------------------------------ #
    def summary(self) -> Dict[str, object]:
        d0, d1 = self.df["datetime"].iloc[[0, -1]]
        return {
            "period": {"from": str(d0), "to": str(d1)},
            "n_rows": len(self.df),
            "action_counts": self.df["action_label"].value_counts().to_dict(),
            "cash": self.df["current_cash"].describe().to_dict(),
            "position": self.df["current_position"].describe().to_dict(),
            "equity": self.df["total_asset_value"].describe().to_dict(),
        }

    # ------------------------------------------------------------------ #
    # Performance metrics
    # ------------------------------------------------------------------ #
    def performance_metrics(
        self,
        *,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 365,
    ) -> Dict[str, float]:
        """Compute core KPIs: Return, MDD, Win‑rate, Sharpe.

        Parameters
        ----------
        risk_free_rate : float, default 0.0
            Annualised risk‑free rate expressed in decimal form.
        periods_per_year : int, default 365
            Scaling factor for Sharpe ratio (daily → annual).
        """
        equity = self.df["total_asset_value"]

        # 1. Final return (percentage)
        ret_pct = (equity.iloc[-1] / equity.iloc[0] - 1) * 100.0

        # 2. Maximum draw‑down (% negative number)
        running_max = equity.cummax()
        drawdowns = (equity - running_max) / running_max
        mdd_pct = drawdowns.min() * 100.0  # negative value

        # 3. Win‑rate over completed BUY→SELL cycles
        wins = trades = 0
        entry_price: Optional[float] = None
        for row in self.df.itertuples(index=False):
            if row.next_action == 1 and entry_price is None:  # 최초 매수 시
                entry_price = row.open
            elif row.next_action == -1 and entry_price is not None:
                trades += 1
                wins += int(row.open > entry_price)  # strict greater‑than only
                entry_price = None
        win_rate = round(wins / trades * 100, 2) if trades else 0

        # 4. Daily Sharpe ratio (excess return / std * sqrt(T))
        daily_ret = equity.pct_change().dropna()
        excess = daily_ret - risk_free_rate / periods_per_year
        sharpe = (
            (excess.mean() / excess.std()) * (periods_per_year**0.5)
            if excess.std() != 0.0
            else float("nan")
        )

        return {
            "return_pct": ret_pct,
            "mdd": mdd_pct,
            "win_rate": win_rate,
            "total_trades": trades,
            "sharpe_index": sharpe,
        }

    # ------------------------------------------------------------------ #
    # Visualisation
    # ------------------------------------------------------------------ #
    def plot_price(
        self,
        *,
        with_actions: bool = True,
        figsize: tuple[int, int] = (12, 5),
        marker_size: int = 80,
    ) -> None:
        plt.figure(figsize=figsize)
        plt.plot(self.df["datetime"], self.df["close"], label="Close")
        if with_actions:
            for label, marker in {"BUY": "^", "SELL": "v", "HOLD": "o"}.items():
                subset = self.df[self.df["action_label"] == label]
                plt.scatter(
                    subset["datetime"],
                    subset["close"],
                    marker=marker,
                    s=marker_size,
                    label=label,
                    alpha=0.8,
                )
        plt.xlabel("DateTime")
        plt.ylabel("Price")
        plt.title("Close Price & Proposed Actions")
        plt.tight_layout()
        plt.legend()
        plt.show()


if __name__ == "__main__":  # pragma: no cover
    ana = DataAnalyzer(
        "/home/tako/Documents/yonghan/Crypto-Trading/data/bull_market_with_4o_records.csv"
    )
    print(json.dumps(ana.performance_metrics(), indent=2, ensure_ascii=False))

    ana.plot_price()
