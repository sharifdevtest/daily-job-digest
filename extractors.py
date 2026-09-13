import re

def extract_salary(text):
    """Extracts LPA (INR), USD, AED, and EUR salary patterns."""
    if not text:
        return "Not Specified"
        
    patterns = [
        r'(?i)(\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*(?:lpa|lacs|lakhs|k|aed|usd|\$|€))',
        r'(?i)(?:₹|\$|€|AED)\s*\d+(?:,\d+)*(?:\s*-\s*\d+(?:,\d+)*)?(?:\s*(?:lpa|k|per annum|monthly))?',
        r'(?i)(\d+(?:\.\d+)?\s*lpa)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
            
    return "Not Specified"

def extract_hiring_manager(text):
    """Extracts headhunter or contact names from scraped job text."""
    if not text:
        return "Not Found"
        
    patterns = [
        r'(?i)(?:posted by|contact|hiring manager|recruiter|headhunter):\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'(?i)(?:reach out to|email)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
            
    return "Not Found"