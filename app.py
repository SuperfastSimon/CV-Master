import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from xhtml2pdf import pisa
import base64
import json
from io import BytesIO

# 1. SETUP
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    client = None

st.set_page_config(layout="wide", page_title="CV Maker Pro")

# 2. HELPER FUNCTIES
def convert_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def create_pdf(html_content):
    """Genereert een PDF die er exact zo uitziet als de HTML/CSS"""
    result = BytesIO()
    # xhtml2pdf werkt het beste met bytes encoding
    pisa_status = pisa.CreatePDF(html_content, dest=result)
    if pisa_status.err:
        return None
    return result.getvalue()

# Sessie Status
keys = ['name', 'job_title', 'email', 'phone', 'address', 'linkedin', 'profile_text', 'work_experience', 'profile_pic_data']
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = [] if key == 'work_experience' else ""

def update_field(key):
    st.session_state[key] = st.session_state[f"input_{key}"]

# 3. UI
st.title('🚀 Professionele CV Generator')

col_top_1, col_top_2 = st.columns([4, 1])
with col_top_1:
    st.info("Vul links je gegevens in. De preview rechts is precies hoe je PDF eruit komt te zien.")
with col_top_2:
    if st.button("🔄 Ververs Preview", type="primary"):
        st.rerun()

col_editor, col_preview = st.columns([1, 1])

# --- EDITOR KOLOM ---
with col_editor:
    st.subheader("1. Gegevens Invoer")
    
    # IMPORT LINKEDIN
    with st.expander("📂 Importeer PDF (LinkedIn)", expanded=False):
        uploaded_pdf = st.file_uploader("Upload LinkedIn PDF", type="pdf")
        if uploaded_pdf and st.button("Vul automatisch in met AI"):
            if not client:
                st.error("Geen API Key gevonden.")
            else:
                with st.spinner("AI leest je PDF..."):
                    text = extract_text_from_pdf(uploaded_pdf)
                    # Prompt vraagt nu ook om adres/woonplaats (NAW)
                    prompt = f"""
                    Haal deze data uit de tekst:
                    - name (Volledige naam)
                    - job_title (Huidige functie)
                    - email
                    - phone (Telefoonnummer)
                    - address (Woonplaats/Adres)
                    - linkedin (URL)
                    - summary (Korte profielschets)
                    - experience (Lijst van werkervaringen)
                    
                    Geef antwoord als JSON:
                    {{
                        "name": "...", "job_title": "...", "email": "...", "phone": "...",
                        "address": "...", "linkedin": "...", "summary": "...", "experience": ["...", "..."]
                    }}
                    Tekst: {text[:3000]}
                    """
                    try:
                        res = client.chat.completions.create(
                            model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"}
                        )
                        data = json.loads(res.choices[0].message.content)
                        st.session_state.update(data)
                        st.session_state['work_experience'] = data.get('experience', [])
                        st.session_state['profile_text'] = data.get('summary', '')
                        st.success("Gelukt! Controleer de velden.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fout: {e}")

    # PERSOONLIJKE GEGEVENS
    with st.expander("👤 Persoonlijke Info", expanded=True):
        st.text_input("Naam", value=st.session_state['name'], key="input_name", on_change=update_field, args=('name',))
        st.text_input("Functie", value=st.session_state['job_title'], key="input_job_title", on_change=update_field, args=('job_title',))
        st.text_input("Email", value=st.session_state['email'], key="input_email", on_change=update_field, args=('email',))
        st.text_input("Telefoon", value=st.session_state['phone'], key="input_phone", on_change=update_field, args=('phone',))
        st.text_input("Adres / Woonplaats", value=st.session_state['address'], key="input_address", on_change=update_field, args=('address',))
        st.text_input("LinkedIn / Website", value=st.session_state['linkedin'], key="input_linkedin", on_change=update_field, args=('linkedin',))
        
        pic = st.file_uploader("Pasfoto", type=['jpg', 'png', 'jpeg'])
        if pic:
            st.session_state['profile_pic_data'] = convert_image_to_base64(pic.read())

    # PROFIEL
    with st.expander("📝 Profiel", expanded=False):
        curr_prof = st.text_area("Profieltekst", value=st.session_state['profile_text'], height=150)
        st.session_state['profile_text'] = curr_prof
        if st.button("✨ Herschrijf met AI"):
            if client:
                with st.spinner("Bezig..."):
                    r = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": f"Herschrijf voor CV: {curr_prof}"}])
                    st.session_state['profile_text'] = r.choices[0].message.content
                    st.rerun()

    # ERVARING
    with st.expander("💼 Werkervaring", expanded=False):
        if st.button("+ Functie toevoegen"):
            st.session_state['work_experience'].append("")
            st.rerun()
        
        to_del = []
        for i, job in enumerate(st.session_state['work_experience']):
            c1, c2 = st.columns([5, 1])
            with c1:
                val = st.text_area(f"Ervaring {i+1}", value=job, key=f"job_{i}", height=100)
                st.session_state['work_experience'][i] = val
            with c2:
                st.write("")
                if st.button("🗑️", key=f"d_{i}"):
                    to_del.append(i)
        
        if to_del:
            for i in sorted(to_del, reverse=True):
                del st.session_state['work_experience'][i]
            st.rerun()

