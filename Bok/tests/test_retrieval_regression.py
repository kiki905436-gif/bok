from __future__ import annotations

import json
import unittest
from pathlib import Path

from bok_core.config import BokConfig
from bok_core.search import VaultSearch
from bok_core.storage import VaultStorage


class RealRetrievalRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vault = Path(__file__).resolve().parents[2] / "Bok-Desktop" / "starter-vault"
        fixture_path = Path(__file__).parent / "fixtures" / "retrieval-regression.json"
        cls.fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        config = BokConfig(
            vault_root=cls.vault,
            provider="none",
            embedding_provider="none",
            port=0,
            personal_core_root="",
        )
        cls.search = VaultSearch(config, VaultStorage(config))

    def test_real_queries_keep_expected_sources_ahead_of_navigation_noise(self) -> None:
        reciprocal_ranks = []
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                result = self.search.search(case["query"], limit=6, semantic=False)
                self.assertTrue(result["results"], f"{case['id']} returned no result")
                paths = [item["path"] for item in result["results"]]
                expected = case["expected_top1"]
                self.assertEqual(paths[0], expected, f"{case['id']} ranked {paths[:3]}")
                rank = paths.index(expected) + 1 if expected in paths else 0
                reciprocal_ranks.append(1.0 / rank if rank else 0.0)
                if case.get("expected_heading_top1"):
                    self.assertEqual(result["results"][0]["heading"], case["expected_heading_top1"])
                forbidden_k = int(case.get("forbidden_k", 6))
                forbidden = set(case.get("forbidden_paths_top_k", []))
                self.assertFalse(forbidden.intersection(paths[:forbidden_k]), f"{case['id']} returned navigation noise: {paths[:forbidden_k]}")
                self.assertEqual(result["semantic"]["status"], "not_requested")
        self.assertEqual(sum(reciprocal_ranks) / len(reciprocal_ranks), 1.0)


if __name__ == "__main__":
    unittest.main()
