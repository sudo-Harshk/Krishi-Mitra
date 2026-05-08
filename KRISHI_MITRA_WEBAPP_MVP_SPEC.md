# Krishi Mitra Web App MVP Spec

## Product Summary
Krishi Mitra is a mobile-first web app that helps farmers identify crop problems and get practical next-step advice in English and Telugu. The app should feel simple, fast, and trustworthy on a phone browser.

## Problem
Farmers need quick guidance for crop issues, but existing tools are often:
- too technical
- English-first
- slow to use in the field
- not grounded in local crop knowledge or weather context

## MVP Goal
Deliver a clean browser-based experience where a user can:
1. describe a crop problem
2. optionally upload a photo
3. optionally provide a location
4. get a bilingual diagnosis and action plan

## Target Users
- Small-scale Indian farmers
- Agricultural support workers
- Telugu-speaking users who need simple guidance

## Core User Flow
1. User opens the app on a phone browser.
2. User enters crop name and problem description.
3. User optionally uploads a photo.
4. User optionally enters location.
5. User taps one primary action button.
6. App shows loading state.
7. App returns a structured result in English and Telugu.

## MVP Scope
### Included
- Single-page mobile-first UI
- Crop name input
- Problem description input
- Optional image upload
- Optional location input
- Primary submit action
- Loading, success, and error states
- Bilingual response rendering
- Weather-aware advice when location is provided
- Basic request validation

### Not Included
- Native mobile app
- APK builds
- User accounts or login
- Chat-style multi-turn UX
- Social features
- Offline-first sync system
- Voice output in the MVP
- Push notifications

## Information Architecture
The page should be organized into:
1. Header and short product explanation
2. Input section
3. Submit action
4. Result section
5. Error/retry state

## Screen Requirements
### Main Screen
- Clear title
- Short plain-language subtitle
- Crop input
- Problem description textarea
- Image upload control
- Optional location input
- Primary CTA button

### Result Screen
- Diagnosis summary
- Likely issue or disease
- Recommended action steps
- Weather caution if applicable
- English section
- Telugu section

### Error State
- Friendly message
- Retry action
- No technical stack traces

## Response Format
The backend should return structured data that the frontend can render consistently.

Suggested fields:
- `summary_en`
- `summary_te`
- `likely_issue`
- `action_steps_en`
- `action_steps_te`
- `weather_warning_en`
- `weather_warning_te`
- `confidence`
- `source_notes`

## Backend Expectations
The frontend should call a single diagnosis endpoint that accepts:
- crop name
- problem description
- optional location
- optional image

The backend can use:
- Gemma 4 for generation
- RAG over the agricultural record set
- weather data for location-aware guidance
- fallback web lookup when retrieval confidence is low

## UX Principles
- Mobile-first, not desktop-first
- Large text
- Strong contrast
- One obvious primary action
- Minimal cognitive load
- No clutter
- Simple language

## Content Principles
- Avoid jargon
- Prefer short sentences
- Keep the English and Telugu sections parallel
- Give direct actions, not abstract theory
- Be specific about safety when weather matters

## Validation Rules
- Crop name required
- Problem description required
- Image optional
- Location optional
- Prevent empty submissions
- Show validation messages inline

## Success Criteria
- A user can submit a request in under a minute
- The result is readable on a phone without zooming
- English and Telugu outputs are always present
- The app works well in a browser on mobile
- The demo clearly shows practical value

## Recommended Tech Direction
- Frontend: React or Next.js
- Styling: simple component-based UI with responsive layout
- Backend: FastAPI or equivalent API service
- Deployment: one hosted frontend, one hosted API

## Short MVP Definition
If the team ships only one thing, ship this:
- a clean mobile-first web page
- one form
- one submit action
- one structured bilingual result

