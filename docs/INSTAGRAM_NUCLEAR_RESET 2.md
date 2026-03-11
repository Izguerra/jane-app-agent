# Instagram Integration Nuclear Reset Procedure

## Why This is Necessary

Your Instagram integration has **"One-Way Silence"** - messages go out but content doesn't come in. The root cause: **Missing `pages_manage_metadata` permission** in your access token.

## Pre-Reset Checklist

- [ ] Take screenshots of current integration settings
- [ ] Note your current Instagram Account ID: `178485835330631`
- [ ] Save any webhook URLs currently configured
- [ ] Export any conversation history if needed

## Step 1: Remove Integration from SupaAgent

1. Navigate to SupaAgent Dashboard
2. Go to **Settings** → **Integrations**
3. Find Instagram integration
4. Click **Delete** or **Disconnect**
5. Confirm removal
6. **Screenshot the confirmation**

## Step 2: Revoke App Access from Meta

1. Go to [Facebook Business Settings](https://business.facebook.com/settings)
2. Navigate to **Business Assets** → **Connected Assets** → **Apps**
3. Find **SupaAgent** in the list
4. Click the **three dots** menu → **Remove App**
5. Alternatively:
   - Go to [Facebook Settings](https://www.facebook.com/settings?tab=business_integrations)
   - Find SupaAgent
   - Click **Remove**
6. **Screenshot the removal confirmation**

## Step 3: Clear Meta Session Data

1. Clear browser cache for these domains:
   - facebook.com
   - instagram.com
   - business.facebook.com
2. Sign out of all Meta accounts
3. Close browser completely

## Step 4: Verify Clean State

Run this command to verify the token is revoked:
```bash
curl -X GET "https://graph.facebook.com/v21.0/debug_token?input_token=OLD_TOKEN&access_token=OLD_TOKEN"
```

Expected response should show `"is_valid": false`

## Step 5: Reconnect with Full Permissions

1. Open SupaAgent Dashboard in **Incognito/Private mode**
2. Log in to SupaAgent
3. Navigate to **Settings** → **Integrations**
4. Click **Connect Instagram**
5. When Facebook OAuth dialog appears:
   
   ### CRITICAL: Permission Checklist
   
   **MUST HAVE ALL OF THESE:**
   - [ ] `pages_messaging` - Send/receive messages
   - [ ] `pages_messaging_subscriptions` - Webhook events
   - [ ] `instagram_basic` - Basic Instagram access
   - [ ] `instagram_manage_messages` - Message management
   - [ ] `pages_manage_metadata` - **CRITICAL - Was missing!**
   - [ ] `pages_read_engagement` - Read engagement data
   - [ ] `business_management` - Business account access
   - [ ] `instagram_manage_insights` - Analytics access
   
   **OPTIONAL BUT RECOMMENDED:**
   - [ ] `pages_manage_posts` - Post management
   - [ ] `pages_read_user_content` - Read user content
   - [ ] `instagram_content_publish` - Content publishing

6. **IMPORTANT**: Take a screenshot of the permission dialog BEFORE clicking Accept
7. Ensure ALL checkboxes are selected
8. Click **Continue** or **Accept**
9. Complete the connection flow

## Step 6: Verify New Token Permissions

1. Create `instagram_config.json`:
```json
{
  "access_token": "YOUR_NEW_TOKEN",
  "app_id": "YOUR_APP_ID",
  "page_id": "YOUR_PAGE_ID",
  "instagram_account_id": "178485835330631",
  "test_recipient_id": "YOUR_TEST_USER_ID"
}
```

2. Run the verification script:
```bash
python scripts/verify_instagram_permissions.py
```

3. Check the report confirms:
   - All required permissions present
   - Token is valid
   - Webhook subscriptions active

## Step 7: Configure Webhook Subscription

If webhooks need reconfiguration:

```bash
curl -X POST "https://graph.facebook.com/v21.0/YOUR_APP_ID/subscriptions" \
  -d "object=instagram" \
  -d "callback_url=https://your-domain.com/webhooks/meta" \
  -d "fields=messages,messaging_seen" \
  -d "verify_token=YOUR_VERIFY_TOKEN" \
  -d "access_token=YOUR_NEW_TOKEN"
```

## Step 8: Subscribe Page to App

```bash
curl -X POST "https://graph.facebook.com/v21.0/YOUR_PAGE_ID/subscribed_apps" \
  -d "subscribed_fields=messages,messaging_seen" \
  -d "access_token=YOUR_NEW_TOKEN"
```

## Step 9: Test the Integration

1. Send a test message from Instagram to your business account
2. Check webhook logs for incoming events
3. Verify message content is present (not just read receipts)

## Troubleshooting

### If Still Receiving Empty Messages

1. **Check App Mode**: Ensure app is in Live mode or tester is added
2. **Verify Webhook URL**: Must be HTTPS with valid SSL
3. **Check Rate Limits**: Meta may throttle during testing
4. **Review App Review Status**: Some permissions need approval

### If Token Still Missing Permissions

1. The OAuth dialog may not show all permissions if:
   - App doesn't have them configured
   - Business verification incomplete
   - App review pending

2. Check Meta App Dashboard:
   - Go to App Dashboard → App Review → Permissions
   - Verify all needed permissions are added
   - Submit for review if needed

### Emergency Rollback

If issues persist after reset:
1. Save new token and config
2. Document any error messages
3. Check Meta Developer Community for similar issues
4. Consider opening Meta support ticket

## Success Indicators

✅ Token has `pages_manage_metadata` permission  
✅ Webhook receives message events with content  
✅ Can read actual message text, not just receipts  
✅ Two-way conversation flow works  

## Post-Reset Monitoring

1. Monitor webhook logs for 24 hours
2. Test with multiple Instagram accounts
3. Verify all message types work:
   - Text messages
   - Media messages
   - Story replies
   - Story mentions

## Documentation to Update

After successful reset:
1. Update `.env` with new token
2. Update database with new IDs if changed
3. Document the working permission set
4. Create backup of working configuration