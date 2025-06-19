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

### Local Documentation (optional)
```env
LOCAL_DOCS_PATH=/path/to/markdown/docs
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
- Direct links to source documents
- Confidence scores for answer reliability
- Interactive Teams adaptive cards

---

## Technology Stack

### Core Framework
- **Microsoft Bot Framework 4.15**: Enterprise-grade Teams integration
- **FastAPI**: High-performance async web framework
- **Enterprise GPT**: AI-powered response generation

### Knowledge Sources
- **Confluence Cloud API**: Atlassian documentation platform
- **Microsoft Graph API**: SharePoint Online integration
- **Local Files**: Markdown documentation support

### Deployment
- **Docker**: Containerized deployment
- **Azure Bot Service**: Cloud-native bot hosting
- **Teams Admin Center**: Enterprise app distribution

---

## Quick Test
```bash
curl -X POST http://localhost:8000/health
# Response: {"status": "healthy", "timestamp": "2025-06-19T10:30:00Z"}
```

---

## Maintainers
- [@mj3b](https://github.com/mj3b) - Core maintainer
- [@dependabot](https://github.com/dependabot) - Security updates

---

## Topics
`microsoft-teams` `confluence` `sharepoint` `enterprise-gpt` `knowledge-management` `documentation` `bot-framework` `fastapi` `python`

