# AI Architecture - Archaeological Classifier System

This document describes how artificial intelligence (Claude) is used in the archaeological classification system.

## Overview

The system uses **Claude 4.5 Sonnet** (Anthropic) for analysis and interpretation of archaeological artifacts, particularly Bronze Age axes of the Savignano type.

### Key Features

- **Connection Resilience**: Automatic retry with exponential backoff for API calls
- **RAG Semantic Search**: Natural language queries across cached AI analyses
- **Session Resumption**: Long-running analyses can resume from interruption
- **Caching System**: All AI interpretations are cached to avoid redundant API calls

---

## Connection Resilience

### Overview

The system implements robust connection handling to prevent losing work during AI analyses. If the connection drops, analyses automatically retry and can resume from intermediate results.

### Implementation (`resilient_ai.py`)

```python
class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,      # Initial delay in seconds
        max_delay: float = 60.0,       # Maximum delay between retries
        exponential_base: float = 2.0, # Base for exponential backoff
        jitter: bool = True            # Add random jitter to delays
    ):
        ...
```

### Retry Logic

The system uses **exponential backoff with jitter**:

| Attempt | Base Delay | With Jitter (approx) |
|---------|------------|---------------------|
| 1 | 2s | 1-3s |
| 2 | 4s | 2-6s |
| 3 | 8s | 4-12s |
| 4 | 16s | 8-24s |
| 5 | 32s | 16-48s |

### Retryable Errors

The following exceptions trigger automatic retry:

- `APIConnectionError` - Network connectivity issues
- `APITimeoutError` - Request timeout
- `RateLimitError` - API rate limit (429)
- `ConnectionError` - General connection failures
- `TimeoutError` - Timeout errors
- `OSError` - Network-related OS errors

Non-retryable (4xx client errors except 429) fail immediately.

### ResilientAnthropicClient

Wrapper around the Anthropic client with built-in resilience:

```python
from acs.core.resilient_ai import ResilientAnthropicClient, RetryConfig

# Create client with custom retry config
client = ResilientAnthropicClient(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    retry_config=RetryConfig(max_retries=5, base_delay=2.0)
)

# Progress callback for UI updates
client.set_progress_callback(lambda msg, cur, total: print(f"{msg} ({cur}/{total})"))

# Create message with automatic retry
response = client.create_message(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2000,
    messages=[{"role": "user", "content": "Analyze this artifact..."}],
    temperature=0.3
)
```

### Analysis Session Resumption

For long-running multi-step analyses:

```python
from acs.core.resilient_ai import AnalysisSession

session = AnalysisSession(
    session_id="analysis_20251208",
    client=resilient_client,
    db=database
)

# Steps are cached - if session resumes, completed steps are skipped
result1 = session.run_step("extract_features", lambda: extract_features(artifact), progress_value=25)
result2 = session.run_step("cluster_analysis", lambda: run_clustering(result1), progress_value=50)
result3 = session.run_step("ai_interpretation", lambda: interpret(result2), progress_value=75)

session.complete()
```

### Frontend Reconnection UI

The web interface shows a reconnection banner when connection is lost:

```javascript
const RETRY_CONFIG = {
    maxRetries: 5,
    baseDelay: 2000,      // 2 seconds
    maxDelay: 60000,      // 60 seconds
    exponentialBase: 2
};

// Banner shows countdown and allows cancellation
showReconnectionBanner(attempt, maxAttempts, delaySeconds);
```

---

## Where AI is Used

### 1. Artifact Classification (`ai_assistant.py`)

**Purpose:** Analyze morphometric features and suggest typological classifications.

**Configuration:**
```python
model = "claude-sonnet-4-5-20250929"
temperature = 0.3  # Low for more deterministic responses
max_tokens = 2000
```

**Input provided to AI:**
- Artifact ID
- Extracted morphometric features (length, width, ratios, etc.)
- Savignano-specific features (heel type, margins, section, etc.)
- Existing typological classes for comparison
- Optional archaeological context

**Output:**
- Classification suggestion
- Typological comparisons
- Methodological notes

### 2. Savignano Interpretation (`routes.py`)

**Endpoint:** `/web/savignano-ai-interpretation/<artifact_id>`

**Configuration:**
```python
temperature = 0.1  # Very low for maximum consistency
max_tokens = 600
```

**Input:**
- Complete morphometric features of the axe
- Dimensional data
- Typological characteristics

**Output saved to cache:** `savignano_interpretation`

### 3. Technological Analysis (`routes.py`)

**Endpoint:** `/artifact/<id>/tech-analysis`

**Purpose:** Analysis of production techniques (hammering, casting).

**Output saved to cache:** `tech_analysis`

### 4. Archaeological Q&A (`archaeological_qa.py`)

**Purpose:** Answer specific questions about artifacts.

**Configuration:**
```python
model = "claude-sonnet-4-5-20250929"
max_tokens = variable (600-2000)
```

### 5. RAG Semantic Search (`rag_search.py`)

