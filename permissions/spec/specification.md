# Official Low-Level Specification

**Version:** 0.3.0

**Status:** Draft

This specification provides a **normative** reference for the core data models, grammar, and integration approach within the extensible permission system. It uses **MUST**, **SHOULD**, **MAY** in accordance with [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) to clarify requirements.

---

## 1. **Introduction**

This document standardizes how permissions **MUST** be declared, stored, and evaluated. By separating user-facing language from underlying engine logic, the system **SHOULD** maintain a consistent, maintainable pipeline from natural or semi-structured expressions to enforceable policies.

---

## 2. **Layered Architecture Overview**

```
Natural Language / Semi-structured Expressions
                ↓
Structured Permission Language
                ↓
API Parameter Mapper & Translator
                ↓
Open Policy Agent (OPA) ⇄ Rego
                ↑↓
        Request / Response
```

1. **Natural or Semi-structured Expressions** – The input statements.
2. **Structured Permission Language** – A well-defined intermediate form.
3. **API Parameter Mapper & Translator** – Converts statements into integration-specific parameters.
4. **OPA Engine** – Evaluates final policies, returning **allow** or **deny**.
5. **Request/Response** – Surfaces the authorization result.

**Requirement:** Implementations **MUST** preserve the separation of these layers.

---

## 3. **Data Models**

All data models **MUST** follow this specification.

### 3.1 Static Data Models

Static data models define fundamental grammar, operators, and data types. They **MUST NOT** change at runtime.

**A. Core Structure Keywords**

```yaml
base_commands:
  - GIVE
  - DENY
  - ACCESS TO

permissions:
  - READ
  - WRITE
  - DELETE
```

> **Note:** Combining permissions (e.g., "READ & WRITE") **SHOULD** be handled by referencing multiple low-level permissions.

**B. Operators**

```yaml
condition_operators:
  equality:
    - IS (=)
    - IS NOT (!=)
    - CONTAINS
  comparison:
    - GREATER THAN (>)
    - LESS THAN (<)
    - GREATER OR EQUAL (>=)
    - LESS OR EQUAL (<=)
    - BEFORE (< datetime)
    - AFTER (> datetime)
  logical:
    - AND
    - OR
    - NOT
```

**Implementation Detail:** Implementations **MUST** interpret these operators consistently in both policy generation and evaluation.

**C. Structural Helpers**

```yaml
structure_helpers:
  - WITH
  - NAMED
  - ASSIGNED_TO   # Displayed as "ASSIGNED TO" in input
  - ACCESS_TO     # Displayed as "ACCESS TO" in input
  - TAGGED
  - FROM
```

> **Note:** Multi-word helpers such as "ASSIGNED TO" MUST be normalized to underscore-separated forms (e.g., "ASSIGNED_TO") in the internal structured representation. Tokenizers SHOULD recognize the natural phrase and convert it accordingly.

**D. Generalized Data Types**

```yaml
data_types:
  - datetime
  - email_address
  - user        # identity-bearing actor (e.g., assignee, sender, owner)
  - string      # default for labels, names, IDs
  - tags        # lists of strings for categorization
  - boolean     # maps to Pydantic bool
  - number      # maps to Pydantic int/float
```

**Requirement:** The system **SHOULD** use these data types as canonical references in policy rules.

---

### 3.2 Dynamic Data Models

Dynamic models declare integration-specific resources and their fields. They **MUST** define how external parameters map to internal permission fields and associated data types.

