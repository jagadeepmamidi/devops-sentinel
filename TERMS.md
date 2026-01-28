# Terms of Service for DevOps Sentinel

**Last Updated**: January 27, 2026  
**Effective Date**: January 27, 2026

---

## 1. Acceptance of Terms

By using DevOps Sentinel ("the Software"), you agree to these Terms of Service. If you don't agree, don't use the Software.

**Key Point**: DevOps Sentinel is **open-source software** licensed under the MIT License. These terms supplement (not replace) the MIT License.

---

## 2. The Service

### 2.1 What DevOps Sentinel Is

DevOps Sentinel is a **self-hosted, open-source SRE monitoring platform** that:
- Monitors service health
- Detects incidents automatically
- Uses AI to generate incident analysis
- Provides intelligent alerting and on-call management

### 2.2 What DevOps Sentinel Is NOT

❌ **Not a SaaS**: We don't host your data  
❌ **Not a managed service**: You deploy and run it  
❌ **Not guaranteed uptime**: Open source, no SLA  
❌ **Not a replacement for human judgment**: AI is assistive, not autonomous

---

## 3. License & Ownership

### 3.1 Software License

DevOps Sentinel is released under the **MIT License**:
- ✅ Use for any purpose (commercial or personal)
- ✅ Modify the source code
- ✅ Distribute copies
- ✅ Sublicense
- ❌ No warranty provided
- ❌ Authors not liable for damages

**Full License**: See `LICENSE` file in the GitHub repository.

### 3.2 Your Data Ownership

**You own 100% of your data**:
- Service health data
- Incident records
- AI-generated postmortems
- Any embeddings or ML models trained on your data

**We have zero claim** to your data.

---

## 4. Your Responsibilities

### 4.1 Infrastructure

You are responsible for:
- Setting up and maintaining your Supabase instance
- Securing your API keys and credentials
- Configuring proper access controls
- Backing up your data
- Paying for third-party services (Supabase, OpenRouter, etc.)

### 4.2 Security

You must:
- Keep dependencies updated
- Use strong passwords
- Enable 2FA on connected services
- Monitor for vulnerabilities
- Not expose credentials in public repositories

### 4.3 Acceptable Use

You may **NOT use DevOps Sentinel to**:
- Monitor services you don't own/operate
- Conduct DDoS attacks or malicious health checks
- Violate any laws or regulations
- Infringe on others' intellectual property
- Harass or abuse third-party services

---

## 5. Third-Party Services

### 5.1 Required Services

DevOps Sentinel requires:
- **Supabase**: PostgreSQL database (your instance)
- **OpenRouter or AI Provider**: For AI features (your API key)

**Your Responsibility**: Comply with their terms of service.

### 5.2 Optional Integrations

Optional integrations (Slack, PagerDuty, Jira, etc.) are governed by:
- Their respective terms of service
- Your agreements with those providers

**We Are Not Responsible** for third-party service outages, costs, or policy changes.

---

## 6. AI & Machine Learning

### 6.1 AI-Generated Content

DevOps Sentinel uses AI to generate:
- Incident postmortems
- Root cause analysis
- Remediation recommendations

**Important**:
- ❗ AI can make mistakes
- ❗ Always verify AI suggestions before acting
- ❗ Human judgment is required
- ❗ We are not liable for AI-generated errors

### 6.2 ML Model Training

Machine learning models (anomaly detection, incident similarity) are:
- Trained on **YOUR data only**
- Stored in **YOUR infrastructure**
- Not shared with us or other users

---

## 7. Disclaimers & Limitations

### 7.1 No Warranty

DevOps Sentinel is provided **"AS IS" without warranty of any kind**:
- No guarantee of uptime
- No guarantee of accuracy
- No guarantee of fitness for purpose
- No guarantee of incident detection

### 7.2 Limitation of Liability

**To the maximum extent permitted by law**:
- We are NOT liable for data loss
- We are NOT liable for missed incidents
- We are NOT liable for service outages
- We are NOT liable for financial damages

