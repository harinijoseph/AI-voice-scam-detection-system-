import os
import pandas as pd

def prepare_content_dataset(output_path="data/phase3/content_dataset.csv"):
    """
    Prepares Phase 3 Content Dataset containing labeled Scam scripts and Normal text messages.
    Covers 4 key scam categories: Bank Fraud, Tech Support, Family Emergency, Government Impersonation.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    scam_samples = [
        # Bank Fraud & Credential Harvesting
        ("Your bank account has been compromised due to suspicious activity. Wire transfer your funds immediately to a safe account.", "bank_fraud"),
        ("This is the security department. Share your OTP verification code right now to unlock your checking account.", "bank_fraud"),
        ("We detected unauthorized transactions on your credit card. Please verify your SSN and PIN to reverse charges.", "bank_fraud"),
        ("Urgent: your bank account will be frozen within 30 minutes unless you verify your full credit card number.", "bank_fraud"),
        ("Send your one time password immediately to stop pending fraudulent wire transfer of $1,500.", "bank_fraud"),
        ("Financial alert: transfer money to our secure Zelle handle immediately to avoid asset liquidation.", "bank_fraud"),

        # Tech Support Scams
        ("This is Microsoft support calling. Your computer is infected with malware and broadcasting private files.", "tech_support"),
        ("Warning: your Windows license has expired and trojan viruses are downloading. Install AnyDesk for remote access.", "tech_support"),
        ("Apple tech support alert: your iCloud has been hacked. Call us back immediately or your data will be deleted.", "tech_support"),
        ("Download TeamViewer right now so our technician can clear the spyware from your system.", "tech_support"),
        ("Your computer is sending spam emails. Pay $299 tech support subscription via gift cards to fix it.", "tech_support"),

        # Family Emergency & Bail Scams
        ("Grandma please help me! I got into a car crash and I am held in police jail right now. Send bail money via wire transfer.", "family_emergency"),
        ("Mom it's Sarah, my phone broke in an accident. I need $2,000 sent via Zelle right now to pay emergency hospital bill.", "family_emergency"),
        ("Help! Your grandson was arrested overseas. Do not hang up or tell his parents. Send $5,000 cash or gift cards for bail.", "family_emergency"),
        ("Emergency alert: your relative is hospitalized and needs urgent medical payment. Transfer funds immediately.", "family_emergency"),
        ("Please don't tell anyone, I am in big trouble with the law. Send money right away or I will be locked up.", "family_emergency"),

        # Government & Tax Impersonation
        ("This is Officer Davis from the Social Security Administration. An arrest warrant has been issued in your name.", "government_impersonation"),
        ("IRS tax warning: you owe back taxes. Federal marshals will arrive at your home unless you pay via Target gift cards.", "government_impersonation"),
        ("Department of Justice alert: your SSN is linked to drug trafficking. Stay on the line or face immediate arrest.", "government_impersonation"),
        ("Internal Revenue Service final notice: pay your unpaid taxes right now or your property will be seized.", "government_impersonation"),
        ("Police department call: failure to pay fine today will result in an enforcement team executing a search warrant.", "government_impersonation"),
        
        # General Urgent Scam Patterns
        ("Congratulations! You won $50,000 in national lottery. Pay processing fee of $500 via Bitcoin to claim prize.", "lottery_scam"),
        ("You have won a free iPhone! Click link and enter your credit card CVV for shipping charges.", "lottery_scam"),
        ("Job offer: earn $5,000 weekly from home. Send registration fee via Venmo immediately.", "job_scam")
    ]

    normal_samples = [
        ("Hi Mom, just checking in to see if we are still on for dinner on Saturday at 7 PM?", "normal"),
        ("Hello, I would like to schedule a doctor's appointment for next Tuesday afternoon if available.", "normal"),
        ("Hey, did you get a chance to review the project slides I sent over email earlier today?", "normal"),
        ("Your package from Amazon has been delivered to your front door. Thank you for shopping with us.", "normal"),
        ("Good morning team, please remember our weekly status sync is at 10 AM in Conference Room B.", "normal"),
        ("Hey, can you pick up some milk and eggs on your way home from work tonight?", "normal"),
        ("Thanks for calling customer service. Your flight reservation has been confirmed for tomorrow morning.", "normal"),
        ("Happy birthday! Hope you have a wonderful day celebrating with family and friends.", "normal"),
        ("Can we reschedule our dentist appointment to Thursday morning instead?", "normal"),
        ("The library book you requested is now available for pickup at the main counter.", "normal"),
        ("Hey, what time does the grocery store close tonight?", "normal"),
        ("Reminder: trash and recycling pickup is tomorrow morning at 6 AM.", "normal"),
        ("Thanks for the lunch yesterday, it was great catching up with you!", "normal"),
        ("Your monthly utility bill statement is ready to view online. Total balance $45.20.", "normal"),
        ("Hi, I am calling to confirm our meeting time for tomorrow at 2 PM.", "normal")
    ]

    # Duplicate & synthesize to reach ~100 balanced samples
    rows = []
    for text, cat in scam_samples * 4: # ~92 scam rows
        rows.append({"text": text, "label": 1, "category": cat})

    for text, cat in normal_samples * 6: # ~90 normal rows
        rows.append({"text": text, "label": 0, "category": cat})

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Content dataset saved to {output_path} with {len(df)} rows.")
    return df

if __name__ == "__main__":
    prepare_content_dataset()
