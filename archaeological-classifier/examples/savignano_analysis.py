#!/usr/bin/env python3
"""
Savignano Bronze Axes Analysis
==============================

Complete workflow for analyzing the Savignano hoard of 96 bronze axes.

This example demonstrates:
1. Batch processing of 3D mesh files
2. Morphometric analysis (PCA, clustering)
3. Formal taxonomy creation
4. Classification of artifacts
5. Answering archaeological questions
"""

from pathlib import Path
from acs import (MeshProcessor, MorphometricAnalyzer, FormalTaxonomySystem)
import json


def main():
    """Run complete Savignano analysis."""

    print("=" * 80)
    print("SAVIGNANO BRONZE AXES ANALYSIS")
    print("=" * 80)
    print()

    # ========================================================================
    # STEP 1: Load and Process 3D Meshes
    # ========================================================================

    print("STEP 1: Processing 3D Meshes")
    print("-" * 80)

    processor = MeshProcessor()

    # Simulated mesh files (replace with actual paths)
    # mesh_directory = Path("./savignano_meshes")
    # mesh_files = list(mesh_directory.glob("*.obj"))

    # For demonstration, using simulated data
    print("Note: Using simulated data for demonstration")
    print("In real analysis, replace with actual OBJ file paths")
    print()

    # Simulated features for 96 axes
    all_features = []
    for i in range(1, 97):
        # Simulated variation around base values
        import random
        base_volume = 145 + random.gauss(0, 8)
        base_length = 120 + random.gauss(0, 5)
        base_width = 65 + random.gauss(0, 3)
        base_thickness = 12 + random.gauss(0, 1)

        # Simulated socket features
        has_socket = random.random() > 0.2  # 80% have socket
        socket_depth = random.gauss(15, 2) if has_socket else 0
        socket_diameter = random.gauss(8, 0.5) if has_socket else 0

        # Simulated wear
        edge_angle = random.gauss(35, 3)
        hammering_index = random.uniform(0.3, 0.9)

        features = {
            'id': f'AXE_{i:03d}',
            'volume': base_volume,
            'surface_area': base_volume * 58,  # Rough approximation
            'length': base_length,
            'width': base_width,
            'thickness': base_thickness,
            'convexity': random.uniform(0.82, 0.92),
            'socket_depth': socket_depth,
            'socket_diameter': socket_diameter,
            'edge_angle': edge_angle,
            'hammering_index': hammering_index,
            'has_socket': has_socket,
            'has_midrib': random.random() > 0.6,
            'hammered': hammering_index > 0.5
        }

        all_features.append(features)

    print(f"✓ Loaded {len(all_features)} artifacts")
    print()

    # ========================================================================
    # STEP 2: Morphometric Analysis
    # ========================================================================

    print("STEP 2: Morphometric Analysis")
    print("-" * 80)

    analyzer = MorphometricAnalyzer()

    # Add all features
    for features in all_features:
        analyzer.add_features(features['id'], features)

    # PCA Analysis
    print("Running PCA...")
    pca_results = analyzer.fit_pca(explained_variance=0.95)
    print(f"  Components needed: {pca_results['n_components']}")
    print(f"  Variance explained: {pca_results['cumulative_variance'][-1]:.2%}")
    print()

    # Hierarchical Clustering to identify potential casting matrices
    print("Clustering to identify casting matrices...")
    clustering = analyzer.hierarchical_clustering(
        n_clusters=None,
        distance_threshold=0.5,
        method='ward'
    )

    print(f"  Identified {clustering['n_clusters']} potential matrices")
    for cluster_id, artifact_ids in clustering['clusters'].items():
        print(f"    Matrix {cluster_id}: {len(artifact_ids)} axes")
    print()

    # ========================================================================
    # STEP 3: Define Formal Taxonomic Classes
    # ========================================================================

    print("STEP 3: Defining Formal Taxonomic Classes")
    print("-" * 80)

    taxonomy = FormalTaxonomySystem()

    # Define class for each cluster (matrix)
    for cluster_id, artifact_ids in clustering['clusters'].items():
        cluster_features = [f for f in all_features if f['id'] in artifact_ids]

        if len(cluster_features) >= 3:  # Minimum for reliable class
            tax_class = taxonomy.define_class_from_reference_group(
                class_name=f"Matrix_{cluster_id}",
                reference_objects=cluster_features,
                parameter_weights={
                    'length': 1.5,      # More diagnostic
                    'width': 1.3,
                    'volume': 1.0,
                    'socket_depth': 2.0,  # Very diagnostic
                    'socket_diameter': 1.8
                },
                tolerance_factor=0.15
            )

            print(f"✓ Defined class: {tax_class.name}")
            print(f"    ID: {tax_class.class_id}")
            print(f"    Specimens: {len(tax_class.validated_samples)}")
            print(f"    Parameters: {len(tax_class.morphometric_params) + len(tax_class.technological_params)}")
            print()

    # ========================================================================
    # STEP 4: Archaeological Questions
    # ========================================================================

    print("STEP 4: Answering Archaeological Questions")
    print("-" * 80)

    # Question 1: How many casting matrices?
    print("Q1: How many casting matrices were used?")
    print(f"    A: {clustering['n_clusters']} matrices identified")
    print()

    # Question 2: Castings per matrix
    print("Q2: How many castings per matrix?")
    for cluster_id, artifact_ids in clustering['clusters'].items():
        print(f"    Matrix {cluster_id}: {len(artifact_ids)} castings")
    print()

    # Question 3: Post-casting treatments
    print("Q3: Post-casting treatments (hammering)?")
    hammered_count = sum(1 for f in all_features if f['hammered'])
    print(f"    {hammered_count}/{len(all_features)} axes show hammering")
    avg_hammering = sum(f['hammering_index'] for f in all_features) / len(all_features)
    print(f"    Average hammering index: {avg_hammering:.2f}")
    print()

    # Question 4: Socket analysis
    print("Q4: Socket characteristics?")
    socket_count = sum(1 for f in all_features if f['has_socket'])
    print(f"    {socket_count}/{len(all_features)} axes have sockets")
    if socket_count > 0:
        avg_depth = sum(f['socket_depth'] for f in all_features if f['has_socket']) / socket_count
        avg_diameter = sum(f['socket_diameter'] for f in all_features if f['has_socket']) / socket_count
        print(f"    Average socket depth: {avg_depth:.2f} mm")
        print(f"    Average socket diameter: {avg_diameter:.2f} mm")
    print()

    # Question 5: Wear analysis
    print("Q5: Evidence of use (edge angle analysis)?")
    avg_edge_angle = sum(f['edge_angle'] for f in all_features) / len(all_features)
    print(f"    Average edge angle: {avg_edge_angle:.1f}°")
    print(f"    Range: {min(f['edge_angle'] for f in all_features):.1f}° - {max(f['edge_angle'] for f in all_features):.1f}°")
    print()

    # ========================================================================
    # STEP 5: Classification Examples
    # ========================================================================

    print("STEP 5: Classification Examples")
    print("-" * 80)

    # Take first 3 axes and classify them
    for test_axe in all_features[:3]:
        print(f"Classifying {test_axe['id']}...")

        result = taxonomy.classify_object(test_axe, return_all_scores=True)

        # Show top 3 matches
        for r in result[:3]:
            print(f"  {r['class_name']}")
            print(f"    Confidence: {r['confidence']:.2%}")
            print(f"    Member: {'✓' if r['is_member'] else '✗'}")

        print()

    # ========================================================================
    # STEP 6: Export Results
    # ========================================================================

    print("STEP 6: Exporting Results")
    print("-" * 80)

    # Export taxonomy
    taxonomy.export_taxonomy("savignano_taxonomy.json")
    print("✓ Taxonomy exported to savignano_taxonomy.json")

    # Export features
    with open("savignano_features.json", 'w') as f:
        json.dump(all_features, f, indent=2)
    print("✓ Features exported to savignano_features.json")

    # Export statistics
    stats = taxonomy.get_statistics()
    with open("savignano_statistics.json", 'w') as f:
        json.dump(stats, f, indent=2)
    print("✓ Statistics exported to savignano_statistics.json")

    print()

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total artifacts analyzed: {len(all_features)}")
    print(f"Casting matrices identified: {clustering['n_clusters']}")
    print(f"Taxonomic classes defined: {len(taxonomy.classes)}")
    print(f"Axes with sockets: {socket_count} ({socket_count/len(all_features)*100:.1f}%)")
    print(f"Axes showing hammering: {hammered_count} ({hammered_count/len(all_features)*100:.1f}%)")
    print()
    print("Archaeological interpretation:")
    print("  - Multiple casting matrices used (production workshop)")
    print("  - Socket feature suggests hafting method to prevent rotation")
    print("  - Hammering indicates post-casting work hardening")
    print("  - Edge wear patterns suggest varied intensity of use")
    print()
    print("All results exported for publication and reproducibility.")
    print("=" * 80)


if __name__ == "__main__":
    main()
