# Product Roadmap

## Future Enhancements

### Scalable Phone Number Provisioning
**Goal:** Automate the assignment of phone numbers to new tenants to support scaling without manual intervention.

**Workflow:**
1.  **Onboarding:** During sign-up or workspace creation, prompt the user to select an Area Code (e.g., 416, 289).
2.  **Search:** Use Twilio API to search for available numbers in that area code.
3.  **Purchase:** Automatically purchase the selected number via Twilio API.
4.  **Configure:** Update the number's Voice URL (or SIP Trunking configuration) to point to the LiveKit SIP Ingress.
5.  **Assign:** Save the new number to the `workspaces` table (`inbound_agent_phone` column).

**Technical Requirements:**
-   Ensure Twilio `ACCOUNT_SID` and `AUTH_TOKEN` are securely stored in env vars.
-   Update `backend/routers/phone.py` to implement the search and buy logic.
-   Add UI in the Dashboard for "Get a Phone Number".

