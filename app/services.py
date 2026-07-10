import os
import json
import base64
from typing import List
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime

# --- Supabase Service ---
class SupabaseService:
    def __init__(self):
        supabase_url = os.environ.get("SUPABASE_URL", "")
        supabase_key = os.environ.get("SUPABASE_KEY", "")
        if not supabase_url or not supabase_key:
            print("WARNING: Supabase credentials not found.")
            self.client = None
        else:
            self.client: Client = create_client(supabase_url, supabase_key)

    def get_leads(self):
        if not self.client:
            return []
        try:
            response = self.client.table("leads").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error fetching leads: {e}")
            return []
            
    def save_message(self, lead_phone: str, message: str, sender: str):
        if not self.client:
            return
        try:
            # Implementação de salvamento de log
            pass
        except Exception as e:
            print(f"Error saving message: {e}")

# --- Twilio Service ---
class TwilioService:
    def __init__(self):
        sid = os.environ.get("TWILIO_SID")
        token = os.environ.get("TWILIO_TOKEN")
        self.phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
        if sid and token:
            self.client = TwilioClient(sid, token)
        else:
            self.client = None

    def send_sms(self, to: str, body: str):
        if not self.client:
            print(f"[Mock Twilio] Sending SMS to {to}: {body}")
            return
        try:
            message = self.client.messages.create(
                body=body,
                from_=self.phone_number,
                to=to
            )
            return message.sid
        except Exception as e:
            print(f"Twilio error: {e}")

# --- Calendar Service ---
class CalendarService:
    def __init__(self):
        creds_b64 = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS")
        self.service = None
        if creds_b64:
            try:
                creds_json = base64.b64decode(creds_b64).decode("utf-8")
                creds_info = json.loads(creds_json)
                creds = Credentials.from_authorized_user_info(creds_info)
                self.service = build("calendar", "v3", credentials=creds)
            except Exception as e:
                print(f"Error setting up Calendar: {e}")

    def get_availability(self) -> List[str]:
        if not self.service:
            print("[Mock Calendar] Returning mock availability.")
            return ["Tomorrow at 10:00 AM", "Tomorrow at 2:00 PM"]
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        try:
            events_result = self.service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=10, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            return [e.get('summary') for e in events]
        except Exception as e:
            print(f"Error getting events: {e}")
            return []

supabase_svc = SupabaseService()
twilio_svc = TwilioService()
calendar_svc = CalendarService()
