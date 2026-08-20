# UNAR - AI Interview Assessment System

## Local Development

### Backend
1. Navigate to the `backend` directory.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables (or rely on defaults):
   - `FRONTEND_URL`: Commma-separated list of allowed frontend origins (e.g. `http://127.0.0.1:5500,http://localhost:5500`).
5. Run the backend:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### Frontend
1. Navigate to the `frontend` directory.
2. Serve the frontend using a local live server (like VS Code Live Server or Python HTTP server):
   ```bash
   npx serve .
   # OR
   python -m http.server 5500
   ```
3. The frontend locally relies on the backend running at `http://127.0.0.1:8000` (or injected via script if customized). If testing, you can also build it with `sed` as done in production.

## Production Deployment (Render)

### Deploying the Backend
1. Create a **Web Service** on Render.
2. Connect this repository.
3. Choose the Python environment.
4. Set the **Build Command**: `pip install -r backend/requirements.txt`
5. Set the **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables:
   - `PYTHON_VERSION`: `3.10.0`
   - `FRONTEND_URL`: URL of your deployed frontend (e.g., `https://unar-frontend.onrender.com`).
7. Deploy! The backend uses the platform-provided `$PORT`.

### Deploying the Frontend
1. Create a **Static Site** on Render.
2. Connect this repository.
3. Set the **Publish Directory** to: `./frontend`
4. Set the **Build Command** to: 
   ```bash
   sed -i "s|<head>|<head><script>window.UNAR_API_URL='${BACKEND_URL}';</script>|g" frontend/index.html
   ```
5. Add Environment Variables:
   - `BACKEND_URL`: Set this to the public URL of your deployed backend service (e.g., `https://unar-backend.onrender.com`). Or use Render's dynamic variable injection.
6. Deploy! The `sed` command automatically configures the frontend to communicate with your public backend.

## Environment Variables

See `.env.example` for the required configuration formats. Never commit real secrets.
