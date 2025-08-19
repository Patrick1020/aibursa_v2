from __future__ import annotations
from typing import Optional
import numpy as np
from joblib import dump, load

from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression

# În sklearn >= 1.6 există FrozenEstimator; pe versiuni mai vechi facem fallback.
try:
    from sklearn.frozen import FrozenEstimator  # scikit-learn ≥ 1.6
    HAS_FROZEN = True
except Exception:
    FrozenEstimator = None  # type: ignore
    HAS_FROZEN = False

class PlattPrefit:
    """
    Calibrator simplu (Platt) pentru estimator *deja antrenat*.
    Se potrivește logistică pe proba brută (prefit estimator) -> proba calibrată.
    """
    def __init__(self):
        self._lr = LogisticRegression(solver="lbfgs")

    def fit(self, probs_valid: np.ndarray, y_valid: np.ndarray):
        p = np.asarray(probs_valid).reshape(-1, 1)
        y = np.asarray(y_valid).astype(int)
        self._lr.fit(p, y)
        return self

    def predict_proba(self, probs_raw: np.ndarray) -> np.ndarray:
        p = np.asarray(probs_raw).reshape(-1, 1)
        return self._lr.predict_proba(p)[:, 1]

    def save(self, path: str): dump(self._lr, path)
    @classmethod
    def load(cls, path: str):
        obj = cls()
        obj._lr = load(path)
        return obj

def calibrate_prefit_estimator(estimator, X_valid, y_valid, method: str = "sigmoid"):
    """
    Returnează un calibrator apt pentru estimator *deja antrenat*.
    - Dacă sklearn >=1.6: folosește CalibratedClassifierCV(FrozenEstimator(estimator)), fără cv='prefit'.
    - Altfel: folosește PlattPrefit (logistică) pe proba brută.
    """
    if HAS_FROZEN:
        # Atenție: X_valid, y_valid trebuie să fie DISJUNCTE față de datele de train ale estimatorului!
        calib = CalibratedClassifierCV(estimator=FrozenEstimator(estimator), method=method)
        calib.fit(X_valid, y_valid)
        return calib
    else:
        # Fallback robust pentru sklearn < 1.6 (fără FrozenEstimator)
        probs_valid = estimator.predict_proba(X_valid)[:, 1]
        cal = PlattPrefit().fit(probs_valid, y_valid)
        return cal  # acesta expune predict_proba(probs_raw), nu pe X!
