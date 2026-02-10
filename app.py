"""
Telecom Customer Complaint Handling Chatbot
============================================
A multilingual chatbot that handles ONLY telecom-sector complaints.
Uses Azure OpenAI GPT-4o-mini for SEMANTIC understanding, language detection,
and generating resolution steps.

Key improvement: All classification uses intent/meaning-based analysis,
not keyword matching. The model reasons about what the user MEANS,
not just what words they used.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, session
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ─── Azure OpenAI Configuration ─────────────────────────────────────────────
client = AzureOpenAI(
    api_key = "",
    api_version = "",
    azure_endpoint="",
)
DEPLOYMENT_NAME = "gpt-4o-mini"


# ─── Telecom Sector Menu Structure ──────────────────────────────────────────
# Each subprocess now has a "semantic_scope" that describes the MEANING of that
# category — not just keywords, but the kinds of real-world problems it covers.
# This gives GPT rich context for intent-based matching.
TELECOM_MENU = {
    "1": {
        "name": "Mobile Services (Prepaid / Postpaid)",
        "icon": "📱",
        "description": "Covers all issues related to mobile phone services including voice calls, SMS, mobile data, SIM cards, prepaid recharges, postpaid billing, roaming, number portability, and mobile network coverage.",
        "subprocesses": {
            "1": {
                "name": "Billing & Payment Issues",
                "semantic_scope": "Unexpected charges, wrong bill amount, double billing, payment failed but money deducted, recharge not credited, balance deducted without usage, auto-renewal charged, EMI issues on phone, refund not received for telecom services, incorrect tax on bill, bill dispute"
            },
            "2": {
                "name": "Network / Signal Problems",
                "semantic_scope": "No signal, weak signal, call drops, poor network coverage, network congestion, unable to make/receive calls, tower issue, dead zone, indoor coverage problem, 4G/5G not available, network outage in area"
            },
            "3": {
                "name": "SIM Card & Activation",
                "semantic_scope": "New SIM not activated, SIM blocked, SIM damaged, SIM swap, eSIM activation, lost SIM replacement, SIM not detected, PUK locked, KYC verification pending, Aadhaar linking with SIM, SIM upgrade to 4G/5G"
            },
            "4": {
                "name": "Data Plan & Recharge Issues",
                "semantic_scope": "Data not working after recharge, wrong plan activated, data exhausted too quickly, unable to recharge, recharge failed but amount debited, validity not extended, data speed throttled, unlimited plan not giving unlimited data, add-on pack issues, coupon/promo code not working"
            },
            "5": {
                "name": "International Roaming",
                "semantic_scope": "Roaming not working abroad, high roaming charges, incoming calls charged during roaming, data roaming activation, roaming pack not applied, unable to call from foreign country, roaming bill shock, ISD/STD calling issues"
            },
            "6": {
                "name": "Mobile Number Portability (MNP)",
                "semantic_scope": "Want to switch operator, MNP request rejected, porting delay, UPC code not received, number lost during porting, services disrupted after porting, porting to another network, port-out issues"
            },
            "7": {
                "name": "Call / SMS Failures",
                "semantic_scope": "Unable to make calls, calls not connecting, one-way audio, SMS not being delivered, SMS not received, OTP not coming, call going to voicemail, DND (Do Not Disturb) issues, spam calls, call forwarding not working, conference call issues"
            },
            "8": {"name": "Others", "semantic_scope": ""}
        },
    },
    "2": {
        "name": "Broadband / Internet Services",
        "icon": "🌐",
        "description": "Covers all issues related to wired/wireless broadband, fiber internet, DSL connections, WiFi, and home/office internet services.",
        "subprocesses": {
            "1": {
                "name": "Slow Speed / No Connectivity",
                "semantic_scope": "Internet too slow, speed not matching plan, buffering while streaming, downloads very slow, no internet connection, WiFi connected but no internet, speed drops at night, latency/ping too high, speed test showing low results, bandwidth issue"
            },
            "2": {
                "name": "Frequent Disconnections",
                "semantic_scope": "Internet keeps disconnecting, connection drops every few minutes, unstable connection, intermittent connectivity, WiFi drops frequently, connection resets, have to restart router repeatedly, disconnects during video calls"
            },
            "3": {
                "name": "Billing & Plan Issues",
                "semantic_scope": "Wrong broadband bill, overcharged, plan upgrade/downgrade issues, FUP limit reached, auto-debit failed, payment not reflected, want to change plan, hidden charges, installation charges disputed, security deposit refund"
            },
            "4": {
                "name": "New Connection / Installation",
                "semantic_scope": "New broadband connection request, installation delayed, technician not showing up, fiber cable not laid, connection pending, availability check, shift connection to new address, relocation of broadband"
            },
            "5": {
                "name": "Router / Equipment Problems",
                "semantic_scope": "Router not working, WiFi router faulty, modem blinking red, ONT device issue, router overheating, need router replacement, firmware update problem, WiFi range too short, LAN port not working, equipment return"
            },
            "6": {
                "name": "IP Address / DNS Issues",
                "semantic_scope": "Cannot access certain websites, DNS resolution failure, need static IP, IP blocked, website loading error, proxy issues, VPN not working over broadband, port forwarding needed"
            },
            "7": {"name": "Others", "semantic_scope": ""}
        },
    },
    "3": {
        "name": "DTH / Cable TV Services",
        "icon": "📺",
        "description": "Covers all issues related to Direct-To-Home television, cable TV, set-top boxes, and TV channel subscriptions.",
        "subprocesses": {
            "1": {
                "name": "Channel Not Working / Missing",
                "semantic_scope": "Channel not showing, channel removed from pack, channel black screen, paid channel not available, regional channel missing, HD channel not working, channel list changed, favorite channel gone"
            },
            "2": {
                "name": "Set-Top Box Issues",
                "semantic_scope": "Set-top box not turning on, remote not working, set-top box hanging/freezing, recording not working, set-top box overheating, display error on box, need set-top box replacement, software update stuck, box showing boot loop"
            },
            "3": {
                "name": "Billing & Subscription",
                "semantic_scope": "Wrong DTH bill, subscription expired, auto-renewal issue, pack change charges, NCF charges too high, channel added without consent, refund not received, wallet recharge failed, monthly charges incorrect"
            },
            "4": {
                "name": "Signal / Picture Quality",
                "semantic_scope": "No signal on TV, picture breaking/pixelating, rain causing signal loss, dish alignment needed, weak signal, audio out of sync, color distortion, signal loss at certain times, frozen picture, horizontal lines on TV"
            },
            "5": {
                "name": "Package / Plan Changes",
                "semantic_scope": "Want to change channel pack, upgrade to HD, add premium channels, downgrade plan, customize channel selection, regional pack addition, sports pack subscription, plan comparison, best value pack"
            },
            "6": {"name": "Others", "semantic_scope": ""}
        },
    },
    "4": {
        "name": "Landline / Fixed Line Services",
        "icon": "☎️",
        "description": "Covers all issues related to traditional landline phone services, fixed-line connections, and wired telephone services.",
        "subprocesses": {
            "1": {
                "name": "No Dial Tone / Dead Line",
                "semantic_scope": "Landline not working, no dial tone, line dead, phone silent, no sound when picking up receiver, line suddenly stopped working, connection cut off, cable damaged"
            },
            "2": {
                "name": "Call Quality Issues (Noise / Echo)",
                "semantic_scope": "Static noise on landline, echo during calls, crackling sound, voice breaking, cross-connection hearing other conversations, humming noise, low volume on calls, distorted audio"
            },
            "3": {
                "name": "Billing & Charges",
                "semantic_scope": "Landline bill too high, calls charged incorrectly, wrong number dialed charges, rental overcharged, payment not updated, metered vs unlimited plan dispute, ISD charges on landline"
            },
            "4": {
                "name": "New Connection / Disconnection",
                "semantic_scope": "Want new landline connection, disconnection request, temporary suspension, connection shifting to new address, reconnection after disconnection, transfer of ownership"
            },
            "5": {
                "name": "Fault Repair Request",
                "semantic_scope": "Cable cut in area, junction box damaged, overhead wire fallen, underground cable fault, technician visit needed, repeated fault in same line, wet cable causing issues, maintenance request"
            },
            "6": {"name": "Others", "semantic_scope": ""}
        },
    },
    "5": {
        "name": "Enterprise / Business Solutions",
        "icon": "🏢",
        "description": "Covers all issues related to business/corporate telecom solutions including leased lines, SLA-based services, bulk connections, cloud telephony, and managed network services.",
        "subprocesses": {
            "1": {
                "name": "SLA Breach / Service Downtime",
                "semantic_scope": "Service level agreement not met, uptime guarantee violated, business internet down, prolonged outage affecting business, compensation for downtime, SLA penalty claim, response time exceeded"
            },
            "2": {
                "name": "Leased Line / Dedicated Connection",
                "semantic_scope": "Leased line down, dedicated bandwidth not delivered, point-to-point link failure, MPLS circuit issue, last mile connectivity problem, fiber cut affecting leased line, jitter/latency on dedicated line"
            },
            "3": {
                "name": "Bulk / Corporate Plan Issues",
                "semantic_scope": "Corporate plan benefits not applied, bulk SIM management, employee connection issues, CUG (Closed User Group) problem, corporate billing discrepancy, group plan changes"
            },
            "4": {
                "name": "Cloud / VPN / MPLS Issues",
                "semantic_scope": "VPN tunnel down, MPLS network unreachable, cloud connectivity slow, SD-WAN issue, site-to-site VPN failure, enterprise cloud access problem, managed WiFi for office not working"
            },
            "5": {
                "name": "Technical Support Escalation",
                "semantic_scope": "Need senior technician, previous complaint not resolved, multiple complaints on same issue, want to escalate to manager, technical team not responding, critical issue needs immediate attention"
            },
            "6": {"name": "Others", "semantic_scope": ""}
        },
    },
}


# ─── Helper: Build subprocess info for prompts ──────────────────────────────
def get_subprocess_details(sector_key: str) -> str:
    """Build a rich description of subprocesses for semantic matching."""
    sector = TELECOM_MENU[sector_key]
    details = []
    for k, v in sector["subprocesses"].items():
        if isinstance(v, dict) and v["name"] != "Others":
            details.append(
                f"SUBPROCESS: \"{v['name']}\"\n"
                f"  Typical issues: {v['semantic_scope']}"
            )
    return "\n\n".join(details)


def get_subprocess_name(sector_key: str, subprocess_key: str) -> str:
    """Get subprocess name from the menu structure."""
    sector = TELECOM_MENU.get(sector_key, {})
    sp = sector.get("subprocesses", {}).get(subprocess_key, {})
    if isinstance(sp, dict):
        return sp.get("name", "Others")
    return sp if isinstance(sp, str) else "Others"


# ─── SEMANTIC CHECK: Is the query telecom-related? ──────────────────────────
def is_telecom_related(query: str, sector_name: str = None, subprocess_name: str = None) -> bool:
    """
    Use chain-of-thought semantic reasoning to determine if a query is
    telecom-related. The model REASONS about the user's intent, not just
    whether telecom keywords appear.
    """
    context_block = ""
    if sector_name:
        context_block = (
            f"\n\n── USER'S MENU NAVIGATION ──\n"
            f"The user already selected telecom sector: \"{sector_name}\""
        )
        if subprocess_name:
            context_block += f"\nThey also selected subprocess: \"{subprocess_name}\""
        context_block += (
            "\n\nBecause the user navigated a TELECOM complaint menu to reach this point, "
            "their query is almost certainly telecom-related. Generic complaints like "
            "'money deducted', 'service not working', 'bad experience', 'want refund', "
            "'not getting what I paid for' etc. should be interpreted in the telecom context.\n"
            "Only classify as NOT telecom if the query is EXPLICITLY about a completely "
            "different industry (e.g., 'my pizza was cold', 'Amazon package not delivered', "
            "'hospital appointment issue', 'my car insurance claim')."
        )

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a semantic intent classifier for a TELECOM complaint chatbot.\n\n"
                        "Your job is to determine whether the user's query is related to telecommunications.\n\n"
                        "TELECOM includes (but is not limited to):\n"
                        "- Mobile phone services (calls, SMS, data, prepaid, postpaid)\n"
                        "- Internet/broadband/WiFi/fiber services\n"
                        "- DTH/cable TV/satellite TV\n"
                        "- Landline/fixed-line telephone\n"
                        "- Enterprise telecom (leased lines, VPN, MPLS, SLA)\n"
                        "- ANY billing, payment, refund, service quality, or customer care issue "
                        "related to any of the above\n\n"
                        "SEMANTIC REASONING RULES:\n"
                        "1. Focus on the USER'S INTENT, not just the words they used.\n"
                        "2. 'Money deducted' in a telecom context = telecom billing issue.\n"
                        "3. 'Service not working' in a telecom context = telecom service disruption.\n"
                        "4. Vague complaints ARE telecom if the user came through the telecom menu.\n"
                        "5. Only reject if the query is CLEARLY about a non-telecom industry.\n"
                        + context_block +
                        "\n\nRespond with ONLY this JSON (no extra text):\n"
                        '{"reasoning": "<one sentence about why>", "is_telecom": true/false}'
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0,
            max_tokens=120,
        )
        raw = response.choices[0].message.content.strip()
        # Handle possible markdown wrapping
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        result = json.loads(raw)
        return result.get("is_telecom", False)
    except Exception as e:
        # If in a telecom menu flow, default to True (benefit of the doubt)
        if sector_name:
            return True
        return False


# ─── SEMANTIC MATCH: Identify subprocess from free-text ─────────────────────
def identify_subprocess(query: str, sector_key: str) -> str:
    """
    When the user selects 'Others' or we need to classify a free-text query,
    use deep semantic matching — the model considers what each subprocess MEANS
    and what kinds of real-world problems fall under it, not just keyword overlap.
    """
    sector = TELECOM_MENU[sector_key]
    subprocess_details = get_subprocess_details(sector_key)

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a semantic complaint classifier for: {sector['name']}.\n"
                        f"Sector description: {sector.get('description', '')}\n\n"
                        "Below are the available subprocesses with descriptions of what each covers:\n\n"
                        f"{subprocess_details}\n\n"
                        "── YOUR TASK ──\n"
                        "Analyze the user's complaint and determine which subprocess it belongs to.\n\n"
                        "SEMANTIC MATCHING RULES:\n"
                        "1. Think about what the user's ACTUAL PROBLEM is, not just matching keywords.\n"
                        "2. A complaint about 'money gone but nothing happened' under Mobile = Billing issue.\n"
                        "3. 'Phone shows no bars' = Network/Signal problem (even without the word 'network').\n"
                        "4. 'Paid but plan not active' = Data Plan & Recharge issue.\n"
                        "5. Consider synonyms, colloquial language, indirect descriptions.\n"
                        "6. 'Net nahi chal raha' (Hindi for internet not working) under Broadband = Slow Speed/No Connectivity.\n"
                        "7. If the complaint genuinely doesn't fit any subprocess, use 'General Inquiry'.\n\n"
                        "Respond with ONLY this JSON:\n"
                        '{"reasoning": "<brief explanation of why this matches>", '
                        '"matched_subprocess": "<exact subprocess name from the list>", '
                        '"confidence": <0.0 to 1.0>}'
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0,
            max_tokens=200,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        result = json.loads(raw)
        return result.get("matched_subprocess", "General Inquiry")
    except Exception:
        return "General Inquiry"


# ─── Helper: Detect language ────────────────────────────────────────────────
def detect_language(text: str) -> str:
    """Detect the language of user input."""
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Detect the language of the following text. "
                        "Consider mixed-language input (e.g., Hinglish = Hindi + English). "
                        "For mixed languages, identify the DOMINANT language.\n"
                        'Respond with ONLY: {"language": "<language_name>", "code": "<iso_code>"}'
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=50,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        result = json.loads(raw)
        return result.get("language", "English")
    except Exception:
        return "English"


# ─── Helper: Generate resolution steps ──────────────────────────────────────
def generate_resolution(query: str, sector_name: str, subprocess_name: str, language: str) -> str:
    """Generate step-by-step resolution for the user's telecom complaint."""
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an expert telecom customer support agent. The user has a complaint "
                        f"under the sector: '{sector_name}' and subprocess: '{subprocess_name}'.\n\n"
                        "Provide a helpful response in the following format:\n"
                        "1. Acknowledge the issue empathetically\n"
                        "2. Provide 4-6 clear, actionable self-help troubleshooting steps the user can try\n"
                        "3. If the steps don't resolve the issue, advise them to contact their telecom "
                        "provider's customer care with their complaint reference\n"
                        "4. Provide a brief note about escalation options (nodal officer, TRAI portal, etc.)\n\n"
                        f"IMPORTANT: Respond entirely in {language}. "
                        "Keep the tone professional, empathetic, and helpful. "
                        "Use clear formatting with numbered steps."
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0.4,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"I apologize, but I encountered an error generating the resolution. Please try again. Error: {str(e)}"


