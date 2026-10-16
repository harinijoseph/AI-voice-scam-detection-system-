import os
import numpy as np
from src.audio.acoustic_analyzer import AcousticAnalyzer
from src.audio.acoustic_visualizer import generate_acoustic_visuals
from src.nlp.content_engine import ContentEngine

def _default_acoustic_result():
    return {
        "synthetic_probability": 0.50,
        "is_synthetic": False,
        "feature_summary": {
            "pitch_jitter": 0.0,
            "shimmer": 0.0,
            "shimmer_local": 0.0,
            "centroid": 0.0,
            "spectral_centroid_mean": 0.0,
            "flatness": 0.0,
            "spectral_flatness_mean": 0.0,
            "zcr": 0.0,
            "zero_crossing_rate_mean": 0.0,
            "inst_freq_std": 0.0,
            "spec_entropy_std": 0.0,
            "spec_flux_mean": 0.0,
            "delta_mfcc_std": 0.0,
            "lfcc_mean_1": 0.0,
            "cqcc_mean_1": 0.0,
            "ssl_mean_1": 0.0
        },
        "explanations": ["Acoustic forensics: Signal evaluation unavailable or defaulted."]
    }

def _default_content_result(transcript=""):
    return {
        "transcript": transcript or "",
        "highlighted_transcript": transcript or "",
        "scam_probability": 0.0,
        "clf_probability": 0.0,
        "behavioral_score": 0.0,
        "is_scam": False,
        "category": "Authentic / Normal Dialogue",
        "flagged_phrases": [],
        "detected_tactics": [],
        "detected_stage": "Stage 1: Greeting & Persona",
        "active_stages": [],
        "explanations": ["Content forensics: Text analysis completed with neutral baseline."]
    }

def _default_visuals():
    import plotly.graph_objects as go
    fig_empty = go.Figure()
    fig_empty.update_layout(title="Visualizer Unavailable", height=320)
    return {
        "pitch_fig": fig_empty,
        "spectrogram_fig": fig_empty,
        "pitch_metrics": {"f0_mean": 0.0, "f0_std": 0.0},
        "spectrogram_metrics": {"anomaly_frame_count": 0, "total_frames": 0}
    }

