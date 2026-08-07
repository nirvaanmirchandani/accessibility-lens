import streamlit as st
from pypdf import PdfReader
from openai import OpenAI
from gtts import gTTS
import io

# Page Configuration
st.set_page_config(page_title="Accessibility Lens", page_icon="🧠", layout="wide")

st.title("🧠 Accessibility Lens")
st.caption("Empowering neurodivergent learners with adaptive AI document processing.")

# Sidebar Controls
with st.sidebar:
    st.title("⚙️ Controls")
    uploaded_file = st.file_uploader("Upload Academic PDF", type=["pdf"])

# Access API Key securely from Streamlit Secrets
api_key = st.secrets.get("OPENAI_API_KEY")

if uploaded_file and api_key:
    # 1. Extract Text
    reader = PdfReader(uploaded_file)
    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() or ""

    client = OpenAI(api_key=api_key)

    # 2. Tabs Interface
    tab1, tab2, tab3 = st.tabs(["⚡ ELI10 Summary", "📖 Bionic View", "🎧 Audio"])

    with tab1:
        if st.button("Generate Summary"):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Summarize this text in simple bullet points for a student with ADHD:\n\n{extracted_text[:3000]}"}]
            )
            st.write(response.choices[0].message.content)

    with tab2:
        words = extracted_text[:1000].split()
        bionic = " ".join([f"<b>{w[:len(w)//2+1]}</b>{w[len(w)//2+1:]}" for w in words])
        st.markdown(f"<div style='font-size: 18px; line-height: 1.8;'>{bionic}</div>", unsafe_allow_html=True)

    with tab3:
        if st.button("Generate Audio"):
            tts = gTTS(text=extracted_text[:500], lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')

elif not api_key:
    st.warning("Please configure your OPENAI_API_KEY in Streamlit Secrets.")
