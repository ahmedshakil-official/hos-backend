from projectile.settings import VERSATILEIMAGEFIELD_RENDITION_KEY_SETS

geo_location_schema = {
    "type": "object",
    "properties": {
        "reverseGeoCode": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "name": {"type": "string"},
                "region": {"type": "string"},
                "street": {"type": "string"},
                "country": {"type": "string"},
                "district": {"type": "string"},
                "timezone": {"type": ["string", "number", "null"]},
                "subregion": {"type": "string"},
                "postalCode": {"type": ["string", "number", "null"]},
                "streetNumber": {"type": ["string", "number", "null"]},
                "isoCountryCode": {"type": ["string", "number", "null"]},
            },
            "additionalProperties": False,
        },
        "currentPosition": {
            "type": "object",
            "properties": {
                "speed": {"type": ["number", "null"]},
                "heading": {"type": ["number", "null"]},
                "accuracy": {"type": ["number", "null"]},
                "altitude": {"type": ["number", "null"]},
                "latitude": {"type": ["number", "null"]},
                "longitude": {"type": ["number", "null"]},
                "altitudeAccuracy": {"type": ["number", "null"]},
            },
            "required": [
                "speed",
                "heading",
                "accuracy",
                "altitude",
                "latitude",
                "longitude",
            ],
            "additionalProperties": False,
        },
    },
    "required": ["currentPosition"],
    "additionalProperties": False,
}


validate_product_image = {
        "type": "object",
        "properties": {
            key: {"type": "string", "format": "uri"} for key, _ in VERSATILEIMAGEFIELD_RENDITION_KEY_SETS.get('product_images', [])
        },
        "required": [key for key, _ in VERSATILEIMAGEFIELD_RENDITION_KEY_SETS.get('product_images', [])]
}
