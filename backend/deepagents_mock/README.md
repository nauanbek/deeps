# DeepAgents Mock Module

**Status:** Temporary mock implementation
**Purpose:** Unblock testing while real deepagents dependency is resolved
**Created:** 2025-11-11

## Overview

This module provides mock implementations of the `deepagents` package to allow tests to run while the actual package dependency is being resolved.

## Problem

The project imports `deepagents.backend`, `deepagents.middleware.subagents`, and related modules, but the `deepagents==0.2.5` package specified in `requirements.txt` is not available on PyPI or is a custom/private package.

## Solution

Created mock implementations that provide the same interface as the real deepagents package:

- `deepagents_mock/__init__.py` - `create_deep_agent()` function
- `deepagents_mock/backends.py` - Backend classes (State, Filesystem, Composite)
- `deepagents_mock/backends/store.py` - StoreBackend class
- `deepagents_mock/middleware/subagents.py` - SubAgent class

## Usage

The integration modules (`deepagents_integration/factory.py`, `backends.py`) automatically fall back to the mock if the real package is not available:

```python
try:
    from deepagents import create_deep_agent
    from deepagents.backends import BackendProtocol
except ImportError:
    from deepagents_mock import create_deep_agent
    from deepagents_mock.backends import BackendProtocol
```

## Limitations

- Mock implementations provide basic functionality only
- Agent execution returns hardcoded mock responses
- No real LLM integration in mocked mode
- Storage backends use in-memory dictionaries

## Next Steps

**Option A:** Find the real deepagents package
- Search PyPI/GitHub for official package
- Contact package maintainers
- Update requirements.txt with correct version

**Option B:** Refactor to remove dependency
- Use pure LangChain/LangGraph without deepagents wrapper
- Implement custom agent orchestration
- Remove deepagents references

**Option C:** Keep using mock (NOT RECOMMENDED for production)
- Useful for testing architecture
- Cannot run real agent executions
- Limited to mock responses

## Files

```
deepagents_mock/
├── __init__.py                      # create_deep_agent()
├── backends.py                      # Backend classes
├── backends/
│   └── store.py                     # StoreBackend
├── middleware/
│   ├── __init__.py
│   └── subagents.py                 # SubAgent class
└── README.md                        # This file
```

## TODO

- [ ] Investigate real deepagents package availability
- [ ] Decide on long-term solution (Option A, B, or C)
- [ ] Update requirements.txt if real package is found
- [ ] Remove mock once real package is integrated
- [ ] Add warnings when mock is used
