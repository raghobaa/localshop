import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import os
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()

# Configure page settings
st.set_page_config(
    page_title="Gemini AI Poster Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Dark Mode and Styling
st.markdown("""
    <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        .stTextInput > div > div > input {
            background-color: #262730;
            color: #FAFAFA;
            border-radius: 10px;
            border: 1px solid #4B5563;
        }
        .stButton > button {
            background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        .poster-card {
            background-color: #1F2937;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-top: 20px;
        }
        .vlog-desc {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: #D1D5DB;
            margin-top: 15px;
            padding: 15px;
            background-color: #374151;
            border-radius: 10px;
            border-left: 4px solid #7C3AED;
        }
        .fb-btn {
            background-color: #1877F2;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            display: inline-block;
            font-weight: bold;
            text-decoration: none;
            margin-top: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize Gemini Client
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    st.error(f"Failed to initialize Gemini Client: {e}")
    st.stop()

# Header
st.title("🎨 AI Poster Generator")
st.markdown("Create stunning posters and vlog descriptions with **Gemini 2.5**")

# Input Section
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.text_input("Describe your poster idea...", placeholder="e.g., A futuristic nano banana dish in a neon-lit cyber cafe")
    with col2:
        generate_btn = st.button("Generate Magic ✨")

# Social & E-commerce Integration (Always Available)
st.markdown("---")
st.subheader("🚀 Quick Actions")
col_fb, col_shopify = st.columns(2)

with col_fb:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #1877F2 0%, #0C63D4 100%); padding: 20px; border-radius: 12px; text-align: center;'>
            <h4 style='color: white; margin-bottom: 10px;'>📘 Auto-Post to Facebook</h4>
            <p style='color: #E3F2FD; font-size: 14px;'>Share your products and promotions instantly</p>
        </div>
    """, unsafe_allow_html=True)
    
    fb_post_text = st.text_area("Facebook Post Content", placeholder="Write your post here... (emojis welcome! 🎉)", height=100)
    
    if st.button("Post to Facebook Now 🚀", key="fb_post"):
        if fb_post_text:
            # Mock Facebook posting (in production, use Facebook Graph API)
            fb_share_url = f"https://www.facebook.com/sharer/sharer.php?u=https://localshop.ai&quote={fb_post_text}"
            st.success("✅ Opening Facebook to post...")
            st.markdown(f'<meta http-equiv="refresh" content="0;url={fb_share_url}">', unsafe_allow_html=True)
            st.markdown(f"[Click here if not redirected]({fb_share_url})")
        else:
            st.warning("Please write something to post!")

with col_shopify:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #96BF48 0%, #5E8E3E 100%); padding: 20px; border-radius: 12px; text-align: center;'>
            <h4 style='color: white; margin-bottom: 10px;'>🛍️ Sell on Shopify</h4>
            <p style='color: #F1F8E9; font-size: 14px;'>List your products on Shopify marketplace</p>
        </div>
    """, unsafe_allow_html=True)
    
    product_name = st.text_input("Product Name", placeholder="e.g., Handmade Pottery Set")
    product_price = st.number_input("Price (₹)", min_value=0, value=999, step=50)
    
    if st.button("List on Shopify 🛒", key="shopify_list"):
        if product_name:
            # Mock Shopify integration (in production, use Shopify Admin API)
            shopify_url = f"https://www.shopify.com/admin/products/new?title={product_name}&price={product_price}"
            st.success(f"✅ Product '{product_name}' ready to list!")
            st.info("In production, this would create a product via Shopify API")
            st.markdown(f"[Open Shopify Admin]({shopify_url})")
        else:
            st.warning("Please enter a product name!")

st.markdown("---")
st.subheader("🎨 AI Poster Generation")

# Generation Logic
if generate_btn and prompt:
    with st.spinner("Gemini is dreaming up your poster..."):
        try:
            # 1. Generate Image
            # Using gemini-2.0-flash-exp which supports image generation
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
            )
            
            generated_image = None
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        generated_image = Image.open(io.BytesIO(part.inline_data.data))
                        break
            
            # 2. Generate Vlog Description
            text_response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[f"Write a catchy, short vlog-style description for a Facebook post about this image: {prompt}. Include emojis and hashtags."]
            )
            vlog_description = text_response.text

            # Display Results
            if generated_image:
                st.markdown("<div class='poster-card'>", unsafe_allow_html=True)
                st.image(generated_image, caption="Generated by Gemini", use_container_width=True)
                
                st.markdown(f"""
                    <div class='vlog-desc'>
                        {vlog_description}
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                    <a href="https://www.facebook.com/sharer/sharer.php?u=https://localshop.ai" target="_blank" class="fb-btn">
                        Share on Facebook 📘
                    </a>
                """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.error("No image was generated. Please try a different prompt.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.info("Tip: Ensure your API key has access to the Gemini 2.5/2.0 Flash models.")
