#!/bin/bash

# Testing OPA with direct file input
echo "Testing OPA - Make sure OPA server is running"

# Load policy and data into OPA server
echo "Loading policy and data into OPA server..."
curl -X PUT http://localhost:8181/v1/policies/authz --data-binary @policies/example.rego
curl -X PUT http://localhost:8181/v1/data/resources --data-binary @policies/data.json

# Test case 1: User accessing own resource (should be true)
echo -e "\nTest 1: User1 accessing their own resource (Should be true)"
curl -X POST http://localhost:8181/v1/data/authz/allow -d @input1.json -H 'Content-Type: application/json'

# Test case 2: User accessing someone else's resource (should be false)
echo -e "\nTest 2: User1 accessing someone else's resource (Should be false)"
curl -X POST http://localhost:8181/v1/data/authz/allow -d @input2.json -H 'Content-Type: application/json'

# Test case 3: Admin accessing any resource (should be true)
echo -e "\nTest 3: Admin accessing any resource (Should be true)"
curl -X POST http://localhost:8181/v1/data/authz/allow -d @input3.json -H 'Content-Type: application/json' 