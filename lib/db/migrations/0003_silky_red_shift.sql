CREATE TABLE "integrations" (
	"id" serial PRIMARY KEY NOT NULL,
	"clinic_id" integer NOT NULL,
	"provider" varchar(50) NOT NULL,
	"credentials" text NOT NULL,
	"settings" text,
	"is_active" boolean DEFAULT true,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "integrations" ADD CONSTRAINT "integrations_clinic_id_clinics_id_fk" FOREIGN KEY ("clinic_id") REFERENCES "public"."clinics"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "clinics" DROP COLUMN "jane_app_url";--> statement-breakpoint
ALTER TABLE "clinics" DROP COLUMN "jane_api_client_id";--> statement-breakpoint
ALTER TABLE "clinics" DROP COLUMN "jane_api_client_secret";