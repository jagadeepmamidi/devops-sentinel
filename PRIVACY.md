# Privacy Policy for DevOps Sentinel

**Last Updated**: January 27, 2026  
**Effective Date**: January 27, 2026

---

## Our Privacy-First Commitment

DevOps Sentinel is designed with **privacy as a core principle**. Unlike commercial SRE platforms that collect and store your data on their servers, DevOps Sentinel keeps all your data **in your own infrastructure**.

**TL;DR**: We don't store, see, or sell your data. You own everything.

---

## What Data is Collected

### 1. Data That Stays in YOUR Infrastructure

All operational data remains in **your own Supabase instance**:

- **Service Health Data**: Response times, status codes, error messages
- **Incident Records**: Incident details, postmortems, resolutions
- **Incident Embeddings**: Vector representations for similarity search (stored in your Supabase)
- **Service Dependencies**: Your service dependency graph
- **Runbooks**: Your playbooks and remediation steps
- **Baselines**: Statistical metrics calculated from your services
- **Anomalies**: ML-detected anomalies from your metrics
- **User Comments**: Incident timeline and collaboration data
- **On-Call Schedules**: Your team's rotation schedules

**We Never See This Data**. It lives in your Supabase database with your credentials.

### 2. Data We Process (But Don't Store)

When using AI features, we send **minimal context** to AI providers:

- **OpenRouter/AI Models**: 
  - Incident summaries for postmortem generation
  - Error messages for root cause analysis
  - Service names (no sensitive data)
  
**What We Don't Send**:
- Credentials, API keys, secrets
- Personal information
- Full logs or request bodies
- Customer data

### 3. Analytics (Optional & Anonymous)

If you opt-in to usage analytics:
- Number of services monitored (not service names)
- Number of incidents detected
- Feature usage statistics
- Error rates (aggregated)

**No Personal Identifiers**: No IP addresses, emails, or user names are collected.

---

## How Your Data is Used

### By You (In Your Infrastructure)
- Monitor service health
- Detect and resolve incidents
- Learn from past incidents (similarity search)
- Generate automated postmortems
- Track MTTR and other SRE metrics

### By AI Models (Temporary Processing)
- Generate incident analysis
- Suggest root causes
- Recommend remediation steps

**AI Processing**: Data is processed transiently and not stored by AI providers when using OpenRouter's API.

---

## Data Storage & Security

### Your Responsibility
Since all data lives in **your Supabase instance**:
- **You control access**: Set your own Row-Level Security (RLS) policies
- **You control backups**: Supabase auto-backups or your own
- **You control encryption**: Supabase uses encryption at rest and in transit
- **You control retention**: Delete data anytime

### Our Recommendations
1. **Enable Supabase RLS**: Restrict access to authenticated users only
2. **Rotate API Keys**: Change Supabase keys regularly
3. **Use Environment Variables**: Never commit `.env` files
4. **Enable 2FA**: On your Supabase account
5. **Monitor Access Logs**: Review Supabase audit logs

---

## Third-Party Services

DevOps Sentinel may integrate with third-party services **at your discretion**:

| Service | Purpose | Data Shared | Your Control |
|---------|---------|-------------|--------------|
| **Supabase** | Database | All operational data | You own the instance |
| **OpenRouter** | AI Models | Incident summaries | Use local models instead |
| **Slack** | Alerts | Service names, incident summaries | Optional webhook |
| **PagerDuty** | On-Call | Incident severity, assignee | Optional integration |
| **Jira** | Ticketing | Incident titles, links | Optional integration |

**You Enable Integrations**: All third-party integrations are opt-in.

---

## Cookies & Tracking

DevOps Sentinel does **not use cookies** for tracking.

**Local Storage**: The web dashboard may use browser local storage for:
- Authentication tokens (your Supabase session)
- UI preferences (theme, layout)
- Cached service data (for offline viewing)

---

## Your Rights

Since you own all the data:

✅ **Right to Access**: You have full access to all your data in Supabase  
✅ **Right to Delete**: Delete your Supabase project anytime  
✅ **Right to Export**: Export all data from Supabase (JSON, CSV, SQL)  
✅ **Right to Portability**: Self-hosted, take it anywhere  
✅ **Right to Opt-Out**: Disable any feature or integration

---

## Children's Privacy

DevOps Sentinel is intended for **professional use by DevOps teams**. We do not knowingly collect data from individuals under 13 years of age.

---

## Open Source Transparency

DevOps Sentinel is **open source** (MIT License):
- Audit the code: [GitHub Repository](https://github.com/yourusername/devops_sentinel)
- See exactly what data is collected
- Verify no hidden tracking
- Contribute improvements

---

## Changes to This Policy

We may update this privacy policy to reflect:
- New features
- Legal requirements
- Community feedback

**Change Notification**: Major changes will be announced via GitHub releases and documented in `CHANGELOG.md`.

---

## Data Breach Protocol

Since data is in **your** Supabase instance:
- **You are responsible** for breach notification under GDPR/CCPA
- **Supabase**: Has its own breach notification procedures
- **DevOps Sentinel Code**: Open source, can be audited for vulnerabilities

**Security Issues**: Report to `security@devops-sentinel.dev` (or create a private GitHub security advisory)

---

## International Users

### GDPR Compliance (EU)
- **Data Controller**: You (the Supabase instance owner)
- **Data Processor**: Supabase (compliant with GDPR)
- **Lawful Basis**: Legitimate interest (monitoring your own services)

### CCPA Compliance (California)
- **No Sale of Data**: We don't sell data (we don't even have it!)
- **Opt-Out**: Stop using the tool anytime

---

## Contact Us

**Open Source Project**: DevOps Sentinel  
**GitHub**: [https://github.com/yourusername/devops_sentinel](https://github.com/yourusername/devops_sentinel)  
**Issues**: [GitHub Issues](https://github.com/yourusername/devops_sentinel/issues)  
**Security**: `security@devops-sentinel.dev`

---

## Summary

🔒 **Your data stays with you** (in your Supabase)  
🚫 **We don't store, see, or sell your data**  
🔓 **Open source & auditable**  
✅ **GDPR & CCPA friendly by design**  
🛡️ **Privacy-first architecture**

**DevOps Sentinel: The privacy-respecting SRE co-pilot.**
