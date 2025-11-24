"""
Command Line Interface for Archaeological Classifier System
==========================================================

CLI tool for mesh processing, analysis, and classification.
"""

import click
import json
from pathlib import Path
from acs.core.mesh_processor import MeshProcessor
from acs.core.morphometric import MorphometricAnalyzer
from acs.core.taxonomy import FormalTaxonomySystem
from acs.api.app import run_server


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Archaeological Classifier System CLI"""
    pass


@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--id', 'artifact_id', help='Artifact ID')
@click.option('--output', '-o', help='Output JSON file')
def process(filepath, artifact_id, output):
    """Process a single mesh file and extract features."""
    processor = MeshProcessor()

    try:
        features = processor.load_mesh(filepath, artifact_id)

        click.echo(f"✓ Processed: {features['id']}")
        click.echo(json.dumps(features, indent=2))

        if output:
            with open(output, 'w') as f:
                json.dump(features, f, indent=2)
            click.echo(f"✓ Saved to: {output}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', default='*.obj', help='File pattern (default: *.obj)')
@click.option('--output', '-o', help='Output JSON file')
def batch(directory, pattern, output):
    """Batch process all meshes in a directory."""
    processor = MeshProcessor()

    # Find files
    path = Path(directory)
    files = list(path.glob(pattern))

    if not files:
        click.echo(f"No files found matching {pattern} in {directory}")
        return

    click.echo(f"Found {len(files)} files")

    results = processor.batch_process([str(f) for f in files])

    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'error')

    click.echo(f"✓ Successful: {successful}")
    click.echo(f"✗ Failed: {failed}")

    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        click.echo(f"✓ Saved to: {output}")


@cli.command()
@click.argument('class_name')
@click.argument('reference_file', type=click.Path(exists=True))
@click.option('--tolerance', default=0.15, help='Tolerance factor')
@click.option('--output', '-o', help='Output JSON file')
def define_class(class_name, reference_file, tolerance, output):
    """Define a new taxonomic class from reference artifacts."""
    taxonomy = FormalTaxonomySystem()

    # Load reference objects
    with open(reference_file, 'r') as f:
        reference_objects = json.load(f)

    try:
        new_class = taxonomy.define_class_from_reference_group(
            class_name=class_name,
            reference_objects=reference_objects,
            tolerance_factor=tolerance
        )

        click.echo(f"✓ Class created: {new_class.class_id}")
        click.echo(f"  Name: {new_class.name}")
        click.echo(f"  Parameters: {len(new_class.morphometric_params) + len(new_class.technological_params)}")
        click.echo(f"  Hash: {new_class.parameter_hash}")

        if output:
            with open(output, 'w') as f:
                json.dump(new_class.to_dict(), f, indent=2)
            click.echo(f"✓ Saved to: {output}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('features_file', type=click.Path(exists=True))
@click.argument('taxonomy_file', type=click.Path(exists=True))
def classify(features_file, taxonomy_file):
    """Classify an artifact using a taxonomy."""
    taxonomy = FormalTaxonomySystem()

    # Load taxonomy
    taxonomy.import_taxonomy(taxonomy_file)

    # Load features
    with open(features_file, 'r') as f:
        features = json.load(f)

    try:
        result = taxonomy.classify_object(features, return_all_scores=True)

        click.echo(f"Classification results for: {features.get('id', 'unknown')}")
        click.echo()

        for r in result[:5]:  # Top 5
            click.echo(f"  {r['class_name']}")
            click.echo(f"    Confidence: {r['confidence']:.2%}")
            click.echo(f"    Member: {'✓' if r['is_member'] else '✗'}")
            click.echo()

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('taxonomy_file', type=click.Path(exists=True))
def list_classes(taxonomy_file):
    """List all classes in a taxonomy."""
    taxonomy = FormalTaxonomySystem()
    taxonomy.import_taxonomy(taxonomy_file)

    click.echo(f"Taxonomy classes ({len(taxonomy.classes)} total):")
    click.echo()

    for class_id, tax_class in taxonomy.classes.items():
        click.echo(f"  {tax_class.name} ({class_id})")
        click.echo(f"    Parameters: {len(tax_class.morphometric_params) + len(tax_class.technological_params)}")
        click.echo(f"    Threshold: {tax_class.confidence_threshold:.2%}")
        click.echo(f"    Samples: {len(tax_class.validated_samples)}")
        click.echo()


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host address')
@click.option('--port', default=5000, help='Port number')
@click.option('--debug/--no-debug', default=False, help='Debug mode')
def server(host, port, debug):
    """Start the Flask API server."""
    click.echo(f"Starting server on {host}:{port}")
    if debug:
        click.echo("Debug mode enabled")

    run_server(host=host, port=port, debug=debug)


if __name__ == '__main__':
    cli()
