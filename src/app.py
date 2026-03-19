from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import sys

# Add src to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.sqlite_service import SqliteService
from services.sync_service import SyncService
from services.cheque_service import ChequeService

app = FastAPI(title="ChequeFlow | Review Dashboard")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "cheques.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Initialize Services
sqlite_service = SqliteService(DB_PATH)
sync_service = SyncService(DB_PATH)
cheque_service = ChequeService(OUTPUT_DIR)

# Templates
templates = Jinja2Templates(directory=TEMPLATE_DIR)

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/cheques")
async def get_cheques(
    page: int = 1,
    page_size: int = 10,
    cheque_number: Optional[str] = None,
    payee_name: Optional[str] = None,
    ssn_last4: Optional[str] = None,
    date: Optional[str] = None
):
    filters = {
        "cheque_number": cheque_number,
        "payee_name": payee_name,
        "ssn_last4": ssn_last4,
        "date": date
    }
    rows, total_count = sqlite_service.get_cheques(page, page_size, filters)
    total_pages = (total_count + page_size - 1) // page_size
    
    return {
        "rows": rows,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@app.post("/api/sync")
async def trigger_sync():
    result = sync_service.run_sync()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result

@app.get("/api/cheques/{cheque_id}/preview")
async def preview_cheque(cheque_id: int):
    # Fetch data
    data_list = sqlite_service.get_full_data_by_ids([cheque_id])
    if not data_list:
        raise HTTPException(status_code=404, detail="Cheque not found")
    
    # Get or generate path
    try:
        pdf_path = cheque_service.get_or_generate_path(data_list[0])
        return FileResponse(pdf_path, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cheques/{cheque_id}/download")
async def download_cheque(cheque_id: int):
    # Fetch data
    data_list = sqlite_service.get_full_data_by_ids([cheque_id])
    if not data_list:
        raise HTTPException(status_code=404, detail="Cheque not found")
    
    # Get or generate path
    try:
        data = data_list[0]
        pdf_path = cheque_service.get_or_generate_path(data)
        filename = f"cheque_{data.get('cheque_number')}.pdf"
        return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
