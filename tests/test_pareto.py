from backend.app.pareto import dominates, fast_sort, optimize_sites

def test_dominance():
    assert dominates([0,0,0],[1,1,1])
    assert not dominates([0,2],[1,1])

def test_pareto_keeps_tradeoffs():
    candidates=[
      {"id":"sunny","sunlight_pct":95,"communication_pct":60,"slope_deg":8},
      {"id":"comms","sunlight_pct":65,"communication_pct":95,"slope_deg":4},
      {"id":"balanced","sunlight_pct":80,"communication_pct":80,"slope_deg":5},
      {"id":"bad","sunlight_pct":50,"communication_pct":40,"slope_deg":20},
    ]
    result=optimize_sites(candidates,population_size=30,generations=10)
    ids={x['id'] for x in result['pareto_front']}
    assert 'bad' not in ids
    assert len(ids)>=2
