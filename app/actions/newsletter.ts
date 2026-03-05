'use server';

import { z } from 'zod';

const newsletterSchema = z.object({
    email: z.string().email('Invalid email address'),
});

export async function subscribeToNewsletter(formData: FormData) {
    try {
        const data = {
            email: formData.get('email') as string,
        };

        // Validate the form data
        const validated = newsletterSchema.parse(data);

        // Log subscription (simplified for now)
        console.log('='.repeat(60));
        console.log('📬 NEW NEWSLETTER SUBSCRIPTION');
        console.log('='.repeat(60));
        console.log('Email:', validated.email);
        console.log('Time:', new Date().toISOString());
        console.log('='.repeat(60));

        const resendApiKey = process.env.RESEND_API;
        if (resendApiKey) {
            try {
                const response = await fetch('https://api.resend.com/emails', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${resendApiKey}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        from: process.env.EMAIL_FROM || 'onboarding@resend.dev',
                        to: 'randy@supaagent.com',
                        subject: `New Newsletter Subscription: ${validated.email}`,
                        html: `
                            <h2>New Newsletter Subscription</h2>
                            <p><strong>Email:</strong> ${validated.email}</p>
                            <p><strong>Time:</strong> ${new Date().toLocaleString()}</p>
                        `,
                    }),
                });

                if (!response.ok) {
                    const error = await response.json();
                    console.error('Resend API Error:', error);
                    // Don't fail the user request on email error, but log it
                } else {
                    console.log('✅ Notification email sent successfully via Resend');
                }
            } catch (emailError) {
                console.error('Failed to send notification email:', emailError);
            }
        } else {
            console.warn('⚠️ RESEND_API key not found. Email not sent.');
        }

        return {
            success: true,
            message: 'Thanks for subscribing! We\'ll keep you posted.'
        };
    } catch (error) {
        console.error('='.repeat(60));
        console.error('❌ NEWSLETTER ERROR:');
        console.error(error);
        console.error('='.repeat(60));

        if (error instanceof z.ZodError) {
            return {
                success: false,
                message: error.errors[0].message
            };
        }

        return {
            success: false,
            message: 'Failed to subscribe. Please try again.'
        };
    }
}
