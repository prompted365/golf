import pytest
import pytest_asyncio


# Use absolute imports
from core import AuthedManager, PipelineConfig
from core.exceptions import AuthedError

from tests.mocks.identity_mock import MockIdentityModule
from tests.mocks.permissions_mock import MockPermissionsModule
from tests.mocks.credentials_mock import MockCredentialsModule
from tests.mocks.audit_mock import MockAuditModule, MockAuditLogger


@pytest_asyncio.fixture
async def authed_manager():
    """Fixture to create an AuthedManager with mock modules."""
    # Create a mock audit logger first
    mock_audit_logger = MockAuditLogger()
    
    # Create the manager with the mock audit logger
    manager = AuthedManager(
        config=PipelineConfig(
            identity=True,
            permissions=True,
            credentials=True,
            audit=True
        ),
        audit_logger=mock_audit_logger
    )
    
    # Register mock modules
    manager.register_module(MockIdentityModule())
    manager.register_module(MockPermissionsModule())
    manager.register_module(MockCredentialsModule())
    
    # Create the audit module with the same audit logger
    audit_module = MockAuditModule()
    audit_module.audit_logger = mock_audit_logger
    manager.register_module(audit_module)
    
    # Start the modules
    await manager.start()
    
    yield manager
    
    # Clean up
    await manager.stop()


@pytest.mark.asyncio
async def test_successful_pipeline(authed_manager):
    """Test a successful request through the entire pipeline."""
    print("\n\n=== TEST: SUCCESSFUL PIPELINE ===")
    
    # Create a mock request
    request = {
        "token": "valid_token",
        "resource": "api/data",
        "action": "read"
    }
    print(f"Request: {request}")
    
    # Process the request using the manager's process_request method
    context = await authed_manager.process_request(request)
    
    print("\n=== FINAL CONTEXT DATA ===")
    for key, value in context.data.items():
        print(f"  {key}: {value}")
    
    # Verify successful pipeline execution
    assert context is not None
    
    # Identity module should have resolved an identity
    assert "agent_id" in context.data
    assert "identity" in context.data
    
    # Permissions module should have granted access
    assert "has_access" in context.data
    assert context.data["has_access"] is True
    
    # Credentials module should have provided credentials
    assert "credential" in context.data
    assert "credential_id" in context.data
    
    # Audit module should have logged the request
    assert "audit_id" in context.data


@pytest.mark.asyncio
async def test_invalid_identity(authed_manager):
    """Test pipeline with invalid identity token."""
    # Create a mock request with invalid token
    request = {
        "token": "invalid_token",
        "resource": "api/data",
        "action": "read"
    }
    
    # Process should raise an IdentityError
    with pytest.raises(AuthedError) as excinfo:
        await authed_manager.process_request(request)
    
    # Verify the error is from identity module
    assert "identity" in str(excinfo.value)


@pytest.mark.asyncio
async def test_permission_denied(authed_manager):
    """Test pipeline with valid identity but insufficient permissions."""
    # Create a mock request with valid token but accessing restricted resource
    request = {
        "token": "valid_token",
        "resource": "api/admin",  # Restricted resource
        "action": "write"
    }
    
    # Process should raise a PermissionValidation
    with pytest.raises(AuthedError) as excinfo:
        await authed_manager.process_request(request)
    
    # Verify the error is from permissions module
    assert "permissions" in str(excinfo.value)


@pytest.mark.asyncio
async def test_missing_credentials(authed_manager):
    """Test pipeline with valid identity and permissions but missing credentials."""
    # Create a mock request requiring unavailable credentials
    request = {
        "token": "valid_token",
        "resource": "api/external",
        "action": "read",
        "credential_type": "missing_type"
    }
    
    # Process should raise a CredentialError
    with pytest.raises(AuthedError) as excinfo:
        await authed_manager.process_request(request)
    
    # Verify the error is from credentials module
    assert "credentials" in str(excinfo.value)


