import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
import base64

load_dotenv()

MCP_SERVER = os.getenv("MCP_SERVER", "http://localhost:3000")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None

# Speech Recognizer
recognizer = sr.Recognizer()

st.set_page_config(page_title="Product Recommendations", page_icon="🎯", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #FF6B6B 0%, #4ECDC4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .product-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stat-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        color: white;
    }
    .recommendation-score {
        background: rgba(255,255,255,0.2);
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF6B6B 0%, #4ECDC4 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- HELPER FUNCTIONS ----------------

def call_api(tool, args):
    """Call MCP server API"""
    try:
        url = f"{MCP_SERVER}/tools/{tool}"
        res = requests.post(url, json=args)
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def speech_to_text_with_ai():
    """Record audio and convert to text with AI enhancement"""
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... (speak within 10 seconds)")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
        
        st.info("🔄 Processing audio...")
        raw_text = recognizer.recognize_google(audio)
        st.success(f"✅ Recognized: {raw_text}")
        
        if model:
            enhancement_prompt = f"""
            Fix any errors in this voice transcription and return only the corrected text:
            "{raw_text}"
            """
            response = model.generate_content(enhancement_prompt)
            enhanced_text = response.text.strip().strip('"')
            if enhanced_text != raw_text:
                st.info(f"✨ AI Enhanced: {enhanced_text}")
                return enhanced_text
        return raw_text
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None

def convert_voice_to_search(voice_text):
    """Convert natural language to product search"""
    if not model:
        return None
    
    prompt = f"""
    Convert this voice command into a product search query.
    
    Command: "{voice_text}"
    
    Return JSON with:
    - action: "RECOMMEND", "SEARCH_CATEGORY", "SEARCH_PRICE", or "PURCHASE_HISTORY"
    - category: product category if mentioned
    - maxPrice: maximum price if mentioned
    - minPrice: minimum price if mentioned
    
    Examples:
    - "Show me dairy products" -> {{"action": "SEARCH_CATEGORY", "category": "Dairy"}}
    - "Find items under 100 rupees" -> {{"action": "SEARCH_PRICE", "maxPrice": 100}}
    - "What have I bought before" -> {{"action": "PURCHASE_HISTORY"}}
    - "Recommend products for me" -> {{"action": "RECOMMEND"}}
    
    Return ONLY JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

def text_to_speech(text):
    """Convert text to speech"""
    try:
        os.makedirs("audio_files", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = f"audio_files/response_{timestamp}.mp3"
        tts = gTTS(str(text), lang='en')
        tts.save(audio_path)
        with open(audio_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
        return f"""
        <audio controls autoplay style="width: 100%;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    except:
        return None

def get_ai_recommendation_explanation(purchases, recommendations):
    """Get AI explanation for recommendations"""
    if not model or not purchases:
        return "Based on popular items in our inventory."
    
    try:
        purchase_summary = ", ".join([f"{p.get('productName')} ({p.get('category')})" for p in purchases[:5]])
        rec_summary = ", ".join([f"{r.get('productName')}" for r in recommendations[:3]])
        
        prompt = f"""
        You are a shopping assistant. Explain why these products are recommended.
        
        User's recent purchases: {purchase_summary}
        Recommended products: {rec_summary}
        
        Provide a friendly, concise explanation (2-3 sentences) of why these recommendations make sense.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "These products match your shopping preferences."

def get_current_season():
    """Determine current season based on month"""
    from datetime import datetime
    month = datetime.now().month
    
    # Indian seasons
    if month in [12, 1, 2]:
        return "Winter", "❄️"
    elif month in [3, 4, 5]:
        return "Summer", "☀️"
    elif month in [6, 7, 8, 9]:
        return "Monsoon", "🌧️"
    else:  # 10, 11
        return "Autumn", "🍂"

def get_upcoming_festivals():
    """Get upcoming festivals based on current date"""
    from datetime import datetime
    month = datetime.now().month
    day = datetime.now().day
    
    festivals = []
    
    # Major Indian festivals (approximate dates)
    festival_calendar = {
        1: [(1, "New Year", "🎊"), (14, "Makar Sankranti", "🪁"), (26, "Republic Day", "🇮🇳")],
        2: [(14, "Valentine's Day", "💝")],
        3: [(8, "Holi", "🎨")],
        4: [(14, "Ugadi/Baisakhi", "🌸")],
        5: [(1, "May Day", "🌺")],
        6: [],
        7: [],
        8: [(15, "Independence Day", "🇮🇳"), (26, "Janmashtami", "🦚")],
        9: [(5, "Teachers Day", "📚")],
        10: [(2, "Gandhi Jayanti", "🕊️"), (15, "Dussehra", "🏹"), (24, "Diwali", "🪔")],
        11: [(14, "Children's Day", "🎈")],
        12: [(25, "Christmas", "🎄"), (31, "New Year's Eve", "🎆")]
    }
    
    # Get festivals for current and next month
    for fest_month in [month, (month % 12) + 1]:
        if fest_month in festival_calendar:
            for fest_day, fest_name, fest_emoji in festival_calendar[fest_month]:
                # Show festivals within next 30 days
                if fest_month == month and fest_day >= day:
                    days_until = fest_day - day
                    festivals.append((fest_name, fest_emoji, days_until))
                elif fest_month == (month % 12) + 1:
                    days_until = (30 - day) + fest_day
                    if days_until <= 30:
                        festivals.append((fest_name, fest_emoji, days_until))
    
    return festivals[:3]  # Return top 3 upcoming festivals

def get_seasonal_products(season):
    """Get product categories relevant to the season"""
    seasonal_map = {
        "Winter": ["Dairy", "Snacks"],  # Hot milk, warm snacks
        "Summer": ["Fruits", "Dairy"],  # Fresh fruits, cold drinks
        "Monsoon": ["Snacks", "Vegetables"],  # Hot snacks, fresh vegetables
        "Autumn": ["Fruits", "Vegetables"]  # Seasonal produce
    }
    return seasonal_map.get(season, ["Fruits", "Vegetables"])

def get_festival_products(festival_name):
    """Get product categories relevant to the festival"""
    festival_map = {
        "Diwali": ["Snacks", "Dairy"],  # Sweets and milk products
        "Holi": ["Snacks", "Dairy"],  # Sweets and drinks
        "Christmas": ["Fruits", "Snacks"],  # Fruits and treats
        "New Year": ["Fruits", "Dairy"],  # Fresh start foods
        "Janmashtami": ["Dairy"],  # Milk products
        "Ugadi": ["Fruits", "Vegetables"],  # Traditional items
        "Makar Sankranti": ["Snacks"],  # Til and jaggery items
        "Independence Day": ["Snacks"],  # Celebration foods
        "Republic Day": ["Snacks"],  # Celebration foods
    }
    
    for key in festival_map:
        if key in festival_name:
            return festival_map[key]
    return []

def get_ai_seasonal_recommendations(username, season, festivals):
    """Get AI-enhanced seasonal and festival recommendations"""
    if not model:
        return None
    
    try:
        festival_text = ", ".join([f"{name} in {days} days" for name, _, days in festivals]) if festivals else "no major festivals"
        
        prompt = f"""
        Generate product recommendations for a user considering:
        - Current season: {season}
        - Upcoming festivals: {festival_text}
        - User: {username}
        
        Suggest 3-5 product categories or specific items that would be relevant.
        Consider Indian context and seasonal preferences.
        
        Return as a JSON array of objects with "category" and "reason" fields.
        Example: [{{"category": "Dairy", "reason": "Fresh milk products are popular in winter"}}]
        
        Return ONLY valid JSON.
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except:
        return None

def get_chatbot_response(user_message, username, purchase_history, recommendations, season_name, upcoming_festivals):
    """Get AI chatbot response with context about user's shopping"""
    if not model:
        return "Sorry, AI chatbot is not available. Please configure GEMINI_API_KEY."
    
    try:
        # Build context
        context_parts = []
        
        # User context
        context_parts.append(f"User: {username}")
        
        # Purchase history context
        if purchase_history and len(purchase_history) > 0:
            recent_purchases = ", ".join([p.get('productName', '') for p in purchase_history[:5]])
            categories = set([p.get('category') for p in purchase_history if p.get('category')])
            total_spent = sum([p.get('price', 0) for p in purchase_history])
            context_parts.append(f"Recent purchases: {recent_purchases}")
            context_parts.append(f"Favorite categories: {', '.join(categories)}")
            context_parts.append(f"Total spent: ₹{total_spent}")
        else:
            context_parts.append("No purchase history yet")
        
        # Recommendations context
        if recommendations and len(recommendations) > 0:
            rec_products = ", ".join([r.get('productName', '') for r in recommendations[:3]])
            context_parts.append(f"Current recommendations: {rec_products}")
        
        # Seasonal context
        context_parts.append(f"Current season: {season_name}")
        if upcoming_festivals:
            fest_names = ", ".join([f"{name} (in {days} days)" for name, _, days in upcoming_festivals[:2]])
            context_parts.append(f"Upcoming festivals: {fest_names}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""
You are a helpful shopping assistant for an online grocery/product store.

User Context:
{context}

User Question: {user_message}

Provide a helpful, friendly response. You can:
- Recommend products based on their history
- Suggest seasonal or festival items
- Answer questions about their purchases
- Help them find specific products
- Provide shopping tips

Keep responses concise (2-4 sentences) and actionable.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# ---------------- MAIN APP LOGIC ----------------

# Get Username from URL
query_params = st.query_params
username = query_params.get("username", None)

if not username:
    st.error("⚠️ No username provided! Please access this page with a username parameter.")
    st.info("Example URL: http://localhost:8503/?username=TestUser")
    
    # Dev mode fallback
    st.divider()
    st.caption("👨‍💻 Developer Mode: Enter username manually")
    username = st.text_input("Enter Username")
    if not username:
        st.stop()

st.markdown(f'<h1 class="main-header">🎯 Recommendations for {username}</h1>', unsafe_allow_html=True)

# Fetch user data
purchase_history = call_api("getPurchaseHistory", {"username": username, "limit": 50})
recommendations = call_api("getRecommendations", {"username": username, "limit": 10})

# Get seasonal data
season_name, season_emoji = get_current_season()
upcoming_festivals = get_upcoming_festivals()

# Initialize chatbot session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_input' not in st.session_state:
    st.session_state.chat_input = ""

# Statistics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-box">
        <h3>{len(purchase_history) if purchase_history else 0}</h3>
        <p>Total Purchases</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if purchase_history:
        categories = set([p.get('category') for p in purchase_history if p.get('category')])
        st.markdown(f"""
        <div class="stat-box">
            <h3>{len(categories)}</h3>
            <p>Categories Explored</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="stat-box">
            <h3>0</h3>
            <p>Categories Explored</p>
        </div>
        """, unsafe_allow_html=True)

with col3:
    if purchase_history:
        total_spent = sum([p.get('price', 0) for p in purchase_history])
        st.markdown(f"""
        <div class="stat-box">
            <h3>₹{total_spent:.0f}</h3>
            <p>Total Spent</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="stat-box">
            <h3>₹0</h3>
            <p>Total Spent</p>
        </div>
        """, unsafe_allow_html=True)

with col4:
    if recommendations:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{len(recommendations)}</h3>
            <p>New Recommendations</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="stat-box">
            <h3>0</h3>
            <p>New Recommendations</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Seasonal & Festival Section
st.subheader(f"{season_emoji} Seasonal & Festival Recommendations")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 15px; color: white; text-align: center;'>
        <h2>{season_emoji}</h2>
        <h3>{season_name} Season</h3>
        <p>Perfect time for {', '.join(get_seasonal_products(season_name))}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if upcoming_festivals:
        st.markdown("### 🎉 Upcoming Festivals")
        for fest_name, fest_emoji, days_until in upcoming_festivals:
            if days_until == 0:
                st.info(f"{fest_emoji} **{fest_name}** - Today!")
            elif days_until == 1:
                st.info(f"{fest_emoji} **{fest_name}** - Tomorrow!")
            else:
                st.info(f"{fest_emoji} **{fest_name}** - in {days_until} days")
            
            # Show relevant products for the festival
            festival_categories = get_festival_products(fest_name)
            if festival_categories:
                st.caption(f"📦 Recommended: {', '.join(festival_categories)}")
    else:
        st.info("🎊 No major festivals in the next 30 days")

# AI Seasonal Recommendations
if model:
    with st.expander("🤖 AI Seasonal Insights", expanded=False):
        ai_seasonal = get_ai_seasonal_recommendations(username, season_name, upcoming_festivals)
        if ai_seasonal:
            st.markdown("**AI suggests these categories for you:**")
            for item in ai_seasonal:
                st.markdown(f"- **{item.get('category')}**: {item.get('reason')}")
        else:
            st.info("AI insights unavailable")

st.divider()

# Main Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🎯 For You", "🎊 Seasonal & Festivals", "📜 Purchase History", "🏪 By Category", "🎤 Voice Search", "💬 AI Chatbot"])

# TAB 1: Personalized Recommendations
with tab1:
    st.header("🎯 Recommended For You")
    
    if recommendations and len(recommendations) > 0:
        # AI Explanation
        if model and purchase_history:
            explanation = get_ai_recommendation_explanation(purchase_history, recommendations)
            st.info(f"💡 **Why these recommendations?** {explanation}")
        
        # Display recommendations
        for rec in recommendations:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"### {rec.get('productName', 'Unknown')}")
                st.caption(f"🏪 Seller: {rec.get('username', 'N/A')} | 📦 Category: {rec.get('category', 'Other')}")
                st.caption(f"💬 {rec.get('reason', 'Recommended for you')}")
            
            with col2:
                st.markdown(f"**₹{rec.get('price', 0):.2f}**")
            
            with col3:
                stock = rec.get('stock', 0)
                color = "🟢" if stock > 50 else "🟡" if stock > 10 else "🔴"
                st.markdown(f"{color} {stock} left")
            
            with col4:
                score = rec.get('recommendationScore', 0.5)
                st.markdown(f"⭐ {score:.1f}")
                
                # Purchase button
                if st.button("🛒 Buy", key=f"buy_{rec.get('_id')}"):
                    purchase_result = call_api("recordPurchase", {
                        "username": username,
                        "productId": str(rec.get('_id')),
                        "productName": rec.get('productName'),
                        "category": rec.get('category'),
                        "sellerType": rec.get('category'),  # Using category as seller type for now
                        "seller": rec.get('username'),
                        "price": rec.get('price')
                    })
                    
                    if purchase_result and purchase_result.get('success'):
                        st.success(f"✅ Purchased {rec.get('productName')}!")
                        st.rerun()
            
            st.divider()
    else:
        st.info("📦 No recommendations available yet. Start shopping to get personalized suggestions!")
        
        # Show some popular items
        st.subheader("🔥 Popular Items")
        all_products = call_api("queryDocuments", {"collection": "inventory", "filter": {"stock": {"$gt": 0}}})
        
        if all_products and len(all_products) > 0:
            for product in all_products[:5]:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{product.get('productName', 'Unknown')}**")
                    st.caption(f"Category: {product.get('category', 'Other')}")
                with col2:
                    st.markdown(f"₹{product.get('price', 0)}")
                with col3:
                    if st.button("🛒 Buy", key=f"popular_{product.get('_id')}"):
                        call_api("recordPurchase", {
                            "username": username,
                            "productId": str(product.get('_id')),
                            "productName": product.get('productName'),
                            "category": product.get('category'),
                            "sellerType": product.get('category'),
                            "seller": product.get('username'),
                            "price": product.get('price')
                        })
                        st.success("✅ Purchase recorded!")
                        st.rerun()
                st.divider()

# TAB 2: Seasonal & Festival Recommendations
with tab2:
    st.header(f"{season_emoji} Seasonal & Festival Recommendations")
    
    # Current Season Section
    st.subheader(f"{season_emoji} {season_name} Specials")
    st.info(f"It's {season_name} season! Here are products perfect for this time of year.")
    
    seasonal_categories = get_seasonal_products(season_name)
    
    for category in seasonal_categories:
        with st.expander(f"📦 {category} Products", expanded=True):
            products = call_api("getProductsByCategory", {
                "category": category,
                "excludeUsername": username,
                "limit": 10
            })
            
            if products and len(products) > 0:
                for product in products:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{product.get('productName', 'Unknown')}**")
                        st.caption(f"🏪 {product.get('username', 'N/A')}")
                    
                    with col2:
                        st.markdown(f"₹{product.get('price', 0):.2f}")
                    
                    with col3:
                        stock = product.get('stock', 0)
                        color = "🟢" if stock > 50 else "🟡" if stock > 10 else "🔴"
                        st.markdown(f"{color} {stock}")
                    
                    with col4:
                        if st.button("🛒 Buy", key=f"seasonal_{category}_{product.get('_id')}"):
                            call_api("recordPurchase", {
                                "username": username,
                                "productId": str(product.get('_id')),
                                "productName": product.get('productName'),
                                "category": product.get('category'),
                                "sellerType": product.get('category'),
                                "seller": product.get('username'),
                                "price": product.get('price')
                            })
                            st.success("✅ Purchase recorded!")
                            st.rerun()
                    
                    st.divider()
            else:
                st.caption(f"No {category} products available right now")
    
    # Festival Section
    if upcoming_festivals:
        st.divider()
        st.subheader("🎉 Festival Specials")
        
        for fest_name, fest_emoji, days_until in upcoming_festivals:
            with st.expander(f"{fest_emoji} {fest_name} ({days_until} days away)", expanded=True):
                festival_categories = get_festival_products(fest_name)
                
                if festival_categories:
                    st.info(f"Stock up for {fest_name}! Recommended categories: {', '.join(festival_categories)}")
                    
                    for category in festival_categories:
                        st.markdown(f"**{category} for {fest_name}:**")
                        
                        products = call_api("getProductsByCategory", {
                            "category": category,
                            "excludeUsername": username,
                            "limit": 5
                        })
                        
                        if products and len(products) > 0:
                            for product in products:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                
                                with col1:
                                    st.markdown(f"• **{product.get('productName')}** - {product.get('username')}")
                                
                                with col2:
                                    st.markdown(f"₹{product.get('price', 0):.2f}")
                                
                                with col3:
                                    if st.button("🛒", key=f"festival_{fest_name}_{product.get('_id')}"):
                                        call_api("recordPurchase", {
                                            "username": username,
                                            "productId": str(product.get('_id')),
                                            "productName": product.get('productName'),
                                            "category": product.get('category'),
                                            "sellerType": product.get('category'),
                                            "seller": product.get('username'),
                                            "price": product.get('price')
                                        })
                                        st.success(f"✅ Ready for {fest_name}!")
                                        st.rerun()
                        else:
                            st.caption(f"No {category} products available")
                        
                        st.divider()
                else:
                    st.caption(f"Enjoy {fest_name}!")
    
    # AI Seasonal Insights
    if model:
        st.divider()
        st.subheader("🤖 AI Seasonal Insights")
        
        ai_seasonal = get_ai_seasonal_recommendations(username, season_name, upcoming_festivals)
        if ai_seasonal:
            st.success("Based on the current season and upcoming festivals, AI recommends:")
            for item in ai_seasonal:
                st.markdown(f"### {item.get('category')}")
                st.caption(f"💡 {item.get('reason')}")
                
                # Fetch products for this category
                products = call_api("getProductsByCategory", {
                    "category": item.get('category'),
                    "excludeUsername": username,
                    "limit": 3
                })
                
                if products:
                    for p in products:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**{p.get('productName')}**")
                        with col2:
                            st.markdown(f"₹{p.get('price')}")
                        with col3:
                            if st.button("🛒", key=f"ai_seasonal_{p.get('_id')}"):
                                call_api("recordPurchase", {
                                    "username": username,
                                    "productId": str(p.get('_id')),
                                    "productName": p.get('productName'),
                                    "category": p.get('category'),
                                    "sellerType": p.get('category'),
                                    "seller": p.get('username'),
                                    "price": p.get('price')
                                })
                                st.success("✅ Purchase recorded!")
                                st.rerun()
                st.divider()

# TAB 3: Purchase History
with tab3:
    st.header("📜 Your Purchase History")
    
    if purchase_history and len(purchase_history) > 0:
        # Category breakdown
        categories = {}
        for p in purchase_history:
            cat = p.get('category', 'Other')
            categories[cat] = categories.get(cat, 0) + 1
        
        st.subheader("📊 Category Breakdown")
        cols = st.columns(len(categories))
        for idx, (cat, count) in enumerate(categories.items()):
            with cols[idx]:
                st.metric(cat, count)
        
        st.divider()
        st.subheader("🛍️ Recent Purchases")
        
        for purchase in purchase_history:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{purchase.get('productName', 'Unknown')}**")
                st.caption(f"🏪 {purchase.get('seller', 'N/A')} | 📦 {purchase.get('category', 'Other')}")
            
            with col2:
                st.markdown(f"₹{purchase.get('price', 0):.2f}")
            
            with col3:
                date = purchase.get('purchaseDate')
                if date:
                    if isinstance(date, str):
                        st.caption(date[:10])
                    else:
                        st.caption(date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date))
            
            st.divider()
    else:
        st.info("📦 No purchase history yet. Start shopping to see your purchases here!")

