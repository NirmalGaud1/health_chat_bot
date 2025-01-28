#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import re

genai.configure(api_key="AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c")
model = genai.GenerativeModel('gemini-pro')

class HealthcareDocProcessor:
    def __init__(self):
        self.key_sections = {
            'compliance': ['compliance', 'regulation'],
            'liability': ['liability', 'responsibility'],
            'patient_data': ['patient data', 'confidentiality'],
            'payment_terms': ['payment', 'fees'],
            'termination': ['termination', 'expiry'],
        }

    def extract_text(self, uploaded_file):
        if uploaded_file.name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            return '\n'.join([page.extract_text() for page in reader.pages])
        else:
            raise ValueError("Unsupported file format")

    def find_sections(self, text):
        results = {}
        for section, keywords in self.key_sections.items():
            pattern = r'(?i)({}).*?(?=\n\s*\n|$)'.format('|'.join(keywords))
            match = re.search(pattern, text, re.DOTALL)
            if match:
                results[section] = match.group(0).strip()
        return results

    def analyze_with_gemini(self, text, prompt):
        response = model.generate_content(prompt + text)
        return response.text

class HealthcareAIAgent:
    def __init__(self):
        self.processor = HealthcareDocProcessor()
    
    def analyze_document(self, uploaded_file):
        text = self.processor.extract_text(uploaded_file)
        sections = self.processor.find_sections(text)
        
        analysis = {
            'metadata': self._get_metadata(text),
            'key_clauses': {},
            'risks': self._identify_risks(text)
        }
        
        for section, content in sections.items():
            analysis['key_clauses'][section] = {
                'summary': self._summarize_clause(content, section),
                'compliance_issues': self._extract_compliance_issues(content),
                'dates': self._extract_dates(content)
            }
        
        return analysis

    def _summarize_clause(self, text, section_name):
        prompt = f"Summarize this {section_name.replace('_', ' ')} clause in 3 bullet points:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _extract_compliance_issues(self, text):
        prompt = "Identify compliance-related issues or gaps from this legal clause:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _extract_dates(self, text):
        prompt = "Extract all critical dates and deadlines in YYYY-MM-DD format:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _get_metadata(self, text):
        prompt = """Extract metadata from this healthcare document:
        - Involved parties
        - Effective date
        - Document type
        - Regulatory references
        Format as JSON:"""
        return self.processor.analyze_with_gemini(text, prompt)

    def _identify_risks(self, text):
        prompt = """Identify potential risks in this document:
        - Non-compliance issues
        - Data privacy concerns
        - Ambiguous responsibilities
        Format as bullet points:"""
        return self.processor.analyze_with_gemini(text, prompt)

st.set_page_config(page_title="Healthcare Document AI Analyzer", layout="wide")

st.title("🏥 Healthcare Document Analyzer AI Agent")
st.write("Upload your healthcare contract or legal document (PDF or Word) for analysis")

uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx'])

if uploaded_file:
    agent = HealthcareAIAgent()
    
    with st.spinner('Analyzing document...'):
        try:
            analysis = agent.analyze_document(uploaded_file)
            
            st.success("Analysis complete!")
            st.divider()
            
            with st.expander("📋 Document Metadata", expanded=True):
                st.json(analysis['metadata'])
            
            with st.expander("📑 Key Clauses"):
                for section, content in analysis['key_clauses'].items():
                    st.subheader(f"{section.replace('_', ' ').title()} Clause")
                    st.write("**Summary:**")
                    st.write(content['summary'])
                    st.write("**Compliance Issues:**")
                    st.write(content['compliance_issues'])
                    st.write("**Key Dates:**")
                    st.write(content['dates'])
                    st.divider()
            
            with st.expander("⚠️ Identified Risks"):
                st.write(analysis['risks'])
        
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")

