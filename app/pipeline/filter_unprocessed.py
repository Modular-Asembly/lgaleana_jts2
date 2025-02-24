import os
from typing import List, Dict, Any
from app.core.database.sql_adaptor import SessionLocal
from app.models.upload_status import UploadStatus

def filter_unprocessed(sales_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters out rows that have already been processed.
    It checks each record from the raw sales data (provided by salesforce_query)
    against the UploadStatus records in the database.
    
    A record is considered processed if its Salesforce ID is already present in the database.
    
    Args:
        sales_data: List of dictionaries containing sales data, where each dictionary
                    is expected to have an "Id" key representing the Salesforce Opportunity Id.
    
    Returns:
        List of dictionaries that haven't been processed yet.
        
    Raises:
        Any exceptions raised by database queries will propagate.
    """
    # Open a new database session.
    with SessionLocal() as session:
        # Retrieve a set of all processed Salesforce IDs from the upload_status table.
        processed_records = session.query(UploadStatus.salesforce_id).all()
        processed_ids = {record[0] for record in processed_records}

    # Filter sales data to include only rows which haven't been processed.
    filtered_data = [row for row in sales_data if row.get("Id") not in processed_ids]

    # Log the count of filtered records.
    filtered_count = len(sales_data) - len(filtered_data)
    print(f"[filter_unprocessed] Filtered out {filtered_count} records that were already processed.")

    return filtered_data
