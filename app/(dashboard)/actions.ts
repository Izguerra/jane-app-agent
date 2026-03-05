'use server';

import { z } from 'zod';

const contactFormSchema = z.object({
    name: z.string().min(1, 'Name is required').max(100),
    email: z.string().email('Invalid email address'),
    subject: z.string().min(1, 'Subject is required'),
    message: z.string().min(10, 'Message must be at least 10 characters').max(1000),
});

export async function submitContactForm(formData: FormData) {
    try {
        const data = {
            name: formData.get('name') as string,
            email: formData.get('email') as string,
            subject: formData.get('subject') as string,
            message: formData.get('message') as string,
        };

        // Validate the form data
        const validated = contactFormSchema.parse(data);

        // Log submission (simplified for now)
        console.log('='.repeat(60));
        console.log('📧 NEW CONTACT FORM SUBMISSION');
        console.log('='.repeat(60));
        console.log('From:', validated.name);
        console.log('Email:', validated.email);
        console.log('Subject:', validated.subject);
        console.log('Message:', validated.message);
        console.log('Time:', new Date().toISOString());
        console.log('='.repeat(60));

        console.log('DESTINATION:', 'randy@supaagent.com');
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
                        subject: `Contact Form: ${validated.subject}`,
                        html: `
                            <h2>New Contact Form Submission</h2>
                            <p><strong>Name:</strong> ${validated.name}</p>
                            <p><strong>Email:</strong> ${validated.email}</p>
                            <p><strong>Subject:</strong> ${validated.subject}</p>
                            <p><strong>Message:</strong></p>
                            <p>${validated.message.replace(/\n/g, '<br>')}</p>
                        `,
                    }),
                });

                if (!response.ok) {
                    const error = await response.json();
                    console.error('Resend API Error:', error);
                    // Don't fail the user request on email error, but log it
                } else {
                    console.log('✅ Email sent successfully via Resend');
                }
            } catch (emailError) {
                console.error('Failed to send email:', emailError);
            }
        } else {
            console.warn('⚠️ RESEND_API key not found. Email not sent.');
        }

        return {
            success: true,
            message: 'Thank you for your message! We\'ll get back to you soon.'
        };
    } catch (error) {
        console.error('='.repeat(60));
        console.error('❌ CONTACT FORM ERROR:');
        console.error('='.repeat(60));
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
            message: 'Failed to send message. Please try again.'
        };
    }
}
