"""
Formal Taxonomy System
=====================

Parametric, traceable, and versioned classification system for archaeological artifacts.

Key features:
- Explicit quantitative parameters
- Complete version history with hash-based tracking
- Mandatory justification for modifications
- Statistical validation
- Automatic class discovery from clustering
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
import hashlib
import numpy as np


@dataclass
class ClassificationParameter:
    """Single classification parameter with validation constraints."""

    name: str
    value: float
    min_threshold: float
    max_threshold: float
    weight: float = 1.0
    measurement_unit: str = "mm"
    tolerance: float = 0.1

    def validate(self, measured_value: float) -> bool:
        """Check if measured value falls within acceptable range."""
        return self.min_threshold <= measured_value <= self.max_threshold

    def distance_from_ideal(self, measured_value: float) -> float:
        """Compute normalized distance from ideal value."""
        if self.tolerance == 0:
            return 0.0 if measured_value == self.value else 1.0
        return abs(measured_value - self.value) / self.tolerance

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'min_threshold': self.min_threshold,
            'max_threshold': self.max_threshold,
            'weight': self.weight,
            'measurement_unit': self.measurement_unit,
            'tolerance': self.tolerance
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ClassificationParameter':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TaxonomicClass:
    """Formally defined taxonomic class with explicit parameters."""

    class_id: str
    name: str
    description: str
    morphometric_params: Dict[str, ClassificationParameter]
    technological_params: Dict[str, ClassificationParameter]
    optional_features: Dict[str, bool] = field(default_factory=dict)
    confidence_threshold: float = 0.75
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    validated_samples: List[str] = field(default_factory=list)
    parameter_hash: str = field(default="", init=False)

    def __post_init__(self):
        """Compute parameter hash after initialization."""
        self.parameter_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute unique hash of classification parameters."""
        params_dict = {
            'morphometric': {k: v.to_dict() for k, v in self.morphometric_params.items()},
            'technological': {k: v.to_dict() for k, v in self.technological_params.items()},
            'optional': self.optional_features,
            'threshold': self.confidence_threshold
        }
        params_str = json.dumps(params_dict, sort_keys=True)
        return hashlib.sha256(params_str.encode()).hexdigest()[:16]

    def classify_object(self, obj_features: Dict) -> Tuple[bool, float, Dict]:
        """
        Classify an object according to formal parameters.

        Args:
            obj_features: Dictionary of measured features

        Returns:
            (is_member, confidence_score, diagnostic_details)
        """
        scores = []
        diagnostic = {}

        # Evaluate morphometric parameters
        for param_name, param in self.morphometric_params.items():
            if param_name not in obj_features:
                return False, 0.0, {'error': f'Missing parameter: {param_name}'}

            measured = obj_features[param_name]

            # Check hard constraints
            if not param.validate(measured):
                diagnostic[param_name] = {
                    'status': 'FAIL',
                    'measured': measured,
                    'expected_range': (param.min_threshold, param.max_threshold)
                }
                return False, 0.0, diagnostic

            # Compute weighted score
            distance = param.distance_from_ideal(measured)
            score = max(0, 1 - distance) * param.weight
            scores.append(score)

            diagnostic[param_name] = {
                'status': 'PASS',
                'measured': measured,
                'ideal': param.value,
                'distance': distance,
                'score': score
            }

        # Evaluate technological parameters
        for param_name, param in self.technological_params.items():
            if param_name not in obj_features:
                return False, 0.0, {'error': f'Missing parameter: {param_name}'}

            measured = obj_features[param_name]

            if not param.validate(measured):
                diagnostic[param_name] = {
                    'status': 'FAIL',
                    'measured': measured,
                    'expected_range': (param.min_threshold, param.max_threshold)
                }
                return False, 0.0, diagnostic

            distance = param.distance_from_ideal(measured)
            score = max(0, 1 - distance) * param.weight
            scores.append(score)

            diagnostic[param_name] = {
                'status': 'PASS',
                'measured': measured,
                'ideal': param.value,
                'distance': distance,
                'score': score
            }

        # Evaluate optional features
        optional_score = 0
        optional_weight = 0.2

        for feature_name, expected in self.optional_features.items():
            if feature_name in obj_features:
                present = obj_features[feature_name]
                if present == expected:
                    optional_score += optional_weight
                    diagnostic[feature_name] = {'status': 'MATCH', 'present': present}
                else:
                    diagnostic[feature_name] = {
                        'status': 'MISMATCH',
                        'present': present,
                        'expected': expected
                    }

        # Compute final confidence
        total_weight = (
            sum(p.weight for p in self.morphometric_params.values()) +
            sum(p.weight for p in self.technological_params.values())
        )

        if total_weight == 0:
            confidence = 0.0
        else:
            confidence = (sum(scores) + optional_score) / (
                total_weight + optional_weight * len(self.optional_features)
            )

        is_member = confidence >= self.confidence_threshold

        return is_member, confidence, diagnostic

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'class_id': self.class_id,
            'name': self.name,
            'description': self.description,
            'parameter_hash': self.parameter_hash,
            'morphometric_params': {k: v.to_dict() for k, v in self.morphometric_params.items()},
            'technological_params': {k: v.to_dict() for k, v in self.technological_params.items()},
            'optional_features': self.optional_features,
            'confidence_threshold': self.confidence_threshold,
            'created_date': self.created_date.isoformat() if isinstance(self.created_date, datetime) else self.created_date,
            'created_by': self.created_by,
            'validated_samples': self.validated_samples
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TaxonomicClass':
        """Create from dictionary."""
        # Convert parameter dicts back to ClassificationParameter objects
        morphometric_params = {
            k: ClassificationParameter.from_dict(v)
            for k, v in data['morphometric_params'].items()
        }
        technological_params = {
            k: ClassificationParameter.from_dict(v)
            for k, v in data['technological_params'].items()
        }

        # Handle datetime
        created_date = data.get('created_date')
        if isinstance(created_date, str):
            created_date = datetime.fromisoformat(created_date)
        elif created_date is None:
            created_date = datetime.now()

        return cls(
            class_id=data['class_id'],
            name=data['name'],
            description=data['description'],
            morphometric_params=morphometric_params,
            technological_params=technological_params,
            optional_features=data.get('optional_features', {}),
            confidence_threshold=data.get('confidence_threshold', 0.75),
            created_date=created_date,
            created_by=data.get('created_by', ''),
            validated_samples=data.get('validated_samples', [])
        )


