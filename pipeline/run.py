"""
Smile of the Day — バッチ実行エントリーポイント

使い方:
    python pipeline/run.py           # 通常実行（cron から呼ぶ）
    python pipeline/run.py --once    # 1回だけ実行して終了（手動テスト用）
"""

import sys
import logging
from pathlib import Path

# ログ設定
LOG_PATH = Path(__file__).parent.parent / "data" / "run.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def run_batch():
    """Flickr 収集 → 笑顔検出 → DB保存 を1サイクル実行する"""
    from pipeline.collect import fetch_candidates
    from pipeline.detect import analyze_smile
    from pipeline.store import init_db, save_photo, count_photos

    logger.info("=== バッチ開始 ===")
    init_db()

    candidates = fetch_candidates()
    logger.info(f"Flickr候補: {len(candidates)} 件")

    saved = 0
    skipped_dup = 0
    skipped_no_smile = 0

    for photo in candidates:
        result = analyze_smile(photo)
        if result is None:
            skipped_no_smile += 1
            continue

        if save_photo(result):
            saved += 1
            logger.info(
                f"  保存: {result['flickr_id']} "
                f"happy={result['emotion_happy_prob']:.2f} "
                f"({result['lat']:.2f}, {result['lon']:.2f})"
            )
        else:
            skipped_dup += 1

    total = count_photos()
    logger.info(
        f"=== バッチ完了 === "
        f"保存:{saved} / 重複スキップ:{skipped_dup} / 笑顔なしスキップ:{skipped_no_smile} "
        f"/ DB合計:{total} 件"
    )


if __name__ == "__main__":
    run_batch()
