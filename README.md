# VisionX-11 Pro: Advanced AI Vision Platform

VisionX-11 Pro is a high-performance, native AI surveillance and identification system. It combines state-of-the-art YOLOv11 posture tracking with deep fashion classification and face-aware re-identification to provide a professional "Command Center" monitoring experience.

![Dashboard Preview](https://raw.githubusercontent.com/nodzen/visionx-11/refs/heads/main/frontend_react/public/favicon.svg)

## 🚀 Key Features

- **Neural Posture Tracking**: Real-time detection of `Walking`, `Standing`, `Sitting`, and `Lying` using YOLOv11-Pose.
- **Fashion Intelligence**: Automatic classification of clothing types (e.g., Winter Parka, Denim Jeans, Formal Suit).
- **Pro Dashboard**: A sleek, Violet-themed React interface with 2:1 dashboard layout for streamlined monitoring.
- **Optimized Streaming**: Secure MJPEG streaming with frame-skipping logic for smooth 24+ FPS on remote devices.
- **Identity Consensus**: Intelligent "Lock" mechanism that prevents redundant processing of confirmed identities.

## 🛠 Tech Stack

### Backend (Neural Core)
- **Python 3.10+**
- **FastAPI**: High-performance async web framework.
- **Uvicorn**: High-performance ASGI server with SSL support.
- **Ultralytics YOLOv11**: Real-time computer vision models (Pose/Classification).
- **OpenCV**: Advanced image processing and MJPEG streaming.
- **DeepFace**: Identity verification and face quality analysis.

### Frontend (Cyber Dashboard)
- **React 19**: Modern UI component architecture.
- **Vite**: Ultra-fast build tool and dev server.
- **Tailwind CSS 4**: Next-gen utility-first styling.
- **Lucide React**: Professional iconography.

## 📦 Installation

This system is designed for **Windows** environments.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/vision-x11.git
   cd vision-x11
   ```

2. **Run Installer**:
   Double-click `install.bat`. This will:
   - Create a Python virtual environment (`venv`).
   - Install all neural and web dependencies.
   - Prepare the React environment.

3. **Download Models**:
   The system will automatically download the required YOLOv11 weights (`yolo11m-pose.pt`, etc.) on first launch.

## 🚦 Usage

1. **Start the System**:
   Double-click `run_native.bat`.
   
2. **Access Dashboard**:
   - **Desktop**: [https://localhost:5173](https://localhost:5173)
   - **Mobile**: Check the console for your local IP (e.g., `https://192.168.0.4:5173`).

> [!IMPORTANT]
> Because the system uses self-signed SSL for camera access, you must accept the "Not Secure" warning in your browser.

## 📝 Performance Tuning

- MJPEG stream quality is set to **70%** for a balance of clarity and speed.
- Neural inference skips every 2nd frame for maximum visual responsiveness.
