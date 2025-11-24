"""
Machine Learning Classifier
============================

Learns from validated classifications to improve predictions.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class MLArtifactClassifier:
    """
    Machine Learning classifier that learns from validated archaeological classifications.

    This system:
    1. Trains on validated human classifications
    2. Improves predictions over time
    3. Provides confidence scores
    4. Explains predictions
    """

    def __init__(self, model_path: str = None):
        """Initialize ML classifier."""
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.class_labels = []
        self.is_trained = False
        self.training_history = []
        self.model_path = model_path or 'acs_ml_model.pkl'

        # Try to load existing model
        if os.path.exists(self.model_path):
            self.load_model(self.model_path)

    def train(self, training_data: List[Dict], validation_split: float = 0.2,
             algorithm: str = 'random_forest') -> Dict:
        """
        Train the classifier on validated data.

        Args:
            training_data: List of training samples with 'features' and 'class_label'
            validation_split: Fraction of data for validation
            algorithm: 'random_forest' or 'gradient_boosting'

        Returns:
            Training metrics
        """
        if len(training_data) < 10:
            return {
                'error': 'Need at least 10 training samples to train model',
                'n_samples': len(training_data)
            }

        # Extract features and labels
        X, y, self.feature_names = self._prepare_data(training_data)

        # Store class labels
        self.class_labels = list(set(y))

        if len(self.class_labels) < 2:
            return {
                'error': 'Need at least 2 different classes to train model',
                'n_classes': len(self.class_labels)
            }

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Initialize model
        if algorithm == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif algorithm == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            return {'error': f'Unknown algorithm: {algorithm}'}

        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True

        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        val_score = self.model.score(X_val_scaled, y_val)

        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=min(5, len(X_train)//2)
        )

        # Predictions on validation set
        y_pred = self.model.predict(X_val_scaled)

        # Feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
        feature_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        # Store training history
        training_record = {
            'timestamp': datetime.now().isoformat(),
            'n_samples': len(training_data),
            'n_classes': len(self.class_labels),
            'algorithm': algorithm,
            'train_accuracy': float(train_score),
            'val_accuracy': float(val_score),
            'cv_mean': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std())
        }
        self.training_history.append(training_record)

        # Save model
        self.save_model(self.model_path)

        return {
            'success': True,
            'n_samples': len(training_data),
            'n_train': len(X_train),
            'n_val': len(X_val),
            'n_classes': len(self.class_labels),
            'classes': self.class_labels,
            'train_accuracy': train_score,
            'val_accuracy': val_score,
            'cv_scores': {
                'mean': cv_scores.mean(),
                'std': cv_scores.std(),
                'scores': cv_scores.tolist()
            },
            'feature_importance': feature_importance,
            'classification_report': classification_report(
                y_val, y_pred, output_dict=True, zero_division=0
            )
        }

    def _prepare_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, List[str], List[str]]:
        """Prepare training data for ML."""
        # Collect all feature names
        feature_names_set = set()
        for sample in training_data:
            feature_names_set.update(sample['features'].keys())

        feature_names = sorted(list(feature_names_set))

        # Build feature matrix
        X = []
        y = []

        for sample in training_data:
            features = sample['features']
            # Create feature vector with consistent ordering
            feature_vector = [features.get(fname, 0.0) for fname in feature_names]
            X.append(feature_vector)
            y.append(sample['class_label'])

        return np.array(X), y, feature_names

    def predict(self, features: Dict[str, float]) -> Dict:
        """
        Predict class for new artifact.

        Args:
            features: Feature dictionary

        Returns:
            Prediction results with confidence
        """
        if not self.is_trained:
            return {
                'error': 'Model not trained yet',
                'prediction': None
            }

        # Prepare feature vector
        feature_vector = [features.get(fname, 0.0) for fname in self.feature_names]
        X = np.array([feature_vector])

        # Scale
        X_scaled = self.scaler.transform(X)

        # Predict
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]

        # Get top 3 predictions
        top_indices = np.argsort(probabilities)[::-1][:3]
        top_predictions = [
            {
                'class': self.class_labels[idx],
                'confidence': float(probabilities[idx])
            }
            for idx in top_indices
        ]

        return {
            'prediction': prediction,
            'confidence': float(probabilities[np.argmax(probabilities)]),
            'top_predictions': top_predictions,
            'all_probabilities': {
                self.class_labels[i]: float(probabilities[i])
                for i in range(len(self.class_labels))
            }
        }

    def explain_prediction(self, features: Dict[str, float], prediction_result: Dict = None) -> Dict:
        """
        Explain why a particular prediction was made.

        Args:
            features: Feature dictionary
            prediction_result: Optional prediction result to explain

        Returns:
            Explanation of the prediction
        """
        if not self.is_trained:
            return {'error': 'Model not trained yet'}

        if prediction_result is None:
            prediction_result = self.predict(features)

        # Get feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))

        # Sort by importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5 most important features

        # Get actual feature values
        feature_values = {
            fname: features.get(fname, 0.0)
            for fname, _ in sorted_features
        }

        explanation = {
            'predicted_class': prediction_result.get('prediction'),
            'confidence': prediction_result.get('confidence'),
            'key_features': [
                {
                    'feature': fname,
                    'value': feature_values[fname],
                    'importance': float(importance),
                    'contribution': 'high' if importance > 0.15 else 'medium' if importance > 0.05 else 'low'
                }
                for fname, importance in sorted_features
            ],
            'interpretation': self._generate_interpretation(
                prediction_result.get('prediction'),
                feature_values,
                sorted_features
            )
        }

        return explanation

    def _generate_interpretation(self, predicted_class: str,
                                feature_values: Dict, important_features: List) -> str:
        """Generate human-readable interpretation."""
        interpretation = f"The artifact was classified as '{predicted_class}' based primarily on: "

        feature_descriptions = []
        for fname, importance in important_features[:3]:
            value = feature_values[fname]
            feature_descriptions.append(
                f"{fname.replace('_', ' ')} ({value:.2f}, importance: {importance:.1%})"
            )

        interpretation += ", ".join(feature_descriptions) + "."

        return interpretation

    def retrain_with_new_samples(self, new_samples: List[Dict]) -> Dict:
        """
        Incrementally update model with new validated samples.

        Args:
            new_samples: New training samples

        Returns:
            Retraining results
        """
        if not self.is_trained:
            return self.train(new_samples)

        # Combine with existing data if available
        # For now, just retrain from scratch
        # In production, could implement incremental learning
        return self.train(new_samples)

    def evaluate_on_test_set(self, test_data: List[Dict]) -> Dict:
        """
        Evaluate model on test data.

        Args:
            test_data: Test samples with ground truth labels

        Returns:
            Evaluation metrics
        """
        if not self.is_trained:
            return {'error': 'Model not trained yet'}

        X_test, y_test, _ = self._prepare_data(test_data)
        X_test_scaled = self.scaler.transform(X_test)

        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        accuracy = self.model.score(X_test_scaled, y_test)

        # Detailed metrics
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        conf_matrix = confusion_matrix(y_test, y_pred, labels=self.class_labels)

        return {
            'accuracy': accuracy,
            'n_test_samples': len(test_data),
            'classification_report': report,
            'confusion_matrix': conf_matrix.tolist(),
            'class_labels': self.class_labels
        }

    def get_training_statistics(self) -> Dict:
        """Get statistics about model training."""
        if not self.is_trained:
            return {
                'is_trained': False,
                'message': 'Model not trained yet'
            }

        return {
            'is_trained': True,
            'n_classes': len(self.class_labels),
            'classes': self.class_labels,
            'n_features': len(self.feature_names),
            'features': self.feature_names,
            'training_history': self.training_history,
            'model_type': type(self.model).__name__
        }

    def save_model(self, path: str):
        """Save model to disk."""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'class_labels': self.class_labels,
            'is_trained': self.is_trained,
            'training_history': self.training_history
        }

        joblib.dump(model_data, path)

    def load_model(self, path: str):
        """Load model from disk."""
        if not os.path.exists(path):
            return False

        try:
            model_data = joblib.load(path)

            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.class_labels = model_data['class_labels']
            self.is_trained = model_data['is_trained']
            self.training_history = model_data.get('training_history', [])

            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def get_feature_importance(self) -> Dict:
        """Get feature importance scores."""
        if not self.is_trained or not hasattr(self.model, 'feature_importances_'):
            return {}

        importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))

        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


# Global ML classifier instance
_ml_instance = None


def get_ml_classifier() -> MLArtifactClassifier:
    """Get or create global ML classifier instance."""
    global _ml_instance
    if _ml_instance is None:
        _ml_instance = MLArtifactClassifier()
    return _ml_instance
