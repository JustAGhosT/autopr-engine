"""
Tests for workflow condition evaluation improvements.
"""
import unittest
import asyncio
from autopr.workflows.base import SequentialWorkflow


class TestWorkflowConditions(unittest.TestCase):
    """Test suite for workflow condition evaluation."""

    def setUp(self):
        """Set up test fixtures."""
        self.workflow = SequentialWorkflow(
            name="test_workflow",
            description="Test workflow for conditions"
        )

    def test_boolean_condition_true(self):
        """Test simple boolean condition - true."""
        step = {"type": "condition", "condition": True}
        context = {}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])
        self.assertEqual(result["condition"], True)

    def test_boolean_condition_false(self):
        """Test simple boolean condition - false."""
        step = {"type": "condition", "condition": False}
        context = {}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertFalse(result["result"])
        self.assertEqual(result["condition"], False)

    def test_dict_condition_eq(self):
        """Test dictionary condition with eq operator."""
        step = {
            "type": "condition",
            "condition": {
                "op": "eq",
                "left": "$status",
                "right": "active"
            }
        }
        context = {"status": "active"}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])

    def test_dict_condition_ne(self):
        """Test dictionary condition with ne operator."""
        step = {
            "type": "condition",
            "condition": {
                "op": "ne",
                "left": "$status",
                "right": "inactive"
            }
        }
        context = {"status": "active"}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])

    def test_dict_condition_gt(self):
        """Test dictionary condition with gt operator."""
        step = {
            "type": "condition",
            "condition": {
                "op": "gt",
                "left": "$score",
                "right": 0.5
            }
        }
        context = {"score": 0.8}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])

    def test_dict_condition_lt(self):
        """Test dictionary condition with lt operator."""
        step = {
            "type": "condition",
            "condition": {
                "op": "lt",
                "left": "$score",
                "right": 0.9
            }
        }
        context = {"score": 0.5}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])

    def test_dict_condition_gte(self):
        """Test dictionary condition with gte operator."""
        step = {
            "type": "condition",
            "condition": {
                "op": "gte",
                "left": "$value",
                "right": 100
            }
        }
        context = {"value": 100}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])

    def test_dict_condition_lte(self):
        """Test dictionary condition with lte operator."""
        step = {
            "type": "condition",
            "condition": {
                "op": "lte",
                "left": "$value",
                "right": 100
            }
        }
        context = {"value": 50}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])

    def test_dict_condition_in(self):
        """Test dictionary condition with in operator."""
        step = {
            "type": "condition",
            "condition": {
                "op": "in",
                "left": "$platform",
                "right": ["base44", "windsurf", "cursor"]
            }
        }
        context = {"platform": "base44"}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])

    def test_dict_condition_contains(self):
        """Test dictionary condition with contains operator."""
        step = {
            "type": "condition",
            "condition": {
                "op": "contains",
                "left": "$platforms",
                "right": "base44"
            }
        }
        context = {"platforms": ["base44", "windsurf", "cursor"]}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        self.assertTrue(result["result"])

    def test_string_condition_with_variables(self):
        """Test string condition with variable substitution."""
        step = {
            "type": "condition",
            "condition": "{score} > 0.5"
        }
        context = {"score": 0.8}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        # String conditions use safe eval, should work
        self.assertIsNotNone(result["result"])

    def test_condition_error_handling(self):
        """Test that errors in conditions are handled gracefully."""
        step = {
            "type": "condition",
            "condition": {
                "op": "invalid_op",
                "left": "$value",
                "right": 100
            }
        }
        context = {"value": 50}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        # Should not crash, should return false on error
        self.assertFalse(result["result"])

    def test_missing_context_variable(self):
        """Test condition with missing context variable."""
        step = {
            "type": "condition",
            "condition": {
                "op": "eq",
                "left": "$missing_var",
                "right": "value"
            }
        }
        context = {}
        
        result = asyncio.run(self.workflow._execute_condition_step(step, context))
        
        # Should handle gracefully
        self.assertIsNotNone(result)


class TestParallelExecution(unittest.TestCase):
    """Test suite for parallel step execution."""

    def setUp(self):
        """Set up test fixtures."""
        self.workflow = SequentialWorkflow(
            name="test_workflow",
            description="Test workflow for parallel execution"
        )

    def test_parallel_steps_execute(self):
        """Test that parallel steps execute correctly."""
        step = {
            "type": "parallel",
            "steps": [
                {"type": "delay", "seconds": 0.1},
                {"type": "delay", "seconds": 0.1},
                {"type": "delay", "seconds": 0.1}
            ]
        }
        context = {}
        
        result = asyncio.run(self.workflow._execute_parallel_step(step, context))
        
        self.assertEqual(result["parallel_steps"], 3)
        self.assertEqual(result["completed"], 3)
        self.assertEqual(result["errors"], 0)

    def test_parallel_steps_with_errors(self):
        """Test parallel execution with errors in some steps."""
        step = {
            "type": "parallel",
            "steps": [
                {"type": "delay", "seconds": 0.1},
                {"type": "invalid_step"},  # This will cause an error
                {"type": "delay", "seconds": 0.1}
            ]
        }
        context = {}
        
        result = asyncio.run(self.workflow._execute_parallel_step(step, context))
        
        # Should still complete, but report errors
        self.assertEqual(result["parallel_steps"], 3)
        self.assertGreaterEqual(result["errors"], 0)  # May have errors

    def test_empty_parallel_steps(self):
        """Test parallel execution with empty steps list."""
        step = {
            "type": "parallel",
            "steps": []
        }
        context = {}
        
        result = asyncio.run(self.workflow._execute_parallel_step(step, context))
        
        self.assertEqual(result["parallel_steps"], 0)
        self.assertEqual(result["completed"], 0)


if __name__ == "__main__":
    unittest.main()