# ─── Helper: Translate text ─────────────────────────────────────────────────
def translate_text(text: str, target_language: str) -> str:
    """Translate system messages to user's detected language."""
    if target_language.lower() in ("english", "en"):
        return text
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": f"Translate the following text to {target_language}. Keep formatting intact. Return ONLY the translation.",
                },
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return text


# ─── Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/menu", methods=["GET"])
def get_menu():
    """Return the telecom sector menu."""
    menu = {}
    for key, sector in TELECOM_MENU.items():
        menu[key] = {"name": sector["name"], "icon": sector["icon"]}
    return jsonify({"menu": menu})


@app.route("/api/subprocesses", methods=["POST"])
def get_subprocesses():
    """Return subprocesses for a chosen sector."""
    data = request.json
    sector_key = data.get("sector_key")
    language = data.get("language", "English")

    if sector_key not in TELECOM_MENU:
        return jsonify({"error": "Invalid sector"}), 400

    sector = TELECOM_MENU[sector_key]
    # Extract just the names for the frontend
    subprocesses = {}
    for k, v in sector["subprocesses"].items():
        if isinstance(v, dict):
            subprocesses[k] = v["name"]
        else:
            subprocesses[k] = v

    # Translate subprocess names if needed
    if language.lower() not in ("english", "en"):
        translated = {}
        for k, v in subprocesses.items():
            translated[k] = translate_text(v, language)
        subprocesses = translated

    return jsonify({
        "sector_name": sector["name"],
        "subprocesses": subprocesses,
    })


