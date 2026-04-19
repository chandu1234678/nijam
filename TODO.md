# PiNE AI — Development Roadmap & TODO
> Last updated: April 2026 | Version 2.6.1
> ✅ = Done | 🔄 = Partial / In Progress | ⬜ = Not Started | 🔥 = High Priority

---

## Phase 1 — Transformer Model Development
*Goal: 95%+ accuracy, <100ms inference, zero external LLM dependency*

### 1.1 Training Infrastructure
- [x] ✅ GPU training notebooks (COLAB_TRAINING_SYSTEM_1/2/3.py)
- [x] ✅ Baseline TF-IDF model (`train.py`, `train_calibrated.py`)
- [x] ✅ Transformer fine-tuning (`train_transformer_clean.py`, `train_production.py`)
- [x] ✅ Ablation study (`ablation_study.py`)
- [x] ✅ Full pipeline evaluation (`train_meta.py`)
- [x] ✅ SHAP explainability (`shap_explainer.py`)
- [ ] ⬜ Structured Kaggle/Colab notebooks with markdown documentation

### 1.2 Dataset Collection & Preparation
- [x] ✅ Fake.csv + True.csv (ISOT ~44k)
- [x] ✅ fake_news_dataset_44k.csv
- [x] ✅ fake_news_dataset_20k.csv
- [x] ✅ Data cleaning (min length, dedup, language filter) in `train.py`
- [x] ✅ 80/10/10 train/val/test split
- [x] ✅ Auto data collection from web (Tavily + NewsAPI) — `news_aggregator.py`
- [ ] ⬜ 🔥 FEVER dataset (185k claims) — download and integrate
- [ ] ⬜ 🔥 LIAR-Plus dataset
- [ ] ⬜ MultiFC dataset
- [ ] ⬜ XFact multilingual dataset
- [ ] ⬜ FakeNewsNet (social context)
- [ ] ⬜ Constraint@AAAI (Hindi COVID misinformation)
- [ ] ⬜ IFND (Indian Fake News Dataset)
- [ ] ⬜ Unified dataset format with pub_date and source fields

### 1.3 Model Training & Deployment
- [x] ✅ DeBERTa-v3 fine-tuning (`train_production.py`)
- [x] ✅ FP16 precision, warmup ratio, weight decay
- [x] ✅ Early stopping on validation F1
- [x] ✅ Model uploaded to HuggingFace (Bharat2004/deberta-fakenews-detector)
- [x] ✅ Fine-tune ensemble pipeline (`train_finetune_ensemble.py`)
- [x] ✅ Backend inference pipeline (`ml.py`, `transformer.py`)
- [x] ✅ Benchmark: accuracy, latency, memory (`model_version.json`)
- [ ] ⬜ 🔥 ONNX export <350MB (`export_onnx_web.py` exists but not integrated)
- [ ] ⬜ Temporal embeddings (publication date in model input)
- [ ] ⬜ 3-class classification (real/fake/uncertain) — currently binary

### 1.4 Browser-side Inference
- [x] ✅ ONNX Runtime Web setup (`onnx_inference.js`)
- [x] ✅ Backend fallback support
- [ ] ⬜ 🔥 ONNX Web model <200MB (current model too large)
- [ ] ⬜ IndexedDB caching for browser inference
- [ ] ⬜ <200ms local inference target

---

## Phase 2 — Rapid Spread Detection (Cooldown System)
*Goal: Detect viral misinformation in real-time, introduce friction*

### 2.1 Velocity Tracking
- [x] ✅ In-memory velocity tracker (`velocity.py`)
- [x] ✅ 5-min / 1-hr / 24-hr sliding windows
- [x] ✅ Velocity score normalization
- [x] ✅ Viral/trending detection
- [x] ✅ VelocityRecord stored in database
- [ ] ⬜ Redis-backed velocity tracking (currently in-memory only)

### 2.2 Cooldown Score
- [x] ✅ Geometric mean formula (`cooldown.py`)
- [x] ✅ VIRAL_PANIC / HIGH_CONCERN / CAUTION / NORMAL thresholds
- [x] ✅ Cooldown score in API response

