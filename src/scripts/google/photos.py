# get_photos_by_day.py

import os
import json
import datetime
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, build_from_document
import requests
import kewi

ARG_time_span: kewi.args.TimeSpan = "today"
kewi.ctx.init()


CREDENTIALS_PATH = "C:\\dev\\projects\\kewi\\src\\scripts\\google\\_credentials.json"
TOKEN_PATH = "C:\\dev\\projects\\kewi\\src\\scripts\\google\\_token.json"

# Define the scopes required by the Google Photos API
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

# URL for Google Photos Library API Discovery document
DISCOVERY_URL = 'https://photoslibrary.googleapis.com/$discovery/rest?version=v1'

def authenticate():
	"""Authenticates the user with OAuth 2.0 and returns a service object."""
	creds = None
	# Token file stores the user's access and refresh tokens
	if os.path.exists(TOKEN_PATH):
		creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				CREDENTIALS_PATH, SCOPES)
			creds = flow.run_local_server(port=0)
		with open(TOKEN_PATH, 'w+') as token:
			token.write(creds.to_json())
	
	# Manually fetch and load the API discovery document
	discovery_doc = requests.get(DISCOVERY_URL).text
	service = build_from_document(discovery_doc, credentials=creds)
	
	return service

def download_image(url, save_path):
	"""Downloads an image from the given URL and saves it to the specified path."""
	response = requests.get(url, stream=True)
	if response.status_code == 200:
		with open(save_path, 'wb+') as f:
			for chunk in response.iter_content(1024):
				f.write(chunk)
		print(f"Downloaded {save_path}")
	else:
		print(f"Failed to download {url} (status code: {response.status_code})")

def get_photos_by_timespan(service, timespan: kewi.args.TimeSpan):
	"""Fetches all photos from a specific date."""

	date_filters = [
		timespan.start - datetime.timedelta(days=1),
		timespan.start,
		timespan.end,
		timespan.end + datetime.timedelta(days=1)
	]
	date_filters = list(map(lambda d: {"year": d.year, "month": d.month, "day": d.day}, date_filters))
	filter_params = {
		"filters": {
			"dateFilter": {
				"dates": date_filters
			}
		}
	}
	
	results = service.mediaItems().search(body=filter_params).execute()
	unfiltered_items = results.get('mediaItems', [])
	items = []
	for item in unfiltered_items:
		date_string = item['mediaMetadata']['creationTime']
		date_string = date_string.replace('Z', '+00:00') 
		item_date = datetime.datetime.fromisoformat(date_string)
		item_date = item_date.replace(tzinfo=datetime.timezone.utc)
		if item_date > timespan.start and item_date < timespan.end:
			items.append(item)
	
	if not items:
		print(f'No photos found for:\n{timespan}.')
	else:
		print(f'Photos found for:\n{timespan}:')
		for item in items:
			print(f"- {item['filename']}: [{item['mediaMetadata']['creationTime']}] {item['productUrl']}")
			# Extract file name and extension
			file_name = item['filename']
			name, ext = os.path.splitext(file_name)

			# Get image URL and the file path where to save
			download_url = item['baseUrl'] + "=d"  # Adding '=d' to get the original quality
			save_path = kewi.cache.new(f"google_photos.{name}", ext.lstrip('.'))  # Call the cache function

			if not os.path.exists(save_path):
				download_image(download_url, save_path)
	return items

# Authenticate and get the Google Photos service object
service = authenticate()


# Retrieve and print photos from the given day
get_photos_by_timespan(service, ARG_time_span)

