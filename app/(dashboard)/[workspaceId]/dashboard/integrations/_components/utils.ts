import { toast } from "sonner";
import { mutate } from "swr";

export const PROVIDER_NAMES: Record<string, string> = {
    'gmail_mailbox': 'Gmail',
    'outlook_mailbox': 'Outlook Mail',
    'icloud_mailbox': 'iCloud Mail',
    'google_calendar': 'Google Calendar',
    'outlook_calendar': 'Outlook Calendar',
    'icloud_calendar': 'iCloud Calendar',
    'google_drive': 'Google Drive',
    'exchange': 'Microsoft Exchange',
    'salesforce': 'Salesforce',
    'shopify': 'Shopify',
    'instagram': 'Instagram',
    'whatsapp': 'WhatsApp (Twilio)',
    'meta_whatsapp': 'WhatsApp (Meta)',
    'website_widget': 'Website Widget'
};

export async function toggleIntegration(provider: string, isActive: boolean) {
    const friendlyName = PROVIDER_NAMES[provider] || provider;
    try {
        if (isActive) {
            // For OAuth integrations (Google Calendar, Gmail), we don't want to overwrite credentials with dummy data
            const oauthProviders = ['google_calendar', 'gmail_mailbox', 'outlook_mailbox', 'icloud_mailbox'];
            const credentials = oauthProviders.includes(provider) ? null : { client_id: "demo", client_secret: "demo" };

            await fetch(`/api/agent/integrations/${provider}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider,
                    credentials,
                    settings: {}
                })
            });
            toast.success(`${friendlyName} enabled`);
        } else {
            await fetch(`/api/agent/integrations/${provider}`, {
                method: 'DELETE'
            });
            toast.success(`${friendlyName} disabled`);
        }
        mutate("/api/agent/integrations");
    } catch (error) {
        toast.error(`Failed to update ${friendlyName}`);
    }
}
