package authz

# Default deny
default allow = false

# Allow users to access resources they own
allow = true if {
    input.method == "GET"
    input.path = ["resources", resource_id]
    input.user.id == data.resources.resources[resource_id].owner
}

# Allow admins to access any resource
allow = true if {
    input.method == "GET"
    input.path = ["resources", _]
    input.user.role == "admin"
} 