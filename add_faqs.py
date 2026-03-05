#!/usr/bin/env python3
"""Add FAQ questions to landing.html"""

# Read the file
with open('public/landing.html', 'r') as f:
    content = f.read()

# New FAQ questions to add (Questions 5-12)
new_faqs = '''
                    <!-- Question 5 -->
                    <div
                        class="flex gap-4 p-4 rounded-lg bg-white dark:bg-surface-dark border border-[#f0f2f4] dark:border-[#2a3441]">
                        <div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">schedule</span>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-bold text-[#111418] dark:text-white mb-2">How long does setup take?</h3>
                            <p class="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">Most users are up and running in under 15 minutes. Upload your knowledge base, configure your agent settings, and you're ready to go live.</p>
                        </div>
                    </div>

                    <!-- Question 6 -->
                    <div
                        class="flex gap-4 p-4 rounded-lg bg-white dark:bg-surface-dark border border-[#f0f2f4] dark:border-[#2a3441]">
                        <div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">integration_instructions</span>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-bold text-[#111418] dark:text-white mb-2">What integrations are supported?</h3>
                            <p class="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">We integrate with Google Calendar, Twilio, Instagram DM, SMS, and web chat. API access is available for custom integrations on Professional and Enterprise plans.</p>
                        </div>
                    </div>

                    <!-- Question 7 -->
                    <div
                        class="flex gap-4 p-4 rounded-lg bg-white dark:bg-surface-dark border border-[#f0f2f4] dark:border-[#2a3441]">
                        <div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">phone</span>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-bold text-[#111418] dark:text-white mb-2">Can I use my own phone number?</h3>
                            <p class="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">Yes! You can port your existing number or use one of ours. Each plan includes phone numbers, and you can add more as needed.</p>
                        </div>
                    </div>

                    <!-- Question 8 -->
                    <div
                        class="flex gap-4 p-4 rounded-lg bg-white dark:bg-surface-dark border border-[#f0f2f4] dark:border-[#2a3441]">
                        <div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">language</span>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-bold text-[#111418] dark:text-white mb-2">What languages are supported?</h3>
                            <p class="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">Our AI agents support 50+ languages for text chat. Voice capabilities are available in English, Spanish, French, German, and more.</p>
                        </div>
                    </div>

                    <!-- Question 9 -->
                    <div
                        class="flex gap-4 p-4 rounded-lg bg-white dark:bg-surface-dark border border-[#f0f2f4] dark:border-[#2a3441]">
                        <div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">calendar_month</span>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-bold text-[#111418] dark:text-white mb-2">Does it handle appointment booking?</h3>
                            <p class="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">Yes! Our agents can book, reschedule, and cancel appointments automatically using your Google Calendar integration with real-time availability.</p>
                        </div>
                    </div>

                    <!-- Question 10 -->
                    <div
                        class="flex gap-4 p-4 rounded-lg bg-white dark:bg-surface-dark border border-[#f0f2f4] dark:border-[#2a3441]">
                        <div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">support_agent</span>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-bold text-[#111418] dark:text-white mb-2">What kind of support do you offer?</h3>
                            <p class="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">Starter plans include email support. Professional plans get priority support with faster response times. Enterprise customers have dedicated success managers.</p>
                        </div>
                    </div>

                    <!-- Question 11 -->
                    <div
                        class="flex gap-4 p-4 rounded-lg bg-white dark:bg-surface-dark border border-[#f0f2f4] dark:border-[#2a3441]">
                        <div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">folder_open</span>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-bold text-[#111418] dark:text-white mb-2">How does the knowledge base work?</h3>
                            <p class="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">Upload documents, FAQs, or service information. Our AI learns from your content to provide accurate, context-aware responses to customer questions.</p>
                        </div>
                    </div>

                    <!-- Question 12 -->
                    <div
                        class="flex gap-4 p-4 rounded-lg bg-white dark:bg-surface-dark border border-[#f0f2f4] dark:border-[#2a3441]">
                        <div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">cancel</span>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-bold text-[#111418] dark:text-white mb-2">Can I cancel anytime?</h3>
                            <p class="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">Yes, you can cancel your subscription at any time. Your service will continue until the end of your current billing period with no penalties or fees.</p>
                        </div>
                    </div>
'''

# Find the insertion point (after Question 4, before closing </div></div></div>)
# Look for the pattern after Question 4's closing tags
marker = '''                    </div>
                </div>
            </div>
        </div>

        <!-- Contact Section -->'''

# Insert the new FAQs
content = content.replace(marker, new_faqs + marker)

# Write back
with open('public/landing.html', 'w') as f:
    f.write(content)

print("✅ Added 8 new FAQ questions (5-12) to landing.html")
