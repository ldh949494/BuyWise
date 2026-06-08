from __future__ import annotations

import json

from app.scripts import repair_product_image_acls as acl_script
from app.scripts.repair_product_image_acls import RepairAclSummary, repair_product_image_acls


def test_repair_product_image_acls_dry_run_collects_cos_product_keys(tmp_path, monkeypatch) -> None:
    csv_path = tmp_path / "products.csv"
    csv_path.write_text(
        "\n".join(
            [
                "sku,image_url,image_urls",
                (
                    "demo,"
                    "https://bucket.cos.ap-shanghai.myqcloud.com/product-images/demo/main.jpg,"
                    "\"[\"\"https://bucket.cos.ap-shanghai.myqcloud.com/product-images/demo/main.jpg\"\"]\""
                ),
                (
                    "external,"
                    "https://cdn.example-real.test/images/main.jpg,"
                    "\"[\"\"https://cdn.example-real.test/images/main.jpg\"\"]\""
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(acl_script.settings, "cos_bucket", "bucket")
    monkeypatch.setattr(acl_script.settings, "cos_region", "ap-shanghai")

    summary = repair_product_image_acls(
        csv_paths=[csv_path],
        include_seed_profiles=False,
        dry_run=True,
        client=None,
    )

    assert summary.as_dict() == {
        "urls_seen": 2,
        "keys_seen": 1,
        "keys_repaired": 0,
        "keys_skipped": 1,
        "keys_failed": 0,
    }


def test_repair_product_image_acls_apply_sets_public_read(tmp_path, monkeypatch) -> None:
    csv_path = tmp_path / "products.csv"
    csv_path.write_text(
        "\n".join(
            [
                "sku,image_url,image_urls",
                (
                    "demo,"
                    "https://bucket.cos.ap-shanghai.myqcloud.com/product-images/demo/main.jpg,"
                    "\"[\"\"https://bucket.cos.ap-shanghai.myqcloud.com/product-images/demo/main.jpg\"\"]\""
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(acl_script.settings, "cos_bucket", "bucket")
    monkeypatch.setattr(acl_script.settings, "cos_region", "ap-shanghai")

    class FakeClient:
        def __init__(self) -> None:
            self.calls = []

        def put_object_acl(self, **kwargs):
            self.calls.append(kwargs)

    fake_client = FakeClient()
    summary = repair_product_image_acls(
        csv_paths=[csv_path],
        include_seed_profiles=False,
        dry_run=False,
        client=fake_client,
    )

    assert summary.keys_repaired == 1
    assert fake_client.calls == [
        {"Bucket": "bucket", "Key": "product-images/demo/main.jpg", "ACL": "public-read"}
    ]


def test_repair_product_image_acls_cli_writes_job_artifact(tmp_path, monkeypatch) -> None:
    artifact = tmp_path / "acl-repair.json"
    summary = RepairAclSummary(urls_seen=2, keys_seen=1, keys_skipped=1)
    calls = []

    def fake_repair_product_image_acls(*, csv_paths, include_seed_profiles, dry_run):
        calls.append(
            {
                "csv_paths": csv_paths,
                "include_seed_profiles": include_seed_profiles,
                "dry_run": dry_run,
            }
        )
        return summary

    monkeypatch.setattr(acl_script, "repair_product_image_acls", fake_repair_product_image_acls)
    monkeypatch.setattr(
        "sys.argv",
        [
            "repair_product_image_acls",
            "--csv",
            "data/products.csv",
            "--skip-seed-profiles",
            "--artifact-json",
            str(artifact),
        ],
    )

    acl_script.main()

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert calls == [
        {
            "csv_paths": ["data/products.csv"],
            "include_seed_profiles": False,
            "dry_run": True,
        }
    ]
    assert payload["job_name"] == "repair_product_image_acls"
    assert payload["status"] == "succeeded"
    assert payload["inputs"] == {
        "csv": ["data/products.csv"],
        "include_seed_profiles": False,
        "apply": False,
    }
    assert payload["output"] == summary.as_dict()
