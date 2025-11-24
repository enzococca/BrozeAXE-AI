"""Classification system data models."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class ParameterModel(BaseModel):
    """Classification parameter model."""

    name: str
    value: float
    min_threshold: float
    max_threshold: float
    weight: float = 1.0
    measurement_unit: str = "mm"
    tolerance: float = 0.1


class TaxonomicClassModel(BaseModel):
    """Taxonomic class model."""

    class_id: str
    name: str
    description: str
    morphometric_params: Dict[str, ParameterModel]
    technological_params: Dict[str, ParameterModel]
    optional_features: Dict[str, bool] = {}
    confidence_threshold: float = 0.75
    created_date: str
    created_by: str
    validated_samples: List[str] = []
    parameter_hash: str


class CreateClassRequest(BaseModel):
    """Request to create new taxonomic class."""

    class_name: str = Field(..., description="Name for the new class")
    reference_objects: List[Dict] = Field(..., description="Reference artifact features")
    parameter_weights: Optional[Dict[str, float]] = Field(None, description="Parameter weights")
    tolerance_factor: float = Field(0.15, description="Tolerance factor")


class ClassificationRequest(BaseModel):
    """Request to classify an artifact."""

    artifact_features: Dict = Field(..., description="Artifact features to classify")
    return_all_scores: bool = Field(False, description="Return scores for all classes")


class ClassificationResponse(BaseModel):
    """Classification result."""

    class_id: str
    class_name: str
    is_member: bool
    confidence: float
    diagnostic: Dict


class ModifyClassRequest(BaseModel):
    """Request to modify class parameters."""

    class_id: str = Field(..., description="ID of class to modify")
    parameter_changes: Dict[str, Dict] = Field(..., description="Parameter changes")
    justification: str = Field(..., description="Archaeological justification")
    operator: str = Field(..., description="Who is making the change")


class DiscoverClassesRequest(BaseModel):
    """Request to discover new classes."""

    unclassified_objects: List[Dict] = Field(..., description="Unclassified artifacts")
    min_cluster_size: int = Field(5, description="Minimum cluster size")
    eps: float = Field(0.3, description="DBSCAN epsilon parameter")
