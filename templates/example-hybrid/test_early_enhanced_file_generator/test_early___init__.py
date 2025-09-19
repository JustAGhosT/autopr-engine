"""
Unit tests for TemplateMetadata.__init__ in enhanced_file_generator.py

Covers happy paths and edge cases for initialization from metadata dict.
"""

import pytest

from ..enhanced_file_generator import TemplateMetadata


@pytest.mark.usefixtures("metadata_dict")
class TestTemplateMetadataInit:
    # --- Happy Path Tests ---

    @pytest.mark.happy_path
    def test_full_metadata_initialization(self):
        """
        Test that all fields are correctly set when metadata dict contains all expected keys.
        """
        metadata = {
            "name": "Test Template",
            "description": "A test template.",
            "category": "test",
            "platforms": ["linux", "windows"],
            "file_extension": ".txt",
            "variables": {"foo": "bar"},
            "variants": {"v1": "desc"},
            "usage": ["step1", "step2"],
            "dependencies": {"dep1": "1.0"},
            "notes": ["note1", "note2"],
            "examples": {"ex1": "example usage"},
        }
        tm = TemplateMetadata(metadata)
        assert tm.name == "Test Template"
        assert tm.description == "A test template."
        assert tm.category == "test"
        assert tm.platforms == ["linux", "windows"]
        assert tm.file_extension == ".txt"
        assert tm.variables == {"foo": "bar"}
        assert tm.variants == {"v1": "desc"}
        assert tm.usage == ["step1", "step2"]
        assert tm.dependencies == {"dep1": "1.0"}
        assert tm.notes == ["note1", "note2"]
        assert tm.examples == {"ex1": "example usage"}

    @pytest.mark.happy_path
    def test_minimal_metadata_initialization(self):
        """
        Test that all fields are set to their default values when metadata dict is empty.
        """
        metadata = {}
        tm = TemplateMetadata(metadata)
        assert tm.name == ""
        assert tm.description == ""
        assert tm.category == ""
        assert tm.platforms == []
        assert tm.file_extension == ""
        assert tm.variables == {}
        assert tm.variants == {}
        assert tm.usage == []
        assert tm.dependencies == {}
        assert tm.notes == []
        assert tm.examples == {}

    @pytest.mark.happy_path
    def test_partial_metadata_initialization(self):
        """
        Test that only provided fields are set, others use defaults.
        """
        metadata = {"name": "Partial", "platforms": ["mac"], "usage": ["do this"]}
        tm = TemplateMetadata(metadata)
        assert tm.name == "Partial"
        assert tm.description == ""
        assert tm.category == ""
        assert tm.platforms == ["mac"]
        assert tm.file_extension == ""
        assert tm.variables == {}
        assert tm.variants == {}
        assert tm.usage == ["do this"]
        assert tm.dependencies == {}
        assert tm.notes == []
        assert tm.examples == {}

    # --- Edge Case Tests ---

    @pytest.mark.edge_case
    def test_metadata_with_none_values(self):
        """
        Test that None values in metadata dict are used as-is (not replaced by defaults).
        """
        metadata = {
            "name": None,
            "description": None,
            "category": None,
            "platforms": None,
            "file_extension": None,
            "variables": None,
            "variants": None,
            "usage": None,
            "dependencies": None,
            "notes": None,
            "examples": None,
        }
        tm = TemplateMetadata(metadata)
        assert tm.name is None
        assert tm.description is None
        assert tm.category is None
        assert tm.platforms is None
        assert tm.file_extension is None
        assert tm.variables is None
        assert tm.variants is None
        assert tm.usage is None
        assert tm.dependencies is None
        assert tm.notes is None
        assert tm.examples is None

    @pytest.mark.edge_case
    def test_metadata_with_unexpected_extra_keys(self):
        """
        Test that extra keys in metadata dict are ignored and do not cause errors.
        """
        metadata = {"name": "Extra", "foo": "bar", "description": "desc", "random": 123}
        tm = TemplateMetadata(metadata)
        assert tm.name == "Extra"
        assert tm.description == "desc"
        assert tm.category == ""
        assert tm.platforms == []
        assert tm.file_extension == ""
        assert tm.variables == {}
        assert tm.variants == {}
        assert tm.usage == []
        assert tm.dependencies == {}
        assert tm.notes == []
        assert tm.examples == {}

    @pytest.mark.edge_case
    def test_metadata_with_wrong_types(self):
        """
        Test that wrong types in metadata dict are assigned as-is (no type enforcement).
        """
        metadata = {
            "name": 123,
            "description": ["not", "a", "string"],
            "category": 5.5,
            "platforms": "notalist",
            "file_extension": 42,
            "variables": "notadict",
            "variants": 0,
            "usage": "notalist",
            "dependencies": "notadict",
            "notes": "notalist",
            "examples": 999,
        }
        tm = TemplateMetadata(metadata)
        assert tm.name == 123
        assert tm.description == ["not", "a", "string"]
        assert tm.category == 5.5
        assert tm.platforms == "notalist"
        assert tm.file_extension == 42
        assert tm.variables == "notadict"
        assert tm.variants == 0
        assert tm.usage == "notalist"
        assert tm.dependencies == "notadict"
        assert tm.notes == "notalist"
        assert tm.examples == 999

    @pytest.mark.edge_case
    def test_metadata_with_empty_strings_and_collections(self):
        """
        Test that empty strings, lists, and dicts are preserved.
        """
        metadata = {
            "name": "",
            "description": "",
            "category": "",
            "platforms": [],
            "file_extension": "",
            "variables": {},
            "variants": {},
            "usage": [],
            "dependencies": {},
            "notes": [],
            "examples": {},
        }
        tm = TemplateMetadata(metadata)
        assert tm.name == ""
        assert tm.description == ""
        assert tm.category == ""
        assert tm.platforms == []
        assert tm.file_extension == ""
        assert tm.variables == {}
        assert tm.variants == {}
        assert tm.usage == []
        assert tm.dependencies == {}
        assert tm.notes == []
        assert tm.examples == {}

    @pytest.mark.edge_case
    def test_metadata_with_missing_dict(self):
        """
        Test that passing a non-dict (e.g., None) raises AttributeError.
        """
        with pytest.raises(AttributeError):
            TemplateMetadata(None)
        with pytest.raises(AttributeError):
            TemplateMetadata("notadict")
        with pytest.raises(AttributeError):
            TemplateMetadata(123)
            TemplateMetadata(123)
