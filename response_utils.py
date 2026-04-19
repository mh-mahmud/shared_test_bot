# response_utils.py
# Idiomatic mapping for 0..99 (common Bengali words)
_0_to_99 = {
    0: "শূন্য", 1: "এক", 2: "দুই", 3: "তিন", 4: "চার", 5: "পাঁচ", 6: "ছয়", 7: "সাত", 8: "আট", 9: "নয়",
    10: "দশ", 11: "এগারো", 12: "বারো", 13: "তেরো", 14: "চৌদ্দ", 15: "পনেরো", 16: "ষোল", 17: "সতেরো", 18: "আঠারো", 19: "উনিশ",
    20: "কুড়ি", 21: "একুশ", 22: "বাইশ", 23: "তেইশ", 24: "চব্বিশ", 25: "পঁচিশ", 26: "ছাব্বিশ", 27: "সাতাশ", 28: "আটাশ", 29: "ঊনত্রিশ",
    30: "ত্রিশ", 31: "একত্রিশ", 32: "বত্রিশ", 33: "তেত্রিশ", 34: "চৌত্রিশ", 35: "পঁয়ত্রিশ", 36: "ছত্রিশ", 37: "সাইত্রিশ", 38: "আটত্রিশ", 39: "উনচল্লিশ",
    40: "চল্লিশ", 41: "একচল্লিশ", 42: "বিয়াল্লিশ", 43: "তেতাল্লিশ", 44: "চুয়াল্লিশ", 45: "পঁয়তাল্লিশ", 46: "ছেচল্লিশ", 47: "সাতচল্লিশ", 48: "আটচল্লিশ", 49: "ঊনপঞ্চাশ",
    50: "পঞ্চাশ", 51: "একান্ন", 52: "বায়ান্ন", 53: "তেপ্পান্ন", 54: "চুয়ান্ন", 55: "পঞ্চান্ন", 56: "ছাপ্পান্ন", 57: "সাতান্ন", 58: "আটান্ন", 59: "উনষাট",
    60: "ষাট", 61: "একষট্টি", 62: "বাষট্টি", 63: "তেষট্টি", 64: "চৌষট্টি", 65: "পঁয়ষট্টি", 66: "ছেষট্টি", 67: "সাতষট্টি", 68: "আটষট্টি", 69: "ঊনসত্তর",
    70: "সত্তর", 71: "একাত্তর", 72: "বাহাত্তর", 73: "তেহাত্তর", 74: "চুয়াত্তর", 75: "পচাত্তর", 76: "ছিয়াত্তর", 77: "সাতাত্তর", 78: "আটাত্তর", 79: "ঊনআশি",
    80: "আশি", 81: "একাশি", 82: "বিরাশি", 83: "তিরাশি", 84: "চুরাশি", 85: "পচাশি", 86: "ছিয়াশি", 87: "সাতাশি", 88: "আটাশি", 89: "ঊননব্বই",
    90: "নব্বই", 91: "একানব্বই", 92: "বিরানব্বই", 93: "তিরানব্বই", 94: "চুরানব্বই", 95: "পঁচানব্বই", 96: "ছিয়ানব্বই", 97: "সাতানব্বই", 98: "আটানব্বই", 99: "নিরানব্বই"
}

def int_to_bangla_words(n: int) -> str:
    """
    Convert integer n >= 0 to Bangla words (idiomatic for 0..99).
    Supports values up to at least hundreds of crores by recursive grouping.
    """
    if n < 0:
        raise ValueError("Negative numbers not supported")
    if n < 100:
        return _0_to_99[n]

    parts = []

    # crore (কোটি) = 10**7 in Indian numbering grouping
    crore = 10**7
    lakh = 10**5
    thousand = 10**3
    hundred = 100

    if n >= crore:
        top = n // crore
        parts.append(int_to_bangla_words(top) + " কোটি")
        n = n % crore

    if n >= lakh:
        top = n // lakh
        parts.append(int_to_bangla_words(top) + " লক্ষ")
        n = n % lakh

    if n >= thousand:
        top = n // thousand
        parts.append(int_to_bangla_words(top) + " হাজার")
        n = n % thousand

    if n >= hundred:
        top = n // hundred
        # for hundreds we often say "পাঁচ শত" or "এক শত"
        parts.append(int_to_bangla_words(top) + " শত")
        n = n % hundred

    if n > 0:
        parts.append(int_to_bangla_words(n))

    return " ".join(parts)

def get_bangla_username(username):
    if username == "Rahim":
        bangla_username = "রহিম"
    elif username == "Karim":
        bangla_username = "করিম"
    elif username == "Selina":
        bangla_username = "সেলিনা"
    elif username == "Fahim":
        bangla_username = "ফাহিম"
    elif username == "Zahid":
        bangla_username = "জাহিদ"
    elif username == "Nahid":
        bangla_username = "নাহিদ"
    else:
        bangla_username = "গ্রাহক"
    return bangla_username

def get_bangla_country_name(requested_country):
    if requested_country.lower() == "singapore":
        bangla_country_name = "সিঙ্গাপুরের"
    elif requested_country.lower() == "nepal":
        bangla_country_name = "নেপালের"
    elif requested_country.lower() == "malaysia":
        bangla_country_name = "মালয়েশিয়ার"
    elif requested_country.lower() == "bhutan":
        bangla_country_name = "ভুটানের"
    else:
        bangla_country_name = "কাঙ্ক্ষিত দেশের"
    return bangla_country_name

def get_bangla_package_info(recommended_package):
    bn_package_info = {}
    
    bn_package_info["price_BDT_in_bn"] = int_to_bangla_words(recommended_package['price_BDT'])
    bn_package_info["validity_days_in_bn"] = int_to_bangla_words(recommended_package['validity_days'])
    bn_package_info["data_limit_MB_in_bn"] = int_to_bangla_words(recommended_package['data_limit_MB'])
    bn_package_info["voice_minutes_in_bn"] = int_to_bangla_words(recommended_package['voice_minutes'])
    bn_package_info["sms_limit_in_bn"] = int_to_bangla_words(recommended_package['sms_limit'])

    return bn_package_info

COUNTRY_NAME_MAP = {
    "singapore": "সিঙ্গাপুর",
    "nepal": "নেপাল",
    "bhutan": "ভুটান",
    "malaysia": "মালয়েশিয়া",
}

def get_valid_country_text(valid_countries):
    valid_country_text = ""
    for country in valid_countries:
        valid_country_text += f", {COUNTRY_NAME_MAP[country]}"
    return valid_country_text
