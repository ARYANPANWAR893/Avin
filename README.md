# Delhi Sustainability & Civic Action Platform  
### Hackathon Project – Avinya HNSUT Hackathon 2026  

Developed by **Aryan Panwar**

---

## Overview

This project is a civic-tech web platform designed to allow citizens of Delhi to report sustainability and public infrastructure issues and enable government officers to monitor, verify and resolve them through a single operational interface.

The system focuses on locality-level governance (not raw GPS storage) and introduces transparency, participation and accountability using AI-assisted classification, regional analytics and blockchain verification.

This project was built as a hackathon submission for  
**Avinya HNSUT Hackathon 2026 (HNSUT)**.

---

## Core Objectives

- Enable citizens to report real-world civic and sustainability problems  
- Automatically detect category and sub-category of issues using AI logic  
- Extract and use locality names (region-based system, not exact GPS storage)  
- Group and visualise issues by locality  
- Allow officers to manage and resolve issues in their jurisdiction  
- Provide tamper-proof records using blockchain proofs  
- Incentivise citizen participation using credits and rankings  

---

## Tech Stack

- Backend: Flask (Python)
- Database: SQLite (SQLAlchemy ORM)
- Frontend: HTML, CSS, Vanilla JavaScript
- Maps: Leaflet + OpenStreetMap
- AI logic: Rule-based NLP classification engine
- Blockchain layer: Custom blockchain proof service

---

## User Roles

### Citizen User  
Any user who signs up using a normal email address.

### Officer User  
Any user who logs in with an email ending in:

@delhi.gov.in


Officer users are automatically redirected to the officer dashboard and cannot access citizen dashboards.

Citizen users cannot access officer dashboards.

---

## Major Features

### Citizen Features

- Report issues using free-text description
- AI assisted pre-fill of:
  - category
  - sub-category
  - locality
- Popup verification before final submission
- View own submitted issues
- Issue dashboard with:
  - category
  - status
  - officer updates
  - missions
- AI generated official complaint draft
- Credits for verified civic actions
- Personal sustainability metrics
- Local hotspot suggestions
- Region-based interactive map
- Community leaderboard (citizens only)
- Area rank and Delhi rank
- Blockchain verification indicator

---

### Officer Features

- Dedicated officer dashboard
- Issues shown only for selected locality
- Locality selector dropdown
- Full citizen description visible
- Issue status update
- Expected resolution days update
- Operational region analytics
- Map-based regional view
- All-Delhi leaderboard for operations monitoring

---

### Transparency & Trust

- Blockchain proof generated for completed missions
- Ledger entries created per verified action
- Officer updates visible to citizens
- AI fallback suggestions when no officer update exists

---

## High-Level System Flow

1. Citizen submits an issue description.
2. AI service classifies category and sub-category.
3. Locality is extracted from text or browser location.
4. Issue is saved in the database.
5. Missions are generated for the issue.
6. Officer reviews and updates the issue.
7. Completed missions write proof to blockchain.
8. Ledger entries are created.
9. Credits and rankings are updated.

---

## Project Structure

.
├── app.py
├── models.py
├── services
│ ├── ai_service.py
│ ├── mission_service.py
│ ├── ledger_service.py
│ ├── blockchain_service.py
│ └── officer_service.py (if present)
│
├── templates
│ ├── home.html
│ ├── report.html
│ ├── issue.html
│ ├── officer.html
│ ├── profile.html
│ ├── leaderboard.html
│ ├── impact.html
│ ├── login.html
│ ├── signup.html
│ └── _navbar.html


---

## Core Backend Files

### app.py

Handles:
- routing
- authentication
- role-based access control
- API endpoints
- page rendering

---

### models.py

Defines:
- User
- Issue
- Mission
- LedgerEntry

---

### services/ai_service.py

Responsible for:
- issue classification
- sub-category detection
- locality extraction
- reverse geocoding
- severity prediction
- complaint rewriting

