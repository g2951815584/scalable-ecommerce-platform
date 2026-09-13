from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCRIPT_PATH = ROOT / "backend" / "scripts" / "generate_secrets.py"


def _load_secret_script():
    spec = importlib.util.spec_from_file_location("generate_secrets", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_env_example_uses_shared_hs256_fallback_by_default():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "JWT_PRIVATE_KEY=" in content
    assert "JWT_PUBLIC_KEY=" in content
    assert "JWT_PUBLIC_KEY=replace-with-jwt-public-key" not in content
    assert "JWT_PUBLIC_KEY=\n" in content


def test_upsert_env_writes_generated_jwt_key_pair(tmp_path: Path):
    module = _load_secret_script()
    env_path = tmp_path / ".env"
    env_path.write_text("INTERNAL_TOKEN=old-token\n", encoding="utf-8")

    module.upsert_env(
        "new-token",
        private_pem="-----BEGIN PRIVATE KEY-----\nprivate\n-----END PRIVATE KEY-----\n",
        public_pem="-----BEGIN PUBLIC KEY-----\npublic\n-----END PUBLIC KEY-----\n",
        env_path=env_path,
    )

    content = env_path.read_text(encoding="utf-8")
    assert "INTERNAL_TOKEN=new-token" in content
    assert 'JWT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nprivate\\n-----END PRIVATE KEY-----\\n"' in content
    assert 'JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\\npublic\\n-----END PUBLIC KEY-----\\n"' in content
