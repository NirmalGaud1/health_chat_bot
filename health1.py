#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import re

# Configure Generative AI API
genai.configure(api_key="AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c")  # Replace with your Gemini API key
model = genai.GenerativeModel('gemini-1.5-flash')

class HealthDocProcessor:
    def __init__(self):
        # Define key sections for healthcare documents
        self.key_sections = {
            'patient_details': ['patient details', 'name', 'age', 'gender'],
            'medical_conditions': ['medical conditions', 'diagnosis', 'symptoms'],
            'treatment_plan': ['treatment plan', 'therapy', 'procedures'],
            'medications': ['medications', 'prescription', 'drugs'],
            'risks': ['risks', 'complications', 'side effects']
        }

    def extract_text(self, uploaded_file):
        """Extract text from uploaded PDF or DOCX file."""
        if uploaded_file.name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            return '\n'.join([page.extract_text() for page in reader.pages])
        else:
            raise ValueError("Unsupported file format. Please upload a PDF file.")

    def find_sections(self, text):
        """Find key sections in the document based on predefined keywords."""
        results = {}
        for section, keywords in self.key_sections.items():
            pattern = r'(?i)({}).*?(?=\n\s*\n|$)'.format('|'.join(keywords))
            match = re.search(pattern, text, re.DOTALL)
            if match:
                results[section] = match.group(0).strip()
        return results

    def analyze_with_gemini(self, text, prompt):
        """Analyze text using the Gemini API."""
        response = model.generate_content(prompt + text)
        return response.text

class HealthAIAgent:
    def __init__(self):
        self.processor = HealthDocProcessor()
    
    def analyze_document(self, uploaded_file):
        """Analyze the uploaded healthcare document and return structured analysis."""
        text = self.processor.extract_text(uploaded_file)
        sections = self.processor.find_sections(text)
        
        analysis = {
            'metadata': self._get_metadata(text),
            'key_sections': {},
            'risks': self._identify_risks(text)
        }
        
        for section, content in sections.items():
            analysis['key_sections'][section] = {
                'summary': self._summarize_section(content, section),
                'details': self._extract_details(content),
                'actions': self._suggest_actions(content)
            }
        
        return analysis

    def _summarize_section(self, text, section_name):
        """Summarize a healthcare section."""
        prompt = f"Summarize this {section_name.replace('_', ' ')} section in 3 bullet points:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _extract_details(self, text):
        """Extract detailed information from a section."""
        prompt = "Extract key details from this section:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _suggest_actions(self, text):
        """Suggest actions based on the section content."""
        prompt = "Suggest actions or next steps based on this section:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _get_metadata(self, text):
        """Extract metadata from the healthcare document."""
        prompt = """Extract metadata from this healthcare document:
        - Patient name
        - Date of birth
        - Medical record number
        - Document type (e.g., prescription, medical report)
        Format as JSON:"""
        return self.processor.analyze_with_gemini(text, prompt)

    def _identify_risks(self, text):
        """Identify potential risks in the healthcare document."""
        prompt = """Identify potential risks or issues in this healthcare document:
        - Medication side effects
        - Treatment complications
        - Missing information
        Format as bullet points:"""
        return self.processor.analyze_with_gemini(text, prompt)

# Streamlit UI
st.set_page_config(page_title="🏥 Health Document Analyzer AI Agent", layout="wide")

st.title("🏥 Health Document Analyzer AI Agent")
st.write("Upload your healthcare document (PDF) for analysis")

uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx'])

if uploaded_file:
    agent = HealthAIAgent()
    
    with st.spinner('Analyzing document...'):
        try:
            analysis = agent.analyze_document(uploaded_file)
            
            st.success("Analysis complete!")
            st.divider()
            
            with st.expander("📋 Document Metadata", expanded=True):
                st.write(analysis['metadata'])
            
            with st.expander("📑 Key Sections"):
                for section, content in analysis['key_sections'].items():
                    st.subheader(f"{section.replace('_', ' ').title()}")
                    st.write("**Summary:**")
                    st.write(content['summary'])
                    st.write("**Details:**")
                    st.write(content['details'])
                    st.write("**Suggested Actions:**")
                    st.write(content['actions'])
                    st.divider()
            
            with st.expander("⚠️ Identified Risks"):
                st.write(analysis['risks'])
        
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")

