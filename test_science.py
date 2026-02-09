import re

def clean_scientific_text(text):
    if not text:
        return ""

    # Handle LaTeX style subscripts/superscripts
    # Old regex: r'\\?\(?_\{([^}]+)\}\\?\)?'
    # Let's try to be more precise. LaTeX often uses \( ... \) as delimiters.
    
    # Remove LaTeX delimiters first or handle them
    text = text.replace(r'\(', '').replace(r'\)', '')
    
    text = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', text)
    text = re.sub(r'_(\d)', r'<sub>\1</sub>', text)
    text = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', text)
    text = re.sub(r'\^(\d)', r'<sup>\1</sup>', text)
    
    # Handle plain text chemical formulas like CO2, H2O (capital letter + digit)
    def chem_sub(match):
        return f"{match.group(1)}<sub>{match.group(2)}</sub>"
    text = re.sub(r'([A-Z][a-z]?)([2-9])', chem_sub, text)
    
    return text.strip()

test_cases = [
    r"\(2NaOH + H_{2}SO_{4} = Na_{2}SO_{4} + 2H_{2}O\)",
    r"CO_{2}",
    r"H_2O",
    r"CO2",
    r"H2SO4",
    r"x^{2} + y^{2} = z^{2}",
    r"10cm^3"
]

for tc in test_cases:
    print(f"In:  {tc}")
    print(f"Out: {clean_scientific_text(tc)}\n")
