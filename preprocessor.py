import re
from typing import Tuple, Optional
from collections import Counter
from config import MALICIOUS_PATTERNS, SUPPORT_VOCAB

class BayesianCorrector:
    """Implements Peter Norvig's Noisy Channel Model: P(c|w) ∝ P(w|c) * P(c)"""
    def __init__(self, vocab_counts: dict):
        self.words = Counter(vocab_counts)
        self.N = sum(self.words.values())

    def P(self, word: str) -> float:
        return self.words[word] / self.N if word in self.words else 0.0

    def edits1(self, word: str) -> set:
        letters = 'abcdefghijklmnopqrstuvwxyz'
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def known(self, words: set) -> set:
        return set(w for w in words if w in self.words)

    def correct_word(self, word: str) -> str:
        candidates = self.known([word]) or self.known(self.edits1(word)) or [word]
        return max(candidates, key=self.P)

    def normalize(self, text: str) -> str:
        words = re.findall(r'\w+', text.lower())
        corrected = [self.correct_word(w) for w in words]
        return " ".join(corrected)


class Preprocessor:
    def __init__(self):
        self.corrector = BayesianCorrector(SUPPORT_VOCAB)

    def process(self, raw_text: str) -> Tuple[str, Optional[dict]]:
        stripped = raw_text.strip()
        
        # 1. Unicode-aware empty / non-alphanumeric check
        if not any(char.isalnum() for char in stripped):
            return stripped, {
                "category": "Uncategorized",
                "priority": "P3",
                "summary": "Empty or non-alphanumeric message.",
                "suggested_action": "Auto-request clarification",
                "needs_human": False,
                "confidence": 100
            }

        # 2. Fast-Reject Security Shield
        for pattern in MALICIOUS_PATTERNS:
            if re.search(pattern, stripped):
                return stripped, {
                    "category": "Security_Spam",
                    "priority": "P3",
                    "summary": "Adversarial or prompt injection attempt detected.",
                    "suggested_action": "Silently drop / Auto-block",
                    "needs_human": False,
                    "confidence": 100
                }

        # 3. Language Check (Devanagari / Non-ASCII bypasses English Bayesian spellchecker)
        non_ascii_ratio = len(re.findall(r'[^\x00-\x7F]', stripped)) / max(len(stripped), 1)
        if non_ascii_ratio > 0.3:
            return stripped, None  # Send raw text directly to LLM for translation

        # 4. Bayesian Normalization for English text
        normalized = self.corrector.normalize(stripped)
        return normalized, None