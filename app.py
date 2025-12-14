import streamlit as st
import openai
from fpdf import FPDF
import base64
from io import BytesIO

# Initial setup
openai.api_key = 'your-openai-api-key'
st.set_page_config(layout="centered", page_title="CV Maker")

# Helper functions
def convert_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def generate_pdf(cv_html):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=cv_html, align='L')
    return pdf.output(dest='S').encode('latin1')

if 'work_experience' not in st.session_state:
    st.session_state['work_experience'] = []

if 'profile_text' not in st.session_state:
    st.session_state['profile_text'] = ""

# UI
st.title('📝 Professionele CV Maker')
tabs = st.tabs(["✏️ Editor", "📄 Voorbeeld CV"])

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
            input_text = st.session_state.profile_text
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Maak deze tekst professioneler: {input_text}"}]
            )
            st.session_state.profile_text = response['choices'][0]['message']['content'].strip()
            st.experimental_rerun()

    with st.expander("Werkervaring"):
        if st.button("+ Voeg werkervaring toe"):
            st.session_state.work_experience.append("")
        for i, job in enumerate(st.session_state.work_experience):
            job_description = st.text_area(f"Experience {i+1}", job, key=f'job_{i}')
            st.session_state.work_experience[i] = job_description

    with st.expander("Styling"):
        accent_color = st.color_picker("Accentkleur", value="#FF5733")

with tabs[1]:
    # Placeholder content if missing any data
    if not name or not job_title:
        st.warning("Vul alstublieft de sectie 'Persoonlijk' in op de Editor tab.")
    else:
        # HTML for Display
        cv_html = f'''
        <html>
        <head>
            <style>
                body {{font-family: sans-serif; color: #333;}}
                .cv-container {{width: 210mm; height: 297mm; margin: auto; padding: 20mm; border: 1px solid #eee; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);}}
                .header {{background-color: {accent_color}; padding: 10px; color: white; text-align: center;}}
                .profile-pic {{width: 100px; height: 100px; border-radius: 50%; overflow: hidden;}}
                .section-title {{margin-top: 20px;}}
            </style>
        </head>
        <body>
            <div class="cv-container">
                <div class="header">
                    <h1>{name}</h1>
                    <h2>{job_title}</h2>
                </div>
                <div class="profile">
                    <img src="data:image/png;base64,{profile_pic_base64}" class="profile-pic" alt="Profile Picture" />
                    <p>{st.session_state.profile_text}</p>
                </div>
                <div class="section-title">
                    <h3>Werkervaring</h3>
                    <ul>
                    {''.join([f"<li>{job}</li>" for job in st.session_state.work_experience])}
                    </ul>
                </div>
            </div>
        </body>
        </html>
        '''
        st.markdown(cv_html, unsafe_allow_html=True)

        # Generate PDF button
        if st.button("Download als PDF"):
            pdf_data = generate_pdf(cv_html)
            st.download_button(
                "Download PDF", data=pdf_data, file_name="cv.pdf", mime="application/pdf"
            )
