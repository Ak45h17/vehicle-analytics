# Vehicle Analytics

A vehicle-monitoring application that detects vehicles in video, tracks
them across frames, classifies vehicle colors, records line-crossing
events, and displays event statistics in a web dashboard.

## Live Demo

-   **Dashboard:** https://vehicle-analytics-dashboard.onrender.com/
-   **Backend API:** https://vehicle-analytics-hb1s.onrender.com/
-   **Events API:**
    https://vehicle-analytics-hb1s.onrender.com/api/events
-   **GitHub Repository:** https://github.com/Ak45h17/vehicle-analytics

## Features

-   Vehicle detection using Ultralytics YOLO.
-   Multi-object tracking using ByteTrack.
-   Vehicle-class filtering for cars, motorcycles, buses, and trucks.
-   Vehicle color classification using a Caffe model.
-   Line-crossing event generation with direction labels.
-   Express REST API for creating and retrieving events.
-   PostgreSQL event persistence.
-   React dashboard with automatic refresh, event totals, color
    breakdowns, direction counts, and recent events.
-   RTSP video publishing support through MediaMTX and FFmpeg.

## Architecture

``` text
Traffic video file
      |
      v
MediaMTX / FFmpeg (RTSP publishing, optional input path)
      |
      v
Python detection pipeline
  - YOLO vehicle detection
  - ByteTrack tracking
  - Color classification
  - Line-crossing detection
      |
      | POST /api/events
      v
Express.js backend
      |
      v
PostgreSQL database
      |
      | GET /api/events
      v
React + Vite dashboard
```

## Technology Stack

-   **Detection and tracking:** Python, Ultralytics YOLO, ByteTrack
-   **Color classification:** OpenCV and a Caffe model
-   **Video streaming:** FFmpeg, MediaMTX
-   **Backend:** Node.js, Express.js
-   **Database:** PostgreSQL
-   **Frontend:** React, Vite
-   **Deployment:** Render (frontend and backend), hosted PostgreSQL

## Repository Structure

``` text
vehicle-analytics/
├── backend/
│   └── server.js
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── detect_vehicles.py
├── test_car_color.py
├── test_color_event.py
├── test_vehicle_color.py
├── Secondary_CarColor/
├── Primary_Detector/
├── README.md
└── ...
```

File and model names can differ slightly depending on the current
checkout.

## Prerequisites

-   Windows, Linux, or macOS
-   Python 3.10+ compatible with the installed project dependencies
-   Node.js and npm
-   FFmpeg
-   MediaMTX if testing the RTSP publishing path
-   A PostgreSQL database
-   YOLO weights and required color-classification model files

The detector may run on CPU, although inference can be slower than on a
supported GPU.

## Run Locally

### 1. Clone the repository

``` bash
git clone https://github.com/Ak45h17/vehicle-analytics.git
cd vehicle-analytics
```

### 2. Configure the backend

``` bash
cd backend
npm install
```

Configure the database connection using the environment variable
expected by `backend/server.js` (commonly `DATABASE_URL`). Do not commit
database credentials or `.env` files.

Start the backend:

``` bash
npm start
```

If the package does not define a `start` script, check
`backend/package.json` and use its configured start command.

Useful endpoints:

-   `GET /` --- API status
-   `GET /api/health` --- health check
-   `GET /api/db-health` --- database health check
-   `GET /api/events` --- retrieve recorded events
-   `POST /api/events` --- create an event

### 3. Configure and run the frontend

Open another terminal:

``` bash
cd frontend
npm install
```

Set the API URL for the frontend. For a local backend, use
`http://localhost:5000`; for the deployed backend, use
`https://vehicle-analytics-hb1s.onrender.com`. Vite browser environment
variables must use the `VITE_` prefix.

PowerShell example for local development:

``` powershell
$env:VITE_API_URL = "http://localhost:5000"
npm run dev
```

Build the production frontend:

``` bash
npm run build
```

### 4. Run the vehicle detector

From the repository root, create and activate a virtual environment if
needed, then install the Python dependencies required by the project.

Windows PowerShell example:

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install ultralytics opencv-python requests
python detect_vehicles.py
```

Install any additional dependencies required by the current script.
Ensure YOLO weights and color-classification model files are present at
the paths expected by the code.

For deployment testing, configure the detector's event API URL to:

``` text
https://vehicle-analytics-hb1s.onrender.com/api/events
```

For local development, use the local backend URL instead.

### 5. Publish a video over RTSP (optional)

Start MediaMTX, then publish a local video using FFmpeg. Adjust the
input path to the location of your video:

``` bash
ffmpeg -re -stream_loop -1 -i traffic_cam_clear_edited_1.mp4 -c copy -f rtsp rtsp://localhost:8554/traffic
```

This publishes the video to `rtsp://localhost:8554/traffic`.
**Publishing an RTSP stream does not by itself mean the detector
consumes that stream.** Confirm the input source configured in
`detect_vehicles.py`; the tested run may read the video file directly.

## API Event Flow

1.  The detector identifies a vehicle and tracks it between frames.
2.  When a tracked vehicle crosses the configured line, the pipeline
    creates an event with fields such as vehicle ID, type, color,
    direction, source, and timestamp.
3.  The detector sends the event to `POST /api/events`.
4.  The backend persists the event in PostgreSQL.
5.  The frontend periodically requests `GET /api/events` and updates the
    dashboard.

The exact accepted fields are defined by the backend implementation.
Check `backend/server.js` before sending custom payloads.

## NVIDIA DeepStream Status and Limitations

This repository has been tested locally using a **Python-based YOLO +
ByteTrack pipeline with CPU inference** and a Caffe color-classification
model. The deployed dashboard and backend have been verified to display
recorded events.

This tested path is **not equivalent to a validated NVIDIA DeepStream
runtime pipeline**. Full NVIDIA DeepStream execution requires a
compatible NVIDIA environment and the appropriate DeepStream, CUDA,
TensorRT, and model configuration. Do not describe the current CPU
fallback as NVIDIA DeepStream execution.

Also verify the configured detector input before claiming end-to-end
RTSP ingestion: FFmpeg/MediaMTX can publish an RTSP stream while the
Python detector independently reads a local file.

## Security and Configuration

-   Keep database URLs, passwords, and API secrets in environment
    variables.
-   Do not commit `.env`, `.env.production`, database credentials, or
    private keys.
-   Restrict CORS to intended frontend origins.
-   Use HTTPS for deployed API calls.
-   Do not commit large model files or private video assets unless
    required and permitted by the assignment.

## Troubleshooting

-   **Events are not appearing:** check the detector terminal for
    successful HTTP responses and verify its API URL points to the same
    backend used by the dashboard.
-   **Connection refused on port 5000:** the local backend is not
    running, or the detector is configured for the wrong URL.
-   **Dashboard says API connected but shows zero events:** open
    `/api/events` directly and confirm the response contains records.
-   **RTSP stream does not open:** confirm MediaMTX is running, FFmpeg
    is publishing to `/traffic`, and the detector is explicitly
    configured to read the RTSP URL.
-   **Slow inference:** CPU inference can be slow. Use a supported GPU
    environment for acceleration where available.

## Acknowledgements

Built as a computer-vision vehicle analytics assignment, combining a
Python detection pipeline with a web API, PostgreSQL storage, and a
React dashboard.
