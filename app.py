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

st.set_page_config(layout="wide", page_title="CV Maker Pro")

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
keys = ['work_experience', 'profile_text', 'name', 'job_title', 'email', 'phone', 'linkedin', 'profile_pic_data']
for key in keys:
    if key not in st.session_state:
        if key == 'work_experience':
            st.session_state[key] = []
        else:
            st.session_state[key] = ""

def update_field(key):
    st.session_state[key] = st.session_state[f"input_{key}"]

# 3. UI - HEADER & KNOPPEN
st.title('🎨 Professionele CV Builder')

col_top_1, col_top_2 = st.columns([4, 1])
with col_top_1:
    st.info("Vul links je gegevens in, kies rechts je stijl en klik op 'Genereer'.")
with col_top_2:
    if st.button("🚀 Genereer CV", key="top_btn", type="primary"):
        st.rerun()

# We gebruiken kolommen voor de layout: Links Editor, Rechts Preview
col_editor, col_preview = st.columns([1, 1])

# --- KOLOM 1: EDITOR ---
with col_editor:
    st.header("✏️ Gegevens")
    
    # === LINKEDIN IMPORT ===
    with st.expander("Importeer van LinkedIn (PDF)", expanded=False):
        uploaded_linkedin = st.file_uploader("Upload PDF", type="pdf")
        if uploaded_linkedin and st.button("Vul automatisch in"):
            if not client:
                st.error("Geen API Key.")
            else:
                with st.spinner("Analyseren..."):
                    try:
                        raw_text = extract_text_from_pdf(uploaded_linkedin)
                        prompt = f"""Haal data uit tekst. JSON format: {{ "name": "", "job_title": "", "email": "", "summary": "", "experience": ["rol 1", "rol 2"] }} Tekst: {raw_text[:3000]}"""
                        res = client.chat.completions.create(
                            model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"}
                        )
                        data = json.loads(res.choices[0].message.content)
                        st.session_state.update(data)
                        st.session_state['work_experience'] = data.get('experience', [])
                        st.session_state['profile_text'] = data.get('summary', '')
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fout: {e}")

    # === PERSOONLIJK ===
    with st.expander("Persoonlijke Info", expanded=True):
        st.text_input("Naam", value=st.session_state['name'], key="input_name", on_change=update_field, args=('name',))
        st.text_input("Functie", value=st.session_state['job_title'], key="input_job_title", on_change=update_field, args=('job_title',))
        st.text_input("Email", value=st.session_state['email'], key="input_email", on_change=update_field, args=('email',))
        st.text_input("Telefoon", value=st.session_state['phone'], key="input_phone", on_change=update_field, args=('phone',))
        st.text_input("LinkedIn/Web", value=st.session_state['linkedin'], key="input_linkedin", on_change=update_field, args=('linkedin',))
        
        uploaded_pic = st.file_uploader("Pasfoto", type=['jpg', 'png'])
        if uploaded_pic:
            st.session_state['profile_pic_data'] = convert_image_to_base64(uploaded_pic.read())

    # === PROFIEL ===
    with st.expander("Profiel & AI", expanded=False):
        current_profile = st.text_area("Profieltekst", value=st.session_state['profile_text'], height=150)
        st.session_state['profile_text'] = current_profile 
        
        if st.button("✨ Herschrijf met AI"):
            if client and st.session_state['profile_text']:
                with st.spinner("Schrijven..."):
                    resp = client.chat.completions.create(
                        model="gpt-4o", messages=[{"role": "user", "content": f"Herschrijf professioneel voor CV: {st.session_state['profile_text']}"}]
                    )
                    st.session_state['profile_text'] = resp.choices[0].message.content
                    st.rerun()

    # === ERVARING ===
    with st.expander("Werkervaring", expanded=False):
        if st.button("+ Functie"):
            st.session_state['work_experience'].append("")
            st.rerun()
        
        indices_to_remove = []
        for i, job in enumerate(st.session_state['work_experience']):
            c1, c2 = st.columns([5,1])
            with c1:
                new_val = st.text_area(f"Rol {i+1}", value=job, key=f"job_{i}", height=100)
                st.session_state['work_experience'][i] = new_val
            with c2:
                st.write("")
                if st.button("X", key=f"del_{i}"):
                    indices_to_remove.append(i)
        
        if indices_to_remove:
            for i in sorted(indices_to_remove, reverse=True):
                del st.session_state['work_experience'][i]
            st.rerun()

