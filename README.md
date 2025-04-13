<div align="center">
# Authed Permissions

**Runtime access control layer for secure agent-to-agent interactions**

[![license MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/authed-dev/authed/pulls)
[![support](https://img.shields.io/badge/support-contact%20author-purple.svg)](https://github.com/authed-dev/authed/issues)
[![PyPI Downloads](https://img.shields.io/pypi/dm/authed)](https://pypi.org/project/authed/)

Authed | [Docs]()
</div>
> **Note**: Authed Permissions is now the core focus of this repository. For identity and authentication, see [Authed Identity](https://github.com/authed-dev/authed-identity).

## Overview

As AI agents become more autonomous and interconnected, managing what they can access and do becomes critical. Authed Permissions offers a natural language approach to defining, enforcing, and managing permissions between agents and resources.

### Key capabilities

#### Natural language rules

Write permission rules in an intuitive syntax that's both human-readable and machine-parsable:

```
GIVE READ ACCESS TO EMAILS WITH TAGS = WORK
DENY WRITE ACCESS TO ISSUES ASSIGNED TO = john@example.com
```

#### Flexible resource model

The permissions system adapts to virtually any resource type with custom fields and conditions, making it ideal for agents that need to access diverse data sources and APIs.

#### Extensible integrations

Easily add new data sources and APIs by defining integration mapping rules that translate between external schemas and permission statements.

#### Real-time evaluation

Optimized for rapid permission checks without compromising security, ensuring agents can make quick decisions with proper authorization.

## Working with agents?

**We'd love to hear from you!** If you're:

- Building with MCP
- Building AI agents that need fine-grained access control
- Developing an agent building platform
- Creating integration tools that connect agents to external services

Visit [getauthed.dev](https://getauthed.dev) and book a call with our team.

## Roadmap

Stay tuned for upcoming features including enhanced condition expressions, permission groups, role-based access control, audit logging, and performance optimizations.

## License

MIT

<div align="center">
Made with ❤️ in Warsaw, Poland and SF
</div>