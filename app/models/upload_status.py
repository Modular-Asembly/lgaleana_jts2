from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database.sql_adaptor import Base
import datetime

class UploadStatus(Base):
    __tablename__ = "upload_status"

    id = Column(Integer, primary_key=True, index=True)
    salesforce_id = Column(String, nullable=False, comment="Primary key for the upload record entry: Salesforce Opportunity Id from the query result.")
    gclid = Column(String, nullable=True, comment="The GCLID value (GCLID__c) from the Salesforce record, used for conversion tracking.")
    original_lead_created_datetime = Column(DateTime, nullable=False, comment="The Original_Lead_Created_Date_Time__c field from the Salesforce record capturing when the lead was created.")
    admission_date = Column(DateTime, nullable=False, comment="The Admission_Date__c field from the Salesforce record indicating the date of admission.")
    status = Column(String, nullable=False, comment="Upload status indicator, e.g., 'successful' or 'failed'.")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, comment="The date and time when this upload status was recorded.")
    error_details = Column(Text, nullable=True, comment="Contains error details if the upload failed, otherwise null.")
    
    def __repr__(self):
        return (f"<UploadStatus(id={self.id}, salesforce_id='{self.salesforce_id}', "
                f"gclid='{self.gclid}', original_lead_created_datetime='{self.original_lead_created_datetime}', "
                f"admission_date='{self.admission_date}', status='{self.status}', "
                f"timestamp='{self.timestamp}', error_details='{self.error_details}')>")
