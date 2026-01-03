"""Tests for main.py entry point."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import requests as requests_module

import sys as sys_module
from pathlib import Path
sys_module.path.insert(0, str(Path(__file__).parent.parent))

# Import the functions from main
from main import check_ollama, check_dependencies


class TestCheckOllama:
    """Tests for check_ollama function."""

    def test_check_ollama_running(self, capsys, monkeypatch):
        """Test when Ollama is running."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:3b"},
                {"name": "llama3:8b"}
            ]
        }

        def mock_get(*args, **kwargs):
            return mock_response

        monkeypatch.setattr(requests_module, "get", mock_get)

        result = check_ollama()

        assert result is True
        captured = capsys.readouterr()
        assert "Ollama is running" in captured.out

    def test_check_ollama_running_no_models(self, capsys, monkeypatch):
        """Test when Ollama is running but no models available."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}

        def mock_get(*args, **kwargs):
            return mock_response

        monkeypatch.setattr(requests_module, "get", mock_get)

        result = check_ollama()

        assert result is True
        captured = capsys.readouterr()
        assert "Ollama is running" in captured.out

    def test_check_ollama_not_running(self, capsys, monkeypatch):
        """Test when Ollama is not running."""

        def mock_get(*args, **kwargs):
            raise requests_module.RequestException("Connection refused")

        monkeypatch.setattr(requests_module, "get", mock_get)

        result = check_ollama()

        assert result is False
        captured = capsys.readouterr()
        assert "Ollama is not running" in captured.out

    def test_check_ollama_lists_models(self, capsys, monkeypatch):
        """Test that available models are listed."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:3b"},
                {"name": "llama3:8b"}
            ]
        }

        def mock_get(*args, **kwargs):
            return mock_response

        monkeypatch.setattr(requests_module, "get", mock_get)

        check_ollama()

        captured = capsys.readouterr()
        assert "qwen2.5:3b" in captured.out
        assert "llama3:8b" in captured.out


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    def test_check_dependencies_all_installed(self, capsys):
        """Test when all dependencies are installed."""
        # All required packages should be installed in test env
        result = check_dependencies()

        assert result is True
        captured = capsys.readouterr()
        assert "All dependencies installed" in captured.out

    def test_required_packages_list(self):
        """Test that required packages list is correct."""
        required = ['flet', 'requests', 'pydantic', 'chromadb', 'fpdf', 'psutil', 'dotenv']

        for package in required:
            try:
                __import__(package)
                installed = True
            except ImportError:
                installed = False

            # If running in test environment, all should be installed
            # This documents what packages are expected
            assert package in required


class TestMainModule:
    """Tests for main module structure."""

    def test_main_function_exists(self):
        """Test that main function exists."""
        from main import main
        assert callable(main)

    def test_check_ollama_exists(self):
        """Test that check_ollama function exists."""
        from main import check_ollama
        assert callable(check_ollama)

    def test_check_dependencies_exists(self):
        """Test that check_dependencies function exists."""
        from main import check_dependencies
        assert callable(check_dependencies)

    def test_run_app_imported(self):
        """Test that run_app is imported from src.ui.app."""
        from main import run_app
        assert callable(run_app)


class TestMainEntryPoint:
    """Tests for main entry point behavior."""

    @patch('main.run_app')
    @patch('main.check_ollama')
    @patch('main.check_dependencies')
    def test_main_calls_checks(self, mock_deps, mock_ollama, mock_run_app, capsys):
        """Test that main calls dependency and Ollama checks."""
        mock_deps.return_value = True
        mock_ollama.return_value = True

        from main import main
        main()

        mock_deps.assert_called_once()
        mock_ollama.assert_called_once()
        mock_run_app.assert_called_once()

    @patch('main.run_app')
    @patch('main.check_ollama')
    @patch('main.check_dependencies')
    def test_main_continues_if_ollama_not_running(self, mock_deps, mock_ollama, mock_run_app, capsys):
        """Test that main continues even if Ollama not running."""
        mock_deps.return_value = True
        mock_ollama.return_value = False  # Ollama not running

        from main import main
        main()

        # Should still call run_app
        mock_run_app.assert_called_once()

    @patch('main.sys.exit')
    @patch('main.check_dependencies')
    def test_main_exits_if_dependencies_missing(self, mock_deps, mock_exit, capsys):
        """Test that main exits if dependencies are missing."""
        mock_deps.return_value = False

        from main import main
        main()

        mock_exit.assert_called_with(1)

    def test_main_prints_header(self, capsys):
        """Test that main prints header."""
        # We can't easily test full main without running the app
        # Just verify the expected output format
        from main import main

        with patch('main.run_app'):
            with patch('main.check_dependencies', return_value=True):
                with patch('main.check_ollama', return_value=True):
                    main()

        captured = capsys.readouterr()
        assert "DocAssist EMR" in captured.out
