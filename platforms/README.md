# Platforms

This directory contains individual platform implementations following the GL naming convention: **gl.{domain}.{capability}-platform**.

## Platform Naming Convention

All platforms follow the format: `gl.{domain}.{capability}-platform`

- **domain**: Platform semantic domain (ai, runtime, api, design, ide, edge, etc.)
- **capability**: Platform core capability or specialized function (gpt, supabase, figma, copilot, etc.)
- **-platform**: Fixed suffix indicating platform-level resource

## Available Platforms

### Runtime Platforms (gl.runtime.*)
- **gl.runtime.core-platform**: 核心執行時平台
- **gl.runtime.sync-platform**: 資料同步平台（esync）
- **gl.runtime.quantum-platform**: 量子運算執行平台
- **gl.runtime.build-platform**: 建構與 CI 執行平台（earthly）

### Development Platforms (gl.dev.*)
- **gl.dev.iac-platform**: 基礎建設即程式碼（terraform）
- **gl.dev.review-platform**: 程式碼審查平台

### API Platforms (gl.api.*)
- **gl.api.supabase-platform**: Supabase 資料 API 平台
- **gl.api.notion-platform**: Notion API 整合平台

### Documentation Platforms (gl.doc.*)
- **gl.doc.gitbook-platform**: GitBook 文件平台

### Design Platforms (gl.design.*)
- **gl.design.figma-platform**: Figma 設計平台
- **gl.design.sketch-platform**: Sketch 元件平台

### IDE Platforms (gl.ide.*)
- **gl.ide.copilot-platform**: GitHub Copilot IDE 插件
- **gl.ide.vscode-platform**: VSCode 擴充平台
- **gl.ide.replit-platform**: Replit Ghostwriter
- **gl.ide.preview-platform**: CodePen 預覽平台

### Edge Platforms (gl.edge.*)
- **gl.edge.vercel-platform**: Vercel 邊緣部署平台

### Web Platforms (gl.web.*)
- **gl.web.wix-platform**: Wix 前端建站平台

### Database Platforms (gl.db.*)
- **gl.db.planetscale-platform**: PlanetScale 雲端資料庫

### AI Platforms (gl.ai.*)
- **gl.ai.gpt-platform**: OpenAI GPT 模型平台
- **gl.ai.claude-platform**: Anthropic Claude 模型平台
- **gl.ai.deepseek-platform**: DeepSeek MOE 模型平台
- **gl.ai.blackbox-platform**: Blackbox AI 平台
- **gl.ai.agent-platform**: MaxAgent 智能代理平台
- **gl.ai.unified-platform**: All-in-One AI 整合平台
- **gl.ai.realtime-platform**: Grok 即時 AI 平台
- **gl.ai.slack-platform**: Slack AI 整合平台
- **gl.ai.csdn-platform**: CSDN AI 平台

## NG Era Consolidation

Legacy NG era platform artifacts (cross-era meta, Era-1/2/3 stacks) are now grouped under `platforms/ng-era-platforms/`. See `platforms/ng-era-platforms/README.md` for layout and audit/replay guidance.

### MCP Platforms (gl.mcp.*)
- **gl.mcp.multimodal-platform**: 多模態控制平台
- **gl.mcp.cursor-platform**: Cursor AI 編輯器平台

### Education Platforms (gl.edu.*)
- **gl.edu.sololearn-platform**: SoloLearn 教育平台

### Bot Platforms (gl.bot.*)
- **gl.bot.poe-platform**: Poe 對話機器人平台

## Platform Structure

Each platform follows a standardized structure:

```
gl.{domain}.{capability}-platform/
├── src/              # Source code
├── configs/          # Configuration files
├── docs/             # Platform documentation
├── tests/            # Test suites
├── deployments/      # Deployment configurations
├── governance/       # Platform-specific governance
├── services/         # Platform services
└── data/             # Platform data schemas
```

## Platform Independence

Each platform is designed to operate independently while maintaining:
- Consistent governance compliance
- Standardized structure
- Cross-platform coordination capability
- Service discovery integration
- Data synchronization support

## Platform Registration

All platforms are registered in `ecosystem/registry/platform-registry/platform-manifest.yaml`

## Platform Metadata

Each platform includes metadata:
- **gl.platform.id**: Unique platform identifier
- **gl.platform.version**: Platform version
- **gl.platform.owner**: Platform owner
- **gl.platform.lifecycle**: Platform lifecycle status

## Platform Naming Compliance

All platforms comply with GL naming ontology:
- Unique `gl.platform.{domain}.{capability}` namespace
- At least one corresponding `gl.component`, `gl.api`, `gl.resource` namespace
- Metadata tracking for lifecycle and governance

## Platform Marketplace

Consumers can:
1. Browse available platforms in `platforms/` directory
2. Select platforms based on domain and capability
3. Purchase/subscribe to desired platforms
4. Deploy selected platforms independently

## Platform Governance

Each platform implements:
- GL enterprise architecture (GL00-09)
- Boundary enforcement (GL60-80)
- Meta specifications (GL90-99)
- Extension framework (GL81-83)

## Creating New Platforms

To add a new platform:
1. Choose appropriate domain and capability
2. Follow naming convention: `gl.{domain}.{capability}-platform`
3. Create platform directory with standard structure
4. Register platform in `ecosystem/registry/platform-registry/`
5. Implement platform-specific services
6. Configure coordination systems
7. Test platform independence
8. Update documentation

---

**GL Compliance**: Yes  
**Naming Convention**: gl.{domain}.{capability}-platform  
**Total Platforms**: 31  
**Status**: Active  
**Consumer Marketplace**: Available for selection and purchase
