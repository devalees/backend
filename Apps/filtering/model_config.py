from typing import Dict, List, Optional, Set, Type, Union
from django.db import models
import logging

logger = logging.getLogger(__name__)

class ModelConfig:
    """
    Configuration class for model-specific filtering and aggregation settings.
    
    This class allows developers to specify which fields should be available
    for filtering and aggregation, along with performance configurations like indexes.
    """
    
    def __init__(self, model_class: Type[models.Model]):
        self.model_class = model_class
        self.model_name = model_class.__name__
        
        # Default empty configurations
        self.filter_fields: Dict[str, List[str]] = {
            'text': [],
            'numeric': [],
            'date': [],
            'time': [],
            'datetime': [],
            'boolean': [],
            'choice': [],
            'related': []
        }
        
        self.aggregation_fields: Dict[str, List[str]] = {
            'group_by': [],
            'sum': [],
            'avg': [],
            'min': [],
            'max': [],
            'count': []
        }
        
        self.indexes: List[List[str]] = []
        
        # Load configurations from model if available
        self._load_config_from_model()
        
    def _load_config_from_model(self) -> None:
        """
        Load configuration from the model's FilterConfig and AggregationConfig classes
        if they exist.
        """
        # Check for FilterConfig
        if hasattr(self.model_class, 'FilterConfig'):
            filter_config = getattr(self.model_class, 'FilterConfig')
            
            for field_type, fields in self.filter_fields.items():
                if hasattr(filter_config, field_type):
                    field_list = getattr(filter_config, field_type)
                    if isinstance(field_list, (list, tuple)):
                        self.filter_fields[field_type] = list(field_list)
                    else:
                        logger.warning(
                            f"Invalid {field_type} field list for {self.model_name}. "
                            f"Expected list or tuple, got {type(field_list).__name__}"
                        )
            
            # Load indexes if available
            if hasattr(filter_config, 'indexes'):
                indexes = getattr(filter_config, 'indexes')
                if isinstance(indexes, (list, tuple)):
                    self.indexes = [list(idx) if isinstance(idx, (list, tuple)) else [idx] 
                                  for idx in indexes if idx]
        
        # Check for AggregationConfig
        if hasattr(self.model_class, 'AggregationConfig'):
            agg_config = getattr(self.model_class, 'AggregationConfig')
            
            for agg_type, fields in self.aggregation_fields.items():
                if hasattr(agg_config, agg_type):
                    field_list = getattr(agg_config, agg_type)
                    if isinstance(field_list, (list, tuple)):
                        self.aggregation_fields[agg_type] = list(field_list)
                    else:
                        logger.warning(
                            f"Invalid {agg_type} field list for {self.model_name}. "
                            f"Expected list or tuple, got {type(field_list).__name__}"
                        )
    
    def get_filter_fields(self, field_type: Optional[str] = None) -> Union[Dict[str, List[str]], List[str]]:
        """
        Get filter fields configuration.
        
        Args:
            field_type: Optional field type to return only fields of that type
            
        Returns:
            Either the full filter fields dict or a list of fields for the specified type
        """
        if field_type:
            return self.filter_fields.get(field_type, [])
        return self.filter_fields
    
    def get_aggregation_fields(self, agg_type: Optional[str] = None) -> Union[Dict[str, List[str]], List[str]]:
        """
        Get aggregation fields configuration.
        
        Args:
            agg_type: Optional aggregation type to return only fields for that type
            
        Returns:
            Either the full aggregation fields dict or a list of fields for the specified type
        """
        if agg_type:
            return self.aggregation_fields.get(agg_type, [])
        return self.aggregation_fields
    
    def get_indexes(self) -> List[List[str]]:
        """Get the list of indexes defined for this model."""
        return self.indexes

    @classmethod
    def create_for_model(cls, model_class: Type[models.Model]) -> 'ModelConfig':
        """
        Factory method to create a ModelConfig instance for a given model.
        
        Args:
            model_class: The Django model class to create configuration for
            
        Returns:
            A ModelConfig instance for the model
        """
        return cls(model_class) 