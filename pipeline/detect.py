"""DeepFace で笑顔スコア（emotion_happy_prob）を計算する"""

import os
import requests
import logging
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
HAPPY_THRESHOLD = 0.6  # このスコア未満はスキップ

logger = logging.getLogger(__name__)


def _download_image(url: str, dest: Path) -> bool:
    """画像を一時ファイルにダウンロードする"""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return True
    except Exception as e:
        logger.warning(f"画像DL失敗: {url} — {e}")
        return False


def analyze_smile(photo: dict) -> dict | None:
    """
    写真の笑顔スコアを計算して photo に emotion_happy_prob を追加して返す。
    スキップ条件（顔未検出 / スコア閾値未満）の場合は None を返す。

    Args:
        photo: collect.py が返す dict（flickr_id, url_medium, ... を含む）

    Returns:
        emotion_happy_prob が追加された dict、またはスキップ時 None
    """
    # deepface は重いので実行時にインポート（初回のみモデルDL発生）
    from deepface import DeepFace

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = CACHE_DIR / f"{photo['flickr_id']}.jpg"

    try:
        if not _download_image(photo["url_medium"], tmp_path):
            return None

        results = DeepFace.analyze(
            img_path=str(tmp_path),
            actions=["emotion"],
            detector_backend="mtcnn",   # 精度重視
            enforce_detection=True,     # 顔が無ければ例外 → スキップ
            silent=True,
        )

        # 複数顔が検出された場合は最初の顔を使用
        happy_score = results[0]["emotion"]["happy"] / 100.0

        if happy_score < HAPPY_THRESHOLD:
            return None

        return {**photo, "emotion_happy_prob": round(happy_score, 4)}

    except Exception as e:
        logger.debug(f"検出スキップ ({photo['flickr_id']}): {e}")
        return None

    finally:
        # 一時ファイルを削除
        if tmp_path.exists():
            tmp_path.unlink()
