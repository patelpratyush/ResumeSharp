# Tailor Flow Deployment Guide

## Production-Ready Security Features ✅

### ✅ P0 Security Hardening Completed

- **MIME Validation**: python-magic validates file types, prevents malicious uploads
- **API Authentication**: Bearer token auth for sensitive endpoints (/rewrite, /parse-upload, /export/docx)
- **Rate Limiting**: slowapi protection against abuse and DoS attacks  
- **Request Tracking**: UUID-based request IDs with structured logging
- **Upload Security**: DOCX zip bomb protection, file size limits, timeout controls
- **Error Handling**: Centralized retry logic, exponential backoff, uniform JSON errors
- **Configuration Security**: Hidden config endpoint in production, sanitized CORS exposure

### Backend Security Features

```python
# Endpoints with authentication required
REQUIRE_AUTH_ENDPOINTS = ["/rewrite", "/parse-upload", "/export/docx"]

# Rate limiting per endpoint type
- General endpoints: 60 requests/minute
- Upload endpoints: 10 requests/minute  
- Compute endpoints: 5 requests/minute

# Upload validation
- MIME type verification using python-magic
- DOCX safety checks (max 100 zip members, 50MB uncompressed)
- File size limits (8MB default)
- Parse timeout protection (30s default)
```

### Frontend Security Features

```typescript
// Centralized API client with retries and auth
- Request ID tracking for observability
- Automatic retry on 429/5xx with exponential backoff
- API key injection for protected endpoints
- Timeout handling (30-60s depending on operation)
- Uniform error parsing and user feedback
```

## Deployment Options

### Option A: Render + Vercel (Recommended)

**Backend (Render):**
```bash
# 1. Create new Web Service on Render
# 2. Connect your GitHub repo
# 3. Configure build & start commands:
Build Command: pip install -r requirements.txt
Start Command: gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -t 60 --bind 0.0.0.0:$PORT

# 4. Set environment variables:
API_KEY=your-secure-random-key-here
ALLOWED_ORIGINS=https://your-frontend.vercel.app
DEBUG_MODE=false
EXPOSE_CONFIG=false
RATE_LIMIT_ENABLED=true
VALIDATE_MIME_TYPES=true
```

**Frontend (Vercel):**
```bash
# 1. Deploy to Vercel via GitHub integration
# 2. Set environment variables:
NEXT_PUBLIC_API_BASE=https://your-backend.onrender.com
NEXT_PUBLIC_API_KEY=your-secure-random-key-here

# 3. Build will automatically use environment variables
```

### Option B: Single VPS (EC2/DigitalOcean)

**1. Server Setup:**
```bash
# Install dependencies
sudo apt update && sudo apt install -y python3 python3-pip nginx certbot python3-certbot-nginx
sudo apt install -y nodejs npm  # For frontend build

# Clone repository
git clone https://github.com/your-username/tailor-flow-ui.git
cd tailor-flow-ui
```

**2. Backend Setup:**
```bash
# Install Python dependencies
cd server
pip3 install -r requirements.txt

# Create production environment file
cp .env.example .env
# Edit .env with your settings

# Create systemd service
sudo tee /etc/systemd/system/tailor-api.service << EOF
[Unit]
Description=Tailor API
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/tailor-flow-ui/server
EnvironmentFile=/home/ubuntu/tailor-flow-ui/server/.env
ExecStart=/usr/local/bin/gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -t 60 -b 127.0.0.1:8000
Restart=always
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable tailor-api
sudo systemctl start tailor-api
```

**3. Frontend Setup:**
```bash
# Build frontend
cd ../src
npm install
npm run build

# Copy build files to nginx directory
sudo cp -r dist/* /var/www/html/
```

**4. Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend static files
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Request-ID $request_id;
        proxy_read_timeout 65s;
        client_max_body_size 8m;
    }
}
```

**5. SSL Setup:**
```bash
sudo certbot --nginx -d your-domain.com
```

## Environment Configuration

### Optional: Enhanced MIME Validation

For enhanced security, install `libmagic` system library:

```bash
# macOS
brew install libmagic

# Ubuntu/Debian
sudo apt-get install libmagic1

# CentOS/RHEL
sudo yum install file-libs
# or
sudo dnf install file-libs

