# app.py
from flask import Flask, request, jsonify, render_template

from utils import (
    create_session,
    call_structured_output_llm, 
    detect_user_intent, 
    extract_country_name, 
    is_eligible, 
    activate_roaming,
    activate_package,
    recommend_package,
    recommend_another_package,
)

from response_utils import (
    get_bangla_username,
    get_bangla_country_name,
    get_bangla_package_info,
    get_valid_country_text
)
    
app = Flask(__name__)

VALID_COUNTRIES = ["singapore", "nepal", "bhutan"]

INTENT_CONFIDENCE_THRESHOLD = 70
SLOT_CONFIDENCE_THRESHOLD = 70
CONSENT_CONFIDENCE_THRESHOLD = 70

MAX_RETRIES = 6

# In-memory session store
sessions = {}

@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")

# @app.route('/', methods=['POST'])
@app.route('/conversation', methods=['POST'])
def conversation():
    data = request.get_json()
    user_id = data.get("user_id")
    user_input = data.get("user_input")
    is_new_conversation = data.get("is_new_conversation")

    if is_new_conversation is None:
        return jsonify({"error": "Missing information about conversation status(is new or old conversation)"}), 400

    if not user_id or not user_input:
        return jsonify({"error": "Missing user_id or user_input"}), 400

    print(f"User id: {user_id}")
    print(f"User message: {user_input}")
    print(f"New conversation: {is_new_conversation}")

    # Initialize session if new user
    if is_new_conversation:
        session = create_session(user_id, sessions)
        if not session:
            return jsonify({"error":"invalid_user"}), 400
        # username = session['user_profile']['username']
        # bangla_username = get_bangla_username(username)
        # msg = f"প্রিয় {bangla_username}। গ্রামীনফোনে আপনাকে স্বাগতম। আমি কিভাবে সহযোগিতা করতে পারি?"
        # print(f"bot: {msg}")
        # return jsonify({"bot": msg})
    else:
        try :
            session = sessions[user_id]
        except:
            return jsonify({"error": f"{user_id} is not a valid user."})
        
    if not session:
        return jsonify({"error":"invalid_user"}), 400

    # get profile of current user
    user_profile = session["user_profile"]
    print(f"Current state: {session['state']}")
    username = user_profile['username']
    bangla_username = get_bangla_username(username)
    # ----- Intent Detection -----
    if session["state"] == "awaiting_intent":
        json_intent = detect_user_intent(user_input)
        if not json_intent:
            session["intent_retries"] += 1
            if session["intent_retries"] >= MAX_RETRIES:
                session["state"] = "awaiting_intent"
                msg = "দুঃখিত, আমি বুঝতে পারিনি। আপনার কলটি আমাদের একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            msg = "দুঃখিত, আমি আপনার অনুরোধ বুঝতে পারিনি। দয়া করে আবার বলুন।"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

        intent = json_intent.get("intent", None)
        intent_confidence = json_intent.get("confidence", 0)
        print(f"Detected intent: {intent}")
        print(f"Intent confidence: {intent_confidence}")
        ####################################################
        # Start of logic for when user greets first on new conversation
        if intent == "user_greet" and intent_confidence > INTENT_CONFIDENCE_THRESHOLD:
            # We only accept user greet when new conversation is created.
            if is_new_conversation:
                session["intent_detected"] = intent
                session["intent_retries"] = 0
                username = user_profile['username']
                bangla_username = get_bangla_username(username)
                msg = f"প্রিয় {bangla_username}। গ্রামীনফোনে আপনাকে স্বাগতম। আমি কিভাবে সহযোগিতা করতে পারি?"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            else:
                session["intent_retries"] += 1
                if session["intent_retries"] >= MAX_RETRIES:
                    session["state"] = "awaiting_intent"
                    msg = "দুঃখিত, আমি বুঝতে পারিনি। আপনার কলটি আমাদের একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                    print(f"Next state: {session['state']}\n")
                    print(f"bot: {msg}")
                    return jsonify({"bot": msg})
                msg = "দুঃখিত, আমি আপনার অনুরোধ বুঝতে পারিনি। দয়া করে আবার বলুন।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
        # End of logic for when user greets first on new conversation
        ####################################################
        # thank you intent at the end of conversation.
        elif intent == "thank_you" and intent_confidence > INTENT_CONFIDENCE_THRESHOLD:
            session["state"] = "awaiting_intent"
            msg = "গ্রামীনফোনের সাথে থাকার জন্য ধন্যবাদ।"
            print(f"bot: {msg}")
            return jsonify({"bot": msg})
        # logic for when the user wants to talk to a human agent.
        elif intent == "agent_transfer" and intent_confidence > INTENT_CONFIDENCE_THRESHOLD:
            session["state"] = "awaiting_intent"
            msg = "আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

        elif intent == "activate_roaming" and intent_confidence > INTENT_CONFIDENCE_THRESHOLD:
            session["intent_detected"] = intent
            session["intent_retries"] = 0
            ########################################################################
            # Start of logic for when user provides country with roaming activate intent.
            session["state"] = "awaiting_country" # next user message will go to the "awaiting_country" branch.
            json_country = extract_country_name(user_input)
            if not json_country:
                msg = "আপনি কোন দেশের জন্য রোমিং চালু করতে চান?"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})

            country = json_country.get("country", None)
            country_confidence = json_country.get("confidence", 0)
            if country is None:
                session["state"] = "awaiting_country"
                msg = "আপনি কোন দেশের জন্য রোমিং চালু করতে চান?"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})

            if country and country_confidence > SLOT_CONFIDENCE_THRESHOLD:
                country = country.strip().lower()
                username = user_profile['username']
                bangla_username = get_bangla_username(username)
                bangla_country_name = get_bangla_country_name(country)
                if country in VALID_COUNTRIES:
                    session["requested_country"] = country
                    # check eligibility
                    if is_eligible(user_profile, session["requested_country"]):
                        # Eligible. Check roaming status.
                        if user_profile["roaming_status"] == "active":
                            # logic for when roaming status active
                            recommended_package = recommend_package(session["requested_country"])
                            # # convert information into Bangla for plugging into static assistant response.
                            if not recommended_package:
                                # static assistant response
                                assistant_response = f"দুঃখিত, {bangla_username}। {bangla_country_name} জন্য আপাতত কোনো প্যাকেজ নেই। আপনি অন্য কোনো দেশের জন্য চেষ্টা করতে পারেন।"
                                # update session
                                session["state"] = "awaiting_country"
                                print(f"Next state: {session['state']}\n")
                                print(f"bot: {assistant_response}")
                                return jsonify({"bot": assistant_response})
                            else:
                                bn_package_info = get_bangla_package_info(recommended_package)
                                assistant_response = f"প্রিয় {bangla_username}। আপনি {bangla_country_name} জন্য রোমিং সেবা সক্রিয় রেখেছেন। আপনার জন্য নির্ধারিত সেরা প্যাকেজ হলো {bn_package_info['data_limit_MB_in_bn']} এমবি ডাটা, {bn_package_info['voice_minutes_in_bn']} মিনিট ভয়েস এবং {bn_package_info['sms_limit_in_bn']}টি এসএমএস। প্যাকেজটির মেয়াদ {bn_package_info['validity_days_in_bn']} দিন এবং মূল্য {bn_package_info['price_BDT_in_bn']} টাকা। আপনি কি এই প্যাকেজটি সক্রিয় করতে আগ্রহী?"
                                # update session
                                session["recommended_package_ids"].append(recommended_package["package_id"])
                                session["state"] = "awaiting_package_consent"
                                print(f"Next state: {session['state']}\n")
                                print(f"bot: {assistant_response}")
                                return jsonify({"bot": assistant_response})  
                        else:
                            # logic for when roaming status not active
                            assistant_response = f"প্রিয় {bangla_username} । আপনার জন্য {bangla_country_name} রোমিং সার্ভিস বর্তমানে সক্রিয় নেই। আপনি কি {bangla_country_name} জন্য রোমিং সুবিধা সক্রিয় করতে চান?"
                            # update session
                            session["state"] = "awaiting_roaming_consent"
                            print(f"Next state: {session['state']}\n")
                            print(f"bot: {assistant_response}")
                            return jsonify({"bot": assistant_response})
                    else:
                        # Not eligible: inform politely and end conversation.
                        session["state"] = "awaiting_intent"
                        msg = "দুঃখিত, আপনার এই নাম্বারের জন্য সার্ভিস টি প্রযোজ্য নয়। আপনি অন্য কোনও সার্ভিস চেষ্টা করতে পারেন।"
                        print(f"Next state: {session['state']}\n")
                        print(f"bot: {msg}")
                        return jsonify({"bot": msg})
                else:
                    # logic for when country not valid
                    # generate llm response using valid country names # that code is removed.
                    valid_country_text = get_valid_country_text(VALID_COUNTRIES)
                    valid_country_text = valid_country_text.split(',')
                    last_one = valid_country_text[-1]
                    valid_country_text = ",".join(valid_country_text[:-1]) + " এবং" + last_one
                    assistant_response = f"দুঃখিত {bangla_username}। {bangla_country_name} জন্য রোমিং সুবিধা প্রযোজ্য নয়। যে সকল দেশের জন্য রোমিং সুবিধা প্রযোজ্য সেগুলো হলো{valid_country_text}।"
                    # assistant_response = f"দুঃখিত, {bangla_username}। {bangla_country_name} জন্য আপাতত কোন প্যাকেজ নেই। আপনি অন্য কোন দেশের জন্য চেষ্টা করতে পারেন।"
                    # update session
                    print(f"Next state: {session['state']}\n")
                    print(f"bot: {assistant_response}")
                    return jsonify({"bot": assistant_response}) 
            else:
                msg = "আপনি কোন দেশের জন্য রোমিং চালু করতে চান?"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
                # return jsonify({"bot": "আপনি কোন দেশের জন্য রোমিং চালু করতে চান?"})
            # End of logic for when user provides country with roaming activate intent.
            ########################################################################
        else:
            session["intent_retries"] += 1
            if session["intent_retries"] >= MAX_RETRIES:
                session["state"] = "awaiting_intent"
                msg = "দুঃখিত, আমি বুঝতে পারিনি। আপনার কলটি আমাদের একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            msg = "দুঃখিত, আমি আপনার অনুরোধ বুঝতে পারিনি। দয়া করে আবার চেষ্টা করুন।"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

    # ---- Country Extraction ----
    elif session["state"] == "awaiting_country":
        json_country = extract_country_name(user_input)
        if not json_country:
            session["country_retries"] += 1
            if session["country_retries"] >= MAX_RETRIES:
                session["state"] = "awaiting_intent"
                msg = "দুঃখিত, আমি দেশটি বুঝতে পারিনি। আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            msg = "আমি দেশটি ধরতে পারিনি। দয়া করে আবার বলুন।"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

        country = json_country.get("country", None)
        confidence = json_country.get("confidence", 0)
        if country is None:
            session["state"] = "awaiting_country"
            msg = "আপনি কোন দেশের জন্য রোমিং চালু করতে চান?"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

        if country and confidence > SLOT_CONFIDENCE_THRESHOLD:
            # logic for when bot can detect country properly.
            country = country.strip().lower()
            username = user_profile['username']
            # convert information into Bangla for plugging into static assistant response.
            bangla_username = get_bangla_username(username)
            bangla_country_name = get_bangla_country_name(country)
            if country in VALID_COUNTRIES:
                session["requested_country"] = country
                session["country_retries"] = 0
                # check eligibility
                if is_eligible(user_profile, session["requested_country"]):
                    # Eligible
                    # check roaming status
                    if user_profile["roaming_status"] == "active":
                        # logic for when roaming status active
                        recommended_package = recommend_package(session["requested_country"])
                        if not recommended_package:
                            # static assistant response
                            assistant_response = f"দুঃখিত, {bangla_username}। {bangla_country_name} জন্য আপাতত কোনো প্যাকেজ নেই। আপনি অন্য কোনো দেশের জন্য চেষ্টা করতে পারেন।"
                            # update session
                            session["state"] = "awaiting_country"
                            print(f"Next state: {session['state']}\n")
                            print(f"bot: {assistant_response}")
                            return jsonify({"bot": assistant_response})
                        else:
                            bn_package_info = get_bangla_package_info(recommended_package)
                            assistant_response = f"প্রিয় {bangla_username}। আপনি {bangla_country_name} জন্য রোমিং সেবা সক্রিয় রেখেছেন। আপনার জন্য নির্ধারিত সেরা প্যাকেজ হলো {bn_package_info['data_limit_MB_in_bn']} এমবি ডাটা, {bn_package_info['voice_minutes_in_bn']} মিনিট ভয়েস এবং {bn_package_info['sms_limit_in_bn']}টি এসএমএস।। প্যাকেজটির মেয়াদ {bn_package_info['validity_days_in_bn']} দিন এবং মূল্য {bn_package_info['price_BDT_in_bn']} টাকা। আপনি কি এই প্যাকেজটি সক্রিয় করতে আগ্রহী?"
                            # update session
                            session["state"] = "awaiting_package_consent"
                            print(f"Next state: {session['state']}\n")
                            print(f"bot: {assistant_response}")
                            return jsonify({"bot": assistant_response})
                    else:
                        # logic for when roaming status not active
                        assistant_response = f"প্রিয় {bangla_username} । আপনার জন্য {bangla_country_name} রোমিং সার্ভিস বর্তমানে সক্রিয় নেই। আপনি কি {bangla_country_name} জন্য রোমিং সুবিধা সক্রিয় করতে চান?"
                        # update session
                        session["state"] = "awaiting_roaming_consent"
                        print(f"Next state: {session['state']}\n")
                        print(f"bot: {assistant_response}")
                        return jsonify({"bot": assistant_response})
                else:
                    # Not eligible: inform politely and end conversation.
                    session["state"] = "awaiting_intent"
                    msg = "দুঃখিত, আপনার এই নাম্বারের জন্য সার্ভিস টি প্রযোজ্য নয়। আপনি অন্য কোনও সার্ভিস চেষ্টা করতে পারেন।"
                    print(f"Next state: {session['state']}\n")
                    print(f"bot: {msg}")
                    return jsonify({"bot": msg})
            else:
                # logic for when country not valid
                session["country_retries"] += 1
                if session["country_retries"] >= MAX_RETRIES:
                    session["state"] = "awaiting_intent"
                    msg = "দুঃখিত, আমি দেশটি বুঝতে পারিনি। আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                    print(f"Next state: {session['state']}\n")
                    print(f"bot: {msg}")
                    return jsonify({"bot": msg})
                # generate llm response using valid country names # that code is removed.
                valid_country_text = get_valid_country_text(VALID_COUNTRIES)
                valid_country_text = valid_country_text.split(',')
                last_one = valid_country_text[-1]
                valid_country_text = ",".join(valid_country_text[:-1]) + " এবং" + last_one
                assistant_response = f"দুঃখিত {bangla_username}। {bangla_country_name} জন্য রোমিং সুবিধা প্রযোজ্য নয়। যে সকল দেশের জন্য রোমিং সুবিধা প্রযোজ্য সেগুলো হলো{valid_country_text}।"
                # assistant_response = f"দুঃখিত, {bangla_username}। {bangla_country_name} জন্য আপাতত কোন প্যাকেজ নেই। আপনি অন্য কোন দেশের জন্য চেষ্টা করতে পারেন।"
                # update session
                print(f"Next state: {session['state']}\n")
                print(f"bot: {assistant_response}")
                return jsonify({"bot": assistant_response}) 
        else:
            # logic for when bot can not detect country properly.
            session["country_retries"] += 1
            if session["country_retries"] >= MAX_RETRIES:
                session["state"] = "awaiting_intent"
                msg = "দুঃখিত, আমি দেশটি বুঝতে পারিনি। আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            msg = "দুঃখিত, আমি দেশটি বুঝতে পারিনি। দয়া করে আবার বলুন।"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

    # State: awaiting_package_consent
    elif session["state"] == "awaiting_package_consent":
        # Detect confirm intent from user_input
        json_intent = detect_user_intent(user_input)
        if not json_intent:
            session["consent_retries"] += 1
            if session["consent_retries"] >= MAX_RETRIES:
                session["state"] = "awaiting_intent"
                msg = "দুঃখিত, আমি বুঝতে পারিনি। আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            msg = "দুঃখিত, আমি বুঝতে পারিনি। দয়া করে আবার বলুন। আমি কি প্যাকেজ টি চালু করবো?"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

        intent = json_intent.get("intent", None)
        confidence = json_intent.get("confidence", 0)
        if intent == "user_confirm" and confidence > CONSENT_CONFIDENCE_THRESHOLD:
            session['consent_retries'] = 0 # reset consent_retries when user consent is detected successfully.
            # Activate package
            user_profile = activate_package(user_profile)
            session["user_profile"] = user_profile
            session["state"] = "awaiting_intent"
            msg = "আপনার প্যাকেজ টি চালু হয়েছে। আমি কি আপনাকে আর কোনোভাবে সহযোগিতা করতে পারি?"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

        # code for when user wants another package instead of the recommended one.
        elif intent == "user_deny" and confidence > CONSENT_CONFIDENCE_THRESHOLD:
            session['consent_retries'] = 0
            bangla_country_name = get_bangla_country_name(session["requested_country"])
            recommended_package = recommend_another_package(session["requested_country"], session["recommended_package_ids"])
            # # convert information into Bangla for plugging into static assistant response.
            if not recommended_package:
                # static assistant response
                assistant_response = f"দুঃখিত, {bangla_username}। {bangla_country_name} জন্য আপাতত আর কোনো প্যাকেজ নেই। আপনি অন্য কোনো দেশের জন্য চেষ্টা করতে পারেন।"
                # update session
                session["state"] = "awaiting_country"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {assistant_response}")
                return jsonify({"bot": assistant_response})
            else:
                bn_package_info = get_bangla_package_info(recommended_package)
                assistant_response = f"প্রিয় {bangla_username}। আপনার জন্য উপযুক্ত আরেকটি প্যাকেজ হলো {bn_package_info['data_limit_MB_in_bn']} এমবি ডাটা, {bn_package_info['voice_minutes_in_bn']} মিনিট ভয়েস এবং {bn_package_info['sms_limit_in_bn']}টি এসএমএস। প্যাকেজটির মেয়াদ {bn_package_info['validity_days_in_bn']} দিন এবং মূল্য {bn_package_info['price_BDT_in_bn']} টাকা। আপনি কি এই প্যাকেজটি সক্রিয় করতে আগ্রহী?"
                # update session
                session["recommended_package_ids"].append(recommended_package["package_id"])
                session["state"] = "awaiting_package_consent"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {assistant_response}")
                return jsonify({"bot": assistant_response}) 

        else:
            session["consent_retries"] += 1
            if session["consent_retries"] >= MAX_RETRIES:
                session["state"] = "awaiting_intent"
                msg = "দুঃখিত, আমি বুঝতে পারিনি। আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            msg = "দুঃখিত, আমি বুঝতে পারিনি। দয়া করে আবার বলুন। আমি কি প্যাকেজ টি চালু করবো?"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

    # State: awaiting_roaming_consent
    elif session["state"] == "awaiting_roaming_consent":
        json_intent = detect_user_intent(user_input)
        if not json_intent:
            session["consent_retries"] += 1
            if session["consent_retries"] >= MAX_RETRIES:
                session["state"] = "awaiting_intent"
                msg = "দুঃখিত, আমি বুঝতে পারিনি। আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            msg = "দুঃখিত, আমি বুঝতে পারিনি। দয়া করে আবার বলুন। আমি কি রোমিং চালু করবো?"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})

        intent = json_intent.get("intent", None)
        confidence = json_intent.get("confidence", 0)
        if intent == "user_confirm" and confidence > CONSENT_CONFIDENCE_THRESHOLD:
            session['consent_retries'] = 0 # reset consent_retries when user consent is detected successfully.
            # Activate roaming
            user_profile = activate_roaming(user_profile)
            session["user_profile"] = user_profile
            # session["state"] = "awaiting_intent" # state reset when activating roaming without package recommendation.
            # proactively recommend package
            recommended_package = recommend_package(session["requested_country"])
            bn_package_info = get_bangla_package_info(recommended_package)
            msg = f"আপনার রোমিং সার্ভিসটি চালু হয়েছে। আপনার জন্য নির্ধারিত সেরা প্যাকেজ হলো {bn_package_info['data_limit_MB_in_bn']} এমবি ডাটা, {bn_package_info['voice_minutes_in_bn']} মিনিট ভয়েস এবং {bn_package_info['sms_limit_in_bn']}টি এসএমএস। প্যাকেজটির মেয়াদ {bn_package_info['validity_days_in_bn']} দিন এবং মূল্য {bn_package_info['price_BDT_in_bn']} টাকা। আপনি কি এই প্যাকেজটি সক্রিয় করতে আগ্রহী?"
            # update session
            session["recommended_package_ids"].append(recommended_package["package_id"])
            session["state"] = "awaiting_package_consent"

            # msg = "আপনার রোমিং সার্ভিসটি চালু হয়েছে। আমি কি আপনাকে আর কোনভাবে সহযোগিতা করতে পারি?"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})
        else:
            session["consent_retries"] += 1
            if session["consent_retries"] >= MAX_RETRIES:
                session["state"] = "awaiting_intent"
                msg = "দুঃখিত, আমি বুঝতে পারিনি। আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
                print(f"Next state: {session['state']}\n")
                print(f"bot: {msg}")
                return jsonify({"bot": msg})
            msg = "দুঃখিত, আমি বুঝতে পারিনি। দয়া করে আবার বলুন। আমি কি রোমিং চালু করবো?"
            print(f"Next state: {session['state']}\n")
            print(f"bot: {msg}")
            return jsonify({"bot": msg})    
    else:
        session["state"] = "awaiting_intent"
        msg = "দুঃখিত, আমি বুঝতে পারিনি। আপনার কলটি একজন প্রতিনিধির কাছে হস্তান্তর করা হচ্ছে।"
        print(f"Next state: {session['state']}\n")
        print(f"bot: {msg}")
        return jsonify({"bot": msg})

if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000)