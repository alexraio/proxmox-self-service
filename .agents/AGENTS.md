# Proxmox WebApp - AGENTS.md

Welcome to the Proxmox WebApp workspace! This document defines the purpose, structure, and guidelines for AI Agents operating within this project.

## 🎯 Purpose
This project is an internal web application designed to simplify the provisioning and deployment of Virtual Machines (VMs) and LXC Containers (CTs) on a Proxmox Virtual Environment (VE). It acts as a user-friendly abstraction layer over the Proxmox API.

## 🏗️ Architecture & Responsibilities
The project is split into two independent domains:

### 1. Backend (`/backend`)
- **Framework**: Python 3.x using `FastAPI`, `uvicorn`, and `SQLAlchemy`.
- **Role**: Validates user requests, serves dropdown options from `config.json`, manages user authentication (JWT + bcrypt), tracks user machines in an SQLite/PostgreSQL database, and interfaces with the Proxmox VE API via `proxmox_client.py`.
- **Agent Guidelines**:
  - Always operate within the virtual environment (`venv`) when managing dependencies or running the server.
  - Define all payload structures using Pydantic models in `schemas.py` and manage database schemas within `models.py`.
  - Keep sensitive information (like tokens/passwords, DB keys) in the `.env` file.
  - Use `requirements.txt` to track any added Python dependencies.

### 2. Frontend (`/frontend`)
- **Framework**: React.js powered by Vite with `react-router-dom`.
- **Role**: Provides the User Interface for Registration/Login processing, deploying new instances (`ProvisionForm.jsx`), and managing/deleting existing user machines (`MachineList.jsx`).
- **Agent Guidelines**:
  - Maintain the modern, responsive UI aesthetic (e.g., glassmorphism, dark themes).
  - Use `npm run dev` for local testing. Ensure all new components are reusable and well-structured.
  - Update `package.json` and `package-lock.json` whenever installing new Node modules.

## 🔄 General Workflow for Agents
When instructed to implement a cross-stack feature (e.g., adding a new configuration field like "VLAN Tag"):
1. **Model First**: Update the backend schema (`ProvisionRequest`) first to accept the new data.
2. **Backend Logic**: Modify `proxmox_client.py` so the new data correctly interfaces with the Proxmox API.
3. **API Validation**: Verify `config.json` logic if the new field requires predefined dropdown options.
4. **Frontend Integration**: Modify the UI (`ProvisionForm.jsx`) to include the new field and update the fetch logic to submit it.
5. **Aesthetics**: Ensure the new frontend component fits perfectly within the existing stylistic guidelines (`index.css`).
