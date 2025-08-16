from dataclasses import dataclass
from typing import Literal

@dataclass
class PredictionResult:
    expected_change_pct: float
    probability_pct: float
    outcome: Literal["win", "loss", "breakeven"]
    reward_to_risk: float
    rationale: str

class PredictionEngine:
    """
    Stub determinist pentru bootstrap.
    Înlocuiești cu logica reală (știri, Alpha Vantage, context istoric + GPT).
    """

    def predict(self, ticker: str, horizon_days: int) -> PredictionResult:
        # Heuristică simplă: doar ca să verificăm cap-coadă (AI → DB → UI).
        base = sum(ord(c) for c in ticker.upper()) % 10
        expected = round((base - 5) / 2.0, 2)  # -2.5 .. +2.5
        prob = 60 + (base % 3) * 10            # 60/70/80
        outcome = "win" if expected > 0 else ("loss" if expected < 0 else "breakeven")
        rr = round(abs(expected) / 1.2 + 1.0, 2)
        rationale = f"Bootstrap stub: ticker={ticker}, horizon={horizon_days}. Verificare lanț end-to-end."
        return PredictionResult(
            expected_change_pct=expected,
            probability_pct=float(prob),
            outcome=outcome,
            reward_to_risk=rr,
            rationale=rationale,
        )
