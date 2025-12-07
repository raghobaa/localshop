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

st.set_page_config(page_title="Inventory Management", page_icon="📦", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton>button {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border-radius: 10px;
    }
    .voice-btn>button {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
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

def convert_voice_to_inventory_action(voice_text, username):
    """Convert natural language to inventory action"""
    if not model:
        return None
    
    prompt = f"""
    Convert this voice command into an inventory action for user '{username}'.
    
    Command: "{voice_text}"
    
    Return JSON with:
    - action: "ADD", "UPDATE", "DELETE", or "QUERY"
    - data: The product data or filter
    
    Examples:
    - "Add 50 packets of Milk price 60" -> {{ "action": "ADD", "data": {{ "productName": "Milk", "price": 60, "stock": 50, "category": "Dairy" }} }}
    - "Update price of Apple to 200" -> {{ "action": "UPDATE", "filter": {{ "productName": "Apple" }}, "update": {{ "price": 200 }} }}
    - "Delete items with 0 stock" -> {{ "action": "DELETE", "filter": {{ "stock": 0 }} }}
    - "Get all dairy products" -> {{ "action": "QUERY", "filter": {{ "category": "Dairy" }} }}
    - "Show items with less than 10 stock" -> {{ "action": "QUERY", "filter": {{ "stock": {{ "$lt": 10 }} }} }}
    - "List all my products" -> {{ "action": "QUERY", "filter": {{}} }}
    
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

# ---------------- MAIN APP LOGIC ----------------

# 1. Get Username from URL
query_params = st.query_params
username = query_params.get("username", None)

if not username:
    st.error("⚠️ No username provided! Please access this page from the Local Shop App.")
    st.info("Example URL: http://localhost:8508/?username=Raj")
    
    # Dev mode fallback
    st.divider()
    st.caption("👨‍💻 Developer Mode: Enter username manually")
    username = st.text_input("Enter Username")
    if not username:
        st.stop()

st.markdown(f'<h1 class="main-header">📦 Inventory: {username}</h1>', unsafe_allow_html=True)

# 2. Main Tabs
tab1, tab2, tab3 = st.tabs(["📋 Standard View", "➕ Add Product", "🎤 AI Voice Manager"])

# TAB 1: Standard Inventory View
with tab1:
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
            
    inventory = call_api("getInventory", {"username": username})
    
    if not inventory:
        st.info("📦 No products found. Add some!")
    else:
        for product in inventory:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                c1.markdown(f"**{product.get('productName', 'N/A')}**")
                c2.markdown(f"₹{product.get('price', 0)}")
                
                stock = product.get('stock', 0)
                color = "🟢" if stock > 50 else "🟡" if stock > 10 else "🔴"
                c3.markdown(f"{color} {stock}")
                
                c4.markdown(f"{product.get('category', 'Other')}")
                
                if c5.button("🗑️", key=f"del_{product['_id']}"):
                    call_api("deleteProduct", {"productId": str(product['_id'])})
                    st.rerun()
            st.divider()

# TAB 2: Add Product Form
with tab2:
    with st.form("add_product"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Product Name")
        price = c2.number_input("Price", min_value=0.0)
        stock = c1.number_input("Stock", min_value=0)
        cat = c2.selectbox("Category", ["Dairy", "Fruits", "Vegetables", "Snacks", "Other"])
        
        if st.form_submit_button("Add Product"):
            res = call_api("addProduct", {
                "username": username,
                "product": {
                    "productName": name,
                    "price": price,
                    "stock": stock,
                    "category": cat
                }
            })
            if res and res.get('success'):
                st.success("Added!")
                st.rerun()

# TAB 3: AI Voice Manager
with tab3:
    st.header("🎤 AI Voice Inventory Manager")
    st.info("Speak commands like: 'Add 50 packets of Milk price 60' or 'Delete items with 0 stock'")
    
    if st.button("🎤 Start Listening", key="voice_cmd"):
        text = speech_to_text_with_ai()
        if text:
            action_data = convert_voice_to_inventory_action(text, username)
            
            if action_data:
                action = action_data.get("action")
                data = action_data.get("data")
                
                st.json(action_data)
                
                if action == "ADD":
                    res = call_api("addProduct", {"username": username, "product": data})
                    if res.get('success'):
                        msg = f"Successfully added {data.get('productName')}"
                        st.success(msg)
                        st.markdown(text_to_speech(msg), unsafe_allow_html=True)
                        
                elif action == "DELETE":
                    # Logic to find and delete would go here
                    st.warning("Delete logic via voice to be implemented based on filter")
                    
                elif action == "QUERY":
                    # Fetch inventory with filter
                    # Note: getInventory tool currently only accepts username, so we filter in Python for now
                    # Ideally, update getInventory tool to accept a filter
                    
                    all_items = call_api("getInventory", {"username": username})
                    filter_criteria = action_data.get("filter", {})
                    
                    if not all_items:
                        st.info("No items found.")
                    else:
                        # Simple client-side filtering (basic implementation)
                        filtered_items = []
                        for item in all_items:
                            match = True
                            for key, value in filter_criteria.items():
                                # Handle simple equality checks
                                if key in item and item[key] != value:
                                    # Very basic support for MongoDB operators could be added here
                                    # For now, just exact match or skip complex queries
                                    if isinstance(value, dict):
                                        pass # Skip complex operators for client-side filter demo
                                    else:
                                        match = False
                            if match:
                                filtered_items.append(item)
                        
                        st.success(f"Found {len(filtered_items)} items matching your request:")
                        st.dataframe(filtered_items)
                        
                        # Voice feedback
                        msg = f"I found {len(filtered_items)} items."
                        st.markdown(text_to_speech(msg), unsafe_allow_html=True)
