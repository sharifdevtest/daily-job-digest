import re

def extract_salary(text):
    """Extracts LPA (INR), USD, AED, SAR, and EUR salary patterns from job text."""
    if not text:
        return "Not Specified"
        
    patterns = [
        # Explicit Range: AED 20,000 - 30,000 / $100k - $120k / 25-30 LPA
        r'(?i)(?:AED|SAR|USD|₹|\$|€)\s*\d+(?:,\d+)*(?:\s*-\s*\d+(?:,\d+)*)?(?:\s*(?:k|lpa|lacs|lakhs|per month|pm|per annum|pa))?',
        r'(?i)\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*(?:lpa|lacs|lakhs|k|aed|sar|usd|\$|€)',
        r'(?i)\b\d{2,3}k\s*-\s*\d{2,3}k\b',
        r'(?i)(\d+(?:\.\d+)?\s*lpa)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
            
    return "Not Specified"

def extract_hiring_manager(text):
    """Extracts recruiter, headhunter, or contact names from job text."""
    if not text:
        return "Not Found"
        
    patterns = [
        r'(?i)(?:posted by|contact|hiring manager|recruiter|headhunter|consultant):\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'(?i)(?:reach out to|email|written by)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'(?i)recruiter\s*-\s*([A-Z][a-z]+\s+[A-Z][a-z]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
            
    return "Not Found"

def extract_contact_email(text):
    """Extracts direct contact emails from job details."""
    if not text:
        return "N/A"
        
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if match:
        return match.group(0).strip()
        
    return "N/A"