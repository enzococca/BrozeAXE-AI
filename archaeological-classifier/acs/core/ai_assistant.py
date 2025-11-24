"""
AI Classification Assistant
============================

Uses Claude 4.5 Sonnet to assist with archaeological artifact classification.
"""

import anthropic
import os
import json
from typing import Dict, List, Optional, Any


class AIClassificationAssistant:
    """
    AI assistant for archaeological classification using Claude 4.5.
    """

    def __init__(self, api_key: str = None):
        """Initialize AI assistant."""
        # Try config first, then environment variable, then parameter
        if api_key is None:
            from acs.core.config import get_config
            config = get_config()
            api_key = config.get_api_key() or os.getenv('ANTHROPIC_API_KEY')

        self.api_key = api_key
        if not self.api_key:
            raise ValueError("API key not configured. Set it in the web interface or via ANTHROPIC_API_KEY environment variable.")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    def analyze_artifact(self, artifact_id: str, features: Dict[str, Any],
                        existing_classes: List[Dict] = None,
                        context: str = None) -> Dict:
        """
        Analyze an artifact and suggest classification.

        Args:
            artifact_id: Artifact identifier
            features: Morphometric features dictionary
            existing_classes: List of existing taxonomic classes
            context: Additional archaeological context

        Returns:
            AI analysis with classification suggestions
        """
        # Build prompt
        prompt = self._build_classification_prompt(
            artifact_id, features, existing_classes, context
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more focused responses
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            analysis_text = response.content[0].text

            return {
                'artifact_id': artifact_id,
                'analysis': analysis_text,
                'model': self.model,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }

        except Exception as e:
            return {
                'artifact_id': artifact_id,
                'error': str(e),
                'analysis': None
            }

    def analyze_artifact_stream(self, artifact_id: str, features: Dict[str, Any],
                               existing_classes: List[Dict] = None,
                               context: str = None):
        """
        Analyze an artifact with streaming response (generator).

        Args:
            artifact_id: Artifact identifier
            features: Morphometric features dictionary
            existing_classes: List of existing taxonomic classes
            context: Additional archaeological context

        Yields:
            Text chunks as they arrive from Claude
        """
        # Build prompt
        prompt = self._build_classification_prompt(
            artifact_id, features, existing_classes, context
        )

        try:
            # Use streaming API
            with self.client.messages.stream(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            yield f"\n\n❌ Error: {str(e)}"

    def _build_classification_prompt(self, artifact_id: str, features: Dict,
                                     existing_classes: List[Dict] = None,
                                     context: str = None) -> str:
        """Build prompt for classification analysis."""
        # Check for Savignano features
        has_savignano = 'savignano' in features and isinstance(features.get('savignano'), dict)

        prompt = f"""You are an expert archaeological AI assistant specializing in Bronze Age artifact classification, particularly bronze axes.

Analyze the following artifact and provide classification insights:

**Artifact ID:** {artifact_id}

"""

        # If Savignano features available, use detailed morphometric format
        if has_savignano:
            from acs.savignano.prompt_formatter import format_savignano_features_for_ai, SavignanoPromptFormatter

            # Add formatted Savignano features
            prompt += format_savignano_features_for_ai(features)
            prompt += "\n"

            # Add classification guidance if it's Savignano type
            formatter = SavignanoPromptFormatter()
            guidance = formatter.create_classification_prompt_section(features)
            if guidance:
                prompt += guidance
                prompt += "\n"
        else:
            # Fallback to generic features if no Savignano analysis
            prompt += "**Morphometric Features:**\n"
            for key, value in features.items():
                if isinstance(value, (int, float)):
                    prompt += f"- {key.replace('_', ' ').title()}: {value:.4f}\n"
            prompt += "\n"

        # Add existing classes if available
        if existing_classes:
            prompt += "**Existing Taxonomic Classes:**\n"
            for cls in existing_classes[:10]:  # Limit to 10 classes
                prompt += f"- {cls['name']}: {cls.get('description', 'No description')}\n"
            prompt += "\n"

        # Add context
        if context:
            prompt += f"**Archaeological Context:**\n{context}\n\n"

        # Build task instructions with Savignano awareness
        prompt += """**Your Task:**

1. **Morphometric Analysis:**
   - Interpret the morphometric features provided
   - Identify distinctive characteristics (especially socket, flanges, blade shape)
   - Note any unusual measurements or unique features

2. **Typological Assessment:**"""

        if has_savignano:
            prompt += """
   - Consider the detailed morphometric analysis above
   - If socket, raised flanges, and lunate blade are present, consider Savignano Type
   - Check matrix classification if provided
   - Provide confidence level (High/Medium/Low)
   - Explain reasoning based on morphometric evidence

3. **Classification Recommendation:**
   - Primary Type: (e.g., Socketed Axe, Flanged Axe, Palstave, etc.)
   - Subtype: (e.g., Savignano Type if characteristics match)
   - Matrix Subclass: (if Savignano type and matrix identified)
   - Confidence level with reasoning
   - If characteristics don't match existing classes, suggest new subclass name

4. **Archaeological Interpretation:**
   - Chronological period (Bronze Age phase)
   - Production technique indicators (casting, finishing)
   - Functional considerations (ceremonial vs utilitarian)
   - Cultural context (if identifiable, e.g., Savignano tradition)
"""
        else:
            prompt += """
   - Suggest which existing class(es) this artifact might belong to
   - Provide confidence level (High/Medium/Low)
   - Explain your reasoning based on features

3. **Classification Recommendation:**
   - Recommend: classify into existing class OR create new class
   - If existing: which class and why
   - If new: suggest name and defining characteristics

4. **Archaeological Interpretation:**
   - Possible chronological period
   - Potential production technique indicators
   - Functional considerations
"""

        prompt += """
**Response Format (JSON):**
```json
{
  "morphometric_assessment": "...",
  "suggested_class": "...","""

        if has_savignano:
            prompt += """
  "subtype": "...",
  "matrix_id": "...","""

        prompt += """
  "confidence": "High|Medium|Low",
  "reasoning": "...",
  "recommendation": "classify_existing|create_new|create_subclass",
  "archaeological_notes": "..."
}
```
"""
        return prompt

    def compare_artifacts(self, artifact1_id: str, features1: Dict,
                         artifact2_id: str, features2: Dict,
                         similarity_score: float) -> Dict:
        """
        Generate comparative analysis of two artifacts.

        Args:
            artifact1_id: First artifact ID
            features1: First artifact features
            artifact2_id: Second artifact ID
            features2: Second artifact features
            similarity_score: Computed similarity score (0-1)

        Returns:
            Comparative analysis
        """
        prompt = f"""You are an expert archaeological analyst specializing in Bronze Age artifacts.

Compare these two artifacts and provide detailed analysis:

**Artifact 1: {artifact1_id}**
"""
        for key, value in features1.items():
            if isinstance(value, (int, float)):
                prompt += f"- {key.replace('_', ' ').title()}: {value:.4f}\n"

        prompt += f"\n**Artifact 2: {artifact2_id}**\n"
        for key, value in features2.items():
            if isinstance(value, (int, float)):
                prompt += f"- {key.replace('_', ' ').title()}: {value:.4f}\n"

        prompt += f"""
**Computed Similarity Score:** {similarity_score:.2%}

**Your Task:**

1. **Morphometric Comparison:**
   - Analyze feature differences
   - Identify significant similarities and differences
   - Interpret what these differences might indicate

2. **Typological Relationship:**
   - Do they likely come from the same typological class?
   - Could they be from the same casting matrix?
   - Evidence of different production stages?

3. **Archaeological Implications:**
   - Chronological relationship
   - Production technique similarities/differences
   - Functional equivalence or specialization

4. **Classification Recommendation:**
   - Should they be grouped together?
   - If separate, how should they be distinguished?

Provide a detailed but concise analysis (max 400 words).
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                'comparison_text': response.content[0].text,
                'model': self.model,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }

        except Exception as e:
            return {
                'error': str(e),
                'comparison_text': None
            }

    def generate_report_content(self, artifact1_id: str, artifact2_id: str,
                               features1: Dict, features2: Dict,
                               similarity_data: Dict) -> Dict:
        """
        Generate narrative content for comparison report.

        Args:
            artifact1_id: First artifact
            artifact2_id: Second artifact
            features1: First artifact features
            features2: Second artifact features
            similarity_data: Similarity analysis results

        Returns:
            Report content sections
        """
        prompt = f"""You are an expert archaeological report writer specializing in Bronze Age artifacts.

Generate a professional archaeological report comparing these two artifacts:

**Artifact IDs:** {artifact1_id} vs {artifact2_id}

**Similarity Score:** {similarity_data.get('similarity', 0):.2%}

**Feature Differences:**
"""
        for key, diff in similarity_data.get('feature_differences', {}).items():
            prompt += f"- {key.replace('_', ' ').title()}: {diff*100:.1f}% difference\n"

        prompt += """
**Generate the following report sections:**

1. **Executive Summary** (3-4 sentences)
   - High-level findings
   - Key similarity/difference highlights
   - Main conclusion

2. **Morphometric Analysis** (1 paragraph)
   - Detailed feature comparison
   - Statistical significance
   - Morphological patterns

3. **Typological Interpretation** (1 paragraph)
   - Classificatory implications
   - Relationship to known types
   - Chronological/cultural context

4. **Production Analysis** (1 paragraph)
   - Manufacturing technique insights
   - Evidence of shared/different matrices
   - Post-casting treatments

5. **Recommendations** (bullet points)
   - Classification actions
   - Further analysis needed
   - Confidence assessment

Format as JSON with these sections as keys.
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )

            # Try to parse as JSON, fallback to raw text
            content = response.content[0].text

            # Extract JSON if present
            try:
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content_json = json.loads(json_match.group(1))
                else:
                    # Try direct parse
                    content_json = json.loads(content)

                return content_json

            except json.JSONDecodeError:
                # Return as sections dict
                return {
                    'full_text': content,
                    'model': self.model
                }

        except Exception as e:
            return {
                'error': str(e),
                'full_text': None
            }

    def suggest_new_class_definition(self, reference_artifacts: List[Dict],
                                     proposed_name: str = None) -> Dict:
        """
        Suggest parameters for defining a new taxonomic class.

        Args:
            reference_artifacts: List of reference artifacts with features
            proposed_name: Proposed class name (optional)

        Returns:
            Suggested class definition
        """
        prompt = """You are an expert in archaeological taxonomy and classification systems.

Based on the following reference artifacts, suggest a formal taxonomic class definition:

**Reference Artifacts:**
"""
        for i, artifact in enumerate(reference_artifacts, 1):
            prompt += f"\n**Artifact {i}: {artifact['id']}**\n"
            for key, value in artifact.get('features', {}).items():
                if isinstance(value, (int, float)):
                    prompt += f"- {key}: {value:.4f}\n"

        if proposed_name:
            prompt += f"\n**Proposed Class Name:** {proposed_name}\n"

        prompt += """
**Your Task:**

1. **Class Name** (if not provided)
   - Suggest a formal archaeological name
   - Follow standard nomenclature

2. **Diagnostic Features**
   - Identify the most diagnostic morphometric features
   - Specify acceptable ranges for each feature
   - Suggest tolerance levels

3. **Class Description**
   - Formal definition (2-3 sentences)
   - Distinguishing characteristics
   - Typological position

4. **Parameter Weights**
   - Suggest importance weights for each feature
   - Justify weighting rationale

Format as structured JSON.
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Try to extract JSON
            try:
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    return json.loads(content)
            except json.JSONDecodeError:
                return {
                    'suggestion_text': content,
                    'model': self.model
                }

        except Exception as e:
            return {
                'error': str(e),
                'suggestion_text': None
            }

    def batch_classify(self, artifacts: List[Dict], existing_classes: List[Dict]) -> List[Dict]:
        """
        Classify multiple artifacts in one request.

        Args:
            artifacts: List of artifacts with features
            existing_classes: List of existing classes

        Returns:
            List of classification results
        """
        # For large batches, process in chunks
        if len(artifacts) > 10:
            results = []
            for i in range(0, len(artifacts), 10):
                chunk = artifacts[i:i+10]
                chunk_results = self._batch_classify_chunk(chunk, existing_classes)
                results.extend(chunk_results)
            return results
        else:
            return self._batch_classify_chunk(artifacts, existing_classes)

    def _batch_classify_chunk(self, artifacts: List[Dict],
                               existing_classes: List[Dict]) -> List[Dict]:
        """Process a chunk of artifacts for classification."""
        results = []
        for artifact in artifacts:
            result = self.analyze_artifact(
                artifact['id'],
                artifact['features'],
                existing_classes,
                artifact.get('context')
            )
            results.append(result)

        return results

    def analyze_multi_artifacts(self, artifacts: List[Dict],
                                existing_classes: List[Dict] = None,
                                context: str = None) -> Dict:
        """
        Analyze multiple artifacts together, considering relationships and patterns.

        Args:
            artifacts: List of artifacts with id, features, and optional stylistic data
            existing_classes: List of existing taxonomic classes
            context: Additional archaeological context

        Returns:
            Comprehensive multi-artifact analysis with grouping suggestions
        """
        prompt = f"""You are an expert archaeological AI assistant specializing in Bronze Age artifact classification.

Analyze the following {len(artifacts)} artifacts TOGETHER as a collection, considering:
- Morphometric similarities and differences
- Stylistic patterns and variations
- Potential groupings and relationships
- Taxonomic parameters that should be tuned for each group

**Artifacts to Analyze:**
"""

        for i, artifact in enumerate(artifacts, 1):
            prompt += f"\n**Artifact {i}: {artifact['id']}**\n"
            prompt += "Morphometric Features:\n"
            for key, value in artifact.get('features', {}).items():
                if isinstance(value, (int, float)):
                    prompt += f"  - {key.replace('_', ' ').title()}: {value:.4f}\n"

            # Add stylistic features if available
            if 'stylistic_features' in artifact:
                prompt += "Stylistic Features:\n"
                for key, value in artifact['stylistic_features'].items():
                    if isinstance(value, (int, float)):
                        prompt += f"  - {key.replace('_', ' ').title()}: {value:.4f}\n"

        if existing_classes:
            prompt += "\n**Existing Taxonomic Classes:**\n"
            for cls in existing_classes[:15]:
                prompt += f"- {cls['name']}: {cls.get('description', 'No description')}\n"

        if context:
            prompt += f"\n**Archaeological Context:**\n{context}\n"

        prompt += """
**Your Task:**

1. **Collection Overview:**
   - Describe the overall morphometric and stylistic characteristics of this collection
   - Identify major patterns, trends, and outliers
   - Note the range of variation

2. **Grouping Analysis:**
   - Suggest how these artifacts should be grouped (e.g., by type, period, production technique)
   - For each suggested group, identify:
     * Which artifacts belong to it
     * Diagnostic features that define the group
     * Morphometric and stylistic parameters

3. **Taxonomic Parameter Recommendations:**
   - For EACH artifact (or group), suggest specific parameters to tune:
     * Feature weights (which features are most diagnostic)
     * Tolerance thresholds for classification
     * Minimum/maximum values for key dimensions
     * Stylistic analysis parameters (symmetry, profile curves, etc.)

4. **Detailed Analysis for Each Artifact:**
   - Individual assessment within the collection context
   - Suggested classification (existing class or new class proposal)
   - Confidence level and reasoning
   - Specific parameters to apply for analysis

5. **Batch Processing Recommendation:**
   - Should these parameters be applied automatically?
   - Which artifacts need manual review?
   - Suggested analysis workflow

**Response Format (JSON):**
```json
{
  "collection_overview": "...",
  "suggested_groups": [
    {
      "group_name": "...",
      "artifact_ids": ["..."],
      "diagnostic_features": ["..."],
      "parameters": {
        "feature_weights": {"length": 1.5, "width": 1.0, ...},
        "tolerances": {"volume": 0.15, ...},
        "stylistic_thresholds": {...}
      }
    }
  ],
  "individual_analyses": [
    {
      "artifact_id": "...",
      "group": "...",
      "classification_suggestion": "...",
      "confidence": "High|Medium|Low",
      "parameters_to_apply": {
        "morphometric": {...},
        "stylistic": {...},
        "taxonomic": {...}
      },
      "reasoning": "..."
    }
  ],
  "batch_recommendation": {
    "auto_apply": true/false,
    "manual_review_needed": ["artifact_id1", ...],
    "workflow": "..."
  }
}
```

Provide a comprehensive, actionable analysis that I can use to optimize the classification system.
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,  # Longer response for multi-artifact analysis
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text

            # Try to extract JSON
            try:
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(1))
                else:
                    analysis = json.loads(content)

                return {
                    'analysis': analysis,
                    'raw_text': content,
                    'model': self.model,
                    'usage': {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens
                    }
                }

            except json.JSONDecodeError:
                return {
                    'analysis': None,
                    'raw_text': content,
                    'model': self.model,
                    'usage': {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens
                    }
                }

        except Exception as e:
            return {
                'error': str(e),
                'analysis': None,
                'raw_text': None
            }

    def suggest_analysis_parameters(self, artifact_id: str, features: Dict[str, Any],
                                   stylistic_features: Dict[str, Any] = None) -> Dict:
        """
        Suggest detailed analysis parameters for a specific artifact.

        Args:
            artifact_id: Artifact identifier
            features: Morphometric features
            stylistic_features: Stylistic analysis features (optional)

        Returns:
            Suggested parameters with reasoning
        """
        prompt = f"""You are an expert in archaeological morphometric and stylistic analysis.

Analyze this artifact and suggest optimal analysis parameters:

**Artifact ID:** {artifact_id}

**Morphometric Features:**
"""
        for key, value in features.items():
            if isinstance(value, (int, float)):
                prompt += f"- {key.replace('_', ' ').title()}: {value:.4f}\n"

        if stylistic_features:
            prompt += "\n**Stylistic Features:**\n"
            for key, value in stylistic_features.items():
                if isinstance(value, (int, float)):
                    prompt += f"- {key.replace('_', ' ').title()}: {value:.4f}\n"

        prompt += """
**Your Task:**

Suggest optimal analysis parameters for this specific artifact:

1. **Morphometric Analysis Parameters:**
   - Feature importance weights (0.0-2.0)
   - Classification tolerance thresholds
   - Dimensional ranges for comparison

2. **Stylistic Analysis Parameters:**
   - Symmetry analysis settings
   - Profile curve resolution
   - Detail preservation level
   - Edge detection sensitivity

3. **Taxonomic Classification Parameters:**
   - Similarity metric to use (euclidean, cosine, etc.)
   - Minimum similarity threshold
   - Number of similar artifacts to retrieve
   - Feature normalization strategy

4. **Quality Assessment:**
   - Expected measurement precision
   - Data completeness check
   - Outlier detection thresholds

**Response Format (JSON):**
```json
{
  "morphometric_params": {
    "feature_weights": {...},
    "tolerances": {...},
    "ranges": {...}
  },
  "stylistic_params": {
    "symmetry_tolerance": 0.05,
    "profile_resolution": 100,
    "detail_level": "high",
    "edge_sensitivity": 0.8
  },
  "taxonomic_params": {
    "similarity_metric": "cosine",
    "min_similarity": 0.70,
    "n_results": 10,
    "normalization": "standard"
  },
  "reasoning": "..."
}
```
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON
            try:
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    params = json.loads(json_match.group(1))
                else:
                    params = json.loads(content)

                return {
                    'parameters': params,
                    'raw_text': content,
                    'model': self.model
                }

            except json.JSONDecodeError:
                return {
                    'parameters': None,
                    'raw_text': content,
                    'model': self.model
                }

        except Exception as e:
            return {
                'error': str(e),
                'parameters': None
            }

    def interpret_technological_analysis(self, artifact_id: str,
                                        tech_features: Dict,
                                        tech_report: str) -> Dict:
        """
        Generate structured archaeological interpretation of technological analysis.

        Uses temperature 0.1 for factual, non-hallucinating responses.
        Returns JSON-structured interpretation.

        Args:
            artifact_id: Artifact identifier
            tech_features: Technological features dictionary
            tech_report: Technical report text

        Returns:
            Structured interpretation with production, use, conservation sections
        """
        prompt = f"""You are an expert archaeologist specializing in Bronze Age metallurgy and artifact analysis.

