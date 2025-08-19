from __future__ import annotations
from typing import List, Dict
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.universe import today_universe, _pool_list, _fixed_list

router = APIRouter(prefix="/api/universe", tags=["universe"])

class UniverseResponse(BaseModel):
    date_seed: int
    fixed: List[str]
    random: List[str]
    all: List[str] = Field(description="fixed + random (unique, in this order)")

@router.get("/today", response_model=UniverseResponse)
def get_today_universe():
    return today_universe()

class PoolStats(BaseModel):
    pool_size: int
    fixed_size: int
    overlap: int

@router.get("/pool/stats", response_model=PoolStats)
def pool_stats():
    pool = set(_pool_list())
    fixed = set(_fixed_list())
    return {"pool_size": len(pool), "fixed_size": len(fixed), "overlap": len(pool & fixed)}