# TAB 4: Browse by Category
with tab4:
    st.header("🏪 Browse by Category")
    
    categories = ["Dairy", "Fruits", "Vegetables", "Snacks", "Other"]
    selected_category = st.selectbox("Select Category", categories)
    
    if st.button("🔍 Search", key="category_search"):
        products = call_api("getProductsByCategory", {
            "category": selected_category,
            "excludeUsername": username,
            "limit": 20
        })
        
        if products and len(products) > 0:
            st.success(f"Found {len(products)} products in {selected_category}")
            
            for product in products:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{product.get('productName', 'Unknown')}**")
                    st.caption(f"🏪 Seller: {product.get('username', 'N/A')}")
                
                with col2:
                    st.markdown(f"₹{product.get('price', 0):.2f}")
                
                with col3:
                    stock = product.get('stock', 0)
                    color = "🟢" if stock > 50 else "🟡" if stock > 10 else "🔴"
                    st.markdown(f"{color} {stock}")
                
                with col4:
                    if st.button("🛒 Buy", key=f"cat_{product.get('_id')}"):
                        call_api("recordPurchase", {
                            "username": username,
                            "productId": str(product.get('_id')),
                            "productName": product.get('productName'),
                            "category": product.get('category'),
                            "sellerType": product.get('category'),
                            "seller": product.get('username'),
                            "price": product.get('price')
                        })
                        st.success("✅ Purchase recorded!")
                        st.rerun()
                
                st.divider()
        else:
            st.warning(f"No products found in {selected_category}")