Analyze this technological data for artifact {artifact_id} and provide a STRUCTURED archaeological interpretation.

{tech_report}

**IMPORTANT**: Respond ONLY with valid JSON in this EXACT format (no extra text):

{{
  "production_interpretation": {{
    "method": "casting|forging|unknown",
    "confidence": 0.0-1.0,
    "description": "1-2 sentences explaining production technique based on data",
    "workshop_quality": "high|medium|low|unknown",
    "evidence": ["specific data point 1", "specific data point 2"]
  }},
  "use_life": {{
    "intensity": "heavy|moderate|light|unknown",
    "duration": "long-term|medium-term|short-term|unknown",
    "description": "1-2 sentences on usage patterns",
    "maintenance": "yes|no|unknown",
    "evidence": ["specific data point 1", "specific data point 2"]
  }},
  "conservation_state": {{
    "condition": "excellent|good|fair|poor|critical",
    "degradation_type": "corrosion|wear|mechanical|mixed",
    "description": "1-2 sentences on current state",
    "functional": true|false,
    "evidence": ["specific data point 1", "specific data point 2"]
  }},
  "archaeological_context": {{
    "period_indicators": ["indicator 1", "indicator 2"],
    "comparative_notes": "1 sentence comparing to known Bronze Age types",
    "research_value": "high|medium|low",
    "recommendations": ["recommendation 1", "recommendation 2"]
  }},
  "summary": "2-3 sentences synthesizing all findings for report"
}}

