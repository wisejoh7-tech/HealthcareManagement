# CareSync Deployment Guide: Render & AWS

This guide provides end-to-end instructions for deploying the Healthcare Management System (CareSync) to **Render** and **Amazon Web Services (AWS)**, along with a complete environment variable reference for both Backend and Frontend.

---

## 📋 Table of Contents
1. [Environment Variables Reference](#environment-variables-reference)
   - [Backend Environment Variables](#backend-environment-variables)
   - [Frontend Environment Variables](#frontend-environment-variables)
2. [Deploying to Render](#deploying-to-render)
   - [Option A: One-Click Blueprint Deployment (Recommended)](#option-a-one-click-blueprint-deployment-recommended)
   - [Option B: Manual Dashboard Setup](#option-b-manual-dashboard-setup)
3. [Deploying to AWS](#deploying-to-aws)
   - [Option 1: AWS App Runner (Fastest & Fully Managed Container/Code)](#option-1-aws-app-runner)
   - [Option 2: AWS ECS (Elastic Container Service - Fargate)](#option-2-aws-ecs-fargate)
   - [Option 3: AWS Elastic Beanstalk](#option-3-aws-elastic-beanstalk)
   - [Database: AWS RDS PostgreSQL](#database-aws-rds-postgresql)
   - [Frontend: AWS S3 + CloudFront (Static Web Hosting)](#frontend-aws-s3--cloudfront)
4. [Local Multi-Container Deployment with Docker Compose](#local-multi-container-deployment)

---

## 🔑 Environment Variables Reference

### Backend Environment Variables

Stored in `.env` (local) or configured in your cloud provider's dashboard / secret manager. Templates are available in `.env.example` and `.env.production.example`.

| Variable | Required | Default | Allowed Values | Description |
|---|---|---|---|---|
| `DATABASE_URL` | Yes (in Prod) | `sqlite:///./healthcare.db` | SQLite URL or PostgreSQL connection string (`postgresql://user:pass@host:5432/dbname`) | The database connection string. Supports PostgreSQL and SQLite. Automatically normalizes legacy `postgres://` to `postgresql://`. |
| `APP_ENV` | No | `development` | `development`, `staging`, `production`, `test` | Application environment indicator. |
| `PORT` | No | `8000` | Any valid TCP port (e.g., `8000`, `8080`) | The port uvicorn listens on. Render and AWS App Runner inject this variable automatically. |
| `HOST` | No | `0.0.0.0` | IP string (e.g., `0.0.0.0`, `127.0.0.1`) | The network interface uvicorn binds to. `0.0.0.0` binds to all interfaces. |
| `ALLOWED_ORIGINS` | No | `*` | `*` or comma-separated list of origins (e.g. `https://caresync.onrender.com,https://app.example.com`) | CORS allowed origin domains. Recommended to restrict to your production frontend domain in production. |
| `APP_NAME` | No | `Healthcare Management System API` | String | API application title shown in OpenAPI docs (`/docs`). |

#### Example `.env` (Production Backend):
```bash
APP_ENV=production
HOST=0.0.0.0
PORT=8000
DATABASE_URL=postgresql://caresync_user:securepassword123@dpg-xxx.oregon-postgres.render.com/caresync
ALLOWED_ORIGINS=https://caresync.onrender.com,https://healthcare.yourdomain.com
```

---

### Frontend Environment Variables

When the frontend is served statically alongside the backend (default in this project via FastAPI static files mounting at `/`), it communicates seamlessly using relative paths `/api`.

If deploying the frontend independently (such as an SPA or separate web host on AWS S3, CloudFront, Render Static Site, Vercel, or Netlify), configure these variables (see `.env.frontend.example`):

| Variable | Framework Prefix | Description | Example Value |
|---|---|---|---|
| `API_BASE_URL` | Plain JS: `window.APP_CONFIG.API_BASE`<br>Vite: `VITE_API_BASE_URL`<br>CRA: `REACT_APP_API_BASE_URL`<br>Next.js: `NEXT_PUBLIC_API_BASE_URL` | Fully qualified base URL pointing to the backend API | `https://caresync-api.onrender.com/api` |
| `FRONTEND_PORT` | Local dev server port | Dev server listening port | `3000` |
| `S3_BUCKET_NAME` | AWS Deploy | Target S3 bucket for frontend bundle | `caresync-frontend-bucket` |
| `CLOUDFRONT_DISTRIBUTION_ID`| AWS Deploy | CloudFront Distribution ID for CDN cache invalidation | `E12345EXAMPLE` |

---

## 🚀 Deploying to Render

### Option A: One-Click Blueprint Deployment (Recommended)

The repository includes a ready-to-use `render.yaml` Blueprint specification.

1. Push your repository to GitHub or GitLab.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** > **Blueprint**.
4. Connect your Git repository.
5. Render reads `render.yaml` and automatically configures:
   - **PostgreSQL Database (`caresync-db`)**: Managed Free or Paid PostgreSQL instance.
   - **Web Service (`caresync-web`)**:
     - Runtime: `Python`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - Health Check Path: `/api/health`
     - Auto-linked `DATABASE_URL` connecting to `caresync-db`.
6. Click **Apply**. Render will provision both services and deploy the application.

---

### Option B: Manual Dashboard Setup

#### 1. Create PostgreSQL Database on Render
1. Go to **Dashboard** > **New +** > **PostgreSQL**.
2. Name: `caresync-db`
3. Database Name: `caresync`
4. User: `caresync_user`
5. Region: Choose your preferred region (e.g., `Oregon (US West)`).
6. Click **Create Database**.
7. Once provisioned, copy the **Internal Database URL** (e.g., `postgres://caresync_user:...@dpg-xxx:5432/caresync`).

#### 2. Create Web Service on Render
1. Go to **Dashboard** > **New +** > **Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name**: `caresync-app`
   - **Region**: Same region as your database.
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Expand **Environment Variables**:
   - `DATABASE_URL`: Paste the Internal Database URL from Step 1.
   - `APP_ENV`: `production`
   - `ALLOWED_ORIGINS`: `*` (or your custom domain)
5. Under **Advanced**, set **Health Check Path** to `/api/health`.
6. Click **Create Web Service**.

---

## ☁️ Deploying to AWS

CareSync is containerized and cloud-ready with a multi-stage `Dockerfile`.

### Database: AWS RDS PostgreSQL

1. Open AWS Console > **RDS** > **Create database**.
2. Engine: **PostgreSQL** (version 15 or 16).
3. Template: **Free tier** or **Production** depending on your needs.
4. Settings:
   - DB instance identifier: `caresync-db`
   - Master username: `caresync_admin`
   - Master password: `<your-secure-password>`
5. Connectivity:
   - VPC: Default or your custom VPC.
   - Public access: No (for production security, access within VPC).
   - VPC Security Group: Allow inbound traffic on port `5432` from your App Runner / ECS security group.
6. Initial database name: `caresync`
7. Once created, note the **Endpoint**:
   - URL Format: `postgresql://caresync_admin:<password>@<rds-endpoint>:5432/caresync`

---

### Option 1: AWS App Runner

AWS App Runner provides fully managed container execution with auto-scaling and zero server administration.

#### Deploy via App Runner:
1. Open AWS Console > **AWS App Runner** > **Create service**.
2. **Source**:
   - Choose **Source code repository** (connect GitHub) or **Container registry** (Amazon ECR).
   - If using source code, specify repository and branch `main`.
3. **Configuration**:
   - Runtime: `Python 3`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
   - Port: `8080`
   - Or select **Use configuration file** (points automatically to `apprunner.yaml`).
4. **Environment Variables**:
   - `DATABASE_URL`: `postgresql://caresync_admin:<password>@<rds-endpoint>:5432/caresync`
   - `APP_ENV`: `production`
   - `ALLOWED_ORIGINS`: `*`
5. **Health check**:
   - Protocol: `HTTP`
   - Path: `/api/health`
6. Click **Create & Deploy**.

---

### Option 2: AWS ECS (Elastic Container Service - Fargate)

1. **Build and push image to Amazon ECR**:
```bash
# 1. Authenticate Docker with Amazon ECR
aws ecr get-login-password --region <AWS_REGION> | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com

# 2. Create ECR repository (first time only)
aws ecr create-repository --repository-name caresync-api --region <AWS_REGION>

# 3. Build container
docker build -t caresync-api .

# 4. Tag container
docker tag caresync-api:latest <AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/caresync-api:latest

# 5. Push container
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/caresync-api:latest
```

2. **Register Task Definition**:
- Review `aws-task-definition.json`. Replace `<AWS_ACCOUNT_ID>` and `<AWS_REGION>` with your credentials.
- Register the task definition:
```bash
aws ecs register-task-definition --cli-input-json file://aws-task-definition.json
```

3. **Create ECS Service**:
- Create an ECS Cluster (e.g. `caresync-cluster`).
- Create a Fargate Service with an **Application Load Balancer (ALB)**:
  - Target Group Health Check: `/api/health`
  - Container Port: `8000`

---

### Option 3: AWS Elastic Beanstalk

1. Install EB CLI: `pip install awsebcli`
2. Initialize Beanstalk environment:
```bash
eb init -p python-3.12 caresync-app
```
3. Create environment:
```bash
eb create caresync-prod-env --single
```
4. Set environment variables:
```bash
eb setenv DATABASE_URL="postgresql://user:password@host:5432/dbname" APP_ENV="production"
```

---

### Frontend: AWS S3 + CloudFront (Static Web Hosting)

If you prefer to host the frontend dashboard on AWS S3 & CloudFront separately from the API:

1. **Create S3 Bucket**:
   - Bucket name: e.g. `caresync-frontend`
   - Enable Static website hosting (index document: `index.html`).

2. **Upload static frontend files**:
```bash
aws s3 sync app/static/ s3://caresync-frontend/ --acl public-read
```

3. **Configure API Base**:
   Include a script tag in `index.html` or configure `window.APP_CONFIG`:
```html
<script>
  window.APP_CONFIG = {
    API_BASE: "https://api.yourdomain.com/api"
  };
</script>
```

4. **CloudFront CDN**:
   - Create a CloudFront Distribution pointing to the S3 bucket origin.
   - Configure HTTPS SSL Certificate via AWS Certificate Manager (ACM).
   - Set CORS on your backend `ALLOWED_ORIGINS` to the CloudFront domain.

---

## 🐳 Local Multi-Container Deployment

To test the application locally in an environment identical to production (using Docker and PostgreSQL):

```bash
# 1. Start backend and PostgreSQL containers
docker-compose up --build

# 2. Access dashboard
http://localhost:8000

# 3. Access Swagger API docs
http://localhost:8000/docs

# 4. Stop containers
docker-compose down
```