---

### services/mission_service.py

Responsible for:
- generating missions for each issue

---

### services/ledger_service.py

Responsible for:
- creating ledger entries
- assigning credits

---

### services/blockchain_service.py

Responsible for:
- writing blockchain proofs
- returning transaction metadata

---

## Web Routes (Pages)

### Public / Authentication

| Route | Description |
|------|------------|
| `/home` | Public landing page |
| `/login` | Login page |
| `/signup` | Signup page |
| `/logout` | Logout |

---

### Citizen Pages

| Route | Description |
|------|------------|
| `/` | Citizen report dashboard |
| `/issue/<id>/view` | Issue detail dashboard |
| `/profile` | Profile and sustainability metrics |
| `/leaderboard` | Citizen leaderboard |
| `/impact` | Sustainability impact and rewards |

---

### Officer Pages

| Route | Description |
|------|------------|
| `/officer` | Officer command dashboard |

---

## API Endpoints

### Issue Processing

| Method | Endpoint | Description |
|-------|--------|-------------|
| POST | `/api/issue/prefill` | AI prefill for popup |
| POST | `/api/issue/report` | Final issue submission |
| GET | `/api/issue/<id>` | Get issue data |
| GET | `/api/issue/<id>/missions` | Missions for issue |
| GET | `/api/issue/<id>/rewrite` | AI rewritten complaint |
| GET | `/api/issue/categories` | Issue taxonomy |

---

### Missions & Ledger

| Method | Endpoint | Description |
|-------|--------|-------------|
| POST | `/api/mission/<id>/complete` | Complete mission and write blockchain proof |
| GET | `/api/user/<id>/ledger` | Ledger entries |

---

### User & Metrics

| Method | Endpoint | Description |
|-------|--------|-------------|
| GET | `/api/me` | Current user profile |
| GET | `/api/me/metrics` | Sustainability metrics |
| GET | `/api/me/rank` | Area and Delhi ranking |

---

### Leaderboards

| Method | Endpoint | Description |
|-------|--------|-------------|
| GET | `/api/leaderboard` | Citizen leaderboard (officers excluded) |

---

### Hotspots & Region APIs

| Method | Endpoint | Description |
|-------|--------|-------------|
| POST | `/api/issues/nearby` | Nearby locality issues |
| GET | `/api/map/regions` | Aggregated regional map data |

---

### Officer APIs

| Method | Endpoint | Description |
|-------|--------|-------------|
| GET | `/api/officer/issues` | Issues for selected locality |
| POST | `/api/officer/issue/update` | Update issue status and ETA |

---

## Map Visualisation Logic

The platform does not store exact latitude or longitude.

Only locality names are stored.

Region coordinates are resolved dynamically using public geocoding.

Aggregated statistics are generated using:

/api/map/regions


Each region record contains:
- total issue count
- dominant category
- category breakdown

The frontend renders region circles using Leaflet.

---

## Credits & Ranking Logic

- Credits are added only when missions are completed.
- Rankings are calculated using ledger entries.
- Officer accounts are excluded from citizen leaderboards.

---

## Blockchain Integration

For every completed mission:

- a proof hash is generated
- blockchain transaction metadata is returned
- stored inside the ledger
- shown in the UI as verified activity

This provides tamper-proof civic action records.

---

## Security & Access Control

- Session-based authentication
- Role determined using email domain
- Officer routes protected from citizen access
- Citizen routes protected from officer access

---

## Running the Project

pip install -r requirements.txt
python app.py


Open:
http://localhost:5000


---

## Developer

**Aryan Panwar**

---

## Hackathon

Built for:

**Avinya NSUT Hackathon 2026**

---

## Project Status

This is a functional hackathon prototype demonstrating:

- AI-assisted civic reporting
- locality-based public issue analytics
- transparent operations
- participatory governance
- blockchain-backed trust layer