# --- KOLOM 2: PREVIEW & STYLING ---
with col_preview:
    st.header("🎨 Design & Preview")
    
    # STYLING OPTIES
    with st.container(border=True):
        st.subheader("Instellingen")
        c_style1, c_style2 = st.columns(2)
        with c_style1:
            template_choice = st.selectbox("Kies Template", ["Modern (Header)", "Minimalist (Clean)", "Creative (Zijbalk)"])
        with c_style2:
            accent_color = st.color_picker("Hoofdkleur", "#007BFF") # Blauw als standaard

    # HTML GENERATOR
    if not st.session_state['name']:
        st.warning("Vul links je naam in voor een voorbeeld.")
    else:
        # Basis Variabelen
        img_html = ""
        if st.session_state.get('profile_pic_data'):
            img_html = f'<img src="data:image/png;base64,{st.session_state["profile_pic_data"]}" class="profile-pic"/>'
        
        work_list = "".join([f"<li>{job}</li>" for job in st.session_state['work_experience'] if job.strip()])

        # --- CSS LOGICA PER TEMPLATE ---
        if "Modern" in template_choice:
            # STYLE 1: MODERN (Gekleurde Header)
            css = f'''
                .cv-box {{ font-family: sans-serif; background: white; padding: 0; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: {accent_color}; color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 32px; }}
                .header h2 {{ margin: 5px 0 0; font-size: 18px; font-weight: normal; opacity: 0.9; }}
                .contact {{ margin-top: 10px; font-size: 13px; opacity: 0.8; }}
                .profile-pic {{ width: 120px; height: 120px; border-radius: 50%; border: 4px solid white; margin-bottom: 15px; object-fit: cover; }}
                .content {{ padding: 30px; }}
                .section-title {{ color: {accent_color}; border-bottom: 2px solid {accent_color}; padding-bottom: 5px; margin-top: 20px; margin-bottom: 10px; font-weight: bold; text-transform: uppercase; }}
                li {{ margin-bottom: 10px; }}
            '''
            body_content = f'''
                <div class="header">
                    {img_html}
                    <h1>{st.session_state['name']}</h1>
                    <h2>{st.session_state['job_title']}</h2>
                    <div class="contact">{st.session_state['email']} | {st.session_state['phone']} | {st.session_state['linkedin']}</div>
                </div>
                <div class="content">
                    <div class="section-title">Profiel</div>
                    <p>{st.session_state['profile_text']}</p>
                    <div class="section-title">Werkervaring</div>
                    <ul>{work_list}</ul>
                </div>
            '''

        elif "Minimalist" in template_choice:
            # STYLE 2: MINIMALIST (Wit, strakke lijnen)
            css = f'''
                .cv-box {{ font-family: 'Georgia', serif; background: white; padding: 40px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
                .header {{ border-bottom: 1px solid #ccc; padding-bottom: 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
                .header-text h1 {{ margin: 0; font-size: 28px; color: #333; }}
                .header-text h2 {{ margin: 5px 0; font-size: 16px; color: {accent_color}; }}
                .contact {{ font-size: 12px; color: #666; }}
                .profile-pic {{ width: 80px; height: 80px; border-radius: 5px; object-fit: cover; }}
                .section-title {{ color: #333; font-weight: bold; margin-top: 25px; margin-bottom: 10px; text-transform: uppercase; font-size: 14px; letter-spacing: 1px; }}
                li {{ margin-bottom: 8px; color: #444; }}
            '''
            body_content = f'''
                <div class="header">
                    <div class="header-text">
                        <h1>{st.session_state['name']}</h1>
                        <h2>{st.session_state['job_title']}</h2>
                        <div class="contact">{st.session_state['email']} • {st.session_state['phone']}</div>
                    </div>
                    {img_html}
                </div>
                <div class="section-title" style="color:{accent_color}">Profiel</div>
                <p>{st.session_state['profile_text']}</p>
                <div class="section-title" style="color:{accent_color}">Werkervaring</div>
                <ul>{work_list}</ul>
            '''

        else:
            # STYLE 3: CREATIVE (Zijbalk Layout met Flexbox)
            css = f'''
                .cv-box {{ font-family: sans-serif; background: white; display: flex; box-shadow: 0 4px 10px rgba(0,0,0,0.1); min-height: 800px; }}
                .sidebar {{ width: 35%; background-color: {accent_color}; color: white; padding: 30px; text-align: center; }}
                .main {{ width: 65%; padding: 30px; }}
                .profile-pic {{ width: 100px; height: 100px; border-radius: 50%; border: 3px solid rgba(255,255,255,0.5); margin-bottom: 20px; object-fit: cover; }}
                .sidebar h1 {{ font-size: 22px; margin-bottom: 5px; }}
                .sidebar h2 {{ font-size: 14px; font-weight: normal; opacity: 0.9; margin-bottom: 20px; }}
                .contact-item {{ font-size: 12px; margin-bottom: 10px; opacity: 0.9; word-wrap: break-word; }}
                .section-title {{ color: {accent_color}; font-size: 18px; font-weight: bold; border-bottom: 2px solid #eee; padding-bottom: 5px; margin-bottom: 15px; margin-top: 0; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 10px; color: #444; }}
            '''
            body_content = f'''
                <div class="sidebar">
                    {img_html}
                    <h1>{st.session_state['name']}</h1>
                    <h2>{st.session_state['job_title']}</h2>
                    <br>
                    <div class="contact-item">📧 {st.session_state['email']}</div>
                    <div class="contact-item">📱 {st.session_state['phone']}</div>
                    <div class="contact-item">🔗 {st.session_state['linkedin']}</div>
                </div>
                <div class="main">
                    <div class="section-title">Profiel</div>
                    <p>{st.session_state['profile_text']}</p>
                    <br>
                    <div class="section-title">Werkervaring</div>
                    <ul>{work_list}</ul>
                </div>
            '''

        # Render de HTML
        final_html = f'<style>{css}</style><div class="cv-box">{body_content}</div>'
        st.markdown(final_html, unsafe_allow_html=True)

        st.write("")
        # PDF DOWNLOAD (Platte tekst versie, want FPDF ondersteunt geen geavanceerde CSS/Flexbox)
        flat_text = f"NAAM: {st.session_state['name']}\n\nPROFIEL:\n{st.session_state['profile_text']}\n\nWERKERVARING:\n"
        for job in st.session_state['work_experience']:
            flat_text += f"- {job}\n"
        pdf_bytes = generate_pdf(flat_text)
        
        st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name="CV.pdf", mime="application/pdf", type="primary")


