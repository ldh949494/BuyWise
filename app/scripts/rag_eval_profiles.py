"""RAG eval profile metadata."""

from __future__ import annotations

import csv
from pathlib import Path

from app.scripts.seed_products import ANDROID_CONTRACT_PRODUCTS, DEMO_PROFILE_PRODUCTS

RAG_EVAL_DIR = Path(__file__).resolve().parents[2] / "data" / "rag_eval"
PROFILE_DATASETS = {
    "android-contract": RAG_EVAL_DIR / "shopping_needs.jsonl",
    "demo": RAG_EVAL_DIR / "demo_shopping_needs.jsonl",
    "beta-fixture": RAG_EVAL_DIR / "beta_shopping_needs.jsonl",
}
PROFILE_PRODUCT_FIXTURES = {
    "beta-fixture": RAG_EVAL_DIR / "beta_products.csv",
}
DEFAULT_PROFILE = "android-contract"
DEFAULT_DATASET_PATH = PROFILE_DATASETS[DEFAULT_PROFILE]
PROFILE_ERROR = "profile must be 'android-contract', 'demo', or 'beta-fixture'."


def dataset_path_for_profile(profile: str) -> Path:
    try:
        return PROFILE_DATASETS[profile]
    except KeyError as exc:
        raise ValueError(PROFILE_ERROR) from exc


def known_seed_product_ids(profile: str = DEFAULT_PROFILE) -> set[int]:
    if profile == "android-contract":
        return {int(product["id"]) for product in ANDROID_CONTRACT_PRODUCTS}
    if profile == "demo":
        return {int(product["id"]) for product in DEMO_PROFILE_PRODUCTS}
    if profile == "beta-fixture":
        return _known_fixture_product_ids(PROFILE_PRODUCT_FIXTURES[profile])
    raise ValueError(PROFILE_ERROR)


def _known_fixture_product_ids(path: Path) -> set[int]:
    with path.open(encoding="utf-8", newline="") as file:
        return {int(row["id"]) for row in csv.DictReader(file)}
