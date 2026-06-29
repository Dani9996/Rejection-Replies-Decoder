"""
Job Rejection Email Detector
=============================

Analyzes the text of an email and estimates two things:

  1. AUTOMATED / TEMPLATED  -> Was this a mass-mailed, boilerplate rejection
                               (as opposed to a personally written reply)?
  2. AI-GENERATED           -> Does the wording show patterns typical of
                               text produced by a large language model?

IMPORTANT: Neither result is a proof. Email text alone cannot definitively
prove who or what wrote it. This tool scores *signals* and returns a
confidence estimate. Treat the output as a heuristic, not a verdict.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Signal dictionaries
# ---------------------------------------------------------------------------

# Boilerplate phrases very common in mass / templated rejection emails.
TEMPLATE_PHRASES = [
    r"thank you for (your )?(interest|application|applying)",
    r"after (careful(ly)? )?(consider(ing|ation)|review(ing)?)",
    r"we (have )?decided (not )?to (move|proceed) forward",
    r"we will not be (moving|proceeding) forward",
    r"other candidates",
    r"more closely (match(ed|es)?|align(ed|s)?)",
    r"we (regret|are sorry) to inform you",
    r"we encourage you to (apply|re-?apply)",
    r"keep your (resume|details|information) on file",
    r"we wish you (the best|success|luck)",
    r"future opportunit(y|ies)",
    r"a (large|high) (number|volume) of applicat",
    r"do not reply to this (email|message)",
    r"this (is|was) an automated",
    r"unfortunately,? (we|at this time)",
    r"competitive (pool|field)",
    r"not (a |to )?(move|proceed) (to|with) the next (stage|step|round)",
]

# Stylistic / structural patterns disproportionately common in LLM output.
AI_PHRASES = [
    r"i (completely )?understand (that|how)",
    r"please (don'?t|do not) hesitate to",
    r"i hope this (email|message) finds you well",
    r"i wanted to (personally )?reach out",
    r"while your (background|experience|qualifications) (is|are|were) impressive",
    r"we were (truly |genuinely )?impressed",
    r"it'?s clear that you",
    r"rest assured",
    r"i want to (acknowledge|recognize)",
    r"navigating (this|the) (process|journey)",
    r"i (truly|genuinely|sincerely) appreciate",
    r"that (said|being said)",
    r"a testament to",
    r"speaks volumes",
    r"wealth of (experience|knowledge)",
    r"in today'?s (competitive|fast-?paced)",
]

# Words LLMs over-use relative to baseline human writing.
AI_LEXICAL = [
    "delve", "moreover", "furthermore", "additionally", "consequently",
    "underscore", "underscores", "holistic", "robust", "leverage",
    "tapestry", "realm", "landscape", "comprehensive", "nuanced",
    "pivotal", "showcase", "elevate", "seamless", "synergy",
    "esteemed", "endeavor", "foster", "embark",
]

# Telltale machine/header markers of automated send infrastructure.
AUTOMATION_HEADERS = [
    r"no-?reply@",
    r"do-?not-?reply@",
    r"noreply@",
    r"automated@",
    r"mailer-?daemon",
    r"unsubscribe",
    r"ref(erence)?\s*(#|no\.?|number)\s*[:#]?\s*\w+",
    r"requisition\s*(id|#|number)",
    r"\bATS\b",
    r"powered by (greenhouse|lever|workday|icims|taleo|smartrecruiters)",
]


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class Analysis:
    automated_score: float = 0.0          # 0..1
    ai_score: float = 0.0                 # 0..1
    automated_hits: List[str] = field(default_factory=list)
    ai_hits: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def is_automated(self) -> bool:
        return self.automated_score >= 0.5

    @property
    def is_ai_generated(self) -> bool:
        return self.ai_score >= 0.5

    def label(self, score: float) -> str:
        if score >= 0.75:
            return "very likely"
        if score >= 0.5:
            return "likely"
        if score >= 0.25:
            return "possible"
        return "unlikely"


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def _find(patterns, text) -> List[str]:
    hits = []
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            hits.append(m.group(0).strip())
    return hits


def analyze(text: str) -> Analysis:
    """Run all detectors over a raw email string and return an Analysis."""
    a = Analysis()
    lowered = text.lower()
    words = re.findall(r"[a-z']+", lowered)
    n_words = max(len(words), 1)

    # --- Automated / templated signals ---------------------------------
    tmpl_hits = _find(TEMPLATE_PHRASES, text)
    head_hits = _find(AUTOMATION_HEADERS, text)
    a.automated_hits = tmpl_hits + head_hits

    # Score: template phrases are strong; headers are very strong.
    tmpl_component = min(len(tmpl_hits) / 4.0, 1.0) * 0.7
    head_component = min(len(head_hits) / 2.0, 1.0) * 0.6
    auto = tmpl_component + head_component

    # Lack of any personal token (a name in greeting) nudges automated up.
    if not re.search(r"^(hi|hello|dear)\s+[a-z][a-z'.-]+", text.strip(),
                     flags=re.IGNORECASE | re.MULTILINE):
        auto += 0.1
        a.notes.append("No personalized greeting with a first name detected.")

    a.automated_score = round(min(auto, 1.0), 2)

    # --- AI-generation signals -----------------------------------------
    ai_phrase_hits = _find(AI_PHRASES, text)
    lex_hits = [w for w in AI_LEXICAL if re.search(rf"\b{re.escape(w)}\b", lowered)]
    a.ai_hits = ai_phrase_hits + [f"word:{w}" for w in lex_hits]

    phrase_component = min(len(ai_phrase_hits) / 3.0, 1.0) * 0.55
    lex_density = len(lex_hits) / (n_words / 100.0)   # hits per 100 words
    lex_component = min(lex_density / 2.0, 1.0) * 0.35

    # Very even sentence length is a weak LLM tell.
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    if len(sentences) >= 4:
        lengths = [len(s.split()) for s in sentences]
        mean = sum(lengths) / len(lengths)
        var = sum((l - mean) ** 2 for l in lengths) / len(lengths)
        if mean > 8 and var < 12:
            a.notes.append("Sentence lengths are unusually uniform.")
            a.ai_score_uniform = 0.1
            phrase_component += 0.1

    a.ai_score = round(min(phrase_component + lex_component, 1.0), 2)

    if not a.automated_hits and not a.ai_hits:
        a.notes.append("Few or no signal phrases found; result is low-confidence.")

    return a
