CREATE TABLE "agents" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"workspace_id" varchar(20) NOT NULL,
	"name" varchar(100) DEFAULT 'My Agent' NOT NULL,
	"voice_id" varchar(50),
	"language" varchar(10) DEFAULT 'en',
	"prompt_template" text,
	"welcome_message" text,
	"is_orchestrator" boolean DEFAULT false,
	"description" text,
	"is_active" boolean DEFAULT true,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "communications" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"workspace_id" varchar(20) NOT NULL,
	"type" varchar(20) NOT NULL,
	"direction" varchar(20) NOT NULL,
	"status" varchar(20) NOT NULL,
	"duration" integer DEFAULT 0,
	"transcript" text,
	"summary" text,
	"sentiment" varchar(20),
	"channel" varchar(50),
	"recording_url" text,
	"user_identifier" varchar(255),
	"agent_id" varchar(20),
	"started_at" timestamp DEFAULT now() NOT NULL,
	"ended_at" timestamp
);
--> statement-breakpoint
CREATE TABLE "conversation_messages" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"workspace_id" varchar(20) NOT NULL,
	"user_identifier" varchar(255) NOT NULL,
	"channel" varchar(50) NOT NULL,
	"role" varchar(20) NOT NULL,
	"content" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"communication_id" varchar(20)
);
--> statement-breakpoint
CREATE TABLE "customers" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"workspace_id" varchar(20) NOT NULL,
	"first_name" varchar(100),
	"last_name" varchar(100),
	"email" varchar(255),
	"phone" varchar(50),
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "documents" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"workspace_id" varchar(20) NOT NULL,
	"filename" varchar(255) NOT NULL,
	"file_type" varchar(50) NOT NULL,
	"content_hash" varchar(64),
	"uploaded_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "integrations" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"workspace_id" varchar(20) NOT NULL,
	"provider" varchar(50) NOT NULL,
	"credentials" text NOT NULL,
	"settings" text,
	"is_active" boolean DEFAULT true,
	"agent_id" varchar(20),
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "phone_numbers" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"workspace_id" varchar(20) NOT NULL,
	"phone_number" varchar(20) NOT NULL,
	"friendly_name" varchar(255),
	"country_code" varchar(2),
	"voice_enabled" boolean DEFAULT false,
	"sms_enabled" boolean DEFAULT false,
	"whatsapp_enabled" boolean DEFAULT false,
	"voice_url" text,
	"whatsapp_webhook_url" text,
	"twilio_sid" varchar(255),
	"agent_id" varchar(20),
	"stripe_subscription_item_id" varchar(255),
	"monthly_cost" integer,
	"purchase_date" timestamp DEFAULT now() NOT NULL,
	"is_active" boolean DEFAULT true,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "phone_numbers_phone_number_unique" UNIQUE("phone_number"),
	CONSTRAINT "phone_numbers_twilio_sid_unique" UNIQUE("twilio_sid")
);
--> statement-breakpoint
CREATE TABLE "whatsapp_templates" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"workspace_id" varchar(20) NOT NULL,
	"name" varchar(255) NOT NULL,
	"language" varchar(10) DEFAULT 'en',
	"category" varchar(50),
	"status" varchar(50),
	"template_id" varchar(255),
	"components" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "workspaces" (
	"id" varchar(20) PRIMARY KEY NOT NULL,
	"team_id" varchar(20) NOT NULL,
	"name" varchar(100) NOT NULL,
	"address" text,
	"phone" varchar(20),
	"email" varchar(255),
	"website" varchar(255),
	"description" text,
	"services" text,
	"business_hours" text,
	"faq" text,
	"reference_urls" text,
	"conversations_this_month" integer DEFAULT 0,
	"voice_minutes_this_month" integer DEFAULT 0,
	"inbound_agent_phone" varchar(50),
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "workspaces_inbound_agent_phone_unique" UNIQUE("inbound_agent_phone")
);
--> statement-breakpoint
ALTER TABLE "activity_logs" ALTER COLUMN "id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "activity_logs" ALTER COLUMN "team_id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "activity_logs" ALTER COLUMN "user_id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "invitations" ALTER COLUMN "id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "invitations" ALTER COLUMN "team_id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "invitations" ALTER COLUMN "invited_by" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "team_members" ALTER COLUMN "id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "team_members" ALTER COLUMN "user_id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "team_members" ALTER COLUMN "team_id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "teams" ALTER COLUMN "id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "users" ALTER COLUMN "id" SET DATA TYPE varchar(20);--> statement-breakpoint
ALTER TABLE "agents" ADD CONSTRAINT "agents_workspace_id_workspaces_id_fk" FOREIGN KEY ("workspace_id") REFERENCES "public"."workspaces"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "communications" ADD CONSTRAINT "communications_workspace_id_workspaces_id_fk" FOREIGN KEY ("workspace_id") REFERENCES "public"."workspaces"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "communications" ADD CONSTRAINT "communications_agent_id_agents_id_fk" FOREIGN KEY ("agent_id") REFERENCES "public"."agents"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "conversation_messages" ADD CONSTRAINT "conversation_messages_workspace_id_workspaces_id_fk" FOREIGN KEY ("workspace_id") REFERENCES "public"."workspaces"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "conversation_messages" ADD CONSTRAINT "conversation_messages_communication_id_communications_id_fk" FOREIGN KEY ("communication_id") REFERENCES "public"."communications"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "customers" ADD CONSTRAINT "customers_workspace_id_workspaces_id_fk" FOREIGN KEY ("workspace_id") REFERENCES "public"."workspaces"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "documents" ADD CONSTRAINT "documents_workspace_id_workspaces_id_fk" FOREIGN KEY ("workspace_id") REFERENCES "public"."workspaces"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "integrations" ADD CONSTRAINT "integrations_workspace_id_workspaces_id_fk" FOREIGN KEY ("workspace_id") REFERENCES "public"."workspaces"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "integrations" ADD CONSTRAINT "integrations_agent_id_agents_id_fk" FOREIGN KEY ("agent_id") REFERENCES "public"."agents"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "phone_numbers" ADD CONSTRAINT "phone_numbers_workspace_id_workspaces_id_fk" FOREIGN KEY ("workspace_id") REFERENCES "public"."workspaces"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "phone_numbers" ADD CONSTRAINT "phone_numbers_agent_id_agents_id_fk" FOREIGN KEY ("agent_id") REFERENCES "public"."agents"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "whatsapp_templates" ADD CONSTRAINT "whatsapp_templates_workspace_id_workspaces_id_fk" FOREIGN KEY ("workspace_id") REFERENCES "public"."workspaces"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "workspaces" ADD CONSTRAINT "workspaces_team_id_teams_id_fk" FOREIGN KEY ("team_id") REFERENCES "public"."teams"("id") ON DELETE no action ON UPDATE no action;