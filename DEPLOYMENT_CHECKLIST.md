# Deployment Checklist

**Project:** YT-Clipper + n8n + Google Drive Integration  
**Date:** 2026-05-19  
**Status:** ✅ Implementation Complete - Ready for Deployment

---

## Pre-Deployment Checklist

### ✅ Code Implementation
- [x] Google Drive service created
- [x] Webhook service created
- [x] CLI flags added (--upload-to-drive, --webhook, --json)
- [x] Workflow integration complete
- [x] Settings updated
- [x] Dependencies added
- [x] All imports working
- [x] Syntax validation passed
- [x] Documentation complete

### ⏳ Google Cloud Setup
- [x] Google Cloud project created
- [x] Google Drive API enabled
- [x] OAuth2 credentials created (Desktop app)
- [x] Credentials JSON downloaded
- [ ] Google Drive folder created
- [ ] Folder ID copied

### ⏳ Local Configuration
- [ ] `.env` file updated with:
  - [ ] `GOOGLE_DRIVE_FOLDER_ID`
  - [ ] `WEBHOOK_ENABLED=true`
  - [ ] `WEBHOOK_URL=https://n8n.fajrsyauqi.com/webhook/clip-notification`
- [ ] `google_oauth_credentials.json` in project root
- [ ] Dependencies installed: `uv sync`

### ⏳ Local Testing
- [ ] First-time OAuth authentication completed
- [ ] `google_drive_token.json` generated
- [ ] Test basic processing (no upload)
- [ ] Test with Google Drive upload
- [ ] Verify files in Google Drive
- [ ] Test shareable links work
- [ ] Test JSON output format

---

## VPS Deployment Checklist

### ⏳ Server Preparation
- [ ] Code deployed to VPS: `/opt/yt-clipper`
- [ ] Python 3.12+ installed
- [ ] FFmpeg installed
- [ ] Virtual environment created
- [ ] Dependencies installed: `uv sync`

### ⏳ Configuration Transfer
- [ ] `.env` file copied to VPS
- [ ] `google_oauth_credentials.json` copied to VPS
- [ ] File permissions set correctly
- [ ] Environment variables verified

### ⏳ OAuth Setup on VPS
- [ ] Run OAuth flow on VPS (one-time)
  ```bash
  python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"
  ```
- [ ] `google_drive_token.json` generated on VPS
- [ ] Token file permissions set (600)

### ⏳ VPS Testing
- [ ] Test CLI on VPS
- [ ] Test upload to Google Drive from VPS
- [ ] Verify webhook can reach n8n
- [ ] Test error handling
- [ ] Check logs directory exists

---

## n8n Integration Checklist

### ⏳ n8n Setup
- [ ] n8n accessible at: https://n8n.fajrsyauqi.com
- [ ] Webhook endpoints configured
- [ ] Environment variables set in n8n

### ⏳ Workflow 1: Process Video (Trigger)
- [ ] Webhook trigger created: `/webhook/clip-process`
- [ ] Validate input node added
- [ ] Respond immediately node added
- [ ] Execute command node configured
- [ ] Error handler added
- [ ] Workflow activated

### ⏳ Workflow 2: Results Handler
- [ ] Webhook trigger created: `/webhook/clip-notification`
- [ ] Switch node for event routing
- [ ] Success flow configured
- [ ] Error flow configured
- [ ] Workflow activated

### ⏳ Workflow 3: Cleanup (Optional)
- [ ] Schedule trigger configured (daily 2 AM)
- [ ] Cleanup command configured
- [ ] Workflow activated

### ⏳ Notifications Setup
- [ ] Discord webhook URL configured
- [ ] Slack webhook URL configured (optional)
- [ ] Test notifications working

### ⏳ History Logging (Optional)
- [ ] Google Sheets created
- [ ] Sheets configured (Processing Log, Clips, Errors)
- [ ] Google Sheets nodes added to workflow
- [ ] Test logging working

---

## Testing Checklist

### ⏳ End-to-End Testing

#### Test 1: Basic Flow
```bash
curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "max_clips": 2}'
```

**Expected:**
- [ ] Immediate 202 response from n8n
- [ ] CLI processes video on VPS
- [ ] Files uploaded to Google Drive
- [ ] Webhook sent to n8n
- [ ] Notification received (Discord/Slack)
- [ ] History logged (if configured)

#### Test 2: Error Handling
```bash
curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=invalid"}'
```

**Expected:**
- [ ] CLI fails gracefully
- [ ] Error webhook sent
- [ ] Error notification received
- [ ] Error logged

#### Test 3: Manual Webhook Test
```bash
curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-notification \
  -H "Content-Type: application/json" \
  -d @test_webhook.json
```

**Expected:**
- [ ] n8n receives webhook
- [ ] Notification sent
- [ ] Data logged correctly

