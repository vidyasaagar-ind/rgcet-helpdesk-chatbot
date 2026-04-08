# RGCET Chatbot Widget

## Purpose
This folder contains the portable frontend widget for the RGCET Help Desk chatbot.

Key files:
- `widget.js`: behavior, API calls, FAQ actions, message rendering
- `widget.css`: widget styles
- `index.html`: local demo shell + widget markup

## Run Locally
From `chatbot-widget/`:
```bash
python -m http.server 5500
```
Open:
- `http://127.0.0.1:5500`

## Why HTTP (not `file://`)
Run through HTTP server instead of opening `index.html` directly because:
- browser fetch behavior from `file://` is inconsistent/restricted
- widget needs predictable request origin when calling backend API
- local HTTP better matches deployment behavior

## API Base URL Configuration
Set backend URL in `widget.js`:
```js
const API_BASE_URL = "http://127.0.0.1:8000";
```

If backend runs on a different host/port, update this value.

## Backend Communication
The widget sends:
- `POST ${API_BASE_URL}/chat`
- JSON body: `{ "message": "<user text>" }`

The widget reads backend response fields (for example `answer`, `fallback_type`) and renders:
- normal grounded messages
- fallback styling for generic fallback responses

## Embedding Into Existing College Website
For integration on an existing site:

1. Host `widget.js` and `widget.css` as static files.
2. Add widget HTML markup (the block under `BEGIN RGCET CHATBOT WIDGET` in `index.html`) into target page template.
3. Include:
```html
<link rel="stylesheet" href="/path/to/widget.css">
<script src="/path/to/widget.js"></script>
```
4. Ensure `API_BASE_URL` points to hosted backend API domain.

## Small Deployment Notes
- Keep backend CORS restricted to approved college domains in production.
- Use HTTPS for production frontend/backend hosts.
- Keep demo shell (`index.html`) separate from production website templates.