**Purpose:** Natural language search across all cached AI analyses.

**How it works:**
1. User query is analyzed for intent and entities
2. Relevant cached analyses are retrieved
3. AI synthesizes a comprehensive answer from the context

**Example queries:**
- "Which axes show intense hammering marks?"
- "Compare SAV_001 with SAV_015"
- "What are the largest axes in the hoard?"

---

## How AI Makes Decisions

### Classification Criteria

The AI uses a structured prompt that includes:

1. **Defined role:** "Expert archaeologist specialized in Bronze Age axes"
2. **Objective data:** Only features extracted algorithmically from the 3D mesh
3. **Typological framework:** Reference to known typologies (Savignano I-IV, regional variants)
4. **Response constraints:** Structured format to avoid digressions

### Example Prompt

```
You are an expert archaeological AI assistant specializing in
Bronze Age artifact classification, particularly bronze axes.

Analyze the following artifact and provide classification insights:

**Artifact ID:** SAV_001

**Morphometric Features:**
- Length: 152.3 mm
- Width: 45.2 mm
- Thickness: 28.1 mm
...

Based on these features, provide:
1. Typological classification
2. Production technique analysis
3. Comparative notes
```

---

## Data Extraction Pipeline

```
3D Mesh (.obj)
    │
    ▼
┌─────────────────────────┐
│ Morphometric Extractor  │  ← Geometric algorithms
│ (morphometric.py)       │
└─────────────────────────┘
    │
    ▼
Numeric features
(length, area, volume, ratios)
    │
    ▼
┌─────────────────────────┐
│ Savignano Extractor     │  ← Type-specific analysis
│ (morphometric_extractor.py)
└─────────────────────────┘
    │
    ▼
Savignano Features
(heel_type, margins, section)
    │
    ▼
┌─────────────────────────┐
│ AI Analysis             │  ← Claude interprets
│ (ai_assistant.py)       │
└─────────────────────────┘
    │
    ▼
Textual interpretation
```

### Data Never Invented by AI

The AI **DOES NOT invent** numerical data. All quantitative data comes from:

1. **Geometric extraction** from 3D mesh (trimesh)
2. **Mathematical calculations** (PCA, clustering, distances)
3. **Database** (previously extracted features)

The AI only:
- **Interprets** existing data
- **Classifies** based on known typologies
- **Compares** with other artifacts
- **Describes** in natural language

---

## Temperature Configuration

| Endpoint | Temperature | Reason |
|----------|-------------|--------|
| Classification | 0.3 | Balance creativity/consistency |
| Savignano Interpretation | 0.1 | Maximum consistency/repeatability |
| Technological Analysis | 0.2 | Low creativity, technical focus |
| General Q&A | 0.3 | Allows more elaborate responses |
| RAG Search | 0.1 | Factual, data-based responses |

**Note:** Low temperatures (0.1-0.3) significantly reduce the risk of "hallucination" by keeping responses anchored to the provided data.

---

## Caching System

To avoid expensive regeneration and ensure consistency:

```
┌─────────────────────────────────────┐
│           ai_cache table            │
├─────────────────────────────────────┤
│ artifact_id | cache_type | content  │
│ SAV_001     | savignano_interpretation | {...} │
│ SAV_001     | hammering_analysis | {...} │
│ SAV_002     | tech_analysis | {...} │
└─────────────────────────────────────┘
```

**Cache types:**
- `savignano_interpretation` - Typological interpretation
- `tech_analysis` - Technological analysis
- `hammering_analysis` - Hammering analysis
- `casting_analysis` - Casting analysis
- `comprehensive_report` - Complete report
- `comparison` - Artifact comparisons
- `analysis_session` - Session state for resumption

**Benefits:**
1. ✅ Token savings (API cost)
2. ✅ Immediate responses for already-analyzed data
3. ✅ Consistency in repeated responses
4. ✅ Ability to aggregate/search interpretations
5. ✅ Session resumption after connection loss

---

## PCA and Cluster Visualization

### PCA (Principal Component Analysis)

The system provides rich PCA visualizations:

- **Scatter Plot**: PC1 vs PC2 with color-coded clusters
- **Density Contours**: Show distribution patterns
- **Marginal Histograms**: Distribution along each axis
- **Feature Loadings**: Which features contribute to each PC
- **Scree Plot**: Variance explained by each component

### Cluster Distribution

For clustering results, the system displays:

- **Cluster Assignment Chart**: Bar chart showing axes per cluster
- **Distribution Statistics**: Mean, std dev for each cluster
- **Silhouette Score**: Quality metric (0-1, higher = better)

---

## Risks and Mitigations

### Hallucination (Data Invention)

**Risk:** AI might invent data not present in features.

**Mitigations:**
1. Low temperature (0.1-0.3)
2. Structured prompts with explicit data
3. Request to cite only provided data
4. Post-hoc validation of numeric references

### Typological Bias

**Risk:** AI might favor known classifications.

**Mitigations:**
1. Inclusion of "uncertain" or "atypical" categories
2. Explicit request to highlight anomalies
3. Comparison with existing database