# --- PREVIEW KOLOM ---
with col_preview:
    st.subheader("2. Design & Resultaat")
    
    c_templ, c_color = st.columns(2)
    with c_templ:
        template = st.selectbox("Kies Template", ["Modern", "Creative (Zijbalk)", "Clean (Minimal)"])
    with c_color:
        accent = st.color_picker("Kleur", "#2c3e50")

    # HTML BOUWEN
    # Let op: We gebruiken tabellen (<table>) omdat de PDF generator (xhtml2pdf) geen Flexbox ondersteunt.
    
    img_tag = ""
    if st.session_state['profile_pic_data']:
        # Zorg dat de afbeelding niet te groot is in de PDF
        img_tag = f'<img src="data:image/jpeg;base64,{st.session_state["profile_pic_data"]}" style="width:100px; height:100px; border-radius:50%; margin-bottom:10px;">'

    work_items = "".join([f"<li style='margin-bottom:8px;'>{item}</li>" for item in st.session_state['work_experience'] if item.strip()])

    # CSS BASIS
    base_css = f"""
        body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12px; color: #333; }}
        h1 {{ color: {accent}; font-size: 24px; margin: 0; }}
        h2 {{ color: #666; font-size: 14px; margin: 2px 0 10px 0; font-weight: normal; }}
        .section {{ color: {accent}; font-weight: bold; border-bottom: 2px solid {accent}; margin-top: 20px; margin-bottom: 10px; padding-bottom: 2px; text-transform: uppercase; font-size: 14px; }}
        .meta {{ font-size: 10px; color: #777; margin-bottom: 20px; }}
        ul {{ padding-left: 20px; }}
    """

    # TEMPLATE LOGICA
    if template == "Creative (Zijbalk)":
        # Tabel layout voor zijbalk effect in PDF
        html_content = f"""
        <html>
        <head><style>
            {base_css}
            td {{ vertical-align: top; padding: 20px; }}
            .sidebar {{ background-color: {accent}; color: white; width: 30%; }}
            .main {{ width: 70%; }}
            .sidebar h1, .sidebar h2 {{ color: white; }}
            .white-txt {{ color: white !important; }}
        </style></head>
        <body>
            <table width="100%" cellspacing="0" cellpadding="0">
                <tr>
                    <td class="sidebar">
                        <div style="text-align:center;">{img_tag}</div>
                        <h1 style="color:white; font-size:20px;">{st.session_state['name']}</h1>
                        <h2 style="color:white;">{st.session_state['job_title']}</h2>
                        <br/><br/>
                        <div class="white-txt"><b>CONTACT</b></div>
                        <div class="white-txt">{st.session_state['email']}</div>
                        <div class="white-txt">{st.session_state['phone']}</div>
                        <div class="white-txt">{st.session_state['address']}</div>
                        <div class="white-txt">{st.session_state['linkedin']}</div>
                    </td>
                    <td class="main">
                        <div class="section">Profiel</div>
                        <div>{st.session_state['profile_text']}</div>
                        
                        <div class="section">Werkervaring</div>
                        <ul>{work_items}</ul>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
    elif template == "Modern":
        html_content = f"""
        <html>
        <head><style>
            {base_css}
            .header-bg {{ background-color: {accent}; color: white; padding: 20px; text-align: center; }}
            .header-bg h1, .header-bg h2, .header-bg .meta {{ color: white; }}
        </style></head>
        <body>
            <div class="header-bg">
                {img_tag}
                <h1>{st.session_state['name']}</h1>
                <h2>{st.session_state['job_title']}</h2>
                <div class="meta" style="color:#eee;">
                    {st.session_state['email']} | {st.session_state['phone']} | {st.session_state['address']} | {st.session_state['linkedin']}
                </div>
            </div>
            <div style="padding:20px;">
                <div class="section">Profiel</div>
                <div>{st.session_state['profile_text']}</div>
                
                <div class="section">Werkervaring</div>
                <ul>{work_items}</ul>
            </div>
        </body>
        </html>
        """

    else: # Clean/Minimal
        html_content = f"""
        <html>
        <head><style>
            {base_css}
            .header-tbl td {{ vertical-align: middle; }}
        </style></head>
        <body>
            <table width="100%" class="header-tbl">
                <tr>
                    <td width="70%">
                        <h1>{st.session_state['name']}</h1>
                        <h2>{st.session_state['job_title']}</h2>
                        <div class="meta">
                            {st.session_state['email']} • {st.session_state['phone']}<br/>
                            {st.session_state['address']} • {st.session_state['linkedin']}
                        </div>
                    </td>
                    <td width="30%" align="right">
                        {img_tag}
                    </td>
                </tr>
            </table>
            <hr color="{accent}" />
            
            <div class="section">Profiel</div>
            <div>{st.session_state['profile_text']}</div>
            
            <div class="section">Werkervaring</div>
            <ul>{work_items}</ul>
        </body>
        </html>
        """

    # PREVIEW TONEN
    st.markdown(f'<div style="border:1px solid #ddd; padding:10px; background:white;">{html_content}</div>', unsafe_allow_html=True)

    # PDF GENEREREN
    st.write("")
    pdf_bytes = create_pdf(html_content)
    
    if pdf_bytes:
        st.download_button(
            label="⬇️ Download PDF (met design)",
            data=pdf_bytes,
            file_name="Mijn_CV.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.error("Kon PDF niet genereren. Controleer of de foto niet te groot/corrupt is.")