class FormalTaxonomySystem:
    """Complete taxonomy system with versioning and traceability."""

    def __init__(self):
        """Initialize taxonomy system."""
        self.classes: Dict[str, TaxonomicClass] = {}
        self.version_history: List[Dict] = []
        self.classification_log: List[Dict] = []

    def define_class_from_reference_group(
        self,
        class_name: str,
        reference_objects: List[Dict],
        parameter_weights: Optional[Dict[str, float]] = None,
        tolerance_factor: float = 0.15
    ) -> TaxonomicClass:
        """
        Create taxonomic class from validated reference group.

        Args:
            class_name: Name for the new class
            reference_objects: List of reference artifact features
            parameter_weights: Optional weights for each parameter
            tolerance_factor: Tolerance as fraction of std dev

        Returns:
            New TaxonomicClass instance
        """
        if len(reference_objects) < 2:
            raise ValueError("Need at least 2 reference objects")

        if parameter_weights is None:
            parameter_weights = {}

        # Compute statistics
        param_stats = self._compute_reference_statistics(reference_objects)

        # Define morphometric parameters
        morphometric_params = {}
        morphometric_keys = ['volume', 'length', 'width', 'thickness', 'surface_area']

        for param_name in morphometric_keys:
            if param_name in param_stats:
                stats = param_stats[param_name]
                morphometric_params[param_name] = ClassificationParameter(
                    name=param_name,
                    value=stats['mean'],
                    min_threshold=stats['mean'] - stats['std'] * 2,
                    max_threshold=stats['mean'] + stats['std'] * 2,
                    weight=parameter_weights.get(param_name, 1.0),
                    measurement_unit=stats.get('unit', 'mm'),
                    tolerance=stats['std'] * tolerance_factor
                )

        # Define technological parameters
        technological_params = {}
        technological_keys = ['socket_depth', 'socket_diameter', 'edge_angle', 'hammering_index']

        for param_name in technological_keys:
            if param_name in param_stats:
                stats = param_stats[param_name]
                technological_params[param_name] = ClassificationParameter(
                    name=param_name,
                    value=stats['mean'],
                    min_threshold=stats['mean'] - stats['std'] * 2,
                    max_threshold=stats['mean'] + stats['std'] * 2,
                    weight=parameter_weights.get(param_name, 1.0),
                    measurement_unit=stats.get('unit', 'mm'),
                    tolerance=stats['std'] * tolerance_factor
                )

        # Identify optional features (presence > 80% or < 20%)
        optional_features = {}
        for feature in ['has_socket', 'has_midrib', 'hammered']:
            if all(feature in obj for obj in reference_objects):
                presence_rate = sum(1 for obj in reference_objects if obj.get(feature, False)) / len(reference_objects)
                if presence_rate > 0.8:
                    optional_features[feature] = True
                elif presence_rate < 0.2:
                    optional_features[feature] = False

        # Create class
        class_id = f"TYPE_{class_name.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        new_class = TaxonomicClass(
            class_id=class_id,
            name=class_name,
            description=f"Class defined from {len(reference_objects)} reference objects",
            morphometric_params=morphometric_params,
            technological_params=technological_params,
            optional_features=optional_features,
            confidence_threshold=0.75,
            created_by="system",
            validated_samples=[obj.get('id', f'ref_{i}') for i, obj in enumerate(reference_objects)]
        )

        # Register class
        self.classes[class_id] = new_class

        # Log creation
        self.version_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'CREATE_CLASS',
            'class_id': class_id,
            'parameter_hash': new_class.parameter_hash,
            'reference_count': len(reference_objects)
        })

        return new_class

    def modify_class_parameters(
        self,
        class_id: str,
        parameter_changes: Dict[str, Dict],
        justification: str,
        operator: str
    ) -> TaxonomicClass:
        """
        Modify class parameters with mandatory justification.

        Args:
            class_id: ID of class to modify
            parameter_changes: Dictionary of changes
            justification: Archaeological justification
            operator: Who is making the change

        Returns:
            New versioned TaxonomicClass
        """
        if class_id not in self.classes:
            raise ValueError(f"Class {class_id} not found")

        if not justification or not operator:
            raise ValueError("Justification and operator are mandatory")

        old_class = self.classes[class_id]
        old_hash = old_class.parameter_hash

        # Apply changes
        new_class = self._apply_parameter_changes(old_class, parameter_changes)
        new_class.created_by = operator

        # Generate versioned ID
        base_id = class_id.rsplit('_v', 1)[0] if '_v' in class_id else class_id
        version = len([h for h in self.version_history if base_id in h.get('class_id', '')]) + 1
        new_class.class_id = f"{base_id}_v{version}"

        # Register new version
        self.classes[new_class.class_id] = new_class

        # Log modification
        self.version_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'MODIFY_CLASS',
            'old_class_id': class_id,
            'new_class_id': new_class.class_id,
            'old_hash': old_hash,
            'new_hash': new_class.parameter_hash,
            'changes': parameter_changes,
            'justification': justification,
            'operator': operator
        })

        return new_class

    def classify_object(
        self,
        obj_features: Dict,
        return_all_scores: bool = False
    ):
        """
        Classify object using all defined classes.

        Args:
            obj_features: Object features to classify
            return_all_scores: Return scores for all classes

        Returns:
            Best match or list of all matches
        """
        results = []

        for class_id, tax_class in self.classes.items():
            is_member, confidence, diagnostic = tax_class.classify_object(obj_features)

            results.append({
                'class_id': class_id,
                'class_name': tax_class.name,
                'is_member': is_member,
                'confidence': confidence,
                'diagnostic': diagnostic
            })

        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)

        # Log classification
        self.classification_log.append({
            'timestamp': datetime.now().isoformat(),
            'object_id': obj_features.get('id', 'unknown'),
            'best_match': results[0]['class_id'] if results else None,
            'confidence': results[0]['confidence'] if results else 0.0
        })

        if return_all_scores:
            return results
        else:
            return results[0] if results else None

    def discover_new_classes(
        self,
        unclassified_objects: List[Dict],
        min_cluster_size: int = 5,
        eps: float = 0.3
    ) -> List[TaxonomicClass]:
        """
        Discover new classes from unclassified objects using clustering.

        Args:
            unclassified_objects: List of unclassified artifact features
            min_cluster_size: Minimum artifacts per cluster
            eps: DBSCAN epsilon parameter

        Returns:
            List of newly created TaxonomicClass instances
        """
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler

        if len(unclassified_objects) < min_cluster_size:
            return []

        # Extract feature vectors
        feature_names = ['volume', 'length', 'width', 'thickness']
        X = []
        for obj in unclassified_objects:
            row = [obj.get(f, 0.0) for f in feature_names]
            X.append(row)

        X = np.array(X)

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Cluster
        clustering = DBSCAN(eps=eps, min_samples=min_cluster_size).fit(X_scaled)

        # Create class for each cluster
        new_classes = []
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:  # noise
                continue

            cluster_objects = [
                obj for i, obj in enumerate(unclassified_objects)
                if clustering.labels_[i] == cluster_id
            ]

            if len(cluster_objects) >= min_cluster_size:
                new_class = self.define_class_from_reference_group(
                    class_name=f"DiscoveredType_{cluster_id}",
                    reference_objects=cluster_objects,
                    parameter_weights={f: 1.0 for f in feature_names}
                )
                new_classes.append(new_class)

        return new_classes

    def export_taxonomy(self, filepath: str):
        """Export complete taxonomy to JSON file."""
        export_data = {
            'classes': {cid: c.to_dict() for cid, c in self.classes.items()},
            'version_history': self.version_history,
            'classification_log': self.classification_log,
            'exported_at': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

    def import_taxonomy(self, filepath: str):
        """Import taxonomy from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Load classes
        for class_id, class_data in data.get('classes', {}).items():
            self.classes[class_id] = TaxonomicClass.from_dict(class_data)

        # Load history
        self.version_history = data.get('version_history', [])
        self.classification_log = data.get('classification_log', [])

    def get_statistics(self) -> Dict:
        """Get taxonomy statistics."""
        return {
            'n_classes': len(self.classes),
            'total_classifications': len(self.classification_log),
            'total_modifications': len([h for h in self.version_history if h['action'] == 'MODIFY_CLASS']),
            'classes': {
                cid: {
                    'name': c.name,
                    'n_validated_samples': len(c.validated_samples),
                    'n_parameters': len(c.morphometric_params) + len(c.technological_params),
                    'confidence_threshold': c.confidence_threshold
                }
                for cid, c in self.classes.items()
            }
        }

    def _compute_reference_statistics(self, objects: List[Dict]) -> Dict:
        """Compute statistics on reference group parameters."""
        stats = {}
        param_names = set()

        for obj in objects:
            param_names.update(obj.keys())

        for param in param_names:
            if param in ['id', 'profiles']:
                continue

            values = [
                obj[param] for obj in objects
                if param in obj and isinstance(obj[param], (int, float))
            ]

            if values:
                stats[param] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'unit': 'mm'
                }

        return stats

    def _apply_parameter_changes(
        self,
        old_class: TaxonomicClass,
        changes: Dict
    ) -> TaxonomicClass:
        """Apply parameter changes to create new class version."""
        import copy

        new_class = copy.deepcopy(old_class)

        for param_type, params in changes.items():
            if param_type == 'morphometric':
                for param_name, new_values in params.items():
                    if param_name in new_class.morphometric_params:
                        for key, value in new_values.items():
                            setattr(new_class.morphometric_params[param_name], key, value)

            elif param_type == 'technological':
                for param_name, new_values in params.items():
                    if param_name in new_class.technological_params:
                        for key, value in new_values.items():
                            setattr(new_class.technological_params[param_name], key, value)

        # Recompute hash
        new_class.parameter_hash = new_class._compute_hash()

        return new_class
