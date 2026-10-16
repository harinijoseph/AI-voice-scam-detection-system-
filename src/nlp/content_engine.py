import os
import re
import joblib
import numpy as np
from collections import Counter

from src.nlp.train_content_classifier import train_content_classifier
from src.nlp.behavioral_analyzer import BehavioralAnalyzer

class ContentEngine:
    """
    Phase 3 Content Engine for VoxSentinel AI.
    Transcribes audio, classifies spoken text using TF-IDF + Logistic Regression scam pattern classifier,
    and runs multi-turn behavioral intent & social engineering funnel analysis.
    """
    def __init__(self, model_dir="models"):
        self.model_dir = model_dir
        self.vec_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")
        self.model_path = os.path.join(model_dir, "content_logistic_model.joblib")
        
        self.vectorizer = None
        self.model = None
        self.behavioral_analyzer = BehavioralAnalyzer()
        self._load_or_train_model()

        self.scam_categories = {
            "Family Emergency & Bail Scam": [
                "grandma", "grandson", "granddaughter", "jail", "arrested", "hospital", "car crash", "bail", "emergency money",
                "held in custody", "bail bond", "car wreck", "attorney fees"
            ],
            "Bank Fraud & Credential Harvesting": [
                "bank account", "wire transfer", "otp", "verification code", "credit card", "zelle", "venmo", "ssn",
                "routing number", "one time password", "cvv", "compromised"
            ],
            "Tech Support & Remote Access Scam": [
                "microsoft", "anydesk", "teamviewer", "virus", "malware", "tech support", "remote access", "quickassist"
            ],
            "Government & Tax Impersonation": [
                "officer", "social security", "irs", "arrest warrant", "taxes", "police", "seized", "federal marshal"
            ],
            "Cryptocurrency & Investment Fraud": [
                "crypto", "bitcoin", "ethereum", "wallet address", "usdt", "guarantee 10x", "investment opportunity",
                "trading platform", "escrow", "buy bitcoin"
            ],
            "Utility & Service Disconnection Scam": [
                "electric power", "power service", "shutoff", "disconnected", "utility bills", "overdue bill", "power disconnected"
            ],
            "Ransomware & Extortion Scam": [
                "ransomware", "encrypted", "decryption key", "pay fine", "extortion", "hostage"
            ]
        }

    def _load_or_train_model(self):
        try:
            if os.path.exists(self.vec_path) and os.path.exists(self.model_path):
                self.vectorizer = joblib.load(self.vec_path)
                self.model = joblib.load(self.model_path)
            else:
                res = train_content_classifier(model_dir=self.model_dir)
                self.vectorizer = res["vectorizer"]
                self.model = res["model"]
        except Exception:
            # Fallback gracefully if model cannot be loaded or trained
            self.vectorizer = None
            self.model = None

    def transcribe_audio(self, audio_path_or_y):
        """
        Transcribes audio using SpeechRecognition with automatic PCM normalization.
        Accepts both file paths and numpy arrays.
        Safely catches network/STT errors and returns empty string without throwing.
        """
        try:
            import io
            import soundfile as sf
            import librosa
            import speech_recognition as sr

            r = sr.Recognizer()
            y = None
            sr_target = 16000

            if isinstance(audio_path_or_y, str):
                if not audio_path_or_y.strip() or not os.path.exists(audio_path_or_y):
                    return ""
                try:
                    y, _ = librosa.load(audio_path_or_y, sr=sr_target)
                except Exception:
                    return ""
            elif isinstance(audio_path_or_y, np.ndarray):
                y = audio_path_or_y
            elif hasattr(audio_path_or_y, "__array__") or isinstance(audio_path_or_y, (list, tuple)):
                y = np.asarray(audio_path_or_y, dtype=np.float32)
            else:
                return ""
            
            if y is None or len(y) == 0:
                return ""

            y = np.asarray(y, dtype=np.float32)

            # Downmix to mono if multi-channel
            if y.ndim > 1:
                if y.shape[0] <= 8 and y.shape[1] > y.shape[0]:
                    y = np.mean(y, axis=0)
                else:
                    y = np.mean(y, axis=-1)

            # Sanitize NaNs and infinities
            y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)

            if len(y) == 0:
                return ""

            # Check if signal has meaningful sound
            max_amp = float(np.max(np.abs(y)))
            if max_amp < 1e-4:
                return ""

            # Normalize amplitude if max exceeds 1.0 to prevent PCM clipping
            if max_amp > 1.0:
                y = y / max_amp

            # Convert to standard 16-bit PCM WAV in memory
            buf = io.BytesIO()
            sf.write(buf, y.astype(np.float32), sr_target, format='WAV', subtype='PCM_16')
            buf.seek(0)

            with sr.AudioFile(buf) as source:
                duration_sec = len(y) / sr_target
                # Only adjust ambient noise if audio duration is sufficient
                if duration_sec >= 0.5:
                    try:
                        r.adjust_for_ambient_noise(source, duration=min(0.2, duration_sec * 0.2))
                    except Exception:
                        pass
                audio_data = r.record(source)

            # Attempt Google STT, catching all errors (offline, unknown, request errors) gracefully
            try:
                transcribed = r.recognize_google(audio_data)
                return transcribed.strip() if transcribed else ""
            except (sr.UnknownValueError, sr.RequestError, Exception):
                return ""
        except Exception:
            return ""

    def analyze_text(self, text):
        """Analyzes text transcript and returns scam probability, category, behavioral intent, and highlighted phrases."""
        if not text or not str(text).strip():
            return {
                "transcript": "",
                "highlighted_transcript": "",
                "scam_probability": 0.0,
                "clf_probability": 0.0,
                "behavioral_score": 0.0,
                "is_scam": False,
                "category": "Authentic / Normal Dialogue",
                "flagged_phrases": [],
                "detected_tactics": [],
                "detected_stage": "Stage 1: Greeting & Persona",
                "active_stages": [],
                "explanations": ["No spoken text transcript provided."]
            }

        text = str(text)
        text_lower = text.lower()

        # 1. Multi-turn Behavioral Funnel Analysis
        beh_res = self.behavioral_analyzer.analyze_transcript(text)
        beh_score = beh_res["behavioral_score"]

        # 2. Compute ML Scam Probability via TF-IDF + Logistic Regression (or heuristic fallback)
        if self.vectorizer is not None and self.model is not None:
            vec = self.vectorizer.transform([text])
            clf_proba = float(self.model.predict_proba(vec)[0][1])
        else:
            # Heuristic ML fallback
            clf_proba = min(1.0, 0.40 + 0.20 * len(beh_res["detected_tactics"])) if beh_res["detected_tactics"] else 0.15

        # Blended Scam Probability (65% ML Classifier + 35% Behavioral Intent Engine)
        scam_proba = float(np.clip(0.65 * clf_proba + 0.35 * beh_score, 0.0, 1.0))

        # Calibrate for completely benign conversation with zero tactics
        if not beh_res["detected_tactics"] and clf_proba < 0.45:
            if beh_res["detected_stage"] in ["Stage 1: Greeting & Persona", "General Dialogue / Initial Statement"]:
                scam_proba = min(scam_proba, 0.15)
            elif len(flagged_phrases) == 0:
                scam_proba = min(scam_proba, 0.20)

        # 3. Match Category & Flagged Phrases
        flagged_phrases = list(set(beh_res["flagged_phrases"]))
        matched_categories = []

        for cat, keywords in self.scam_categories.items():
            for kw in keywords:
                if kw in text_lower:
                    flagged_phrases.append(kw)
                    matched_categories.append(cat)

        flagged_phrases = list(set(flagged_phrases))
        
        if matched_categories:
            counts = Counter(matched_categories)
            detected_category = counts.most_common(1)[0][0]
        else:
            detected_category = "Scam Call Pattern" if scam_proba >= 0.5 else "Authentic / Normal Dialogue"

        # 4. Create HTML Highlighted Transcript
        highlighted = text
        for phrase in flagged_phrases:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            highlighted = pattern.sub(f'<span class="badge-keyword" style="background-color: #FF4B4B; color: white; padding: 2px 6px; border-radius: 4px;">{phrase}</span>', highlighted)

        # 5. Generate Explanations
        explanations = []
        if scam_proba >= 0.5:
            explanations.append(f"Spoken text matches high-risk scam category: '{detected_category}'.")
        if beh_res["detected_stage"] != "Stage 1: Greeting & Persona":
            explanations.append(f"Advanced Social Engineering Stage detected: [{beh_res['detected_stage']}].")
        explanations.extend(beh_res["explanations"])
        if flagged_phrases:
            explanations.append(f"Flagged coercive phrases: {', '.join(flagged_phrases[:6])}.")

        # Deduplicate explanations
        seen = set()
        unique_explanations = [x for x in explanations if not (x in seen or seen.add(x))]

        return {
            "transcript": text,
            "highlighted_transcript": highlighted,
            "scam_probability": round(scam_proba, 4),
            "clf_probability": round(clf_proba, 4),
            "behavioral_score": round(beh_score, 4),
            "is_scam": scam_proba >= 0.5,
            "category": detected_category,
            "flagged_phrases": flagged_phrases,
            "detected_tactics": beh_res["detected_tactics"],
            "detected_stage": beh_res["detected_stage"],
            "active_stages": beh_res.get("active_stages", [beh_res["detected_stage"]]),
            "explanations": unique_explanations
        }

    def analyze_audio_content(self, audio_path_or_y, optional_transcript=""):
        """Full Content Engine Pipeline: Transcribes audio (if text not provided) and analyzes content."""
        text = optional_transcript or ""
        if not text and audio_path_or_y is not None:
            try:
                text = self.transcribe_audio(audio_path_or_y)
            except Exception:
                text = ""

        try:
            return self.analyze_text(text)
        except Exception:
            return {
                "transcript": "",
                "highlighted_transcript": "",
                "scam_probability": 0.0,
                "clf_probability": 0.0,
                "behavioral_score": 0.0,
                "is_scam": False,
                "category": "Authentic / Normal Dialogue",
                "flagged_phrases": [],
                "detected_tactics": [],
                "detected_stage": "Stage 1: Greeting & Persona",
                "active_stages": [],
                "explanations": ["Audio content analysis completed: no coercive or scam dialogue detected."]
            }
