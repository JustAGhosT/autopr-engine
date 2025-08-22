#!/usr/bin/env python3
"""
Test script for the AI Enhanced File Splitter

This script demonstrates the capabilities of the AI enhanced file splitter
by testing it with various file types and complexity levels.
"""

import os
import tempfile
from pathlib import Path

# Import the file splitter components
from autopr.actions.ai_linting_fixer.file_splitter import (
    FileSplitter,
    SplitConfig,
    FileComplexityAnalyzer,
    SplitComponent,
)


def create_test_file(content: str, filename: str = "test_file.py") -> str:
    """Create a temporary test file with the given content."""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


def test_complexity_analysis():
    """Test the complexity analysis functionality."""
    print("=== Testing Complexity Analysis ===")

    # Create a complex test file
    complex_content = """
import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: int
    
    def is_adult(self) -> bool:
        return self.age >= 18
    
    def get_display_name(self) -> str:
        if self.name:
            return self.name
        return self.email.split('@')[0]

class UserManager:
    def __init__(self):
        self.users: List[User] = []
        self.user_cache: Dict[str, User] = {}
    
    def add_user(self, user: User) -> bool:
        if user.email in self.user_cache:
            return False
        self.users.append(user)
        self.user_cache[user.email] = user
        return True
    
    def get_user(self, email: str) -> Optional[User]:
        return self.user_cache.get(email)
    
    def remove_user(self, email: str) -> bool:
        if email not in self.user_cache:
            return False
        user = self.user_cache.pop(email)
        self.users.remove(user)
        return True
    
    def get_adult_users(self) -> List[User]:
        return [user for user in self.users if user.is_adult()]
    
    def get_users_by_age_range(self, min_age: int, max_age: int) -> List[User]:
        return [user for user in self.users if min_age <= user.age <= max_age]

def process_user_data(users: List[User]) -> Dict[str, int]:
    result = {}
    for user in users:
        age_group = "adult" if user.is_adult() else "minor"
        result[age_group] = result.get(age_group, 0) + 1
    return result

def validate_user_input(name: str, email: str, age: int) -> bool:
    if not name or not email:
        return False
    if '@' not in email:
        return False
    if age < 0 or age > 150:
        return False
    return True

if __name__ == "__main__":
    manager = UserManager()
    
    # Add some test users
    users_data = [
        ("Alice", "alice@example.com", 25),
        ("Bob", "bob@example.com", 17),
        ("Charlie", "charlie@example.com", 30),
    ]
    
    for name, email, age in users_data:
        if validate_user_input(name, email, age):
            user = User(name, email, age)
            manager.add_user(user)
    
    # Process and display results
    adult_users = manager.get_adult_users()
    age_stats = process_user_data(manager.users)
    
    print(f"Total users: {len(manager.users)}")
    print(f"Adult users: {len(adult_users)}")
    print(f"Age statistics: {age_stats}")
"""

    file_path = create_test_file(complex_content)

    try:
        # Test complexity analyzer
        analyzer = FileComplexityAnalyzer()
        complexity_data = analyzer.analyze_file_complexity(file_path, complex_content)

        print(f"Complexity Analysis Results:")
        print(f"  Total lines: {complexity_data['total_lines']}")
        print(f"  Total functions: {complexity_data['total_functions']}")
        print(f"  Total classes: {complexity_data['total_classes']}")
        print(
            f"  Max function complexity: {complexity_data['max_function_complexity']}"
        )
        print(f"  File size: {complexity_data['file_size_bytes']} bytes")
        print(f"  Cyclomatic complexity: {complexity_data['cyclomatic_complexity']}")

        # Test split decision
        config = SplitConfig(
            max_lines_per_file=50,
            max_functions_per_file=5,
            max_classes_per_file=2,
            max_cyclomatic_complexity=10,
            max_file_size_bytes=2000,
        )

        should_split, reasoning = analyzer.should_split_by_complexity(
            complexity_data, config
        )
        print(f"\nSplit Decision: {should_split}")
        print(f"Reasoning: {reasoning}")

    finally:
        # Cleanup
        os.remove(file_path)
        os.rmdir(os.path.dirname(file_path))


