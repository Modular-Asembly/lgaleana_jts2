import logging
from fastapi import APIRouter
from typing import Any, Dict, List, Tuple

from app.pipeline import salesforce_query
from app.pipeline import filter_unprocessed
from app.pipeline import google_ads_upload
from app.pipeline import store_success
from app.pipeline import google_sheets_report
from app.pipeline import gmail_notification

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
      - Each record in upload_results has keys: "gclid", "conversionAction", and potentially "error".
      Success is determined by the presence of conversionAction in the result.
    """
    success_data: List[Dict[str, Any]] = []
    failed_data: List[Dict[str, Any]] = []

    # Create a lookup dict for original records by GCLID
    record_lookup = {record["GCLID__c"]: record for record in filtered_data}

    for result in upload_results:
        gclid = result.get("gclid")
        orig = record_lookup.get(gclid, {})
        
        if "conversionAction" in result:
            success_data.append({
                "salesforce_id": orig.get("Id"),
                "gclid": gclid,
                "original_lead_created_datetime": orig.get("Original_Lead_Created_Date_Time__c"),
                "admission_date": orig.get("Admission_Date__c"),
                "status": "successful",
                "error_details": None
            })
        else:
            failed_data.append({
                "salesforce_id": orig.get("Id", ""),
                "error": result.get("error", "Unknown error")
            })
    
    return success_data, failed_data


@router.get("/pipeline", response_model=Dict[str, Any])
def run_pipeline() -> Dict[str, Any]:
    """
    FastAPI endpoint that executes the entire pipeline sequentially:
      1. Calls salesforce_query to fetch data from Salesforce.
      2. Filters out processed records using filter_unprocessed.
      3. Uploads conversions to Google Ads via google_ads_upload.
      4. Stores successful uploads in the database via store_success.
      5. Creates a Google Sheets report with google_sheets_report.
      6. Sends an email notification with the report link via gmail_notification.
    Returns:
      A JSON dictionary summarizing pipeline execution.
    """
    logger.debug("Step 1: Querying Salesforce for data.")
    sales_data: List[Dict[str, Any]] = salesforce_query.query_salesforce()
    logger.debug(f"Step 1 complete. Retrieved {len(sales_data)} Salesforce records.")

    logger.debug("Step 2: Filtering out already processed records.")
    filtered_data: List[Dict[str, Any]] = filter_unprocessed.filter_unprocessed(sales_data)
    logger.debug(f"Step 2 complete. {len(filtered_data)} records remain after filtering.")

    logger.debug("Step 3: Uploading conversions to Google Ads.")
    upload_results: List[Dict[str, Any]] = google_ads_upload.upload_conversions(filtered_data)
    logger.debug(f"Step 3 complete. Upload results: {upload_results}")

    logger.debug("Partitioning upload results into success and failure.")
    success_data, failed_data = partition_upload_results(filtered_data, upload_results)
    logger.debug(f"Partition complete. {len(success_data)} successes; {len(failed_data)} failures.")

    logger.debug("Step 4: Storing successful upload records into the database.")
    stored_records = store_success.store_success_records(success_data)
    logger.debug(f"Step 4 complete. Stored {len(stored_records)} successful records into the database.")

    logger.debug("Step 5: Generating Google Sheets report.")
    sheet_report = google_sheets_report.generate_google_sheets_report(success_data, failed_data)
    logger.debug(f"Step 5 complete. Report generated with URL: {sheet_report.get('spreadsheet_url', '')}")

    report_url: str = sheet_report.get("spreadsheet_url", "")
    
    logger.debug("Step 6: Sending email notification with the report link.")
    email_report = gmail_notification.send_email_report(
        success_count=len(success_data),
        failed_count=len(failed_data),
        report_url=report_url
    )
    logger.debug(f"Step 6 complete. Email report status: {email_report}")

    pipeline_report = {
        "salesforce_records": len(sales_data),
        "filtered_records": len(filtered_data),
        "upload_successes": len(success_data),
        "upload_failures": len(failed_data),
        "stored_records": len(stored_records),
        "report": sheet_report,
        "email_report": email_report
    }
    logger.debug(f"Pipeline execution complete. Aggregated report: {pipeline_report}")

    return pipeline_report
