# dummy_database.py
# Dummy user profiles keyed by user_id
user_profiles_db = {
    "01765061401": {
        "username": "Rahim",
        "type": "Prepaid",                # Prepaid or Postpaid
        "roaming_status": "active",       # active / inactive
        "country_supported": "singapore",      # whether Singapore roaming is supported
        "restrictions": []                # list of restrictions like ['outgoing_barred']
    },
    "01765061402": {
        "username": "Karim",
        "type": "Postpaid",
        "roaming_status": "inactive",
        "country_supported": "singapore",
        "restrictions": []
    },
    "01765061403": {
        "username": "Selina",
        "type": "Prepaid",
        "roaming_status": "inactive",
        "country_supported": "singapore",
        "restrictions": []
    },
    "01765061404": {
        "username": "Fahim",
        "type": "Postpaid",
        "roaming_status": "inactive",
        "country_supported": "singapore",
        "restrictions": ["outgoing_barred"]
    },
    "01765061405": {
        "username": "Zahid",
        "type": "Postpaid",
        "roaming_status": "inactive",
        "country_supported": "nepal",
        # "restrictions": ["outgoing_barred"]
        "restrictions": []
    },
    "01765061406": {
        "username": "Nahid",
        "type": "Postpaid",
        "roaming_status": "active",
        "country_supported": "nepal",
        # "restrictions": ["outgoing_barred"]
        "restrictions": []
    }
    
}

roaming_packages_db = [
    {
        "package_id": 1,
        "country": "Singapore",
        "region": "Asia",
        "price_BDT": 499,
        "validity_days": 1,
        "data_limit_MB": 500,
        "voice_minutes": 30,
        "sms_limit": 20,
        "recommended_for": "daily",
        "description": "Best for short business or leisure trips with moderate usage."
    },
    {
        "package_id": 2,
        "country": "Singapore",
        "region": "Asia",
        "price_BDT": 1499,
        "validity_days": 7,
        "data_limit_MB": 3000,
        "voice_minutes": 100,
        "sms_limit": 50,
        "recommended_for": "weekly",
        "description": "Ideal for weekly travelers who need both data and calls."
    },
    {
        "package_id": 3,
        "country": "Singapore",
        "region": "Asia",
        "price_BDT": 3999,
        "validity_days": 30,
        "data_limit_MB": 10000,
        "voice_minutes": 500,
        "sms_limit": 200,
        "recommended_for": "monthly",
        "description": "Perfect for frequent travelers or long-term stays abroad."
    },
    {
        "package_id": 4,
        "country": "Malaysia",
        "region": "Asia",
        "price_BDT": 450,
        "validity_days": 1,
        "data_limit_MB": 500,
        "voice_minutes": 25,
        "sms_limit": 20,
        "recommended_for": "daily",
        "description": "Suitable for short trips or transit stays."
    },
    {
        "package_id": 5,
        "country": "Nepal",
        "region": "Asia",
        "price_BDT": 999,
        "validity_days": 7,
        "data_limit_MB": 2500,
        "voice_minutes": 80,
        "sms_limit": 40,
        "recommended_for": "weekly",
        "description": "Budget-friendly pack for regional travelers."
    }
]


user_usage_history_db = {
    "01765061401": {
        "recent_destinations": ["India", "Malaysia"],
        "previous_roaming_packs": [
            {"country": "India", "data_used_MB": 800, "validity_days": 7},
            {"country": "Malaysia", "data_used_MB": 450, "validity_days": 1}
        ],
        "avg_monthly_data_usage_MB": 3200,
        "avg_call_minutes": 180,
        "preferred_pack_type": "daily"
    },
    "01765061402": {
        "recent_destinations": [],
        "previous_roaming_packs": [],
        "avg_monthly_data_usage_MB": 2100,
        "avg_call_minutes": 90,
        "preferred_pack_type": "weekly"
    },
    "01765061403": {
        "recent_destinations": ["Thailand"],
        "previous_roaming_packs": [
            {"country": "Thailand", "data_used_MB": 600, "validity_days": 7}
        ],
        "avg_monthly_data_usage_MB": 2500,
        "avg_call_minutes": 100,
        "preferred_pack_type": "weekly"
    },
    "01765061404": {
        "recent_destinations": ["UAE"],
        "previous_roaming_packs": [
            {"country": "UAE", "data_used_MB": 1200, "validity_days": 10}
        ],
        "avg_monthly_data_usage_MB": 4000,
        "avg_call_minutes": 240,
        "preferred_pack_type": "monthly"
    }
}

