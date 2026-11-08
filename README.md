# AI & Machine Learning — Expert Systems and Search Algorithms

An interactive application developed with **Python and Streamlit** .

The application brings together two fundamental concepts of Artificial Intelligence: **rule-based reasoning through expert systems** and **problem-solving through search algorithms**.

---
Live Demo

Try the application directly through Streamlit:

Launch the AI & Machine Learning Application

No local installation is required to explore the application.

## Project Overview

The application is organized into two independent modules accessible through a main navigation menu.

### 1. Expert System — Tunisian Company Legal Form Identification

The first module implements a rule-based expert system designed to **identify the appropriate legal form for a company in Tunisia**, based on its characteristics and legal requirements represented in a knowledge base.

The system analyzes information provided by the user, such as:
- Number of partners or shareholders.
- Share capital.
- Capital structure (social shares or stocks).
- Whether the company makes a public offering of securities.

Based on these initial facts, the inference engine applies production rules to derive intermediate facts and determine the corresponding legal form.

**Supported legal forms:**
- SUARL — Société Unipersonnelle à Responsabilité Limitée.
- SARL — Société à Responsabilité Limitée.
- SA — Société Anonyme, with or without a public offering of securities.

**Key Features:**
- Presentation and exploration of the knowledge base (facts and production rules).
- Goal selection and verification.
- Forward Chaining and Backward Chaining.
- Step-by-step visualization of the inference process.
- Explanation of rule activation and derived conclusions.
- Interactive management of facts and production rules.
- Saving and loading the knowledge base.

### 2. Search Algorithms — Graph Search and Pathfinding

The second module provides an interactive environment for studying and visualizing search algorithms in state spaces.

Users can construct their own directed, weighted graphs and search for a path between an initial state and a goal state.

**Graph Construction:**
- Add and remove nodes.
- Create directed edges and assign costs.
- Define initial and goal states.
- Assign heuristic values \(h(n)\) for informed search algorithms.
- Load predefined graph examples.

**Implemented Search Algorithms:**

**Uninformed Search**
- Breadth-First Search (BFS)
- Depth-First Search (DFS)
- Depth-Limited Search (DLS)
- Iterative Deepening Search (IDS)
- Uniform Cost Search (UCS)

**Informed Search**
- Greedy Best-First Search
- A* Search

**Key Features:**
- Interactive graph construction and visualization.
- Step-by-step execution and exploration tracking.
- Visualization of the frontier (Open List) and explored nodes (Closed List).
- Display of the exploration order.
- Highlighting of the final path.
- Path cost calculation.
- Algorithm comparison on the same graph.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application |
| Pandas | Data handling and tabular presentation |
| Graph Theory | Graph representation and search |
| JSON | Knowledge base and graph data persistence |

---

## Project Structure

```text
legal-form-expert-system-and-search/
│
├── app.py                  # Main application and navigation
│
├── interface.py            # Expert system interface
├── engine.py               # Inference engine
├── knowledge_base.py       # Facts and production rules
│
├── search_interface.py     # Search algorithms interface
├── search_engine.py        # Graph model and search algorithms
├── search_app.py           # Standalone search module entry point
│
├── requirements.txt        # Project dependencies
│
└── README.md
```

---

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/elaa-bou/legal-form-expert-system-and-search.git
```

### 2. Navigate to the project directory

```bash
cd legal-form-expert-system-and-search
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv
```

Activate it:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
streamlit run app.py
```

The application will open automatically in your browser, usually at:

`http://localhost:8501`

---

## How to Use

1. Launch the application using Streamlit.
2. Select one of the two modules from the main menu.
3. Explore the knowledge base or construct a graph, depending on the selected module.
4. Configure the inference or search parameters.
5. Execute the selected method.
6. Follow the execution steps and examine the results.

---

## Educational Objectives

This project aims to put theoretical Artificial Intelligence concepts into practice through interactive implementations.

It focuses on:
- Knowledge representation using facts and production rules.
- Logical inference and reasoning mechanisms.
- Forward and backward chaining.
- State-space representation.
- Uninformed and informed search strategies.
- Heuristic evaluation and path-cost optimization.
- Algorithm execution, traceability and visualization.

---



## Disclaimer

The legal-form identification module is an educational expert system based on a predefined knowledge base and simplified production rules. Its conclusions are intended for academic demonstration and should not be considered professional legal advice or a substitute for verifying current Tunisian legislation.