**STRICT RULES**:
1. Base ONLY on provided numerical data
2. Use EXACT numbers from the report (e.g., "edge angle 86.25°")
3. If uncertain, use "unknown" rather than guessing
4. Keep descriptions factual and concise
5. Reference specific threshold values (e.g., "hammering intensity 0.55 < 0.6 threshold")
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.1,  # Very low for factual responses
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text.strip()

            # Extract JSON from response
            try:
                # Try to find JSON in markdown code blocks
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    interpretation = json.loads(json_match.group(1))
                else:
                    # Try parsing entire response
                    interpretation = json.loads(content)

                return {
                    'artifact_id': artifact_id,
                    'interpretation': interpretation,
                    'raw_response': content,
                    'model': self.model,
                    'temperature': 0.1,
                    'usage': {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens
                    }
                }

            except json.JSONDecodeError as e:
                return {
                    'artifact_id': artifact_id,
                    'error': f'JSON parse error: {str(e)}',
                    'raw_response': content,
                    'interpretation': None
                }

        except Exception as e:
            return {
                'artifact_id': artifact_id,
                'error': str(e),
                'interpretation': None
            }

    def interpret_batch_technological_analysis(self, batch_results: Dict,
                                               batch_report: str) -> Dict:
        """
        Generate structured archaeological interpretation for batch analysis.

        Args:
            batch_results: Batch analysis results
            batch_report: Batch report text

        Returns:
            Structured batch interpretation
        """
        total = batch_results['total_analyzed']
        summary = batch_results.get('summary', {})

        prompt = f"""You are an expert archaeologist analyzing a collection of {total} Bronze Age artifacts.

{batch_report}

**IMPORTANT**: Respond ONLY with valid JSON in this EXACT format:

{{
  "collection_overview": {{
    "homogeneity": "very_homogeneous|homogeneous|heterogeneous|very_heterogeneous",
    "production_consistency": "uniform|variable|mixed",
    "description": "2-3 sentences on overall collection character"
  }},
  "production_analysis": {{
    "dominant_technique": "casting|forging|mixed|unknown",
    "workshop_evidence": "same_workshop|multiple_workshops|unknown",
    "quality_assessment": "high|medium|low|variable",
    "description": "2-3 sentences on production patterns",
    "evidence": ["data point 1", "data point 2"]
  }},
  "use_patterns": {{
    "intensity_distribution": "uniform_heavy|uniform_moderate|variable|minimal",
    "functional_state": "mostly_functional|partially_functional|non_functional",
    "description": "2-3 sentences on usage evidence",
    "evidence": ["data point 1", "data point 2"]
  }},
  "chronological_cultural": {{
    "period_consistency": "single_period|multi_period|unknown",
    "cultural_attribution": "description of cultural context",
    "deposition_context": "ritual|utilitarian|abandonment|unknown",
    "description": "2-3 sentences on archaeological implications"
  }},
  "research_recommendations": [
    "specific recommendation 1",
    "specific recommendation 2",
    "specific recommendation 3"
  ],
  "executive_summary": "3-4 sentences for archaeological report"
}}

Base ONLY on the numerical data provided. Use EXACT statistics from the report.
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            try:
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    interpretation = json.loads(json_match.group(1))
                else:
                    interpretation = json.loads(content)

                return {
                    'interpretation': interpretation,
                    'raw_response': content,
                    'model': self.model,
                    'temperature': 0.1
                }

            except json.JSONDecodeError as e:
                return {
                    'error': f'JSON parse error: {str(e)}',
                    'raw_response': content,
                    'interpretation': None
                }

        except Exception as e:
            return {
                'error': str(e),
                'interpretation': None
            }


# Global AI assistant instance
_ai_instance = None


def get_ai_assistant() -> AIClassificationAssistant:
    """Get or create global AI assistant instance."""
    global _ai_instance
    if _ai_instance is None:
        try:
            _ai_instance = AIClassificationAssistant()
        except ValueError as e:
            # API key not set - return None
            print(f"Warning: AI Assistant not initialized: {e}")
            return None
    return _ai_instance
