# Microsoft Teams Deployment Guide

## 🚀 **Complete Teams Bot Deployment**

This guide walks you through deploying NAVO as a Microsoft Teams bot following official Microsoft guidelines.

## 📋 **Prerequisites**

### **Required Access**
- [ ] Microsoft Teams admin permissions
- [ ] Azure subscription with Bot Service capability
- [ ] Confluence Cloud admin access
- [ ] SharePoint Online admin access
- [ ] Enterprise GPT API access

### **Development Environment**
- [ ] Python 3.11+
- [ ] Git
- [ ] Azure CLI (optional)
- [ ] Teams App Studio or Developer Portal access

## 🔧 **Step 1: Azure Bot Service Setup**

### **1.1 Create Azure Bot Resource**
```bash
# Using Azure CLI (optional)
az bot create \
  --resource-group your-resource-group \
  --name navo-teams-bot \
  --kind registration \
  --endpoint https://your-domain.com/api/messages
```

### **1.2 Manual Setup via Azure Portal**
1. Go to [Azure Portal](https://portal.azure.com)
2. Create new resource → "Bot Service"
3. Configure:
   - **Bot handle**: `navo-teams-bot`
   - **Subscription**: Your Azure subscription
   - **Resource group**: Create or select existing
   - **Pricing tier**: F0 (free) or S1 (standard)
   - **Bot template**: Echo Bot
   - **App service plan**: Create new

### **1.3 Configure Bot Settings**
1. Navigate to your bot resource
2. Go to "Configuration" 
3. Set **Messaging endpoint**: `https://your-domain.com/api/messages`
4. Save the **Microsoft App ID** and **App Password**

## 🔐 **Step 2: App Registration for SharePoint**

### **2.1 Register Application in Azure AD**
1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory
2. App registrations → New registration
3. Configure:
   - **Name**: NAVO SharePoint Integration
   - **Supported account types**: Single tenant
   - **Redirect URI**: Not required for this scenario

### **2.2 Configure API Permissions**
1. Go to "API permissions"
2. Add permissions:
   - **Microsoft Graph** → Application permissions:
     - `Sites.Read.All`
     - `Files.Read.All`
     - `User.Read.All` (optional)
3. Grant admin consent

### **2.3 Create Client Secret**
1. Go to "Certificates & secrets"
2. New client secret
3. Save the **Client ID** and **Client Secret**

## 🔑 **Step 3: Confluence API Setup**

### **3.1 Generate API Token**
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create API token
3. Save the token securely

### **3.2 Test API Access**
```bash
curl -u your-email@company.com:your-api-token \
  https://yourcompany.atlassian.net/wiki/rest/api/space
```

## 🚀 **Step 4: Deploy NAVO Backend**

### **4.1 Environment Configuration**
Create `.env` file:
```env
# Microsoft Teams Bot Framework
TEAMS_APP_ID=your-bot-app-id
TEAMS_APP_PASSWORD=your-bot-app-password

# Enterprise GPT
OPENAI_API_KEY=your-enterprise-gpt-key
OPENAI_API_BASE=https://your-enterprise-gpt-endpoint

# Confluence Cloud
CONFLUENCE_CLOUD_URL=https://yourcompany.atlassian.net
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

# SharePoint Online
SHAREPOINT_TENANT_ID=your-tenant-id
SHAREPOINT_CLIENT_ID=your-client-id
SHAREPOINT_CLIENT_SECRET=your-client-secret
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/yoursite
```

### Local Docs (optional)
```env
LOCAL_DOCS_PATH=/path/to/local/docs
```

### **4.2 Local Testing**
```bash
git clone https://github.com/mj3b/navo.git
cd navo
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python main.py
```

### **4.3 Production Deployment Options**

#### **Option A: Docker Deployment**
```bash
docker build -t navo-teams-bot .
docker run -p 8000:8000 --env-file .env navo-teams-bot
```

#### **Option B: Azure App Service**
```bash
# Deploy to Azure App Service
az webapp create \
  --resource-group your-resource-group \
  --plan your-app-service-plan \
  --name navo-teams-bot \
  --runtime "PYTHON|3.11"

# Configure environment variables
az webapp config appsettings set \
  --resource-group your-resource-group \
  --name navo-teams-bot \
  --settings @.env
```

#### **Option C: Kubernetes**
```yaml
# k8s-deployment.yaml
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
    metadata:
      labels:
        app: navo-teams-bot
    spec:
      containers:
      - name: navo-teams-bot
        image: your-registry/navo-teams-bot:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: navo-secrets
```

## 📱 **Step 5: Teams App Package Creation**

### **5.1 Prepare App Icons**
Create two PNG files:
- `color.png`: 192x192 pixels (full color icon)
- `outline.png`: 32x32 pixels (transparent background)

### **5.2 Update Manifest**
1. Edit `manifest.json`
2. Replace `{{TEAMS_APP_ID}}` with your actual Bot App ID
3. Update company information and URLs

### **5.3 Create App Package**
```bash
# Create Teams app package
zip -r navo-teams-app.zip manifest.json color.png outline.png
```

## 🏢 **Step 6: Teams App Installation**

### **6.1 Upload to Teams Admin Center**
1. Go to [Teams Admin Center](https://admin.teams.microsoft.com)
2. Teams apps → Manage apps
3. Upload → Upload custom app
4. Select `navo-teams-app.zip`

### **6.2 Configure App Policies**
1. Setup policies → App setup policies
2. Create or edit policy
3. Add NAVO to pinned apps (optional)
4. Assign policy to users/groups

### **6.3 Test Installation**
1. Open Microsoft Teams
2. Apps → Built for your org
3. Find and install NAVO
4. Test in personal chat, team, or group chat

## ✅ **Step 7: Testing and Validation**

### **7.1 Basic Functionality Tests**
- [ ] Bot responds to @mentions in channels
- [ ] Bot works in personal chats
- [ ] Bot works in group chats
- [ ] Welcome message displays correctly
- [ ] Adaptive cards render properly
- [ ] Links in cards work correctly

### **7.2 Integration Tests**
- [ ] Confluence search returns results
- [ ] SharePoint search returns results
- [ ] Enterprise GPT responses are generated
- [ ] Error handling works gracefully
- [ ] Feedback buttons function

### **7.3 Performance Tests**
- [ ] Response time < 5 seconds
- [ ] Bot handles concurrent requests
- [ ] Memory usage is stable
- [ ] No memory leaks detected

## 🔧 **Step 8: Monitoring and Maintenance**

### **8.1 Application Insights (Recommended)**
```python
# Add to main.py
from applicationinsights import TelemetryClient
tc = TelemetryClient('your-instrumentation-key')
```

### **8.2 Health Monitoring**
- Monitor `/health` endpoint
- Set up alerts for failures
- Track response times
- Monitor API rate limits

### **8.3 Log Management**
```python
# Configure structured logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Bot Not Responding**
- Check messaging endpoint URL
- Verify App ID and Password
- Check firewall/network settings
- Review application logs

#### **Authentication Errors**
- Verify SharePoint app permissions
- Check Confluence API token
- Ensure Enterprise GPT endpoint is accessible
- Review Azure AD app registration

#### **Adaptive Cards Not Displaying**
- Validate card JSON schema
- Check Teams client version
- Review card complexity (keep under 28KB)
- Test with Card Validator

## 📞 **Support**

- **Documentation**: [GitHub Repository](https://github.com/mj3b/navo)
- **Issues**: [GitHub Issues](https://github.com/mj3b/navo/issues)
- **Microsoft Teams Platform**: [Teams Developer Documentation](https://docs.microsoft.com/en-us/microsoftteams/platform/)

---

**NAVO is now ready for enterprise deployment in Microsoft Teams!** 🎉

