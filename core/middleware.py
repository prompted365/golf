"""Permission middleware for API calls."""

import logging
from typing import Any, Dict, List, Optional, TypeVar, Callable

from .base import PermissionEngine, SchemaMapper
from .models import AccessRequest, AccessResult, AccessType, Resource, ResourceType

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for generic typing
T = TypeVar('T')

class PermissionMiddleware:
    """
    Permission middleware that enforces permissions for API calls.
    
    This middleware integrates with different service integrations
    and applies appropriate permission checks based on the service,
    resource type, and action being performed.
    """
    
    def __init__(
        self, 
        engine: PermissionEngine,
        schema_mapper: SchemaMapper,
        integration_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the permission middleware.
        
        Args:
            engine: The permission engine used for evaluating access
            schema_mapper: Schema mapper to map between API and internal fields
            integration_name: Name of the service integration (e.g., "linear", "gmail")
            config: Configuration options for the middleware
        """
        self.engine = engine
        self.schema_mapper = schema_mapper
        self.integration_name = integration_name
        
        # Default configuration
        self.config = {
            "log_level": "warning",                    # Logging level for permission denials
            "skip_missing_properties": True,           # Skip items with missing properties
            "default_item_key": "id",                  # Default key for collection items
            "endpoint_configs": {}                     # Custom configs for specific endpoints
        }
        
        # Update with user-provided config
        if config:
            self.config.update(config)
            
            # Merge nested dictionaries properly
            if "endpoint_configs" in config:
                self.config["endpoint_configs"].update(config["endpoint_configs"])
    
    async def get_resource_fields(self, resource_type: ResourceType) -> Dict[str, Dict[str, Any]]:
        """
        Get field information for a specific resource type in the current integration.
        
        Args:
            resource_type: The resource type
            
        Returns:
            Dictionary of field definitions from the integration schema
        """
        # Get integration from schema mapper
        integration = await self.schema_mapper.get_integration(self.integration_name)
        if not integration:
            logger.warning(f"Integration '{self.integration_name}' not found")
            return {}
            
        # Get resource mappings from integration mapping
        from .integrations import get_integration_mappings
        integration_mappings = get_integration_mappings()
        
        if self.integration_name not in integration_mappings:
            logger.warning(f"No mappings found for integration '{self.integration_name}'")
            return {}
            
        mappings = integration_mappings[self.integration_name]
        
        # Get resource fields
        if resource_type.value in mappings:
            fields = mappings[resource_type.value]
            # Filter out metadata and helper mappings
            return {k: v for k, v in fields.items() 
                   if not k.startswith('_') and isinstance(v, dict)}
        
        return {}
    
    async def get_id_fields(self, resource_type: ResourceType) -> List[str]:
        """
        Get the ID fields for a resource type in the current integration.
        
        Args:
            resource_type: The resource type
            
        Returns:
            List of field names that identify a resource
        """
        # Get endpoint-specific configuration if available
        endpoint_key = f"{resource_type.value.lower()}"
        endpoint_config = self.config.get("endpoint_configs", {}).get(endpoint_key, {})
        
        # Use endpoint-specific ID fields if provided
        if "id_fields" in endpoint_config:
            return endpoint_config["id_fields"]
            
        # Default ID fields if not specified in config
        default_fields = ["id", "identifier"]
        
        # Try to find ID fields from the resource fields
        resource_fields = await self.get_resource_fields(resource_type)
        
        # Look for fields with names that suggest they're identifiers
        id_field_names = []
        for field_name, field_info in resource_fields.items():
            # Fields named "id" or containing "id" in their name are likely identifiers
            if field_name == "id" or "id" in field_name.lower():
                id_field_names.append(field_name)
                
            # Fields that map to internal "id" field are identifiers
            if field_info.get("permission_field") == "id":
                id_field_names.append(field_name)
        
        # Use found ID fields if any, otherwise use default
        return id_field_names if id_field_names else default_fields
    
    async def get_endpoint_type(
        self, 
        resource_type: ResourceType, 
        endpoint_name: str
    ) -> str:
        """
        Determine the endpoint type (collection, resource, mixed).
        
        Args:
            resource_type: The resource type
            endpoint_name: Name of the endpoint/method
            
        Returns:
            String indicating the endpoint type ("collection", "resource", "mixed")
        """
        # Check endpoint-specific configuration
        endpoint_key = f"{resource_type.value.lower()}.{endpoint_name}"
        endpoint_config = self.config.get("endpoint_configs", {}).get(endpoint_key, {})
        
        if "type" in endpoint_config:
            return endpoint_config["type"]
            
        # Use naming convention to guess endpoint type if not configured
        if endpoint_name.startswith("get_") and not endpoint_name.endswith("s"):
            return "resource"  # get_user, get_issue likely return single resources
        elif endpoint_name.startswith("list_") or endpoint_name.startswith("search_") or endpoint_name.endswith("s"):
            return "collection"  # list_users, search_issues likely return collections
        else:
            return "mixed"  # Default to mixed if uncertain
    
    async def authorize(
        self,
        resource_type: ResourceType,
        action: AccessType,
        properties: Dict[str, Any] = None
    ) -> AccessResult:
        """
        Check if an action is authorized based on permissions.
        
        Args:
            resource_type: Type of resource being accessed
            action: Type of access (READ, WRITE, DELETE)
            properties: Properties of the resource
            
        Returns:
            AccessResult with allowed flag and reason
        """
        # Transform external API properties to internal field names
        transformed_properties = await self._transform_properties(resource_type, properties or {})
        
        # Print debug info for priority 3 issues specifically
        if resource_type == ResourceType.ISSUES:
            print("\n[DEBUG] Authorization check details:")
            print(f"[DEBUG] Resource type: {resource_type.value}")
            print(f"[DEBUG] Action: {action.value}")
            if properties and "priority" in properties:
                print(f"[DEBUG] Priority in original properties: {properties['priority']} (type: {type(properties['priority'])})")
            if "priority" in transformed_properties:
                print(f"[DEBUG] Priority in transformed properties: {transformed_properties['priority']} (type: {type(transformed_properties['priority'])})")
            
            # Print all properties for debugging
            print(f"[DEBUG] All original properties: {properties}")
            print(f"[DEBUG] All transformed properties: {transformed_properties}")
        
        # Create and evaluate access request
        request = AccessRequest(
            action=action,
            resource=Resource(
                type=resource_type,
                properties=transformed_properties
            )
        )
        
        result = await self.engine.check_access(request)
        
        # Debug output for priority issues
        if resource_type == ResourceType.ISSUES and properties and "priority" in properties:
            print(f"[DEBUG] Access decision for priority {properties.get('priority')}: {result.allowed}")
            print(f"[DEBUG] Reason: {result.reason}")
            
        return result
    
    async def _transform_properties(
        self,
        resource_type: ResourceType,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform properties from external API format to internal field names.
        
        Args:
            resource_type: Type of resource
            properties: Properties in external API format
            
        Returns:
            Properties with mapped internal field names
        """
        resource_fields = await self.get_resource_fields(resource_type)
        if not resource_fields:
            return properties  # No transformation if no field mappings
            
        transformed = {}
        
        # Map fields according to the integration schema
        for field_name, field_value in properties.items():
            if field_name in resource_fields:
                field_info = resource_fields[field_name]
                internal_field = field_info.get("permission_field", field_name)
                transformed[internal_field] = field_value
            else:
                # Pass through unmapped fields
                transformed[field_name] = field_value
                
        return transformed
    
    async def check_request(
        self,
        resource_type: ResourceType,
        action: AccessType,
        method_name: str,
        properties: Dict[str, Any] = None
    ) -> Optional[bool]:
        """
        Check if a request should proceed based on permissions.
        
        Args:
            resource_type: Type of resource being accessed
            action: Type of access (READ, WRITE, DELETE)
            method_name: API method/endpoint name
            properties: Properties of the resource
            
        Returns:
            True if allowed, False if denied, None if check should be skipped
        """
        # Determine endpoint type based on method name and configuration
        endpoint_type = await self.get_endpoint_type(resource_type, method_name)
        
        # For collection endpoints, typically skip pre-request check
        if endpoint_type == "collection":
            return None
        
        # For resource endpoints, always check permissions
        if endpoint_type == "resource":
            result = await self.authorize(resource_type, action, properties)
            if not result.allowed:
                self._log_denial(f"Permission denied for {method_name}: {result.reason}")
            return result.allowed
        
        # For mixed endpoints, check if it's a specific resource request
        if endpoint_type == "mixed":
            id_fields = await self.get_id_fields(resource_type)
            is_specific_request = any(field in properties for field in id_fields)
            
            if is_specific_request:
                result = await self.authorize(resource_type, action, properties)
                if not result.allowed:
                    self._log_denial(f"Permission denied for {method_name}: {result.reason}")
                return result.allowed
            else:
                return None  # Skip check for collection-like requests
        
        # Default to None (skip check)
        return None
    
    async def filter_results(
        self,
        results: Any,
        resource_type: ResourceType,
        action: AccessType,
        method_name: str,
        format_hint: Optional[str] = None
    ) -> Any:
        """
        Filter results based on permissions.
        
        Args:
            results: Results from the API call
            resource_type: Type of resource
            action: Type of access
            method_name: API method/endpoint name
            format_hint: Optional hint about the format of results
            
        Returns:
            Filtered results - NEVER returns None
        """
        try:
            print(f"[FILTER] Filtering {method_name} results for {resource_type.value}")
            
            # Get endpoint-specific configuration
            endpoint_key = f"{resource_type.value.lower()}.{method_name}"
            endpoint_config = self.config.get("endpoint_configs", {}).get(endpoint_key, {})
            
            # Get empty result template
            empty_result = endpoint_config.get("empty_result", None)
            if format_hint == "tuple" and empty_result is None:
                empty_result = ([], False)  # Default empty tuple result for paginated lists
            elif format_hint == "list" and empty_result is None:
                empty_result = []  # Default empty list for list results
            
            # Safety check: if results is None, return appropriate empty result
            if results is None:
                print(f"[FILTER] Results is None for {method_name}, returning empty result")
                return empty_result if empty_result is not None else []
            
            # Determine endpoint type
            endpoint_type = await self.get_endpoint_type(resource_type, method_name)
            
            # For resource endpoints with dict results, check permission
            if endpoint_type == "resource" and isinstance(results, dict):
                result = await self.authorize(resource_type, action, results)
                return results if result.allowed else (empty_result if empty_result is not None else {})
            
            # Handle different response formats based on configuration or auto-detection
            response_format = format_hint or endpoint_config.get("response_format")
            
            if response_format is None:
                # Auto-detect format
                if isinstance(results, list):
                    response_format = "list"
                elif isinstance(results, tuple) and len(results) >= 1:
                    response_format = "tuple"
                elif isinstance(results, dict):
                    # Check if this is a dict with lists or a single resource
                    has_lists = any(isinstance(v, list) for v in results.values())
                    if has_lists:
                        response_format = "dict_with_list"
                    else:
                        # Check if it looks like a single resource
                        id_fields = await self.get_id_fields(resource_type)
                        is_resource = any(field in results for field in id_fields)
                        response_format = "resource" if is_resource else "other"
                else:
                    response_format = "other"
                    
            print(f"[FILTER] Detected response format: {response_format}")
            
            # Get item key for collections
            item_key = endpoint_config.get("item_key", self.config.get("default_item_key", "id"))
            
            # Filter based on format
            if response_format == "list":
                filtered = await self._filter_list(results, resource_type, action, item_key)
                # If all items were filtered out or result is None, return empty list
                if filtered is None or (not filtered and results):
                    print(f"[FILTER] All items were filtered out, returning empty list")
                    return [] if empty_result is None else empty_result
                return filtered
                
            elif response_format == "tuple":
                # Handle (items, metadata) format common in paginated responses
                if len(results) >= 1 and isinstance(results[0], list):
                    # Process items in the first position
                    filtered_items = await self._filter_list(results[0], resource_type, action, item_key)
                    
                    # Safety check for None filtered_items
                    if filtered_items is None:
                        filtered_items = []
                    
                    # Return filtered tuple with the rest of the elements preserved
                    return (filtered_items,) + results[1:]
                return results
                
            elif response_format == "dict_with_list":
                # Map of collection configs for this endpoint
                collections_config = endpoint_config.get("collections", {})
                
                # Copy the dict to avoid modifying the original
                filtered_dict = dict(results)
                
                # Filter each list in the dict
                for key, value in results.items():
                    if isinstance(value, list):
                        # Get item key for this specific collection if configured
                        collection_item_key = collections_config.get(key, {}).get("item_key", item_key)
                        
                        # Filter the list
                        filtered_list = await self._filter_list(value, resource_type, action, collection_item_key)
                        
                        # Safety check for None filtered_list
                        if filtered_list is None:
                            filtered_list = []
                            
                        filtered_dict[key] = filtered_list
                
                return filtered_dict
                
            elif response_format == "resource":
                # Single resource
                result = await self.authorize(resource_type, action, results)
                return results if result.allowed else (empty_result if empty_result is not None else {})
                
            # Default, return as is
            return results
            
        except Exception as e:
            # Log the error but don't crash - return empty result based on format
            print(f"[FILTER] Error during filtering for {method_name}: {str(e)}")
            
            # Determine appropriate empty result based on detected format
            if format_hint == "tuple":
                return empty_result if empty_result is not None else ([], False)
            elif format_hint == "list":
                return empty_result if empty_result is not None else []
            else:
                return empty_result if empty_result is not None else {}
    
    async def _filter_list(
        self,
        items: List[Dict[str, Any]],
        resource_type: ResourceType,
        action: AccessType,
        item_key: str
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of items based on permissions.
        
        Args:
            items: List of items to filter
            resource_type: Type of resource
            action: Type of access
            item_key: Key that uniquely identifies items
            
        Returns:
            List[Dict[str, Any]]: Filtered list - NEVER returns None
        """
        try:
            # Safety check to prevent NoneType errors
            if items is None:
                print("[FILTER_LIST] Received None instead of a list, returning empty list")
                return []
                
            if not items:
                return []
                
            filtered_items = []
            skip_missing = self.config.get("skip_missing_properties", True)
            
            print(f"[FILTER_LIST] Filtering {len(items)} {resource_type.value} items")
            
            for item in items:
                try:
                    if item is None:
                        print("[FILTER_LIST] Found None item in list, skipping")
                        continue
                        
                    # Skip items without the key if configured that way
                    if item_key not in item and not skip_missing:
                        self._log_warning(f"Item missing '{item_key}'")
                        continue
                    
                    # Check if this item is allowed
                    try:
                        result = await self.authorize(resource_type, action, item)
                        
                        if result.allowed:
                            filtered_items.append(item)
                        else:
                            item_id = item.get(item_key, "[unknown]")
                            print(f"[FILTER_LIST] DENIED: {resource_type.value} with {item_key}={item_id}: {result.reason}")
                    except Exception as auth_err:
                        print(f"[FILTER_LIST] Error during authorization check: {str(auth_err)}")
                        # Skip this item but continue processing others
                        continue
                        
                except Exception as item_err:
                    print(f"[FILTER_LIST] Error processing item: {str(item_err)}")
                    continue
                    
            print(f"[FILTER_LIST] Filtered result: {len(filtered_items)} of {len(items)} items passed")
            return filtered_items
            
        except Exception as e:
            print(f"[FILTER_LIST] Unexpected error filtering list: {str(e)}")
            return []  # Always return a list, even if empty
    
    def _log_denial(self, message: str) -> None:
        """Log a permission denial based on the configured log level."""
        log_level = self.config.get("log_level", "warning").lower()
        if log_level == "debug":
            logger.debug(message)
        elif log_level == "info":
            logger.info(message)
        elif log_level == "warning":
            logger.warning(message)
        elif log_level == "error":
            logger.error(message)
    
    def _log_warning(self, message: str) -> None:
        """Log a warning message."""
        logger.warning(message)
    
    def _log_debug(self, message: str) -> None:
        """Log a debug message."""
        logger.debug(message)
    
    def apply_to(
        self,
        client_class: Any,
        method_configs: Dict[str, Dict[str, Any]]
    ) -> Any:
        """
        Apply middleware to methods of a client class.
        
        Args:
            client_class: The API client class to apply middleware to
            method_configs: Configuration for methods to apply middleware to
            
        Returns:
            A new class with middleware applied
        """
        middleware = self
        
        class MiddlewareClient:
            """A client with permission middleware applied."""
            
            def __init__(self, *args, **kwargs):
                self._client = client_class(*args, **kwargs)
                self._middleware = middleware
                
                # Apply middleware to configured methods
                for method_name, config in method_configs.items():
                    if hasattr(self._client, method_name):
                        setattr(self, method_name, self._create_middleware_method(
                            method_name=method_name, 
                            original_method=getattr(self._client, method_name),
                            resource_type=config["resource_type"],
                            action=config["action"],
                            **config.get("options", {})
                        ))
            
            def _create_middleware_method(
                self,
                method_name: str,
                original_method: Callable,
                resource_type: ResourceType,
                action: AccessType,
                **options
            ) -> Callable:
                """Create a middleware-wrapped method."""
                debug = options.get("debug", False)
                empty_result = options.get("empty_result", None)
                
                async def middleware_method(*args, **kwargs):
                    # Extract request properties from kwargs
                    properties = {k: v for k, v in kwargs.items() if v is not None}
                    
                    if debug:
                        print(f"[MIDDLEWARE] Starting request {method_name} with properties {properties}")
                    
                    # Pre-request check
                    proceed = await self._middleware.check_request(
                        resource_type=resource_type,
                        action=action,
                        method_name=method_name,
                        properties=properties
                    )
                    
                    # If explicitly denied, don't proceed
                    if proceed is False:
                        if debug:
                            print(f"[MIDDLEWARE] Request {method_name} denied by pre-request check")
                        # Return appropriate empty result
                        return empty_result
                    
                    # Call the original method
                    if debug:
                        print(f"[MIDDLEWARE] Calling original method {method_name}")
                    results = await original_method(*args, **kwargs)
                    
                    # Very important: Handle None results from the API
                    if results is None:
                        if debug:
                            print(f"[MIDDLEWARE] Original method {method_name} returned None")
                        return empty_result
                    
                    # Filter results - handle None return values from filter_results
                    if debug:
                        print(f"[MIDDLEWARE] Filtering results for {method_name}")
                        
                    try:
                        filtered_results = await self._middleware.filter_results(
                            results=results,
                            resource_type=resource_type,
                            action=action,
                            method_name=method_name,
                            format_hint=options.get("format_hint")
                        )
                        
                        # Critical: Handle None filtered results
                        if filtered_results is None:
                            if debug:
                                print(f"[MIDDLEWARE] filter_results returned None for {method_name}")
                            return empty_result
                            
                        return filtered_results
                        
                    except Exception as e:
                        if debug:
                            print(f"[MIDDLEWARE] Error during filtering: {str(e)}")
                        # On error, return empty result instead of propagating the exception
                        return empty_result
                
                return middleware_method
            
            # Pass through other methods and properties
            def __getattr__(self, name):
                return getattr(self._client, name)
                
            # Support context manager if the client does
            async def __aenter__(self):
                if hasattr(self._client, "__aenter__"):
                    await self._client.__aenter__()
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if hasattr(self._client, "__aexit__"):
                    await self._client.__aexit__(exc_type, exc_val, exc_tb)
        
        return MiddlewareClient 