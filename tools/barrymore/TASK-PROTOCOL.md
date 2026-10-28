# Barrymore Task Protocol

Version:
0.1


## Purpose

A task is the primary instruction artifact for Barrymore.

Barrymore does not operate from informal commands alone.
Every meaningful action must have a documented task.


## Task Lifecycle

1. Read task file.
2. Validate task format.
3. Validate allowed actions.
4. Create execution plan.
5. Request approval.
6. Execute approved actions.
7. Generate report.
8. Preserve history.


## Safety Rules

Barrymore must:

- follow explicit instructions;
- respect permissions;
- create execution reports;
- preserve audit trail.


Barrymore must not:

- invent permissions;
- perform destructive actions;
- modify unrelated components;
- bypass approval.


## Human Authority

Human approval remains the highest authority.