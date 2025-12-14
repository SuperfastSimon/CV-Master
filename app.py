import streamlit as st
from openai import OpenAI
from fpdf import FPDF

# 1. Client Setup (Nieuwe syntax)
# Zorg dat je 'OPENAI_API_KEY' in je Streamlit Secrets staat
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_pdf(text):
    """Hulpfunctie om tekst naar PDF te converteren"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Let op: FPDF (standaard) ondersteunt geen speciale UTF-8 tekens (zoals emoji's).
    # 'encode' en 'decode' hieronder filtert karakters die errors veroorzaken.
    sanitized_text = text.encode('latin-1', 'replace').decode('latin-1')
    
    # Multi_cell zorgt voor automatische regelafbreking
    pdf.multi_cell(0, 10, txt=sanitized_text)
    
    # Sla op naar een tijdelijke string/bytes
    return pdf.output(dest='S').encode('latin-1')

st.title("GPT-4o PDF Generator")

topic = st.text_input("Waar moet de tekst over gaan?")

if st.button("Genereer en maak PDF"):
    if not topic:
        st.warning("Vul eerst een onderwerp in.")
    else:
        with st.spinner('GPT-4o is aan het schrijven...'):
            try:
                # 2. De OpenAI aanroep (Nieuwe syntax)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Je bent een behulpzame schrijver."},
                        {"role": "user", "content": f"Schrijf een kort artikel over: {topic}"}
                    ]
                )
                
                # Data uitlezen met punt-notatie
                generated_text = response.choices[0].message.content
                
                # Toon de tekst op het scherm
                st.subheader("Resultaat:")
                st.write(generated_text)
                
                # 3. PDF Genereren
                pdf_bytes = generate_pdf(generated_text)
                
                # 4. Download knop
                st.download_button(
                    label="📄 Download als PDF",
                    data=pdf_bytes,
                    file_name="gegenereerd_artikel.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Er ging iets mis: {e}")
