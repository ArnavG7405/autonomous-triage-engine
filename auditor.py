import re

class Auditor:
    @staticmethod
    def audit(decision: dict, original_text: str) -> dict:
        """Audits the generated decision against the original text to calibrate confidence."""
        text_lower = original_text.lower()

        # 1. Check for extreme brevity with low clarity
        words = original_text.strip().split()
        if len(words) <= 3 and decision["category"] not in ["Security_Spam", "Uncategorized"]:
            if decision["confidence"] > 80:
                decision["confidence"] = 70
                decision["needs_human"] = True

        # 2. Force human escalation for non-English / native script inquiries
        if len(re.findall(r'[^\x00-\x7F]', original_text)) > 0 and decision["category"] != "Uncategorized":
            decision["needs_human"] = True

        # 3. Force human escalation for broken authentication / lockouts
        auth_fail_keywords = ["not working", "cant access", "can't access", "cannot access", "locked out", "invalido", "invalid"]
        if ("password" in text_lower or "acount" in text_lower or "account" in text_lower or "login" in text_lower) and any(kw in text_lower for kw in auth_fail_keywords):
            decision["needs_human"] = True

        # 4. Hard-override for legal / chargeback escalations
        legal_keywords = ["sue", "lawyer", "attorney", "chargeback", "police", "fraud", "gdpr"]
        if any(kw in text_lower for kw in legal_keywords):
            decision["priority"] = "P0"
            decision["needs_human"] = True
            decision["confidence"] = max(decision["confidence"], 95)

        # 5. FAQ Fast-Lane (Force routine informational queries to P3)
        if "invoice" in text_lower and ("download" in text_lower or "where" in text_lower):
            decision["priority"] = "P3"
            decision["needs_human"] = False
            decision["confidence"] = max(decision["confidence"], 95)

        # 6. Confidence threshold enforcement
        if decision["confidence"] < 75:
            decision["needs_human"] = True

        return decision