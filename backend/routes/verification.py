from fastapi import APIRouter
from pydantic import BaseModel
import re

router = APIRouter(prefix="/api/verify", tags=["Verification"])

class CodewordVerificationRequest(BaseModel):
    secret_codeword: str = "BlueSky2024"
    caller_response: str = ""

@router.get("/questions")
def get_challenge_questions():
    return {
        "questions": [
            {
                "id": "q1",
                "category": "Private Episodic Memory",
                "question": "What was the name of our first rescue dog from childhood?",
                "rationale": "Zero-shot voice cloning models trained on social media videos cannot access private, unindexed episodic memory."
            },
            {
                "id": "q2",
                "category": "Idiosyncratic Shared Event",
                "question": "Where did our rental car break down during our trip to the mountains in 2021?",
                "rationale": "High-specificity autobiographical memory foils algorithmic LLM hallucinations and script readers."
            },
            {
                "id": "q3",
                "category": "Pre-Shared Family Codeword",
                "question": "What is our secret emergency passphrase agreed upon at Thanksgiving?",
                "rationale": "Cryptographic out-of-band shared secret. Adversaries cannot guess high-entropy private strings."
            },
            {
                "id": "q4",
                "category": "Disinformation Trap",
                "question": "Did Uncle David lend you his blue jacket before you got arrested?",
                "rationale": "Cognitive honeypot: 'Uncle David' does not exist. An authentic relative immediately objects; an AI or scammer agrees."
            }
        ]
    }

@router.post("/codeword")
def verify_codeword(req: CodewordVerificationRequest):
    secret = req.secret_codeword.strip().lower()
    caller = req.caller_response.strip().lower()

    if not caller:
        return {
            "verified": False,
            "status": "AWAITING_INPUT",
            "type": "warning",
            "title": "Awaiting Spoken Response",
            "summary": "Please enter the caller's answer to the challenge question.",
            "action": "Prompt the caller with your pre-shared question and type their verbatim response."
        }

    # Normalize alphanumeric characters
    clean_secret = re.sub(r'[^a-z0-9]', '', secret)
    clean_caller = re.sub(r'[^a-z0-9]', '', caller)

    is_match = (clean_secret in clean_caller) or (clean_caller in clean_secret) or (clean_secret == clean_caller)

    if is_match and len(clean_caller) >= 3:
        return {
            "verified": True,
            "status": "CONFIRMED",
            "type": "safe",
            "title": "🟢 IDENTITY CONFIRMED: AUTHENTIC FAMILY MEMBER",
            "subtitle": "Challenge question answered correctly with pre-shared episodic memory.",
            "summary": "The caller demonstrated genuine episodic knowledge matching your pre-shared family secret. This confirms physical identity independent of acoustic voice signals.",
            "action": "Proceed with legitimate call. You may safely discuss the matter."
        }
    else:
        return {
            "verified": False,
            "status": "FAILED",
            "type": "danger",
            "title": "🔴 ALERT: ADVERSARIAL CLONE SUSPECTED — VERIFICATION FAILED",
            "subtitle": "Caller failed the pre-shared secret challenge or gave an evasion response.",
            "summary": "The caller could not provide the private passphrase or gave an evasive answer. Voice cloning algorithms scrape vocal timbre from social media videos but have zero access to private family memories.",
            "action": "TERMINATE THIS CALL IMMEDIATELY. Hang up and dial your family member directly on their known, trusted telephone number. Never transfer money, buy gift cards, or post bail."
        }
