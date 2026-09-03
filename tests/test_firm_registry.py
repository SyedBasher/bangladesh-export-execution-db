from pathlib import Path
from beod.firm_registry import load_seed_registry, build_firm_capability_features


def test_seed_registry():
    root=Path(__file__).resolve().parents[1]
    firms,links=load_seed_registry(root/'data/seed')
    f=build_firm_capability_features(firms,links)
    assert len(firms)==28
    assert len(links)==104
    assert len(f)==28
    assert set(links['link_confidence'])=={'A'}
