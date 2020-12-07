import io
import re
import objects
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
standard_fields = 'files(id, name, parents, modifiedTime)'
scope = ['https://www.googleapis.com/auth/drive']


def revoke_time(file):
    if file.get('modifiedTime'):
        stamp = re.sub(r'\..*?Z', '', file['modifiedTime'])
        file['modifiedTime'] = objects.stamper(stamp, '%Y-%m-%dT%H:%M:%S')
    return file


class Drive:
    def __init__(self, path):
        credentials = service_account.Credentials.from_service_account_file(path, scopes=scope)
        self.client = build('drive', 'v3', credentials=credentials)

    def file(self, file_id):
        response = self.client.files().get(fileId=file_id).execute()
        return response

    def get_file_by_name(self, file_name, fields=standard_fields):
        response = None
        drive_response = self.client.files().list(pageSize=1000, fields=fields).execute()
        for file in drive_response['files']:
            if file_name == file['name']:
                response = revoke_time(file)
                break
        return response

    def files(self, fields=standard_fields):
        response = []
        result = self.client.files().list(pageSize=1000, fields=fields).execute()
        for file in result['files']:
            response.append(revoke_time(file))
        return response

    def create_file(self, file_path, folder_id, same_file_name='True'):
        if same_file_name == 'True':
            same_file_name = re.sub('(.*)/', '', file_path)
        media_body = MediaFileUpload(file_path, resumable=True)
        file_metadata = {'name': same_file_name, 'parents': [folder_id]}
        return self.client.files().create(body=file_metadata, media_body=media_body, fields='id').execute()

    def update_file(self, file_id, file_path):
        media_body = MediaFileUpload(file_path, resumable=True)
        response = self.client.files().update(fileId=file_id, media_body=media_body).execute()
        return response

    def download_file(self, file_id, file_path):
        done = False
        file = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(file, self.client.files().get_media(fileId=file_id))
        while done is False:
            status, done = downloader.next_chunk()

    def delete_file(self, file_id):
        self.client.files().delete(fileId=file_id).execute()
