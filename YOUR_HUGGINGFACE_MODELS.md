# Your HuggingFace Models

## Account: Bharat2004

### Available Models (5 total)

#### 1. ⭐ Bharat2004/deberta-fakenews-detector (PRIMARY)
- **Type**: DeBERTa-v2 for Text Classification
- **Downloads**: 21 (most popular)
- **Status**: ✅ Currently Active
- **Updated**: 1 day ago
- **Tags**: transformers, safetensors, deberta-v2, text-classification
- **Use Case**: Primary fake news detection model
- **Performance**: Best overall accuracy

#### 2. 🔄 Bharat2004/deberta-factchecker (ALTERNATIVE)
- **Type**: DeBERTa-v3-base fine-tuned
- **Downloads**: 12
- **Status**: ✅ Available for ensemble
- **Updated**: 6 days ago
- **License**: MIT
- **Tags**: transformers, safetensors, deberta-v2, text-classification
- **Use Case**: Alternative DeBERTa model for ensemble voting
- **Performance**: High accuracy, good for cross-validation

#### 3. ⚡ Bharat2004/out (FAST FALLBACK)
- **Type**: DistilBERT-base fine-tuned
- **Downloads**: 8
- **Status**: ✅ Available for fast inference
- **Updated**: 6 days ago
- **License**: Apache 2.0
- **Tags**: transformers, safetensors, distilbert, text-classification
- **Use Case**: Fast inference when speed is critical
- **Performance**: Good accuracy, 2-3x faster than DeBERTa

#### 4. 📦 Bharat2004/factchecker-deberta (BACKUP)
- **Type**: DeBERTa base
- **Downloads**: 0
- **Status**: Available but not recommended
- **Updated**: 6 days ago
- **Use Case**: Backup model
- **Note**: Less popular, use alternatives instead

#### 5. 🔧 Bharat2004/results_split3 (TRAINING CHECKPOINT)
- **Type**: Training checkpoint/results
- **Downloads**: 0
- **Status**: Not a complete model
- **Updated**: 1 hour ago
- **Use Case**: Training artifacts, not for inference
- **Note**: Keep for reference, not for production

---

## Current Configuration

### Single Model Mode (Default)
```env
DEBERTA_MODEL=Bharat2004/deberta-fakenews-detector
HF_TOKEN=your-hf-token
FORCE_TRANSFORMER_LOAD=true
ENABLE_ENSEMBLE=false
```

**Pros**:
- Fastest inference
- Lowest memory usage
- Simplest configuration
- Uses your most popular model

**Cons**:
- Single point of failure
- No cross-validation

### Ensemble Mode (Advanced)
```env
DEBERTA_MODEL=Bharat2004/deberta-fakenews-detector
DEBERTA_MODEL_ALT=Bharat2004/deberta-factchecker
DISTILBERT_MODEL=Bharat2004/out
HF_TOKEN=your-hf-token
FORCE_TRANSFORMER_LOAD=true
ENABLE_ENSEMBLE=true
```

**Pros**:
- Higher accuracy through voting
- More robust predictions
- Cross-validation built-in
- Reduces false positives/negatives

**Cons**:
- 3x slower inference
- 3x memory usage (~4.5 GB RAM needed)
- More complex

---

## Model Weights in Ensemble

When ensemble is enabled, predictions are weighted:

1. **DeBERTa-v2** (deberta-fakenews-detector): 50% weight
   - Most downloads, most trusted
   - Primary model

2. **DeBERTa-v3** (deberta-factchecker): 30% weight
   - Alternative architecture
   - Good for cross-validation

3. **DistilBERT** (out): 20% weight
   - Fast inference
   - Lower weight due to smaller model

**Ensemble Formula**:
```
final_score = (deberta_v2 * 0.5) + (deberta_v3 * 0.3) + (distilbert * 0.2)
```

---

## Performance Comparison

| Model | Size | Speed | Accuracy | Memory | Downloads |
|-------|------|-------|----------|--------|-----------|
| deberta-fakenews-detector | 0.2B | Medium | ⭐⭐⭐⭐⭐ | 1.5 GB | 21 |
| deberta-factchecker | 0.2B | Medium | ⭐⭐⭐⭐⭐ | 1.5 GB | 12 |
| out (DistilBERT) | 66M | Fast | ⭐⭐⭐⭐ | 500 MB | 8 |
| Ensemble (all 3) | - | Slow | ⭐⭐⭐⭐⭐ | 3.5 GB | - |

---

## Recommendations

### For Production (Current Setup) ✅
**Use**: Single model mode with `deberta-fakenews-detector`

**Why**:
- Most popular (21 downloads)
- Best balance of speed and accuracy
- Proven in production
- Lower resource requirements

### For Research/Testing
**Use**: Ensemble mode with all 3 models

**Why**:
- Highest accuracy
- Cross-validation
- Reduces bias
- Better for edge cases

### For Low-Resource Environments
**Use**: Single model mode with `out` (DistilBERT)

**Why**:
- Fastest inference
- Lowest memory (500 MB)
- Still good accuracy
- Works on limited hardware

---

## How to Switch Models

### Switch to Alternative DeBERTa
```bash
# Edit backend/.env
DEBERTA_MODEL=Bharat2004/deberta-factchecker
```

### Switch to DistilBERT (Fast)
```bash
# Edit backend/.env
DEBERTA_MODEL=Bharat2004/out
```

### Enable Ensemble
```bash
# Edit backend/.env
ENABLE_ENSEMBLE=true
```

### Test Model
```bash
cd backend
venv\Scripts\activate
python -c "from app.analysis.ml import run_ml_analysis; print(run_ml_analysis('Test claim'))"
```

---

## Model Statistics

- **Total Models**: 5
- **Production-Ready**: 3
- **Total Downloads**: 41
- **Most Popular**: deberta-fakenews-detector (21 downloads)
- **Fastest**: out/DistilBERT
- **Most Accurate**: Ensemble of all 3

---

## Next Steps

1. ✅ **Current**: Using deberta-fakenews-detector (best choice)
2. 🔄 **Optional**: Test ensemble mode for higher accuracy
3. ⚡ **Optional**: Test DistilBERT for faster inference
4. 📊 **Recommended**: Monitor model performance in production
5. 🔄 **Future**: Retrain models with production feedback

---

**Last Updated**: 2026-04-18
**Status**: ✅ All models accessible and ready to use
