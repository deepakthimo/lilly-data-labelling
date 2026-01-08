import os
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


# Paths & Credentials
CLIENT_SECRET_FILE = 'credentials.json' 
TOKEN_FILE = 'token.json'
SPREADSHEET_ID = '1brJxCWtUrCCCMrDe8UTeWLIDZSr_tgWdJEU8tEkKxKY'
SHEET_NAME = 'main'
PARENT_DRIVE_FOLDER_ID = '1Rbc_QD-PMOIb3qQgoC_tUOnoXPBQwEB9'

# Scopes (Read/Write)
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets', 
    'https://www.googleapis.com/auth/drive'
]


def get_google_services():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    sheets = build('sheets', 'v4', credentials=creds)
    drive = build('drive', 'v3', credentials=creds)
    return sheets, drive

sheets_service, drive_service = get_google_services()


def get_or_create_folder(folder_name, parent_id):
    """Finds a folder by name or creates it if missing."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{parent_id}' in parents and trashed=false"
    files = drive_service.files().list(q=query, fields='files(id)').execute().get('files', [])
    if files: 
        return files[0]['id']
    
    meta = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    created = drive_service.files().create(body=meta, fields='id').execute()
    return created.get('id')

def upload_or_update_file(content, filename, folder_id, mime_type='text/markdown'):
    """
    Checks if file exists in folder. 
    If YES -> Updates content (Overwrites).
    If NO -> Creates new file.
    Returns: WebViewLink
    """
    # 1. Search for existing file
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, webViewLink)").execute()
    files = results.get('files', [])

    # 2. Normalize content to bytes (CRITICAL FIX)
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    elif isinstance(content, bytes):
        content_bytes = content
    else:
        raise TypeError("content must be str or bytes")

    media = MediaIoBaseUpload(BytesIO(content_bytes), mimetype=mime_type, resumable=True)

    if files:
        # UPDATE existing
        file_id = files[0]['id']
        print(f"   -> File exists ({filename}). Overwriting...")
        drive_service.files().update(fileId=file_id, media_body=media).execute()
        return files[0]['webViewLink']
    else:
        # CREATE new
        print(f"   -> Creating new file ({filename})...")
        meta = {'name': filename, 'parents': [folder_id]}
        file = drive_service.files().create(body=meta, media_body=media, fields='webViewLink').execute()
        return file.get('webViewLink')


def update_or_append_sheet(row_data, target_filename):
    """
    Scans Column B (Filename) for existence.
    If Found -> Updates that row.
    If Not Found -> Appends to bottom.
    """
    # 1. Fetch all existing filenames (Column B)
    # Assuming Column B is index 1. We fetch B:B
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, 
        range=f"{SHEET_NAME}!B:B"
    ).execute()
    
    existing_filenames = [row[0] for row in result.get('values', []) if row] # Flatten list

    row_index_to_update = -1
    
    # 2. Check if filename exists
    for i, name in enumerate(existing_filenames):
        if name == target_filename:
            row_index_to_update = i + 1 # Sheets are 1-indexed
            break

    body = {'values': [row_data]}

    if row_index_to_update > 0:
        # UPDATE
        print(f"   -> Entry found at Row {row_index_to_update}. Updating row.")
        # Calculate range based on length of row_data (e.g., A5:J5)
        # Assuming data starts at Col A. 
        end_col_char = chr(65 + len(row_data) - 1) # Calculate letter (A=65)
        range_name = f"{SHEET_NAME}!A{row_index_to_update}:{end_col_char}{row_index_to_update}"
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range=range_name,
            valueInputOption="RAW", body=body
        ).execute()
    else:
        # APPEND
        print("   -> Entry not found. Appending new row.")
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS", body=body
        ).execute()

def download_file_content(filename, folder_id):
    """Finds a file containing the filename in the specific folder and downloads content."""
    # We search using 'contains' in case the file is named "NCT..._cleaned.md" or just "NCT..."
    query = f"name contains '{filename}' and '{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        raise FileNotFoundError(f"No file found for '{filename}' in the folder.")

    # Use the first match
    file_id = files[0]['id']
    request = drive_service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    return fh.getvalue().decode('utf-8')

def get_row_data(target_filename):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, 
        range=f"{SHEET_NAME}!A:M" # Fetch up to Column M
    ).execute()
    
    values = result.get('values', [])
    
    # Column B is Index 1
    for i, row in enumerate(values):
        if len(row) > 1 and row[1] == target_filename:
            return i + 1, row # Return 1-based index and row data
            
    return None, None

def update_cell(row_index, col_letter, value):
    range_name = f"{SHEET_NAME}!{col_letter}{row_index}"
    body = {'values': [[value]]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=range_name,
        valueInputOption="RAW", body=body
    ).execute()