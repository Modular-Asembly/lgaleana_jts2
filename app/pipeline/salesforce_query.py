import os
import requests
from typing import List, Dict, Any
from simple_salesforce import Salesforce

def get_salesforce_access_token() -> Dict[str, str]:
    """
    Obtains an OAuth 2.0 access token from Salesforce.

    This function makes a POST request to the hardcoded Salesforce OAuth token endpoint using
    the following environment variables:
      - SALESFORCE_CLIENT_ID
      - SALESFORCE_CLIENT_SECRET
      - SALESFORCE_USERNAME
      - SALESFORCE_PASSWORD
      - SALESFORCE_SECURITY_TOKEN (optional)

    The password is combined with the security token (if provided) to authenticate.
    
    Returns:
        A dictionary containing 'access_token' and 'instance_url'.
    
    Raises:
        EnvironmentError: If any of the required environment variables (except the security token) is missing.
        requests.HTTPError: If the POST request fails.
        ValueError: If the response JSON does not contain the required keys.
    """
    token_url = "https://login.salesforce.com/services/oauth2/token"
    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
    username = os.getenv("SALESFORCE_USERNAME")
    password = os.getenv("SALESFORCE_PASSWORD")
    security_token = os.getenv("SALESFORCE_SECURITY_TOKEN", "")

    if not (client_id and client_secret and username and password):
        raise EnvironmentError("One or more required Salesforce OAuth environment variables are not set.")

    combined_password = password + security_token

    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": combined_password
    }

    response = requests.post(token_url, data=payload)
    response.raise_for_status()
    auth_response = response.json()

    if "access_token" not in auth_response or "instance_url" not in auth_response:
        raise ValueError("Salesforce OAuth response missing access_token or instance_url.")

    return {
        "access_token": auth_response["access_token"],
        "instance_url": auth_response["instance_url"]
    }

def get_salesforce_connection() -> Salesforce:
    """
    Initializes and returns a Salesforce connection using the simple_salesforce library.

    Uses the OAuth access token and instance_url obtained from get_salesforce_access_token.
    The Salesforce API version is hardcoded to "55.0".
    
    Returns:
        An instance of simple_salesforce.Salesforce.
    
    Raises:
        Any exceptions raised from get_salesforce_access_token or the connection initialization.
    """
    auth_data = get_salesforce_access_token()
    sf = Salesforce(
        instance_url=auth_data["instance_url"],
        session_id=auth_data["access_token"],
        version="55.0"
    )
    return sf

def query_salesforce() -> List[Dict[str, Any]]:
    """
    Queries Salesforce data using its API.

    Executes the following SOQL query with hardcoded parameters:
      • SELECT Id, GCLID__c, Name, Original_Lead_Created_Date_Time__c, Admission_Date__c
      • FROM Opportunity
      • WHERE StageName IN ('Admitted', 'Alumni')
      • AND Original_Lead_Created_Date_Time__c = LAST_90_DAYS

    After retrieving the results, the function:
      1. Removes the extraneous 'attributes' field from each record.
      2. Filters out records where the 'GCLID__c' field is null.

    Returns:
        A list of dictionaries representing the cleaned Salesforce records.
    
    Raises:
        Any exceptions raised during the query or data processing.
    """
    sf = get_salesforce_connection()
    soql_query = (
        "SELECT Id, GCLID__c, Name, Original_Lead_Created_Date_Time__c, Admission_Date__c "
        "FROM Opportunity "
        "WHERE StageName IN ('Admitted', 'Alumni') "
        "AND Original_Lead_Created_Date_Time__c = LAST_90_DAYS"
    )
    result = sf.query_all(soql_query)
    records = result.get("records", [])
    
    # Remove extraneous 'attributes' field from each record.
    for record in records:
        record.pop("attributes", None)
    
    # Filter out records with a null GCLID__c field.
    filtered_records = [record for record in records if record.get("GCLID__c") is not None]
    return filtered_records
