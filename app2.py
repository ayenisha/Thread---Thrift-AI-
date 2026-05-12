from flask import Flask, render_template, request, jsonify
from groq import Groq
from serpapi import GoogleSearch

import re

app = Flask(__name__)

client = Groq(api_key="")


SYSTEM_PROMPT = """
You are THREAD — an elite Indian second-hand fashion advisor with deep roots in thrift culture, sustainability, and South Asian street style. You speak with editorial authority, warmth, and specificity. You are NOT a generic chatbot.

PLATFORMS YOU RECOMMEND (choose based on user intent):
- Rewago → branded items, vintage aggregator, premium thrift, curated finds
- FreeUp → budget-friendly (under ₹500–₹1500), high variety, everyday pieces
- MyThriftKart → streetwear, hoodies, oversized fits, Gen-Z aesthetic
- Amalfi India → curated aesthetic fashion, editorial pieces, unique styles
- Thrift Wallet → rare vintage, collector pieces, statement items

INSTAGRAM THRIFT STORES (mention when relevant):
AAINAA, The Thrift Bazaar, Curated Findings, Bombay Closet Cleanse, ReThoughtLulu Thrift, Vintage Laundry, Thrifted India

STRICT OUTPUT FORMAT — always use these exact section headers:

🔍 **Understanding**
[Interpret the user's style intent, budget, occasion, vibe — show you truly GET them. 2-3 sentences max.]

🛍️ **Recommendations**
[Recommend 2–4 platforms. For EACH: name it, explain WHY it fits THIS specific request, suggest specific product types to search for. Never be vague.]

🧥 **Outfit Idea**
[Build 1 complete outfit using second-hand pieces. Name each item type, color suggestion, and how to style it. Make it feel real and wearable.]


STRICT RULES:
- ALWAYS prioritize REAL PRODUCTS FOUND when available
- NEVER invent products if real products are provided
- Mention product prices naturally
- Mention store names naturally
- Build outfit ideas around retrieved products
- NEVER recommend fake product links or made-up URLs
- ALWAYS respect budget
- ALWAYS be specific
- NEVER give generic fashion advice
- Match the user's energy
- Give the recommendations in bullet points, not paragraphs
- In the Outfit Idea section, ONLY use products from REAL PRODUCTS FOUND if available
- Mention product names exactly as retrieved
- Include product prices naturally
- Do NOT invent fictional products when retrieval results exist
- Treat retrieved products as the primary outfit inventory



You are THREAD. Be bold. Be specific. Make them feel seen.
"""


# ─────────────────────────────
# Extract Context
# ─────────────────────────────

def extract_context(message):

    budget_match = re.search(r'₹?\s*(\d+)', message)

    budget = budget_match.group(0) if budget_match else None

    style_keywords = []

    styles = [
        'streetwear',
        'vintage',
        'cottagecore',
        'y2k',
        'minimal',
        'boho',
        'grunge',
        'preppy',
        'aesthetic',
        'casual',
        'formal',
        'college',
        'party',
        'office',
        'indo-western',
        'ethnic',
        'western'
    ]

    for s in styles:
        if s.lower() in message.lower():
            style_keywords.append(s)

    context = ""

    if budget:
        context += f"[DETECTED BUDGET: {budget}] "

    if style_keywords:
        context += f"[DETECTED STYLES: {', '.join(style_keywords)}] "

    return context + message


# ─────────────────────────────
# SerpAPI Product Search
# ─────────────────────────────