class Phase4FusionEngine:
    """
    Phase 4 Fusion Layer for VoxSentinel AI.
    Integrates Phase 1/2 Acoustic Forensics Engine and Phase 3 Content NLP Engine into a unified Risk Score.
    Provides explicit engine contribution breakdowns and generates Out-of-Band Verification Challenges.
    """
    def __init__(self, w_acoustic=0.50, w_content=0.50):
        self.w_acoustic = w_acoustic
        self.w_content = w_content
        self.acoustic_analyzer = AcousticAnalyzer()
        self.content_engine = ContentEngine()

    def analyze_audio_call(self, audio_path_or_y, optional_transcript="", sr=16000):
        """
        Runs full multimodal analysis pipeline:
        Audio -> Acoustic Engine -> Content Engine -> Visualizer -> Fusion Engine
        Wraps all sub-engines in defensive checks to guarantee valid output dictionary.
        """
        # 1. Acoustic Engine Evaluation (Phase 1)
        try:
            ac_res = self.acoustic_analyzer.analyze_audio_file(audio_path_or_y, sr=sr)
            if not isinstance(ac_res, dict) or "synthetic_probability" not in ac_res:
                ac_res = _default_acoustic_result()
        except Exception as e:
            ac_res = _default_acoustic_result()
            ac_res["explanations"].append(f"Acoustic Engine Notice: Fallback used ({type(e).__name__}).")

        ac_score = float(np.nan_to_num(ac_res.get("synthetic_probability", 0.50), nan=0.50))
        ac_score = float(np.clip(ac_score, 0.0, 1.0))

        # 2. Content Engine Evaluation (Phase 3)
        try:
            cnt_res = self.content_engine.analyze_audio_content(audio_path_or_y, optional_transcript=optional_transcript)
            if not isinstance(cnt_res, dict) or "scam_probability" not in cnt_res:
                cnt_res = _default_content_result(transcript=optional_transcript)
        except Exception as e:
            cnt_res = _default_content_result(transcript=optional_transcript)
            cnt_res["explanations"].append(f"Content Engine Notice: Fallback used ({type(e).__name__}).")

        cnt_score = float(np.nan_to_num(cnt_res.get("scam_probability", 0.0), nan=0.0))
        cnt_score = float(np.clip(cnt_score, 0.0, 1.0))

        # 3. Acoustic Visualizations (Phase 2)
        try:
            visuals = generate_acoustic_visuals(audio_path_or_y, sr=sr)
            if not isinstance(visuals, dict) or "pitch_fig" not in visuals:
                visuals = _default_visuals()
        except Exception:
            visuals = _default_visuals()

        # 4. Weighted Risk Score Fusion Calculation
        overall_risk_score = (self.w_acoustic * ac_score) + (self.w_content * cnt_score)

        # Synergy boost: If both acoustic synthetic probability AND scam content are elevated
        if ac_score >= 0.50 and cnt_score >= 0.50:
            overall_risk_score = min(1.0, overall_risk_score + 0.10)

        overall_risk_score = round(float(np.clip(overall_risk_score, 0.0, 1.0)), 4)

        # 5. Risk Category Assignment (Distinguishing AI Synthetic Clone vs Human Voice Scam)
        if overall_risk_score >= 0.65:
            if ac_score >= 0.50:
                risk_category = "HIGH RISK / AI SCAM DETECTED"
                risk_color = "#FF4B4B" # Red
            else:
                risk_category = "HIGH RISK / HUMAN VOICE SCAM"
                risk_color = "#EA580C" # Matte Orange
        elif overall_risk_score >= 0.35:
            if ac_score >= 0.50:
                risk_category = "MODERATE RISK / AI VOICE DETECTED"
                risk_color = "#7C3AED" # Purple
            else:
                risk_category = "MODERATE RISK / CAUTION"
                risk_color = "#FFAA00" # Amber
        else:
            risk_category = "LOW RISK / AUTHENTIC"
            risk_color = "#00CC66" # Green

        # Engine Contribution Breakdown
        breakdown = {
            "acoustic_contribution": round(self.w_acoustic * ac_score, 4),
            "content_contribution": round(self.w_content * cnt_score, 4),
            "w_acoustic": self.w_acoustic,
            "w_content": self.w_content
        }

        # 6. Out-of-Band Challenge Protocol (Paper #3 Defense)
        challenge_triggered = False
        challenge_prompt = None

        detected_tactics = cnt_res.get("detected_tactics", []) or []
        flagged_phrases = cnt_res.get("flagged_phrases", []) or []
        category = cnt_res.get("category", "") or ""
        is_scam = bool(cnt_res.get("is_scam", False))

        is_emergency = category == "Family Emergency & Bail Scam" or "FAMILY_EMERGENCY_SCAM" in detected_tactics
        is_credential_trap = "CREDENTIAL_HARVEST" in detected_tactics
        is_isolation_tactic = "ISOLATION_TACTIC" in detected_tactics
        is_high_coercion = len(flagged_phrases) >= 2 or is_scam or is_isolation_tactic

        if is_emergency or is_credential_trap or (ac_score >= 0.40 and is_high_coercion) or overall_risk_score >= 0.50:
            challenge_triggered = True
            if is_emergency:
                challenge_prompt = {
                    "title": "🛡️ Emergency Familiar Voice Verification Challenge Prompt",
                    "action": "Caller claims a family emergency. Do NOT wire money or panic. Immediately verify caller using an out-of-band secret question.",
                    "examples": [
                        "What was the name of our childhood pet in 2018?",
                        "What street did grandma live on?",
                        "What is our secret family codeword?"
                    ]
                }
            elif is_credential_trap:
                challenge_prompt = {
                    "title": "🛡️ Credential & Financial Isolation Defense Protocol",
                    "action": "Caller is demanding one-time verification codes (OTP) or immediate wire transfers. Legitimate institutions never ask for full security credentials over an unverified inbound call.",
                    "examples": [
                        "Never read back SMS verification codes or passcodes over the phone.",
                        "Hang up immediately and call back using the verified number on the back of your card.",
                        "Refuse to transfer funds via Zelle, Bitcoin, or prepaid gift cards."
                    ]
                }
            else:
                challenge_prompt = {
                    "title": "🛡️ Out-of-Band Challenge Verification Prompt",
                    "action": "High synthetic audio signature and coercive language detected. Verify caller out-of-band.",
                    "examples": [
                        "Hang up immediately and call back on the official published service number.",
                        "Ask caller for their official badge/employee ID and supervisor extension.",
                        "Never share OTP verification codes or credit card details over the phone."
                    ]
                }

        # Synthesize explanations
        explanations = list(ac_res.get("explanations", [])) + list(cnt_res.get("explanations", []))
        seen = set()
        unique_explanations = [x for x in explanations if not (x in seen or seen.add(x))]

        return {
            "overall_risk_score": overall_risk_score,
            "risk_category": risk_category,
            "risk_color": risk_color,
            "engine_breakdown": breakdown,
            "acoustic_result": ac_res,
            "content_result": cnt_res,
            "visuals": visuals,
            "challenge_triggered": challenge_triggered,
            "challenge_prompt": challenge_prompt,
            "explanations": unique_explanations
        }
