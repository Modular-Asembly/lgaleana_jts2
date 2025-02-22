# Instructions

```
cd <repo>
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
vim .env
# Add your environment variables
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
