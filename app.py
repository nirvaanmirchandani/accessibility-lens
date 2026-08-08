import streamlit as st
from pypdf import PdfReader
from openai import OpenAI
from gtts import gTTS
import io

api_key = st.secrets.get("GEMINI_API_KEY")
client = None

if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    
# ==========================================
# 1. PAGE & ACCESSIBILITY STYLING
# ==========================================
st.set_page_config(
    page_title="Accessibility Lens",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)
with st.sidebar:
    st.title("⚙️ Controls")
    uploaded_file = st.file_uploader("📁 Upload PDF", type=["pdf"])
    
    # Dynamic text scaling controls
    font_size = st.slider("Font Size ", min_value=16, max_value=32, value=22, step=2)
    bold_size = font_size 
    
    st.divider()
    st.info("💡 **Tip:** Use the Bionic Reader tab to bold key word anchors and improve reading speed.")
# Custom High-Contrast & Readable CSS
# Custom High-Contrast & Readable CSS
# Custom High-Contrast & Dynamic CSS
st.markdown(f"""
<style>
    @import url('https://fonts.cdnfonts.com/css/opendyslexic');

    .stApp {{
        background-color: #121212;
        color: #f5e6c8;
        font-family: 'OpenDyslexic', sans-serif !important;
        font-size: 18px;
        line-height: 1.8;
    }}

    h1, h2, h3 {{
        color: #ffd700 !important;
        font-family: 'OpenDyslexic', sans-serif !important;
    }}

    /* DYNAMIC BIONIC OVERRIDE */
    .bionic-container {{
        font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif !important;
        font-size: {font_size}px !important;
        line-height: 2.2 !important;
        color: #888888 !important;
    }}

    .bionic-container b {{
        font-family: system-ui, -apple-system, sans-serif !important;
        font-weight: 900 !important;
        font-size: {bold_size}px !important;
        color: #ffd700 !important;
    }}

    .reading-box {{
        background-color: #1e1e1e;
        border: 2px solid #ffd700;
        border-radius: 12px;
        padding: 24px;
        margin-top: 15px;
        margin-bottom: 25px;
        max-height: 500px !important;
        overflow-y: auto !important;
    }}

    .stButton>button {{
        background-color: #ffd700 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR CONTROLS
# ==========================================

# Retrieve Gemini API Key securely from Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

# Initialize Gemini Client if API key exists
client = None
if api_key:
    client = OpenAI(api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
  )

# Helper Function: Bionic Reading
# Helper Function: Bionic Reading


# ==========================================
# BIONIC READING
# ==========================================
def convert_to_bionic(text):
    import re
    
    # Preserve paragraph and line breaks
    lines = text.split('\n')
    bionic_lines = []
    
    for line in lines:
        words = line.split(' ')
        bionic_words = []
        
        for word in words:
            if not word:
                continue
            
            # Handle word vs punctuation separately so tags don't break
            match = re.match(r'^(\W*)([\w]+)(\W*)$', word, re.UNICODE)
            if match:
                prefix_punct, core_word, suffix_punct = match.groups()
                mid = max(1, len(core_word) // 2)
                bionic_word = f"{prefix_punct}<b>{core_word[:mid]}</b>{core_word[mid:]}{suffix_punct}"
            else:
                mid = max(1, len(word) // 2)
                bionic_word = f"<b>{word[:mid]}</b>{word[mid:]}"
                
            bionic_words.append(bionic_word)
            
        bionic_lines.append(" ".join(bionic_words))
        
    return "<br>".join(bionic_lines)

 # ==========================================
 # PDF SEARCH
 # ==========================================

    def find_relevant_chunks(text, query, chunk_size=1500, top_k=3):
    import re

    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    query_words = set(
        word.lower()
        for word in re.findall(r"\b[a-zA-Z0-9]+\b", query)
        if len(word) > 2
    )

    scored_chunks = []

    for chunk in chunks:
        chunk_words = set(
            word.lower()
            for word in re.findall(r"\b[a-zA-Z0-9]+\b", chunk)
        )

        score = len(query_words.intersection(chunk_words))

        scored_chunks.append((score, chunk))

    scored_chunks.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    return "\n\n".join(
        chunk for score, chunk in scored_chunks[:top_k]
    )

# ==========================================
# 3. MAIN APPLICATION INTERFACE
# ==========================================
st.title("🧠 Accessibility Lens")
st.caption("Empowering neurodivergent learners with adaptive AI document processing.")

if not api_key:
    st.error("⚠️ `GEMINI_API_KEY` is missing in Streamlit Secrets. Please add it under Settings > Secrets in Streamlit Cloud.")

elif not uploaded_file:
    st.markdown("""
    <div class="reading-box" style="text-align: center;">
        <h3>Welcome! Upload a PDF document in the sidebar to begin.</h3>
        <p>Accessibility Lens automatically formats dense text into high-contrast Bionic reading views, simplified AI executive summaries, and audio playback.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Extract PDF Text
    try:
        reader = PdfReader(uploaded_file)
        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text() or ""
        
        st.success(f"Successfully processed {len(reader.pages)} pages!")
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        extracted_text = ""

    if extracted_text:
        # Organized Main View via Tabs
        tab_summary, tab_bionic, tab_audio, tab_chat = st.tabs([
            "⚡ ELI10 Summary", 
            "📖 Bionic Reader", 
            "🎧 Audio Assistant",
            "💬 Ask Questions"
        ])

        # TAB 1: ELI10 Summary
        with tab_summary:
            st.subheader("Simplified Executive Summary")
            if st.button("Generate AI Summary"):
                with st.spinner("Analyzing document with Gemini..."):
                    try:
                        if extracted_text and extracted_text.strip():
                            prompt = (
                                "Summarize the following academic text for a student with ADHD or learning differences. "
                                "Use short bullet points, bold key terms, simple everyday words, and an 'Explain Like I'm 10' tone:\n\n"
                                f"{extracted_text[:4000]}"
                            )
                            
                            response = client.chat.completions.create(
                                model="gemini-3.1-flash-lite",
                                messages=[{"role": "user", "content": prompt}]
                            )
                            st.markdown(f'<div class="reading-box">{response.choices[0].message.content}</div>', unsafe_allow_html=True)
                        else:
                            st.warning("Please upload a document first.")
                    except Exception as e:
                        st.error(f"API Error: {e}")
        # TAB 2: Bionic Reader View
        with tab_bionic:
            st.subheader("Bionic Focused View")
            bionic_html = convert_to_bionic(extracted_text)
            st.markdown(f'<div class="reading-box"><div class="bionic-container">{bionic_html}</div></div>', unsafe_allow_html=True)

        # TAB 3: Audio Assistant
        with tab_audio:
            st.subheader("Listen to Document Audio")
            if st.button("Convert First Section to Audio"):
                with st.spinner("Generating audio file..."):
                    try:
                        tts = gTTS(text=extracted_text[:800], lang='en')
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        st.audio(fp, format='audio/mp3')
                    except Exception as e:
                        st.error(f"Audio Generation Error: {e}")

        # TAB 4: Interactive Q&A Assistant
        with tab_chat:
            st.subheader("Interactive Document Q&A")
            user_query = st.text_input("Ask any question about this document:")
            
            if user_query and user_query.strip():
                if extracted_text and extracted_text.strip():
                    with st.spinner("Gemini is searching the document..."):
                        try:
                            relevant_text = find_relevant_chunks(
                                extracted_text,
                                user_query
                            )
                            
                            prompt = (
                                "You are a helpful study assistant. "
                                "Answer the user's question using ONLY the provided document context. "
                                "If the answer cannot be found in the context, say that the information "
                                "is not available in the provided document. "
                                "Keep your response concise and easy to read.\n\n"
                                f"DOCUMENT CONTEXT:\n{relevant_text}\n\n"
                                f"USER QUESTION:\n{user_query}"
                            )
                            
                            response = client.chat.completions.create(
                                model="gemini-3.1-flash-lite",
                                messages=[{"role": "user", "content": prompt}]
                            )
                            
                            st.markdown(f'<div class="reading-box">{response.choices[0].message.content}</div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"API Error: {e}")
                else:
                    st.warning("Please upload a PDF document before asking a question.")
