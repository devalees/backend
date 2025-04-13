import pytest
from unittest.mock import patch, MagicMock, call
import sys
import os

from ..apply_to_existing_models import apply_to_apps, print_summary, main


class TestApplyToExistingModels:
    """Test suite for apply_to_existing_models.py script."""
    
    @pytest.fixture
    def mock_model_registry(self):
        """Fixture to mock the model_registry."""
        with patch('Apps.filtering.apply_to_existing_models.model_registry') as mock:
            # Create mock models
            mock_model1 = MagicMock()
            mock_model1._meta.app_label = 'app1'
            mock_model1.__name__ = 'Model1'
            
            mock_model2 = MagicMock()
            mock_model2._meta.app_label = 'app1'
            mock_model2.__name__ = 'Model2'
            
            mock_model3 = MagicMock()
            mock_model3._meta.app_label = 'app2'
            mock_model3.__name__ = 'Model3'
            
            # Set up discover_models and register_discovered_models
            mock.discover_models.return_value = {mock_model1, mock_model2, mock_model3}
            
            # Set up registered_models property
            mock.registered_models = [mock_model1, mock_model2, mock_model3]
            
            yield mock
    
    @pytest.fixture
    def mock_logger(self):
        """Fixture to mock the logger."""
        with patch('Apps.filtering.apply_to_existing_models.logger') as mock:
            yield mock
    
    def test_apply_to_apps_with_app_labels(self, mock_model_registry):
        """Test applying to specific apps."""
        app_labels = ['app1', 'app2']
        
        # Call the function
        summary = apply_to_apps(app_labels)
        
        # Check that discover_models was called with app_labels
        mock_model_registry.discover_models.assert_called_once_with(app_labels)
        
        # Check that register_discovered_models was called
        mock_model_registry.register_discovered_models.assert_called_once()
        
        # Check summary
        assert 'app1' in summary
        assert 'app2' in summary
        assert len(summary['app1']) == 2
        assert len(summary['app2']) == 1
        assert 'Model1' in summary['app1']
        assert 'Model2' in summary['app1']
        assert 'Model3' in summary['app2']
    
    def test_apply_to_apps_without_app_labels(self, mock_model_registry):
        """Test applying to all apps."""
        # Call the function without app_labels
        summary = apply_to_apps()
        
        # Check that discover_models was called with None
        mock_model_registry.discover_models.assert_called_once_with(None)
        
        # Check that register_discovered_models was called
        mock_model_registry.register_discovered_models.assert_called_once()
    
    def test_print_summary(self, mock_logger):
        """Test printing summary."""
        summary = {
            'app1': ['Model1', 'Model2'],
            'app2': ['Model3']
        }
        
        # Call the function
        print_summary(summary)
        
        # Check that logger.info was called with the expected messages
        assert mock_logger.info.call_count >= 4
        mock_logger.info.assert_any_call("Registration Summary:")
        mock_logger.info.assert_any_call("  app1: 2 models")
        mock_logger.info.assert_any_call("    - Model1")
        mock_logger.info.assert_any_call("    - Model2")
        mock_logger.info.assert_any_call("  app2: 1 models")
        mock_logger.info.assert_any_call("    - Model3")
    
    @patch('Apps.filtering.apply_to_existing_models.apply_to_apps')
    @patch('Apps.filtering.apply_to_existing_models.print_summary')
    def test_main_success(self, mock_print_summary, mock_apply_to_apps, mock_logger):
        """Test main function with successful execution."""
        # Set up mock return value
        mock_apply_to_apps.return_value = {'app1': ['Model1']}
        
        # Mock sys.argv
        with patch.object(sys, 'argv', ['apply_to_existing_models.py', 'app1']):
            # Call main
            result = main()
        
        # Check that apply_to_apps was called with the correct arguments
        mock_apply_to_apps.assert_called_once_with(['app1'])
        
        # Check that print_summary was called with the correct arguments
        mock_print_summary.assert_called_once_with({'app1': ['Model1']})
        
        # Check that logger.info was called with success message
        mock_logger.info.assert_any_call("Successfully applied filtering and aggregation to existing models")
        
        # Check result
        assert result == 0
    
    @patch('Apps.filtering.apply_to_existing_models.apply_to_apps')
    def test_main_error(self, mock_apply_to_apps, mock_logger):
        """Test main function with error."""
        # Set up mock to raise an exception
        mock_apply_to_apps.side_effect = Exception("Test error")
        
        # Call main
        result = main()
        
        # Check that logger.error was called with error message
        mock_logger.error.assert_called_once()
        
        # Check result
        assert result == 1 