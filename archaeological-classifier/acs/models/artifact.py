"""Artifact data models."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ArtifactFeatures(BaseModel):
    """Features extracted from 3D mesh."""

    id: str = Field(..., description="Artifact identifier")
    volume: float = Field(..., description="Volume in cubic mm")
    surface_area: float = Field(..., description="Surface area in square mm")
    length: float = Field(..., description="Maximum length in mm")
    width: float = Field(..., description="Maximum width in mm")
    thickness: float = Field(..., description="Minimum thickness in mm")
    convexity: Optional[float] = Field(None, description="Convexity ratio")

    # Optional technological features
    socket_depth: Optional[float] = Field(None, description="Socket depth in mm")
    socket_diameter: Optional[float] = Field(None, description="Socket diameter in mm")
    edge_angle: Optional[float] = Field(None, description="Edge angle in degrees")
    hammering_index: Optional[float] = Field(None, description="Hammering intensity index")

    # Optional boolean features
    has_socket: Optional[bool] = Field(None, description="Presence of socket")
    has_midrib: Optional[bool] = Field(None, description="Presence of midrib")
    hammered: Optional[bool] = Field(None, description="Evidence of hammering")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "AXE_001",
                "volume": 145.3,
                "surface_area": 8523.4,
                "length": 120.5,
                "width": 65.2,
                "thickness": 12.3,
                "convexity": 0.87,
                "socket_depth": 15.3,
                "socket_diameter": 8.2,
                "edge_angle": 35.5,
                "hammering_index": 0.65,
                "has_socket": True,
                "has_midrib": False,
                "hammered": True
            }
        }


class MeshUploadResponse(BaseModel):
    """Response from mesh upload and processing."""

    status: str = Field(..., description="Processing status")
    artifact_id: str = Field(..., description="Assigned artifact ID")
    features: ArtifactFeatures = Field(..., description="Extracted features")
    processing_time: float = Field(..., description="Processing time in seconds")
    message: Optional[str] = Field(None, description="Optional message")


class BatchProcessRequest(BaseModel):
    """Request for batch mesh processing."""

    artifact_ids: List[str] = Field(..., description="List of artifact IDs to process")


class BatchProcessResponse(BaseModel):
    """Response from batch processing."""

    total: int = Field(..., description="Total artifacts processed")
    successful: int = Field(..., description="Successfully processed")
    failed: int = Field(..., description="Failed to process")
    results: List[Dict] = Field(..., description="Processing results")