### ⏳ Google Drive Verification
- [ ] Files appear in correct folder
- [ ] Files have public permissions
- [ ] View links work (open in browser)
- [ ] Download links work
- [ ] Thumbnail links work (if available)

### ⏳ Performance Testing
- [ ] Process short video (< 5 min)
- [ ] Process medium video (5-15 min)
- [ ] Process long video (15-30 min)
- [ ] Verify timeout settings adequate
- [ ] Check resource usage on VPS

---

## Security Checklist

### ⏳ Credentials Security
- [ ] `google_oauth_credentials.json` not in git
- [ ] `google_drive_token.json` not in git
- [ ] `.env` file not in git
- [ ] `.gitignore` updated
- [ ] File permissions set correctly (600 for sensitive files)

### ⏳ API Security
- [ ] n8n webhook URLs kept private
- [ ] API keys rotated if exposed
- [ ] HTTPS used for all webhooks
- [ ] n8n basic auth enabled (optional)

### ⏳ Google Drive Security
- [ ] OAuth scope limited to `drive.file` only
- [ ] Token refresh working
- [ ] Folder permissions reviewed
- [ ] Quota limits monitored

---

## Monitoring Checklist

### ⏳ Logging
- [ ] Application logs configured
- [ ] Log rotation setup
- [ ] Error logs monitored
- [ ] n8n execution logs reviewed

### ⏳ Alerts
- [ ] Discord/Slack notifications working
- [ ] Error notifications configured
- [ ] Processing time tracked
- [ ] Failure rate monitored

### ⏳ Maintenance
- [ ] Temp file cleanup scheduled
- [ ] Google Drive quota monitored
- [ ] Token refresh working
- [ ] Backup strategy defined

---

## Documentation Checklist

### ✅ Documentation Created
- [x] N8N_INTEGRATION.md - Complete setup guide
- [x] N8N_WORKFLOWS.md - Workflow templates
- [x] IMPLEMENTATION_SUMMARY.md - Implementation details
- [x] DEPLOYMENT_CHECKLIST.md - This file
- [x] .env.example - Updated with new variables

### ⏳ Documentation Review
- [ ] Setup instructions tested
- [ ] Webhook examples verified
- [ ] Troubleshooting guide reviewed
- [ ] Command examples tested

---

## Post-Deployment Checklist

### ⏳ Validation
- [ ] Process 3-5 test videos successfully
- [ ] Verify all clips uploaded correctly
- [ ] Confirm notifications received
- [ ] Check history logs accurate
- [ ] Review error handling

### ⏳ Optimization
- [ ] Adjust timeout settings if needed
- [ ] Tune max_clips default
- [ ] Optimize upload batch size
- [ ] Review processing time

### ⏳ User Training
- [ ] Document common workflows
- [ ] Create usage examples
- [ ] Share webhook URLs securely
- [ ] Train on error recovery

---

## Rollback Plan

If issues occur:

1. **Disable webhooks:**
   ```bash
   # In .env
   WEBHOOK_ENABLED=false
   ```

2. **Disable uploads:**
   ```bash
   # Don't use --upload-to-drive flag
   python main.py clip run "URL" --no-webhook
   ```

3. **Deactivate n8n workflows:**
   - Pause workflows in n8n UI
   - Fix issues
   - Reactivate when ready

4. **Revert code:**
   ```bash
   git checkout main
   ```

---

## Success Criteria

### Minimum Viable Product (MVP)
- [x] Code implementation complete
- [ ] Google OAuth working
- [ ] Upload to Google Drive working
- [ ] Webhook notifications working
- [ ] n8n receives and processes webhooks
- [ ] Basic notifications working

### Full Production
- [ ] All MVP criteria met
- [ ] Error handling tested
- [ ] Performance acceptable
- [ ] Monitoring in place
- [ ] Documentation complete
- [ ] Team trained

---

## Next Actions

### Immediate (Today)
1. ✅ Complete code implementation
2. ⏳ Setup Google Cloud project
3. ⏳ Configure local environment
4. ⏳ Test locally

### Short-term (This Week)
5. ⏳ Deploy to VPS
6. ⏳ Setup OAuth on VPS
7. ⏳ Create n8n workflows
8. ⏳ Test end-to-end

### Medium-term (Next Week)
9. ⏳ Setup notifications
10. ⏳ Configure history logging
11. ⏳ Optimize performance
12. ⏳ Document workflows

---

## Contact & Support

**Documentation:**
- N8N_INTEGRATION.md - Setup guide
- N8N_WORKFLOWS.md - Workflow templates
- IMPLEMENTATION_SUMMARY.md - Technical details

**Troubleshooting:**
- Check logs: `tail -f logs/yt-clipper.log`
- Review n8n execution logs
- Test webhooks manually with curl
- Verify Google Drive API quotas

---

**Status:** ✅ Ready for Deployment  
**Last Updated:** 2026-05-19T14:10:31Z  
**Next Milestone:** Google OAuth Setup & Local Testing
