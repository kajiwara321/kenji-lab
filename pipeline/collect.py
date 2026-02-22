"""Flickr API から笑顔写真候補を収集する"""

import os
from datetime import datetime, timedelta

import flickrapi
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["FLICKR_API_KEY"]
SECRET  = os.environ["FLICKR_SECRET"]

# 人物写真を広く取得し、笑顔かどうかは DeepFace に委ねる
SEARCH_TAGS = "portrait,people,person,family"

# 都市名（text検索）と代表座標（ジオタグなし写真のフォールバック）
# Flickr Places API が廃止済みのため text= 検索 + 座標フォールバックで代替
CITIES = {
    "Tokyo":       (35.68,  139.69),
    "Paris":       (48.86,    2.35),
    "New York":    (40.71,  -74.01),
    "London":      (51.51,   -0.13),
    "Berlin":      (52.52,   13.40),
    "Sao Paulo":   (-23.55, -46.63),
    "Delhi":       (28.61,   77.21),
    "Beijing":     (39.91,  116.39),
    "Sydney":      (-33.87, 151.21),
    "Seoul":       (37.57,  126.98),
    "Rome":        (41.90,   12.48),
    "Madrid":      (40.42,   -3.70),
    "Toronto":     (43.65,  -79.38),
    "Bangkok":     (13.75,  100.52),
    "Jakarta":     (-6.21,  106.85),
    "Mexico City": (19.43,  -99.13),
    "Cairo":       (30.04,   31.24),
    "Lagos":       (6.52,    3.38),
    "Istanbul":    (41.01,   28.97),
    "Buenos Aires":(-34.60, -58.38),
}


def fetch_candidates(per_city: int = 30, days: int = 30) -> list[dict]:
    """
    都市名テキスト検索で人物写真を取得し、候補リストを返す。
    ジオタグの有無に関わらず取得し、ない場合は都市の代表座標を使う。

    Args:
        per_city: 都市ごとの取得件数（デフォルト30）
        days: 過去何日分を取得するか（デフォルト30日）

    Returns:
        list of dict with keys:
            flickr_id, photo_page_url, url_medium, lat, lon,
            geo_accuracy, license_id, taken_date
    """
    flickr = flickrapi.FlickrAPI(API_KEY, SECRET, format="parsed-json")
    min_date = int((datetime.now() - timedelta(days=days)).timestamp())

    candidates = []

    for city_name, (default_lat, default_lon) in CITIES.items():
        result = flickr.photos.search(
            text=city_name,
            tags=SEARCH_TAGS,
            tag_mode="any",
            content_type=1,   # 写真のみ
            safe_search=1,    # Safe コンテンツのみ
            extras="geo,url_m,date_taken,license,accuracy",
            per_page=per_city,
            page=1,
            sort="date-posted-desc",
            min_upload_date=min_date,
        )

        photos = result.get("photos", {}).get("photo", [])

        for p in photos:
            url_medium = p.get("url_m")
            if not url_medium:
                continue

            # 実ジオタグがあればそれを使い、なければ都市の代表座標
            raw_lat = p.get("latitude")
            raw_lon = p.get("longitude")
            if raw_lat and raw_lon and float(raw_lat) != 0.0 and float(raw_lon) != 0.0:
                lat = float(raw_lat)
                lon = float(raw_lon)
                accuracy = int(p.get("accuracy", 0))
            else:
                lat = default_lat
                lon = default_lon
                accuracy = 0  # 都市レベル精度

            candidates.append({
                "flickr_id":      p["id"],
                "photo_page_url": f"https://www.flickr.com/photos/{p['owner']}/{p['id']}",
                "url_medium":     url_medium,
                "lat":            lat,
                "lon":            lon,
                "geo_accuracy":   accuracy,
                "license_id":     int(p.get("license", 0)),
                "taken_date":     p.get("datetaken", "")[:10],
            })

    return candidates
