# Sample rule-based detection
if "phone number" in text or "email" in text:
    flagged = True
    issue = "Data Privacy Violation"
else:
    flagged = False
    issue = "None"
