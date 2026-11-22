# 🤖 AI Excel Data Analyst
### Agentic AI Based Data Analysis System — Final Year B.Tech Project

---

## 📌 Project Objective

Build an AI-powered Excel and CSV data analyst that uses an **Agentic AI workflow** to:
- Understand natural language questions about uploaded datasets
- Plan analysis steps automatically
- Execute real Python/Pandas calculations (no hallucinated numbers)
- Reflect on whether results are sufficient
- Re-plan and run additional analysis if needed
- Return answers, insights, charts, and recommendations

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📂 File Upload | Drag & drop or browse CSV / XLSX files |
| 📊 Dataset Inspection | Rows, columns, dtypes, missing values, duplicates |
| 💬 Natural Language Q&A | Ask any question in plain English |
| 🤖 Agentic AI Workflow | Plan → Tool Select → Execute → Reflect → Re-plan |
| ⚗️ Python/Pandas Analysis | Real calculations, never invented numbers |
| 📈 Auto Chart Generation | Line, bar, histogram, scatter, pie charts |
| 💡 Insights & Recommendations | Automatically extracted from results |
| 🔄 Reflection Loop | Agent re-analyzes if initial results are insufficient |
| 🛡️ Fallback Mode | Works without LLM using keyword-based analysis |

---

## 🛠️ Technology Stack

```
Frontend:   React + Vite + Vanilla CSS
Backend:    Python + FastAPI
Data:       Pandas + NumPy
Excel:      OpenPyXL
Charts:     Matplotlib
AI:         OpenAI-compatible API (configurable, optional)
```

---

## 📁 Project Structure

```
AI_Excel_Data_Analyst/
│
├── backend/
│   ├── main.py               ← FastAPI app (API endpoints)
│   ├── config.py             ← Configuration & env vars
│   ├── requirements.txt      ← Python dependencies
│   ├── .env.example          ← Template for .env file
│   ├── generate_sample_data.py ← Run once to create sample CSV
│   │
│   ├── agent/
│   │   ├── agent.py          ← Main agent orchestrator
│   │   ├── planner.py        ← Analysis plan creator
│   │   ├── tool_selector.py  ← Tool selection logic
│   │   └── reflection.py     ← Result evaluation (Tool 7)
│   │
│   ├── tools/
│   │   ├── dataset_tool.py   ← Tool 1: Dataset inspection
│   │   ├── cleaning_tool.py  ← Tool 2: Data cleaning
│   │   ├── pandas_tool.py    ← Tool 3: Pandas analysis
│   │   ├── statistics_tool.py← Tool 4: Statistical analysis
│   │   ├── visualization_tool.py ← Tool 5: Chart generation
│   │   └── insight_tool.py   ← Tool 6: Insight generation
│   │
│   ├── services/
│   │   ├── file_service.py   ← File upload handling
│   │   ├── llm_service.py    ← LLM API wrapper
│   │   └── analysis_service.py ← Bridge between API and agent
│   │
│   ├── utils/
│   │   └── helpers.py        ← Utility functions
│   │
│   ├── uploads/              ← Uploaded files stored here
│   ├── generated_charts/     ← Charts saved here
│   └── sample_data/          ← Sample ecommerce CSV
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx           ← Main app component
│       ├── main.jsx          ← React entry point
│       ├── api.js            ← Backend API calls
│       ├── styles.css        ← Global styles
│       └── components/
│           ├── FileUpload.jsx
│           ├── DatasetPreview.jsx
│           ├── QuestionBox.jsx
│           ├── AgentProgress.jsx
│           ├── Results.jsx
│           ├── Charts.jsx
│           └── InsightCards.jsx
│
└── README.md
```

---

## 🤖 Agent Workflow (Agentic AI System)

```
USER UPLOADS FILE
       ↓
DATASET INSPECTION (Tool 1)
       ↓
USER ASKS QUESTION
       ↓
AI PLANNER → Creates step-by-step plan
       ↓
TOOL SELECTOR → Decides which tools to use
       ↓
┌─────────────────────────────────────────┐
│  Tool 2: Data Cleaning                  │
│  Tool 3: Pandas Analysis                │
│  Tool 4: Statistical Analysis           │
│  Tool 5: Visualization                  │
└─────────────────────────────────────────┘
       ↓
ACTUAL RESULTS (Python computed, not hallucinated)
       ↓
REFLECTION (Tool 7) → Are results sufficient?
       ↓
    ┌──────┴──────┐
    ↓             ↓
SUFFICIENT     NOT SUFFICIENT
    ↓             ↓ (max 3 loops)
    │         ADDITIONAL ANALYSIS
    │             ↓
    └──────→ REFLECTION AGAIN
                  ↓
         FINAL ANSWER + CHARTS (Tool 5)
                  ↓
         INSIGHTS (Tool 6) + RECOMMENDATIONS
```