# TAB 5: Voice Search
with tab5:
    st.header("🎤 Voice-Powered Product Search")
    st.info("Try saying: 'Show me dairy products' or 'Find items under 100 rupees' or 'What have I bought before'")
    
    if st.button("🎤 Start Voice Search", key="voice_search"):
        voice_text = speech_to_text_with_ai()
        
        if voice_text:
            search_data = convert_voice_to_search(voice_text)
            
            if search_data:
                action = search_data.get("action")
                
                if action == "RECOMMEND":
                    st.info("🎯 Fetching personalized recommendations...")
                    recs = call_api("getRecommendations", {"username": username, "limit": 5})
                    
                    if recs:
                        st.success(f"Found {len(recs)} recommendations!")
                        for rec in recs:
                            st.markdown(f"**{rec.get('productName')}** - ₹{rec.get('price')} ({rec.get('reason')})")
                        
                        msg = f"I found {len(recs)} recommendations for you"
                        audio = text_to_speech(msg)
                        if audio:
                            st.markdown(audio, unsafe_allow_html=True)
                
                elif action == "SEARCH_CATEGORY":
                    category = search_data.get("category")
                    st.info(f"🔍 Searching for {category} products...")
                    
                    products = call_api("getProductsByCategory", {
                        "category": category,
                        "excludeUsername": username,
                        "limit": 10
                    })
                    
                    if products:
                        st.success(f"Found {len(products)} {category} products!")
                        for p in products:
                            st.markdown(f"**{p.get('productName')}** - ₹{p.get('price')} (Stock: {p.get('stock')})")
                        
                        msg = f"I found {len(products)} {category} products"
                        audio = text_to_speech(msg)
                        if audio:
                            st.markdown(audio, unsafe_allow_html=True)
                
                elif action == "PURCHASE_HISTORY":
                    st.info("📜 Fetching your purchase history...")
                    
                    if purchase_history:
                        st.success(f"You have {len(purchase_history)} purchases!")
                        for p in purchase_history[:10]:
                            st.markdown(f"**{p.get('productName')}** - ₹{p.get('price')} ({p.get('category')})")
                        
                        msg = f"You have made {len(purchase_history)} purchases"
                        audio = text_to_speech(msg)
                        if audio:
                            st.markdown(audio, unsafe_allow_html=True)
                    else:
                        st.info("No purchase history found")
                
                elif action == "SEARCH_PRICE":
                    max_price = search_data.get("maxPrice", 1000)
                    st.info(f"🔍 Searching for products under ₹{max_price}...")
                    
                    all_products = call_api("queryDocuments", {
                        "collection": "inventory",
                        "filter": {"price": {"$lte": max_price}, "stock": {"$gt": 0}}
                    })
                    
                    if all_products:
                        # Exclude user's own products
                        filtered = [p for p in all_products if p.get('username') != username]
                        st.success(f"Found {len(filtered)} products under ₹{max_price}!")
                        
                        for p in filtered[:10]:
                            st.markdown(f"**{p.get('productName')}** - ₹{p.get('price')} ({p.get('category')})")
                        
                        msg = f"I found {len(filtered)} products under {max_price} rupees"
                        audio = text_to_speech(msg)
                        if audio:
                            st.markdown(audio, unsafe_allow_html=True)

