# ADR-002: Island Architecture Model

Date:
2026-08-05

Status:
Accepted


## Context

Platform/eVo requires a unified model where:

- visual world representation
- software architecture
- runtime infrastructure

describe the same system.


The Estate artwork is not only a visual concept.
It represents the architectural structure of eVo.


## Decision

The primary architectural boundary of eVo is Island.


World

└── Island

    ├── Buildings
    │
    ├── Rooms
    │
    ├── Objects
    │
    └── Roads


Mapping:


Island
= Autonomous Application System


Building
= Software Domain


Room
= Service


Object
= Component


Docker Container
= Runtime Implementation



## Runtime Evolution


Phase 1:

Docker Compose


Phase 2:

Kubernetes


The domain model must remain independent from runtime technology.


## Principles


1. Visual entities correspond to architectural entities.

2. New capabilities are introduced as new entities.

3. Interface should discover entities instead of hardcoding them.

4. Runtime changes must not change the world model.


## Consequences


Positive:

- Visual world and software architecture stay aligned.
- Domains can evolve independently.
- Migration between runtimes is possible.


Negative:

- Requires strict boundaries.
- Requires entity registration.


## Future


Island becomes the foundation for:

- Barrymore observation
- World navigation
- Runtime monitoring
- Agent interaction