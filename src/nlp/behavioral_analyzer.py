import re

class BehavioralAnalyzer:
    """
    Behavioral & Conversational Intent Analyzer for VoxSentinel AI.
    Evaluates text transcripts across multi-turn scam funnels, detecting coercion,
    panic induction, financial traps, credential harvesting, and social engineering funnels.
    """
    def __init__(self):
        self.stage_keywords = {
            "Stage 1: Greeting & Persona": [
                r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgreetings\b", r"\bgood morning\b", r"\bgood afternoon\b", r"\bgood evening\b",
                r"\bcalling from\b", r"\bdepartment\b", r"\bofficer\b", r"\brepresentative\b",
                r"\bcustomer support\b", r"\bfraud prevention\b", r"\bsecurity desk\b", r"\bdispatch\b",
                r"\bagent\b", r"\bthis is\b", r"\bmy name is\b", r"\bspeaking with\b"
            ],
            "Stage 2: Impersonation / Fraud Hook": [
                r"\bbank account\b", r"\bsocial security\b", r"\birs\b", r"\bpolice\b", r"\bsecurity breach\b",
                r"\bgrandson\b", r"\bgranddaughter\b", r"\bhospital\b", r"\bhospitalized\b", r"\baccident\b",
                r"\bcar crash\b", r"\bcar wreck\b", r"\barrest warrant\b", r"\barrested\b", r"\bjail\b",
                r"\bin custody\b", r"\bfederal marshal\b", r"\bcustoms\b", r"\bborder protection\b",
                r"\bcompromised\b", r"\bsuspicious transaction\b", r"\bunauthorized charge\b",
                r"\bcriminal investigation\b", r"\blegal case\b", r"\bpower service\b",
                r"\bransomware\b", r"\bmalware\b", r"\bvirus\b", r"\bkidnapped\b", r"\battorney\b"
            ],
            "Stage 3: Artificial Urgency & Panic": [
                r"\bimmediately\b", r"\bwithin \d+ minutes\b", r"\bright now\b", r"\burgent\b", r"\burgently\b",
                r"\bhurry\b", r"\basap\b", r"\bconsequences\b", r"\bdo not hang up\b", r"\bdon't hang up\b",
                r"\bfreeze your account\b", r"\bjail time\b", r"\blegal action\b", r"\bpower shutoff\b",
                r"\butility disconnect\b", r"\bfinal notice\b", r"\btime sensitive\b", r"\bact immediately\b",
                r"\bpenalty of law\b", r"\bimmediate arrest\b", r"\bbefore officers arrive\b", r"\bdo not tell\b",
                r"\bkeep this private\b", r"\bstay on the line\b", r"\bemergency\b", r"\bdon't tell anyone\b",
                r"\bsecret\b", r"\bquickly\b", r"\bfast\b"
            ],
            "Stage 4: Action Request & Coercion": [
                r"\bbail\b", r"\bbail money\b", r"\bwire\b", r"\bwire transfer\b", r"\bgift card\b",
                r"\botp\b", r"\bverification code\b", r"\bzelle\b", r"\bvenmo\b", r"\bbitcoin\b",
                r"\bcrypto\b", r"\btransfer funds\b", r"\bsend money\b", r"\bmoney\b", r"\bcash\b",
                r"\bdollars\b", r"\b\$\s*\d+\b", r"\bpay\b", r"\bpayment\b", r"\bfee\b", r"\bfine\b",
                r"\bpay immediately\b", r"\bcredit card\b", r"\brouting number\b", r"\bescrow\b",
                r"\bwestern union\b", r"\bmoneygram\b", r"\bcash app\b", r"\banydesk\b", r"\bteamviewer\b",
                r"\bremote access\b", r"\bwallet address\b", r"\bdecryption key\b", r"\bcode\b",
                r"\bpin\b", r"\bpassword\b", r"\bpasscode\b", r"\bcvv\b", r"\bsend\b", r"\btransfer\b", r"\bbuy\b"
            ]
        }

        self.tactic_categories = {
            "FINANCIAL_TRAP": [
                "wire transfer", "gift card", "zelle", "venmo", "bitcoin", "crypto", "bank transfer",
                "pay immediately", "fine payment", "bail money", "transfer funds", "cash app",
                "western union", "moneygram", "apple gift card", "google play", "target card",
                "escrow", "direct wire", "wallet address", "pay with crypto", "send money",
                "bail", "cash", "dollars", "send funds", "pay the fee"
            ],
            "CREDENTIAL_HARVEST": [
                "otp", "verification code", "one time password", "social security number", "ssn",
                "credit card number", "cvv", "pin", "password", "security code", "2fa",
                "routing number", "card number"
            ],
            "ISOLATION_TACTIC": [
                "do not hang up", "don't hang up", "keep this call private", "do not tell your family",
                "stay on the line", "don't call anyone else", "keep this quiet", "confidential investigation",
                "gag order", "do not disclose to anyone"
            ],
            "FAMILY_EMERGENCY_SCAM": [
                "grandson", "granddaughter", "in jail", "car crash", "hospitalized", "kidnapped",
                "held for ransom", "need bail", "emergency money", "bail bond", "bond payment",
                "held in custody", "attorney fees", "car wreck"
            ],
            "TECH_REMOTE_TAKEOVER": [
                "anydesk", "teamviewer", "remote access", "quickassist", "malware detected",
                "virus detected", "grant access", "syskey"
            ],
            "REMOTE_ACCESS_MALWARE": [
                "anydesk", "teamviewer", "remote access", "quickassist", "malware",
                "virus", "remote desktop"
            ],
            "UTILITY_SHUTOFF_COERCION": [
                "power disconnected", "power shutoff", "utility shutoff", "water shutoff",
                "disconnect power", "electric shutoff", "overdue utility bill", "utility bills",
                "will be disconnected", "power service", "shutoff"
            ]
        }

    def analyze_transcript(self, text):
        if not text or not text.strip():
            return {
                "behavioral_score": 0.0,
                "detected_stage": "Stage 1: Greeting & Persona",
                "active_stages": [],
                "detected_tactics": [],
                "flagged_phrases": [],
                "explanations": ["No text transcript detected."]
            }

        text_lower = text.lower()
        flagged_phrases = []
        detected_tactics = []
        stage_counts = {stage: 0 for stage in self.stage_keywords}

        for stage, patterns in self.stage_keywords.items():
            for pat in patterns:
                matches = re.findall(pat, text_lower)
                if matches:
                    stage_counts[stage] += len(matches)

        for category, phrases in self.tactic_categories.items():
            for phrase in phrases:
                if phrase in text_lower:
                    detected_tactics.append(category)
                    flagged_phrases.append(phrase)

        detected_tactics = list(set(detected_tactics))
        flagged_phrases = list(set(flagged_phrases))

        # Map detected tactics to their corresponding stages
        if any(t in detected_tactics for t in ["FINANCIAL_TRAP", "CREDENTIAL_HARVEST", "TECH_REMOTE_TAKEOVER", "REMOTE_ACCESS_MALWARE"]):
            stage_counts["Stage 4: Action Request & Coercion"] = max(stage_counts["Stage 4: Action Request & Coercion"], 1)

        if any(t in detected_tactics for t in ["ISOLATION_TACTIC", "UTILITY_SHUTOFF_COERCION"]):
            stage_counts["Stage 3: Artificial Urgency & Panic"] = max(stage_counts["Stage 3: Artificial Urgency & Panic"], 1)

        if "FAMILY_EMERGENCY_SCAM" in detected_tactics:
            stage_counts["Stage 2: Impersonation / Fraud Hook"] = max(stage_counts["Stage 2: Impersonation / Fraud Hook"], 1)

        active_stages = [stage for stage, count in stage_counts.items() if count > 0]

        if active_stages:
            current_stage = "Stage 1: Greeting & Persona"
            for stage in reversed(list(self.stage_keywords.keys())):
                if stage_counts[stage] > 0:
                    current_stage = stage
                    break
        else:
            current_stage = "General Dialogue / Initial Statement"

        # Baseline stage score
        stages_active = len(active_stages)
        
        if not detected_tactics and current_stage in ["Stage 1: Greeting & Persona", "General Dialogue / Initial Statement"]:
            # Pure benign conversational dialogue
            base_score = 0.05
            progression_score = 0.0
        else:
            base_score = 0.10
            if "Stage 2: Impersonation / Fraud Hook" in current_stage:
                base_score += 0.25
            elif "Stage 3: Artificial Urgency & Panic" in current_stage:
                base_score += 0.45
            elif "Stage 4: Action Request & Coercion" in current_stage:
                base_score += 0.65

            # Multi-turn stage progression bonus
            if stages_active >= 4:
                progression_score = 0.20
            elif stages_active >= 3:
                progression_score = 0.12
            elif stages_active >= 2:
                progression_score = 0.05
            else:
                progression_score = 0.0

        score_boost = len(detected_tactics) * 0.15
        behavioral_score = min(1.0, round(base_score + progression_score + score_boost, 4))

        explanations = []
        if "FINANCIAL_TRAP" in detected_tactics:
            explanations.append("Explicit request for unrecoverable payment (Wire/Crypto/Gift Card/Zelle/Bail) detected.")
        if "CREDENTIAL_HARVEST" in detected_tactics:
            explanations.append("Attempt to harvest sensitive authentication credentials (OTP/SSN/PIN).")
        if "ISOLATION_TACTIC" in detected_tactics:
            explanations.append("Coercive isolation tactic ('Do not hang up') detected to prevent out-of-band verification.")
        if "FAMILY_EMERGENCY_SCAM" in detected_tactics:
            explanations.append("Family emergency impersonation pattern (Bail/Hospital/Ransom) detected.")
        if "TECH_REMOTE_TAKEOVER" in detected_tactics:
            explanations.append("Remote desktop access takeover tactic (AnyDesk/TeamViewer) detected.")
        if "UTILITY_SHUTOFF_COERCION" in detected_tactics:
            explanations.append("Utility shutoff coercion tactic detected with artificial time limits.")

        if stages_active >= 3:
            explanations.append(f"Multi-turn social engineering progression detected across {stages_active} distinct funnel stages.")

        if not explanations and behavioral_score > 0.4:
            explanations.append("Conversational trajectory displays artificial urgency and pressure patterns.")
        elif not explanations:
            explanations.append("Conversational intent appears benign with standard dialogue flow.")

        return {
            "behavioral_score": behavioral_score,
            "detected_stage": current_stage,
            "active_stages": active_stages,
            "detected_tactics": detected_tactics,
            "flagged_phrases": flagged_phrases,
            "explanations": explanations
        }
