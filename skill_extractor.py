import nltk
import re
import logging
import os
import tempfile
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from skills_data import SKILLS_LIST
from pypdf import PdfReader

logger = logging.getLogger(__name__)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt_tab')
    except:
        logger.warning("Unable to download punkt_tab. Using basic sentence splitting as fallback.")

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using PyPDF.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            
            num_pages = len(pdf_reader.pages)
            
            text = ""
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                
                page_text = page.extract_text()
                
                if page_text:
                    text += page_text + "\n"
            
            if not text.strip():
                logger.warning("PDF text extraction yielded empty result, see what you uploaded")
                
            return text
    except Exception as e:
        logger.exception(f"Error extracting text from PDF: {e}")
        raise

def preprocess_text(text):
    """
    Preprocess the extracted text by removing special characters,
    converting to lowercase, and tokenizing.
    
    Args:
        text (str): Text extracted from PDF
        
    Returns:
        list: List of processed tokens
    """
    text = text.lower()
    
    text = re.sub(r'[^\w\s]', ' ', text)
    
    tokens = word_tokenize(text)
    
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    return tokens

def identify_skills(tokens, sentences):
    """
    Identify skills from the processed tokens and original sentences.
    
    Args:
        tokens (list): List of processed tokens
        sentences (list): List of sentences from the original text
        
    Returns:
        list: List of identified skills
    """
    identified_skills = set()
    
    for token in tokens:
        if token in SKILLS_LIST and len(token) > 1:  
            identified_skills.add(token)
    
    for skill in SKILLS_LIST:
        if ' ' in skill and skill.lower() in ' '.join(tokens).lower():
            identified_skills.add(skill)
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for skill in SKILLS_LIST:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, sentence_lower):
                identified_skills.add(skill)
    
    return sorted(list(identified_skills))

def categorize_skills(skills):
    """
    Categorize skills into different categories.
    
    Args:
        skills (list): List of identified skills
        
    Returns:
        dict: Dictionary with skills categorized
    """
    categories = {
        'Programming Languages': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'typescript', 'go', 'kotlin', 'swift'],
        'Web Development': ['html', 'css', 'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'wordpress', 'bootstrap'],
        'Data Science': ['machine learning', 'deep learning', 'data analysis', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'nlp'],
        'Database': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'firebase', 'redis', 'nosql', 'sqlite'],
        'DevOps': ['docker', 'kubernetes', 'jenkins', 'ci/cd', 'aws', 'azure', 'gcp', 'terraform', 'ansible'],
        'Other': []
    }
    
    categorized_skills = {category: [] for category in categories}
    
    for skill in skills:
        skill_lower = skill.lower()
        categorized = False
        
        for category, keywords in categories.items():
            if category == 'Other':
                continue
                
            for keyword in keywords:
                if keyword in skill_lower or skill_lower in keyword:
                    categorized_skills[category].append(skill)
                    categorized = True
                    break
            
            if categorized:
                break
        
        if not categorized:
            categorized_skills['Other'].append(skill)
    
    return {k: v for k, v in categorized_skills.items() if v}

def custom_sentence_tokenize(text):
    """
    A simple custom sentence tokenizer as fallback when NLTK's sent_tokenize fails.
    
    Args:
        text (str): Text to tokenize into sentences
        
    Returns:
        list: List of sentences
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_skills_from_pdf(pdf_path):
    """
    Main function to extract skills from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary with extracted skills categorized
    """
    try:
        text = extract_text_from_pdf(pdf_path)
        
        if not text.strip():
            return {"Error": ["No text could be extracted from the PDF. Please check the file and try uploading again."]}
        
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            logger.warning(f"NLTK sentence tokenization failed, retry")
            sentences = custom_sentence_tokenize(text)
        
        tokens = preprocess_text(text)
        
        skills = identify_skills(tokens, sentences)
        
        if not skills:
            return {"Notice": ["No skills were identified in this resume. Try a different file or ensure the resume contains relevant skills."]}
        
        categorized_skills = categorize_skills(skills)
        
        return categorized_skills
    except Exception as e:
        logger.exception(f"Error extracting skills from PDF: {e}")
        return {"Error": [f"An error occurred while processing your resume: {str(e)}"]}
