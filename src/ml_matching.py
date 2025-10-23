
"""
ml_matching.py
Feature 8: AI-Powered Matching
--------------------------------
This module provides an interface for advanced matching driven by NLP and simple predictive
analytics. It is designed to *optionally* use scikit-learn if available. If not, it falls back to
pure-Python implementations so the app still runs without extra dependencies.

Inputs expected by `AIMatcher.score_team()`:
- survey_free_text: list[str] free-text answers from team members
- numeric_features: dict[str, float] aggregated numeric features (e.g., skills coverage, availability harmony)
- pairwise_features: dict[str, float] pairwise compatibility features

Outputs:
- score: float in [0, 1], higher = better predicted success/compatibility

Training data (optional):
If you have 10 years of labeled historical capstone data, place a CSV at data/historical_labels.csv
with columns like:
team_id,year,free_text,skills_coverage,availability_harmony,pairwise_synergy,success_label

Run-time will auto-train a simple model if scikit-learn is installed; otherwise falls back to a
weighted heuristic with learned weights persisted to data/learned_weights.json if labels are present.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import math, re, json, os, statistics, random

# Attempt optional imports
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score
    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover
    SKLEARN_AVAILABLE = False

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WEIGHTS_FILE = os.path.join(DATA_DIR, "learned_weights.json")
HISTORICAL_FILE = os.path.join(DATA_DIR, "historical_labels.csv")

# Very small sentiment lexicon (fallback). You can extend this list or plug in VADER if available.
POS_WORDS = {
    "great","good","excellent","love","cooperative","teamwork","supportive","helpful","reliable",
    "positive","productive","motivated","enthusiastic","respectful","friendly","aligned"
}
NEG_WORDS = {
    "bad","poor","hate","lazy","conflict","toxic","unreliable","late","negative","unmotivated",
    "disrespectful","hostile","argumentative","misaligned"
}

def simple_sentiment(text: str) -> float:
    """Return sentiment in [-1, 1] using a tiny lexicon."""
    words = re.findall(r"[a-zA-Z']+", (text or "").lower())
    if not words:
        return 0.0
    pos = sum(1 for w in words if w in POS_WORDS)
    neg = sum(1 for w in words if w in NEG_WORDS)
    score = (pos - neg) / max(1, (pos + neg))
    return max(-1.0, min(1.0, score))

def aggregate_sentiment(texts: List[str]) -> float:
    if not texts:
        return 0.0
    vals = [simple_sentiment(t) for t in texts if isinstance(t, str)]
    return statistics.fmean(vals) if vals else 0.0

@dataclass
class TeamFeatures:
    free_texts: List[str]
    numeric_features: Dict[str, float]
    pairwise_features: Dict[str, float]

class AIMatcher:
    def __init__(self) -> None:
        self._pipeline: Optional[Any] = None
        self._weights: Dict[str, float] = {
            # Default heuristic weights if we don't have learned ones
            "sentiment": 0.25,
            "skills_coverage": 0.30,
            "availability_harmony": 0.20,
            "pairwise_synergy": 0.25,
        }
        self._bias: float = 0.0
        # Attempt to load learned weights (for fallback heuristic path)
        if os.path.exists(WEIGHTS_FILE):
            try:
                data = json.load(open(WEIGHTS_FILE, "r"))
                self._weights.update(data.get("weights", {}))
                self._bias = float(data.get("bias", 0.0))
            except Exception:
                pass

        # If sklearn available and historical labels exist, auto-train
        if SKLEARN_AVAILABLE and os.path.exists(HISTORICAL_FILE):
            try:
                self._train_with_sklearn(HISTORICAL_FILE)
            except Exception:
                # Fallback silently if training fails; keep heuristic
                pass

    # Sklearn path: train a simple TFIDF + Logistic Regression on success labels
    def _train_with_sklearn(self, csv_path: str) -> None:
        import csv
        X_text = []
        X_num = []
        y = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                X_text.append(row.get("free_text", ""))
                X_num.append([
                    float(row.get("skills_coverage", 0) or 0),
                    float(row.get("availability_harmony", 0) or 0),
                    float(row.get("pairwise_synergy", 0) or 0),
                ])
                y.append(int(row.get("success_label", 0)))

        # Build a simple text model
        text_model = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1,2))),
            ("clf", LogisticRegression(max_iter=1000))
        ])
        X_train, X_test, y_train, y_test = train_test_split(X_text, y, test_size=0.2, random_state=42)
        text_model.fit(X_train, y_train)
        try:
            proba = text_model.predict_proba(X_test)[:,1]
            auc = roc_auc_score(y_test, proba)
            # print(f"[AIMatcher] Text AUC={auc:.3f}")
        except Exception:
            pass
        self._pipeline = text_model

        # Learn linear weights on numeric features by simple correlation-based heuristic
        # (we avoid an extra dependency; for better results, fit a regression)
        def corr(xs, ys):
            if len(xs) < 3:
                return 0.0
            m_x, m_y = statistics.fmean(xs), statistics.fmean(ys)
            num = sum((a-m_x)*(b-m_y) for a,b in zip(xs, ys))
            den = math.sqrt(sum((a-m_x)**2 for a in xs) * sum((b-m_y)**2 for b in ys))
            return (num/den) if den else 0.0

        cols = list(zip(*X_num)) if X_num else [[],[],[]]
        labels = y
        keys = ["skills_coverage","availability_harmony","pairwise_synergy"]
        for i, key in enumerate(keys):
            r = corr(cols[i], labels) if cols and i < len(cols) else 0.0
            self._weights[key] = max(0.0, r)

        # Normalize weights and set bias (small default)
        s = sum(self._weights[k] for k in keys)
        if s > 0:
            for k in keys:
                self._weights[k] /= s
        self._weights["sentiment"] = 0.25  # keep text weight reasonable
        self._bias = 0.0

        # Persist fallback weights for runs without sklearn
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            json.dump({"weights": self._weights, "bias": self._bias}, open(WEIGHTS_FILE, "w"))
        except Exception:
            pass

    def score_team(self, feats: TeamFeatures) -> float:
        # 1) Text sentiment as robust fallback signal
        sent = aggregate_sentiment(feats.free_texts)

        # 2) If sklearn pipeline exists, combine its probability with sentiment
        text_score = None
        if self._pipeline is not None:
            try:
                # Join free-text answers as a single document
                doc = " ".join(t for t in feats.free_texts if isinstance(t, str))
                prob = float(self._pipeline.predict_proba([doc])[0][1])
                text_score = prob
            except Exception:
                text_score = None

        if text_score is None:
            # Map sentiment [-1,1] to [0,1]
            text_score = (sent + 1.0) / 2.0

        # 3) Numeric & pairwise features
        sc = float(feats.numeric_features.get("skills_coverage", 0.0))
        ah = float(feats.numeric_features.get("availability_harmony", 0.0))
        ps = float(feats.pairwise_features.get("pairwise_synergy", 0.0))

        # 4) Weighted combination
        w = self._weights
        raw = (
            w.get("sentiment", 0.25) * text_score +
            w.get("skills_coverage", 0.30) * sc +
            w.get("availability_harmony", 0.20) * ah +
            w.get("pairwise_synergy", 0.25) * ps +
            self._bias
        )

        # Clamp to [0,1]
        return max(0.0, min(1.0, raw))

# Helper to compute simple features from Student objects
def compute_team_features(students: list, project_texts: Optional[List[str]] = None) -> TeamFeatures:
    free_texts = []
    skills = {}
    availability_vals = []
    pairwise_agreements = []

    for s in students:
        # Pretend teammate_ranks and workstyle/meeting_pref include text we can analyze
        free_texts.extend([getattr(s, "workstyle", ""), getattr(s, "meeting_pref", "")])
        # Skills aggregation (coverage = fraction of skills above threshold)
        for k, v in getattr(s, "skills", {}).items():
            skills[k] = max(skills.get(k, 0), v)
        # Availability harmony as 1 - normalized variance
        if hasattr(s, "availability"):
            availability_vals.append(float(s.availability))

        # Pairwise agreement: simple overlap in teammate preferences
    for i in range(len(students)):
        for j in range(i+1, len(students)):
            a = set(getattr(students[i], "teammate_ranks", []) or [])
            b = set(getattr(students[j], "teammate_ranks", []) or [])
            if a or b:
                inter = len(a & b)
                union = len(a | b) or 1
                pairwise_agreements.append(inter/union)

    skills_coverage = 0.0
    if skills:
        # Consider coverage as average of normalized skill strengths (0..1)
        vals = [min(1.0, v/5.0) for v in skills.values()]  # assume skills 0..5 scale
        skills_coverage = statistics.fmean(vals) if vals else 0.0

    availability_harmony = 1.0
    if availability_vals:
        mu = statistics.fmean(availability_vals)
        var = statistics.variance(availability_vals) if len(availability_vals) > 1 else 0.0
        # normalize assuming availabilities are 0..1; higher variance => worse harmony
        availability_harmony = max(0.0, 1.0 - var)

    pairwise_synergy = statistics.fmean(pairwise_agreements) if pairwise_agreements else 0.5

    return TeamFeatures(
        free_texts=free_texts + (project_texts or []),
        numeric_features={
            "skills_coverage": skills_coverage,
            "availability_harmony": availability_harmony
        },
        pairwise_features={"pairwise_synergy": pairwise_synergy}
    )
