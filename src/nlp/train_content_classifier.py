import os
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from src.data.prepare_content_dataset import prepare_content_dataset

def train_content_classifier(data_path="data/phase3/content_dataset.csv", model_dir="models"):
    """
    Phase 3 Content Engine Training Script.
    Trains TF-IDF + Logistic Regression baseline text classifier for scam language detection.
    """
    if not os.path.exists(data_path):
        df = prepare_content_dataset(output_path=data_path)
    else:
        df = pd.read_csv(data_path)

    X_text = df["text"].values
    y = df["label"].values

    # 1. Feature Extraction: TF-IDF Vectorizer (Unigrams + Bigrams)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=2000, stop_words='english')
    X_vec = vectorizer.fit_transform(X_text)

    # 2. Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42, stratify=y)

    # 3. Train Logistic Regression Classifier
    clf = LogisticRegression(C=1.0, solver='lbfgs', random_state=42)
    clf.fit(X_train, y_train)

    # 4. Predictions & Evaluation
    y_pred = clf.predict(X_test)
    y_scores = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    # Top Informative Scam Keywords (highest positive logistic regression coefficients)
    feature_names = np.array(vectorizer.get_feature_names_out())
    coefs = clf.coef_[0]
    top_indices = np.argsort(coefs)[::-1][:10]
    top_scam_keywords = [(feature_names[i], round(float(coefs[i]), 4)) for i in top_indices]

    # Save artifacts
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(model_dir, "tfidf_vectorizer.joblib"))
    joblib.dump(clf, os.path.join(model_dir, "content_logistic_model.joblib"))

    print("\n" + "=" * 50)
    print("📈 PHASE 3 CONTENT CLASSIFIER EVALUATION")
    print("=" * 50)
    print(f"Accuracy  : {acc * 100:.2f}%")
    print(f"Precision : {prec * 100:.2f}%")
    print(f"Recall    : {rec * 100:.2f}%")
    print(f"F1-Score  : {f1 * 100:.2f}%")
    print("\nConfusion Matrix [TN FP / FN TP]:")
    print(cm)
    print("\nTop Informative Scam Keywords (Highest Log Odds Weight):")
    for kw, weight in top_scam_keywords:
        print(f"  - '{kw}': +{weight}")

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm,
        "top_keywords": top_scam_keywords,
        "vectorizer": vectorizer,
        "model": clf
    }

if __name__ == "__main__":
    train_content_classifier()
