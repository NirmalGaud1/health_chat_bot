#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import os
import re
import time
import json
import logging
from typing import Dict, List, Optional, Any

import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key='AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c')
model = genai.GenerativeModel('gemini-1.5-flash')

# Helper Class for Healthcare Analysis
class HealthcareAgent:
    def __init__(self):
        self.medical_terms = {
            'vitals': ['temperature', 'blood pressure', 'heart rate', 'respiratory rate'],
            'blood_tests': ['hemoglobin', 'wbc', 'rbc', 'platelets', 'glucose'],
            'imaging': ['x-ray', 'mri', 'ct scan', 'ultrasound']
        }

    def analyze_with_gemini(self, text: str, prompt: str, max_retries: int = 3) -> str:
        """Handle Gemini API call with retries."""
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
        """Extract text and analyze medical data from PDF reports."""
        if not uploaded_file.name.endswith('.pdf'):
            raise ValueError("Only PDF medical reports are supported")

        reader = PdfReader(uploaded_file)
        text = '\n'.join([page.extract_text() for page in reader.pages])
        return self._process_medical_report(text)

    def _process_medical_report(self, text: str) -> Dict[str, Any]:
        """Extract key medical metrics using regex."""
        findings = {}
        for category, terms in self.medical_terms.items():
            pattern = r'(?i)({}):?\s*([\d\.]+(?:/\d+)?(?:\s*(?:mmHg|°F|°C|mg/dL|bpm))?)'.format('|'.join(terms))
            matches = re.findall(pattern, text)
            if matches:
                findings[category] = {match[0].lower(): match[1] for match in matches}
        return findings

    def symptom_checker(self, symptoms: str) -> Dict[str, Any]:
        """Analyze symptoms and return structured medical guidance."""
        prompt = f"""Analyze these symptoms: {symptoms}
        Provide response in VALID JSON format only:
        {{
            "possible_conditions": [],
            "recommended_actions": [],
            "emergency_signs": []
        }}
        Do not include any markdown formatting."""
        
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
        """Analyze medication interactions and guidelines."""
        prompt = f"""Analyze these medications: {medications}
        Provide response in VALID JSON format:
        {{
            "interactions": [],
            "side_effects": [],
            "guidelines": []
        }}
        No markdown, only pure JSON."""
        
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

# Streamlit UI
def setup_streamlit_ui():
    st.set_page_config(page_title="Healthcare AI Assistant", layout="wide")
    st.title("🏥 AI Healthcare Assistant")

    # Tabbed Layout
    tab1, tab2, tab3 = st.tabs(["Symptom Checker", "Report Analysis", "Medication Manager"])

    # Tab 1: Symptom Checker
    with tab1:
        st.subheader("Symptom Analysis")
        symptoms = st.text_area("Describe your symptoms (e.g., fever, headache):", placeholder="Enter your symptoms here...")
        
        if st.button("Analyze Symptoms", key="symptoms"):
            agent = HealthcareAgent()
            with st.spinner('Analyzing symptoms...'):
                result = agent.symptom_checker(symptoms)
                
                if "error" in result:
                    st.error(f"Analysis failed: {result['error']}")
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.subheader("Possible Conditions")
                        for condition in result.get("possible_conditions", [])[:3]:
                            st.markdown(f"- {condition}")
                    with col2:
                        st.subheader("Recommended Actions")
                        for action in result.get("recommended_actions", []):
                            st.markdown(f"- {action}")
                    with col3:
                        st.subheader("Emergency Signs")
                        for sign in result.get("emergency_signs", []):
                            st.markdown(f"⚠️ {sign}")

    # Tab 2: Medical Report Analysis
    with tab2:
        st.subheader("Medical Report Analysis")
        uploaded_file = st.file_uploader("Upload Medical Report (PDF)", type=['pdf'], key="report")
        
        if uploaded_file:
            agent = HealthcareAgent()
            with st.spinner('Processing report...'):
                try:
                    # Step 1: Extract text from the PDF
                    reader = PdfReader(uploaded_file)
                    text = '\n'.join([page.extract_text() for page in reader.pages])
                    
                    # Debugging: Display raw extracted text
                    with st.expander("View Raw Extracted Text"):
                        st.text(text)
                    
                    # Step 2: Extract medical data using regex
                    report_data = agent._process_medical_report(text)
                    
                    # Step 3: Analyze the report using Gemini
                    analysis = agent.analyze_with_gemini(
                        str(report_data), 
                        "Analyze this medical report and highlight key findings:"
                    )
                    
                    # Step 4: Display the results
                    st.subheader("Report Summary")
                    st.markdown(analysis)
                    
                    st.subheader("Key Metrics")
                    if report_data:
                        for category, values in report_data.items():
                            with st.expander(category.replace('_', ' ').title()):
                                st.json(values)
                    else:
                        st.warning("No key metrics found in the report.")
                        
                except Exception as e:
                    st.error(f"Error processing the report: {str(e)}")

    # Tab 3: Medication Analysis
    with tab3:
        st.subheader("Medication Analysis")
        meds = st.text_input("Enter medications (comma-separated):", placeholder="e.g., Aspirin, Paracetamol")
        
        if st.button("Analyze Medications", key="medications"):
            agent = HealthcareAgent()
            with st.spinner('Checking interactions...'):
                result = agent.medication_analyzer(meds)
                
                if "error" in result:
                    st.error(f"Analysis failed: {result['error']}")
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.subheader("Interactions")
                        for interaction in result.get("interactions", []):
                            st.markdown(f"- {interaction}")
                    with col2:
                        st.subheader("Side Effects")
                        for effect in result.get("side_effects", []):
                            st.markdown(f"- {effect}")
                    with col3:
                        st.subheader("Guidelines")
                        for guideline in result.get("guidelines", []):
                            st.markdown(f"- {guideline}")

    st.divider()
    st.caption("Note: This AI assistant provides informational support only and does not replace professional medical advice.")

if __name__ == "__main__":
    setup_streamlit_ui()
