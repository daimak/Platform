# Quickstart Guide for Project Context

## Project Overview
This guide provides a high-level overview of the project structure and key files to help AI tools quickly understand the workflow and dependencies.

## Core Architecture
The project follows an island architecture model, with Barrymore as a read-only component that interacts with the system through tools. All agents never access the OS directly.

## Key Components

### Core Files
- **`eVo/dashboard/brief.js`**: Main dashboard logic and configuration.
- **`Memory/Context/CURRENT.md`**: Current project state and metadata.

### Data and Configuration
- **`tools/barrymore/logger.py`**: Custom logging utility for tracking project progress.

### Bug and Task Files
- **`/new/4/bug.txt`**: Contains bug reports or specific task details.
- **`/report`**: Directory where the output of processing bug reports should be saved.

## Workflow Summary

### Task: Update `eVo/dashboard/brief.js`
- **Input**: Data from `bug.txt` (located at `/new/4/bug.txt`).
- **Action**: Parse and integrate bug report details into `eVo/dashboard/brief.js`.
- **Output**: Updated `brief.js` file and a report saved to `/report`.

### Example Workflow
1. **Read**: Extract data from `bug.txt`.
2. **Process**: Integrate data into `eVo/dashboard/brief.js`.
3. **Save**: Output the updated `brief.js` and generate a report in `/report`.

## Key Files to Focus On
- **`eVo/dashboard/brief.js`**: Primary file for updates.
- **`/new/4/bug.txt`**: Source of bug report data.
- **`/report`**: Destination for output files.

---
**Why:** This guide ensures AI tools can quickly locate and understand the project's core files and workflows.
**How to apply:** Use this guide as a reference when asking for help with project-specific tasks.

## Overview
This guide provides a high-level overview of the project structure and key files to help AI tools quickly understand the workflow and dependencies.

## Project Structure

### Core Files
- **`eVo/dashboard/brief.js`**: Main dashboard logic and configuration.

### Data and Configuration
- **`Memory/Context/CURRENT.md`**: Current project state and metadata.

### Bug and Task Files
- **`Vision/First_evo_pictures/...`**: Image assets and visual references (e.g., `Start/Engineer.png`, `Test/Analize_syntez.png`).
- **`tools/barrymore/logger.py`**: Custom logging utility for tracking project progress.

### Bug and Report Files
- **`/new/4/bug.txt`**: Contains bug reports or specific task details.
- **`/report`**: Directory where the output of processing bug reports should be saved.

## Workflow Summary

### Task: Update `eVo/dashboard/brief.js`
- **Input**: Data from `bug.txt` (located at `/new/4/bug.txt`).
- **Action**: Parse and integrate bug report details into `eVo/dashboard/brief.js`.
- **Output**: Updated `brief.js` file and a report saved to `/report`.

### Example Workflow
1. **Read**: Extract data from `bug.txt`.
2. **Process**: Integrate data into `eVo/dashboard/brief.js`.
3. **Save**: Output the updated `brief.js` and generate a report in `/report`.

## Key Files to Focus On
- **`eVo/dashboard/brief.js`**: Primary file for updates.
- **`/new/4/bug.txt`**: Source of bug report data.
- **`/report`**: Destination for output files.

---
**Why:** This guide ensures AI tools can quickly locate and understand the project's core files and workflows.
**How to apply:** Use this guide as a reference when asking for help with project-specific tasks.