### 2.3 Friction UX
- [x] ✅ Full-screen interstitial for VIRAL_PANIC
- [x] ✅ 5-second delay card for HIGH_CONCERN
- [x] ✅ Caution banner
- [x] ✅ Bypass tracking
- [x] ✅ A/B testing framework (`ab_testing.py`, `ab_routes.py`)

### 2.4 Social Graph Analysis
- [x] ✅ Twitter/X API integration (`social_graph.py`, `news_aggregator.py`)
- [x] ✅ Reddit API integration
- [x] ✅ Bot score calculation
- [x] ✅ Temporal clustering detection
- [x] ✅ Campaign score (0–1)
- [ ] ⬜ Full retweet graph visualization in UI
- [ ] ⬜ Coordinated campaign alerts in extension

### 2.5 Semantic Clustering
- [x] ✅ Sentence embeddings (`semantic_clustering.py`)
- [x] ✅ HDBSCAN clustering
- [x] ✅ Cluster IDs in API response
- [x] ✅ Campaign score from cluster size
- [ ] ⬜ Cluster insights UI in extension (viral.html shows stats but not cluster details)

---

## Phase 3 — Training Data Enhancements
*Goal: 200k+ samples, multilingual, domain-specific*

### 3.1 Self-Labeling Pipeline
- [x] ✅ Snorkel weak supervision (`snorkel_labeling.py`)
- [x] ✅ Labeling functions (source credibility, manipulation, evidence)
- [x] ✅ Auto data collection from web every 24h (`continuous_learning.py`)
- [ ] ⬜ 🔥 Noise reduction with label model
- [ ] ⬜ Expand to 200k+ samples

### 3.2 Multilingual Support
- [x] ✅ Language detection (`multilingual.py`)
- [x] ✅ Translation to English for analysis
- [x] ✅ Multilingual training scripts (`train_multilingual.py`, `prepare_multilingual.py`)
- [ ] ⬜ 🔥 Hindi dataset integration
- [ ] ⬜ Telugu dataset integration
- [ ] ⬜ mBERT/XLM-R fine-tuning
- [ ] ⬜ Evaluate on Indian misinformation cases

### 3.3 Domain-Specific Training
- [x] ✅ Domain classifier (`domain_classifier.py`)
- [x] ✅ Domain-specific training scripts (`train_domain_specific.py`)
- [ ] ⬜ Medical misinformation dataset
- [ ] ⬜ Climate misinformation dataset
- [ ] ⬜ Political deepfake dataset
- [ ] ⬜ Multi-task learning

---

## Phase 4 — Production Hardening
*Goal: Explainable, continuously improving, reliable*

### 4.1 Explainability
- [x] ✅ SHAP explainer (`shap_explainer.py`)
- [x] ✅ Attention extractor (`attention_extractor.py`)
- [x] ✅ Token highlighting in UI (`highlight.py`)
- [x] ✅ SHAP-based highlights with fallback to heuristic
- [x] ✅ Explainability report in API response (`explainability.py`)
- [ ] ⬜ SHAP installed and working (currently `pip install shap` needed)
- [ ] ⬜ Attention weight visualization in extension UI

### 4.2 Active Learning Loop (Human-in-the-Loop)
- [x] ✅ Uncertainty sampling (0.45–0.55 confidence) in review queue
- [x] ✅ Human review interface (`review.html`, `review.js`)
- [x] ✅ Corrections stored in UserFeedback table
- [x] ✅ Auto-retrain on 50+ corrections (`continuous_learning.py`)
- [x] ✅ Immediate retrain for viral claims
- [x] ✅ Weekly retrain trigger (7-day interval)
- [x] ✅ Improvement metrics tracked in `model_version.json`
- [ ] ⬜ 🔥 Retrain working end-to-end on Windows (Unicode fix deployed, needs verification)

### 4.3 A/B Testing
- [x] ✅ A/B test framework (`ab_testing.py`)
- [x] ✅ Traffic splitting
- [x] ✅ Variant assignment and tracking
- [x] ✅ A/B routes (`ab_routes.py`)
- [ ] ⬜ Champion-challenger deployment automation

