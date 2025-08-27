#!/usr/bin/env python3
"""
Comprehensive tests for file operations module.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
import yaml

# Import the modules we're testing
try:
    from autopr.actions.file_ops import (FileAnalyzer, FileBackup,
                                         FileOperations, FileProcessor,
                                         FileSynchronizer, FileTransformer,
                                         FileValidator)
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestFileOperations:
    """Test FileOperations class."""

    @pytest.fixture
    def file_ops(self):
        """Create a FileOperations instance for testing."""
        return FileOperations()

    def test_file_operations_initialization(self, file_ops):
        """Test FileOperations initialization."""
        assert file_ops.base_path is not None
        assert file_ops.backup_dir is not None
        assert file_ops.temp_dir is not None

    def test_create_directory(self, file_ops):
        """Test creating a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_dir")
            result = file_ops.create_directory(test_dir)
            
            assert result is True
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)

    def test_create_directory_already_exists(self, file_ops):
        """Test creating a directory that already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = file_ops.create_directory(temp_dir)
            
            # Should return True even if directory exists
            assert result is True

    def test_create_directory_with_parents(self, file_ops):
        """Test creating a directory with parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "parent", "child", "grandchild")
            result = file_ops.create_directory(nested_dir)
            
            assert result is True
            assert os.path.exists(nested_dir)

    def test_delete_file(self, file_ops):
        """Test deleting a file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            result = file_ops.delete_file(temp_file)
            assert result is True
            assert not os.path.exists(temp_file)
        except:
            # Clean up if test fails
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_delete_file_not_exists(self, file_ops):
        """Test deleting a file that doesn't exist."""
        non_existent_file = "/path/to/non/existent/file.txt"
        result = file_ops.delete_file(non_existent_file)
        
        # Should return False for non-existent files
        assert result is False

    def test_copy_file(self, file_ops):
        """Test copying a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            source_file = f.name
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            dest_file = f.name
            os.unlink(dest_file)  # Remove the temp file
        
        try:
            result = file_ops.copy_file(source_file, dest_file)
            assert result is True
            assert os.path.exists(dest_file)
            
            with open(dest_file, 'r') as f:
                content = f.read()
            assert content == "test content"
            
        finally:
            # Clean up
            if os.path.exists(source_file):
                os.unlink(source_file)
            if os.path.exists(dest_file):
                os.unlink(dest_file)

    def test_move_file(self, file_ops):
        """Test moving a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            source_file = f.name
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            dest_file = f.name
            os.unlink(dest_file)  # Remove the temp file
        
        try:
            result = file_ops.move_file(source_file, dest_file)
            assert result is True
            assert not os.path.exists(source_file)
            assert os.path.exists(dest_file)
            
            with open(dest_file, 'r') as f:
                content = f.read()
            assert content == "test content"
            
        finally:
            # Clean up
            if os.path.exists(source_file):
                os.unlink(source_file)
            if os.path.exists(dest_file):
                os.unlink(dest_file)

    def test_read_file(self, file_ops):
        """Test reading a file."""
        test_content = "test file content\nwith multiple lines"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            content = file_ops.read_file(temp_file)
            assert content == test_content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_file_binary(self, file_ops):
        """Test reading a file in binary mode."""
        test_content = b"binary test content"
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            content = file_ops.read_file(temp_file, binary=True)
            assert content == test_content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_write_file(self, file_ops):
        """Test writing to a file."""
        test_content = "test write content"
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
            os.unlink(temp_file)  # Remove the temp file
        
        try:
            result = file_ops.write_file(temp_file, test_content)
            assert result is True
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                content = f.read()
            assert content == test_content
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_write_file_binary(self, file_ops):
        """Test writing binary content to a file."""
        test_content = b"binary write content"
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
            os.unlink(temp_file)  # Remove the temp file
        
        try:
            result = file_ops.write_file(temp_file, test_content, binary=True)
            assert result is True
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'rb') as f:
                content = f.read()
            assert content == test_content
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_file_exists(self, file_ops):
        """Test checking if a file exists."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            assert file_ops.file_exists(temp_file) is True
            assert file_ops.file_exists("/non/existent/file.txt") is False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_get_file_size(self, file_ops):
        """Test getting file size."""
        test_content = "test content for size calculation"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            size = file_ops.get_file_size(temp_file)
            assert size == len(test_content)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_get_file_extension(self, file_ops):
        """Test getting file extension."""
        assert file_ops.get_file_extension("test.txt") == ".txt"
        assert file_ops.get_file_extension("test.py") == ".py"
        assert file_ops.get_file_extension("test") == ""
        assert file_ops.get_file_extension("test.file.txt") == ".txt"

    def test_get_file_name(self, file_ops):
        """Test getting file name without extension."""
        assert file_ops.get_file_name("test.txt") == "test"
        assert file_ops.get_file_name("path/to/file.py") == "file"
        assert file_ops.get_file_name("test") == "test"


class TestFileProcessor:
    """Test FileProcessor class."""

    @pytest.fixture
    def file_processor(self):
        """Create a FileProcessor instance for testing."""
        return FileProcessor()

    def test_file_processor_initialization(self, file_processor):
        """Test FileProcessor initialization."""
        assert file_processor.processors == {}
        assert file_processor.default_processor is None

    def test_register_processor(self, file_processor):
        """Test registering a file processor."""
        def test_processor(content):
            return content.upper()
        
        file_processor.register_processor("uppercase", test_processor)
        assert "uppercase" in file_processor.processors

    def test_process_file(self, file_processor):
        """Test processing a file."""
        def uppercase_processor(content):
            return content.upper()
        
        file_processor.register_processor("uppercase", uppercase_processor)
        
        test_content = "test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            result = file_processor.process_file(temp_file, "uppercase")
            assert result == "TEST CONTENT"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_process_file_with_default(self, file_processor):
        """Test processing a file with default processor."""
        def default_processor(content):
            return content.lower()
        
        file_processor.register_processor("default", default_processor)
        file_processor.set_default_processor("default")
        
        test_content = "TEST CONTENT"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            result = file_processor.process_file(temp_file)
            assert result == "test content"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_process_content(self, file_processor):
        """Test processing content directly."""
        def reverse_processor(content):
            return content[::-1]
        
        file_processor.register_processor("reverse", reverse_processor)
        
        test_content = "hello world"
        result = file_processor.process_content(test_content, "reverse")
        assert result == "dlrow olleh"

    def test_process_multiple_files(self, file_processor):
        """Test processing multiple files."""
        def uppercase_processor(content):
            return content.upper()
        
        file_processor.register_processor("uppercase", uppercase_processor)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = os.path.join(temp_dir, "file1.txt")
            file2 = os.path.join(temp_dir, "file2.txt")
            
            with open(file1, 'w') as f:
                f.write("hello")
            with open(file2, 'w') as f:
                f.write("world")
            
            results = file_processor.process_multiple_files(
                [file1, file2], "uppercase"
            )
            
            assert results[file1] == "HELLO"
            assert results[file2] == "WORLD"


class TestFileValidator:
    """Test FileValidator class."""

    @pytest.fixture
    def file_validator(self):
        """Create a FileValidator instance for testing."""
        return FileValidator()

    def test_file_validator_initialization(self, file_validator):
        """Test FileValidator initialization."""
        assert file_validator.validators == {}
        assert file_validator.rules == []

    def test_add_validator(self, file_validator):
        """Test adding a file validator."""
        def size_validator(file_path):
            return os.path.getsize(file_path) < 1000
        
        file_validator.add_validator("size", size_validator)
        assert "size" in file_validator.validators

    def test_add_rule(self, file_validator):
        """Test adding a validation rule."""
        def extension_rule(file_path):
            return file_path.endswith('.txt')
        
        file_validator.add_rule(extension_rule)
        assert len(file_validator.rules) == 1

    def test_validate_file(self, file_validator):
        """Test validating a file."""
        def size_validator(file_path):
            return os.path.getsize(file_path) < 1000
        
        file_validator.add_validator("size", size_validator)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("small content")
            temp_file = f.name
        
        try:
            result = file_validator.validate_file(temp_file, ["size"])
            assert result is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_validate_file_fails(self, file_validator):
        """Test file validation that fails."""
        def size_validator(file_path):
            return os.path.getsize(file_path) < 10  # Very small limit
        
        file_validator.add_validator("size", size_validator)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("this content is too large for the validator")
            temp_file = f.name
        
        try:
            result = file_validator.validate_file(temp_file, ["size"])
            assert result is False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_validate_file_with_rules(self, file_validator):
        """Test file validation with rules."""
        def txt_rule(file_path):
            return file_path.endswith('.txt')
        
        file_validator.add_rule(txt_rule)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            result = file_validator.validate_file(temp_file)
            assert result is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_validate_multiple_files(self, file_validator):
        """Test validating multiple files."""
        def size_validator(file_path):
            return os.path.getsize(file_path) < 100
        
        file_validator.add_validator("size", size_validator)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = os.path.join(temp_dir, "file1.txt")
            file2 = os.path.join(temp_dir, "file2.txt")
            
            with open(file1, 'w') as f:
                f.write("small")
            with open(file2, 'w') as f:
                f.write("this content is too large for the validator")
            
            results = file_validator.validate_multiple_files(
                [file1, file2], ["size"]
            )
            
            assert results[file1] is True
            assert results[file2] is False


class TestFileBackup:
    """Test FileBackup class."""

    @pytest.fixture
    def file_backup(self):
        """Create a FileBackup instance for testing."""
        return FileBackup()

    def test_file_backup_initialization(self, file_backup):
        """Test FileBackup initialization."""
        assert file_backup.backup_dir is not None
        assert file_backup.backup_format is not None

    def test_create_backup(self, file_backup):
        """Test creating a backup of a file."""
        test_content = "original content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            original_file = f.name
        
        try:
            backup_path = file_backup.create_backup(original_file)
            assert os.path.exists(backup_path)
            
            with open(backup_path, 'r') as f:
                backup_content = f.read()
            assert backup_content == test_content
            
            # Clean up backup
            if os.path.exists(backup_path):
                os.unlink(backup_path)
                
        finally:
            if os.path.exists(original_file):
                os.unlink(original_file)

    def test_restore_backup(self, file_backup):
        """Test restoring a file from backup."""
        original_content = "original content"
        modified_content = "modified content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(original_content)
            original_file = f.name
        
        try:
            # Create backup
            backup_path = file_backup.create_backup(original_file)
            
            # Modify original file
            with open(original_file, 'w') as f:
                f.write(modified_content)
            
            # Restore from backup
            result = file_backup.restore_backup(original_file, backup_path)
            assert result is True
            
            with open(original_file, 'r') as f:
                restored_content = f.read()
            assert restored_content == original_content
            
            # Clean up backup
            if os.path.exists(backup_path):
                os.unlink(backup_path)
                
        finally:
            if os.path.exists(original_file):
                os.unlink(original_file)

    def test_list_backups(self, file_backup):
        """Test listing available backups."""
        test_content = "test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            original_file = f.name
        
        try:
            # Create multiple backups
            backup1 = file_backup.create_backup(original_file)
            backup2 = file_backup.create_backup(original_file)
            
            backups = file_backup.list_backups(original_file)
            assert len(backups) >= 2
            
            # Clean up backups
            for backup in [backup1, backup2]:
                if os.path.exists(backup):
                    os.unlink(backup)
                    
        finally:
            if os.path.exists(original_file):
                os.unlink(original_file)

    def test_cleanup_old_backups(self, file_backup):
        """Test cleaning up old backups."""
        test_content = "test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            original_file = f.name
        
        try:
            # Create multiple backups
            backup1 = file_backup.create_backup(original_file)
            backup2 = file_backup.create_backup(original_file)
            
            # Clean up old backups (keep only 1)
            file_backup.cleanup_old_backups(original_file, keep_count=1)
            
            backups = file_backup.list_backups(original_file)
            assert len(backups) <= 1
            
            # Clean up remaining backups
            for backup in backups:
                if os.path.exists(backup):
                    os.unlink(backup)
                    
        finally:
            if os.path.exists(original_file):
                os.unlink(original_file)


class TestFileSynchronizer:
    """Test FileSynchronizer class."""

    @pytest.fixture
    def file_synchronizer(self):
        """Create a FileSynchronizer instance for testing."""
        return FileSynchronizer()

    def test_file_synchronizer_initialization(self, file_synchronizer):
        """Test FileSynchronizer initialization."""
        assert file_synchronizer.sync_rules == {}
        assert file_synchronizer.sync_history == []

    def test_add_sync_rule(self, file_synchronizer):
        """Test adding a sync rule."""
        def sync_rule(source, dest):
            return True
        
        file_synchronizer.add_sync_rule("test_rule", sync_rule)
        assert "test_rule" in file_synchronizer.sync_rules

    def test_sync_file(self, file_synchronizer):
        """Test syncing a file."""
        source_content = "source content"
        dest_content = "dest content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(source_content)
            source_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(dest_content)
            dest_file = f.name
        
        try:
            result = file_synchronizer.sync_file(source_file, dest_file)
            assert result is True
            
            with open(dest_file, 'r') as f:
                synced_content = f.read()
            assert synced_content == source_content
            
        finally:
            if os.path.exists(source_file):
                os.unlink(source_file)
            if os.path.exists(dest_file):
                os.unlink(dest_file)

    def test_sync_directory(self, file_synchronizer):
        """Test syncing a directory."""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as dest_dir:
                # Create files in source directory
                source_file1 = os.path.join(source_dir, "file1.txt")
                source_file2 = os.path.join(source_dir, "file2.txt")
                
                with open(source_file1, 'w') as f:
                    f.write("content1")
                with open(source_file2, 'w') as f:
                    f.write("content2")
                
                result = file_synchronizer.sync_directory(source_dir, dest_dir)
                assert result is True
                
                # Check that files were synced
                dest_file1 = os.path.join(dest_dir, "file1.txt")
                dest_file2 = os.path.join(dest_dir, "file2.txt")
                
                assert os.path.exists(dest_file1)
                assert os.path.exists(dest_file2)
                
                with open(dest_file1, 'r') as f:
                    assert f.read() == "content1"
                with open(dest_file2, 'r') as f:
                    assert f.read() == "content2"

    def test_get_sync_status(self, file_synchronizer):
        """Test getting sync status."""
        source_content = "source content"
        dest_content = "different content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(source_content)
            source_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(dest_content)
            dest_file = f.name
        
        try:
            status = file_synchronizer.get_sync_status(source_file, dest_file)
            assert status["synced"] is False
            assert status["source_size"] == len(source_content)
            assert status["dest_size"] == len(dest_content)
            
        finally:
            if os.path.exists(source_file):
                os.unlink(source_file)
            if os.path.exists(dest_file):
                os.unlink(dest_file)


class TestFileAnalyzer:
    """Test FileAnalyzer class."""

    @pytest.fixture
    def file_analyzer(self):
        """Create a FileAnalyzer instance for testing."""
        return FileAnalyzer()

    def test_file_analyzer_initialization(self, file_analyzer):
        """Test FileAnalyzer initialization."""
        assert file_analyzer.analyzers == {}
        assert file_analyzer.analysis_cache == {}

    def test_add_analyzer(self, file_analyzer):
        """Test adding a file analyzer."""
        def word_count_analyzer(content):
            return len(content.split())
        
        file_analyzer.add_analyzer("word_count", word_count_analyzer)
        assert "word_count" in file_analyzer.analyzers

    def test_analyze_file(self, file_analyzer):
        """Test analyzing a file."""
        def word_count_analyzer(content):
            return len(content.split())
        
        file_analyzer.add_analyzer("word_count", word_count_analyzer)
        
        test_content = "this is a test file with multiple words"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            result = file_analyzer.analyze_file(temp_file, ["word_count"])
            assert result["word_count"] == 8
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_analyze_file_multiple_analyzers(self, file_analyzer):
        """Test analyzing a file with multiple analyzers."""
        def word_count_analyzer(content):
            return len(content.split())
        
        def char_count_analyzer(content):
            return len(content)
        
        def line_count_analyzer(content):
            return len(content.splitlines())
        
        file_analyzer.add_analyzer("word_count", word_count_analyzer)
        file_analyzer.add_analyzer("char_count", char_count_analyzer)
        file_analyzer.add_analyzer("line_count", line_count_analyzer)
        
        test_content = "line one\nline two\nline three"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            result = file_analyzer.analyze_file(
                temp_file, ["word_count", "char_count", "line_count"]
            )
            assert result["word_count"] == 6
            assert result["char_count"] == len(test_content)
            assert result["line_count"] == 3
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_get_file_metadata(self, file_analyzer):
        """Test getting file metadata."""
        test_content = "test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            metadata = file_analyzer.get_file_metadata(temp_file)
            assert metadata["size"] == len(test_content)
            assert metadata["exists"] is True
            assert "created" in metadata
            assert "modified" in metadata
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestFileTransformer:
    """Test FileTransformer class."""

    @pytest.fixture
    def file_transformer(self):
        """Create a FileTransformer instance for testing."""
        return FileTransformer()

    def test_file_transformer_initialization(self, file_transformer):
        """Test FileTransformer initialization."""
        assert file_transformer.transformers == {}
        assert file_transformer.transformation_history == []

    def test_add_transformer(self, file_transformer):
        """Test adding a file transformer."""
        def uppercase_transformer(content):
            return content.upper()
        
        file_transformer.add_transformer("uppercase", uppercase_transformer)
        assert "uppercase" in file_transformer.transformers

    def test_transform_file(self, file_transformer):
        """Test transforming a file."""
        def uppercase_transformer(content):
            return content.upper()
        
        file_transformer.add_transformer("uppercase", uppercase_transformer)
        
        test_content = "test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            result = file_transformer.transform_file(temp_file, "uppercase")
            assert result is True
            
            with open(temp_file, 'r') as f:
                transformed_content = f.read()
            assert transformed_content == "TEST CONTENT"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_transform_file_with_backup(self, file_transformer):
        """Test transforming a file with backup."""
        def reverse_transformer(content):
            return content[::-1]
        
        file_transformer.add_transformer("reverse", reverse_transformer)
        
        original_content = "hello world"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(original_content)
            temp_file = f.name
        
        try:
            result = file_transformer.transform_file(
                temp_file, "reverse", create_backup=True
            )
            assert result is True
            
            with open(temp_file, 'r') as f:
                transformed_content = f.read()
            assert transformed_content == "dlrow olleh"
            
            # Check that backup was created
            backup_files = [f for f in os.listdir(os.path.dirname(temp_file)) 
                          if f.startswith(os.path.basename(temp_file) + ".backup")]
            assert len(backup_files) > 0
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_transform_content(self, file_transformer):
        """Test transforming content directly."""
        def title_case_transformer(content):
            return content.title()
        
        file_transformer.add_transformer("title_case", title_case_transformer)
        
        test_content = "hello world"
        result = file_transformer.transform_content(test_content, "title_case")
        assert result == "Hello World"

    def test_chain_transformations(self, file_transformer):
        """Test chaining multiple transformations."""
        def uppercase_transformer(content):
            return content.upper()
        
        def reverse_transformer(content):
            return content[::-1]
        
        file_transformer.add_transformer("uppercase", uppercase_transformer)
        file_transformer.add_transformer("reverse", reverse_transformer)
        
        test_content = "hello"
        result = file_transformer.chain_transformations(
            test_content, ["uppercase", "reverse"]
        )
        assert result == "OLLEH"
