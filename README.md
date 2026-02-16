# DC OPF Simulator

A web-based DC Optimal Power Flow (OPF) simulator with visual network editor, MATPOWER import, and result visualization.

## Architecture

```
┌─────────────────┐      ┌─────────────────────┐
│   Vercel       │      │   Hugging Face     │
│   (Frontend)   │──────│   (Backend API)    │
│   Next.js      │      │   FastAPI          │
└─────────────────┘      └─────────────────────┘
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── models/
│   │   │   └── schemas.py   # Pydantic data models
│   │   ├── parser/
│   │   │   └── matpower.py  # MATPOWER case file parser
│   │   └── solver/
│   │       └── opf_solver.py # DC OPF solver
│   ├── requirements.txt
│   └── run.py               # Backend runner
│
└── frontend/
    ├── app/
    │   ├── layout.tsx       # Root layout
    │   ├── page.tsx         # Main editor page
    │   ├── globals.css      # Global styles
    │   └── results/
    │       └── page.tsx     # Results dashboard
    ├── components/
    │   ├── NetworkCanvas.tsx    # Visual network editor
    │   ├── BusEditor.tsx       # Bus parameter editor
    │   ├── GeneratorEditor.tsx # Generator parameter editor
    │   └── LineEditor.tsx      # Line parameter editor
    ├── lib/
    │   ├── api.ts           # API client
    │   └── store.ts        # Zustand state management
    ├── package.json
    └── next.config.js
```

## Features

- **Visual Network Editor**: Drag-and-drop network builder with SVG canvas
- **MATPOWER Import**: Parse MATPOWER format case files
- **DC OPF Solver**: Pure Python implementation using scipy optimization
- **Results Visualization**: Tables, charts, annotated single-line diagram
- **Export**: CSV and JSON export for results
- **Example Cases**: Built-in IEEE 9-bus test case

## Backend API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/case` | POST | Parse power system from JSON |
| `/case/text` | POST | Parse MATPOWER case file |
| `/case` | GET | Get current case data |
| `/opf` | POST | Run DC OPF optimization |
| `/results` | GET | Get OPF results |
| `/export/csv` | GET | Export results as CSV |
| `/export/json` | GET | Export results as JSON |
| `/example/case9` | GET | Get IEEE 9-bus example case |

## Setup & Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

The backend runs on http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on http://localhost:3000

## Deployment

### Backend (Hugging Face Spaces)

1. Create a new Space on Hugging Face
2. Select "Static" or "Docker" runtime
3. Upload the `backend/` folder
4. The API will be available at `https://your-space.hf.space`

### Frontend (Vercel)

1. Connect your GitHub repository to Vercel
2. Set environment variable `NEXT_PUBLIC_API_URL` to your backend URL
3. Deploy

## Usage

1. Open the web application
2. Click "Load Example" to load the IEEE 9-bus test case
3. Click "Run DC OPF" to solve the optimization
4. View results in the Results page
5. Export results as CSV or JSON

### Adding Elements

- Click on the canvas to add buses
- Connect buses by selecting "Add Line" mode
- Click on a bus to edit its properties
- Add generators and loads to buses

### Importing MATPOWER Cases

1. Click the import icon in the toolbar
2. Paste your MATPOWER format case file
3. Click "Import Case"

## Technology Stack

- **Frontend**: Next.js 14, React 18, Zustand, Recharts
- **Backend**: FastAPI, NumPy, SciPy
- **Deployment**: Vercel (frontend), Hugging Face Spaces (backend)
