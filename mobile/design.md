# IndestructibleEco — KUBE-1.0 ULTRA Mobile App Design

## Brand Identity

- **App Name**: IndestructibleEco
- **Tagline**: Enterprise AI Inference Platform
- **Color Palette**:
  - Primary: `#00D4FF` (Quantum Cyan — AI/tech brand)
  - Background Dark: `#0A0E1A` (Deep Navy — enterprise dark)
  - Background Light: `#F0F4FF` (Soft Blue-White)
  - Surface Dark: `#111827` (Dark Card)
  - Surface Light: `#FFFFFF`
  - Accent: `#7C3AED` (Violet — inference engine highlight)
  - Success: `#10B981` (Emerald)
  - Warning: `#F59E0B` (Amber)
  - Error: `#EF4444` (Red)
  - Muted: `#6B7280` (Gray)

## Screen List

1. **Chat** (Home Tab) — AI Inference Chat Interface
2. **Platforms** (Platforms Tab) — Platform Management Dashboard
3. **Monitor** (Monitor Tab) — Observability & Health Dashboard
4. **Settings** (Settings Tab) — Configuration & Engine Settings

## Primary Content and Functionality

### 1. Chat Screen
- Engine selector (7 engines: vLLM, TGI, SGLang, TensorRT-LLM, DeepSpeed, LMDeploy, Ollama)
- Chat message list (user + assistant bubbles)
- Input bar with send button and model selector
- Streaming response indicator
- Token count display
- Engine status badge (HEALTHY / DEGRADED / DOWN)

### 2. Platforms Screen
- Platform cards: Platform-01 (IndestructibleAutoOps), Platform-02 (IAOps), Platform-03 (MachineNativeOps)
- Each card shows: status badge, namespace, pod count, last sync time
- Quick action buttons: View Logs, Sync, Rollback
- Shared Kernel services status: Auth, Memory Hub, Event Bus, Policy & Audit, Infra Manager

### 3. Monitor Screen
- SLO dashboard: Availability %, P95 Latency, Error Rate
- Engine health grid (7 engines with status indicators)
- Active alerts list (Prometheus rules)
- Recent events feed (Kafka/Event Bus)
- Quick metrics: Requests/sec, Active Pods, Memory Usage

### 4. Settings Screen
- API Gateway URL configuration
- Active engine selection (default engine)
- Auth token management
- Theme toggle (Dark/Light)
- About section (version, repo link)

## Key User Flows

1. **AI Chat**: Chat tab → Select engine → Type message → Send → View streaming response
2. **Platform Check**: Platforms tab → Tap platform card → View pod status → Trigger sync
3. **Monitor Alert**: Monitor tab → View SLO breach → Tap alert → View details
4. **Engine Switch**: Chat tab → Tap engine badge → Engine picker modal → Select engine → Confirm

## Layout Principles

- **Dark-first design** (enterprise DevOps aesthetic)
- **Bottom tab navigation** (4 tabs)
- **Card-based layouts** for platforms and monitoring
- **Monospace font** for log/metric displays
- **Status badges** with color coding throughout
