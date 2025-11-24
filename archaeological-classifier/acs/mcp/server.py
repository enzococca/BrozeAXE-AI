#!/usr/bin/env python3
"""
ACS MCP Server
==============

Model Context Protocol server for Archaeological Classifier System.
Provides advanced AI and ML tools for Claude Desktop.
"""

import asyncio
import json
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from acs.core.mesh_processor import MeshProcessor
from acs.core.morphometric import MorphometricAnalyzer
from acs.core.taxonomy import FormalTaxonomySystem
from acs.core.database import get_database
from acs.core.ai_assistant import get_ai_assistant
from acs.core.ml_classifier import get_ml_classifier
from acs.core.stylistic_analyzer import get_stylistic_analyzer
from acs.core.similarity_search import get_similarity_engine
from acs.core.technical_drawing import get_technical_drawing_generator


# Initialize components
mesh_processor = MeshProcessor()
morphometric = MorphometricAnalyzer()
taxonomy = FormalTaxonomySystem()
db = get_database()
ai_assistant = get_ai_assistant()
ml_classifier = get_ml_classifier()
stylistic = get_stylistic_analyzer()
similarity_engine = get_similarity_engine()
technical_drawer = get_technical_drawing_generator()

# Create server
server = Server("acs-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available tools."""
    return [
        types.Tool(
            name="ai_classify_artifact",
            description="Use AI (Claude 4.5) to analyze and suggest classification for an artifact",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "Artifact identifier"
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional archaeological context"
                    }
                },
                "required": ["artifact_id"]
            }
        ),
        types.Tool(
            name="ai_compare_artifacts",
            description="Get AI-powered comparative analysis of two artifacts",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact1_id": {"type": "string"},
                    "artifact2_id": {"type": "string"}
                },
                "required": ["artifact1_id", "artifact2_id"]
            }
        ),
        types.Tool(
            name="stylistic_analyze",
            description="Analyze stylistic characteristics of an artifact (symmetry, proportions, surface quality, curvature)",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "Artifact identifier"
                    }
                },
                "required": ["artifact_id"]
            }
        ),
        types.Tool(
            name="find_similar_artifacts",
            description="Find N most similar artifacts using morphometric and stylistic features (batch 1:many comparison)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_id": {
                        "type": "string",
                        "description": "Query artifact identifier"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)"
                    },
                    "metric": {
                        "type": "string",
                        "description": "Similarity metric: 'cosine' or 'euclidean' (default: 'cosine')"
                    },
                    "min_similarity": {
                        "type": "number",
                        "description": "Minimum similarity threshold 0-1 (default: 0.0)"
                    }
                },
                "required": ["query_id"]
            }
        ),
        types.Tool(
            name="batch_compare_artifacts",
            description="Compare one artifact against multiple specific targets (1:many comparison with specific targets)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_id": {
                        "type": "string",
                        "description": "Query artifact identifier"
                    },
                    "target_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of target artifact identifiers"
                    }
                },
                "required": ["query_id", "target_ids"]
            }
        ),
        types.Tool(
            name="generate_technical_drawing",
            description="Generate professional archaeological technical drawings for Bronze Age axes (longitudinal profile, cross-sections, front/back views)",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact_id": {
                        "type": "string",
                        "description": "Artifact identifier"
                    },
                    "view_type": {
                        "type": "string",
                        "description": "View type: 'complete_sheet', 'longitudinal_profile', 'cross_section_max', 'cross_section_min', 'front_view', 'back_view'. Default: 'complete_sheet'"
                    }
                },
                "required": ["artifact_id"]
            }
        ),
        types.Tool(
            name="create_project",
            description="Create a new project for organizing artifacts",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Unique project identifier"},
                    "name": {"type": "string", "description": "Project name"},
                    "description": {"type": "string", "description": "Project description"}
                },
                "required": ["project_id", "name"]
            }
        ),
        types.Tool(
            name="list_projects",
            description="List all projects with statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Optional filter by status: 'active', 'archived', 'merged'"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_project",
            description="Get detailed project information with artifacts",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"}
                },
                "required": ["project_id"]
            }
        ),
        types.Tool(
            name="assign_artifact_to_project",
            description="Move an artifact to a different project",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact_id": {"type": "string"},
                    "project_id": {"type": "string"}
                },
                "required": ["artifact_id", "project_id"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle tool execution."""
    try:
        if name == "ai_classify_artifact":
            artifact_id = arguments["artifact_id"]
            context = arguments.get("context")
            features = db.get_features(artifact_id)

            if not features:
                return [types.TextContent(
                    type="text",
                    text=f"Error: No features found for artifact {artifact_id}"
                )]

            classes = [{'name': c.name, 'description': c.description} for c in taxonomy.classes.values()]
            result = ai_assistant.analyze_artifact(artifact_id, features, classes, context)

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "ai_compare_artifacts":
            art1 = arguments["artifact1_id"]
            art2 = arguments["artifact2_id"]
            feat1 = db.get_features(art1)
            feat2 = db.get_features(art2)

            if not feat1 or not feat2:
                return [types.TextContent(type="text", text="Error: Missing features")]

            from acs.core.mesh_processor import MeshProcessor
            processor = MeshProcessor()
            sim = processor.compute_similarity(feat1, feat2)
            result = ai_assistant.compare_artifacts(art1, feat1, art2, feat2, sim)

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "stylistic_analyze":
            artifact_id = arguments["artifact_id"]

            # Get artifact from database or loaded meshes
            if artifact_id not in mesh_processor.meshes:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Artifact {artifact_id} not found in loaded meshes"
                )]

            mesh = mesh_processor.meshes[artifact_id]
            morph_features = mesh_processor._extract_features(mesh, artifact_id)

            # Analyze stylistic features
            style_features = stylistic.analyze_style(mesh, artifact_id, morph_features)

            result = {
                "artifact_id": artifact_id,
                "stylistic_features": style_features,
                "summary": {
                    "symmetry": style_features.get('symmetry', {}).get('overall_symmetry', 0),
                    "surface_quality": style_features.get('surface_quality', {}).get('overall_quality', 0),
                    "shape_category": style_features.get('proportions', {}).get('shape_category', 'unknown')
                }
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "find_similar_artifacts":
            query_id = arguments["query_id"]
            n_results = arguments.get("n_results", 10)
            metric = arguments.get("metric", "cosine")
            min_similarity = arguments.get("min_similarity", 0.0)

            if query_id not in mesh_processor.meshes:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Query artifact {query_id} not found"
                )]

            # Build similarity index
            for artifact_id, mesh in mesh_processor.meshes.items():
                morph_features = mesh_processor._extract_features(mesh, artifact_id)
                style_features = stylistic.analyze_style(mesh, artifact_id, morph_features)
                similarity_engine.add_artifact_features(artifact_id, morph_features, style_features)

            similarity_engine.build_index()

            # Find similar artifacts
            similar_artifacts = similarity_engine.find_similar(
                query_id,
                n_results=n_results,
                metric=metric,
                min_similarity=min_similarity
            )

            result = {
                "query_id": query_id,
                "n_results": len(similar_artifacts),
                "metric": metric,
                "similar_artifacts": [
                    {"artifact_id": aid, "similarity_score": float(score)}
                    for aid, score in similar_artifacts
                ]
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "batch_compare_artifacts":
            query_id = arguments["query_id"]
            target_ids = arguments["target_ids"]

            if query_id not in mesh_processor.meshes:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Query artifact {query_id} not found"
                )]

            # Check all targets exist
            missing = [tid for tid in target_ids if tid not in mesh_processor.meshes]
            if missing:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Target artifacts not found: {', '.join(missing)}"
                )]

            # Build index with query and targets
            for artifact_id in [query_id] + target_ids:
                mesh = mesh_processor.meshes[artifact_id]
                morph_features = mesh_processor._extract_features(mesh, artifact_id)
                style_features = stylistic.analyze_style(mesh, artifact_id, morph_features)
                similarity_engine.add_artifact_features(artifact_id, morph_features, style_features)

            similarity_engine.build_index()

            # Batch compare
            results = similarity_engine.batch_compare(query_id, target_ids)

            result = {
                "query_id": query_id,
                "n_targets": len(target_ids),
                "comparisons": [
                    {"artifact_id": aid, "similarity_score": float(score)}
                    for aid, score in results
                ]
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "generate_technical_drawing":
            artifact_id = arguments["artifact_id"]
            view_type = arguments.get("view_type", "complete_sheet")

            if artifact_id not in mesh_processor.meshes:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Artifact {artifact_id} not found"
                )]

            mesh = mesh_processor.meshes[artifact_id]
            morph_features = mesh_processor._extract_features(mesh, artifact_id)

            # Generate technical drawings
            views = technical_drawer.generate_complete_drawing(mesh, artifact_id, morph_features)

            if view_type not in views:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Invalid view type '{view_type}'. "
                         f"Valid types: {', '.join(views.keys())}"
                )]

            # Convert image bytes to base64 for return
            import base64
            img_b64 = base64.b64encode(views[view_type]).decode('utf-8')

            result = {
                "artifact_id": artifact_id,
                "view_type": view_type,
                "image_base64": img_b64,
                "format": "png",
                "message": "Technical drawing generated successfully"
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "create_project":
            project_id = arguments["project_id"]
            name = arguments["name"]
            description = arguments.get("description", "")

            db.create_project(project_id, name, description)

            result = {
                "status": "success",
                "project_id": project_id,
                "name": name,
                "message": f"Project '{name}' created successfully"
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_projects":
            status_filter = arguments.get("status")
            projects = db.list_projects(status=status_filter)

            # Add statistics for each project
            for project in projects:
                stats = db.get_project_statistics(project['project_id'])
                project['stats'] = stats

            result = {
                "status": "success",
                "n_projects": len(projects),
                "projects": projects
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_project":
            project_id = arguments["project_id"]
            project = db.get_project(project_id)

            if not project:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Project '{project_id}' not found"
                )]

            artifacts = db.get_project_artifacts(project_id)
            stats = db.get_project_statistics(project_id)

            result = {
                "status": "success",
                "project": project,
                "artifacts": artifacts,
                "stats": stats
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "assign_artifact_to_project":
            artifact_id = arguments["artifact_id"]
            project_id = arguments["project_id"]

            db.assign_artifact_to_project(artifact_id, project_id)

            result = {
                "status": "success",
                "artifact_id": artifact_id,
                "project_id": project_id,
                "message": f"Artifact '{artifact_id}' assigned to project '{project_id}'"
            }

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="acs",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
