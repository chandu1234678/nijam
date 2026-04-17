# 🚀 Parallel Training on 3 Free Colab T4 GPUs

Train your DeBERTa model 3x faster by splitting the dataset across 3 computers!

## 📋 What You Have

- **3 Training Scripts**: One for each computer
- **HuggingFace Token**: `your-hf-token`
- **Dataset**: `Bharat2004/factchecker-deberta` (on HuggingFace)

## 🎯 Strategy

Each system trains on 1/3 of your data in parallel:
- **System 1**: Samples 0 to 33%
- **System 2**: Samples 33% to 66%
- **System 3**: Samples 66% to 100%

## 📝 Instructions

### System 1 (Computer 1)

1. Open Google Colab: https://colab.research.google.com/
2. Change runtime to **GPU (T4)**:
   - Runtime → Change runtime type → T4 GPU → Save
3. Create a new code cell
4. Copy **ALL** code from `COLAB_TRAINING_SYSTEM_1.py`
5. Paste into the cell
6. Run the cell (Ctrl+Enter)
7. Wait ~30-45 minutes

### System 2 (Computer 2)

1. Open Google Colab: https://colab.research.google.com/
2. Change runtime to **GPU (T4)**
3. Create a new code cell
4. Copy **ALL** code from `COLAB_TRAINING_SYSTEM_2.py`
5. Paste into the cell
6. Run the cell (Ctrl+Enter)
7. Wait ~30-45 minutes

### System 3 (Computer 3)

1. Open Google Colab: https://colab.research.google.com/
2. Change runtime to **GPU (T4)**
3. Create a new code cell
4. Copy **ALL** code from `COLAB_TRAINING_SYSTEM_3.py`
5. Paste into the cell
6. Run the cell (Ctrl+Enter)
7. Wait ~30-45 minutes

## ⏱️ Timeline

```
Time    System 1              System 2              System 3
────────────────────────────────────────────────────────────────
0:00    Start training        Start training        Start training
0:30    Training...           Training...           Training...
0:45    ✅ Upload to HF       ✅ Upload to HF       ✅ Upload to HF
```

**Total Time**: ~45 minutes (vs 2+ hours sequential!)

## 📦 Output Models

After completion, you'll have 3 models on HuggingFace:

1. `Bharat2004/factchecker-deberta-split1`
2. `Bharat2004/factchecker-deberta-split2`
3. `Bharat2004/factchecker-deberta-split3`

## 🎯 Using the Models

### Option 1: Use Best Single Model

Check which split has the highest accuracy and use that one:

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Use the best performing split (check accuracy in model cards)
model_name = "Bharat2004/factchecker-deberta-split1"  # or split2, split3

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

text = "Your claim to fact-check"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
outputs = model(**inputs)
prediction = outputs.logits.argmax(-1).item()
# 0 = Real, 1 = Fake
```

### Option 2: Ensemble All 3 Models (Best Accuracy!)

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load all 3 models
models = []
for i in range(1, 4):
    model = AutoModelForSequenceClassification.from_pretrained(
        f"Bharat2004/factchecker-deberta-split{i}"
    )
    models.append(model)

tokenizer = AutoTokenizer.from_pretrained("Bharat2004/factchecker-deberta-split1")

# Predict with ensemble
text = "Your claim to fact-check"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

# Get predictions from all models
predictions = []
for model in models:
    with torch.no_grad():
        outputs = model(**inputs)
        predictions.append(outputs.logits)

# Average predictions
ensemble_logits = torch.stack(predictions).mean(dim=0)
final_prediction = ensemble_logits.argmax(-1).item()
# 0 = Real, 1 = Fake
```

## 🔧 Troubleshooting

### "No GPU available"
- Go to Runtime → Change runtime type → Select T4 GPU → Save
- Restart runtime and try again

### "Out of memory"
- The batch size is already optimized for T4 (8)
- If still failing, reduce to batch_size=4 in the code

### "Dataset not found"
- Make sure your dataset is public on HuggingFace
- Check the dataset name: `Bharat2004/factchecker-deberta`

### "Token authentication failed"
- Verify your HF token: `your-hf-token`
- Make sure it has write permissions

## 📊 Expected Results

Each split should achieve:
- **Accuracy**: ~90-95%
- **F1 Score**: ~0.90-0.95
- **Training Time**: 30-45 minutes on T4

Ensemble of all 3 splits typically gives +2-3% accuracy boost!

## 🎉 After Training

1. Check all 3 models on HuggingFace
2. Compare their accuracy scores
3. Either use the best one or ensemble all 3
4. Update your backend to use the new model

## 💡 Tips

- Run all 3 systems simultaneously for fastest results
- Use different Google accounts if you hit Colab limits
- Monitor GPU usage in Colab (top right corner)
- Save model links for later use

## 🔗 Useful Links

- Your HuggingFace Profile: https://huggingface.co/Bharat2004
- Colab: https://colab.research.google.com/
- Transformers Docs: https://huggingface.co/docs/transformers

---

**Good luck with training! 🚀**
