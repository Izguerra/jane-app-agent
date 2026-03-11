# Pre-built Email Templates for Campaigns

This file contains pre-built HTML templates that can be used as starting points for campaign emails.

## Trial Expiration Templates

### Trial Ending Soon (7 days warning)

**Subject:** Your trial ends in {{days_remaining}} days

```html
<h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 600; color: #18181b;">Hi {{first_name}},</h2>

<p style="margin: 0 0 16px; line-height: 1.6;">Just a friendly reminder that your free trial ends in <strong>{{days_remaining}} days</strong>.</p>

<p style="margin: 0 0 16px; line-height: 1.6;">Make sure you've had a chance to try out all our features. When you're ready, upgrading is quick and easy.</p>

<p style="margin: 24px 0;">
  <a href="{{billing_url}}" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">
    View Plans
  </a>
</p>

<p style="margin: 0 0 16px; line-height: 1.6;">Need more time or have questions? Just reply and we'll help!</p>
```

---

### Trial Ending Very Soon (3 days or less)

**Subject:** Your trial ends in {{days_remaining}} day(s) – Don't lose access!

```html
<h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 600; color: #18181b;">Hi {{first_name}},</h2>

<p style="margin: 0 0 16px; line-height: 1.6;">Your free trial is ending soon! You have <strong>{{days_remaining}} day(s)</strong> left to explore everything.</p>

<p style="margin: 0 0 16px; line-height: 1.6;">Don't lose access to:</p>

<ul style="margin: 0 0 16px; padding-left: 24px;">
  <li style="margin-bottom: 8px;">AI-powered voice agents</li>
  <li style="margin-bottom: 8px;">Automated campaigns</li>
  <li style="margin-bottom: 8px;">Customer insights & analytics</li>
  <li style="margin-bottom: 8px;">24/7 customer support automation</li>
</ul>

<p style="margin: 24px 0;">
  <a href="{{billing_url}}" style="display: inline-block; background-color: #dc2626; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
    Upgrade Now
  </a>
</p>

<p style="margin: 0 0 16px; line-height: 1.6;">Questions? Just reply to this email!</p>
```

---

### Trial Expired

**Subject:** Your trial has ended – Upgrade to continue

```html
<h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 600; color: #18181b;">Hi {{first_name}},</h2>

<p style="margin: 0 0 16px; line-height: 1.6;">Your free trial has ended. To continue using all the features you love, please upgrade to a paid plan.</p>

<p style="margin: 0 0 8px; line-height: 1.6;"><strong>What happens now?</strong></p>

<ul style="margin: 0 0 16px; padding-left: 24px;">
  <li style="margin-bottom: 8px;">✓ Your data is safe and preserved</li>
  <li style="margin-bottom: 8px;">⏸ Access to core features is paused</li>
  <li style="margin-bottom: 8px;">🔓 Upgrade anytime to restore full access</li>
</ul>

<p style="margin: 24px 0;">
  <a href="{{billing_url}}" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
    Choose a Plan
  </a>
</p>

<p style="margin: 0 0 16px; line-height: 1.6;">If you have any questions, just reply to this email – we're here to help!</p>
```

---

## Appointment Reminder Templates

### Appointment Reminder (24 hours before)

**Subject:** Reminder: Your appointment is tomorrow

```html
<h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 600; color: #18181b;">Hi {{first_name}},</h2>

<p style="margin: 0 0 16px; line-height: 1.6;">This is a friendly reminder that you have an appointment scheduled for:</p>

<div style="background-color: #f4f4f5; padding: 20px; border-radius: 8px; margin: 16px 0;">
  <p style="margin: 0 0 8px; font-size: 18px; font-weight: 600; color: #18181b;">📅 {{appointment_date}}</p>
</div>

<p style="margin: 0 0 16px; line-height: 1.6;">Please arrive 5-10 minutes early. If you need to reschedule or cancel, please let us know as soon as possible.</p>

<p style="margin: 0 0 16px; line-height: 1.6;">See you soon!</p>
```

---

### Appointment Confirmation

**Subject:** Your appointment is confirmed!

```html
<h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 600; color: #18181b;">Hi {{first_name}},</h2>

<p style="margin: 0 0 16px; line-height: 1.6;">Great news! Your appointment has been confirmed.</p>

<div style="background-color: #ecfdf5; border: 1px solid #10b981; padding: 20px; border-radius: 8px; margin: 16px 0;">
  <p style="margin: 0 0 8px; font-size: 18px; font-weight: 600; color: #065f46;">✓ Confirmed</p>
  <p style="margin: 0; font-size: 16px; color: #065f46;">📅 {{appointment_date}}</p>
</div>

<p style="margin: 0 0 16px; line-height: 1.6;">We'll send you a reminder before your appointment. If you have any questions or need to make changes, just reply to this email.</p>

<p style="margin: 0 0 16px; line-height: 1.6;">Looking forward to seeing you!</p>
```

---

## Welcome / Onboarding Templates

### Welcome Email

**Subject:** Welcome to SupaAgent! 🎉

```html
<h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 600; color: #18181b;">Welcome aboard, {{first_name}}!</h2>

<p style="margin: 0 0 16px; line-height: 1.6;">Thanks for signing up for SupaAgent. We're excited to have you!</p>

<p style="margin: 0 0 16px; line-height: 1.6;">Here's what you can do to get started:</p>

<ul style="margin: 0 0 16px; padding-left: 24px;">
  <li style="margin-bottom: 8px;"><strong>Set up your first AI agent</strong> – Create a voice or text agent in minutes</li>
  <li style="margin-bottom: 8px;"><strong>Connect your calendar</strong> – Let your agent schedule appointments automatically</li>
  <li style="margin-bottom: 8px;"><strong>Create a campaign</strong> – Automate reminders and follow-ups</li>
</ul>

<p style="margin: 24px 0;">
  <a href="{{dashboard_url}}" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">
    Go to Dashboard
  </a>
</p>

<p style="margin: 0 0 16px; line-height: 1.6;">Have questions? Reply to this email anytime – we're here to help!</p>
```

---

## Usage Notes

1. **Copy the HTML content** into the email body field in the Campaign Step Builder
2. **Replace placeholder URLs** like `{{billing_url}}` and `{{dashboard_url}}` with actual links
3. **Available variables:** `{{first_name}}`, `{{last_name}}`, `{{appointment_date}}`, `{{appointment_id}}`
4. **Images:** You can add images using the editor's image tool or paste image URLs directly
5. **Buttons:** Use the link button in the editor and style with inline CSS for email compatibility
