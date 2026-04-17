"""
Transformer-based fake news classifier using DeBERTa

This module provides a high-performance transformer model for fake news detection.
Falls back to TF-IDF if transformer model is not available.
"""

import os
import logging
from typing import Dict, Optional
import torch

logger = logging.getLogger(__name__)

class TransformerClassifier:
    """
    Transformer-based classifier for fake news detection
    
    Uses DeBERTa-v3-base fine-tuned on fake news datasets.
    Provides semantic understanding and adversarial robustness.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize transformer classifier
        
        Args:
            model_path: Path to model directory or HuggingFace model ID.
                       If None, uses default HF model or local path.
        """
        if model_path is None:
            # Arko007/fact-check1-v3-final — DeBERTa-v3-large, 99.98% accuracy,
            # calibrated on scientific facts + fake news, MIT license.
            # Override with DEBERTA_MODEL env var to use your own fine-tuned model.
            model_path = "Arko007/fact-check1-v3-final"
            # Fallback to local path if HF model not found
            self.fallback_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data", "deberta_factcheck"
            )
        else:
            self.fallback_path = None
        
        self.model_path = model_path
        self.classifier = None
        self._load_model()
    
    def _load_model(self):
        """Load transformer model from HuggingFace Hub or local disk"""
        try:
            from transformers import pipeline
            import os
            
            # Get HF token from environment
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                logger.info("Using HuggingFace token for model download")
            
            # Get model name from environment or use default
            model_name = os.getenv("DEBERTA_MODEL", self.model_path)
            logger.info(f"Loading model: {model_name}")
            
            # Try loading from HuggingFace Hub or local path
            try:
                device = 0 if torch.cuda.is_available() else -1
                self.classifier = pipeline(
                    "text-classification",
                    model=model_name,
                    token=hf_token,  # Use HF token for private/gated models
                    device=device,
                    truncation=True,
                    max_length=512
                )
                logger.info(f"✓ Transformer model loaded: {model_name}")
                logger.info(f"  Device: {'GPU (CUDA)' if device == 0 else 'CPU'}")
                return
                
            except Exception as e:
                logger.warning(f"Failed to load from {model_name}: {e}")
                
                # Try fallback local path if available
                if self.fallback_path and os.path.exists(self.fallback_path):
                    logger.info(f"Trying fallback path: {self.fallback_path}")
                    device = 0 if torch.cuda.is_available() else -1
                    self.classifier = pipeline(
                        "text-classification",
                        model=self.fallback_path,
                        device=device,
                        truncation=True,
                        max_length=512
                    )
                    logger.info(f"✓ Transformer model loaded from fallback path")
                    logger.info(f"  Device: {'GPU' if device == 0 else 'CPU'}")
                else:
                    logger.warning("No fallback path available or path doesn't exist")
            
        except ImportError:
            logger.warning("transformers library not installed. Install with: pip install transformers torch")
        except Exception as e:
            logger.error(f"Failed to load transformer model: {e}")
    
    def is_available(self) -> bool:
        """Check if transformer model is loaded and ready"""
        return self.classifier is not None
    
    def predict(self, text: str) -> Dict[str, any]:
        """
        Predict if text is fake news
        
        Args:
            text: Input text to classify
        
        Returns:
            {
                'fake_probability': float (0-1),
                'verdict': 'fake' or 'real',
                'confidence': float (0-1),
                'model': 'transformer'
            }
        
        Raises:
            RuntimeError: If model is not available
        """
        if not self.is_available():
            raise RuntimeError("Transformer model not available. Train model first or use TF-IDF fallback.")
        
        # Truncate very long texts
        if len(text) > 5000:
            text = text[:5000]
        
        # Run inference
        result = self.classifier(text)[0]
        
        # Parse result
        # LABEL_0 = real, LABEL_1 = fake (standard convention)
        is_fake = result['label'] == 'LABEL_1'
        confidence = result['score']
        
        return {
            'fake_probability': confidence if is_fake else 1 - confidence,
            'verdict': 'fake' if is_fake else 'real',
            'confidence': confidence,
            'model': 'transformer'
        }
    
    def predict_batch(self, texts: list) -> list:
        """
        Predict multiple texts at once (faster)
        
        Args:
            texts: List of texts to classify
        
        Returns:
            List of prediction dictionaries
        """
        if not self.is_available():
            raise RuntimeError("Transformer model not available")
        
        # Truncate texts
        texts = [t[:5000] if len(t) > 5000 else t for t in texts]
        
        # Batch inference
        results = self.classifier(texts)
        
        # Parse results
        predictions = []
        for result in results:
            is_fake = result['label'] == 'LABEL_1'
            confidence = result['score']
            predictions.append({
                'fake_probability': confidence if is_fake else 1 - confidence,
                'verdict': 'fake' if is_fake else 'real',
                'confidence': confidence,
                'model': 'transformer'
            })
        
        return predictions


# Singleton instance for reuse
_transformer_instance = None

def get_transformer() -> TransformerClassifier:
    """
    Get singleton transformer classifier instance
    
    Returns:
        TransformerClassifier instance
    """
    global _transformer_instance
    if _transformer_instance is None:
        _transformer_instance = TransformerClassifier()
    return _transformer_instance


def predict_with_transformer(text: str) -> Optional[Dict[str, any]]:
    """
    Convenience function to predict with transformer
    
    Args:
        text: Input text
    
    Returns:
        Prediction dict or None if model not available
    """
    try:
        transformer = get_transformer()
        if transformer.is_available():
            return transformer.predict(text)
        return None
    except Exception as e:
        logger.error(f"Transformer prediction failed: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Test the classifier
    transformer = get_transformer()
    
    if transformer.is_available():
        test_texts = [
            "COVID vaccines are safe and effective according to WHO",
            "Breaking: Scientists confirm earth is flat, NASA admits cover-up",
            "Stock market reaches new high amid economic recovery"
        ]
        
        print("Single predictions:")
        for text in test_texts:
            result = transformer.predict(text)
            print(f"{result['verdict'].upper()} ({result['confidence']:.2%}): {text[:60]}...")
        
        print("\nBatch prediction:")
        results = transformer.predict_batch(test_texts)
        for text, result in zip(test_texts, results):
            print(f"{result['verdict'].upper()} ({result['confidence']:.2%}): {text[:60]}...")
    else:
        print("Transformer model not available. Train model first!")
        print("See: backend/training/README_TRAINING.md")
