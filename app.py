import streamlit as st
from openai import OpenAI
from fpdf import FPDF
from pypdf import PdfReader
import base64
import json

# 1. SETUP & CLIENT
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    client = None
    st.warning("Let op: Stel je OPENAI_API_KEY in bij de Secrets!")

st.set_page_config(layout="centered", page_title="CV Maker")

# 2. HELPER FUNCTIES
def convert_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def generate_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    sanitized_text = text_content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=sanitized_text, align='L')
    return pdf.output(dest='S').encode('latin-1')

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Sessie status initialiseren
if 'work_experience' not in st.session_state:
    st.session_state['work_experience'] = []
if 'profile_text' not in st.session_state:
    st.session_state['profile_text'] = ""
if 'name' not in st.session_state:
    st.session_state['name'] = ""
if 'job_title' not in st.session_state:
    st.session_state['job_title'] = ""
if 'email' not in st.session_state:
    st.session_state['email'] = ""

# 3. UI
st.title('📝 Professionele CV Maker')

tabs = st.tabs(["✏️ Editor", "📄 Voorbeeld CV"])

# --- TAB 1: EDITOR ---
with tabs[0]:
    
    # === NIEUW: LINKEDIN IMPORT ===
    with st.expander("🚀 Importeer van LinkedIn", expanded=True):
        st.write("Ga naar je LinkedIn profiel > knop 'More' > 'Save to PDF' en upload die hier.")
        uploaded_linkedin = st.file_uploader("Upload LinkedIn PDF", type="pdf")
        
        if uploaded_linkedin and st.button("Vul CV automatisch in"):
            if not client:
                st.error("Geen API key gevonden.")
            else:
                with st.spinner("LinkedIn data analyseren..."):
                    raw_text = extract_text_from_pdf(uploaded_linkedin)
                    
                    # We vragen GPT om JSON terug te geven
                    prompt = f"""
                    Haal de volgende gegevens uit deze ruwe CV tekst:
                    - Volledige naam
                    - Huidige functietitel (of laatste)
                    - Emailadres (indien aanwezig)
                    - Korte samenvatting/profielschets
                    - Een lijst van werkervaringen (Samenvatting per rol)

                    Geef antwoord puur als JSON in dit formaat:
                    {{
                        "name": "...",
                        "job_title": "...",
                        "email": "...",
                        "summary": "...",
                        "experience": ["rol 1...", "rol 2..."]
                    }}

                    TEKST:
                    {raw_text[:4000]} 
                    """
                    
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt}],
                            response_format={"type": "json_object"}
                        )
                        
                        data = json.loads(response.choices[0].message.content)
                        
                        # Sessie updaten
                        st.session_state['name'] = data.get('name', '')
                        st.session_state['job_title'] = data.get('job_title', '')
                        st.session_state['email'] = data.get('email', '')
                        st.session_state['profile_text'] = data.get('summary', '')
                        st.session_state['work_experience'] = data.get('experience', [])
                        
                        st.success("Gegevens ingeladen! Controleer de velden hieronder.")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Fout bij uitlezen: {e}")

    # === DE STANDAARD VELDEN ===
    with st.expander("Persoonlijk", expanded=True):
        st.session_state['name'] = st.text_input("Naam", st.session_state['name'])
        st.session_state['job_title'] = st.text_input("Functietitel", st.session_state['job_title'])
        st.session_state['email'] = st.text_input("Email", st.session_state['email'])
        phone = st.text_input("Telefoon")
        linkedin = st.text_input("LinkedIn URL")
        
        profile_pic = st.file_uploader("Upload je pasfoto", type=['jpg', 'png'])
        profile_pic_base64 = ""
        if profile_pic:
            profile_pic_base64 = convert_image_to_base64(profile_pic.read())

    with st.expander("Profiel"):
        st.session_state['profile_text'] = st.text_area("Introduceer jezelf", st.session_state['profile_text'], height=150)
        
        if st.button("✨ Herschrijf profiel met AI"):
            if client:
                with st.spinner("AI is aan het schrijven..."):
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": f"Herschrijf professioneel: {st.session_state['profile_text']}"}]
                    )
                    st.session_state['profile_text'] = resp.choices[0].message.content
                    st.rerun()

    with st.expander("Werkervaring"):
        if st.button("+ Voeg werkervaring toe"):
            st.session_state['work_experience'].append("")
        
        # We gebruiken een kopie van de lijst om indexfouten te voorkomen tijdens typen
        updated_experience = st.session_state['work_experience'].copy()
        
        for i, job in enumerate(st.session_state['work_experience']):
            updated_experience[i] = st.text_area(f"Ervaring {i+1}", job, key=f'job_{i}', height=100)
        
        # Sync terug naar session state
        st.session_state['work_experience'] = updated_experience

    with st.expander("Styling"):
        accent_color = st.color_picker("Accentkleur", value="#FF5733")

