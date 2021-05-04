#!/usr/bin/env python3

import time
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


class GdriveUploader:
    """Base class providing google drive functionality"""

    __CREDENTIALS_FILE = 'credentials.json'
    __AUTH_ATTEMPTS = 5
    __AUTH_RETRY_DELAY = 3  # Seconds to wait before trying again

    def __init__(self):
        self.gauth = GoogleAuth()
        self.authenticated = False

    def authenticate(self):
        """Try to authenticate with google drive."""
        if self.authenticated:
            return True

        attempts = 0
        while not self.authenticated and attempts < self.__AUTH_ATTEMPTS:
            attempts += 1
            try:
                self.gauth.LoadCredentialsFile(self.__CREDENTIALS_FILE)

                if self.gauth.credentials is None:  # Authenticate if they're not there
                    self.gauth.LocalWebserverAuth()  # Creates local web server
                elif self.gauth.access_token_expired:
                    self.gauth.Refresh()  # Refresh them if expired
                else:
                    self.gauth.Authorize()
                    self.gauth.SaveCredentialsFile(self.__CREDENTIALS_FILE)

                self.authenticated = True
            except Exception as e:
                print("ERROR: Unable to authenticate google drive:", e)
                print(f"Retrying in {self.__AUTH_RETRY_DELAY} s")
                time.sleep(self.__AUTH_RETRY_DELAY)

        status = "success" if self.authenticated else "failed"
        print(f"Gdrive authentication {status} after {attempts} attempt(s)")

        return self.authenticated

    def upload_from_disk(self, filename: str):
        """Upload a new file from disk to google drive"""
        if self.authenticate():
            try:
                drive = GoogleDrive(self.gauth)
                drive_file = drive.CreateFile()
                drive_file.SetContentFile(filename)
                drive_file.Upload()
            except Exception as e:
                print("ERROR: Gdrive upload failed:", e)
        else:
            print("ERROR: Skipping upload, since authenticating failed")

    def overwrite_from_disk(self, filename: str):
        """Update an existing file on drive from a file on disk
        If it doesn't already exist, create a new one.
        """
        if self.authenticate():
            try:
                drive = GoogleDrive(self.gauth)
                matching_files = drive.ListFile(
                    {'q': f"title='{filename}' and trashed=false"}
                ).GetList()

                if matching_files:
                    print(f"Overwriting existing file '{filename}'")
                    drive_file = matching_files[0]
                else:
                    print(f"Creating new file '{filename}'")
                    drive_file = drive.CreateFile()

                    drive_file.SetContentFile(filename)
                    drive_file.Upload()
            except Exception as e:
                print("ERROR: Gdrive upload failed:", e)
        else:
            print("ERROR: Skipping upload, since authenticating failed")


def main():
    print("Authenticating")
    gdrive = GdriveUploader()
    gdrive.authenticate()
    print("Done")
