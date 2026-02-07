# Resume File: OAuth Issue on Render Deployment

## Goal
Deploy the Invoice App to Render and enable Google OAuth login for users.

## Current Status
**BLOCKED** - Google OAuth returns `Error 400: invalid_request` when trying to log in.

## The Error
```
Error 400: invalid_request
Request details: redirect_uri=https://invoice-app-fpr0.onrender.com/auth/callback flowName=GeneralOAuthFlow
```

## Live URLs
- **App**: https://invoice-app-fpr0.onrender.com
- **Privacy Policy**: https://invoice-app-fpr0.onrender.com/privacy
- **Terms**: https://invoice-app-fpr0.onrender.com/terms

## Current Render Environment Variables
| Key | Value |
|-----|-------|
| `ANTHROPIC_API_KEY` | (set) |
| `DATABASE_URL` | `postgresql://invoice_app_db_fc31_user:...@dpg-d630m9cr85hc739vbc5g-a.frankfurt-postgres.render.com/invoice_app_db_fc31` |
| `FLASK_ENV` | `production` |
| `GOOGLE_CLIENT_ID` | (from Invoice App2 project - check Render) |
| `GOOGLE_CLIENT_SECRET` | (from Invoice App2 project - check Render) |
| `GOOGLE_REDIRECT_URI` | `https://invoice-app-fpr0.onrender.com/auth/callback` |
| `REDIS_URL` | `redis://red-d630vpf5r7bs73a5gmog:6379` |
| `SECRET_KEY` | (set) |

## Google Cloud Project: "Invoice App2"
- **Project created fresh** to avoid legacy issues
- **APIs Enabled**: Google Drive API, Google Sheets API, Gmail API
- **OAuth Consent Screen**: External, Testing mode
- **Test User**: mwpicard@gmail.com
- **OAuth Client Type**: Web application
- **Authorized JavaScript origins**: `https://invoice-app-fpr0.onrender.com`
- **Authorized redirect URIs**: `https://invoice-app-fpr0.onrender.com/auth/callback`

## What We've Tried (ALL FAILED)
1. ✗ Multiple OAuth clients in different projects
2. ✗ Adding/verifying redirect URIs multiple times
3. ✗ Adding JavaScript origins
4. ✗ Enabling all required APIs (Drive, Sheets, Gmail)
5. ✗ Configuring OAuth consent screen with all details
6. ✗ Adding test users
7. ✗ Publishing app to production mode
8. ✗ Going back to testing mode
9. ✗ Adding privacy policy and terms pages
10. ✗ Adding privacy/terms links to homepage
11. ✗ Changing Drive scope from `drive` to `drive.readonly`
12. ✗ Simplifying OAuth authorization URL parameters (removed `include_granted_scopes`, simplified `prompt`)
13. ✗ Creating a brand new Google Cloud project
14. ✗ Multiple combinations of the above

## Key Files
- **OAuth handler**: `app/auth/google_auth.py`
- **Auth routes**: `app/auth/routes.py`
- **Config**: `app/config.py`

## OAuth Flow Code (google_auth.py)
```python
self.scopes = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.readonly'
]

# Authorization URL generation
authorization_url, state = flow.authorization_url(
    access_type='offline',
    prompt='consent'
)
```

## Important Notes
- The app worked **locally** with a different OAuth client (from a project the user no longer has access to)
- The redirect URI shown in the error **matches** what's configured in Google Cloud Console
- Render logs show no errors
- The error occurs **before** the Google consent screen appears

## Possible Causes Not Yet Investigated
1. Something specific about Render's infrastructure that Google doesn't like
2. Domain verification requirements for onrender.com subdomains
3. Time propagation issues (though we waited several minutes between attempts)
4. Some hidden Google Cloud project setting
5. Rate limiting or blocking from too many failed OAuth attempts

## To Continue
1. Update Render env vars with the new OAuth credentials from "Invoice App2" Google Cloud project
2. Try logging in at https://invoice-app-fpr0.onrender.com
3. If still failing, check Render logs during login attempt
4. Consider alternative hosting (Railway, Fly.io) if Render has specific issues

## GitHub Repository
https://github.com/AlellaGreenTech/Invoice_app
