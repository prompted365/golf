"""Declarative coercion pipeline engine for type conversion."""

from typing import Any, Dict, List, Optional, Union
import re
from .models import DataType

class CoercionEngine:
    """
    Engine for coercing values using declarative pipelines.
    
    A coercion pipeline is a sequence of operations that transform
    a value from one form to another. Each pipeline step can be a
    simple operation (like 'lowercase') or a more complex operation
    with parameters (like splitting with a separator).
    """
    
    def __init__(self, pipelines: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the coercion engine with pipelines.
        
        Args:
            pipelines: Dictionary mapping data type names to their pipeline definitions
        """
        self.pipelines = pipelines or {}
        self._processors = {
            "lowercase": self._process_lowercase,
            "map_values": self._process_map_values,
            "split": self._process_split,
            "try_int": self._process_try_int,
            "try_float": self._process_try_float,
            "validate_email_format": self._process_validate_email,
            "default": self._process_default
        }
    
    def coerce(self, value: str, data_type: DataType) -> Any:
        """
        Coerce a value to the specified data type using the appropriate pipeline.
        
        Args:
            value: The value to coerce
            data_type: The target data type
            
        Returns:
            Any: The coerced value
        """
        # Get pipeline for this data type
        pipeline = self.pipelines.get(data_type.value, [])
        
        # If no pipeline defined, use default pipeline for the data type
        if not pipeline:
            pipeline = self._default_pipeline_for_type(data_type)
        
        # Process the value through the pipeline
        result = value
        for step in pipeline:
            # Simple string step (e.g., "lowercase")
            if isinstance(step, str):
                processor = self._processors.get(step)
                if processor:
                    result = processor(result)
            
            # Dictionary step with parameters
            elif isinstance(step, dict):
                for op, params in step.items():
                    processor = self._processors.get(op)
                    if processor:
                        result = processor(result, params)
            
            # Skip invalid steps
            else:
                continue
                
        return result
    
    def _default_pipeline_for_type(self, data_type: DataType) -> List[Union[str, Dict[str, Any]]]:
        """
        Get a default pipeline for a data type when no custom pipeline is defined.
        
        Args:
            data_type: The data type
            
        Returns:
            List[Union[str, Dict[str, Any]]]: Default pipeline for the type
        """
        if data_type == DataType.BOOLEAN:
            return [
                "lowercase",
                {"map_values": {
                    "true": ["true", "yes", "on", "1"],
                    "false": ["false", "no", "off", "0"]
                }},
                {"default": False}
            ]
        elif data_type == DataType.NUMBER:
            return [
                "try_int",
                "try_float",
                {"default": None}
            ]
        elif data_type == DataType.TAGS:
            return [
                {"split": {
                    "separator": ",",
                    "strip_whitespace": True
                }}
            ]
        elif data_type == DataType.EMAIL_ADDRESS:
            return [
                "validate_email_format",
                {"default": None}
            ]
        
        # Default to returning the value unchanged
        return []
    
    # Pipeline step processors
    
    def _process_lowercase(self, value: str) -> str:
        """Convert value to lowercase."""
        if isinstance(value, str):
            return value.lower()
        return value
    
    def _process_map_values(self, value: Any, mapping: Dict[str, List[str]]) -> Any:
        """
        Map a value to another based on a mapping of values to aliases.
        
        Args:
            value: The value to map
            mapping: Dictionary mapping target values to lists of possible input values
            
        Returns:
            The mapped value if a match is found, otherwise the original value
        """
        if not isinstance(value, str):
            return value
            
        value_str = str(value).lower()  # Convert to string and lowercase for comparison
        
        for target, aliases in mapping.items():
            if value_str in aliases:
                # Map special values like true/false to Python equivalents
                if target == "true":
                    return True
                elif target == "false":
                    return False
                return target
                
        return value
    
    def _process_split(self, value: Any, params: Dict[str, Any]) -> List[str]:
        """
        Split a string into a list based on the given separator.
        
        Args:
            value: The string to split
            params: Dictionary with 'separator' and optional 'strip_whitespace' flag
            
        Returns:
            List[str]: The split string
        """
        if not isinstance(value, str):
            return [value] if value is not None else []
            
        separator = params.get("separator", ",")
        strip_whitespace = params.get("strip_whitespace", False)
        
        if separator in value:
            parts = value.split(separator)
            if strip_whitespace:
                parts = [p.strip() for p in parts]
            return parts
        
        return [value]
    
    def _process_try_int(self, value: Any) -> Any:
        """Try to convert the value to an integer."""
        if isinstance(value, (int, float, bool)):
            return value
            
        try:
            return int(value)
        except (ValueError, TypeError):
            return value
    
    def _process_try_float(self, value: Any) -> Any:
        """Try to convert the value to a float."""
        if isinstance(value, (int, float, bool)):
            return value
            
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
    
    def _process_validate_email(self, value: Any) -> Any:
        """Validate if the value is an email address."""
        if not isinstance(value, str):
            return value
            
        # Basic email validation
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if re.match(pattern, value):
            return value
        return None
    
    def _process_default(self, value: Any, default_value: Any) -> Any:
        """Return the default value if the current value is None."""
        if value is None:
            return default_value
        return value 