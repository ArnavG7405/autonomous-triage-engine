# Blocklisted patterns for instant fast-reject (bypasses LLM, auto-handled)
MALICIOUS_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)system\s*:\s*override",
    r"(?i)drop\s+table",
    r"(?i)bypass\s+security",
    r"(?i)act\s+as\s+a\s+hacker",
    r"(?i)output\s+only\s+P0"
]

# Support domain lexicon for the Bayesian language model P(c)
SUPPORT_VOCAB = {
    "account": 150, "login": 120, "password": 110, "access": 100, "locked": 80,
    "billing": 130, "refund": 120, "charge": 110, "payment": 105, "invoice": 90,
    "cancel": 95, "subscription": 85, "crash": 100, "error": 110, "bug": 115,
    "update": 80, "support": 90, "help": 140, "issue": 100, "broken": 90,
    "feature": 60, "request": 70, "slow": 75, "loading": 70, "furious": 40
}