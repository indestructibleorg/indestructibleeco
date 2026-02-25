# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# AEP Engine Governance & Audit App

> Mobile application for AEP Engine governance auditing and monitoring

[![GL Charter]([EXTERNAL_URL_REMOVED])]([EXTERNAL_URL_REMOVED])
[![Expo]([EXTERNAL_URL_REMOVED])]([EXTERNAL_URL_REMOVED])
[![React Native]([EXTERNAL_URL_REMOVED])]([EXTERNAL_URL_REMOVED])

## Overview

The AEP Engine Governance & Audit App is a React Native/Expo mobile application that provides a user interface for:

- **Governance Auditing**: Execute and monitor governance audits on the AEP Engine
- **Detection Results**: View and analyze detected issues with severity classification
- **Global Reports**: Access comprehensive governance audit reports
- **Settings Management**: Configure audit parameters and preferences

## Features

### 📊 Dashboard (Home)
- Overview statistics (total files, issues, events)
- Quick access to recent audit results
- Real-time status indicators

### 🔍 Audit Execution
- Start new governance audits
- Monitor audit progress
- View audit history

### 📋 Detection Results
- Issue list with severity levels (P0-P3)
- Filter by issue type
- Detailed issue information

### 📈 Global Reports
- Comprehensive audit summaries
- Governance event stream
- Export capabilities

### ⚙️ Settings
- Audit configuration
- Notification preferences
- Theme settings

## Project Structure

```
aep-engine-app/
├── app/                    # Expo Router pages
│   ├── (tabs)/            # Tab navigation screens
│   │   ├── index.tsx      # Home/Dashboard
│   │   ├── audit.tsx      # Audit Execution
│   │   ├── results.tsx    # Detection Results
│   │   ├── report.tsx     # Global Reports
│   │   └── settings.tsx   # Settings
│   ├── _layout.tsx        # Root layout
│   ├── dev/               # Development tools
│   └── oauth/             # OAuth callback
├── components/            # Reusable components
│   └── ui/               # UI components
│       ├── statistic-card.tsx
│       ├── event-card.tsx
│       └── problem-card.tsx
├── constants/            # App constants
├── hooks/               # Custom React hooks
├── assets/              # Images and icons
├── scripts/             # Build scripts
├── app.config.ts        # Expo configuration
└── package.json         # Dependencies
```

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm 9.12+
- Expo CLI

### Installation

```bash
cd aep-engine-app
pnpm install
```

### Development

```bash
# Start development server
pnpm dev

# Start Metro bundler only
pnpm dev:metro

# Start on iOS
pnpm ios

# Start on Android
pnpm android
```

### Build

```bash
# Type check
pnpm check

# Lint
pnpm lint

# Format
pnpm format

# Test
pnpm test
```

## GL Metadata

```json
{
  "layer": "GL70-89",
  "component": "Presentation Layer",
  "charter-activated": true,
  "semantic-anchor": "ECO-70-PRESENTATION-APP"
}
```

## Integration with AEP Engine

This app integrates with the AEP Engine (`/engine`) to:

1. Trigger governance audits via API
2. Fetch audit results and reports
3. Display governance event streams
4. Manage audit configurations

## License

MIT License - see [LICENSE](../LICENSE) for details.