@app.route("/api/resolve", methods=["POST"])
def resolve_complaint():
    """Process the user's complaint and return resolution steps."""
    data = request.json
    query = data.get("query", "").strip()
    sector_key = data.get("sector_key")
    subprocess_key = data.get("subprocess_key")
    language = data.get("language", "English")

    if not query:
        return jsonify({"error": "Please enter your complaint/query."}), 400

    # Get sector & subprocess info
    sector = TELECOM_MENU.get(sector_key, {})
    sector_name = sector.get("name", "Telecom")
    subprocess_name = get_subprocess_name(sector_key, subprocess_key)

    # Step 1: Semantic telecom validation (with full context)
    if not is_telecom_related(query, sector_name=sector_name, subprocess_name=subprocess_name):
        msg = (
            "I'm sorry, but I can only assist with **telecom-related** complaints "
            "(mobile, broadband, DTH, landline, enterprise telecom services). "
            "Your query doesn't appear to be telecom-related. Please try again with a telecom issue."
        )
        translated_msg = translate_text(msg, language)
        return jsonify({"resolution": translated_msg, "is_telecom": False})

    # Step 2: Semantic subprocess identification
    if subprocess_name == "Others":
        subprocess_name = identify_subprocess(query, sector_key)

    # Step 3: Generate resolution
    resolution = generate_resolution(query, sector_name, subprocess_name, language)

    return jsonify({
        "resolution": resolution,
        "is_telecom": True,
        "identified_subprocess": subprocess_name,
    })


@app.route("/api/detect-language", methods=["POST"])
def detect_lang():
    """Detect language from user text."""
    data = request.json
    text = data.get("text", "")
    language = detect_language(text)
    return jsonify({"language": language})


# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5500)