```yaml
integration_objects:
  gmail:
    EMAILS:
      recipient:
        permission_field: recipient
        data_type: email_address
      sender:
        permission_field: sender
        data_type: email_address
      sender_domain:
        permission_field: sender_domain
        data_type: domain
      date_received:
        permission_field: date
        data_type: datetime
      subject:
        permission_field: name
        data_type: string
      tags:
        permission_field: tags
        data_type: tags
      attachments:
        permission_field: attachments
        data_type: boolean
    ATTACHMENTS:
      filename:
        permission_field: name
        data_type: string
      size:
        permission_field: size
        data_type: number
      mime_type:
        permission_field: mime_type
        data_type: string
  linear:
    ISSUES:
      issue_id:
        permission_field: id
        data_type: string
      title:
        permission_field: name
        data_type: string
      description:
        permission_field: description
        data_type: string
      assignee:
        permission_field: assignee
        data_type: user
      status:
        permission_field: status
        data_type: string
      labels:
        permission_field: tags
        data_type: tags
      created_date:
        permission_field: created_date
        data_type: datetime
      updated_date:
        permission_field: updated_date
        data_type: datetime
    TEAMS:
      team_id:
        permission_field: id
        data_type: string
      name:
        permission_field: name
        data_type: string
      owner:
        permission_field: owner
        data_type: user
```

> Implementations **MUST** use this mapping for two purposes:
>   1. Mapping external API fields to internal permission fields used in condition logic.
>   2. Resolving the canonical data type (from §3.1D) to enable proper type coercion and validation.

**Requirement:** Each integration's resource definitions **MUST** be declared in a consistent format so that the system can correctly apply conditions.

### 3.3 Field and Type Semantics

Each integration MAY include the following extensions to support semantic evaluation and type-safe condition checking:

- `_helper_mappings`: Maps structural helpers (e.g., `TAGGED`) to internal permission field names.
- `_pipelines`: Defines declarative coercion pipelines (§3.3.1) for parsing and validating values of specific data types.

> These mappings eliminate the need for hardcoded logic in the interpreter and enable full configuration-based extensibility.

### 3.3.1 Declarative Coercion Pipelines

Integration configurations MUST provide coercion pipelines for each data type requiring custom conversion logic. A pipeline consists of sequential operations that explicitly describe value transformation and validation.

**Example: Gmail Integration Pipeline Configuration**
```yaml
_pipelines:
  boolean:
    - "lowercase"
    - map_values:
        true: ["true", "yes", "on", "1"]
        false: ["false", "no", "off", "0"]
    - default: false
  
  tags:
    - split:
        separator: ","
        strip_whitespace: true
  
  email_address:
    - "validate_email_format"
```

**Pipeline Operation Details:**
| Operation               | Description                                                        |
|-------------------------|--------------------------------------------------------------------|
| `"lowercase"`           | Converts input string to lowercase.                                |
| `map_values`            | Maps listed input aliases to canonical boolean or enum outputs.    |
| `split`                 | Splits input string into a list based on the defined separator.    |
| `"validate_email_format"`| Checks input string against standard email format (RFC 5322).     |
| `default`               | Defines fallback output if no prior pipeline steps succeed.        |

Additional custom operations MAY be introduced as required by specific integrations but MUST be documented clearly within the integration's configuration.

---

## 4. **Language Specification**

Permissions **MUST** be expressible using a semi-structured grammar:

```
COMMAND PERMISSION ACCESS TO RESOURCE_TYPE [STRUCTURAL_HELPER CONDITION_OPERATOR RESOURCE_VALUE]
```

### 4.1 Examples

- `GIVE READ ACCESS TO EMAILS TAGGED = WORK`
- `DENY READ ACCESS TO EMAILS FROM DOMAIN = personal.com`
- `GIVE READ & WRITE ACCESS TO PROJECTS NAMED = BACKLOG`
- `DENY READ ACCESS TO ISSUES ASSIGNED TO ANTONI AND NAMED = "Urgent Bug"`

> **Note:** These examples rely on normalization of `"="` to `"IS"`, `"ASSIGNED TO"` to `"ASSIGNED_TO"`, and `"&"` to a separate logical token.

**Note:** Implementations **MAY** add additional structural helpers or condition operators but **SHOULD** remain backward-compatible.

### 4.2 Token Normalization Rules

To ensure robust interpretation of user input, all implementations **MUST** adhere to the following normalization behaviors during tokenization:

