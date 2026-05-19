import time
import pandas as pd
import streamlit as st

from streamlit_option_menu import option_menu
from streamlit_extras.add_vertical_space import add_vertical_space
from PyPDF2 import PdfReader

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from huggingface_hub import InferenceClient


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Resume Analyzer AI",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stHeader"]{
    background: rgba(0,0,0,0);
}
.block-container{
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;color:orange;'>Resume Analyzer AI</h1>",
    unsafe_allow_html=True
)


# ---------------- PDF TEXT EXTRACTION ----------------

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""

    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    return text


# ---------------- AI RESPONSE (FIXED) ----------------

def get_ai_response(api_key, prompt):

    client = InferenceClient(
        model="meta-llama/Llama-3.1-8B-Instruct",
        token=api_key
    )

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a professional resume analyzer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=700
    )

    return response.choices[0].message["content"]


# ---------------- PROMPTS ----------------

def summary_prompt(text):
    return f"""
Analyze this resume and provide:

1. Professional Summary
2. Skills
3. Education
4. Experience
5. Projects
6. Final Conclusion

Resume:
{text}
"""


def strength_prompt(text):
    return f"""
Analyze strengths of this resume:

- Technical strengths
- Project strengths
- Communication strengths
- Career strengths
- Best qualities

Resume:
{text}
"""


def weakness_prompt(text):
    return f"""
Analyze weaknesses and improvements:

- Missing skills
- Resume improvements
- Better formatting
- Career improvement ideas
- ATS optimization tips

Resume:
{text}
"""


def jobs_prompt(text):
    return f"""
Suggest suitable job roles:

- Internship roles
- Entry level jobs
- Software roles
- AI/ML roles
- Career path suggestion

Resume:
{text}
"""


# ---------------- RESUME ANALYSIS ----------------

def analyze_resume(prompt_function, heading):

    with st.form(key=heading):

        add_vertical_space(1)

        pdf = st.file_uploader("Upload Resume PDF", type="pdf")

        add_vertical_space(1)

        api_key = st.text_input("Enter Hugging Face Token", type="password")

        add_vertical_space(1)

        submit = st.form_submit_button("Analyze")

    if submit:

        if pdf is None:
            st.error("Please upload resume PDF")
            return

        if api_key.strip() == "":
            st.error("Please enter Hugging Face token")
            return

        try:
            with st.spinner("Analyzing Resume..."):

                resume_text = extract_text_from_pdf(pdf)

                if len(resume_text.strip()) == 0:
                    st.error("Unable to extract text from PDF")
                    return

                prompt = prompt_function(resume_text)

                result = get_ai_response(api_key, prompt)

            st.markdown(
                f"<h2 style='color:orange;'>{heading}</h2>",
                unsafe_allow_html=True
            )

            st.write(result)

        except Exception as e:
            st.error(f"Error: {e}")


# ---------------- SELENIUM DRIVER ----------------

def setup_driver():

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


# ---------------- LINKEDIN JOBS ----------------

def linkedin_jobs():

    with st.form("linkedin_form"):

        job_title = st.text_input("Job Title")
        location = st.text_input("Location", value="India")
        count = st.number_input("Scroll Count", min_value=1, max_value=20, value=5)

        submit = st.form_submit_button("Search Jobs")

    if submit:

        if job_title.strip() == "":
            st.error("Please enter job title")
            return

        driver = None

        try:
            with st.spinner("Fetching LinkedIn jobs..."):

                driver = setup_driver()

                url = f"https://www.linkedin.com/jobs/search?keywords={job_title}&location={location}"
                driver.get(url)

                time.sleep(5)

                for _ in range(count):
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                    time.sleep(2)

                companies = driver.find_elements(By.CSS_SELECTOR, "h4.base-search-card__subtitle")
                titles = driver.find_elements(By.CSS_SELECTOR, "h3.base-search-card__title")
                locs = driver.find_elements(By.CSS_SELECTOR, "span.job-search-card__location")
                links = driver.find_elements(By.CSS_SELECTOR, "a.base-card__full-link")

                n = min(len(companies), len(titles), len(locs), len(links))

                if n == 0:
                    st.warning("No jobs found")
                    return

                for i in range(n):

                    st.markdown(f"### Job {i+1}")
                    st.write("Company:", companies[i].text)
                    st.write("Role:", titles[i].text)
                    st.write("Location:", locs[i].text)
                    st.write("Link:", links[i].get_attribute("href"))
                    st.divider()

        except Exception as e:
            st.error(f"Error: {e}")

        finally:
            if driver:
                driver.quit()


# ---------------- SIDEBAR ----------------

with st.sidebar:

    add_vertical_space(2)

    selected = option_menu(
        menu_title="Menu",
        options=["Summary", "Strength", "Weakness", "Job Titles", "LinkedIn Jobs"],
        icons=["file-text", "star", "x-circle", "briefcase", "linkedin"],
        default_index=0
    )


# ---------------- ROUTING ----------------

if selected == "Summary":
    analyze_resume(summary_prompt, "Resume Summary")

elif selected == "Strength":
    analyze_resume(strength_prompt, "Resume Strength Analysis")

elif selected == "Weakness":
    analyze_resume(weakness_prompt, "Resume Weakness Analysis")

elif selected == "Job Titles":
    analyze_resume(jobs_prompt, "Suggested Job Titles")

elif selected == "LinkedIn Jobs":
    linkedin_jobs()