@pytest.mark.asyncio
async def test_custom_pipeline_config():
    """Test customizing the pipeline configuration."""
    # Create a mock audit logger first
    mock_audit_logger = MockAuditLogger()
    
    # Create a manager with only identity and audit enabled
    manager = AuthedManager(config=PipelineConfig(
        identity=True,
        permissions=False,
        credentials=False,
        audit=True
    ), audit_logger=mock_audit_logger)
    
    # Register only the necessary modules
    manager.register_module(MockIdentityModule())
    manager.register_module(MockAuditModule())
    
    await manager.start()
    
    try:
        # Create a mock request
        request = {
            "token": "valid_token",
            "resource": "api/data",
            "action": "read"
        }
        
        # Process the request
        context = await manager.process_request(request)
        
        # Verify only enabled modules were executed
        assert "agent_id" in context.data  # Identity was processed
        assert "has_access" not in context.data  # Permissions was skipped
        assert "credential" not in context.data  # Credentials was skipped
        assert "audit_id" in context.data  # Audit was processed
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_audit_trail():
    """Test that the audit trail correctly captures pipeline execution."""
    # Create a mock audit logger first
    mock_audit_logger = MockAuditLogger()
    
    # Create the manager with the mock audit logger
    manager = AuthedManager(
        config=PipelineConfig(
            identity=True,
            permissions=True,
            credentials=True,
            audit=True
        ),
        audit_logger=mock_audit_logger
    )
    
    # Register mock modules
    manager.register_module(MockIdentityModule())
    manager.register_module(MockPermissionsModule())
    manager.register_module(MockCredentialsModule())
    
    # Create the audit module with the same audit logger
    audit_module = MockAuditModule()
    audit_module.audit_logger = mock_audit_logger
    manager.register_module(audit_module)
    
    # Start the modules
    await manager.start()
    
    try:
        # Process a successful request
        request = {
            "token": "valid_token",
            "resource": "api/data",
            "action": "read"
        }
        
        print("\n=== TESTING AUDIT TRAIL FUNCTIONALITY ===")
        context = await manager.process_request(request)
        
        # Verify audit records were created
        print("\n=== CHECKING AUDIT RECORDS ===")
        records = await mock_audit_logger.query_records()
        print(f"Found {len(records)} audit records")
        
        # There should be at least one record (from start() call in each module)
        assert len(records) > 0, "No audit records were created"
        
        # The most recent record should have the same run_id as the context
        latest_record = records[-1]
        print(f"Latest record run_id: {latest_record.run_id}")
        print(f"Context audit_id: {context.data['audit_id']}")
        
        # The audit module should use the context's run_id for consistent tracking
        assert latest_record.run_id == context.run_id, "Audit record run_id doesn't match context run_id"
        assert context.data["audit_id"] == context.run_id, "Context audit_id doesn't match context run_id"
        
        # Check events logged during processing
        print("\n=== CHECKING AUDIT EVENTS ===")
        events = mock_audit_logger.events
        print(f"Found {len(events)} audit events")
        
        # Store the current event count
        event_count_before_failure = len(events)

        # There should be at least one event per module
        assert len(events) > 0, "No audit events were logged"

        # Print a summary of logged events
        for i, event in enumerate(events):
            print(f"Event {i+1}: {event['event_type']} - {event['attributes']}")
        
        # Process a failing request to ensure errors are audited
        print("\n=== TESTING AUDIT TRAIL FOR FAILED REQUEST ===")
        failing_request = {
            "token": "invalid_token",
            "resource": "api/data",
            "action": "read"
        }
        
        try:
            await manager.process_request(failing_request)
        except Exception as e:
            print(f"Expected exception occurred: {type(e).__name__}: {str(e)}")
            
        # Check that new events were logged for the failure
        new_events_count = len(mock_audit_logger.events)
        print(f"Total events after failure: {new_events_count}")
        print(f"Events before failure: {event_count_before_failure}")
        assert new_events_count > event_count_before_failure, "No new events were logged for the failed request"
        
        # Check for error events
        error_events = [e for e in mock_audit_logger.events if "error" in str(e).lower() or "fail" in str(e).lower()]
        print(f"Found {len(error_events)} error-related events")
        assert len(error_events) > 0, "No error events were logged for the failed request"
        
        print("\n=== AUDIT TRAIL VERIFICATION COMPLETE ===")
    
    finally:
        # Clean up
        await manager.stop() 