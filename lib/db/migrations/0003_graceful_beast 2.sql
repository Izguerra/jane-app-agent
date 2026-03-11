ALTER TABLE "agents" ADD COLUMN "settings" json;--> statement-breakpoint
ALTER TABLE "communications" ADD COLUMN "integration_id" varchar(20);--> statement-breakpoint
ALTER TABLE "customers" ADD COLUMN "status" varchar(20) DEFAULT 'active' NOT NULL;--> statement-breakpoint
ALTER TABLE "customers" ADD COLUMN "plan" varchar(50) DEFAULT 'Starter';--> statement-breakpoint
ALTER TABLE "customers" ADD COLUMN "usage_limit" integer DEFAULT 1000;--> statement-breakpoint
ALTER TABLE "customers" ADD COLUMN "usage_used" integer DEFAULT 0;--> statement-breakpoint
ALTER TABLE "customers" ADD COLUMN "avatar_url" varchar(255);--> statement-breakpoint
ALTER TABLE "customers" ADD COLUMN "created_at" timestamp DEFAULT now() NOT NULL;--> statement-breakpoint
ALTER TABLE "communications" ADD CONSTRAINT "communications_integration_id_integrations_id_fk" FOREIGN KEY ("integration_id") REFERENCES "public"."integrations"("id") ON DELETE no action ON UPDATE no action;