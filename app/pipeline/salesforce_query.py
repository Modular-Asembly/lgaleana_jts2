import os
import requests
from typing import List, Dict, Any
from simple_salesforce import Salesforce

def get_salesforce_access_token() -> Dict[str, str]:
    """
    Obtains an OAuth 2.0 access token from Salesforce using credentials from environment variables.
    
    Expected environment variables:
    - SALESFORCE_CLIENT_ID
    - SALESFORCE_CLIENT_SECRET
    - SALESFORCE_USERNAME
    - SALESFORCE_PASSWORD
    - SALESFORCE_SECURITY_TOKEN (optional, if required by your Salesforce org)
    
    Returns:
        A dictionary containing 'access_token' and 'instance_url'.
    """
    token_url = "https://login.salesforce.com/services/oauth2/token"
    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
    username = os.getenv("SALESFORCE_USERNAME")
    password = os.getenv("SALESFORCE_PASSWORD")
    # Optional security token
    security_token = os.getenv("SALESFORCE_SECURITY_TOKEN", "")

    if not (client_id and client_secret and username and password):
        raise EnvironmentError("One or more Salesforce OAuth environment variables are not set.")

    # Combine password and security token if token is provided
    pwd_combined = password + security_token

    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": pwd_combined
    }

    response = requests.post(token_url, data=payload)
    response.raise_for_status()  # Let errors raise if the request failed
    auth_response = response.json()

    if "access_token" not in auth_response or "instance_url" not in auth_response:
        raise ValueError("Salesforce OAuth response does not contain access_token or instance_url.")

    return {
        "access_token": auth_response["access_token"],
        "instance_url": auth_response["instance_url"]
    }

def get_salesforce_connection() -> Salesforce:
    """
    Creates and returns a Salesforce connection using an OAuth access token.
    
    Returns:
        An instance of simple_salesforce.Salesforce.
    """
    auth_data = get_salesforce_access_token()
    # Create a Salesforce connection using the access token.
    sf = Salesforce(instance_url=auth_data["instance_url"], session_id=auth_data["access_token"], version="55.0")
    return sf

def query_salesforce() -> List[Dict[str, Any]]:
    """
    Queries Salesforce using its API. Executes the following SOQL query:
    
    SELECT Id, GCLID__c, Name, Original_Lead_Created_Date_Time__c, Admission_Date__c 
    FROM Opportunity 
    WHERE StageName IN ('Admitted', 'Alumni')
    AND Original_Lead_Created_Date_Time__c = LAST_90_DAYS
    
    Returns:
        A list of dictionaries where each dictionary represents a row from the query result.
        Records where GCLID__c is None are filtered out.
    """
    sf = get_salesforce_connection()
    soql_query = (
        "SELECT Id, GCLID__c, Name, Original_Lead_Created_Date_Time__c, Admission_Date__c "
        "FROM Opportunity "
        "WHERE StageName IN ('Admitted', 'Alumni') "
        "AND Original_Lead_Created_Date_Time__c = LAST_90_DAYS"
    )
    # Use query_all to ensure all records are retrieved.
    result = sf.query_all(soql_query)
    records = result.get("records", [])
    # Remove attributes added by simple_salesforce for a clean response.
    for record in records:
        record.pop('attributes', None)
    # Filter out records where GCLID__c is None
    records = [record for record in records if record.get('GCLID__c') is not None]
    return records
