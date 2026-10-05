# RentMatch AI — Intelligent Rental Discovery

A full-stack FAI project for AI-assisted rental discovery across India.

## Highlights
- User registration and login with renter/owner roles
- India-wide starter property catalog covering multiple major cities and localities
- Natural-language rental search
- Gemini-based requirement extraction when `GEMINI_API_KEY` is configured, with a local fallback parser
- AI-agent orchestration with explicit search, hard-filter, heuristic scoring and ranking tools
- City/locality-aware hard location filtering
- Budget, BHK, parking, Wi-Fi and furnished constraints
- Explainable deterministic match scores
- Interactive Leaflet/OpenStreetMap property map
- Favorites and search history stored in SQLite
- Separate Owner Portal for publishing properties
- Multiple flat-photo uploads per owner listing
- Owner listings appear in the same renter search catalog

## India-wide locations
The bundled catalog includes properties across Hyderabad, Mumbai, Bengaluru, Kolkata, Chennai, Pune, Gurugram, Noida, New Delhi, Ghaziabad, Lucknow, Kochi, Thane, Chandigarh, Ahmedabad, Patna and Jaipur, with multiple localities. Owners can publish additional localities through the Owner Portal.

## Run
1. Open this folder directly in VS Code.
2. First run: `cmd /c setup.bat`
3. Terminal 1: `./start_backend.bat`
4. Terminal 2: `./start_frontend.bat`
5. Open `http://127.0.0.1:5173`

## Gemini
Set `GEMINI_API_KEY=YOUR_API_KEY_HERE` in `backend/.env`. The application still works without a Gemini key using the built-in requirement parser.

## Owner flow
Register with the **List my property** role, open **Owner Portal**, enter property details, upload up to 8 images, and publish. The property is stored in SQLite and becomes available to renters immediately.

## Deploy to Render
This repository includes a Render Blueprint (`render.yaml`) that builds the frontend and serves it with the FastAPI backend from one web service. The service uses a persistent disk for the SQLite database and owner-uploaded photos; the Blueprint uses Render's paid Starter plan because persistent disks are not available on free instances.

1. Push this repository to GitHub and open [Render Blueprints](https://dashboard.render.com/blueprints).
2. Select **New Blueprint Instance**, connect this repository, and deploy the `render.yaml` Blueprint.
3. Render generates a private `AUTH_SECRET` and mounts persistent data at `/var/data`. Gemini is optional; set `GEMINI_API_KEY` in the service environment if you want Gemini-powered requirement extraction.
4. Open the deployed service URL. Its `/api/health` endpoint is used for health checks.
