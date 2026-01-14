"""
Lease clause classification module
Uses fine-tuned ALBERT model for 26-class lease clause classification
"""
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.config import MODEL_PATH, LEASE_LABEL_MAP


class LeaseLegalClassifier:
    """
    Classifier for lease agreement clauses.

    Identifies 26 different types of clauses including:
    - Dates (start, end, signing, expiration)
    - Parties (lessor, lessee)
    - Financial terms (rent, VAT, payment terms)
    - Red flags and problematic clauses
    - Structural elements (clause numbers, titles, definitions)
    - And more...
    """

    def __init__(self, model_path=MODEL_PATH, label_map=LEASE_LABEL_MAP, temperature=1.0):
        """
        Initialize the classifier.

        Args:
            model_path: Path to fine-tuned ALBERT model
            label_map: Dictionary mapping label indices to clause types
            temperature: Temperature scaling for confidence calibration
        """
        self.label_map = label_map
        self.temperature = temperature
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(f"🚀 Loading model from {model_path}...")
        print(f"📱 Using device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)

        print("✅ Model loaded successfully!")

    def classify(self, text: str) -> dict:
        """
        Classify a single clause.

        Args:
            text: The clause text to classify

        Returns:
            dict with keys:
                - predicted_label: Integer label index
                - predicted_class: String label name
                - confidence: Confidence score (0-1)
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)

        with torch.no_grad():
            logits = self.model(**inputs).logits

        # Apply temperature scaling
        scaled_logits = logits / self.temperature
        probs = F.softmax(scaled_logits, dim=-1).cpu().numpy()[0]

        pred_idx = int(probs.argmax())
        confidence = float(probs[pred_idx])
        pred_class = self.label_map.get(pred_idx, "Unknown")

        return {
            "predicted_label": pred_idx,
            "predicted_class": pred_class,
            "confidence": confidence
        }

    def classify_batch(self, texts: list[str]) -> list[dict]:
        """
        Classify multiple clauses efficiently in batch mode.

        Args:
            texts: List of clause texts to classify

        Returns:
            List of prediction dictionaries (same format as classify())
        """
        if not texts:
            return []

        # Tokenize all texts at once
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            logits = self.model(**inputs).logits

        # Apply temperature scaling
        scaled_logits = logits / self.temperature
        probs = F.softmax(scaled_logits, dim=-1).cpu().numpy()

        results = []
        for i in range(len(texts)):
            pred_idx = int(probs[i].argmax())
            confidence = float(probs[i][pred_idx])
            pred_class = self.label_map.get(pred_idx, "Unknown")

            results.append({
                "predicted_label": pred_idx,
                "predicted_class": pred_class,
                "confidence": confidence
            })

        return results
