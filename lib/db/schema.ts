import {
  pgTable,
  varchar,
  text,
  timestamp,
  integer,
  boolean as pgBoolean,
  json,
  real,
} from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

export const users = pgTable('users', {
  id: varchar('id', { length: 36 }).primaryKey(),
  name: varchar('name', { length: 100 }),
  firstName: varchar('first_name', { length: 50 }),
  lastName: varchar('last_name', { length: 50 }),
  username: varchar('username', { length: 50 }).unique(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  role: varchar('role', { length: 20 }).notNull().default('member'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
  deletedAt: timestamp('deleted_at'),
});

export const teams = pgTable('teams', {
  id: varchar('id', { length: 36 }).primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
  stripeCustomerId: text('stripe_customer_id').unique(),
  stripeSubscriptionId: text('stripe_subscription_id').unique(),
  stripeProductId: text('stripe_product_id'),
  planName: varchar('plan_name', { length: 50 }),
  subscriptionStatus: varchar('subscription_status', { length: 20 }),
});

export const teamMembers = pgTable('team_members', {
  id: varchar('id', { length: 36 }).primaryKey(),
  userId: varchar('user_id', { length: 36 })
    .notNull()
    .references(() => users.id),
  teamId: varchar('team_id', { length: 36 })
    .notNull()
    .references(() => teams.id),
  role: varchar('role', { length: 50 }).notNull(),
  joinedAt: timestamp('joined_at').notNull().defaultNow(),
});

export const activityLogs = pgTable('activity_logs', {
  id: varchar('id', { length: 36 }).primaryKey(),
  teamId: varchar('team_id', { length: 36 })
    .notNull()
    .references(() => teams.id),
  userId: varchar('user_id', { length: 36 }).references(() => users.id),
  action: text('action').notNull(),
  timestamp: timestamp('timestamp').notNull().defaultNow(),
  ipAddress: varchar('ip_address', { length: 45 }),
});

export const invitations = pgTable('invitations', {
  id: varchar('id', { length: 36 }).primaryKey(),
  teamId: varchar('team_id', { length: 36 })
    .notNull()
    .references(() => teams.id),
  email: varchar('email', { length: 255 }).notNull(),
  role: varchar('role', { length: 50 }).notNull(),
  invitedBy: varchar('invited_by', { length: 36 })
    .notNull()
    .references(() => users.id),
  invitedAt: timestamp('invited_at').notNull().defaultNow(),
  status: varchar('status', { length: 20 }).notNull().default('pending'),
});

export const teamsRelations = relations(teams, ({ many }) => ({
  teamMembers: many(teamMembers),
  activityLogs: many(activityLogs),
  invitations: many(invitations),
}));

export const usersRelations = relations(users, ({ many }) => ({
  teamMembers: many(teamMembers),
  invitationsSent: many(invitations),
}));

export const invitationsRelations = relations(invitations, ({ one }) => ({
  team: one(teams, {
    fields: [invitations.teamId],
    references: [teams.id],
  }),
  invitedBy: one(users, {
    fields: [invitations.invitedBy],
    references: [users.id],
  }),
}));

export const teamMembersRelations = relations(teamMembers, ({ one }) => ({
  user: one(users, {
    fields: [teamMembers.userId],
    references: [users.id],
  }),
  team: one(teams, {
    fields: [teamMembers.teamId],
    references: [teams.id],
  }),
}));

export const activityLogsRelations = relations(activityLogs, ({ one }) => ({
  team: one(teams, {
    fields: [activityLogs.teamId],
    references: [teams.id],
  }),
  user: one(users, {
    fields: [activityLogs.userId],
    references: [users.id],
  }),
}));

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Team = typeof teams.$inferSelect;
export type NewTeam = typeof teams.$inferInsert;
export type TeamMember = typeof teamMembers.$inferSelect;
export type NewTeamMember = typeof teamMembers.$inferInsert;
export type ActivityLog = typeof activityLogs.$inferSelect;
export type NewActivityLog = typeof activityLogs.$inferInsert;
export type Invitation = typeof invitations.$inferSelect;
export type NewInvitation = typeof invitations.$inferInsert;
export type TeamDataWithMembers = Team & {
  teamMembers: (TeamMember & {
    user: Pick<User, 'id' | 'name' | 'email'>;
  })[];
};

export const workspaces = pgTable('workspaces', {
  id: varchar('id', { length: 36 }).primaryKey(),
  teamId: varchar('team_id', { length: 36 })
    .notNull()
    .references(() => teams.id),
  name: varchar('name', { length: 100 }).notNull(),
  address: text('address'),
  phone: varchar('phone', { length: 20 }),
  email: varchar('email', { length: 255 }),
  website: varchar('website', { length: 255 }),

  description: text('description'),
  services: text('services'),
  businessHours: text('business_hours'), // JSON string
  faq: text('faq'), // JSON string
  referenceUrls: text('reference_urls'), // JSON string
  conversationsThisMonth: integer('conversations_this_month').default(0),
  voiceMinutesThisMonth: integer('voice_minutes_this_month').default(0),
  inboundAgentPhone: varchar('inbound_agent_phone', { length: 50 }).unique(),

  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const integrations = pgTable('integrations', {
  id: varchar('id', { length: 36 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 36 })
    .notNull()
    .references(() => workspaces.id),
  provider: varchar('provider', { length: 50 }).notNull(),
  credentials: text('credentials').notNull(),
  settings: text('settings'),
  isActive: pgBoolean('is_active').default(true),
  agentId: varchar('agent_id', { length: 36 }).references(() => agents.id),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const agents = pgTable('agents', {
  id: varchar('id', { length: 36 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 36 })
    .notNull()
    .references(() => workspaces.id),
  name: varchar('name', { length: 100 }).notNull().default('My Agent'),
  voiceId: varchar('voice_id', { length: 50 }),
  language: varchar('language', { length: 10 }).default('en'),
  promptTemplate: text('prompt_template'),
  welcomeMessage: text('welcome_message'),
  isOrchestrator: pgBoolean('is_orchestrator').default(false),
  description: text('description'),
  isActive: pgBoolean('is_active').default(true),
  settings: json('settings'),
  allowedWorkerTypes: json('allowed_worker_types').$type<string[]>(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const communications = pgTable('communications', {
  id: varchar('id', { length: 36 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 36 })
    .notNull()
    .references(() => workspaces.id),
  type: varchar('type', { length: 20 }).notNull(),
  direction: varchar('direction', { length: 20 }).notNull(),
  status: varchar('status', { length: 20 }).notNull(),
  duration: integer('duration').default(0),
  transcript: text('transcript'),
  summary: text('summary'),
  sentiment: varchar('sentiment', { length: 20 }),

  channel: varchar('channel', { length: 50 }),
  integrationId: varchar('integration_id', { length: 36 }).references(() => integrations.id),
  recordingUrl: text('recording_url'),
  userIdentifier: varchar('user_identifier', { length: 255 }),
  agentId: varchar('agent_id', { length: 36 }).references(() => agents.id),

  startedAt: timestamp('started_at').notNull().defaultNow(),
  endedAt: timestamp('ended_at'),
});

export const documents = pgTable('documents', {
  id: varchar('id', { length: 36 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 36 })
    .notNull()
    .references(() => workspaces.id),
  filename: varchar('filename', { length: 255 }).notNull(),
  fileType: varchar('file_type', { length: 50 }).notNull(),
  contentHash: varchar('content_hash', { length: 64 }),
  uploadedAt: timestamp('uploaded_at').notNull().defaultNow(),
});

export const customers = pgTable('customers', {
  id: varchar('id', { length: 36 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 36 })
    .notNull()
    .references(() => workspaces.id),
  firstName: varchar('first_name', { length: 100 }),
  lastName: varchar('last_name', { length: 100 }),
  email: varchar('email', { length: 255 }),
  phone: varchar('phone', { length: 50 }),
  status: varchar('status', { length: 20 }).notNull().default('active'),
  plan: varchar('plan', { length: 50 }).default('Starter'),
  usageLimit: integer('usage_limit').default(1000),
  usageUsed: integer('usage_used').default(0),
  avatarUrl: varchar('avatar_url', { length: 255 }),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const phoneNumbers = pgTable('phone_numbers', {
  id: varchar('id', { length: 36 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 36 })
    .notNull()
    .references(() => workspaces.id),
  phoneNumber: varchar('phone_number', { length: 20 }).notNull().unique(),
  friendlyName: varchar('friendly_name', { length: 255 }),
  countryCode: varchar('country_code', { length: 2 }),
  voiceEnabled: pgBoolean('voice_enabled').default(false),
  smsEnabled: pgBoolean('sms_enabled').default(false),
  whatsappEnabled: pgBoolean('whatsapp_enabled').default(false),
  voiceUrl: text('voice_url'),
  whatsappWebhookUrl: text('whatsapp_webhook_url'),
  twilioSid: varchar('twilio_sid', { length: 255 }).unique(),
  agentId: varchar('agent_id', { length: 36 }).references(() => agents.id),
  stripeSubscriptionItemId: varchar('stripe_subscription_item_id', { length: 255 }),
  monthlyCost: integer('monthly_cost'),
  purchaseDate: timestamp('purchase_date').notNull().defaultNow(),
  isActive: pgBoolean('is_active').default(true),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const conversationMessages = pgTable('conversation_messages', {
  id: varchar('id', { length: 36 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 36 })
    .notNull()
    .references(() => workspaces.id),
  userIdentifier: varchar('user_identifier', { length: 255 }).notNull(),
  channel: varchar('channel', { length: 50 }).notNull(),
  role: varchar('role', { length: 20 }).notNull(),
  content: text('content').notNull(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  communicationId: varchar('communication_id', { length: 36 }).references(() => communications.id),
});

export const whatsappTemplates = pgTable('whatsapp_templates', {
  id: varchar('id', { length: 36 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 36 })
    .notNull()
    .references(() => workspaces.id),
  name: varchar('name', { length: 255 }).notNull(),
  language: varchar('language', { length: 10 }).default('en'),
  category: varchar('category', { length: 50 }),
  status: varchar('status', { length: 50 }),
  templateId: varchar('template_id', { length: 255 }),
  components: text('components'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const workspacesRelations = relations(workspaces, ({ one, many }) => ({
  team: one(teams, {
    fields: [workspaces.teamId],
    references: [teams.id],
  }),
  agents: many(agents),
  communications: many(communications),
  integrations: many(integrations),
  documents: many(documents),
  customers: many(customers),
  phoneNumbers: many(phoneNumbers),
  whatsappTemplates: many(whatsappTemplates),
}));

export const integrationsRelations = relations(integrations, ({ one }) => ({
  workspace: one(workspaces, {
    fields: [integrations.workspaceId],
    references: [workspaces.id],
  }),
}));

export const agentsRelations = relations(agents, ({ one }) => ({
  workspace: one(workspaces, {
    fields: [agents.workspaceId],
    references: [workspaces.id],
  }),
}));

export const communicationsRelations = relations(communications, ({ one, many }) => ({
  workspace: one(workspaces, {
    fields: [communications.workspaceId],
    references: [workspaces.id],
  }),
  messages: many(conversationMessages),
}));

export const documentsRelations = relations(documents, ({ one }) => ({
  workspace: one(workspaces, {
    fields: [documents.workspaceId],
    references: [workspaces.id],
  }),
}));

export const customersRelations = relations(customers, ({ one }) => ({
  workspace: one(workspaces, {
    fields: [customers.workspaceId],
    references: [workspaces.id],
  }),
}));

export const phoneNumbersRelations = relations(phoneNumbers, ({ one }) => ({
  workspace: one(workspaces, {
    fields: [phoneNumbers.workspaceId],
    references: [workspaces.id],
  }),
}));

export const conversationMessagesRelations = relations(conversationMessages, ({ one }) => ({
  workspace: one(workspaces, {
    fields: [conversationMessages.workspaceId],
    references: [workspaces.id],
  }),
  communication: one(communications, {
    fields: [conversationMessages.communicationId],
    references: [communications.id],
  }),
}));

export const whatsappTemplatesRelations = relations(whatsappTemplates, ({ one }) => ({
  workspace: one(workspaces, {
    fields: [whatsappTemplates.workspaceId],
    references: [workspaces.id],
  }),
}));

export const contactSubmissions = pgTable('contact_submissions', {
  id: varchar('id', { length: 36 }).primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  email: varchar('email', { length: 255 }).notNull(),
  subject: varchar('subject', { length: 100 }).notNull(),
  message: text('message').notNull(),
  status: varchar('status', { length: 20 }).notNull().default('new'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

export type ContactSubmission = typeof contactSubmissions.$inferSelect;
export type NewContactSubmission = typeof contactSubmissions.$inferInsert;

export enum ActivityType {
  SIGN_UP = 'SIGN_UP',
  SIGN_IN = 'SIGN_IN',
  SIGN_OUT = 'SIGN_OUT',
  UPDATE_PASSWORD = 'UPDATE_PASSWORD',
  DELETE_ACCOUNT = 'DELETE_ACCOUNT',
  UPDATE_ACCOUNT = 'UPDATE_ACCOUNT',
  CREATE_TEAM = 'CREATE_TEAM',
  REMOVE_TEAM_MEMBER = 'REMOVE_TEAM_MEMBER',
  INVITE_TEAM_MEMBER = 'INVITE_TEAM_MEMBER',
  ACCEPT_INVITATION = 'ACCEPT_INVITATION',
}


export const workerTemplates = pgTable('worker_templates', {
  id: varchar('id', { length: 50 }).primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  slug: varchar('slug', { length: 100 }).notNull().unique(),
  description: text('description'),
  category: varchar('category', { length: 50 }).default('general'),
  defaultInstructions: text('default_instructions'),
  parameterSchema: json('parameter_schema').default({}),
  requiredTools: json('required_tools').default([]),
  requiredIntegrations: json('required_integrations').default([]),
  outcomePrice: integer('outcome_price').default(0),
  evaluationLogic: json('evaluation_logic').default({}),
  icon: varchar('icon', { length: 50 }).default('bot'),
  color: varchar('color', { length: 20 }).default('orange'),
  isActive: pgBoolean('is_active').default(true),
  isSystem: pgBoolean('is_system').default(false),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

export const workerTasks = pgTable('worker_tasks', {
  id: varchar('id', { length: 50 }).primaryKey(),
  workspaceId: varchar('workspace_id', { length: 50 }).notNull().references(() => workspaces.id, { onDelete: 'cascade' }),
  templateId: varchar('template_id', { length: 50 }).references(() => workerTemplates.id),
  workerType: varchar('worker_type', { length: 100 }).notNull(),
  customerId: varchar('customer_id', { length: 100 }),
  createdByUserId: varchar('created_by_user_id', { length: 50 }),
  status: varchar('status', { length: 20 }).notNull().default('pending'),
  inputData: json('input_data').default({}),
  outputData: json('output_data'),
  outcomeStatus: varchar('outcome_status', { length: 50 }).default('pending_eval'),
  outcomeScore: real('outcome_score'),
  stepsCompleted: integer('steps_completed').default(0),
  stepsTotal: integer('steps_total'),
  currentStep: varchar('current_step', { length: 255 }),
  logs: json('logs').default([]),
  errorMessage: text('error_message'),
  tokensUsed: integer('tokens_used').default(0),
  apiCalls: json('api_calls').default({}),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  startedAt: timestamp('started_at'),
  completedAt: timestamp('completed_at'),
  rating: integer('rating'),
  ratingFeedback: text('rating_feedback'),
  ratedAt: timestamp('rated_at'),
  ratedByUserId: varchar('rated_by_user_id', { length: 50 }),
  outcomeFeeCents: integer('outcome_fee_cents').default(0),
  totalFeeCents: integer('total_fee_cents').default(0),
  feeBilled: pgBoolean('fee_billed').default(false),
  dispatchedByAgentId: varchar('dispatched_by_agent_id', { length: 50 }).references(() => agents.id),
});

export const workerTemplatesRelations = relations(workerTemplates, ({ many }) => ({
  tasks: many(workerTasks),
}));

export const workerTasksRelations = relations(workerTasks, ({ one }) => ({
  workspace: one(workspaces, {
    fields: [workerTasks.workspaceId],
    references: [workspaces.id],
  }),
  template: one(workerTemplates, {
    fields: [workerTasks.templateId],
    references: [workerTemplates.id],
  }),
}));
