# YouTube Cookies Setup Guide

**Issue:** YouTube blocks VPS IP addresses, treating them as bots.  
**Solution:** Use browser cookies for authentication.

---

## Quick Setup (5 minutes)

### Step 1: Export Cookies from Browser

#### Option A: Using Browser Extension (Easiest)

**Chrome:**
1. Install extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Go to [youtube.com](https://youtube.com) and make sure you're logged in
3. Click the extension icon
4. Click "Export" → Save as `cookies.txt`

**Firefox:**
1. Install extension: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Go to [youtube.com](https://youtube.com) and make sure you're logged in
3. Click the extension icon
4. Click "Export" → Save as `cookies.txt`

#### Option B: Using yt-dlp (Alternative)

On your local machine:
```bash
# Extract from Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Or from Firefox
yt-dlp --cookies-from-browser firefox --cookies cookies.txt \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

---

### Step 2: Upload to VPS

```bash
# Upload cookies file to VPS
scp cookies.txt user@your-vps:/opt/yt-clipper/

# Or if using current directory
scp cookies.txt user@your-vps:~/yt-clipper/
```

---

### Step 3: Configure .env

On your VPS, edit `.env`:

```bash
# YouTube Authentication
YOUTUBE_COOKIES_FILE=cookies.txt
```

Or specify full path:
```bash
YOUTUBE_COOKIES_FILE=/opt/yt-clipper/cookies.txt
```

---

### Step 4: Test

```bash
cd /opt/yt-clipper
source .venv/bin/activate

# Test download
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-clips 1 \
  --json
```

**Expected:** Download should work without bot detection error.

---

## Troubleshooting

### Issue: "cookiefile not found"

**Solution:** Check the path in `.env`:
```bash
# Verify file exists
ls -la /opt/yt-clipper/cookies.txt

# Update .env with correct path
YOUTUBE_COOKIES_FILE=/opt/yt-clipper/cookies.txt
```

### Issue: Still getting bot detection error

**Solutions:**

1. **Refresh cookies** - Cookies expire, export new ones:
   ```bash
   # On local machine, export fresh cookies
   # Upload to VPS again
   scp cookies.txt user@vps:/opt/yt-clipper/
   ```

2. **Check cookie format** - File should start with:
   ```
   # Netscape HTTP Cookie File
   .youtube.com	TRUE	/	TRUE	...
   ```

3. **Use different Google account** - Some accounts may be flagged:
   - Log out of YouTube
   - Log in with different account
   - Export cookies again

### Issue: Cookies expire frequently

**Solution:** Set up automatic cookie refresh:

1. Export cookies from a browser that's always logged in
2. Set up a cron job to copy fresh cookies periodically
3. Or use `--cookies-from-browser` in yt-dlp (requires browser on VPS)

---

## Security Notes

⚠️ **Important:**
- Cookies contain authentication tokens
- Keep `cookies.txt` secure (don't commit to git)
- Add to `.gitignore`:
  ```bash
  echo "cookies.txt" >> .gitignore
  ```
- Set proper permissions:
  ```bash
  chmod 600 /opt/yt-clipper/cookies.txt
  ```

---

## How It Works

1. You export cookies from your browser (where you're logged into YouTube)
2. yt-dlp uses these cookies to authenticate as you
3. YouTube sees the request as coming from a logged-in user, not a bot
4. Downloads work normally

---

## Cookie Lifespan

- **Typical lifespan:** 1-6 months
- **Signs of expiration:**
  - Bot detection errors return
  - "Sign in to confirm" messages
- **Solution:** Export fresh cookies and upload again

---

## Alternative: Use Proxy

If cookies don't work, you can also use a proxy:

```bash
# In .env (not implemented yet, but can be added)
YOUTUBE_PROXY=http://proxy-server:port
```

---

## Files Modified

- ✅ `app/config/settings.py` - Added `youtube_cookies_file` setting
- ✅ `app/services/youtube/service.py` - Added cookie support to yt-dlp
- ✅ `.env.example` - Added `YOUTUBE_COOKIES_FILE` example

---

## Quick Reference

```bash
# Export cookies (local machine)
# Use browser extension or yt-dlp

# Upload to VPS
scp cookies.txt user@vps:/opt/yt-clipper/

# Configure (on VPS)
echo "YOUTUBE_COOKIES_FILE=cookies.txt" >> .env

# Test
python main.py clip run "URL" --max-clips 1 --json
```

---

**Status:** Ready to use! Export cookies and configure `.env` on your VPS.
