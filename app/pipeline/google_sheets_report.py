import os
from typing import List, Dict, Any

import gspread
from google.oauth2.credentials import Credentials

from app.core.google_auth.google_auth import get_google_oauth_credentials

def create_spreadsheet_report(success_records: List[Dict[str, Any]], 
                                failed_records: List[Dict[str, Any]]) -> str:
    """
    Creates a Google Sheets report containing both successful and failed upload records.
    Uses credentials from app.core.google_auth.google_auth to authenticate with Google Sheets API.
    
    Args:
        success_records: List of dictionaries representing successful uploads.
        failed_records: List of dictionaries representing failed uploads.
    
    Returns:
        URL of the created Google Sheets document.
    
    Raises:
        Any exceptions raised by gspread or google-auth.
    """
    # Obtain OAuth2 credentials required by gspread
    creds: Credentials = get_google_oauth_credentials()
    
    # Authorize gspread client using the credentials
    client: gspread.Client = gspread.authorize(creds)
    
    # Define spreadsheet title from environment variable or default value
    sheet_title: str = os.getenv("GOOGLE_SHEETS_REPORT_TITLE", "Uploads Report")
    
    # Create new spreadsheet
    spreadsheet = client.create(sheet_title)
    
    # Share the spreadsheet with the service account email if provided
    service_account_email: str = os.getenv("SERVICE_ACCOUNT_EMAIL", "")
    if service_account_email:
        spreadsheet.share(service_account_email, perm_type='user', role='writer')

    # Prepare header rows for both worksheets
    success_headers = ["Salesforce ID", "GCLID", "Original Lead Created", "Admission Date", "Status", "Error Details"]
    failed_headers = ["Salesforce ID", "Error Details"]
    
    # Create a worksheet for successful uploads and populate with header and data rows
    try:
        worksheet_success = spreadsheet.worksheet("Successful Uploads")
    except gspread.WorksheetNotFound:
        worksheet_success = spreadsheet.add_worksheet(title="Successful Uploads", rows="100", cols="20")
    worksheet_success.clear()
    worksheet_success.append_row(success_headers)
    for record in success_records:
        row = [
            record.get("salesforce_id", ""),
            record.get("gclid", ""),
            record.get("original_lead_created_datetime", ""),
            record.get("admission_date", ""),
            record.get("status", ""),
            record.get("error_details", "")
        ]
        worksheet_success.append_row(row)
    
    # Create a worksheet for failed uploads and populate with header and data rows
    try:
        worksheet_failed = spreadsheet.worksheet("Failed Uploads")
    except gspread.WorksheetNotFound:
        worksheet_failed = spreadsheet.add_worksheet(title="Failed Uploads", rows="100", cols="10")
    worksheet_failed.clear()
    worksheet_failed.append_row(failed_headers)
    for record in failed_records:
        row = [
            record.get("salesforce_id", ""),
            record.get("error", "")
        ]
        worksheet_failed.append_row(row)
    
    # Apply basic formatting (e.g., set column widths) if needed.
    # This example sets format by auto-resizing columns for both sheets.
    worksheet_success.resize(rows=1+len(success_records))
    worksheet_failed.resize(rows=1+len(failed_records))
    
    # Return the URL of the created spreadsheet
    return spreadsheet.url

def generate_google_sheets_report(success_records: List[Dict[str, Any]], 
                                  failed_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a Google Sheets report containing successful and failed upload records.
    This function is designed to be called by the pipeline orchestration service.
    
    Args:
        success_records: List of dicts with details of successful uploads.
        failed_records: List of dicts with details of failed uploads.
    
    Returns:
        A dictionary containing:
            - 'spreadsheet_url': URL to the Google Sheets report.
            - 'success_count': Number of successful records.
            - 'failed_count': Number of failed records.
    
    Raises:
        Any exceptions raised during report creation.
    """
    spreadsheet_url: str = create_spreadsheet_report(success_records, failed_records)
    
    report_summary: Dict[str, Any] = {
        "spreadsheet_url": spreadsheet_url,
        "success_count": len(success_records),
        "failed_count": len(failed_records)
    }
    return report_summary