### Inconsistency

**Risk:** Different responses for the same artifact.

**Mitigations:**
1. Cache system for reuse
2. Low temperature
3. Deterministic prompts

### Connection Loss

**Risk:** Long analyses fail mid-way, losing progress.

**Mitigations:**
1. Automatic retry with exponential backoff
2. Intermediate result caching
3. Session resumption support
4. User-visible reconnection status

---

## Architectural Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB INTERFACE                            │
│  (Templates: viewer3d.html, morphometric.html, etc.)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ROUTES (routes.py)                       │
│  Endpoints: /artifact/*, /savignano-*, /run-pca, etc.      │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│  MORPHOMETRIC     │ │  AI ASSISTANT     │ │  DATABASE         │
│  ANALYZER         │ │  (Claude API)     │ │  (SQLite)         │
│                   │ │                   │ │                   │
│ - PCA             │ │ - Classify        │ │ - artifacts       │
│ - Clustering      │ │ - Interpret       │ │ - features        │
│ - Similarity      │ │ - Analyze Tech    │ │ - ai_cache        │
└───────────────────┘ └───────────────────┘ └───────────────────┘
            │                 │                       │
            │         ┌───────┴───────┐               │
            │         ▼               │               │
            │ ┌───────────────────┐   │               │
            │ │ RESILIENT CLIENT  │   │               │
            │ │ (resilient_ai.py) │   │               │
            │ │                   │   │               │
            │ │ - Retry logic     │   │               │
            │ │ - Session mgmt    │   │               │
            │ │ - Progress track  │   │               │
            │ └───────────────────┘   │               │
            │                         │               │
            └─────────────────┬───────┘───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    MESH PROCESSING                          │
│  Savignano Extractor → Features → Storage                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE (Dropbox)                        │
│  Mesh files (.obj), Backups, Reports                       │
└─────────────────────────────────────────────────────────────┘
```

---

## API Reference

### ResilientAnthropicClient

```python
from acs.core.resilient_ai import ResilientAnthropicClient, RetryConfig, get_resilient_client

# Get global singleton
client = get_resilient_client()

# Or create custom instance
client = ResilientAnthropicClient(
    api_key="your-api-key",
    retry_config=RetryConfig(max_retries=5)
)

# Set progress callback
client.set_progress_callback(
    lambda msg, cur, total: update_ui(msg, cur, total)
)

# Create message with automatic retry
response = client.create_message(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2000,
    messages=[{"role": "user", "content": "..."}],
    temperature=0.3,
    system="You are an archaeological expert..."
)
```

### AIClassificationAssistant

```python
from acs.core.ai_assistant import AIClassificationAssistant

ai = AIClassificationAssistant()

# Single analysis
result = ai.analyze_artifact(
    artifact_id="SAV_001",
    features=features_dict,
    existing_classes=taxonomy_classes,
    context="Found in zone X"
)

# Streaming analysis
for chunk in ai.analyze_artifact_stream(artifact_id, features):
    print(chunk, end='')
```

### Database Cache

```python
from acs.core.database import get_database

db = get_database()

# Save interpretation
db.save_ai_cache(
    artifact_id="SAV_001",
    cache_type="savignano_interpretation",
    content=interpretation_text,
    model="claude-sonnet-4-5-20250929"
)

# Retrieve cached interpretation
cached = db.get_ai_cache("SAV_001", "savignano_interpretation")
if cached:
    print(cached['content'])
```

### RAG Search

```python
from acs.core.rag_search import RAGSearchEngine

rag = RAGSearchEngine(db)

# Search with AI-generated response
results = rag.search(
    query="Which axes show intense hammering?",
    generate_ai_response=True,
    max_results=10
)

print(results['ai_response']['summary'])
print(results['ai_response']['analysis'])
```

---

## User Persistence

### Overview

User accounts are persisted in SQLite and backed up to cloud storage. The system now properly preserves user accounts during database restore operations.

### Backup/Restore Logic

The database restore function checks both artifacts AND users:

```python
# Check BOTH artifacts AND users to prevent overwriting newly created users
local_user_count = cursor.execute(
    "SELECT COUNT(*) FROM users WHERE username != 'admin'"
).fetchone()[0]

if local_user_count > 0:
    # Skip restore to preserve user accounts
    return {'status': 'skipped', 'reason': 'local_db_has_users'}
```

This prevents losing user accounts created after a deployment when cloud backup only contains older data.

---

## Conclusions

The AI in the ACS system is configured to:

1. **Be transparent:** All input data is visible and verifiable
2. **Be consistent:** Low temperatures and caching reduce variability
3. **Not invent:** AI only interprets algorithmically provided data
4. **Be traceable:** Every interpretation is saved with metadata
5. **Be resilient:** Connection issues don't lose work progress

For questions or issues: open an issue on GitHub.

---

*Document updated: December 2025*
*Version: 3.0 - Connection Resilience & Enhanced Visualization*
