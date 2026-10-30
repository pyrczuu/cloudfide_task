# CityWheels Help Desk AI Agent — Solution Documentation

## 1. Installation & How to Run

### Prerequisites
- Python 3.10 or higher
- Set your Gemini API Key in your environment:
  ```bash
  export GEMINI_API_KEY="your-gemini-api-key"'
  ```
  
### Installation
1. Clone the repository and navigate into the root directory:
```bash
git clone <repository-url>
cd citywheels-helpdesk
```
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/venv/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
### Running the Application
- Interactive CLI Agent:
```bash
python -m helpdesk.cli
```
or
```bash
PYTHONPATH=. python helpdesk/cli.py
```
- Unit Tests <br>
Runs tool unit tests and agent loop mocks without network calls or API keys:
```bash
python -m pytest tests/
```
- Evaluation Suite (Live Evaluation):
```bash
python -m eval.run_eval
```
## Model and Provider Choice
- *Provider* - Google Gemini API
- *Model* - gemini-3.8-flash
- *Reasoning*:
  1. Fast and accurate function calling.
  2. Quick and cheap (free) responses. 