# If libmagic is not available, the system will fall back to extension-based validation
```

### Required Environment Variables

```bash
# Security (Required for production)
API_KEY=your-secure-api-key-here           # Generate with: openssl rand -hex 32
ALLOWED_ORIGINS=https://your-frontend.com
DEBUG_MODE=false
EXPOSE_CONFIG=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Upload Security  
VALIDATE_MIME_TYPES=true
MAX_UPLOAD_SIZE_MB=8
MAX_DOCX_MEMBERS=100
PARSE_TIMEOUT_SECONDS=30

# Analysis Configuration
ENHANCED_JD_NORMALIZATION=true
FUZZY_THRESHOLD=85
```

### Optional LLM Configuration

```bash
# For enhanced rewriting (optional)
OPENAI_API_KEY=sk-...        # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-... # Anthropic Claude API key
```

## Monitoring & Logging

### Request Tracking
```python
# Every request gets a UUID for tracking
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000

# Structured logging includes:
- Request method, path, client IP
- Response status, duration in ms  
- Error details with request ID
- Rate limit violations
```

### Health Checks
```bash
# API health endpoint
GET /api/health
Response: {"ok": true}

# Configuration check (if enabled)
GET /api/config  
Response: {"version": "0.1.0", "config_valid": true, ...}
```

## Security Checklist

### Pre-Production Security Review

- [ ] **API Key Configured**: Strong random key set in `API_KEY` env var
- [ ] **CORS Restricted**: `ALLOWED_ORIGINS` set to frontend domain only
- [ ] **Config Locked Down**: `EXPOSE_CONFIG=false` and `DEBUG_MODE=false`
- [ ] **Rate Limiting Active**: `RATE_LIMIT_ENABLED=true` 
- [ ] **File Validation On**: `VALIDATE_MIME_TYPES=true`
- [ ] **HTTPS Enabled**: SSL certificates installed and redirects configured
- [ ] **Firewall Configured**: Only ports 80, 443, and SSH open
- [ ] **Monitoring Setup**: Request IDs logged, error tracking enabled

### Recommended Production Settings

```bash
# .env for production
DEBUG_MODE=false
EXPOSE_CONFIG=false
EXPOSE_CORS_ORIGINS=false
ALLOWED_ORIGINS=https://your-actual-domain.com
API_KEY=your-256-bit-random-key
RATE_LIMIT_ENABLED=true
VALIDATE_MIME_TYPES=true
MAX_UPLOAD_SIZE_MB=5
PARSE_TIMEOUT_SECONDS=20
```

## Performance Optimization

### Backend
- **Gunicorn**: 2 workers for small instance, 4+ for larger
- **Timeout**: 60s for LLM operations, 30s for parsing
- **Memory**: ~512MB per worker, 1GB+ recommended

### Frontend  
- **CDN**: Vercel/Netlify handle this automatically
- **Caching**: Static assets cached, API responses not cached
- **Bundle Size**: ~500KB gzipped with code splitting

## Troubleshooting

### Common Issues

**1. MIME validation errors:**
```bash
# Check if libmagic is installed
python3 -c "import magic; print(magic.from_buffer(b'test', mime=True))"
# Install if missing: apt-get install libmagic1
```

**2. Rate limit issues:**
```bash
# Check rate limit settings
curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/api/health
# Adjust RATE_LIMIT_PER_MINUTE if needed
```

**3. Upload failures:**
```bash
# Check file size and type limits
# Verify CORS settings for file uploads
# Check nginx client_max_body_size
```

### Logs to Monitor

```bash
# Application logs
sudo journalctl -u tailor-api -f

# Nginx access logs  
sudo tail -f /var/log/nginx/access.log

# Rate limiting violations
grep "rate_limit_exceeded" /var/log/tailor-api.log
```

## Next Steps (P1 Features)

1. **Monitoring**: Add Sentry for error tracking, Uptime monitoring
2. **Analytics**: PostHog events for usage analytics
3. **Accessibility**: ARIA labels, keyboard navigation, color contrast
4. **Data Retention**: Automatic cleanup, privacy policy compliance
5. **PDF Export**: Alternative to DOCX export option

---

**🎉 Your Tailor Flow app is now production-ready with enterprise-grade security!**