# OutFlo Public API — Compiled Reference
Source: https://reach.outflo.io/docs (fetched 2026-07-28)
Base URL: https://live.outflo.in
All 43 operations are mounted under /api/public, grouped into 7 resources: Authentication, Accounts, Conversations, Campaigns, Lead Lists, Analytics, Workspace.

## Getting Started
1. Create an API key from your OutFlo workspace Integration settings (Manage API keys: https://reach.outflo.io/integration/api).
2. Send it in the x-api-key header with every request.
3. All responses use a standard envelope:
   { "status": <int>, "data": <object|array|null>, "error": <string|null> }
   On success, error is null. On failure, data is null and error is a developer-readable message.
4. POST/PUT/PATCH requests with a JSON body must set Content-Type: application/json. The lead-list write endpoints instead accept multipart/form-data for CSV uploads.

This document does not include an actual API key. Supply your own key when making requests.

---

## 1. Authentication

### GET /api/public/ping — Verify API credentials and inspect granted scopes
Headers: x-api-key (required)
No path parameters, no query parameters, no request body.
Note: this operation has no dedicated guide page on the docs site, so only the endpoint summary is documented; the response follows the standard envelope above.

---

## 2. Accounts — LinkedIn Account Login Flow

Overview: connect LinkedIn accounts, resolve OTP/2FA checkpoints, and poll connection status.

### POST /api/public/accounts/login — Start a LinkedIn account login
Headers: x-api-key (required), Content-Type: application/json (required)
Request body:
  - username (string, required) — LinkedIn account email address or phone number
  - password (string, required) — LinkedIn account password
Success response: 200
Example: { "username": "<string>", "password": "<string>" }

### POST /api/public/accounts/checkpoint/solve — Submit an account login checkpoint
Headers: x-api-key (required), Content-Type: application/json (required)
Request body:
  - accountId (string · UUID, required) — Account ID returned by the login request
  - code (string, required) — OTP or two-factor verification code
Success response: 200
Example: { "accountId": "00000000-0000-4000-8000-000000000000", "code": "<string>" }

### POST /api/public/accounts/checkpoint/resend — Resend an account login checkpoint
Headers: x-api-key (required), Content-Type: application/json (required)
Request body: accountId (string · UUID, required)
Success response: 200
Example: { "accountId": "00000000-0000-4000-8000-000000000000" }

### GET /api/public/accounts/status/{id} — Get LinkedIn account connection status
Headers: x-api-key (required)
Path params: id (string · UUID, required)
No query params, no request body. Success response: 200

All Accounts operations share the standard envelope:
  Success: { "status": 200, "data": "<endpoint-specific response data>", "error": null }
  Error:   { "status": 400, "data": null, "error": "Developer-readable error message" }

---

## 3. Conversations & Messages

Overview: inbox retrieval, context, messages, tags, star/archive/read state, drafts, reply-tags, and sending/replying to LinkedIn messages.

### GET /api/public/conversations — List conversations
Headers: x-api-key (required)
Query params (all optional):
  - page (integer) — page number, starting at 1
  - pageSize (integer) — results per page, up to 100
  - fromDate (string · date-time) — inclusive ISO 8601 start timestamp
  - toDate (string · date-time) — inclusive ISO 8601 end timestamp
  - searchText (string) — search attendee names and LinkedIn profile URLs
  - accountIDs (string · CSV) — comma-separated sender account UUIDs
  - campaign_ids (string · CSV) — comma-separated campaign UUIDs
  - tag_ids (string · CSV) — comma-separated numeric tag IDs
  - reply_tag (enum) — INTERESTED, NOT_INTERESTED, or GENERIC
  - is_starred (boolean), isArchived (boolean)
  - show_sent_messages (boolean), show_responses (boolean)
  - include_messages (boolean), message_limit (integer, up to 100)
No request body. Success response: 200

### POST /api/public/conversations/query — Query conversations with advanced filters
Headers: x-api-key (required), Content-Type: application/json (required)
Query params: same as GET /conversations (query-string equivalents also accepted)
Request body: filters (object, optional, see below), page (integer), pageSize (integer, up to 200)
filters object: fromDate, toDate (date-time), search (string), linkedinUrl (URL), starred (boolean), tags (integer[]|string), archived (boolean), drafts (boolean), replyStatus (enum: awaiting_reply/my_reply), campaigns (string[]|"all"), showSentMessages (boolean), showResponses (boolean), replyTag (enum: INTERESTED/NOT_INTERESTED/GENERIC), accountIDs (string[])
Success response: 200
Example: { "filters": { "fromDate": "<string>", "toDate": "<string>", "search": "<string>" } }

### GET /api/public/conversations/{id}/context — Get conversation context
Headers: x-api-key. Path: id (UUID, required). Query: include_messages (boolean), message_limit (integer, up to 50). Success: 200

### GET /api/public/conversations/{id}/messages — List messages in a conversation
Headers: x-api-key. Path: id (UUID, required). No query params. Success: 200

### POST /api/public/conversations/{id}/tags — Apply tags to a conversation
Headers: x-api-key, Content-Type: application/json. Path: id (UUID, required)
Request body: tags (object[], required) — one or more { id (integer|null, optional), name (string, required, 1-80 chars), color (string|null, optional, up to 40 chars) }
Example: { "tags": [ { "name": "Follow up", "color": "#2563eb" } ] }. Success: 200

### PATCH /api/public/conversations/{id}/star — Update a conversation star
Headers: x-api-key, Content-Type: application/json. Path: id (UUID, required)
Request body: is_starred (boolean, required). Example: { "is_starred": false }. Success: 200

### PATCH /api/public/conversations/{id}/archive — Update a conversation archive state
Headers: x-api-key, Content-Type: application/json. Path: id (UUID, required)
Query: isArchived (boolean, alternative to body). Request body: isArchived (boolean, optional, default true)
Example: { "isArchived": false }. Success: 200

### PATCH /api/public/conversations/{id}/read — Update a conversation read state
Headers: x-api-key. Path: id (UUID, required). No query params, no request body. Success: 200

### PATCH /api/public/conversations/{id}/draft — Save a conversation draft
Headers: x-api-key, Content-Type: application/json. Path: id (UUID, required)
Request body: draft (string|null) — null/empty clears it. Example: { "draft": "<string>" }. Success: 200

### PATCH /api/public/conversations/{id}/reply-tag — Update a conversation reply tag
Headers: x-api-key, Content-Type: application/json. Path: id (UUID, required)
Request body: tag (enum, required: INTERESTED/NOT_INTERESTED/GENERIC), reason (string, optional, up to 1000 chars)
Example: { "tag": "<string>", "reason": "<string>" }. Success: 200

### POST /api/public/conversations/reply — Send or reply to a LinkedIn message
Headers: x-api-key, Content-Type: application/json
Request body: senderProfileUrl (URL, required), receiverLinkedInUrl (URL, required), text (string, required), attachments (string[], optional)
Example: { "senderProfileUrl": "https://www.linkedin.com/in/example/", "receiverLinkedInUrl": "https://www.linkedin.com/in/example/", "text": "<string>", "attachments": [] }. Success: 200

All Conversations operations share the standard envelope shown in section 2.

---
## 4. Campaigns

Overview: lifecycle control, sequence configuration (classic + smart/graph sequences), lead retrieval, timelines, and campaign-scoped analytics.

### GET /api/public/campaigns — List campaigns
Headers: x-api-key. Query: status (enum: active/paused/draft/completed), search_text (string). Success: 200

### POST /api/public/campaigns — Create a campaign
Headers: x-api-key, Content-Type: application/json
Request body:
  - name (string, required) — campaign name
  - senderUrls (string[]) — connected sender LinkedIn profile URLs (one sender source required: senderUrls or senderAccountIds)
  - senderAccountIds (string[]·UUID) — connected OutFlo account IDs
  - timeZone (string) — e.g. "UTC"
  - leadListId (string·UUID) — existing lead list to attach
  - sendMessageToPreviousConnectedLeads (boolean)
  - sequence (object) — inline classic or smart outreach sequence (schema below)
  - sequenceCampaignId (string·UUID) — existing campaign whose sequence should be cloned
  - operationalTimes (object) — enabled days/operating hours (schema below)
  - variableResolution (object) — template-variable fallback behavior (schema below)
  - launchCampaign (boolean) — launch immediately after creation

  sequence object:
    - sequenceType (enum, required) — "classic" or "smart"
    - sequenceSteps (record<string,object>) — classic sequences; steps keyed consecutively from "0"
    - graph (object) — smart sequences; node-and-edge graph

  sequence.sequenceSteps.{step} object (one classic step):
    - actionType (enum, required) — SEND_CONNECTION_REQUEST, SEND_MESSAGE, SEND_VOICE_NOTE, FOLLOW_PROFILE, LIKE_A_POST, VIEW_PROFILE, and other action types
    - standardText (string) — connection-request note (SEND_CONNECTION_REQUEST only)
    - premiumText (string) — premium connection-request note (SEND_CONNECTION_REQUEST only)
    - messageText (string) — message/InMail body
    - subject (string) — InMail subject
    - voiceNoteUrl (string·URL) — public voice-note URL (SEND_VOICE_NOTE)
    - delay (number) — delay before execution, minutes; message/InMail/voice-note actions require at least 180

  sequence.graph object (smart sequences):
    - nodes (object[], required) — at least two nodes, including exactly one start node
    - edges (object[], required) — at least one edge connecting node IDs

  sequence.graph.nodes[] object: id (string, required), type (enum, required: start/action/end), actionType (enum, for action nodes), data (object, payload for selected action type)
  sequence.graph.nodes[].data object: messageText, attachments (string[]), standardText, premiumText, subject, voiceNoteUrl
  sequence.graph.edges[] object: id (string, optional), source (string, required), target (string, required), outcome (enum: positive/negative/open_profile_false), waitMinutes (number)

  operationalTimes object: keyed by capitalized weekday (Monday-Sunday); each day: enabled (boolean), startTime (HH:MM e.g. "09:00"), endTime (HH:MM e.g. "18:00")
  variableResolution object: keyed by template variable name; each entry: fixType (enum, required: skipLead/sendBlank/fallbackValue), fallbackValue (string, required when fixType=fallbackValue)

Success response: 201
Example (abbreviated): { "name": "<string>", "senderUrls": [], "senderAccountIds": [], "timeZone": "UTC", "leadListId": "<uuid>", "sequence": { "sequenceType": "classic", "sequenceSteps": { "0": { "actionType": "SEND_CONNECTION_REQUEST" } } } }

### GET /api/public/campaigns/{id}/sequence — Get a campaign sequence
Headers: x-api-key. Path: id (UUID, required). Success: 200

### GET /api/public/campaigns/{id}/leads/{leadId}/timeline — Get a campaign lead timeline
Headers: x-api-key. Path: id (UUID, required), leadId (UUID, required). Success: 200

### GET /api/public/campaigns/{id}/analytics/overview — Get campaign analytics overview
Headers: x-api-key. Path: id (UUID, required)
Query (all optional): connection_status (CSV), reply_status (CSV), account_id (CSV), overall_status (CSV), from_date (date-time), to_date (date-time), search_text (string), timezone (string)
Success: 200

### GET /api/public/campaigns/{id}/analytics/funnel — Get campaign funnel analytics
Same params as overview (minus timezone). Success: 200

### GET /api/public/campaigns/{id}/analytics/sequences — Get campaign sequence analytics
Headers: x-api-key. Path: id (UUID, required). No query params. Success: 200

### GET /api/public/campaigns/{id}/analytics/tags — Get campaign tag analytics
Path: id (UUID, required). Query: tag_ids (CSV) plus connection_status/reply_status/account_id/overall_status/from_date/to_date/search_text (same as overview). Success: 200

### GET /api/public/campaigns/{id}/leads — List campaign leads
Path: id (UUID, required). Query: connection_status, reply_status, account_id, overall_status, from_date, to_date, search_text. Success: 200

### POST /api/public/campaigns/launch — Launch a campaign
Headers: x-api-key. Query: campaign_id (UUID, required). No body. Success: 200

### POST /api/public/campaigns/pause — Pause a campaign
Query: campaign_id (UUID, required). Success: 200

### POST /api/public/campaigns/resume — Resume a campaign
Query: campaign_id (UUID, required). Success: 200

### POST /api/public/campaigns/exclude-leads — Exclude leads from a campaign
Headers: x-api-key, Content-Type: application/json
Body: campaign_id (UUID, required), linkedin_urls (string[], required)
Example: { "campaign_id": "00000000-0000-4000-8000-000000000000", "linkedin_urls": [] }. Success: 200

### POST /api/public/campaigns/pause-leads — Pause campaign leads
Same body shape as exclude-leads. Success: 200

### POST /api/public/campaigns/resume-leads — Resume campaign leads
Same body shape as exclude-leads. Success: 200

### PUT /api/public/campaigns/sequence — Update a campaign sequence
Headers: x-api-key, Content-Type: application/json. Query: campaign_id (UUID, required) — draft campaign to update
Body: sequence (object, same schema as create-campaign's sequence field), sequenceCampaignId (UUID, optional). Success: 200

### POST /api/public/campaign/addleadtoactivecampaign/{campaignId} — Add a lead to an active campaign
Headers: x-api-key, Content-Type: application/json. Path: campaignId (UUID, required)
Body: linkedinUrl (URL, required), firstName/lastName/company/title (string, optional), {customField} — any additional top-level key becomes a template variable; keys cannot contain spaces
Example: { "linkedinUrl": "https://www.linkedin.com/in/example/", "firstName": "<string>", "lastName": "<string>" }. Success response: 201

All Campaigns operations share the standard envelope shown in section 2.

---
## 5. Lead Lists

Overview: create lead lists, import leads (JSON or CSV), search by LinkedIn URL, and retrieve lead details.

### GET /api/public/lead-lists — List lead lists
Headers: x-api-key. Query: page (integer), limit (integer). Success: 200

### POST /api/public/lead-lists — Create a lead list
Headers: x-api-key, Content-Type: multipart/form-data
Body: name (string, required), csv (file·CSV, optional). Success response: 201

### POST /api/public/lead-lists/leads — Add leads to a lead list
Headers: x-api-key, Content-Type: multipart/form-data
Body: leadListId (UUID, required — lead_list_id also accepted), leads (object[], optional — JSON lead records; supply this or csv, not both), csv (file·CSV, optional)
leads[] object: linkedinUrl (URL, required — common column names auto-detected), {column} (string) — any additional column becomes a stored lead detail
Success response: 200

### GET /api/public/lead-lists/leads/search — Find a lead by LinkedIn URL
Headers: x-api-key. Query: linkedinUrl (URL, required), leadListId (UUID, optional), limit (integer, 1-50). Success: 200

### GET /api/public/lead-lists/leads/{leadId} — Get lead details
Headers: x-api-key. Path: leadId (UUID, required). Query: includeProfileDetails (boolean). Success: 200

All Lead Lists operations share the standard envelope shown in section 2.

---

## 6. Analytics & Reporting (organization level)

Overview: reporting endpoints keyed by date ranges, campaigns, senders, statuses, and aggregation buckets. (Campaign-scoped analytics endpoints — overview/funnel/sequences/tags — are documented in section 4; they are duplicated on the Analytics guide page.)

### GET /api/public/analytics/overview — Get organization analytics overview
Headers: x-api-key. Query (all optional): start_date (date), end_date (date), campaign_id (CSV), account_id (CSV), status (enum: active/paused/draft/completed), timezone (IANA string), bucket (enum: daily/weekly), rolling (boolean)
Success: 200

### GET /api/public/analytics/timeseries — Get organization analytics timeseries
Same query params as overview, plus metric (enum) — metric to plot, e.g. replies_received or messages_sent. Success: 200

### GET /api/public/analytics/senders — Get sender analytics
Same query params as overview, minus bucket. Success: 200

### GET /api/public/analytics/campaigns — Get campaign analytics
Same query params as overview, minus bucket and rolling. Success: 200

All Analytics operations share the standard envelope shown in section 2.

---

## 7. Workspace

### GET /api/public/context — Get workspace context for integrations
Headers: x-api-key (required).
Note: like /ping, this endpoint has no dedicated guide page, so no field-level schema is published beyond the standard envelope.

---

## 8. Webhooks

OutFlo sends webhook events to a destination URL you configure. All payloads include a top-level timestamp and event_type. Configure your endpoint and simulate events from the Webhooks & Events guide page.

### Connection Accepted — event_type: CONNECTION_ACCEPTED
Triggered when a lead accepts a connection request sent via an OutFlo campaign.
Fields: timestamp (date-time), event_type, campaign (id/name/url), sender_account (sending account details), lead (full lead details), lead_list (list the lead belongs to, incl. custom data)
Example payload:
  { "timestamp": "2026-05-09T12:44:48.000Z", "event_type": "CONNECTION_ACCEPTED",
    "campaign": { "name": "LinkedIn Outreach Q2", "id": "camp_99182", "url": "https://app.outflo.io/campaign/camp_99182" },
    "sender_account": { "id": "acc_112233", "first_name": "Kunal", "last_name": "Shah", "full_name": "Kunal Shah", "profile_url": "https://www.linkedin.com/in/kunalshah" },
    "lead": { "id": "lead_556677", "profile_url": "https://www.linkedin.com/in/janedoe", "first_name": "Jane", "last_name": "Doe", "full_name": "Jane Doe", "location": "San Francisco, CA", "headline": "Software Engineer at TechCorp", "company_name": "TechCorp", "job_title": "Software Engineer" },
    "lead_list": { "id": "list_443322", "name": "Engineering Leads Q2", "data": { "source": "Sales Navigator" } } }

### Lead Replied in Campaign — event_type: FIRST_REPLY_FROM_A_LEAD_IN_OUTFLO_CAMPAIGN
Triggered when a lead sends their first reply in an active OutFlo campaign.
Fields: timestamp, event_type, conversation_id, campaign (id/name), message (content/metadata of the reply)
Example payload:
  { "timestamp": "2026-04-14T14:15:22Z", "event_type": "FIRST_REPLY_FROM_A_LEAD_IN_OUTFLO_CAMPAIGN", "conversation_id": "conv_8273645",
    "campaign": { "name": "LinkedIn Outreach Q2", "id": "camp_99182" },
    "sender_account": { "id": "acc_112233", "full_name": "Kunal Shah" },
    "lead": { "id": "lead_556677", "full_name": "Jane Doe", "profile_url": "https://www.linkedin.com/in/janedoe" },
    "message": { "id": "msg_445566", "text": "Hey Kunal, thanks for reaching out! I would love to chat.", "sent_at": "2026-04-14T14:15:22Z" } }

### Every Message Received — event_type: EVERY_MESSAGE_OR_INMAIL_RECEIVED
Triggered for every incoming message or InMail received on any connected account.
Fields: timestamp, event_type, account (the connected account that received the message), message
Example payload:
  { "timestamp": "2026-04-14T14:15:22Z", "event_type": "EVERY_MESSAGE_OR_INMAIL_RECEIVED", "conversation_id": "conv_123456",
    "account": { "id": "acc_112233", "full_name": "Kunal Shah" },
    "message": { "id": "msg_778899", "text": "Hello! Looking forward to our call.", "sent_at": "2026-04-14T14:15:22Z" } }

---

_End of compiled reference. Generated from https://reach.outflo.io/docs by Claude for use alongside a user-supplied API key. No API key is included in this file._