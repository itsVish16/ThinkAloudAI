# User Service

## 📌 Overview
The User Service handles authentication, authorization, and user profile management. It is designed to be completely decoupled from the core interview logic.

## ⚙️ How It Works (Excalidraw Diagram Guide)

**Draw these boxes on your whiteboard:**
1. **Frontend / Client**: The user's browser.
2. **User Service (FastAPI)**: The backend API handling authentication.
3. **PostgreSQL (User DB)**: Stores user credentials (hashed) and profile details.

**Draw the flow (arrows):**
1. **Frontend -> User Service**: `POST /login` with email and password.
2. **User Service <-> PostgreSQL**: Look up user and verify hashed password.
3. **User Service -> Frontend**: Returns a stateless **JWT (JSON Web Token)**.
4. **Frontend -> Other Services**: The frontend attaches this JWT in the `Authorization` header for all future requests to prove identity.

## 🛠️ Key Details
- **Stateless Auth:** Uses JWT instead of server-side sessions (no session data stored in DB).
- **Why Separate?** High CPU load on the interview services (like saving code or processing AI text) will not prevent new users from logging in or viewing their profile dashboards.
