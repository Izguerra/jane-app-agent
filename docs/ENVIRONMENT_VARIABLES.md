# Required Environment Variables

This document lists all environment variables that need to be configured in your `.env` file.

## Database

```env
POSTGRES_URL=postgres://postgres:postgres@localhost:54322/postgres
```

## Authentication

```env
AUTH_SECRET=<your-generated-secret>
```

## Stripe

```env
STRIPE_SECRET_KEY=<your-stripe-secret-key>
STRIPE_WEBHOOK_SECRET=<your-stripe-webhook-secret>
BASE_URL=http://localhost:3000
```

## LiveKit (Voice Agent)

**Required for voice agent functionality:**

```env
LIVEKIT_API_KEY=<your-livekit-api-key>
LIVEKIT_API_SECRET=<your-livekit-api-secret>
LIVEKIT_URL=wss://<your-project>.livekit.cloud
```

To get LiveKit credentials:
1. Sign up at https://livekit.io
2. Create a new project
3. Copy the API Key, API Secret, and WebSocket URL from your project settings

## Optional: AI Features

```env
OPENAI_API_KEY=<your-openai-api-key>
PINECONE_API_KEY=<your-pinecone-api-key>
```

---

**Note:** Please add the LiveKit environment variables to your `.env` file to enable the voice agent feature. The backend server will need to be restarted after updating the `.env` file.
