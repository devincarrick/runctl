# Architecture Decision Records

## Overview
This directory contains Architecture Decision Records (ADRs) for the RunCtl project.

## What is an ADR?
An ADR is a document that captures an important architectural decision made along with its context and consequences.

## ADR Format
Each ADR should follow this format:

```markdown
# ADR {NUMBER}: {TITLE}

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Updates
When the status changes, include the date and explanation here.
```

## ADR List
* [ADR-0000](0000-record-architecture-decisions.md) - Record Architecture Decisions
* [ADR-0001](0001-use-pydantic-v2-for-data-validation.md) - Use Pydantic V2 for Data Validation
* [ADR-0002](0002-use-localstack-for-aws-emulation.md) - Use LocalStack for AWS Emulation
* [ADR-0003](0003-data-enrichment-strategy.md) - Data Enrichment Strategy