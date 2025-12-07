import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
import base64
from datetime import datetime

load_dotenv()

MCP_SERVER = os.getenv("MCP_SERVER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI if API key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None

# Speech Recognizer
recognizer = sr.Recognizer()

st.set_page_config(page_title="MongoDB AI Admin with Voice", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
    }
    .voice-btn>button {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🧠 MongoDB AI Admin Panel (Voice-Enabled)</h1>', unsafe_allow_html=True)

def call(tool, args):
    """Call MCP server tool"""
    url = f"{MCP_SERVER}/tools/{tool}"
    res = requests.post(url, json=args)
    return res.json()

def convert_natural_language_to_query(natural_text, operation_type):
    """Use Gemini AI to convert natural language to MongoDB query"""
    if not model:
        st.warning("⚠️ Gemini API key not configured. Add GEMINI_API_KEY to .env file.")
        return None
    
    try:
        prompt = f"""
        Convert the following natural language command into a MongoDB query.
        
        Operation Type: {operation_type}
        Natural Language: {natural_text}
        
        Return ONLY valid JSON without any explanation, markdown, or code blocks.
        
        Examples:
        - "show all sellers" → {{}}
        - "find products with price greater than 100" → {{"price": {{"$gt": 100}}}}
        - "get items where type is Fruit" → {{"type": "Fruit"}}
        - "find sellers with name Raghav" → {{"seller": "Raghav Store"}}
        
        For UPDATE operations, return JSON with "filter" and "update" keys:
        - "update price to 150 for Apple" → {{"filter": {{"product": "Apple"}}, "update": {{"$set": {{"price": 150}}}}}}
        
        For INSERT operations, return the document structure:
        - "add new product Mango price 50" → {{"product": "Mango", "price": 50}}
        
        For DELETE operations, return the filter:
        - "delete items with no stock" → {{"no_of_items": 0}}
        
        Now convert: {natural_text}
        """
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean up markdown code blocks if present
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        # Parse and return JSON
        parsed = json.loads(result_text)
        return parsed
    except Exception as e:
        st.error(f"❌ AI conversion error: {str(e)}")
        return None

def speech_to_text_with_ai():
    """Record audio and convert to text with AI enhancement"""
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... (speak within 10 seconds)")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
        
        st.info("🔄 Processing audio...")
        
        # Basic recognition
        raw_text = recognizer.recognize_google(audio)
        st.success(f"✅ Recognized: {raw_text}")
        
        # AI Enhancement (optional)
        if model:
            try:
                enhancement_prompt = f"""
                Fix any errors in this voice transcription and return only the corrected text:
                "{raw_text}"
                """
                response = model.generate_content(enhancement_prompt)
                enhanced_text = response.text.strip().strip('"').strip("'")
                
                if enhanced_text != raw_text and len(enhanced_text) > 0:
                    st.info(f"✨ AI Enhanced: {enhanced_text}")
                    return enhanced_text
            except:
                pass
        
        return raw_text
        
    except sr.WaitTimeoutError:
        st.error("⏱️ No speech detected. Please try again.")
        return None
    except sr.UnknownValueError:
        st.error("🤷 Could not understand audio. Please speak more clearly.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None

def text_to_speech(text):
    """Convert text to speech and return audio player HTML"""
    try:
        os.makedirs("audio_files", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = f"audio_files/response_{timestamp}.mp3"
        
        # Clean text for speech
        clean_text = str(text).replace("{", "").replace("}", "").replace("[", "").replace("]", "")
        
        tts = gTTS(clean_text, lang='en')
        tts.save(audio_path)
        
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
        
        audio_html = f"""
        <audio controls autoplay style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """
        return audio_html
    except Exception as e:
        st.error(f"TTS Error: {e}")
        return None

# Sidebar
with st.sidebar:
    st.header("📋 Menu")
    page = st.radio("Select Operation", [
        "🔍 Query Documents",
        "➕ Insert Document",
        "✏️ Update Document",
        "❌ Delete Document",
    ])
    
    st.divider()
    
    st.header("⚙️ Settings")
    if model:
        st.success("✅ AI Enabled")
    else:
        st.warning("⚠️ AI Disabled (Add GEMINI_API_KEY to .env)")
    
    st.info(f"🌐 Server: {MCP_SERVER}")


# ---------------- QUERY DOCUMENTS ----------------
if page == "🔍 Query Documents":
    st.header("🔍 Query MongoDB Documents")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        collection = st.text_input("Collection Name:", value="seller")
    
    with col2:
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        if st.button("🎤 Voice", key="query_voice", help="Use voice command"):
            voice_text = speech_to_text_with_ai()
            if voice_text:
                query_data = convert_natural_language_to_query(voice_text, "QUERY")
                if query_data:
                    st.session_state['query_filter'] = json.dumps(query_data, indent=2)
    
    filter_json = st.text_area(
        "Filter JSON:", 
        value=st.session_state.get('query_filter', '{}'),
        height=150,
        help="MongoDB query filter or use voice command"
    )
    
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        run_query = st.button("▶️ Run Query", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state['query_filter'] = '{}'
            st.rerun()

    if run_query:
        if not collection.strip():
            st.error("❌ Please specify a collection name.")
        else:
            try:
                filt = json.loads(filter_json)
                with st.spinner("🔍 Querying database..."):
                    result = call("queryDocuments", {"collection": collection, "filter": filt})
                
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ Found {len(result) if isinstance(result, list) else 1} document(s)")
                    st.json(result)
                    
                    # Voice feedback
                    if model:
                        count = len(result) if isinstance(result, list) else 1
                        feedback = f"Found {count} documents in the {collection} collection"
                        audio_html = text_to_speech(feedback)
                        if audio_html:
                            st.markdown("🔊 **Voice Feedback:**")
                            st.markdown(audio_html, unsafe_allow_html=True)
                            
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format in Filter.")


# ---------------- INSERT DOCUMENT ----------------
elif page == "➕ Insert Document":
    st.header("➕ Insert New Document")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        collection = st.text_input("Collection Name:", value="seller")
    
    with col2:
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        if st.button("🎤 Voice", key="insert_voice", help="Use voice command"):
            voice_text = speech_to_text_with_ai()
            if voice_text:
                doc_data = convert_natural_language_to_query(voice_text, "INSERT")
                if doc_data:
                    st.session_state['insert_doc'] = json.dumps(doc_data, indent=2)
    
    doc = st.text_area(
        "Document JSON:", 
        value=st.session_state.get('insert_doc', '{"seller": "Store Name", "product": "Product Name", "type": "Category", "price": 100, "no_of_items": 10, "code": "CODE123"}'),
        height=200
    )
    
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        insert_btn = st.button("➕ Insert Document", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Clear", key="clear_insert", use_container_width=True):
            st.session_state['insert_doc'] = '{}'
            st.rerun()

    if insert_btn:
        if not collection.strip():
            st.error("❌ Please specify a collection name.")
        else:
            try:
                doc_json = json.loads(doc)
                with st.spinner("➕ Inserting document..."):
                    result = call("insertDocument", {"collection": collection, "document": doc_json})
                
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success("✅ Document inserted successfully!")
                    st.json(result)
                    
                    # Voice feedback
                    if model:
                        feedback = f"Successfully inserted document into {collection} collection"
                        audio_html = text_to_speech(feedback)
                        if audio_html:
                            st.markdown("🔊 **Voice Feedback:**")
                            st.markdown(audio_html, unsafe_allow_html=True)
                            
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format in Document.")


# ---------------- UPDATE DOCUMENT ----------------
elif page == "✏️ Update Document":
    st.header("✏️ Update Documents")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        collection = st.text_input("Collection Name:", value="seller")
    
    with col2:
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        if st.button("🎤 Voice", key="update_voice", help="Use voice command"):
            voice_text = speech_to_text_with_ai()
            if voice_text:
                update_data = convert_natural_language_to_query(voice_text, "UPDATE")
                if update_data and isinstance(update_data, dict):
                    if "filter" in update_data:
                        st.session_state['update_filter'] = json.dumps(update_data["filter"], indent=2)
                    if "update" in update_data:
                        st.session_state['update_update'] = json.dumps(update_data["update"], indent=2)
    
    filter_json = st.text_area(
        "Filter JSON:", 
        value=st.session_state.get('update_filter', '{"product": "Apple"}'),
        height=100
    )
    
    update_json = st.text_area(
        "Update JSON:", 
        value=st.session_state.get('update_update', '{"$set": {"price": 150}}'),
        height=100
    )
    
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        update_btn = st.button("✏️ Update Documents", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Clear", key="clear_update", use_container_width=True):
            st.session_state['update_filter'] = '{}'
            st.session_state['update_update'] = '{}'
            st.rerun()

    if update_btn:
        if not collection.strip():
            st.error("❌ Please specify a collection name.")
        else:
            try:
                filt = json.loads(filter_json)
                upd = json.loads(update_json)
                with st.spinner("✏️ Updating documents..."):
                    result = call("updateDocument", {"collection": collection, "filter": filt, "update": upd})
                
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ Updated {result.get('modified', 0)} document(s)")
                    st.json(result)
                    
                    # Voice feedback
                    if model:
                        count = result.get('modified', 0)
                        feedback = f"Updated {count} documents in the {collection} collection"
                        audio_html = text_to_speech(feedback)
                        if audio_html:
                            st.markdown("🔊 **Voice Feedback:**")
                            st.markdown(audio_html, unsafe_allow_html=True)
                            
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format.")


# ---------------- DELETE DOCUMENT ----------------
elif page == "❌ Delete Document":
    st.header("❌ Delete Documents")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        collection = st.text_input("Collection Name:", value="seller")
    
    with col2:
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        if st.button("🎤 Voice", key="delete_voice", help="Use voice command"):
            voice_text = speech_to_text_with_ai()
            if voice_text:
                delete_data = convert_natural_language_to_query(voice_text, "DELETE")
                if delete_data:
                    st.session_state['delete_filter'] = json.dumps(delete_data, indent=2)
    
    filter_json = st.text_area(
        "Filter JSON:", 
        value=st.session_state.get('delete_filter', '{"no_of_items": 0}'),
        height=150,
        help="⚠️ Be careful! This will delete matching documents permanently."
    )
    
    st.warning("⚠️ **Warning:** Deletion is permanent and cannot be undone!")
    
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        delete_btn = st.button("❌ Delete Documents", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Clear", key="clear_delete", use_container_width=True):
            st.session_state['delete_filter'] = '{}'
            st.rerun()

    if delete_btn:
        if not collection.strip():
            st.error("❌ Please specify a collection name.")
        else:
            try:
                filt = json.loads(filter_json)
                with st.spinner("❌ Deleting documents..."):
                    result = call("deleteDocument", {"collection": collection, "filter": filt})
                
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.warning(f"⚠️ Deleted {result.get('deleted', 0)} document(s)")
                    st.json(result)
                    
                    # Voice feedback
                    if model:
                        count = result.get('deleted', 0)
                        feedback = f"Deleted {count} documents from the {collection} collection"
                        audio_html = text_to_speech(feedback)
                        if audio_html:
                            st.markdown("🔊 **Voice Feedback:**")
                            st.markdown(audio_html, unsafe_allow_html=True)
                            
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format in Filter.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🎤 Voice-Enabled MongoDB Admin Panel | Powered by Gemini AI & MCP</p>
    <p><small>Click the 🎤 Voice button next to any field to use natural language commands</small></p>
</div>
""", unsafe_allow_html=True)
