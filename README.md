# NAVO: Microsoft Teams Knowledge Discovery Bot
> A lightweight AI-powered Teams bot that answers engineering questions by pulling content from Confluence and SharePoint using GPT.

[![Production](https://img.shields.io/badge/Production-Ready-brightgreen)](https://github.com/mj3b/navo)
[![Teams](https://img.shields.io/badge/Microsoft-Teams-blue)](https://teams.microsoft.com)
[![Confluence](https://img.shields.io/badge/Confluence-Cloud-blue)](https://www.atlassian.com/software/confluence)
[![SharePoint](https://img.shields.io/badge/SharePoint-Online-blue)](https://www.microsoft.com/en-us/microsoft-365/sharepoint)

**NAVO brings your documentation to where work happens.** Ask questions in Microsoft Teams and get instant answers from your Confluence and SharePoint documentation, powered by Enterprise GPT.

---

## Quick Start

### Prerequisites
- Microsoft Teams with bot deployment permissions
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

---

## Configuration

### Enterprise GPT
```env
OPENAI_API_KEY=your_enterprise_gpt_key
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

### Microsoft Teams
```env
TEAMS_APP_ID=your_teams_app_id
TEAMS_APP_PASSWORD=your_teams_app_password
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
- Confidence scoring and adaptive learning (Phase 2+ ready)
- Action buttons for instant follow-up

---

## Architecture

```
Microsoft Teams → NAVO Bot → Query Processor → [Confluence + SharePoint] → Enterprise GPT → Adaptive Card Response
```

**Technology Stack:**  
Enterprise GPT · Microsoft Teams · FastAPI · Confluence Cloud · SharePoint Online · Redis

---

## Quick Test (Optional)
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Where is the retry logic for QLAB02?"}'
```

---

## About
NAVO is an enterprise knowledge discovery platform that transforms documentation search into proactive knowledge orchestration. It features:

- AI-powered conversational interface
- Transparent reasoning and memory (Phase 2+)
- Integration with Confluence & SharePoint using Enterprise GPT

---

## Topics
`python` `nlp` `docker` `enterprise` `flask` `oauth` `machine-learning` `microservices` `rest-api` `sharepoint` `confluence` `semantic-search` `knowledge-management` `enterprise-search` `ai-search`

---

## Maintainers
- [@mj3b](https://github.com/mj3b) — Creator & Maintainer
- [@dependabot](https://github.com/dependabot[bot]) — Dependency automation

---

**NAVO knows where it's written.**  
Navigate + Ops = Better documentation discovery.