# --- TAB 2: VOORBEELD ---
with tabs[1]:
    if not st.session_state['name']:
        st.info("Vul eerst je gegevens in (of importeer LinkedIn PDF).")
    else:
        work_list_items = ''.join([f"<li style='margin-bottom:10px;'>{job}</li>" for job in st.session_state['work_experience']])

        cv_html = f'''
        <html>
        <head>
        <style>
            body {{font-family: Helvetica, Arial, sans-serif; color: #333; line-height: 1.5;}}
            .cv-container {{width: 210mm; padding: 40px; background: white; margin: auto; box-shadow: 0 0 15px rgba(0,0,0,0.1);}}
            .header {{border-bottom: 5px solid {accent_color}; padding-bottom: 20px; margin-bottom: 20px; display: flex; align-items: center;}}
            .header-text {{flex: 1;}}
            .profile-pic {{width: 120px; height: 120px; border-radius: 50%; object-fit: cover; margin-right: 20px; border: 3px solid {accent_color};}}
            h1 {{margin: 0; font-size: 32px; color: {accent_color}; text-transform: uppercase;}}
            h2 {{margin: 5px 0; font-size: 18px; color: #666; font-weight: normal;}}
            .contact-info {{font-size: 12px; color: #888; margin-top: 5px;}}
            .section-title {{font-size: 16px; font-weight: bold; color: {accent_color}; text-transform: uppercase; border-bottom: 1px solid #ddd; margin-top: 25px; margin-bottom: 10px; padding-bottom: 5px;}}
            ul {{padding-left: 20px;}}
        </style>
        </head>
        <body>
            <div class="cv-container">
                <div class="header">
                    {'<img src="data:image/png;base64,' + profile_pic_base64 + '" class="profile-pic"/>' if profile_pic_base64 else ''}
                    <div class="header-text">
                        <h1>{st.session_state['name']}</h1>
                        <h2>{st.session_state['job_title']}</h2>
                        <div class="contact-info">{st.session_state['email']} | {phone} | {linkedin}</div>
                    </div>
                </div>
                
                <div class="section-title">PROFIEL</div>
                <p>{st.session_state['profile_text']}</p>
                
                <div class="section-title">WERKERVARING</div>
                <ul>
                    {work_list_items}
                </ul>
            </div>
        </body>
        </html>
        '''
        
        st.markdown(cv_html, unsafe_allow_html=True)

        if st.button("Download als PDF"):
            # Simpele PDF export (tekst basis)
            flat_text = f"NAAM: {st.session_state['name']}\n\nPROFIEL:\n{st.session_state['profile_text']}\n\nWERKERVARING:\n"
            for job in st.session_state['work_experience']:
                flat_text += f"- {job}\n"
            pdf_data = generate_pdf(flat_text)
            st.download_button("Download PDF Bestand", data=pdf_data, file_name="cv.pdf", mime="application/pdf")
