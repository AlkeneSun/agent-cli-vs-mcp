import requests
import json
import os

AMAP_KEY = os.environ.get("AMAP_KEY", "YOUR_AMAP_KEY_HERE")
BASE_URL = "https://restapi.amap.com/v3/place/text"

def search_poi(keywords: str, city: str = "", offset: int = 3, force_error: str = ""):
    """
    Search POI from Amap. 
    force_error: Mock parameter for Error Recovery testing.
    """
    if force_error:
        # Mock amap error
        return {
            "status": "0",
            "info": "INVALID_USER_PARAMETER",
            "infocode": "10001",
            "mocked_reason": force_error
        }

    params = {
        "key": AMAP_KEY,
        "keywords": keywords,
        "city": city,
        "offset": offset,
        "page": 1, 
        "extensions": "base"
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        if data.get("status") == "1":
            pois = data.get("pois", [])
            result = []
            for poi in pois:
                result.append({
                    "name": poi.get("name"),
                    "type": poi.get("type", ""),
                    "address": str(poi.get("address", "")), # Force cast to string for safety
                    "location": poi.get("location", "")
                })
            return {"status": "success", "info": "OK", "data": result}
        else:
            return {"status": "error", "info": data.get("info", "Unknown error")}
    except Exception as e:
        return {"status": "error", "info": str(e)}

if __name__ == "__main__":
    print(search_poi("星巴克", "北京", 2))