### 4.4 Deployment & Monitoring
- [x] ✅ Render deployment (`render.yaml`, `Procfile`)
- [x] ✅ Prometheus metrics (`monitoring.py`)
- [x] ✅ Grafana dashboard (`grafana_dashboard.json`)
- [x] ✅ Structured JSON logging
- [x] ✅ Health check endpoint (`/health`)
- [x] ✅ Drift detection (`drift.py`)
- [ ] ⬜ 🔥 Deploy v2.6.1 to Render (trigger manual deploy)
- [ ] ⬜ Canary deployments
- [ ] ⬜ HuggingFace Spaces deployment

---

## Phase 5 — Advanced Features
*Goal: Research-level innovation*

### 5.1 Temporal Claim Validity
- [x] ✅ ClaimRecord with timestamps in DB
- [x] ✅ Verdict change detection (`verdict_changed` in API)
- [ ] ⬜ 🔥 Publication date in model input (temporal embeddings)
- [ ] ⬜ Time-aware fact-checking (claims expire)

### 5.2 Information Operation Detection
- [x] ✅ Campaign score from social graph + clustering
- [x] ✅ Coordinated campaign flag in API
- [ ] ⬜ Suspicious activity pattern alerts in UI

### 5.3 Psychological Inoculation
- [x] ✅ Manipulation signal detection (`manipulation.py`)
- [x] ✅ Conspiracy language patterns
- [x] ✅ Urgency/emotional triggers detected
- [x] ✅ Manipulation badge in UI
- [ ] ⬜ Short explanatory warnings ("This uses fear language")
- [ ] ⬜ Inoculation effectiveness study

### 5.4 Passive Feed Scanner
- [x] ✅ Content script (`content.js`) — basic text selection
- [ ] ⬜ 🔥 Continuous page scanning
- [ ] ⬜ Color-coded highlights on page
- [ ] ⬜ <50ms latency target

### 5.5 Multimodal Analysis
- [x] ✅ Image analysis via Gemini Vision (`image_check.py`)
- [x] ✅ Image upload in extension
- [x] ✅ Image-text consistency check
- [x] ✅ Audio transcription (`audio_transcription.py`)
- [x] ✅ PDF/DOCX text extraction (`upload_routes.py`)
- [ ] ⬜ Deepfake detection
- [ ] ⬜ OCR for text in images
- [ ] ⬜ CLIP-based similarity scoring

### 5.6 Knowledge Graph Integration
- [x] ✅ Wikidata entity verification (`wikidata.py`)
- [x] ✅ Named entity extraction
- [x] ✅ Entity risk score in API
- [ ] ⬜ Internal knowledge graph (beyond Wikidata lookup)
- [ ] ⬜ Relationship verification

### 5.7 Adversarial Robustness
- [ ] ⬜ Adversarial example generation
- [ ] ⬜ Augmented training data
- [ ] ⬜ Malicious input detection

### 5.8 Cross-Lingual Transfer
- [x] ✅ Language detection + translation
- [ ] ⬜ Code-mixed language support (Hinglish, Tenglish)
- [ ] ⬜ Transliteration handling

### 5.9 Contextual Fact-Checking
- [x] ✅ Chat history in API (`history` field)
- [x] ✅ Session-based conversation
- [ ] ⬜ Reference resolution ("he said" → who?)
- [ ] ⬜ Context-aware verdicts

### 5.10 Real-Time Web Grounding
- [x] ✅ Tavily real-time search (`brave_search.py`)
- [x] ✅ NewsAPI fallback
- [x] ✅ Google Fact Check API (`platform_tracker.py`)
- [x] ✅ Cross-encoder reranking (`cross_encoder.py`)
- [x] ✅ Evidence provenance (source + trust + bias labels)
- [ ] ⬜ Evidence provenance chain visualization in UI

---

## Phase 6 — Research-Level Innovations

### 6.1 Causal Inference
- [ ] ⬜ Cause-effect modeling
- [ ] ⬜ Counterfactual scenarios
- [ ] ⬜ Spurious correlation detection

