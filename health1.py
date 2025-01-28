#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import re
import os
import json

# Configure Generative AI API using environment variables
api_key = os.getenv("AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c")  # Ensure this is set in your environment
if not api_key:
    st.error("GEMINI_API_KEY environment variable is not set. Please configure it.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

class HealthcareDocProcessor:
    def __init__(self):
        self.key_sections = {
            'confidentiality': ['confidentiality', 'nda'],
            'data_privacy': ['data privacy', 'HIPAA', 'GDPR'],
            'payment_terms': ['payment', 'fees', 'remuneration'],
            'responsibilities': ['responsibility', 'obligations'],
        }

    def extract_text(self, uploaded_file):
        """Extract text from uploaded PDF or DOCX file."""
        try:
            if uploaded_file.name.endswith('.pdf'):
                reader = PdfReader(uploaded_file)
                return '\n'.join([page.extract_text() for page in reader.pages])
            elif uploaded_file.name.endswith('.docx'):
                doc = Document(uploaded_file)
                return '\n'.join([para.text for para in doc.paragraphs])
            else:
                raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")
        except Exception as e:
            raise ValueError(f"Error extracting text from file: {str(e)}")

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
        try:
            response = model.generate_content(prompt + text)
            return response.text
        except Exception as e:
            raise ValueError(f"Error calling Gemini API: {str(e)}")

class HealthcareAIAgent:
    def __init__(self):
        self.processor = HealthcareDocProcessor()
    
    def analyze_document(self, uploaded_file):
        """Analyze the uploaded document and return structured analysis."""
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
                'obligations': self._extract_obligations(content),
                'dates': self._extract_dates(content)
            }
        
        return analysis

    def _summarize_clause(self, text, section_name):
        prompt = f"Summarize this {section_name.replace('_', ' ')} clause in 3 bullet points:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _extract_obligations(self, text):
        prompt = "List all party obligations from this clause:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _extract_dates(self, text):
        prompt = "Extract all critical dates and deadlines in YYYY-MM-DD format:\n"
        return self.processor.analyze_with_gemini(text, prompt)

    def _get_metadata(self, text):
        prompt = """Extract metadata from this healthcare document:
        - Parties involved
        - Effective date
        - Document type
        - Key stakeholders
        Format as JSON:"""
        metadata = self.processor.analyze_with_gemini(text, prompt)
        try:
            return json.loads(metadata)  # Parse JSON for better display
        except json.JSONDecodeError:
            return metadata  # Return raw text if JSON parsing fails

    def _identify_risks(self, text):
        prompt = """Identify potential risks in this healthcare document:
        - Non-compliance with HIPAA/GDPR
        - Data privacy issues
        - Ambiguous responsibilities
        - Missing information
        Format as bullet points:"""
        return self.processor.analyze_with_gemini(text, prompt)

# Streamlit UI
st.set_page_config(page_title="🏥 Healthcare Document Analyzer AI Agent", layout="wide")

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
                metadata = analysis['metadata']
                if isinstance(metadata, dict):
                    st.json(metadata)
                else:
                    st.write(metadata)  # Display raw text if JSON parsing failed
            
            with st.expander("📑 Key Clauses"):
                for section, content in analysis['key_clauses'].items():
                    st.subheader(f"{section.replace('_', ' ').title()}")
                    st.write("**Summary:**")
                    st.write(content['summary'])
                    st.write("**Obligations:**")
                    st.write(content['obligations'])
                    st.write("**Key Dates:**")
                    st.write(content['dates'])
                    st.divider()
            
            with st.expander("⚠️ Identified Risks"):
                st.write(analysis['risks'])
        
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")