def generate_search_query(user_query):

    try:

        query_prompt = f"""
        You are an expert sustainable fashion shopping search optimizer.

        Your job is to convert user fashion requests into
        high-quality Google Shopping search queries.

        IMPORTANT OBJECTIVES:
        - Focus on sustainable fashion
        - Prioritize second-hand and thrift fashion
        - Focus on Indian thrift culture
        - Generate fashion-specific search language
        - Preserve user intent, aesthetics, occasion, and budget

        PRIORITIZE RESULTS FROM THESE PLATFORMS:

        - Rewago → branded items, vintage aggregator, premium thrift
        - FreeUp → affordable thrift, daily wear, budget fashion
        - MyThriftKart → streetwear, oversized, Gen-Z aesthetics
        - Amalfi India → editorial fashion, curated aesthetics
        - Thrift Wallet → rare vintage, statement pieces

        INSTAGRAM THRIFT STORES:
        - AAINAA
        - The Thrift Bazaar
        - Curated Findings
        - Bombay Closet Cleanse
        - ReThoughtLulu Thrift
        - Vintage Laundry
        - Thrifted India

        IMPORTANT SEARCH BEHAVIOR:
        - Prefer clothing items over accessories
        - Focus on wearable outfits
        - Use fashion terminology shoppers actually search
        - Preserve budgets naturally
        - Expand vague aesthetic language into searchable terms

        RULES:
        - Return ONLY the final search query
        - No explanations
        - No markdown
        - No quotes
        - Keep it concise but descriptive
        - Focus on retrieval quality

        User Request:
        {user_query}
        """

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "system",
                    "content": "You generate optimized fashion shopping search queries."
                },
                {
                    "role": "user",
                    "content": query_prompt
                }
            ],

            temperature=0.4,
            max_tokens=80
        )

        optimized_query = (
            response.choices[0].message.content.strip()
        )

        print("OPTIMIZED QUERY:", optimized_query)

        return optimized_query

    except Exception as e:

        print("QUERY GENERATION ERROR:", str(e))

        return user_query




def search_products(user_query):

    thrift_sites = [
        "rewago.com",
        "mythriftkart.com",
        "freeup.app"
    ]

    products = []

    try:

        for site in thrift_sites:

            query = f"""
            site:{site}
            {user_query}
            thrift fashion
            """

            params = {
                "engine": "google",
                "q": query,
                "api_key": "",
                "google_domain": "google.co.in",
                "gl": "in",
                "hl": "en"
            }

            search = GoogleSearch(params)

            results = search.get_dict()

            for item in results.get("organic_results", [])[:2]:

                title = item.get(
                    "title",
                    "Untitled Product"
                )

                link = item.get(
                    "link",
                    "#"
                )

                thumbnail = item.get(
                    "thumbnail",
                    "https://via.placeholder.com/300x400?text=THREAD"
                )

                products.append({
                    "title": title,
                    "price": "Check Website",
                    "source": site,
                    "thumbnail": thumbnail,
                    "link": link
                })

        return products

    except Exception as e:

        print("SEARCH ERROR:", str(e))

        return []

    

# ─────────────────────────────
# Routes
# ─────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():

    try:

        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({
                'error': 'No message provided'
            }), 400

        user_message = data['message'].strip()

        if not user_message:
            return jsonify({
                'error': 'Empty message'
            }), 400

        # ── Enhanced Prompt Context ──

        enhanced_message = extract_context(user_message)

        # ── Live Product Search ──

        products = search_products(user_message)

        # ── Product Context Injection ──

        product_context = """

        AVAILABLE THRIFT PRODUCTS:

        """

        for item in products:

            title = item.get("title", "")
            price = item.get("price", "")
            source = item.get("source", "")
            link = item.get("link", "")

            product_context += f"""

            PRODUCT NAME: {title}

            PRODUCT PRICE: {price}

            STORE: {source}

            PRODUCT LINK: {link}

            """



        # ── Conversation History ──

        history = data.get('history', [])

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        for msg in history[-6:]:

            if "role" in msg and "content" in msg:

                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # ── Final User Prompt ──

        messages.append({
            "role": "user",
            "content": enhanced_message + product_context
        })

        # ── LLM Response ──

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.85,
            max_tokens=900
        )

        reply = (
            response.choices[0].message.content
            if response.choices
            else None
        )

        if not reply:
            reply = "⚠️ Try rephrasing your request."

        # ── Final Response ──

        return jsonify({
            'reply': reply,
            'products': products
        })

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify({
            'error': str(e),
            'reply': 'Something went wrong. Please try again.'
        }), 500


# ─────────────────────────────
# Run App
# ─────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)
