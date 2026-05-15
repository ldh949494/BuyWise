from app.core.config import Settings


def test_settings_reads_new_env_names() -> None:
    import os

    env = {
        "APP_NAME": "BuyWise",
        "APP_ENV": "prod",
        "APP_PORT": "9000",
        "MYSQL_HOST": "db.example.com",
        "MYSQL_PORT": "3307",
        "MYSQL_USER": "buyer",
        "MYSQL_PASSWORD": "secret",
        "MYSQL_DATABASE": "buywise",
        "CHROMA_PERSIST_DIR": "/var/lib/chroma",
        "CHROMA_PRODUCT_COLLECTION": "products_prod",
        "LLM_BASE_URL": "https://llm.example.com/v1",
        "LLM_API_KEY": "key-123",
        "LLM_MODEL": "gpt-4.1-mini",
        "EMBEDDING_MODEL": "text-embedding-3-large",
        "TENCENT_SECRET_ID": "sid",
        "TENCENT_SECRET_KEY": "skey",
        "COS_BUCKET": "bucket",
        "COS_REGION": "ap-shanghai",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        settings = Settings(_env_file=None)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert settings.app_name == "BuyWise"
    assert settings.app_env == "prod"
    assert settings.app_port == 9000
    assert settings.mysql_host == "db.example.com"
    assert settings.mysql_port == 3307
    assert settings.mysql_user == "buyer"
    assert settings.mysql_password == "secret"
    assert settings.mysql_database == "buywise"
    assert settings.chroma_persist_dir == "/var/lib/chroma"
    assert settings.chroma_persist_directory == "/var/lib/chroma"
    assert settings.chroma_product_collection == "products_prod"
    assert settings.llm_base_url == "https://llm.example.com/v1"
    assert settings.llm_api_key == "key-123"
    assert settings.llm_model == "gpt-4.1-mini"
    assert settings.embedding_model == "text-embedding-3-large"
    assert settings.tencent_secret_id == "sid"
    assert settings.tencent_secret_key == "skey"
    assert settings.cos_bucket == "bucket"
    assert settings.cos_region == "ap-shanghai"


def test_settings_database_url_uses_pymysql() -> None:
    import os

    env = {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "root",
        "MYSQL_DATABASE": "buywise",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        settings = Settings(_env_file=None)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert settings.database_url == "mysql+pymysql://root:root@localhost:3306/buywise"


def test_settings_accepts_supported_app_env_values() -> None:
    import os

    previous = os.environ.get("APP_ENV")
    try:
        for app_env in ("dev", "test", "prod"):
            os.environ["APP_ENV"] = app_env
            assert Settings(_env_file=None).app_env == app_env
    finally:
        if previous is None:
            os.environ.pop("APP_ENV", None)
        else:
            os.environ["APP_ENV"] = previous


def test_settings_keeps_legacy_chroma_directory_alias() -> None:
    import os

    previous = os.environ.get("CHROMA_PERSIST_DIRECTORY")
    os.environ["CHROMA_PERSIST_DIRECTORY"] = "/tmp/legacy-chroma"
    try:
        settings = Settings(_env_file=None)
    finally:
        if previous is None:
            os.environ.pop("CHROMA_PERSIST_DIRECTORY", None)
        else:
            os.environ["CHROMA_PERSIST_DIRECTORY"] = previous

    assert settings.chroma_persist_dir == "/tmp/legacy-chroma"
