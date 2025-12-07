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

### DNS Configuration Steps

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

## Common Error: "DuplicateManagedCertificateInEnvironment"

### Error Message:
```
ERROR: "code": "DeploymentFailed"
"code": "DuplicateManagedCertificateInEnvironment"
"message": "Another managed certificate with subject name 'app.*.io' and certificate name 'app.*.io-prod-aut-251205170140' available in environment 'prod-*-san-env'."
```

### What This Means

Azure Container Apps allows only **ONE managed certificate per domain per environment**. This error occurs when:

1. **Previous deployment created a certificate** that still exists in the environment
2. **New deployment tries to create another certificate** for the same domain
3. **Azure rejects the duplicate** to prevent conflicts

### Automatic Fix (GitHub Actions):

If you're using the GitHub Actions workflow (`.github/workflows/deploy-autopr-engine.yml`), this is **automatically handled** for you! The workflow includes a cleanup step that:

1. ✅ Checks for existing managed certificates for your domain
2. ✅ Removes any duplicates before deployment
3. ✅ Ensures clean deployment every time

### Manual Fix

If deploying manually with Azure CLI, run this cleanup script before deployment:

```bash
# Set your environment variables
RESOURCE_GROUP="prod-rg-san-autopr"
ENV_NAME="prod-autopr-san-env"
CUSTOM_DOMAIN="app.autopr.io"

# List all managed certificates for the domain
az containerapp env certificate list \
  --name $ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?properties.subjectName=='$CUSTOM_DOMAIN' && type=='Microsoft.App/managedEnvironments/managedCertificates'].name" \
  --output tsv | while read -r cert_name; do
  echo "Deleting duplicate certificate: $cert_name"
  az containerapp env certificate delete \
    --name $ENV_NAME \
    --resource-group $RESOURCE_GROUP \
    --certificate "$cert_name" \
    --yes
done

# Now deploy your template
az deployment group create \
  --name autopr-engine \
  --resource-group $RESOURCE_GROUP \
  --template-file infrastructure/bicep/autopr-engine.bicep \
  --parameters customDomain=$CUSTOM_DOMAIN ...
```

### Why This Happens

- Each deployment may try to create a certificate with the same domain name
- Azure maintains strict uniqueness constraint on managed certificates per domain
- Old certificates may not be automatically cleaned up when redeploying
- The cleanup ensures idempotent deployments

### Prevention

- Use the GitHub Actions workflow which handles cleanup automatically
- If deploying manually, always run the cleanup script first
- The deployment is now designed to be fully idempotent

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