### 6.2 Uncertainty Quantification
- [x] ✅ Confidence calibration (isotonic regression in `train_calibrated.py`)
- [x] ✅ Brier score tracking
- [ ] ⬜ Bayesian uncertainty (Monte Carlo dropout)
- [ ] ⬜ Uncertainty intervals in UI

### 6.3 Federated Learning
- [ ] ⬜ Privacy-preserving training
- [ ] ⬜ Decentralized updates
- [ ] ⬜ Differential privacy

### 6.4 Continual Learning
- [x] ✅ Incremental retraining from feedback
- [x] ✅ Concept drift detection (`drift.py`)
- [ ] ⬜ Catastrophic forgetting prevention (EWC/replay)

### 6.5 Meta-Learning
- [ ] ⬜ Few-shot learning for new topics
- [ ] ⬜ Rapid domain adaptation

### 6.6 Interpretable AI
- [x] ✅ SHAP values
- [x] ✅ Attention weights
- [ ] ⬜ Concept activation vectors (TCAV)
- [ ] ⬜ Influence functions
- [ ] ⬜ Counterfactual explanations

### 6.7 Fairness & Bias Mitigation
- [x] ✅ Publisher bias database (`publisher_bias.py`)
- [x] ✅ Bias-weighted evidence scoring
- [ ] ⬜ Formal bias audit
- [ ] ⬜ Fairness constraints in training
- [ ] ⬜ Fairness benchmark evaluation

### 6.8 Human-AI Collaboration
- [x] ✅ Interactive corrections (feedback button in UI)
- [x] ✅ Review queue with Real/Fake/Skip
- [x] ✅ User feedback aggregation
- [ ] ⬜ Teach mode (explain why verdict changed)

---

## Phase 7 — Infrastructure & Scaling

### 7.1 Performance Optimization
- [x] ✅ TF-IDF fast path (instant, <10ms)
- [x] ✅ Parallel LLM calls (ThreadPoolExecutor)
- [x] ✅ RAM check before loading transformer
- [ ] ⬜ 🔥 INT8/FP16 quantization for ONNX
- [ ] ⬜ Model pruning
- [ ] ⬜ Knowledge distillation (DeBERTa → DistilBERT)
- [ ] ⬜ Request batching

### 7.2 Caching & CDN
- [x] ✅ Redis cache layer (`cache.py`) — disabled on free tier
- [x] ✅ In-memory partial cache (ML score, AI score, evidence)
- [x] ✅ 1-hour TTL for AI/evidence, 24-hour for ML
- [ ] ⬜ Semantic caching (cache by embedding similarity)
- [ ] ⬜ CDN for model weights

### 7.3 Database Optimization
- [x] ✅ Composite indexes on ClaimRecord, VelocityRecord
- [x] ✅ Connection pooling (pool_size=5, max_overflow=10)
- [x] ✅ PostgreSQL on Render
- [ ] ⬜ Read replicas
- [ ] ⬜ Database sharding
- [ ] ⬜ Time-series DB for analytics

### 7.4 Security & Rate Limiting
- [x] ✅ Per-IP rate limiting (`middleware.py`)
- [x] ✅ Per-route limits (login, signup, message)
- [x] ✅ JWT authentication
- [x] ✅ Security headers (CSP, HSTS, X-Frame-Options)
- [x] ✅ Request body size guard (2MB)
- [x] ✅ Redis-based quota system (`rate_limit.py`)
- [ ] ⬜ API key authentication for public API
- [ ] ⬜ CAPTCHA for abuse prevention
- [ ] ⬜ DDoS protection (Cloudflare)
- [ ] ⬜ Security audit

### 7.5 Observability
- [x] ✅ Structured JSON logging
- [x] ✅ Prometheus metrics (`monitoring.py`)
- [x] ✅ Grafana dashboard
- [x] ✅ Health check with drift stats
- [ ] ⬜ Distributed tracing (OpenTelemetry)
- [ ] ⬜ Alerting system (PagerDuty/Slack)