def test_file_splitting():
    """Test the file splitting functionality."""
    print("\n=== Testing File Splitting ===")

    # Create a large test file that should be split
    large_content = """
import os
import sys
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Configuration class
@dataclass
class Config:
    debug: bool = False
    log_level: str = "INFO"
    max_connections: int = 100
    timeout: int = 30
    
    def validate(self) -> bool:
        if self.max_connections <= 0:
            return False
        if self.timeout <= 0:
            return False
        return True

# Database connection class
class DatabaseConnection:
    def __init__(self, host: str, port: int, database: str):
        self.host = host
        self.port = port
        self.database = database
        self.connected = False
        self.connection_pool = []
    
    def connect(self) -> bool:
        try:
            # Simulate connection
            self.connected = True
            return True
        except Exception:
            return False
    
    def disconnect(self) -> None:
        self.connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if not self.connected:
            raise ConnectionError("Not connected to database")
        # Simulate query execution
        return [{"result": "success"}]
    
    def get_connection_info(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "connected": self.connected
        }

# User management class
class UserManager:
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.users_cache = {}
    
    def create_user(self, username: str, email: str, password: str) -> bool:
        if username in self.users_cache:
            return False
        
        user_data = {
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password),
            "created_at": datetime.now().isoformat()
        }
        
        self.users_cache[username] = user_data
        return True
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        return self.users_cache.get(username)
    
    def update_user(self, username: str, **kwargs) -> bool:
        if username not in self.users_cache:
            return False
        
        user = self.users_cache[username]
        user.update(kwargs)
        return True
    
    def delete_user(self, username: str) -> bool:
        if username not in self.users_cache:
            return False
        
        del self.users_cache[username]
        return True
    
    def list_users(self) -> List[Dict[str, Any]]:
        return list(self.users_cache.values())
    
    def _hash_password(self, password: str) -> str:
        # Simple hash simulation
        return f"hash_{password}_{len(password)}"

# Authentication class
class Authenticator:
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
        self.active_sessions = {}
    
    def login(self, username: str, password: str) -> Optional[str]:
        user = self.user_manager.get_user(username)
        if not user:
            return None
        
        if self._verify_password(password, user["password_hash"]):
            session_id = self._generate_session_id()
            self.active_sessions[session_id] = username
            return session_id
        
        return None
    
    def logout(self, session_id: str) -> bool:
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def is_authenticated(self, session_id: str) -> bool:
        return session_id in self.active_sessions
    
    def get_user_from_session(self, session_id: str) -> Optional[str]:
        return self.active_sessions.get(session_id)
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        expected_hash = f"hash_{password}_{len(password)}"
        return password_hash == expected_hash
    
    def _generate_session_id(self) -> str:
        import uuid
        return str(uuid.uuid4())

# API handler class
class APIHandler:
    def __init__(self, config: Config, db_connection: DatabaseConnection):
        self.config = config
        self.db = db_connection
        self.user_manager = UserManager(db_connection)
        self.authenticator = Authenticator(self.user_manager)
    
    def handle_request(self, method: str, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if method == "GET":
            return self._handle_get_request(path, data)
        elif method == "POST":
            return self._handle_post_request(path, data)
        elif method == "PUT":
            return self._handle_put_request(path, data)
        elif method == "DELETE":
            return self._handle_delete_request(path, data)
        else:
            return {"error": "Method not allowed"}
    
    def _handle_get_request(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if path == "/users":
            return {"users": self.user_manager.list_users()}
        elif path.startswith("/users/"):
            username = path.split("/")[-1]
            user = self.user_manager.get_user(username)
            if user:
                return {"user": user}
            return {"error": "User not found"}
        else:
            return {"error": "Path not found"}
    
    def _handle_post_request(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if path == "/users":
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            
            if not all([username, email, password]):
                return {"error": "Missing required fields"}
            
            success = self.user_manager.create_user(username, email, password)
            if success:
                return {"message": "User created successfully"}
            return {"error": "User already exists"}
        
        elif path == "/login":
            username = data.get("username")
            password = data.get("password")
            
            if not all([username, password]):
                return {"error": "Missing credentials"}
            
            session_id = self.authenticator.login(username, password)
            if session_id:
                return {"session_id": session_id}
            return {"error": "Invalid credentials"}
        
        else:
            return {"error": "Path not found"}
    
    def _handle_put_request(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if path.startswith("/users/"):
            username = path.split("/")[-1]
            success = self.user_manager.update_user(username, **data)
            if success:
                return {"message": "User updated successfully"}
            return {"error": "User not found"}
        else:
            return {"error": "Path not found"}
    
    def _handle_delete_request(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if path.startswith("/users/"):
            username = path.split("/")[-1]
            success = self.user_manager.delete_user(username)
            if success:
                return {"message": "User deleted successfully"}
            return {"error": "User not found"}
        else:
            return {"error": "Path not found"}

# Main application class
class Application:
    def __init__(self, config: Config):
        self.config = config
        self.db_connection = DatabaseConnection("localhost", 5432, "myapp")
        self.api_handler = APIHandler(config, self.db_connection)
        self.logger = self._setup_logging()
    
    def start(self) -> None:
        self.logger.info("Starting application...")
        
        if not self.config.validate():
            self.logger.error("Invalid configuration")
            return
        
        if not self.db_connection.connect():
            self.logger.error("Failed to connect to database")
            return
        
        self.logger.info("Application started successfully")
    
    def stop(self) -> None:
        self.logger.info("Stopping application...")
        self.db_connection.disconnect()
        self.logger.info("Application stopped")
    
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("myapp")
        logger.setLevel(getattr(logging, self.config.log_level))
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

# Utility functions
def load_config_from_file(file_path: str) -> Config:
    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        return Config(**config_data)
    except Exception as e:
        print(f"Error loading config: {e}")
        return Config()

def save_config_to_file(config: Config, file_path: str) -> bool:
    try:
        config_data = {
            "debug": config.debug,
            "log_level": config.log_level,
            "max_connections": config.max_connections,
            "timeout": config.timeout
        }
        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def validate_config(config: Config) -> List[str]:
    errors = []
    
    if config.max_connections <= 0:
        errors.append("max_connections must be positive")
    
    if config.timeout <= 0:
        errors.append("timeout must be positive")
    
    if config.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        errors.append("invalid log_level")
    
    return errors

if __name__ == "__main__":
    # Load configuration
    config = load_config_from_file("config.json")
    
    # Validate configuration
    errors = validate_config(config)
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Create and start application
    app = Application(config)
    app.start()
    
    try:
        # Simulate some API calls
        api_handler = app.api_handler
        
        # Create a user
        result = api_handler.handle_request("POST", "/users", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        print(f"Create user result: {result}")
        
        # Login
        result = api_handler.handle_request("POST", "/login", {
            "username": "testuser",
            "password": "password123"
        })
        print(f"Login result: {result}")
        
        # Get users
        result = api_handler.handle_request("GET", "/users", {})
        print(f"Get users result: {result}")
        
    finally:
        app.stop()
"""

    file_path = create_test_file(large_content, "large_app.py")

    try:
        # Test file splitter
        config = SplitConfig(
            max_lines_per_file=100,
            max_functions_per_file=10,
            max_classes_per_file=3,
            max_cyclomatic_complexity=15,
            max_file_size_bytes=5000,
            use_ai_analysis=False,  # Disable AI for testing
        )

        splitter = FileSplitter(config=config)

        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Test should_split_file
        should_split, reasoning = splitter.should_split_file(file_path, content)
        print(f"Should split: {should_split}")
        print(f"Reasoning: {reasoning}")

        if should_split:
            # Test actual splitting
            result = splitter.split_file(file_path, content)
            print(f"\nSplit Result:")
            print(f"  Success: {result.success}")
            print(f"  Strategy: {result.split_strategy}")
            print(f"  Components: {len(result.components)}")
            print(f"  Processing time: {result.processing_time:.2f}s")
            print(f"  Validation passed: {result.validation_passed}")

            # Show component details
            for i, component in enumerate(result.components):
                print(f"\n  Component {i+1}: {component.name}")
                print(f"    Type: {component.component_type}")
                print(f"    Lines: {component.start_line}-{component.end_line}")
                print(f"    Complexity: {component.complexity_score}")
                print(f"    Dependencies: {len(component.dependencies)}")

        # Get statistics
        stats = splitter.get_split_statistics()
        print(f"\nSplit Statistics:")
        print(f"  Total splits: {stats['total_splits']}")
        print(f"  Success rate: {stats['success_rate']:.2%}")
        print(f"  Strategy distribution: {stats['strategy_distribution']}")

    finally:
        # Cleanup
        os.remove(file_path)
        os.rmdir(os.path.dirname(file_path))


def main():
    """Run all tests."""
    print("AI Enhanced File Splitter Test Suite")
    print("=" * 50)

    test_complexity_analysis()
    test_file_splitting()

    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    main()