- Keyword and enum tokens (e.g., `GIVE`, `ASSIGNED TO`, `TAGGED`) **MUST** be matched case-insensitively.
- `"ACCESS TO"` **MUST** be recognized as a single grammar unit.
- `"ASSIGNED TO"` **MUST** be normalized to `"ASSIGNED_TO"` internally.
- `"="` **MUST** be interpreted as the condition operator `"IS"`.
- Quoted values (e.g., `"Urgent Bug"`) **MUST** be parsed with quotes stripped and inner content preserved.
- Tokenizers **MAY** skip or ignore unrecognized characters but **SHOULD** preserve parseable segments.

### 4.3 Special Symbols

- `=` is a shorthand alias for the condition operator `IS`.
- `&` **MAY** be used to visually represent conjunction (e.g., `READ & WRITE`) and **SHOULD** be tokenized as a standalone symbol.

### 4.4 Permission Parser Module

The permission parser module is responsible for converting a semi-structured natural language statement into a structured internal representation (`PermissionStatement`). It composes three layers:

1. **Tokenizer** – breaks the input string into canonical tokens.
2. **Interpreter** – identifies and organizes the logical structure (e.g., command, resource type, conditions).
3. **Statement Builder** – constructs a complete `PermissionStatement` object with appropriate typing.

#### 4.4.1 Requirements

Implementations of the parser module MUST:

- Accept a raw string as input.
- Use the tokenizer layer defined in §4.2.
- Construct valid and type-safe PermissionStatement outputs.
- Be modular: each component (tokenizer, interpreter, builder) MUST be replaceable.
- Perform field resolution and type inference using integration schema mappings (from §3.2).
- Interpreter implementations MUST NOT hardcode field-type associations or semantic field mappings.
- All type conversions and data validations MUST be delegated exclusively to the Declarative Coercion Engine (§4.4.3).
- Data type transformations MUST follow the declarative pipelines defined in integration configurations (§3.3.1).

#### 4.4.2 Asynchronous Support

The parser's main entrypoint MAY be implemented as an `async def parse_statement()` coroutine to support future extensions such as:
  - Asynchronous schema resolution from remote metadata sources
  - On-demand integration parameter fetching
  - Hybrid or AI-based natural language parsing with external APIs

Implementations SHOULD keep this method synchronous unless such I/O operations are needed.

#### 4.4.3 Declarative Coercion Engine

Implementations MUST provide a centralized **Declarative Coercion Engine** responsible for:
- Executing data-type conversion based on declarative pipeline definitions (§3.3.1).
- Merging pipeline configurations from all integrations at runtime.
- Providing standard default pipelines for common data types (`boolean`, `number`, `tags`, `email_address`) to ensure sensible baseline behavior.
- Clearly logging pipeline processing steps for debugging and auditability.

The interpreter MUST NOT perform any direct data-type conversion logic outside the coercion engine.

---

## 5. **Parameter Mapping & Translation Layer**

Implementations **MUST** translate user statements into an internal JSON structure suitable for policy evaluation.

- **Input**: e.g. `GIVE READ ACCESS TO EMAILS TAGGED = WORK`
- **Output**:

```json
{
  "input": {
    "action": "READ",
    "resource": {
      "type": "EMAILS",
      "conditions": [
        {
          "field": "tags",
          "operator": "IS",
          "value": "WORK"
        }
      ]
    }
  }
}
```

Nested fields **MAY** be referenced with dot-path syntax (e.g. `email.sender.domain`) if the integration model requires it.

**Requirement:** The translator **MUST** ensure that the final JSON is valid for OPA input.

---

## 6. **OPA & Rego Integration**

Authorization logic **SHOULD** be delegated to OPA. Policies **MUST** be valid Rego.

Example:

```rego
package auth.emails

default allow = false

allow {
    input.action == "READ"
    input.resource.type == "EMAILS"
    some tag in input.resource.tags
    tag == "WORK"
}
```

