import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import base64

# 1. SETUP & CLIENT
# We halen de key veilig uit de Streamlit secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    # Fallback voor als de secret nog niet is ingesteld (voorkomt directe crash)
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
    
    # Fix: Emoji's en speciale tekens filteren om crashes te voorkomen in standaard FPDF
    sanitized_text = text_content.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=sanitized_text, align='L')
    return pdf.output(dest='S').encode('latin-1')

# Sessie status initialiseren
if 'work_experience' not in st.session_state:
    st.session_state['work_experience'] = []

if 'profile_text' not in st.session_state:
    st.session_state['profile_text'] = ""

# 3. DE GEBRUIKERSINTERFACE (UI)
st.title('📝 Professionele CV Maker')

tabs = st.tabs(["✏️ Editor", "📄 Voorbeeld CV"])

# --- TAB 1: EDITOR ---
with tabs[0]:
    with st.expander("Persoonlijk"):
        name = st.text_input("Naam")
        job_title = st.text_input("Functietitel")
        email = st.text_input("Email")
        phone = st.text_input("Telefoon")
        linkedin = st.text_input("LinkedIn URL")
        
        profile_pic = st.file_uploader("Upload je pasfoto", type=['jpg', 'png'])
        profile_pic_base64 = ""
        if profile_pic:
            profile_pic_base64 = convert_image_to_base64(profile_pic.read())

    with st.expander("Profiel"):
        st.session_state.profile_text = st.text_area("Introduceer jezelf", st.session_state.profile_text)
        
        if st.button("✨ Herschrijf met AI"):
            if not client:
                st.error("OpenAI API key ontbreekt in Secrets.")
            else:
                try:
                    with st.spinner("AI is aan het schrijven..."):
                        input_text = st.session_state.profile_text
                        # NIEUWE SYNTAX VOOR OPENAI v1.x
                        response = client.chat.completions.create(
                            model="gpt-4o", # Of gpt-4
                            messages=[{"role": "user", "content": f"Maak deze tekst professioneler voor een CV: {input_text}"}]
                        )
                        # Nieuwe manier van data uitlezen (object notatie)
                        st.session_state.profile_text = response.choices[0].message.content.strip()
                        st.rerun() # Vervanging voor experimental_rerun
                except Exception as e:
                    st.error(f"Fout bij verbinden met OpenAI: {e}")

    with st.expander("Werkervaring"):
        if st.button("+ Voeg werkervaring toe"):
            st.session_state.work_experience.append("")
        
        for i, job in enumerate(st.session_state.work_experience):
            job_description = st.text_area(f"Ervaring {i+1}", job, key=f'job_{i}')
            st.session_state.work_experience[i] = job_description

    with st.expander("Styling"):
        accent_color = st.color_picker("Accentkleur", value="#FF5733")

# --- TAB 2: VOORBEELD ---
with tabs[1]:
    if not name or not job_title:
        st.info("Vul eerst je gegevens in bij de Editor.")
    else:
        # Lijst items maken voor HTML
        work_list_items = ''.join([f"<li>{job}</li>" for job in st.session_state.work_experience])

        # HTML voor de weergave in de browser
        cv_html = f'''
        <html>
        <head>
        <style>
            body {{font-family: sans-serif; color: #333;}}
            .cv-container {{width: 210mm; padding: 20px; border: 1px solid #eee; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);}}
            .header {{background-color: {accent_color}; padding: 20px; color: white; text-align: center; border-radius: 5px;}}
            .profile-pic {{width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 10px;}}
            h1 {{margin: 0; font-size: 24px;}}
            h2 {{margin: 5px 0 0 0; font-size: 18px; font-weight: normal;}}
            .section-title {{margin-top: 20px; border-bottom: 2px solid {accent_color}; color: {accent_color}; font-weight: bold;}}
            ul {{padding-left: 20px;}}
        </style>
        </head>
        <body>
            <div class="cv-container">
                <div class="header">
                    {'<img src="data:image/png;base64,' + profile_pic_base64 + '" class="profile-pic"/>' if profile_pic_base64 else ''}
                    <h1>{name}</h1>
                    <h2>{job_title}</h2>
                    <p style="font-size: 12px;">{email} | {phone} | {linkedin}</p>
                </div>
                
                <div class="section-title">PROFIEL</div>
                <p>{st.session_state.profile_text}</p>
                
                <div class="section-title">WERKERVARING</div>
                <ul>
                    {work_list_items}
                </ul>
            </div>
        </body>
        </html>
        '''
        
        st.markdown(cv_html, unsafe_allow_html=True)

        # PDF Download Knop
        # Let op: FPDF print de HTML code als tekst, omdat simpele FPDF geen HTML rendering ondersteunt.
        # Voor nu printen we de platte tekst versie in de PDF om errors te voorkomen.
        if st.button("Download als PDF"):
            # We maken een simpele tekstversie voor de PDF (omdat FPDF geen HTML leest)
            flat_text = f"NAAM: {name}\nTITEL: {job_title}\n\nPROFIEL:\n{st.session_state.profile_text}\n\nWERKERVARING:\n"
            for job in st.session_state.work_experience:
                flat_text += f"- {job}\n"
            
            pdf_data = generate_pdf(flat_text)
            
            st.download_button(
                "Download PDF Bestand", 
                data=pdf_data, 
                file_name="mijn_cv.pdf", 
                mime="application/pdf"
            )
