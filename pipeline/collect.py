"""Flickr API から笑顔写真候補を収集する"""

import os
import flickrapi
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["FLICKR_API_KEY"]
SECRET  = os.environ["FLICKR_SECRET"]

# CCライセンスホワイトリスト（NC/ND系は除外）
# 4=CC BY, 5=CC BY-SA, 6=CC BY-ND, 9=CC0, 10=PDM
ALLOWED_LICENSES = "4,5,6,9,10"

SEARCH_TAGS = "smile,happy,笑顔"


def fetch_candidates(per_page: int = 250) -> list[dict]:
    """
    Flickr API でジオタグ付き笑顔写真を検索し、候補リストを返す。

    Returns:
        list of dict with keys:
            flickr_id, photo_page_url, url_medium, lat, lon,
            geo_accuracy, license_id, taken_date
    """
    flickr = flickrapi.FlickrAPI(API_KEY, SECRET, format="parsed-json")

    result = flickr.photos.search(
        tags=SEARCH_TAGS,
        tag_mode="any",
        has_geo=1,
        license=ALLOWED_LICENSES,
        content_type=1,          # 写真のみ（スクリーンショット・イラスト除外）
        safe_search=1,           # Safe コンテンツのみ
        extras="geo,url_m,date_taken,license,accuracy",
        per_page=per_page,
        page=1,
        sort="date-posted-desc",
    )

    photos = result.get("photos", {}).get("photo", [])
    candidates = []

    for p in photos:
        url_medium = p.get("url_m")
        lat = p.get("latitude")
        lon = p.get("longitude")

        # ジオタグが無効な写真はスキップ
        if not url_medium or not lat or not lon:
            continue
        if float(lat) == 0.0 and float(lon) == 0.0:
            continue

        candidates.append({
            "flickr_id":      p["id"],
            "photo_page_url": f"https://www.flickr.com/photos/{p['owner']}/{p['id']}",
            "url_medium":     url_medium,
            "lat":            float(lat),
            "lon":            float(lon),
            "geo_accuracy":   int(p.get("accuracy", 0)),
            "license_id":     int(p.get("license", 0)),
            "taken_date":     p.get("datetaken", "")[:10],  # YYYY-MM-DD
        })

    return candidates