**Requirement:** A successful allow/deny decision **MUST** be returned, to be enforced by the calling system.

---

## 7. **Request/Response Workflow**

1. **API Request** – The user or service **MUST** supply resource + action.
2. **Normalization** – The system **SHOULD** convert external fields into the internal JSON.
3. **Evaluation** – The JSON **MUST** be fed to OPA for a decision.
4. **Decision** – OPA responds with allow or deny.
5. **Enforcement** – The system **MUST** enforce the decision.

---

## 8. **High-Level Modular Structure**

```
USER-FRIENDLY LANGUAGE MODULE
          ↓
LANGUAGE PARSER MODULE
          ↓
STRUCTURED STATEMENT BUILDER MODULE
          ↓
INTEGRATION PARAMETER MAPPING MODULE
          ↓
DECLARATIVE COERCION ENGINE MODULE
          ↓
JSON POLICY GENERATOR MODULE
          ↓
OPA POLICY EVALUATION MODULE
          ↓
RESULT HANDLING MODULE
```

Each module **MUST** be independently testable.

---

## 9. **Suggested File Structure**

```plaintext
permissions/
│
├── models.py
│   # Defines static/dynamic schemas & typed data models.
|
├── base.py
│   # Abstract classes and shared helpers.
|
├── parser/
│   ├── tokenizer.py
│   ├── interpreter.py
│   └── builder.py
|
├── integrations/
│   ├── gmail.py
│   └── linear.py
|
├── coercion_engine.py
|
├── engine/
│   ├── opa_client.py
│   ├── policy_generator.py
│   └── rego_templates/
│       └── auth.rego
|
└── tests/
    # Tests for all modules.
```

**Requirement:** Each directory **SHOULD** implement logic relevant to its domain (e.g., `parser/` only for statement parsing, `engine/` only for OPA interaction).

---

## 10. **Change History**

- **v0.1.0 (Draft)** – Initial version, specifying data models, grammar, and OPA integration.
- **v0.1.1 (Draft)** – Improved tokenization rules to align with the implementation:
  - Updated Structural Helpers section to use underscore format (e.g., `ASSIGNED_TO` instead of `ASSIGNED TO`)
  - Added `ACCESS_TO` to Structural Helpers 
  - Added Token Normalization Rules (Section 4.2) to document token handling behavior
  - Added Special Symbols section (Section 4.3) to document the handling of special characters
  - Added clarification note to Examples section regarding token normalization
- **v0.2.0 (Draft)** – Enhanced schema mapping and type inference:
  - Restructured Dynamic Data Models (Section 3.2) to use a more explicit mapping format
  - Added clear requirements for field mapping and type resolution
  - Added new Permission Parser Module section (Section 4.4) with explicit requirements
  - Added prohibition against hardcoding field-type associations in interpreters
- **v0.2.1 (Draft)** – Clarified asynchronous parser interface:
  - Expanded Section 4.4 with description of the parser's three-layer architecture
  - Added Section 4.4.2 about asynchronous support for the parser
  - Enhanced Section 4.4.2 with detailed documentation about the optional async nature of the parser
  - Provided rationale and use cases for when async interfaces are appropriate
  - Added guidance for implementers on when to use sync vs. async methods
- **v0.3.0 (Draft)** – Added Declarative Coercion Pipelines:
  - Added Section 3.3 for Field and Type Semantics with extensibility mappings
  - Added Section 3.3.1 introducing declarative pipeline definitions in integration mappings
  - Specified required and optional pipeline operations with detailed description table
  - Introduced Declarative Coercion Engine (Section 4.4.3) to handle all conversions centrally
  - Updated parser module (Section 4.4.1) to delegate all conversions exclusively to the coercion engine
  - Updated High-Level Modular Structure and Suggested File Structure to include coercion engine
  - Provided explicit Gmail integration configuration example demonstrating pipeline definitions

This concludes the normative low-level specification. All future modifications **SHOULD** update the version and document changes in this final section. 