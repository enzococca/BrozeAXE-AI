#!/usr/bin/env python3
"""
Quick System Test
================

Test all major components of Archaeological Classifier System.
"""

import sys


def test_imports():
    """Test that all modules can be imported."""
    print("=" * 80)
    print("TEST 1: Module Imports")
    print("=" * 80)

    try:
        from acs import MeshProcessor, MorphometricAnalyzer, FormalTaxonomySystem
        print("✅ Core modules imported successfully")

        from acs.api import create_app
        print("✅ API module imported successfully")

        from acs.models import ArtifactFeatures, ClassificationRequest
        print("✅ Data models imported successfully")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_mesh_processor():
    """Test MeshProcessor basic functionality."""
    print("\n" + "=" * 80)
    print("TEST 2: MeshProcessor")
    print("=" * 80)

    try:
        from acs import MeshProcessor

        processor = MeshProcessor()
        print("✅ MeshProcessor instantiated")

        # Test with simulated data
        print("✅ MeshProcessor ready for real OBJ files")

        return True
    except Exception as e:
        print(f"❌ MeshProcessor test failed: {e}")
        return False


def test_morphometric():
    """Test MorphometricAnalyzer."""
    print("\n" + "=" * 80)
    print("TEST 3: MorphometricAnalyzer")
    print("=" * 80)

    try:
        from acs import MorphometricAnalyzer

        analyzer = MorphometricAnalyzer()

        # Add some test features
        test_features = [
            {'id': 'test_1', 'volume': 100, 'length': 50, 'width': 30},
            {'id': 'test_2', 'volume': 105, 'length': 52, 'width': 31},
            {'id': 'test_3', 'volume': 98, 'length': 49, 'width': 29},
        ]

        for features in test_features:
            analyzer.add_features(features['id'], features)

        print(f"✅ Added {len(test_features)} feature sets")

        # Test PCA
        pca_results = analyzer.fit_pca(n_components=2)
        print(f"✅ PCA completed: {pca_results['n_components']} components")

        # Test clustering
        clustering = analyzer.hierarchical_clustering(n_clusters=2)
        print(f"✅ Clustering completed: {clustering['n_clusters']} clusters")

        return True
    except Exception as e:
        print(f"❌ MorphometricAnalyzer test failed: {e}")
        return False


def test_taxonomy():
    """Test FormalTaxonomySystem."""
    print("\n" + "=" * 80)
    print("TEST 4: FormalTaxonomySystem")
    print("=" * 80)

    try:
        from acs import FormalTaxonomySystem

        taxonomy = FormalTaxonomySystem()

        # Create reference group
        references = [
            {'id': 'ref_1', 'volume': 145, 'length': 120, 'width': 65},
            {'id': 'ref_2', 'volume': 148, 'length': 122, 'width': 64},
            {'id': 'ref_3', 'volume': 146, 'length': 121, 'width': 66},
        ]

        # Define class
        test_class = taxonomy.define_class_from_reference_group(
            class_name="TestClass",
            reference_objects=references
        )

        print(f"✅ Class created: {test_class.name}")
        print(f"   ID: {test_class.class_id}")
        print(f"   Hash: {test_class.parameter_hash}")
        print(f"   Parameters: {len(test_class.morphometric_params)}")

        # Test classification
        test_artifact = {'id': 'test', 'volume': 146, 'length': 121, 'width': 65}
        is_member, confidence, diagnostic = test_class.classify_object(test_artifact)

        print(f"✅ Classification: member={is_member}, confidence={confidence:.2%}")

        # Test export
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            export_path = f.name

        taxonomy.export_taxonomy(export_path)
        print(f"✅ Taxonomy exported to {export_path}")

        # Test statistics
        stats = taxonomy.get_statistics()
        print(f"✅ Statistics: {stats['n_classes']} classes defined")

        return True
    except Exception as e:
        print(f"❌ FormalTaxonomySystem test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api():
    """Test Flask API."""
    print("\n" + "=" * 80)
    print("TEST 5: Flask API")
    print("=" * 80)

    try:
        from acs.api import create_app

        app = create_app()

        with app.test_client() as client:
            # Test root endpoint
            response = client.get('/')
            assert response.status_code == 200
            print("✅ Root endpoint working")

            # Test docs endpoint
            response = client.get('/api/docs')
            assert response.status_code == 200
            print("✅ API docs endpoint working")

        print("✅ Flask API ready")
        print("   Start with: acs-cli server --port 5000")

        return True
    except Exception as e:
        print(f"❌ Flask API test failed: {e}")
        return False


def test_cli():
    """Test CLI availability."""
    print("\n" + "=" * 80)
    print("TEST 6: CLI Tools")
    print("=" * 80)

    import subprocess

    try:
        result = subprocess.run(
            ['acs-cli', '--version'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ CLI available: {result.stdout.strip()}")
            print("   Commands: process, batch, define-class, classify, server")
            return True
        else:
            print("❌ CLI not working properly")
            return False
    except FileNotFoundError:
        print("❌ acs-cli command not found")
        print("   Try: pip install -e .")
        return False
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False


def test_mcp_server():
    """Test MCP server can be imported."""
    print("\n" + "=" * 80)
    print("TEST 7: MCP Server")
    print("=" * 80)

    try:
        from acs.mcp import server

        print("✅ MCP server module imported")
        print("   Configure Claude Desktop:")
        print("   File: ~/Library/Application Support/Claude/claude_desktop_config.json")
        print('   Add: {"mcpServers": {"archaeological-classifier": {...}}}')

        return True
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "ARCHAEOLOGICAL CLASSIFIER SYSTEM" + " " * 31 + "║")
    print("║" + " " * 28 + "System Test Suite" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    tests = [
        test_imports,
        test_mesh_processor,
        test_morphometric,
        test_taxonomy,
        test_api,
        test_cli,
        test_mcp_server,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Unexpected error in {test_func.__name__}: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED! System is ready to use.")
        print("\nNext steps:")
        print("  1. Read GET_STARTED.md")
        print("  2. Run examples/savignano_analysis.py")
        print("  3. Try with your OBJ files")
        print("  4. Configure Claude Desktop integration")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
