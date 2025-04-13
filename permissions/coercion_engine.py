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
    
    def coerce(self, value: Any, data_type: Optional[DataType]) -> Any:
        """
        Coerce a value to the specified data type.
        
        Args:
            value: The value to coerce
            data_type: The target data type
            
        Returns:
            Any: The coerced value
        """
        # If no data type is specified, return the value as-is
        if data_type is None:
            return value
            
        # Get pipeline for this data type if available
        pipeline = self.get_pipeline_for_type(data_type)
        
        # If no pipeline, try to use built-in coercion
        if not pipeline:
            return self._basic_coercion(value, data_type)
            
        # Apply each step of the pipeline
        current_value = value
        for step in pipeline:
            if isinstance(step, dict):
                # Complex step with configuration
                step_name = list(step.keys())[0] if step else None
                if not step_name:
                    continue
                    
                step_config = step[step_name]
                current_value = self.apply_coercion_step(current_value, step_name, step_config)
            else:
                # Simple step name
                current_value = self.apply_coercion_step(current_value, step)
                
        return current_value
    
    def _basic_coercion(self, value: Any, data_type: DataType) -> Any:
        """
        Basic coercion for common data types when no pipeline is specified.
        
        Args:
            value: The value to coerce
            data_type: The target data type
            
        Returns:
            Any: The coerced value
        """
        # Ensure value is properly converted from string input
        if isinstance(value, str):
            # String type coercions
            if data_type == DataType.STRING:
                return value
            elif data_type == DataType.BOOLEAN:
                lower_value = value.lower()
                if lower_value in ["true", "yes", "1", "on"]:
                    return True
                elif lower_value in ["false", "no", "0", "off"]:
                    return False
                return bool(value)
            elif data_type == DataType.NUMBER:
                try:
                    if "." in value:
                        return float(value)
                    return int(value)
                except ValueError:
                    return value  # Return original if conversion fails
            elif data_type == DataType.TAGS:
                # Split comma-separated string if needed
                if "," in value:
                    return [tag.strip() for tag in value.split(",")]
                return [value]
            
        # Default case - return value unchanged if coercion not defined
        return value
    
    def get_pipeline_for_type(self, data_type: DataType) -> List[Union[str, Dict[str, Any]]]:
        """
        Get the pipeline for a specific data type.
        
        Args:
            data_type: The target data type
            
        Returns:
            List[Union[str, Dict[str, Any]]]: The pipeline for the data type
        """
        return self.pipelines.get(data_type.value, [])
    
    def apply_coercion_step(self, value: Any, step: Union[str, Dict[str, Any]], config: Any = None) -> Any:
        """
        Apply a single step of the pipeline to a value.
        
        Args:
            value: The value to apply the step to
            step: The step to apply
            config: Configuration for the step
            
        Returns:
            Any: The processed value
        """
        if isinstance(step, str):
            processor = self._processors.get(step)
            if processor:
                return processor(value)
        elif isinstance(step, dict):
            step_name = list(step.keys())[0] if step else None
            if step_name:
                processor = self._processors.get(step_name)
                if processor:
                    return processor(value, config)
        return value
    
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