### 7.6 Testing & CI/CD
- [x] ✅ Backend test suite (`run_tests.py`, `check_verdicts.py`)
- [x] ✅ 14/14 API tests passing
- [x] ✅ Verdict accuracy tests
- [ ] ⬜ 🔥 Unit tests (80%+ coverage target)
- [ ] ⬜ Integration tests
- [ ] ⬜ Load testing
- [ ] ⬜ GitHub Actions CI/CD pipeline (`.github/workflows/` exists but needs test step)
- [ ] ⬜ Automated model evaluation on deploy

---

## Phase 8 — Platform Expansion

### 8.1 Mobile Applications
- [ ] ⬜ Cross-platform mobile app (React Native / Flutter)
- [ ] ⬜ Share extension for quick fact-checking
- [ ] ⬜ Offline inference
- [ ] ⬜ Push notifications

### 8.2 Social Media Integrations
- [ ] ⬜ Twitter/X bot
- [ ] ⬜ WhatsApp bot
- [ ] ⬜ Telegram bot
- [ ] ⬜ Discord bot

### 8.3 API & Developer Platform
- [x] ✅ REST API (FastAPI with OpenAPI docs at /docs)
- [ ] ⬜ Public API with API key auth
- [ ] ⬜ GraphQL endpoint
- [ ] ⬜ Python SDK
- [ ] ⬜ JavaScript SDK
- [ ] ⬜ Developer portal

### 8.4 Partnerships
- [ ] ⬜ News organization integrations
- [ ] ⬜ Fact-checking agency partnerships
- [ ] ⬜ Structured data markup (schema.org/ClaimReview)
- [ ] ⬜ Social platform partnerships

---

## Phase 9 — Academic & Research

### 9.1 Research Publications
- [ ] ⬜ Cooldown score methodology paper
- [ ] ⬜ Temporal claim validity study
- [ ] ⬜ ACL/EMNLP submission

### 9.2 Open Source
- [x] ✅ Code on GitHub (chandu1234678/nijam)
- [ ] ⬜ Training notebooks published
- [ ] ⬜ Datasets published
- [ ] ⬜ Reproducibility package

### 9.3 Benchmarks
- [ ] ⬜ Public evaluation benchmark
- [ ] ⬜ Leaderboard

### 9.4 Educational Content
- [ ] ⬜ Technical blog posts
- [ ] ⬜ Video tutorials

---

## 🔥 Immediate Priority Queue (Next Actions)

| Priority | Task | Effort |
|----------|------|--------|
| 🔥🔥🔥 | Deploy v2.6.1 to Render (trigger manual deploy) | 5 min |
| 🔥🔥🔥 | Verify retrain works end-to-end after Unicode fix | 10 min |
| 🔥🔥 | Download FEVER + LIAR datasets, integrate into training | 2 hrs |
| 🔥🔥 | ONNX export <350MB for browser inference | 3 hrs |
| 🔥🔥 | GitHub Actions CI/CD with test step | 1 hr |
| 🔥🔥 | Passive feed scanner (content.js highlight on page) | 4 hrs |
| 🔥 | Hindi/Telugu dataset integration | 2 hrs |
| 🔥 | SHAP pip install + verify working | 30 min |
| 🔥 | Unit test coverage to 80% | 4 hrs |
| 🔥 | Temporal embeddings (pub_date in model) | 3 hrs |

---

## Current Stats (v2.6.1)
- **API Tests**: 14/14 passing ✅
- **Verdict Accuracy**: 4/4 correct (flat earth fake, vaccine real, conspiracy fake, WHO real) ✅
- **Auto Data Collection**: 104 samples/run across 6 topics ✅
- **Auto Retrain**: Triggers at 50+ corrections ✅
- **Human Review Queue**: 249 claims pending ✅
- **TF-IDF Accuracy**: ~96.6% ✅
- **LLM Ensemble**: MiniMax M2.7 + Gemma 4 31B + Gemini + Groq + Cerebras ✅
- **Render Deployment**: v2.0.0 live (needs v2.6.1 deploy) 🔄
