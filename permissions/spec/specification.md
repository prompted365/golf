# Official Low-Level Specification

**Version:** 0.1.1

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

Dynamic models declare integration-specific objects and **MAY** vary by environment or user.

```yaml
integration_objects:
  gmail:
    EMAILS:
      - recipient: email_address
      - sender: email_address
      - sender_domain: domain
      - date_received: datetime
      - subject: string
      - tags: tags
      - attachments: boolean
    ATTACHMENTS:
      - filename: string
      - size: number
      - mime_type: string
  linear:
    ISSUES:
      - issue_id: string
      - title: string
      - description: string
      - assignee: user
      - status: string
      - labels: tags
      - created_date: datetime
      - updated_date: datetime
    TEAMS:
      - team_id: string
      - name: string
      - owner: user
```

**Requirement:** Each integration's resource definitions **MUST** be declared in a consistent format so that the system can correctly apply conditions.

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

This concludes the normative low-level specification. All future modifications **SHOULD** update the version and document changes in this final section. 