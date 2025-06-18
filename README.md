# NAVO: Microsoft Teams Knowledge Discovery Bot

[![Production](https://img.shields.io/badge/Production-Ready-brightgreen)](https://github.com/mj3b/navo)
[![Teams](https://img.shields.io/badge/Microsoft-Teams-blue)](https://teams.microsoft.com)
[![Confluence](https://img.shields.io/badge/Confluence-Cloud-blue)](https://www.atlassian.com/software/confluence)
[![SharePoint](https://img.shields.io/badge/SharePoint-Online-blue)](https://www.microsoft.com/en-us/microsoft-365/sharepoint)

**NAVO brings your documentation to where work happens.** Ask questions in Microsoft Teams and get instant answers from your Confluence and SharePoint documentation, powered by Enterprise GPT.

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

## Configuration

```bash
# Enterprise GPT
OPENAI_API_KEY=your_enterprise_gpt_key
OPENAI_API_BASE=https://your-enterprise-gpt-endpoint

# Confluence Cloud
CONFLUENCE_CLOUD_URL=https://yourcompany.atlassian.net
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token

# SharePoint Online
SHAREPOINT_TENANT_ID=your_tenant_id
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/yoursite

# Teams
TEAMS_APP_ID=your_teams_app_id
TEAMS_APP_PASSWORD=your_teams_app_password
```

## Architecture

Simple, focused architecture for Teams integration:

```
Microsoft Teams → NAVO Bot → Query Processor → [Confluence + SharePoint] → Enterprise GPT → Adaptive Card Response
```

## Example Usage

```
@NAVO Where's the API documentation?
@NAVO How do I configure the deployment pipeline?
@NAVO What's our troubleshooting guide for production issues?
```

## Teams Integration

NAVO responds with rich adaptive cards containing:
- AI-generated answer based on documentation
- Source attribution with direct links
- Document metadata (last modified, confidence score)
- Action buttons (View Document, Provide Feedback)

---

**NAVO knows where it's written.** Navigate + Ops = Better documentation discovery.