**Maximum Liability**: $0 (it's free, open-source software)

### 7.3 Critical Systems

**WARNING**: DevOps Sentinel is NOT certified for:
- Life-critical systems (medical, aviation, etc.)
- Financial trading systems
- Nuclear facilities
- Any system where failure could cause death or serious injury

**Use at your own risk** for critical infrastructure.

---

## 8. Support & Maintenance

### 8.1 Community Support

Support is provided via:
- GitHub Issues (bug reports, feature requests)
- GitHub Discussions (community forum)
- Documentation (README, guides)

**No SLA**: Response times are not guaranteed.

### 8.2 No Maintenance Obligation

The maintainers have **no obligation** to:
- Fix bugs
- Add features
- Provide updates
- Continue development

**Open Source**: You can fork and maintain it yourself.

---

## 9. Privacy & Data

See our **[Privacy Policy](./PRIVACY.md)** for details.

**Summary**:
- We don't collect or store your data
- All data lives in your Supabase instance
- You are the data controller (GDPR terms)

---

## 10. Intellectual Property

### 10.1 Trademarks

"DevOps Sentinel" and any logos are intellectual property of the project maintainers.

**You MAY**:
- Use the name to describe the software
- Link to the official repository

**You MAY NOT**:
- Imply official endorsement
- Use logos in misleading ways
- Register confusingly similar trademarks

### 10.2 Contributions

By contributing code to DevOps Sentinel:
- You agree to license your contributions under the MIT License
- You have the right to submit the contribution
- Your contribution doesn't infringe on third-party IP

---

## 11. Modifications & Updates

### 11.1 Software Updates

The software may be updated via:
- GitHub releases
- Pull requests
- Security patches

**You control** when to update (since it's self-hosted).

### 11.2 Terms Updates

We may update these Terms of Service when:
- Adding new features
- Legal requirements change
- Community feedback

**Notification**: Changes announced in `CHANGELOG.md` and GitHub releases.

---

## 12. Termination

### 12.1 By You

You can stop using DevOps Sentinel **anytime**:
- Delete your deployment
- Remove your Supabase instance
- Disconnect integrations

No penalties, no questions asked.

### 12.2 By Us

Since it's self-hosted, **we can't terminate your use**.

However, we reserve the right to:
- Remove fork access (if violating GitHub ToS)
- Block contributors (if violating Code of Conduct)

---

## 13. Governing Law

### 13.1 Jurisdiction

These Terms are governed by the laws of **[Your Jurisdiction]**.

**Disputes**: Resolved through arbitration or local courts.

### 13.2 Open Source Exception

Nothing in these Terms restricts your rights under the **MIT License**.

---

## 14. Indemnification

You agree to indemnify and hold harmless the DevOps Sentinel maintainers from:
- Your violation of these Terms
- Your violation of third-party rights
- Your use of the Software
- Claims arising from your monitored services

---

## 15. Severability

If any provision of these Terms is found invalid:
- That provision is severed
- The rest of the Terms remain in effect

---

## 16. Entire Agreement

These Terms, along with:
- The MIT License
- The Privacy Policy
- The Code of Conduct

constitute the **entire agreement** between you and DevOps Sentinel.

---

## 17. Contact & Reporting

**Project**: DevOps Sentinel  
**GitHub**: [https://github.com/yourusername/devops_sentinel](https://github.com/yourusername/devops_sentinel)  
**Issues**: [GitHub Issues](https://github.com/yourusername/devops_sentinel/issues)  
**Security**: `security@devops-sentinel.dev`  
**Legal**: `legal@devops-sentinel.dev`

---

## Summary

📜 **MIT Licensed** - Use freely, modify, distribute  
🏠 **Self-Hosted** - You control everything  
💾 **You Own Your Data** - 100% yours  
⚠️ **No Warranty** - Use at your own risk  
🤝 **Community-Driven** - Open source support  
🔒 **Privacy-First** - We don't collect data  

**By using DevOps Sentinel, you acknowledge that you've read and agree to these Terms of Service.**

---

_DevOps Sentinel is not affiliated with PagerDuty, Datadog, New Relic, or any other commercial SRE platform._
