import os
import requests
from datetime import datetime
from typing import List, Dict, Any

from app.core.google_auth.google_auth import get_access_token


def upload_conversions(filtered_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    action_id = 462477827
    customer_id = os.getenv("GADS_CUSTOMER")
    api_version = "v18"

    access_token = get_access_token()

    conversion_objects = []
    for record in filtered_records:
        lead_created_time = record.get(
            "Original_Lead_Created_Date_Time__c"
        ) or record.get("Admission_Date__c")
        gclid = record.get("GCLID__c")

        if not (gclid and lead_created_time):
            continue

        formatted_date = datetime.strptime(lead_created_time, "%Y-%m-%dT%H:%M:%S.%f%z")
        formatted_date = formatted_date.strftime("%Y-%m-%d %H:%M:%S%z")
        formatted_date = formatted_date[:-2] + ":" + formatted_date[-2:]

        conversion = {
            "conversionAction": f"customers/{customer_id}/conversionActions/{action_id}",
            "gclid": gclid,
            "conversionValue": 1,
            "conversionDateTime": formatted_date,
            "currencyCode": "USD",
        }
        conversion_objects.append(conversion)

    if not conversion_objects:
        return []

    url = f"https://googleads.googleapis.com/{api_version}/customers/{customer_id}:uploadClickConversions"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "developer-token": os.getenv("GADS_DEVELOPER_TOKEN"),
        "login-customer-id": os.getenv("GADS_LOGIN_CUSTOMER_ID"),
    }
    payload = {
        "conversions": conversion_objects,
        "partialFailure": True,
    }

    response = requests.post(url, headers=headers, json=payload)
    if not response.ok:
        print(response.text)
        response.raise_for_status()

    conversion_response = response.json()
    results = []
    if "partialFailureError" in conversion_response:
        # Extract error details
        error_details = conversion_response["partialFailureError"]["details"][0][
            "errors"
        ]
        error_by_index = {
            error["location"]["fieldPathElements"][0]["index"]: error
            for error in error_details
        }

        # Map results with original GCLIDs
        for idx, original_conversion in enumerate(conversion_objects):
            result = {"gclid": original_conversion["gclid"]}
            if idx in error_by_index:
                result["error"] = error_by_index[idx]
            else:
                # Copy successful conversion data
                result.update(conversion_response["results"][idx])
            results.append(result)
    else:
        results = conversion_response.get("results", [])

    return results