# TAB 6: AI Chatbot
with tab6:
    st.header("💬 AI Shopping Assistant")
    st.info("Ask me anything about products, recommendations, your purchases, or shopping tips!")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        if len(st.session_state.chat_history) == 0:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px;'>
                <h3>👋 Hello! I'm your AI Shopping Assistant</h3>
                <p>I can help you with:</p>
                <ul>
                    <li>🎯 Product recommendations based on your history</li>
                    <li>🎊 Seasonal and festival shopping suggestions</li>
                    <li>📊 Information about your purchases</li>
                    <li>🔍 Finding specific products</li>
                    <li>💡 Shopping tips and advice</li>
                </ul>
                <p><strong>Try asking me something!</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display conversation history
        for i, (role, message) in enumerate(st.session_state.chat_history):
            if role == "user":
                st.markdown(f"""
                <div style='background: #e3f2fd; padding: 15px; border-radius: 10px; 
                            margin: 10px 0; border-left: 4px solid #2196F3;'>
                    <strong>You:</strong> {message}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background: #f3e5f5; padding: 15px; border-radius: 10px; 
                            margin: 10px 0; border-left: 4px solid #9C27B0;'>
                    <strong>🤖 Assistant:</strong> {message}
                </div>
                """, unsafe_allow_html=True)
    
    # Suggested questions
    if len(st.session_state.chat_history) == 0:
        st.subheader("💡 Suggested Questions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 What should I buy?", use_container_width=True):
                user_msg = "What products do you recommend for me?"
                st.session_state.chat_history.append(("user", user_msg))
                bot_response = get_chatbot_response(user_msg, username, purchase_history, 
                                                    recommendations, season_name, upcoming_festivals)
                st.session_state.chat_history.append(("assistant", bot_response))
                st.rerun()
        
        with col2:
            if st.button("🎊 Festival shopping?", use_container_width=True):
                user_msg = "What should I buy for upcoming festivals?"
                st.session_state.chat_history.append(("user", user_msg))
                bot_response = get_chatbot_response(user_msg, username, purchase_history, 
                                                    recommendations, season_name, upcoming_festivals)
                st.session_state.chat_history.append(("assistant", bot_response))
                st.rerun()
        
        with col3:
            if st.button("📊 My shopping stats?", use_container_width=True):
                user_msg = "Tell me about my shopping history"
                st.session_state.chat_history.append(("user", user_msg))
                bot_response = get_chatbot_response(user_msg, username, purchase_history, 
                                                    recommendations, season_name, upcoming_festivals)
                st.session_state.chat_history.append(("assistant", bot_response))
                st.rerun()
    
    # Chat input
    st.divider()
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your message...", 
            key="chat_input_field",
            placeholder="Ask me anything about products, recommendations, or shopping..."
        )
    
    with col2:
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        send_button = st.button("Send 📤", use_container_width=True)
    
    if send_button and user_input.strip():
        # Add user message to history
        st.session_state.chat_history.append(("user", user_input))
        
        # Get bot response
        bot_response = get_chatbot_response(
            user_input, 
            username, 
            purchase_history, 
            recommendations,
            season_name,
            upcoming_festivals
        )
        
        # Add bot response to history
        st.session_state.chat_history.append(("assistant", bot_response))
        
        # Rerun to update chat display
        st.rerun()
    
    # Clear chat button
    if len(st.session_state.chat_history) > 0:
        st.divider()
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🎯 AI-Powered Product Recommendations | Powered by Gemini AI & MCP</p>
    <p><small>Recommendations based on your purchase history, seasons, and festivals</small></p>
</div>
""", unsafe_allow_html=True)
