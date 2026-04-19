# utils.py
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

from dummy_database import user_profiles_db, roaming_packages_db, user_usage_history_db

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def create_session(user_id, sessions):
    user_profile = get_user_profile(user_id)
    if user_profile is None:
        print("Invalid User.")
        return False
    print(user_profile)

    sessions[user_id] = {
        # available states -> "awaiting_intent", "awaiting_country", "awaiting_package_consent", "awaiting_roaming_consent"
        "is_new_conversation": True,
        "state": "awaiting_intent", 
        "intent_retries": 0,
        "country_retries": 0,
        "consent_retries": 0,
        # "messages": messages,
        "user_profile": user_profile,
        "requested_country": None,
        "intent_detected": None,
        "recommended_package_ids": []
    }

    return sessions[user_id]

def call_structured_output_llm(messages, MAX_RETRIES=3):
    for retry in range(MAX_RETRIES):
        # call llm
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        assistant_response = response.choices[0].message.content

        try:
            parsed = json.loads(assistant_response)
            return parsed
        except:
            print(f"trial {retry+1} failed.")
    return False

def detect_user_intent(user_input):
    """
        Detects user intent and returns in following json format:
        {
            "intent": <string>, # available intents "user_greet", "activate_roaming", "user_confirm", "user_deny", "thank_you", "agent_transfer".
            "confidence": <int between 0 and 100>
        }
    """
    INTENT_SYSTEM_PROMPT = """
        You are a Grameenphone Roaming Activation Assistant for the 121 Hotline.  
        Your sole job is to understand the intents of customer messages written in Bangla and return them in strict JSON format.   

        ### Objectives:
        1. Identify the customer’s intent (Available intents are "user_greet", "activate_roaming", "user_confirm", "user_deny", "thank_you" and "agent_transfer").
        2. Assign a confidence score between 0 and 100 representing how sure you are about your interpretation.  

        ### Expected Output:
        Always return a single valid JSON object in this exact format:
        {
        "intent": "<string>",
        "confidence": <int between 0 and 100>
        }

        ### Example 1:
        **Input (Bangla):**  
        "আমি সিঙ্গাপুরে রোমিং চালু করতে চাই।"  

        **Output (JSON):**  
        {
        "intent": "activate_roaming",
        "confidence": 95
        }

        ### Example 2:
        **Input (Bangla):**  
        "হ্যাঁ, এখনই চালু করে দিন।"  

        **Output (JSON):**  
        {
        "intent": "user_confirm",
        "confidence": 95
        }

        ### Example 3:
        **Input (Bangla):**  
        "হ্যালো"  

        **Output (JSON):**  
        {
        "intent": "user_greet",
        "confidence": 95
        }

        ### Example 4:
        **Input (Bangla):**  
        "না, অন্যটা দিন।"  

        **Output (JSON):**  
        {
        "intent": "user_deny",
        "confidence": 95
        }

        ### Example 5:
        **Input (Bangla):**  
        "অন্য কোন প্যাকেজ আছে?"  

        **Output (JSON):**  
        {
        "intent": "user_deny",
        "confidence": 95
        }

        ### Example 6:
        **Input (Bangla):**  
        "না, ধন্যবাদ।"  

        **Output (JSON):**  
        {
        "intent": "thank_you",
        "confidence": 95
        }

        ### Example 7:
        **Input (Bangla):**  
        "ধন্যবাদ।"  

        **Output (JSON):**  
        {
        "intent": "thank_you",
        "confidence": 95
        }
        ### Example 8:
        **Input (Bangla):**  
        "আমি একজন প্রতিনিধির সাথে কথা বলতে চাই।"  

        **Output (JSON):**  
        {
        "intent": "agent_transfer",
        "confidence": 95
        }

    """
    messages = [{"role": "system", "content": INTENT_SYSTEM_PROMPT}]

    messages.append({"role": "user", "content": user_input})
    json_intent = call_structured_output_llm(messages)
    if json_intent:
        return json_intent
    else:
        return False

def extract_country_name(user_input):
    """
        Extracts country name from user input and returns in following json format:
        {
            "country": <string>,
            "confidence": <int between 0 and 100>
        }
    """
    COUNTRY_SYSTEM_PROMPT = """
        You are a Grameenphone Roaming Activation Assistant for the 121 Hotline.  
        Your sole job is to extract country name (if present) from customer messages written in Bangla and return them in strict JSON format.   

        ### Objectives:
        1. Extract country name (if available in user message).
        2. Assign a confidence score between 0 and 100 representing how sure you are about your interpretation.  

        ### Expected Output:
        Always return a single valid JSON object in this exact format:
        {
        "country": "<string>",
        "confidence": <int between 0 and 100>
        }

        ### Example:
        **Input (Bangla):**  
        "আমি সিঙ্গাপুরে রোমিং চালু করতে চাই।"  

        **Output (JSON):**  
        {
        "country": "Singapore",
        "confidence": 95
        }

    """
    messages = [{"role": "system", "content": COUNTRY_SYSTEM_PROMPT}]

    messages.append({"role": "user", "content": user_input})
    json_country = call_structured_output_llm(messages)
    if json_country:
        return json_country
    else:
        return False

def get_user_profile(user_id):
    user_profile = user_profiles_db.get(user_id, None)
    return user_profile

def is_eligible(user_profile, requested_country):
    supported_country = user_profile.get("country_supported", None)
    if supported_country == None:
        print("User has not supported country.")
        return False
    restrictions = user_profile.get("restrictions", [])
    has_no_restrictions = (len(restrictions) == 0)
    if (requested_country.strip().lower() == supported_country.strip().lower()) and has_no_restrictions:
        return True
    else:
        return False

def activate_roaming(user_profile):
    user_profile["roaming_status"] = "active"
    return user_profile

def activate_package(user_profile):
    user_profile["package_active"] = True
    return user_profile

def recommend_package(requested_country):
    available_packs = [
        pack for pack in roaming_packages_db
        if pack["country"].lower() == requested_country.lower()
    ]
    if available_packs:
        return available_packs[0]
    else:
        return None

def recommend_another_package(requested_country, recommended_package_ids):
    # Filter by country first
    available_packs = [
        pack for pack in roaming_packages_db
        if pack["country"].lower() == requested_country.lower()
    ]

    if not available_packs:
        return None

    # Exclude previously recommended packages
    remaining_packs = [
        pack for pack in available_packs
        if pack["package_id"] not in recommended_package_ids
    ]

    # Return the next package in the list
    if remaining_packs:
        return remaining_packs[0]
    else:
        return None
