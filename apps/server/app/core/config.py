import os
from functools import lru_cache
from pathlib import Path

DEFAULT_DATA_DIR = r"E:\PaperLens\data"


class Settings:
    def __init__(self) -> None:
        # 本机定制：无 D 盘且禁止写入 C 盘，数据目录固定为 E:\PaperLens\data；
        # PAPERLENS_DATA_DIR 环境变量仍可显式覆盖。
        raw = os.environ.get("PAPERLENS_DATA_DIR") or DEFAULT_DATA_DIR
        self.data_dir = Path(raw)
        # 模型写目录固定为数据目录 models/；PAPERLENS_MODELS_DIR 仅作内置只读模型目录（随安装包分发）
        self.models_dir = self.data_dir / "models"
        models_env = os.environ.get("PAPERLENS_MODELS_DIR")
        self.bundled_models_dir = Path(models_env) if models_env else None
        ecdict_env = os.environ.get("PAPERLENS_ECDICT_PATH")
        self.bundled_ecdict_path = Path(ecdict_env) if ecdict_env else None
        self.skip_migrate = os.environ.get("PAPERLENS_SKIP_MIGRATE") == "1"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "paperlens.db"

    @property
    def ecdict_path(self) -> Path:
        return self.data_dir / "ecdict.db"

    @property
    def files_dir(self) -> Path:
        return self.data_dir / "files"

    @property
    def ocr_dir(self) -> Path:
        return self.data_dir / "ocr"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.models_dir, self.files_dir, self.ocr_dir, self.backups_dir):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
