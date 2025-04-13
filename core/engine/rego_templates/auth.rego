package authed.permissions.{resource_type}

# Default deny
default allow = false
default deny = false

# Grant access if allow rule matches
allow {{
    # Resource type check
    input.resource.type == "{resource_type}"
    
    # Action check
    {action_conditions}
    
    # Custom conditions
    {custom_conditions}
}}

# Deny access if deny rule matches
deny {{
    # Resource type check
    input.resource.type == "{resource_type}"
    
    # Action check
    {action_conditions}
    
    # Custom conditions
    {custom_conditions}
}} 