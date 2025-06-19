# NAVO: Microsoft Teams Knowledge Discovery Bot

**NAVO** is your AI-powered teammate for documentation clarity. Designed for engineering teams, NAVO turns natural language queries into precise, sourced answers from Confluence and SharePoint—right inside Microsoft Teams.

> **NAVO knows where it's written.**  
> It's not just documentation search—it's documentation orchestration.

Built with Enterprise GPT integration and Microsoft Bot Framework, NAVO enhances productivity by bringing tribal knowledge, sprint specs, and production playbooks to where work happens.

[![Production](https://img.shields.io/badge/Production-Ready-brightgreen)](https://github.com/mj3b/navo)
[![Teams](https://img.shields.io/badge/Microsoft-Teams-blue)](https://teams.microsoft.com)
[![Bot Framework](https://img.shields.io/badge/Bot%20Framework-4.15-blue)](https://dev.botframework.com/)
[![Confluence](https://img.shields.io/badge/Confluence-Cloud-blue)](https://www.atlassian.com/software/confluence)
[![SharePoint](https://img.shields.io/badge/SharePoint-Online-blue)](https://www.microsoft.com/en-us/microsoft-365/sharepoint)

---

## Quick Start

### Prerequisites
- Microsoft Teams with bot deployment permissions
- Azure subscription with Bot Service capability
- Confluence Cloud instance with API access
- SharePoint Online with Microsoft Graph API access
- Enterprise GPT API access
- Python 3.11+

### Installation
```bash
git clone https://github.com/mj3b/navo.git
cd navo
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python main.py
```

### Teams Bot Registration
1. Create Azure Bot Service resource
2. Configure messaging endpoint: `https://your-domain.com/api/messages`
3. Get App ID and App Password
4. Update `.env` with Teams credentials

**Full deployment guide**: [TEAMS_DEPLOYMENT.md](./TEAMS_DEPLOYMENT.md)

---

## Configuration

### Microsoft Teams Bot Framework
```env
TEAMS_APP_ID=your-teams-app-id
TEAMS_APP_PASSWORD=your-teams-app-password
```

### Enterprise GPT
```env
OPENAI_API_KEY=your-enterprise-gpt-key
OPENAI_API_BASE=https://your-enterprise-gpt-endpoint
```

### Confluence Cloud
```env
CONFLUENCE_CLOUD_URL=https://yourcompany.atlassian.net
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token
```

### SharePoint Online
```env
SHAREPOINT_TENANT_ID=your_tenant_id
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/yoursite
```

### Local Docs (optional)
```env
LOCAL_DOCS_PATH=/path/to/local/docs
```

> **Ensure your Enterprise GPT endpoint supports OpenAI-compatible responses.**

---

## Example Usage
```text
@NAVO Where's the API documentation?
@NAVO How do I configure the deployment pipeline?
@NAVO What's our troubleshooting guide for production issues?
```

NAVO responds with:
- GPT-augmented answers from trusted documentation
- Confluence + SharePoint links with freshness indicators
- Interactive adaptive cards with action buttons
- Confidence scoring and source attribution

---

## How It Works

1. **Ask a question** in Teams (personal, group, or channel)
2. **NAVO searches** Confluence & SharePoint using Microsoft APIs
3. **Enterprise GPT processes** the content and generates answers
4. **You get a rich response** with sources, confidence, and actions

### Microsoft Teams Integration
- **Bot Framework 4.15**: Official Microsoft Bot Framework SDK
- **Adaptive Cards v1.4**: Rich, interactive response cards
- **Multi-scope support**: Personal chats, group chats, and channels
- **@mention handling**: Responds to direct mentions in Teams
- **Welcome messages**: Onboarding for new users

---

## Architecture

```
Microsoft Teams → Bot Framework → NAVO Bot → Query Processor → [Confluence + SharePoint] → Enterprise GPT → Adaptive Card Response
```

**Technology Stack:**  
Microsoft Bot Framework · Enterprise GPT · FastAPI · aiohttp · Confluence Cloud API · Microsoft Graph API · Adaptive Cards

### Microsoft Compliance
- ✅ **Bot Framework SDK**: Official Microsoft botbuilder-core
- ✅ **Teams Activity Handler**: Proper Teams-specific event handling  
- ✅ **Adaptive Cards v1.4**: Latest adaptive card specification
- ✅ **Multi-scope support**: Personal, team, and group chat scopes
- ✅ **Security**: OAuth2 and secure token handling

---

## Codebase Overview

NAVO is intentionally small and easy to navigate. The important modules are:

| File | Purpose |
|------|---------|
| `main.py` | aiohttp server and Bot Framework adapter setup |
| `bot.py` | Teams bot logic and message handling |
| `query_processor.py` | Coordinates searches and GPT prompts |
| `confluence_client.py` | Confluence Cloud search client |
| `sharepoint_client.py` | SharePoint Graph search client |
| `local_docs_client.py` | Optional local docs search (Markdown/text) |
| `adaptive_cards.py` | Builds Teams Adaptive Cards |

Each component can be extended or replaced. For example, you can implement a new
knowledge source client and register it in `query_processor.py`. The card layout
and actions are defined in `adaptive_cards.py` and can be tailored to your
organization's style.

---

## Feature Roadmap

| Phase | Feature Highlights                                        | Status       |
|-------|-----------------------------------------------------------|--------------|
| 1     | Natural language querying + GPT answers + source links    | ✅ Completed |
| 2     | Confidence scoring, freshness indicators, reasoning trace | 🚧 In Progress |
| 3     | Feedback loop and adaptive learning                       | 🔜 Planned    |

---

## API Endpoints

### Teams Webhook
```
POST /api/messages
```
Microsoft Teams webhook endpoint for bot messages.

### Health Check
```
GET /health
```
Service health and component status.

### Direct Query API (Optional)
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Where is the retry logic for QLAB02?"}'
```

---

## Deployment

### Docker
```bash
docker build -t navo-teams-bot .
docker run -p 8000:8000 --env-file .env navo-teams-bot
```

### Azure App Service
```bash
az webapp create --resource-group myRG --plan myPlan --name navo-bot --runtime "PYTHON|3.11"
az webapp config appsettings set --resource-group myRG --name navo-bot --settings @.env
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: navo-teams-bot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: navo-teams-bot
  template:
    spec:
      containers:
      - name: navo-teams-bot
        image: navo-teams-bot:latest
        ports:
        - containerPort: 8000
```

For step-by-step instructions on registering the bot in Azure and packaging the Teams app, see **[TEAMS_DEPLOYMENT.md](./TEAMS_DEPLOYMENT.md)**.

---

## Microsoft Teams App Package

### Files Included
- `manifest.json`: Teams app manifest (v1.16)
- `color.png`: 192x192 app icon
- `outline.png`: 32x32 outline icon

### Installation
1. Update `manifest.json` with your Bot App ID
2. Create app package: `zip -r navo-teams-app.zip manifest.json *.png`
3. Upload to Teams Admin Center
4. Install in your organization

---

## About
NAVO is an enterprise knowledge discovery platform that transforms documentation search into proactive knowledge orchestration. It features:

- **AI-powered conversational interface** using Enterprise GPT
- **Microsoft Teams native integration** with Bot Framework
- **Transparent reasoning and memory** (Phase 2+)
- **Enterprise security** with OAuth2 and secure token handling
- **Multi-source integration** with Confluence & SharePoint APIs

### Microsoft Teams Bot Categories
NAVO fits perfectly into Microsoft's recommended bot types:
- ✅ **Q&A Bots**: Answers user questions from documentation
- ✅ **Information Retrieval Bots**: Accesses external enterprise systems
- ✅ **Workflow Bots**: Initiates knowledge discovery workflows
- ✅ **Enterprise Bots**: Connects to business-critical data sources

---

## Topics
`microsoft-teams` `bot-framework` `python` `nlp` `docker` `enterprise` `oauth` `machine-learning` `microservices` `rest-api` `sharepoint` `confluence` `semantic-search` `knowledge-management` `enterprise-search` `ai-search` `adaptive-cards`

---

## Maintainers
- [@mj3b](https://github.com/mj3b) — Creator & Maintainer
- [@dependabot](https://github.com/dependabot[bot]) — Dependency automation

---

## Support
- **Documentation**: [GitHub Repository](https://github.com/mj3b/navo)
- **Issues**: [GitHub Issues](https://github.com/mj3b/navo/issues)
- **Deployment Guide**: [TEAMS_DEPLOYMENT.md](./TEAMS_DEPLOYMENT.md)
- **Microsoft Teams Platform**: [Teams Developer Documentation](https://docs.microsoft.com/en-us/microsoftteams/platform/)

---

**NAVO knows where it's written.**  
Navigate + Ops = Better documentation discovery.

*Built with ❤️ for engineering teams using Microsoft Teams*

