"""Tests for taxonomy system."""

import pytest
from acs.core.taxonomy import FormalTaxonomySystem, ClassificationParameter, TaxonomicClass


def test_create_parameter():
    """Test parameter creation."""
    param = ClassificationParameter(
        name="length",
        value=120.0,
        min_threshold=110.0,
        max_threshold=130.0,
        weight=1.5,
        tolerance=5.0
    )

    assert param.name == "length"
    assert param.validate(115.0)
    assert param.validate(125.0)
    assert not param.validate(105.0)
    assert not param.validate(135.0)


def test_define_class():
    """Test class definition from reference group."""
    taxonomy = FormalTaxonomySystem()

    references = [
        {"id": "AXE_1", "volume": 145, "length": 120, "width": 65},
        {"id": "AXE_2", "volume": 148, "length": 122, "width": 64},
        {"id": "AXE_3", "volume": 146, "length": 121, "width": 66},
    ]

    tax_class = taxonomy.define_class_from_reference_group(
        class_name="TestClass",
        reference_objects=references
    )

    assert tax_class.name == "TestClass"
    assert len(tax_class.validated_samples) == 3
    assert "volume" in tax_class.morphometric_params
    assert len(tax_class.parameter_hash) == 16


def test_classify_object():
    """Test object classification."""
    taxonomy = FormalTaxonomySystem()

    references = [
        {"id": "AXE_1", "volume": 145, "length": 120, "width": 65},
        {"id": "AXE_2", "volume": 148, "length": 122, "width": 64},
    ]

    tax_class = taxonomy.define_class_from_reference_group(
        class_name="TestClass",
        reference_objects=references
    )

    # Should classify similar object as member
    test_object = {"id": "TEST", "volume": 146, "length": 121, "width": 65}
    is_member, confidence, diagnostic = tax_class.classify_object(test_object)

    assert is_member
    assert confidence > 0.7
    assert "volume" in diagnostic


def test_modify_class():
    """Test class modification with versioning."""
    taxonomy = FormalTaxonomySystem()

    references = [
        {"id": "AXE_1", "volume": 145, "length": 120, "width": 65},
        {"id": "AXE_2", "volume": 148, "length": 122, "width": 64},
    ]

    original_class = taxonomy.define_class_from_reference_group(
        class_name="TestClass",
        reference_objects=references
    )

    original_id = original_class.class_id
    original_hash = original_class.parameter_hash

    # Modify class
    new_class = taxonomy.modify_class_parameters(
        class_id=original_id,
        parameter_changes={
            "morphometric": {
                "length": {"max_threshold": 135.0}
            }
        },
        justification="Test modification",
        operator="Test User"
    )

    # Verify new version created
    assert new_class.class_id != original_id
    assert new_class.parameter_hash != original_hash
    assert "_v" in new_class.class_id

    # Original still exists
    assert original_id in taxonomy.classes


def test_export_import():
    """Test taxonomy export and import."""
    import tempfile
    import os

    taxonomy = FormalTaxonomySystem()

    references = [
        {"id": "AXE_1", "volume": 145, "length": 120, "width": 65},
        {"id": "AXE_2", "volume": 148, "length": 122, "width": 64},
    ]

    taxonomy.define_class_from_reference_group(
        class_name="TestClass",
        reference_objects=references
    )

    # Export
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        filepath = f.name

    try:
        taxonomy.export_taxonomy(filepath)

        # Import into new taxonomy
        new_taxonomy = FormalTaxonomySystem()
        new_taxonomy.import_taxonomy(filepath)

        assert len(new_taxonomy.classes) == len(taxonomy.classes)
        assert list(new_taxonomy.classes.keys()) == list(taxonomy.classes.keys())

    finally:
        os.unlink(filepath)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
