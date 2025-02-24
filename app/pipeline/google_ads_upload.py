import os
from typing import List, Dict, Any
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from app.core.google_auth.google_auth import get_access_token

def _build_google_ads_config() -> dict:
    """
    Build configuration dictionary required to initialize GoogleAdsClient.
    Environment variables used:
      - GADS_DEVELOPER_TOKEN
      - GADS_LOGIN_CUSTOMER_ID
      - GADS_CLIENT_ID
      - GADS_CLIENT_SECRET
      - GADS_CUSTOMER
    Additionally, obtain an OAuth2 access token via google_auth.
    Returns:
        Dictionary configuration for GoogleAdsClient.
    Raises:
        EnvironmentError: if any required environment variable is missing.
    """
    developer_token = os.getenv("GADS_DEVELOPER_TOKEN")
    login_customer_id = os.getenv("GADS_LOGIN_CUSTOMER_ID")
    client_id = os.getenv("GADS_CLIENT_ID")
    client_secret = os.getenv("GADS_CLIENT_SECRET")
    customer_id = os.getenv("GADS_CUSTOMER")
    if not all([developer_token, login_customer_id, client_id, client_secret, customer_id]):
        raise EnvironmentError("One or more required Google Ads environment variables are not set.")
    
    # Obtain OAuth2 access token using our custom google_auth module.
    access_token = get_access_token()
    
    # Prepare configuration dictionary for GoogleAdsClient.
    # Note: The configuration may contain non-string types.
    config = {
        "developer_token": developer_token,
        "login_customer_id": login_customer_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": "",  # Not used because we're providing an access token.
        "use_proto_plus": True,
        "access_token": access_token,
        "customer_id": customer_id,  # Our default customer id value.
    }
    return config

def _init_google_ads_client() -> GoogleAdsClient:
    """
    Initializes and returns a GoogleAdsClient instance using configuration from environment variables.
    Returns:
        An instance of GoogleAdsClient.
    """
    config = _build_google_ads_config()
    # GoogleAdsClient can be initialized from dictionary config.
    client = GoogleAdsClient.load_from_dict(config, version="v22")
    return client

def upload_conversions(filtered_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Uploads conversions to Google Ads using the Google Ads API.
    For each record in filtered_records, constructs a conversion object and uploads it.
    Uses the ConversionUploadService to perform the upload.
    Each record is expected to contain at least:
      - 'salesforce_id': str, unique identifier for the conversion.
      - 'gclid': str, the Google Click Identifier.
      - 'conversion_date_time': str, in the format "yyyy-mm-dd hh:mm:ss" (required by Google Ads API).
      - 'conversion_value': float, the value for the conversion (optional, default to 0.0 if missing).
    Returns:
        A list of dictionaries with the upload result for each conversion.
        Each dictionary contains:
            - 'salesforce_id': str
            - 'status': 'success' or 'failure' or 'partial_success'
            - 'error': Optional error message in case of failure.
    Raises:
        GoogleAdsException: Errors from the Google Ads API will be raised.
    """
    client = _init_google_ads_client()
    conversion_service = client.get_service("ConversionUploadService")
    results: List[Dict[str, Any]] = []

    # Build a list of click conversion objects.
    conversions = []
    for record in filtered_records:
        gclid = record.get("gclid")
        conversion_date_time = record.get("conversion_date_time")
        conversion_value = record.get("conversion_value", 0.0)
        salesforce_id = record.get("salesforce_id")

        if not (gclid and conversion_date_time and salesforce_id):
            results.append({
                "salesforce_id": salesforce_id if salesforce_id is not None else "",
                "status": "failure",
                "error": "Missing required fields: gclid, conversion_date_time, or salesforce_id."
            })
            continue

        conversion = client.get_type("ClickConversion")
        conversion.gclid = gclid
        conversion.conversion_action = f"customers/{os.getenv('GADS_CUSTOMER')}/conversionActions/{salesforce_id}"
        conversion.conversion_date_time = conversion_date_time
        conversion.conversion_value = float(conversion_value)
        conversions.append(conversion)

    if not conversions:
        return results

    request = client.get_type("UploadClickConversionsRequest")
    request.customer_id = os.getenv("GADS_CUSTOMER")
    request.conversions.extend(conversions)
    request.partial_failure = True

    response = conversion_service.upload_click_conversions(request=request)

    for conv_result in response.results:
        results.append({
            "salesforce_id": conv_result.conversion_action.split("/")[-1],
            "status": "success",
            "error": None
        })

    if response.partial_failure_error:
        failure_message = response.partial_failure_error.message
        for record in results:
            if record["status"] == "success":
                record["status"] = "partial_success"
                record["error"] = failure_message

    return results
