# NAVO Web Interface

This directory contains the web interface components for NAVO's browser-based knowledge discovery platform.

## Directory Structure

```
web/
├── __init__.py                 # Package initialization
├── templates/                  # HTML templates
│   └── index.html             # Main web interface
├── static/                     # Static assets (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
└── routes/                     # Web route handlers
    ├── __init__.py
    └── web_routes.py          # Web interface routes
```

## Web Interface Overview

### Main Interface (`templates/index.html`)
Modern, responsive web interface built with Tailwind CSS that provides an intuitive chat-based knowledge discovery experience.

**Key Features:**
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Chat Interface**: Interactive conversation with NAVO
- **Quick Actions**: Pre-defined queries for common use cases
- **System Status**: Live monitoring of integration health
- **Recent Queries**: History of user interactions
- **Progressive Enhancement**: Works with and without JavaScript

**Interface Components:**
- **Chat Container**: Main conversation area with message bubbles
- **Query Input**: Natural language input with auto-complete
- **Sidebar**: Quick actions, system status, and recent queries
- **Status Indicators**: Real-time system health monitoring
- **Typing Indicators**: Visual feedback during processing

### Design System

#### Color Palette
- **Primary**: Blue gradient (#667eea to #764ba2)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Error**: Red (#EF4444)
- **Neutral**: Gray scale (#F9FAFB to #111827)

#### Typography
- **Headers**: Inter font family, bold weights
- **Body**: Inter font family, regular weights
- **Code**: Fira Code, monospace

#### Components
- **Message Bubbles**: Rounded corners, subtle shadows
- **Buttons**: Consistent padding, hover states
- **Cards**: White background, subtle borders
- **Status Indicators**: Color-coded dots

### User Experience Features

#### Chat Interface
```html
<!-- Message Structure -->
<div class="message-bubble">
    <div class="flex items-start space-x-3">
        <div class="avatar">N</div>
        <div class="message-content">
            <div class="message-text">...</div>
            <div class="message-metadata">...</div>
        </div>
    </div>
</div>
```

#### Quick Actions
Pre-configured queries for common enterprise scenarios:
- **Engineering Updates**: Latest technical documentation
- **Deployment Procedures**: Release and deployment guides
- **Troubleshooting**: Error resolution and debugging
- **Security Policies**: Compliance and security documentation

#### System Status Monitoring
Real-time health checks for:
- **OpenAI Enterprise**: AI service availability
- **Confluence**: Atlassian integration status
- **SharePoint**: Microsoft Graph API status

### JavaScript Architecture

#### NAVOInterface Class
Main JavaScript class that manages the web interface:

```javascript
class NAVOInterface {
    constructor() {
        this.chatContainer = document.getElementById('chatContainer');
        this.queryForm = document.getElementById('queryForm');
        this.init();
    }
    
    async sendQuery(text) {
        // Send query to NAVO API
    }
    
    addMessage(content, sender, metadata) {
        // Add message to chat interface
    }
    
    checkSystemStatus() {
        // Monitor system health
    }
}
```

#### Key Methods
- **handleSubmit()**: Process user queries
- **sendQuery()**: API communication
- **addMessage()**: Update chat interface
- **checkSystemStatus()**: Health monitoring
- **updateRecentQueries()**: Query history management

### API Integration

#### Query Endpoint
```javascript
const response = await fetch('/api/v1/query', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        text: query,
        user_id: userId,
        context: {},
        filters: {}
    })
});
```

#### Health Check Endpoint
```javascript
const health = await fetch('/health');
const status = await health.json();
```

### Responsive Design

#### Breakpoints
- **Mobile**: < 768px (single column layout)
- **Tablet**: 768px - 1024px (adjusted sidebar)
- **Desktop**: > 1024px (full layout)

#### Mobile Optimizations
- **Touch-friendly**: Large tap targets
- **Readable**: Appropriate font sizes
- **Fast**: Optimized loading and interactions
- **Accessible**: Screen reader support

### Accessibility Features

#### WCAG 2.1 Compliance
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Readers**: Proper ARIA labels and roles
- **Color Contrast**: WCAG AA compliant contrast ratios
- **Focus Management**: Clear focus indicators

#### Implementation
```html
<!-- Accessible form -->
<form id="queryForm" role="search" aria-label="Knowledge query">
    <input 
        type="text" 
        id="queryInput"
        aria-label="Enter your question"
        placeholder="Ask me anything..."
    >
    <button type="submit" aria-label="Submit query">
        <i class="fas fa-paper-plane" aria-hidden="true"></i>
    </button>
</form>
```

### Performance Optimization

#### Loading Strategy
- **Critical CSS**: Inlined for fast rendering
- **Progressive Enhancement**: Core functionality without JavaScript
- **Lazy Loading**: Non-critical resources loaded on demand
- **Caching**: Aggressive caching for static assets

#### Bundle Optimization
- **Minification**: CSS and JavaScript minification
- **Compression**: Gzip compression for text assets
- **CDN**: External libraries from CDN
- **Tree Shaking**: Remove unused code

### Security Considerations

#### Content Security Policy
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com;
               script-src 'self' 'unsafe-inline';
               img-src 'self' data:;">
```

#### Input Sanitization
- **XSS Prevention**: All user input sanitized
- **CSRF Protection**: CSRF tokens for state-changing operations
- **Rate Limiting**: Query rate limiting on frontend

### Browser Support

#### Supported Browsers
- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

#### Fallbacks
- **CSS Grid**: Flexbox fallback
- **Fetch API**: XMLHttpRequest fallback
- **ES6 Features**: Babel transpilation for older browsers

### Development Workflow

#### Local Development
```bash
# Start development server
python main.py

# Access web interface
open http://localhost:8000
```

#### Build Process
```bash
# Minify CSS
npx tailwindcss -i ./src/input.css -o ./static/css/styles.min.css --minify

# Optimize images
npx imagemin static/images/* --out-dir=static/images/optimized
```

### Testing

#### Unit Tests
```javascript
// Test query submission
describe('NAVOInterface', () => {
    test('should submit query correctly', async () => {
        const navo = new NAVOInterface();
        const result = await navo.sendQuery('test query');
        expect(result).toBeDefined();
    });
});
```

#### Integration Tests
```python
def test_web_interface_loads():
    response = client.get('/')
    assert response.status_code == 200
    assert 'NAVO' in response.text
```

#### Accessibility Tests
```javascript
// Test keyboard navigation
test('should be keyboard accessible', () => {
    const queryInput = document.getElementById('queryInput');
    queryInput.focus();
    expect(document.activeElement).toBe(queryInput);
});
```

### Deployment

#### Production Build
```bash
# Build optimized assets
npm run build

# Deploy to production
docker build -t navo-web .
docker run -p 8000:8000 navo-web
```

#### CDN Configuration
```nginx
# Nginx configuration for static assets
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    gzip_static on;
}
```

The web interface provides an intuitive, accessible, and performant way for users to interact with NAVO's knowledge discovery capabilities through a modern browser-based chat interface.

