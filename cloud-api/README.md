# DocAssist Cloud API

Zero-knowledge encrypted backup storage for DocAssist EMR using Cloudflare Workers + R2.

## Architecture

The server stores only encrypted blobs and **cannot decrypt** patient data. All encryption/decryption happens client-side using PyNaCl.

```
Client Device         Cloud API          R2 Storage
┌─────────────┐      ┌─────────┐       ┌──────────┐
│ Plaintext   │──────│ Workers │───────│ Encrypted│
│ SQLite +    │ AES  │ (proxy) │       │ Blobs    │
│ ChromaDB    │──────│         │───────│          │
└─────────────┘      └─────────┘       └──────────┘
     │                                       │
     └───────────────────────────────────────┘
              Encryption key NEVER
              leaves the device
```

## Features

- ✅ Zero-knowledge storage (server cannot decrypt)
- ✅ API key authentication
- ✅ Rate limiting (100 req/min)
- ✅ Storage quota enforcement
- ✅ Device isolation
- ✅ Metadata tracking (size, checksum, timestamps)
- ✅ CORS support for web clients

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Create KV Namespaces

```bash
# API Keys storage
wrangler kv:namespace create "API_KEYS"
wrangler kv:namespace create "API_KEYS" --preview

# Usage tracking
wrangler kv:namespace create "USAGE"
wrangler kv:namespace create "USAGE" --preview

# Rate limiting
wrangler kv:namespace create "RATE_LIMIT"
wrangler kv:namespace create "RATE_LIMIT" --preview
```

Copy the namespace IDs into `wrangler.toml`.

### 3. Create R2 Buckets

```bash
# Production bucket
wrangler r2 bucket create docassist-backups

# Preview bucket (for local dev)
wrangler r2 bucket create docassist-backups-preview
```

### 4. Update Configuration

Edit `wrangler.toml` and replace placeholder IDs:
- `YOUR_API_KEYS_KV_ID`
- `YOUR_USAGE_KV_ID`
- `YOUR_RATE_LIMIT_KV_ID`

### 5. Generate API Keys

```bash
# Generate a new API key for a device
wrangler kv:key put --binding=API_KEYS \
  "sk_live_abc123xyz" \
  '{"api_key":"sk_live_abc123xyz","device_id":"device-001","tier":"free","created_at":"2024-01-01T00:00:00Z"}'
```

**Key format:**
```json
{
  "api_key": "sk_live_abc123xyz",
  "device_id": "device-001",
  "tier": "free",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Development

### Run Locally

```bash
npm run dev
```

This starts the worker at `http://localhost:8787`.

### Test Endpoints

```bash
# Health check
curl http://localhost:8787/health

# Upload backup
curl -X PUT http://localhost:8787/v1/backups/device-001/backup-2024-01-01.enc \
  -H "Authorization: Bearer sk_live_abc123xyz" \
  -H "Content-Type: application/octet-stream" \
  -H "X-Backup-Checksum: sha256:abc123..." \
  --data-binary @backup.enc

# List backups
curl http://localhost:8787/v1/backups/device-001 \
  -H "Authorization: Bearer sk_live_abc123xyz"

# Download backup
curl http://localhost:8787/v1/backups/device-001/backup-2024-01-01.enc \
  -H "Authorization: Bearer sk_live_abc123xyz" \
  -o backup.enc

# Get account info
curl http://localhost:8787/v1/account \
  -H "Authorization: Bearer sk_live_abc123xyz"

# Check if backup exists (HEAD)
curl -I http://localhost:8787/v1/backups/device-001/backup-2024-01-01.enc \
  -H "Authorization: Bearer sk_live_abc123xyz"

# Get backup metadata
curl http://localhost:8787/v1/backups/device-001/backup-2024-01-01.enc/metadata \
  -H "Authorization: Bearer sk_live_abc123xyz"

# Delete backup
curl -X DELETE http://localhost:8787/v1/backups/device-001/backup-2024-01-01.enc \
  -H "Authorization: Bearer sk_live_abc123xyz"
```

## Deployment

### Deploy to Production

```bash
npm run deploy
```

Your API will be available at:
```
https://docassist-cloud.<your-subdomain>.workers.dev
```

### Custom Domain (Optional)

1. Go to Cloudflare Dashboard > Workers & Pages
2. Select your worker
3. Add custom domain (e.g., `api.docassist.health`)

## API Reference

### Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer sk_live_abc123xyz
```

### Endpoints

#### `PUT /v1/backups/:device_id/:key`

Upload encrypted backup.

**Headers:**
- `Content-Type`: `application/octet-stream`
- `Content-Length`: Required
- `X-Backup-Checksum`: Optional SHA256 checksum

**Response:**
```json
{
  "success": true,
  "message": "Backup uploaded successfully",
  "metadata": {
    "device_id": "device-001",
    "key": "backup-2024-01-01.enc",
    "size": 1024000,
    "uploaded_at": "2024-01-01T12:00:00Z",
    "checksum": "sha256:abc123...",
    "content_type": "application/octet-stream"
  }
}
```

#### `GET /v1/backups/:device_id/:key`

Download encrypted backup.

**Response:** Binary blob with headers:
- `Content-Type`: `application/octet-stream`
- `Content-Length`: Size in bytes
- `X-Backup-Checksum`: SHA256 checksum
- `X-Uploaded-At`: ISO timestamp

#### `DELETE /v1/backups/:device_id/:key`

Delete backup.

**Response:**
```json
{
  "success": true,
  "message": "Backup deleted successfully"
}
```

#### `GET /v1/backups/:device_id`

List all backups for device.

**Response:**
```json
{
  "device_id": "device-001",
  "backups": [
    {
      "key": "backup-2024-01-01.enc",
      "size": 1024000,
      "uploaded_at": "2024-01-01T12:00:00Z",
      "checksum": "sha256:abc123..."
    }
  ],
  "total_count": 1,
  "total_size": 1024000
}
```

#### `HEAD /v1/backups/:device_id/:key`

Check if backup exists.

**Response:** 200 if exists, 404 if not found

**Headers:**
- `X-Backup-Exists`: `true`
- `Content-Length`: Size in bytes
- `X-Uploaded-At`: ISO timestamp

#### `GET /v1/backups/:device_id/:key/metadata`

Get backup metadata without downloading.

**Response:**
```json
{
  "device_id": "device-001",
  "key": "backup-2024-01-01.enc",
  "size": 1024000,
  "uploaded_at": "2024-01-01T12:00:00Z",
  "checksum": "sha256:abc123...",
  "content_type": "application/octet-stream"
}
```

#### `GET /v1/account`

Get account information.

**Response:**
```json
{
  "device_id": "device-001",
  "tier": "free",
  "quota_bytes": 1073741824,
  "used_bytes": 1024000,
  "backup_count": 1,
  "percentage_used": 0.09
}
```

## Storage Tiers

| Tier   | Storage | Price/mo | Features                    |
|--------|---------|----------|-----------------------------|
| Free   | 1 GB    | ₹0       | Manual backup               |
| Basic  | 10 GB   | ₹99      | Auto-backup, 30-day history |
| Pro    | 50 GB   | ₹299     | + Multi-device sync         |
| Clinic | 200 GB  | ₹999     | + 5 users, audit log        |

## Rate Limiting

- **Limit:** 100 requests per minute per API key
- **Response:** 429 Too Many Requests

## Error Codes

| Status | Error                  | Description                      |
|--------|------------------------|----------------------------------|
| 400    | invalid_request        | Malformed request                |
| 401    | unauthorized           | Invalid or missing API key       |
| 403    | forbidden              | Device ID mismatch               |
| 404    | not_found              | Backup or endpoint not found     |
| 413    | payload_too_large      | File too large                   |
| 413    | quota_exceeded         | Storage quota exceeded           |
| 429    | rate_limit_exceeded    | Too many requests                |
| 500    | upload_failed          | Upload error                     |
| 500    | download_failed        | Download error                   |

## Security

### Zero-Knowledge Architecture

The server **cannot decrypt** backups because:

1. All encryption happens **client-side** using PyNaCl
2. Encryption keys are derived from user passwords via Argon2
3. Keys **never leave** the user's device
4. Server stores only encrypted blobs

### API Key Management

- API keys start with `sk_live_` for production, `sk_test_` for testing
- Store keys securely in KV namespace
- Rotate keys periodically
- Never commit keys to version control

### HTTPS Only

All production traffic must use HTTPS. Cloudflare Workers enforce this by default.

## Monitoring

### View Logs

```bash
npm run tail
```

### Metrics

View in Cloudflare Dashboard:
- Request count
- Error rate
- Response time
- Bandwidth usage

## Cost Estimation

Cloudflare Workers pricing (as of 2024):

- **Workers:** $5/month for 10M requests
- **R2 Storage:** $0.015/GB/month
- **R2 Operations:** Free egress, minimal operation costs

**Example:** 100 users × 1GB average = $1.50/month storage + $5 workers = **$6.50/month**

## Troubleshooting

### "Invalid API key" error

- Verify KV namespace IDs in `wrangler.toml`
- Check API key format in KV store
- Ensure Bearer token is correct

### "Quota exceeded" error

- Check account tier: `GET /v1/account`
- Delete old backups to free space
- Upgrade tier if needed

### CORS errors

- Verify CORS headers are present
- Check browser console for specific error
- Test with `curl` to isolate client issues

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test locally: `npm run dev`
4. Run type check: `npm run type-check`
5. Commit: `git commit -m "feat: add new feature"`
6. Push and create PR

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://github.com/docassist/cloud-api
- Issues: https://github.com/docassist/cloud-api/issues
- Email: support@docassist.health
