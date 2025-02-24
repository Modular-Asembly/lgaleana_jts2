from fastapi import APIRouter
from typing import Any, Dict, List, Tuple

from app.pipeline import salesforce_query
from app.pipeline import filter_unprocessed
from app.pipeline import google_ads_upload
from app.pipeline import store_success
from app.pipeline import google_sheets_report
from app.pipeline import gmail_notification

router = APIRouter()


def partition_upload_results(
    filtered_data: List[Dict[str, Any]], 
    upload_results: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Partitions the upload results into success and failure lists.
    For successful uploads, merge additional fields from the original Salesforce record.
    
    Assumes:
      - Each record in filtered_data has keys: "Id", "GCLID__c",
        "Original_Lead_Created_Date_Time__c", "Admission_Date__c".
      - Each record in upload_results has key "salesforce_id" and "status" and "error".
    """
    success_data: List[Dict[str, Any]] = []
    failed_data: List[Dict[str, Any]] = []
    
    # Create a lookup dict for original records by Salesforce Id
    record_lookup = {record["Id"]: record for record in filtered_data}
    
    for result in upload_results:
        sf_id = result.get("salesforce_id")
        if result.get("status") == "success":
            # Find original record details
            orig = record_lookup.get(sf_id, {})
            success_data.append({
                "salesforce_id": sf_id,
                "gclid": orig.get("GCLID__c"),
                "original_lead_created_datetime": orig.get("Original_Lead_Created_Date_Time__c"),
                "admission_date": orig.get("Admission_Date__c"),
                "status": "successful",
                "error_details": None
            })
        else:
            failed_data.append({
                "salesforce_id": sf_id if sf_id is not None else "",
                "error": result.get("error", "Unknown error")
            })
    return success_data, failed_data


@router.get("/pipeline", response_model=Dict[str, Any])
def run_pipeline() -> Dict[str, Any]:
    """
    FastAPI endpoint that executes the entire pipeline sequentially:
      1. Calls salesforce_query to fetch data.
      2. Filters out processed records using filter_unprocessed.
      3. Uploads conversions to Google Ads via google_ads_upload.
      4. Stores successful uploads into the database via store_success.
      5. Creates a Google Sheets report with google_sheets_report.
      6. Sends an email notification with the report link via gmail_notification.
      
    Returns:
      A JSON dictionary summarizing pipeline execution.
    """
    # Step 1: Query Salesforce
    sales_data: List[Dict[str, Any]] = salesforce_query.query_salesforce()
    
    # Step 2: Filter already processed records
    filtered_data: List[Dict[str, Any]] = filter_unprocessed.filter_unprocessed(sales_data)
    
    # Step 3: Upload conversions to Google Ads
    upload_results: List[Dict[str, Any]] = google_ads_upload.upload_conversions(filtered_data)
    
    # Partition the upload results into successes and failures, merging record details for successes
    success_data, failed_data = partition_upload_results(filtered_data, upload_results)
    
    # Step 4: Store successful uploads in the database
    stored_records = store_success.store_success_records(success_data)
    
    # Step 5: Generate a Google Sheets report
    sheet_report = google_sheets_report.generate_google_sheets_report(success_data, failed_data)
    
    # Ensure report_url is a string
    report_url: str = sheet_report.get("spreadsheet_url", "")
    
    # Step 6: Send email notification with report link
    email_report = gmail_notification.send_email_report(
        success_count=len(success_data), 
        failed_count=len(failed_data), 
        report_url=report_url
    )
    
    # Aggregate results for the JSON report
    pipeline_report = {
        "salesforce_records": len(sales_data),
        "filtered_records": len(filtered_data),
        "upload_successes": len(success_data),
        "upload_failures": len(failed_data),
        "stored_records": len(stored_records),
        "report": sheet_report,
        "email_report": email_report
    }
    
    return pipeline_report
