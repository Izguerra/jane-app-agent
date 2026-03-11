
export interface AgentFormData {
    // Step 1: Configure
    name: string;
    language: string;
    voice_id: string;
    avatar: string;
    avatarUrl: string;
    avatarFile: File | null;
    primaryFunction: string;
    conversationStyle: string;
    welcomeGreeting: string;
    businessName: string;
    websiteUrl: string;
    businessDescription: string;
    email: string;
    phone: string;
    address: string;
    services: string;
    hoursOfOperation: string;
    faqItems: { question: string; answer: string; keywords?: string[] }[];
    refUrls: string[];
    kbFiles: File[];
    existingKbUrls: string[];

    // NEW: Avatar Configuration
    tavusReplicaId?: string;
    tavusPersonaId?: string;
    anamPersonaId?: string;
    avatarProvider?: 'tavus' | 'anam';
    avatarVoiceId?: string;
    useTavusAvatar: boolean;

    // Step 2: Capabilities
    allowedWorkerTypes: string[];
    enabledSkillIds: string[];
    openClawInstanceId?: string;

    // Step 3: Behavior
    soul: string;
    creativityLevel: number;
    responseLength: number;
    proactiveFollowups: boolean;
    intentRules: { intent: string; action: string }[];
    handoffMessage: string;
    notificationEmail: string;
    slackWebhook: string;
    autoEscalate: boolean;

    // Step 3: Deployment
    deploymentChannel: string;
    accentColor: string;
    widgetIcon: string;
    widgetIconUrl: string;
    widgetIconFile: File | null;
    widgetPosition: string;
    removeBranding: boolean;
    whitelistedDomains: string;
    isActive: boolean;

    // Agent Type
    agentType?: string; // allow string instead of just "business" | "personal"

    // Personal Agent Profile
    ownerName?: string;
    location?: string;
    timezone?: string;
    favoriteFoods?: string;
    favoriteRestaurants?: string;
    favoriteMusic?: string;
    favoriteActivities?: string;
    otherInterests?: string;
    likes?: string;
    dislikes?: string;

    // Legacy / OpenClaw
    personalPreferences?: string;
    user_email?: string;
    user_phone?: string;
}
