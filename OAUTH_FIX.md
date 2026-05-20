# OAuth 403 Error - Troubleshooting Guide

**Error:** `Error 403: access_denied`

**Cause:** OAuth consent screen not configured or user not added as test user.

---

## Quick Fix (5 minutes)

### Step 1: Go to OAuth Consent Screen
```
https://console.cloud.google.com/apis/credentials/consent?project=opportune-cairn-418017
```

### Step 2: Configure Consent Screen

#### If NOT configured yet:

1. **User Type:**
   - Select: **External**
   - Click: **Create**

2. **App Information:**
   - App name: `YT-Clipper`
   - User support email: `your-email@gmail.com`
   - App logo: (optional, skip)
   - App domain: (optional, skip)
   - Developer contact: `your-email@gmail.com`
   - Click: **Save and Continue**

3. **Scopes:**
   - Click: **Add or Remove Scopes**
   - Search: `drive.file`
   - Check: `https://www.googleapis.com/auth/drive.file`
   - Description: "See, edit, create, and delete only the specific Google Drive files you use with this app"
   - Click: **Update**
   - Click: **Save and Continue**

4. **Test Users:** ⚠️ IMPORTANT
   - Click: **Add Users**
   - Enter: `your-email@gmail.com` (the Gmail you'll use)
   - Click: **Add**
   - Click: **Save and Continue**

5. **Summary:**
   - Review and click: **Back to Dashboard**

#### If already configured:

1. Click **Edit App**
2. Go to **Test Users** section
3. Click **Add Users**
4. Add your Gmail address
5. Click **Save**

---

## Step 3: Verify Configuration

Check that:
- ✅ OAuth consent screen is configured
- ✅ Scope `https://www.googleapis.com/auth/drive.file` is added
- ✅ Your Gmail is added as a test user
- ✅ App status shows "Testing" (this is OK)

---

## Step 4: Try Authentication Again

```bash
cd /Users/mac/Documents/Works/python/yt-clipper
python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"
```

**Expected:**
1. Browser opens
2. Select your Google account
3. See warning: "Google hasn't verified this app" - Click **Continue**
4. Grant permissions
5. See "The authentication flow has completed"
6. Token saved to `google_drive_token.json`

---

## Alternative: Publish the App (Optional)

If you don't want the "unverified app" warning:

1. Go to OAuth consent screen
2. Click **Publish App**
3. Click **Confirm**

**Note:** For personal use, keeping it in "Testing" mode is fine.

---

## Common Issues

### Issue 1: "This app is blocked"
**Solution:** Make sure you added yourself as a test user.

### Issue 2: "Access blocked: Authorization Error"
**Solution:** 
- Check that Drive API is enabled
- Verify scope is correct: `https://www.googleapis.com/auth/drive.file`

### Issue 3: "Redirect URI mismatch"
**Solution:** This shouldn't happen with Desktop app type, but if it does:
- Go to Credentials
- Edit OAuth client
- Add redirect URI: `http://localhost`

---

## Verification Checklist

Before trying again:

- [ ] OAuth consent screen configured
- [ ] User type: External
- [ ] App name: YT-Clipper
- [ ] Scope added: `https://www.googleapis.com/auth/drive.file`
- [ ] Test user added: your-email@gmail.com
- [ ] Google Drive API enabled
- [ ] OAuth credentials downloaded

---

## After Successful Authentication

You should see:
```
✓ Token saved to google_drive_token.json
```

Then test upload:
```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-clips 1 \
  --upload-to-drive \
  --json
```

---

## Still Having Issues?

1. **Delete old token:**
   ```bash
   rm google_drive_token.json
   ```

2. **Check project ID matches:**
   ```bash
   cat google_oauth_credentials.json | grep project_id
   # Should show: opportune-cairn-418017
   ```

3. **Verify Drive API is enabled:**
   ```
   https://console.cloud.google.com/apis/library/drive.googleapis.com?project=opportune-cairn-418017
   ```

4. **Check credentials:**
   ```
   https://console.cloud.google.com/apis/credentials?project=opportune-cairn-418017
   ```

---

## Quick Links

- **OAuth Consent Screen:** https://console.cloud.google.com/apis/credentials/consent?project=opportune-cairn-418017
- **Credentials:** https://console.cloud.google.com/apis/credentials?project=opportune-cairn-418017
- **Drive API:** https://console.cloud.google.com/apis/library/drive.googleapis.com?project=opportune-cairn-418017

---

**Most Common Fix:** Add yourself as a test user in OAuth consent screen!
