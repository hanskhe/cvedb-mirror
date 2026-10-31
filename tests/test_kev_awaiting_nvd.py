"""KEV entries that CISA lists before NVD publishes them.

This gap broke the deploy pipeline on 2026-10-13: the entry was dropped from
by_year_published and from the CVSS page's KEV count, so the totals no longer
reconciled. It is a normal state for a day or so after a KEV addition.
"""

from __future__ import annotations

import json
from pathlib import Path

from data.scoring_analysis import ScoringAnalyzer


def _analyzer(tmp_path: Path, nvd_ids: list[str], kev_ids: list[str]) -> ScoringAnalyzer:
    cache = tmp_path / "cache"
    out = tmp_path / "out"
    cache.mkdir()
    out.mkdir()
    nvd = [{"cve": {"id": cid, "published": "2026-10-01T00:00:00.000"}} for cid in nvd_ids]
    (cache / "nvd.json").write_text(json.dumps(nvd))
    kev = {
        "catalogVersion": "test",
        "vulnerabilities": [
            {"cveID": cid, "vendorProject": "V", "product": "P", "dateAdded": "2026-10-13"} for cid in kev_ids
        ],
    }
    (cache / "known_exploited_vulnerabilities.json").write_text(json.dumps(kev))
    return ScoringAnalyzer(base_dir=tmp_path, cache_dir=cache, output_dir=out)


def test_kev_entry_missing_from_nvd_is_reported_not_dropped(tmp_path):
    analyzer = _analyzer(tmp_path, nvd_ids=["CVE-2026-0001"], kev_ids=["CVE-2026-0001", "CVE-2026-0002"])

    k = analyzer.generate_kev_analysis()

    assert k["total_kev_cves"] == 2
    assert k["by_year_published"] == {"2026": 1}
    assert k["awaiting_nvd"] == {"count": 1, "cve_ids": ["CVE-2026-0002"]}
    assert sum(k["by_year_published"].values()) + k["awaiting_nvd"]["count"] == k["total_kev_cves"]


def test_awaiting_nvd_is_empty_when_nvd_has_every_entry(tmp_path):
    analyzer = _analyzer(tmp_path, nvd_ids=["CVE-2026-0001"], kev_ids=["CVE-2026-0001"])

    k = analyzer.generate_kev_analysis()

    assert k["awaiting_nvd"] == {"count": 0, "cve_ids": []}
