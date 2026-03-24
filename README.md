# asyioflow-sdk

[![CI](https://github.com/mohashari/asyioflow-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/mohashari/asyioflow-sdk/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/asyioflow-sdk)](https://pypi.org/project/asyioflow-sdk/)
[![npm](https://img.shields.io/npm/v/@asyioflow/sdk)](https://www.npmjs.com/package/@asyioflow/sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Multi-language client SDK for [AysioFlow](https://github.com/mohashari/asyioflow-engine) — a distributed workflow orchestration engine.

## SDKs

| Language | Install | Docs |
|----------|---------|------|
| Python 3.10+ | `pip install asyioflow-sdk` | [Python SDK](sdk/python/README.md) |
| TypeScript 5 | `npm install @asyioflow/sdk` | [TypeScript SDK](sdk/typescript/README.md) |

## Monorepo Structure

```
schema/          # Shared JSON Schema (source of truth for all types)
sdk/python/      # Python SDK (httpx + pydantic)
sdk/typescript/  # TypeScript SDK (axios + zod)
```

## Engine Compatibility

Requires [asyioflow-engine](https://github.com/mohashari/asyioflow-engine) v0.1.0+, running at `:8080` (REST).
