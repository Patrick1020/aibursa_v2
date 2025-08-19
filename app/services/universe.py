from __future__ import annotations
import csv, os, random
from datetime import datetime, timezone
from typing import List, Dict
from functools import lru_cache

from app.core.config import settings

def _norm(t: str) -> str:
    return t.strip().upper()

@lru_cache(maxsize=1)
def _fixed_list() -> List[str]:
    if not settings.universe_fixed:
        return []
    return [_norm(x) for x in settings.universe_fixed.split(",") if x.strip()]

@lru_cache(maxsize=1)
def _pool_list() -> List[str]:
    path = settings.universe_random_pool_path
    if not path or not os.path.exists(path):
        return []
    out: List[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        # Acceptăm fie header 'ticker', fie fișier cu o singură coloană fără header
        if "ticker" in (r.fieldnames or []):
            for row in r:
                if row.get("ticker"):
                    out.append(_norm(row["ticker"]))
        else:
            f.seek(0)
            for line in f:
                if line.strip():
                    out.append(_norm(line))
    # Unic & ordonat
    seen = set(); uniq = []
    for t in out:
        if t not in seen:
            seen.add(t); uniq.append(t)
    return uniq

def _today_seed(dt: datetime | None = None) -> int:
    if settings.universe_random_seed is not None:
        return int(settings.universe_random_seed)
    if dt is None:
        dt = datetime.now(timezone.utc)
    return int(dt.strftime("%Y%m%d"))

def daily_random(count: int | None = None, dt: datetime | None = None) -> List[str]:
    pool = _pool_list()
    if not pool:
        return []
    base_seed = _today_seed(dt)
    rng = random.Random(base_seed)
    # Excludem din pool tickerele fixe, ca să nu se dubleze
    fixed = set(_fixed_list())
    candidates = [t for t in pool if t not in fixed]
    if count is None:
        count = max(0, int(settings.universe_random_daily_count))
    if count <= 0:
        return []
    if count >= len(candidates):
        return candidates
    # Tragere fără înlocuire, deterministă pe zi
    return rng.sample(candidates, count)

def today_universe(dt: datetime | None = None) -> Dict[str, List[str]]:
    fixed = _fixed_list()
    rnd = daily_random(dt=dt)
    # combinat, unic, păstrăm ordinea: mai întâi fixe, apoi random
    all_list: List[str] = []
    seen = set()
    for t in list(fixed) + list(rnd):
        if t not in seen:
            seen.add(t); all_list.append(t)
    return {"fixed": fixed, "random": rnd, "all": all_list, "date_seed": _today_seed(dt)}
