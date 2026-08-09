import streamlit as st
from pypdf import PdfReader
from openai import OpenAI
from gtts import gTTS
import io
import numpy as np


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
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )


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

            # Handle word vs punctuation separately
            match = re.match(
                r'^(\W*)([\w]+)(\W*)$',
                word,
                re.UNICODE
            )

            if match:
                prefix_punct, core_word, suffix_punct = match.groups()
                mid = max(1, len(core_word) // 2)

                bionic_word = (
                    f"{prefix_punct}"
                    f"<b>{core_word[:mid]}</b>"
                    f"{core_word[mid:]}"
                    f"{suffix_punct}"
                )

            else:
                mid = max(1, len(word) // 2)
                bionic_word = (
                    f"<b>{word[:mid]}</b>{word[mid:]}"
                )

            bionic_words.append(bionic_word)

        bionic_lines.append(" ".join(bionic_words))

    return "<br>".join(bionic_lines)


# ==========================================
# PDF SEARCH
# ==========================================

def create_chunks(pages):
    import re

    chunks = []

    for page_data in pages:
        page_number = page_data["page"]
        text = page_data["text"]

        # Clean whitespace
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)

        # Split around questions/sections
        sections = re.split(
            r'(?=\n?\s*(?:\d+\.\s+|Q(?:uestion)?\.?\s*\d*[:.]?))',
            text,
            flags=re.IGNORECASE
        )

        for section in sections:
            section = section.strip()

            if not section:
                continue

            words = section.split()

            if len(words) <= 450:
                chunks.append({
                    "text": section,
                    "page": page_number
                })
            else:
                for i in range(0, len(words), 350):
                    chunk = " ".join(words[i:i + 350])

                    chunks.append({
                        "text": chunk,
                        "page": page_number
                    })

    return chunks
def get_embedding(text):
    response = client.embeddings.create(
        model="gemini-embedding-2",
        input=text
    )

    return np.array(response.data[0].embedding)


def find_relevant_chunks(text, query, top_k=2):
    chunks = create_chunks(pages)

    if not chunks:
        return []

    # Embed the user's question
    query_embedding = get_embedding(query)

    scored_chunks = []

    # Embed each document chunk
    for chunk in chunks:
        chunk_embedding = get_embedding(chunk["text"])

        # Calculate cosine similarity
        similarity = np.dot(
            query_embedding,
            chunk_embedding
        ) / (
            np.linalg.norm(query_embedding)
            * np.linalg.norm(chunk_embedding)
        )

        scored_chunks.append((similarity, chunk))

    # Sort from most relevant to least relevant
    scored_chunks.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Return the best chunks
    return [
        chunk
        for similarity, chunk in scored_chunks[:top_k]
    ]
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
    # Extract PDF Text
         
    try:
        reader = PdfReader(uploaded_file)
    
        pages = []
    
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
    
            if page_text.strip():
                pages.append({
                    "page": page_number,
                    "text": page_text
                })
    
        # Combine page text for the rest of the app
        extracted_text = "\n\n".join(
            page["text"] for page in pages
        )
    
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
            
                            relevant_chunks = find_relevant_chunks(
                                extracted_text,
                                user_query,
                                top_k=2
                            )
            
                            relevant_text = "\n\n".join(
                                f"[Page {chunk['page']}]\n{chunk['text']}"
                                for chunk in relevant_chunks
                            )
            
                            prompt = (
                                "You are a helpful study assistant. "
                                "Answer the user's question accurately based ONLY "
                                "on the provided document context. "
                                "If the answer is not in the context, say so.\n\n"
                                f"DOCUMENT CONTEXT:\n{relevant_text}\n\n"
                                f"USER QUESTION:\n{user_query}"
                            )
            
                            response = client.chat.completions.create(
                                model="gemini-3.1-flash",
                                messages=[
                                    {"role": "user", "content": prompt}
                                ]
                            )
            
                            # AI answer
                            st.markdown(
                                f'<div class="reading-box">'
                                f'{response.choices[0].message.content}'
                                f'</div>',
                                unsafe_allow_html=True
                            )
            
                            # Source pages
                            pages_used = sorted(set(
                                chunk["page"]
                                for chunk in relevant_chunks
                            ))
            
                            st.caption(
                                "📄 Source: " +
                                ", ".join(
                                    f"Page {page}"
                                    for page in pages_used
                                )
                            )
            
                        except Exception as e:
                            st.error(f"API Error: {e}")
                            st.error(f"API Error: {e}")
