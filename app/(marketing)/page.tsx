import { Button } from '@/components/ui/button';
import { ArrowRight, MessageSquare, BarChart3, Zap, Globe, Shield, Sparkles, Check, BrainCircuit, User, Calendar, History, FileText, Megaphone, Heart, Users, Code } from 'lucide-react';
import Link from 'next/link';
import { FAQItem } from '@/components/faq-item';
import { ContactForm } from '@/components/contact-form';
import { NewsletterForm } from '@/components/marketing/newsletter-form';


export default function HomePage() {
  return (
    <main className="bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <section className="py-12 lg:py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-20">
            {/* Hero Content (Left) */}
            <div className="flex flex-col gap-8 flex-1 w-full max-w-[600px] text-center lg:text-left items-center lg:items-start z-10">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-orange-200 bg-orange-50 text-orange-600 text-xs font-bold w-fit">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                </span>
                AI-Powered Customer Support
              </div>

              {/* Headline */}
              <div className="flex flex-col gap-4">
                <h1 className="text-5xl lg:text-6xl font-black leading-[1.1] tracking-tight text-gray-900">
                  Your AI Customer Support Agent,
                  <span className="block bg-gradient-to-r from-orange-500 to-orange-600 bg-clip-text text-transparent mt-2">
                    Ready in Minutes
                  </span>
                </h1>
                <p className="text-lg text-gray-600 leading-relaxed max-w-[540px]">
                  Create intelligent voice and text chatbots trained on your business data. Handle customer inquiries 24/7 with no coding required.
                </p>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
                <Link href="#contact">
                  <Button
                    size="lg"
                    className="min-w-[160px] h-12 text-base font-bold rounded-xl bg-orange-600 hover:bg-orange-700 shadow-lg shadow-orange-600/25 transition-all"
                  >
                    <ArrowRight className="mr-2 h-5 w-5" />
                    Get in Touch
                  </Button>
                </Link>
                <Link href="#features">
                  <Button
                    size="lg"
                    variant="outline"
                    className="min-w-[160px] h-12 text-base font-bold rounded-xl border-2 transition-all"
                  >
                    Explore Features
                  </Button>
                </Link>
              </div>

              {/* Social Proof */}
              <div className="flex flex-col gap-3 pt-4 items-center lg:items-start">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  No credit card required • 14-day free trial • Cancel anytime
                </p>
              </div>
            </div>

            {/* Hero Visual (Right) - Chat Demo */}
            <div className="flex-1 w-full relative">
              {/* Decorative blurred blobs */}
              <div className="absolute -top-10 -right-10 w-72 h-72 bg-orange-500/20 rounded-full blur-3xl opacity-50 pointer-events-none"></div>
              <div className="absolute -top-10 -left-10 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl opacity-50 pointer-events-none"></div>

              {/* Coming Soon Badge */}
              <div className="absolute -top-6 -right-6 md:-top-8 md:-right-8 bg-black text-white px-6 py-2 rounded-full font-bold text-sm md:text-base shadow-xl z-30 transform rotate-12 border-4 border-white">
                COMING SOON
              </div>

              {/* Main Chat Card */}
              <div className="relative bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 z-10 transform transition hover:-translate-y-1 duration-500">
                {/* Card Header */}
                <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="size-10 rounded-full bg-gradient-to-tr from-orange-500 to-orange-400 flex items-center justify-center text-white">
                        <MessageSquare className="h-5 w-5" />
                      </div>
                      <span className="absolute bottom-0 right-0 size-3 rounded-full bg-green-500 border-2 border-white"></span>
                    </div>
                    <div>
                      <h3 className="font-bold text-sm text-gray-900">SupaAgent</h3>
                      <p className="text-xs text-gray-500">AI Customer Success • Online</p>
                    </div>
                  </div>
                </div>

                {/* Chat Messages */}
                <div className="flex flex-col gap-4 min-h-[260px]">
                  {/* User Message */}
                  <div className="flex justify-end">
                    <div className="bg-orange-600 text-white px-4 py-3 rounded-2xl rounded-tr-none max-w-[85%] shadow-md">
                      <p className="text-sm font-medium">Hi! I need to reschedule my appointment specifically to next Tuesday at 2 PM.</p>
                    </div>
                  </div>

                  {/* AI Message */}
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-900 px-4 py-3 rounded-2xl rounded-tl-none max-w-[90%] border border-gray-200">
                      <p className="text-sm leading-relaxed">Sure thing, Sarah! I found an opening for <span className="font-semibold">Tuesday, Oct 24th at 2:00 PM</span>.</p>
                      <p className="text-sm leading-relaxed mt-2">
                        I've updated your booking. You'll receive a confirmation email shortly. Is there anything else I can help with?
                      </p>
                    </div>
                  </div>

                  {/* Typing Indicator / Voice Active */}
                  <div className="flex items-center gap-3 mt-auto pt-2">
                    <div className="flex items-center justify-center size-8 rounded-full bg-gray-100 text-orange-600">
                      <Sparkles className="h-4 w-4" />
                    </div>
                    {/* Waveform visual */}
                    <div className="flex items-center gap-1 h-8">
                      <div className="w-1 bg-orange-600 rounded-full h-3 animate-pulse"></div>
                      <div className="w-1 bg-orange-600 rounded-full h-5 animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-1 bg-orange-600 rounded-full h-3 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-1 bg-orange-600 rounded-full h-6 animate-pulse" style={{ animationDelay: '0.3s' }}></div>
                      <div className="w-1 bg-orange-600 rounded-full h-4 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                    <span className="text-xs text-gray-500 font-medium">AI is typing...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>


      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header */}
          <div className="text-center mb-16">
            <span className="bg-orange-100 text-orange-600 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
              Features & Benefits
            </span>
            <h2 className="text-3xl md:text-5xl font-black text-gray-900 mt-4 mb-4 leading-tight tracking-tight max-w-3xl mx-auto">
              Intelligence that Speaks Your Customer's Language
            </h2>
            <p className="text-gray-500 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
              Explore how SupaAgent transforms your customer experience with cutting-edge AI voice and chat capabilities.
            </p>
          </div>

          {/* Feature Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            <FeatureCard
              icon={<Zap className="h-6 w-6" />}
              title="Native Skill Engine"
              description="Orchestrate complex multi-step tasks natively. We've implemented the same powerful skills found in OpenClaw, but with added enterprise-grade security and isolated execution."
              badge="Secure & Advanced"
            />
            <FeatureCard
              icon={<Megaphone className="h-6 w-6" />}
              title="Native Telephony"
              description="Professional outbound and inbound calling via Telnyx and LiveKit SIP. Your agent is a phone-call away."
            />
            <FeatureCard
              icon={<MessageSquare className="h-6 w-6" />}
              title="Unified Voice & Chat"
              description="Experience seamless omnichannel support that allows your customers to switch between voice and text instantly without losing context."
            />
            <FeatureCard
              icon={<BarChart3 className="h-6 w-6" />}
              title="Real-time Analytics"
              description="Track sentiment, resolution times, and customer satisfaction in real-time dashboards with actionable insights."
            />
            <FeatureCard
              icon={<Globe className="h-6 w-6" />}
              title="Multilingual Support"
              description="Speak over 50 languages fluently. Our AI adapts to your customer's preferred language automatically."
            />
            <FeatureCard
              icon={<Users className="h-6 w-6" />}
              title="Lead Management"
              description="Capture, qualify, and track leads automatically, integrating directly with your CRM."
            />
            <FeatureCard
              icon={<Code className="h-6 w-6" />}
              title="Easy Embed"
              description="Embed your chatbot or voice assistant directly into your website with a simple one-line snippet."
            />
            <FeatureCard
              icon={<User className="h-6 w-6" />}
              title="AI Video Avatars"
              description="Ultra-realistic visual agents that bring a human face to your digital interactions."
              badge="Pro Plan"
            />
            <FeatureCard
              icon={<BrainCircuit className="h-6 w-6" />}
              title="Context-Aware memory"
              description="Remembers past interactions, purchase history, and user preferences to deliver hyper-personalized support."
            />
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-black text-gray-900 mb-4 leading-tight tracking-tight">
              How It Works
            </h2>
            <p className="text-gray-600 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
              From data to agent in minutes. Transform complex AI processes into a simple 5-step workflow.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 relative max-w-7xl mx-auto">
            {/* Step 1 */}
            <div className="group flex flex-col items-center text-center p-6 rounded-2xl bg-white border border-gray-200 shadow-sm hover:shadow-lg transition-all">
              <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4 ring-4 ring-white group-hover:ring-orange-50 transition-all">
                <BrainCircuit className="h-8 w-8 text-orange-600" />
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-orange-600 text-xs font-bold uppercase tracking-wider">Step 1</span>
                <h3 className="text-gray-900 text-lg font-bold">Configure Soul</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Name your agent, define its personality, and upload your knowledge base.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="group flex flex-col items-center text-center p-6 rounded-2xl bg-white border border-gray-200 shadow-sm hover:shadow-lg transition-all relative overflow-hidden">
              <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4 ring-4 ring-white group-hover:ring-orange-50 transition-all">
                <User className="h-8 w-8 text-orange-600" />
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-orange-600 text-xs font-bold uppercase tracking-wider">Step 2</span>
                <h3 className="text-gray-900 text-lg font-bold">Identity Mode</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Choose between Voice, Text, or high-fidelity Video Avatar modes.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="group flex flex-col items-center text-center p-6 rounded-2xl bg-white border border-gray-200 shadow-sm hover:shadow-lg transition-all">
              <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4 ring-4 ring-white group-hover:ring-orange-50 transition-all">
                <Zap className="h-8 w-8 text-orange-600" />
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-orange-600 text-xs font-bold uppercase tracking-wider">Step 3</span>
                <h3 className="text-gray-900 text-lg font-bold">Enable Skills</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Equip your agent with native skills like calendar booking, CRM updates, and browser automation.
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="group flex flex-col items-center text-center p-6 rounded-2xl bg-white border border-gray-200 shadow-sm hover:shadow-lg transition-all">
              <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4 ring-4 ring-white group-hover:ring-orange-50 transition-all">
                <Code className="h-8 w-8 text-orange-600" />
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-orange-600 text-xs font-bold uppercase tracking-wider">Step 4</span>
                <h3 className="text-gray-900 text-lg font-bold">Connect Tech</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Connect to your professional phone line or embed on your website.
                </p>
              </div>
            </div>

            {/* Step 5 */}
            <div className="group flex flex-col items-center text-center p-6 rounded-2xl bg-white border border-gray-200 shadow-sm hover:shadow-lg transition-all">
              <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4 ring-4 ring-white group-hover:ring-orange-50 transition-all">
                <Globe className="h-8 w-8 text-orange-600" />
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-orange-600 text-xs font-bold uppercase tracking-wider">Step 5</span>
                <h3 className="text-gray-900 text-lg font-bold">Deploy Agent</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Go live globally. Your agent handles inquiries 24/7 across all channels.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>


      {/* Newsletter Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-orange-50 rounded-3xl p-8 md:p-12 text-center max-w-4xl mx-auto border border-orange-100">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Stay in the Loop
            </h2>
            <p className="text-gray-600 text-lg mb-8 max-w-2xl mx-auto">
              Join our newsletter to get the latest updates on AI features, product releases, and customer support trends.
            </p>
            <NewsletterForm />
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-gray-900 mb-4 leading-tight tracking-tight">
              Frequently Asked Questions
            </h2>
            <p className="text-gray-600 text-lg leading-relaxed max-w-2xl mx-auto">
              Everything you need to know about SupaAgent. Can't find the answer you're looking for? Chat with our friendly team.
            </p>
          </div>

          <div className="flex flex-col gap-4">
            <FAQItem
              question="Can I change plans later?"
              answer="Yes, you can upgrade or downgrade your plan at any time from your account settings. Changes take effect immediately."
              defaultOpen={true}
            />
            <FAQItem
              question="What happens if I hit my limit?"
              answer="Your agents will pause until the next billing cycle. You can always purchase a booster pack or upgrade to keep running."
            />
            <FAQItem
              question="Is voice synthesis included?"
              answer="Voice capabilities are available starting on the Professional plan. The Starter plan includes text-based chat only."
            />
            <FAQItem
              question="Is my data secure?"
              answer="Data security is our top priority. We use enterprise-grade encryption for all data and strictly isolate each workspace to ensure agents can only access authorized files and information. Our platform includes robust system-level guardrails, and you have the power to define your own custom guardrails for every agent. Furthermore, we never use your private data to train our public models."
            />
            <FAQItem
              question="How long does setup take?"
              answer="Most users are up and running in under 15 minutes. Upload your knowledge base, configure your agent settings, and you're ready to go live."
            />
            <FAQItem
              question="What integrations are supported?"
              answer="SupaAgent integrates seamlessly with WhatsApp, Google Calendar, Twilio, Telnyx, and LiveKit. We also provide native support for professional phone systems via SIP trunks and custom API webhooks for bespoke enterprise integrations."
            />
            <FAQItem
              question="Can I use my own phone number?"
              answer="Yes! Our new Telephony integration allows you to port your existing business numbers or instantly provision new local and toll-free ones. We also support direct integration with your existing phone systems or PBX via SIP."
            />
            <FAQItem
              question="What languages are supported?"
              answer="Our AI agents support 50+ languages for text chat. Voice capabilities are available in English, Spanish, French, German, and more."
            />
            <FAQItem
              question="Does it handle appointment booking?"
              answer="Yes! Our agents can book, reschedule, and cancel appointments automatically using your Google Calendar integration with real-time availability."
            />
            <FAQItem
              question="What kind of support do you offer?"
              answer="Starter plans include email support. Professional plans get priority support with faster response times. Enterprise customers have dedicated success managers."
            />
            <FAQItem
              question="How does the knowledge base work?"
              answer="Upload documents, FAQs, or service information. Our AI learns from your content to provide accurate, context-aware responses to customer questions."
            />
            <FAQItem
              question="Can I cancel anytime?"
              answer="Yes, you can cancel your subscription at any time. Your service will continue until the end of your current billing period with no penalties or fees."
            />
          </div>
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Trusted by Growing Businesses
            </h2>
            <p className="text-xl text-gray-600">
              Join hundreds of companies automating their customer support
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <StatCard number="10,000+" label="Conversations Handled" />
            <StatCard number="95%" label="Customer Satisfaction" />
            <StatCard number="24/7" label="Always Available" />
          </div>
        </div>
      </section>

      {/* Contact Us Section */}
      <section id="contact" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-gray-900 mb-4 leading-tight tracking-tight">
              Let's Start a Conversation
            </h2>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto leading-relaxed">
              Have questions about SupaAgent? We're here to help you automate your customer experience with our AI experts.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            {/* Left Column: Contact Form */}
            <div className="lg:col-span-7">
              <ContactForm />
            </div>

            {/* Right Column: Contact Info */}
            <div className="lg:col-span-5 flex flex-col gap-8">
              <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm">
                <h3 className="text-gray-900 text-xl font-bold mb-6">Contact Information</h3>
                <div className="flex flex-col gap-6">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-orange-100 text-orange-600">
                      <MessageSquare className="h-5 w-5" />
                    </div>
                    <div className="flex flex-col">
                      <p className="text-gray-900 text-base font-bold">Email</p>
                      <a className="text-gray-600 text-sm hover:text-orange-600 transition-colors" href="mailto:info@supaagent.com">
                        info@supaagent.com
                      </a>
                    </div>
                  </div>


                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-orange-600 to-pink-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Transform Your Customer Support?
          </h2>
          <p className="text-xl text-orange-100 mb-8">
            Contact us today to schedule a demo and see SupaAgent in action.
          </p>
          <a href="#contact">
            <Button
              size="lg"
              className="text-lg px-8 py-6 rounded-full bg-white text-orange-600 hover:bg-gray-100"
            >
              Get in Touch
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </a>
        </div>
      </section>
    </main>
  );
}

function FeatureCard({ icon, title, description, badge }: { icon: React.ReactNode; title: string; description: string; badge?: string }) {
  return (
    <div className="p-6 rounded-xl border border-gray-200 hover:border-orange-300 hover:shadow-lg transition-all relative">
      {badge && (
        <span className="absolute top-4 right-4 bg-orange-100 text-orange-700 text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider">
          {badge}
        </span>
      )}
      <div className="w-12 h-12 rounded-lg bg-orange-100 text-orange-600 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function StatCard({ number, label }: { number: string; label: string }) {
  return (
    <div className="text-center p-8 bg-white rounded-xl shadow-sm">
      <div className="text-4xl font-bold text-orange-600 mb-2">{number}</div>
      <div className="text-gray-600">{label}</div>
    </div>
  );
}
