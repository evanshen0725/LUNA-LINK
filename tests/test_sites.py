from backend.app.sites import SITES

def test_site_ids_are_unique():
    ids = [site["id"] for site in SITES]
    assert len(ids) == len(set(ids))

def test_sites_are_marked_as_south_pole_candidates():
    assert len(SITES) >= 3
    assert all(site["lat"] < -80 for site in SITES)
