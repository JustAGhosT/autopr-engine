# Azure Container Apps Deployment FAQ

## Certificate Management

### Q: Do I need to provide a certificate or certificate link for the custom domain?

**A: No, you do not need to provide a certificate!** 

Azure Container Apps automatically manages SSL/TLS certificates for your custom domain at no additional cost. The deployment template is configured to use **Azure Managed Certificates**, which means:

✅ **Automatic Certificate Provisioning**: Azure creates a free SSL certificate for your domain
✅ **Automatic Renewal**: Certificates are renewed before expiration without any manual intervention
✅ **No Certificate Upload Required**: You don't need to buy, upload, or manage certificates
✅ **Single Deployment**: Everything is configured in one deployment step

### What You DO Need to Provide:

1. **A custom domain name** (e.g., `app.autopr.io`)
2. **DNS CNAME record** pointing your domain to the Container App FQDN

### DNS Configuration Steps:

Before or immediately after deployment, add a CNAME record:

```
Type: CNAME
Name: app.autopr.io (or your subdomain)
Value: prod-autopr-san-app.eastus2.azurecontainerapps.io
TTL: 3600 (or default)
```

To get your Container App FQDN after deployment:
```bash
az deployment group show \
  --resource-group prod-rg-san-autopr \
  --name autopr-engine \
  --query properties.outputs.containerAppUrl.value
```

### Certificate Provisioning Timeline:

After DNS is configured:
- ⏱️ **DNS Propagation**: 15-30 minutes (varies by DNS provider)
- ⏱️ **Certificate Validation**: 5-15 minutes (Azure validates domain ownership)
- ⏱️ **Certificate Provisioning**: Automatic (Azure creates and binds the certificate)

Total time: Typically 20-45 minutes from DNS configuration to working HTTPS.

---

## Common Error: "CertificateMissing"

### Error Message:
```
ERROR: "code": "InvalidTemplateDeployment"
Inner Errors: "code": "CertificateMissing", 
"message": "CertificateId property is missing for customDomain 'app.*.io'."
```

### This error occurs if:

1. **Using an older version of the template** that doesn't have managed certificate support
   - **Solution**: Pull the latest version from the `main` branch
   - The fix was implemented in commit `7337442`

2. **DNS is not configured** before deployment
   - **Solution**: Configure DNS first, or deploy without custom domain initially, then add it later
   - See "DNS Configuration Steps" above

### How to Fix:

#### Option 1: Update to Latest Template (Recommended)
```bash
# Pull latest changes
git pull origin main

# Redeploy with the updated template
az deployment group create \
  --name autopr-engine \
  --resource-group prod-rg-san-autopr \
  --template-file infrastructure/bicep/autopr-engine.bicep \
  --parameters \
    environment=prod \
    regionAbbr=san \
    location=eastus2 \
    customDomain=app.autopr.io \
    containerImage=ghcr.io/justaghost/autopr-engine:latest \
    postgresLogin="<your-login>" \
    postgresPassword="<your-password>" \
    redisPassword="<your-password>"
```

#### Option 2: Deploy Without Custom Domain First

```bash
# Deploy without customDomain parameter
az deployment group create \
  --name autopr-engine \
  --resource-group prod-rg-san-autopr \
  --template-file infrastructure/bicep/autopr-engine.bicep \
  --parameters \
    environment=prod \
    regionAbbr=san \
    location=eastus2 \
    containerImage=ghcr.io/justaghost/autopr-engine:latest \
    postgresLogin="<your-login>" \
    postgresPassword="<your-password>" \
    redisPassword="<your-password>"

# Configure DNS with the Container App FQDN

# Redeploy with custom domain
az deployment group create \
  --name autopr-engine \
  --resource-group prod-rg-san-autopr \
  --template-file infrastructure/bicep/autopr-engine.bicep \
  --parameters \
    environment=prod \
    regionAbbr=san \
    location=eastus2 \
    customDomain=app.autopr.io \
    containerImage=ghcr.io/justaghost/autopr-engine:latest \
    postgresLogin="<your-login>" \
    postgresPassword="<your-password>" \
    redisPassword="<your-password>"
```

---

## Verification

### Check Certificate Status:
```bash
az containerapp show \
  --name prod-autopr-san-app \
  --resource-group prod-rg-san-autopr \
  --query "properties.configuration.ingress.customDomains"
```

### Check Managed Certificate
```bash
az containerapp env certificate list \
  --name prod-autopr-san-env \
  --resource-group prod-rg-san-autopr
```

### Test HTTPS:

```bash
curl -I https://app.autopr.io
```

---

## Additional Resources

- **Detailed Technical Explanation**: See [CERTIFICATE_FIX.md](./CERTIFICATE_FIX.md)
- **Deployment Guide**: See [README-AUTOPR-ENGINE.md](./README-AUTOPR-ENGINE.md)
- **Azure Documentation**: [Container Apps Custom Domains](https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-certificates)
