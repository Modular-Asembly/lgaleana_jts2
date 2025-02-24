from fastapi import APIRouter
from typing import List, Dict, Any, Tuple
import logging

from app.pipeline.salesforce_query import query_salesforce
from app.pipeline.filter_unprocessed import filter_unprocessed
from app.pipeline.google_ads_upload import upload_conversions
from app.pipeline.store_success import store_success_records

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def partition_upload_results(
    upload_results: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Partitions the upload results into successful and failed conversions.

    Success is determined by the absence of an "error" key in the result.
    
    Args:
        upload_results: List of dictionaries returned by the google_ads_upload module.
    
    Returns:
        A tuple containing two lists:
         - successful_results: List of dictionaries for successful uploads.
         - failed_results: List of dictionaries for failed uploads.
    """
    successful_results = []
    failed_results = []
    for result in upload_results:
        if "error" in result:
            failed_results.append(result)
        else:
            successful_results.append(result)
    return successful_results, failed_results


def map_success_to_store_data(
    successful_results: List[Dict[str, Any]], filtered_records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Matches each successful upload result with its corresponding original sales record
    (based on matching GCLID value) and prepares the data for storing success in the database.

    The resulting dictionary includes:
      - salesforce_id: The Opportunity Id from the original record.
      - gclid: The GCLID value.
      - original_lead_created_datetime: Value from "Original_Lead_Created_Date_Time__c" in the original record.
      - admission_date: Value from "Admission_Date__c" in the original record.
      - status: Static string "successful".
      - error_details: None.

    Args:
        successful_results: The list of successful upload results from google_ads_upload.
        filtered_records: The list of filtered sales records from Salesforce.

    Returns:
        List of dictionaries ready to be stored using store_success_records.
    """
    # Create mapping from gclid to original record
    gclid_to_record = {record.get("GCLID__c"): record for record in filtered_records if record.get("GCLID__c")}
    store_data = []
    for result in successful_results:
        gclid = result.get("gclid")
        original_record = gclid_to_record.get(gclid)
        if original_record:
            data = {
                "salesforce_id": original_record.get("Id"),
                "gclid": original_record.get("GCLID__c"),
                "original_lead_created_datetime": original_record.get("Original_Lead_Created_Date_Time__c"),
                "admission_date": original_record.get("Admission_Date__c"),
                "status": "successful",
                "error_details": None,
            }
            store_data.append(data)
    return store_data


@router.get("/pipeline", response_model=List[Dict[str, Any]])
async def orchestrate_pipeline() -> List[Dict[str, Any]]:
    """
    Orchestrates the data pipeline by sequentially invoking:
      1. salesforce_query to fetch Salesforce data.
      2. filter_unprocessed to filter out already processed records.
      3. google_ads_upload to upload conversions to Google Ads.
      4. Partition the upload results into successful and failed conversions.
      5. store_success to store successful conversion uploads into the database.
    
    Logging is added between each step for debugging.
    
    Returns:
        A list of dictionaries representing the stored successful upload records.
    
    Raises:
        Any exceptions from the modules invoked will propagate.
    """
    logger.info("Starting pipeline orchestration.")

    # Step 1: Query Salesforce data.
    sales_data: List[Dict[str, Any]] = query_salesforce()
    logger.info(f"Fetched {len(sales_data)} records from Salesforce.")

    # Step 2: Filter out already processed records.
    filtered_data: List[Dict[str, Any]] = filter_unprocessed(sales_data)
    logger.info(f"{len(sales_data) - len(filtered_data)} records filtered out; {len(filtered_data)} records remain for processing.")

    # Step 3: Upload conversions to Google Ads.
    upload_results: List[Dict[str, Any]] = upload_conversions(filtered_data)
    logger.info(f"Google Ads upload attempted on {len(filtered_data)} records; received {len(upload_results)} upload result(s).")

    # Step 4: Partition upload results into successful and failed.
    successful_results, failed_results = partition_upload_results(upload_results)
    logger.info(f"{len(successful_results)} successful uploads; {len(failed_results)} failed uploads.")

    # Step 5: Prepare and store successful conversion data.
    if successful_results:
        store_data: List[Dict[str, Any]] = map_success_to_store_data(successful_results, filtered_data)
        stored_successes = store_success_records(store_data)
        logger.info(f"Stored {len(stored_successes)} successful upload record(s) in the database.")
    else:
        stored_successes = []
        logger.info("No successful uploads to store.")

    return [record.__dict__ for record in stored_successes]
