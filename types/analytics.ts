export interface AnalyticsSummary {
    total_conversations: number;
    avg_duration: number;
    successful_conversations: number;
    total_minutes: number;
    total_agents: number;
    total_messages: number;
    active_campaigns: number;
    total_appointments: number;

    // Subscription / Plan Usage
    minutes_limit: number;
    minutes_used: number;

    sms_limit: number;
    sms_used: number;

    whatsapp_limit: number;
    whatsapp_used: number;

    chatbot_limit: number;
    chatbot_used: number;

    agents_limit: number;
    conversations_limit: number;
}

export interface AnalyticsHistoryItem {
    date: string;
    count: number;
}

export interface CommunicationLogItem {
    id: string;
    type: string;
    direction: string;
    status: string;
    duration: number;
    started_at: string;
}

export interface PaginatedLogs {
    items: CommunicationLogItem[];
    total: number;
}
