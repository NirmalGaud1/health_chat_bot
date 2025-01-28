#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import os
import re
import time
import json
import logging
from typing import Dict, List, Any

import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key='AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c')
model = genai.GenerativeModel('gemini-1.5-flash')

# Healthcare Analysis Helper Class
class HealthcareAgent:
    def __init__(self):
        self.medical_terms = {
            'vitals': ['temperature', 'blood pressure', 'heart rate', 'respiratory rate'],
            'blood_tests': ['hemoglobin', 'wbc', 'rbc', 'platelets', 'glucose'],
            'imaging': ['x-ray', 'mri', 'ct scan', 'ultrasound']
        }

    def analyze_with_gemini(self, text: str, prompt: str, max_retries: int = 3) -> str:
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt + text)
                return response.text
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"API Error: {str(e)}")
        raise Exception("API Error: Maximum retries exceeded")

    def extract_medical_data(self, uploaded_file) -> Dict[str, Any]:
        if not uploaded_file.name.endswith('.pdf'):
            raise ValueError("Only PDF medical reports are supported")

        reader = PdfReader(uploaded_file)
        text = '\n'.join([page.extract_text() for page in reader.pages])
        return self._process_medical_report(text)

    def _process_medical_report(self, text: str) -> Dict[str, Any]:
        findings = {}
        for category, terms in self.medical_terms.items():
            pattern = r'(?i)({}):?\s*([\d\.]+(?:/\d+)?(?:\s*(?:mmHg|°F|°C|mg/dL|bpm))?)'.format('|'.join(terms))
            matches = re.findall(pattern, text)
            if matches:
                findings[category] = {match[0].lower(): match[1] for match in matches}
        return findings

    def symptom_checker(self, symptoms: str) -> Dict[str, Any]:
        prompt = f"""Analyze these symptoms: {symptoms}
        Provide response in VALID JSON format only:
        {{
            "possible_conditions": [],
            "recommended_actions": [],
            "emergency_signs": []
        }}
        """
        try:
            response = self.analyze_with_gemini(symptoms, prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            return {"error": "Failed to parse medical analysis"}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}

    def medication_analyzer(self, medications: str) -> Dict[str, Any]:
        prompt = f"""Analyze these medications: {medications}
        Provide response in VALID JSON format:
        {{
            "interactions": [],
            "side_effects": [],
            "guidelines": []
        }}
        """
        try:
            response = self.analyze_with_gemini(medications, prompt)
            response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            return {"error": "Failed to parse medication analysis"}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}

# Streamlit App UI
def setup_streamlit_ui():
    st.set_page_config(page_title="Healthcare AI Assistant", layout="wide")
    st.title("🏥 AI Healthcare Assistant")

    # Tabbed Layout
    tab1, tab2, tab3 = st.tabs(["Symptom Checker", "Report Analysis", "Medication Manager"])

    # Tab 1: Symptom Checker
    with tab1:
        st.subheader("Symptom Analysis")
        symptoms = st.text_area("Describe your symptoms:", placeholder="Enter your symptoms here...")
        if st.button("Analyze Symptoms", key="symptoms"):
            agent = HealthcareAgent()
            with st.spinner('Analyzing symptoms...'):
                result = agent.symptom_checker(symptoms)
                st.json(result)

    # Tab 2: Medical Report Analysis
    with tab2:
        st.subheader("Medical Report Analysis")
        uploaded_file = st.file_uploader("Upload Medical Report (PDF)", type=['pdf'])
        if uploaded_file:
            agent = HealthcareAgent()
            with st.spinner('Processing report...'):
                try:
                    report_data = agent.extract_medical_data(uploaded_file)
                    st.json(report_data)
                except Exception as e:
                    st.error(f"Error processing the report: {str(e)}")

    # Tab 3: Medication Manager
    with tab3:
        st.subheader("Medication Analysis")
        medications = st.text_input("Enter medications (comma-separated):", placeholder="e.g., Aspirin, Paracetamol")
        if st.button("Analyze Medications", key="medications"):
            agent = HealthcareAgent()
            with st.spinner('Checking interactions...'):
                result = agent.medication_analyzer(medications)
                st.json(result)

if __name__ == "__main__":
    setup_streamlit_ui()

