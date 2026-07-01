# Cloud Deployment Guide (Git Clone & Build Method)

Since you pushed the code to GitHub but aren't using a Docker Registry yet, we will use the **"Git Clone & Build"** method. 

Instead of pulling pre-built images, we will clone your GitHub repositories directly onto your AWS and Azure servers and instruct Docker to build the images right there on the server.

---

## Part 1: Deploying to AWS (User & Main Service)

1. **SSH into your AWS EC2 instance:**
   ```bash
   ssh -i your-key.pem ubuntu@<AWS_PUBLIC_IP>
   ```

2. **Install Docker and Git (if not already installed):**
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose-v2 git -y
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Clone your Repositories:**
   Clone both services into the home directory of your server:
   ```bash
   git clone https://github.com/itsVish16/Scalable_User_Service.git
   git clone https://github.com/itsVish16/Main_Service.git  # Replace with actual repo name
   ```

4. **Create the Environment Files:**
   Go into each folder and create the `.env` file containing the Neon DB URL and Upstash Redis URL.
   ```bash
   nano Scalable_User_Service/.env
   nano Main_Service/.env
   ```

5. **Create the Master `docker-compose.yml`:**
   Go back to the home directory (`cd ~`) and create the compose file:
   ```yaml
   version: '3.8'
   services:
     user_service:
       build: ./Scalable_User_Service
       ports:
         - "8000:8000"
       env_file: ./Scalable_User_Service/.env
       restart: always

     main_service:
       build: ./Main_Service
       ports:
         - "8001:8001"
       env_file: ./Main_Service/.env
       restart: always
   ```

6. **Build and Deploy!**
   ```bash
   # Docker will compile the Dockerfiles from the local folders and start them
   docker compose up -d --build
   ```

---

## Part 2: Deploying to Azure (AI Interviewer)

1. **SSH into your Azure VM:**
   ```bash
   ssh azureuser@<AZURE_PUBLIC_IP>
   ```

2. **Install Docker and Git:**
   *(Run the exact same installation commands as Step 2 above)*

3. **Clone the Repository:**
   ```bash
   git clone https://github.com/itsVish16/AI_Interviewer.git
   cd AI_Interviewer
   ```

4. **Create the Environment File:**
   Create the `.env` file (`nano .env`) with all your API keys (Neon, Upstash, LiveKit, Featherless, etc.).

5. **Create `docker-compose.yml`:**
   Since the AI Interviewer uses a multi-stage Dockerfile, we will use Docker Compose's `target` feature to tell it to build one container for the FastAPI server, and a separate container for the background worker.
   
   Create `nano docker-compose.yml` inside the `AI_Interviewer` folder:
   ```yaml
   version: '3.8'
   services:
     ai_api:
       build:
         context: .
         target: api
       ports:
         - "8002:8000"  # Mapping server port 8002 to container port 8000
       env_file: .env
       restart: always

     ai_worker:
       build:
         context: .
         target: worker
       env_file: .env
       restart: always
   ```

6. **Build and Deploy!**
   ```bash
   docker compose up -d --build
   ```

---

## Final Verification
Once both servers are running their respective `docker compose up -d --build` commands:
1. Check that AWS User Service is responding: `curl http://<AWS_PUBLIC_IP>:8000/docs`
2. Check that Azure AI Interviewer is responding: `curl http://<AZURE_PUBLIC_IP>:8002/docs`
3. Test a full interview! Since both servers share the Upstash Redis URL, the `InterviewCompleted` event will seamlessly jump from Azure to AWS.