---

## 🚀 Setup & Running Instructions

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher

---

### Backend Setup

```bash
# 1. Navigate to backend folder
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install Python packages
pip install -r requirements.txt

# 5. Create environment file
copy .env.example .env
# Then open .env and add your LLM API key (optional)

# 6. Generate sample data (run once)
python generate_sample_data.py

# 7. Start the backend server
uvicorn main:app --reload
```

Backend runs at: **http://localhost:8000**

---

### Frontend Setup

Open a **new terminal**:

```bash
# 1. Navigate to frontend folder
cd frontend

# 2. Install npm packages
npm install

# 3. Start development server
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## 🔧 Environment Variables

Create `backend/.env` based on `.env.example`:

```env
# LLM API Key (leave empty to use keyword-based fallback mode)
LLM_API_KEY=your-api-key-here

# Model name
LLM_MODEL=gpt-4o-mini

# API Base URL (change for Groq, Together AI, etc.)
LLM_BASE_URL=https://api.openai.com/v1
```

> **Note:** The app works fully WITHOUT an API key using keyword-based fallback analysis!

### Supported LLM Providers:

| Provider | Base URL | Model Example |
|----------|----------|---------------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| Groq (Free) | https://api.groq.com/openai/v1 | llama3-8b-8192 |
| Together AI | https://api.together.xyz/v1 | meta-llama/Llama-3-8b-chat-hf |

---

## 💬 Example Questions

Upload `sample_data/ecommerce_sales.csv` and try:

```
What is the total revenue?
Which category has the highest sales?
Show monthly revenue trend.
Why did revenue decrease?
Which region performed best?
What is the average order value?
What are the most important insights?
Which product generates the most revenue?
How are returns distributed across categories?
Compare performance across all regions.
```

---

## 🎬 Example Demo Workflow

1. **Upload** `ecommerce_sales.csv`
2. Dataset shows: 503 rows, 8 columns, 10 missing values, 3 duplicates
3. **Ask**: "Why did revenue decrease?"
4. Agent runs:
   - ✅ Dataset Inspection
   - ✅ Data Cleaning (removes duplicates, fills NaN)
   - ✅ Planning: 6-step plan created
   - ✅ Tool Selection: Pandas + Stats + Visualization + Insight
   - ✅ Monthly trend analysis (actual revenue by month)
   - ✅ Reflection Loop 1: "Need category breakdown"
   - ✅ Additional: Revenue by Category, Revenue by Region
   - ✅ Reflection Loop 2: "Results are sufficient"
   - ✅ Charts generated (line chart, bar chart, histogram)
   - ✅ Final answer with insights and recommendations

---

## 🔑 Seven Custom Tools

| # | Tool | File | Purpose |
|---|------|------|---------|
| 1 | Dataset Inspection | `tools/dataset_tool.py` | Analyze structure, types, missing data |
| 2 | Data Cleaning | `tools/cleaning_tool.py` | Fix duplicates, missing values |
| 3 | Pandas Analysis | `tools/pandas_tool.py` | groupby, sum, mean, trend analysis |
| 4 | Statistical Analysis | `tools/statistics_tool.py` | correlation, std, growth rate |
| 5 | Visualization | `tools/visualization_tool.py` | Generate charts as PNG |
| 6 | Insight Generation | `tools/insight_tool.py` | Extract key findings from results |
| 7 | Result Evaluation | `agent/reflection.py` | Assess if results answer the question |

---

## 🛡️ Security

- File types validated (only CSV/XLSX allowed)
- Max file size: 20 MB
- Safe filenames (removes special characters)
- API keys stored in `.env` (never committed)
- No code execution from uploaded files

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `CORS error` | Make sure backend is running on port 8000 |
| `File not found` | Re-upload your file |
| `Charts not showing` | Check `backend/generated_charts/` folder exists |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `npm not found` | Install Node.js from nodejs.org |
| `LLM not working` | Check `.env` file; app works in fallback mode |

---

## 🔮 Future Scope

- [ ] Support for Google Sheets integration
- [ ] Export analysis report as PDF
- [ ] Multi-file comparison
- [ ] Advanced ML: clustering, forecasting
- [ ] Chat history (multiple questions per session)
- [ ] Voice input for questions
- [ ] PostgreSQL for storing analysis history

---

## 📚 Academic Concepts Demonstrated

This project covers:
- **Artificial Intelligence** — LLM integration
- **Agentic AI** — Plan → Execute → Reflect → Re-plan
- **Natural Language Processing** — Question understanding
- **Data Science** — Pandas, NumPy, statistical analysis
- **Data Visualization** — Matplotlib chart generation
- **REST API Design** — FastAPI backend
- **React Frontend** — Modern SPA development
- **Software Engineering** — Modular design, error handling

---

*Final Year B.Tech Computer Science Project*
