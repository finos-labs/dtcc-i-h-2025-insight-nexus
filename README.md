![badge-labs](https://user-images.githubusercontent.com/327285/230928932-7c75f8ed-e57b-41db-9fb7-a292a13a1e58.svg)

# DTCC AI Hackathon 2025: Empowering India's Innovators
The purpose of hackathon is to leverage AI and ML Technologies to address critical challenges in the financial markets. The overall goal is to progress industry through Innovation, Networking and by providing effective Solutions.

**Hackathon Key Dates** 
•	June 6th - Event invites will be sent to participants
•	June 9th - Hackathon Open
•	June 9th-11th - Team collaboration and Use Case development
•	June 12th - Team presentations & demos
•	June 16th - Winners Announcement

More Info - https://communications.dtcc.com/dtcc-ai-hackathon-registration-17810.html

Commit Early & Commit Often!!!

## Project Name


### Project Details


### Team Information


## Using DCO to sign your commits

**All commits** must be signed with a DCO signature to avoid being flagged by the DCO Bot. This means that your commit log message must contain a line that looks like the following one, with your actual name and email address:

```
Signed-off-by: John Doe <john.doe@example.com>
```

Adding the `-s` flag to your `git commit` will add that line automatically. You can also add it manually as part of your commit log message or add it afterwards with `git commit --amend -s`.

See [CONTRIBUTING.md](./.github/CONTRIBUTING.md) for more information

---

# AI-Powered Stock Market Research & Compliance Hub

A comprehensive platform integrating three AI-driven tools—**StockSage Bot**, **GenAI MarketView**, and **Compliance Regulation Assistant**—to streamline financial research and regulatory compliance tasks. Leveraging generative AI and large language models (LLMs), this project delivers actionable insights and efficient workflows for investors, traders, and compliance professionals.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
  - [StockSage Bot](#stocksage-bot)
  - [GenAI MarketView](#genai-marketview)
  - [Compliance Regulation Assistant Bot](#compliance-regulation-assistant-bot)
  - [Integrated UI](#integrated-ui)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Overview

The **AI-Powered Stock Market Research & Compliance Hub** addresses challenges in financial research and regulatory compliance by combining real-time data, intelligent summarization, and document analysis. The platform is designed to empower users with a unified, intuitive interface for stock analysis and compliance tasks.

---

## Features

### 1. StockSage Bot

An intelligent chatbot that unifies fragmented financial data into a single conversational interface.

- **Purpose**: Centralizes corporate actions (e.g., splits, dividends), real-time technical indicators (e.g., price, volume, RSI), and financial summaries.
- **Architecture**: Powered by LLMs via AWS Bedrock, with a middleware layer (MCP Server) connecting to yFinance, Wikipedia API, and AWS RDS.
- **Interface**: Streamlit-based UI for an interactive, real-time experience.

### 2. GenAI MarketView

A real-time, AI-powered tool for in-depth stock analysis.

- **Purpose**: Generates LLM-based summaries of company overviews, historical performance, valuation, fundamentals, and trading signals using yFinance and Finnhub data.
- **Key Features**: Groups stock-related news into key themes for easy understanding.
- **Architecture**: Streamlit UI, AWS Bedrock LLMs, and JSON-based dynamic content generation.

### 3. Compliance Regulation Assistant Bot

An AI tool simplifying regulatory document analysis for legal, compliance, and financial teams.

- **Purpose**: Reduces time and errors in navigating dense compliance PDFs.
- **Key Features**:
  - 📄 **Document Summarization**: Concise AI-generated summaries.
  - 🆚 **PDF Comparison Tool**: Highlights changes between document versions.
  - 🎯 **Impact Summary Generator**: Analyzes clause impacts on clients, companies, and investors.
  - 💬 **Chat with PDF**: Query documents in plain English with source-grounded answers.
- **Why It’s Powerful**: Precise citations (with page numbers), rejects unrelated queries to prevent hallucination, and modular for integration.

---

## Prerequisites

Ensure the following are installed:

- **Python 3.8+** (for StockSage Bot and MCP Server)
- **Node.js** and **npm** (for Integrated UI)
- **Docker** (for GenAI MarketView and Compliance Regulation Assistant)
- **Streamlit** (for StockSage Bot UI)
- **uv** (for MCP Server)
- `.env` file with credentials for:
  - AWS Bedrock
  - yFinance
  - Finnhub
  - Wikipedia API
  - AWS RDS

---

## Installation and Setup

### StockSage Bot

#### MCP Server

The MCP Server connects the chatbot to data sources.

```bash
cd /path/to/dtcc-i-h-2025-insight-nexus/StockSage\ Bot/mcp_server
pip install uv
uv run main.py --transport streamable-http
````

#### Streamlit App

The Streamlit app provides the StockSage Bot UI.

```bash
cd /path/to/dtcc-i-h-2025-insight-nexus/StockSage\ Bot/instrument_insights_chat
streamlit run app.py
```

Access at: [http://localhost:8501](http://localhost:8501)

---

### GenAI MarketView

This feature runs in a Docker container.

1. Create an `.env` file with credentials (AWS Bedrock, yFinance, Finnhub).
2. Run the container:

```bash
docker run -p 8602:8602 --env-file .env aryangupta2000/stock_analysis
```

Access at: [http://localhost:8602](http://localhost:8602)

---

### Compliance Regulation Assistant Bot

This feature also runs in a Docker container.

1. Create an `.env` file with credentials (e.g., AWS Bedrock).
2. Run the container:

```bash
docker run -p 8601:8601 --env-file .env aryangupta2000/comp-reg-bot
```

Access at: [http://localhost:8601](http://localhost:8601)

---

### Integrated UI

The integrated UI unifies access to all three features.

Ensure Node.js and npm are installed:

```bash
# macOS (Homebrew)
brew install node

# Ubuntu/Debian
sudo apt-get install nodejs npm

# Windows
Download from https://nodejs.org/
```

Then:

```bash
cd /path/to/dtcc-i-h-2025-insight-nexus/chatbot/src
npm i
npm run dev
```

Access at the provided URL (e.g., [http://localhost:3000](http://localhost:3000))

---

## Usage

### StockSage Bot

* Open [http://localhost:8501](http://localhost:8501)
* Query corporate actions, indicators, or summaries.

  * Example: `"What are AAPL’s recent dividends?"`
  * Example: `"Show TSLA’s RSI."`

### GenAI MarketView

* Open [http://localhost:8602](http://localhost:8602)
* Enter a stock ticker to get:

  * AI-generated summaries
  * Performance data
  * Thematic news grouping

### Compliance Regulation Assistant Bot

* Open [http://localhost:8601](http://localhost:8601)
* Upload PDFs for:

  * Summarization

  * Comparison

  * Impact analysis

  * Natural language querying

  * Example: `"Summarize this compliance document."`

### Integrated UI

* Access at [http://localhost:3000](http://localhost:3000) after running `npm run dev`
* Navigate seamlessly between all features

---

## Project Structure

```
dtcc-i-h-2025-insight-nexus/
├── StockSage Bot/
│   ├── mcp_ai/                     # Middleware for data sources
│   └── instrument_insights_chat/   # Streamlit UI
├── chatbot/
│   └── src/                        # Integrated UI (Node.js)
├── .env                            # Environment variables (not tracked)
└── README.md                       # Documentation
```

---

## Technologies Used

* **Frontend**:

  * Streamlit (StockSage Bot, GenAI MarketView)
  * Node.js (Integrated UI)
* **Backend**:

  * Python, AWS Bedrock (LLMs), MCP Server (middleware)
* **Data Sources**:

  * yFinance, Finnhub, Wikipedia API, AWS RDS
* **Containerization**:

  * Docker
* **Others**:

  * JSON-based dynamic content
  * Modular architecture

---

## Contributing

1. Fork the repository.
2. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit your changes:

   ```bash
   git commit -m 'Add your feature'
   ```
4. Push to the branch:

   ```bash
   git push origin feature/your-feature
   ```
5. Open a pull request.

---

### Helpful DCO Resources
- [Git Tools - Signing Your Work](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)
- [Signing commits
](https://docs.github.com/en/github/authenticating-to-github/signing-commits)


## License

Copyright 2025 FINOS

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)
