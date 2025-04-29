import base64
from email.message import EmailMessage

import requests


def draft_email(token: str, recipient: str, subject: str, body: str) -> dict:
    """
    Draft an email using the Gmail API.

    Args:
        token (str): The OAuth2 token for authentication.
        recipient (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): The body of the email.

    Returns:
        dict: The draft email response from the Gmail API.
    """
    message = EmailMessage()
    message['To'] = recipient
    message['Subject'] = subject
    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_draft_message = {'message': {'raw': encoded_message}}

    try:
        response = requests.post(
            'https://gmail.googleapis.com/gmail/v1/users/me/drafts',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            json=create_draft_message
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to draft email: {e}")

def get_drafts(token: str, search_string: str = '') -> dict:
    """
    Get a list of email drafts using the Gmail API.

    Args:
        token (str): The OAuth2 token for authentication.
        search_string (str): The search string to filter drafts (optional).

    Returns:
        dict: The list of email drafts from the Gmail API.
    """
    try:
        if search_string:
            response = requests.get(
                f'https://gmail.googleapis.com/gmail/v1/users/me/drafts?q={search_string}',
                headers={'Authorization': f'Bearer {token}'}
            )
        else:
            response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/drafts',
                headers={'Authorization': f'Bearer {token}'}
            )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get drafts: {e}")

def send_draft(token: str, draft_id: str) -> dict:
    """
    Send a draft email using the Gmail API.

    Args:
        token (str): The OAuth2 token for authentication.
        draft_id (str): The ID of the draft to send.

    Returns:
        dict: The sent email response from the Gmail API.
    """
    try:
        get_draft_response = requests.get(
            f'https://gmail.googleapis.com/gmail/v1/users/me/drafts/{draft_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        get_draft_response.raise_for_status()
        draft = get_draft_response.json()
        send_response = requests.post(
            f'https://gmail.googleapis.com/gmail/v1/users/me/drafts/send',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json=draft
        )
        send_response.raise_for_status()
        return send_response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to send draft: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error! Failed to send draft: {e}")

def delete_draft(token: str, draft_id: str) -> None:
    """
    Delete a draft email using the Gmail API.

    Args:
        token (str): The OAuth2 token for authentication.
        draft_id (str): The ID of the draft to delete.

    Returns:
        None
    """
    try:
        response = requests.delete(
            f'https://gmail.googleapis.com/gmail/v1/users/me/drafts/{draft_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to delete draft: {e}")

def get_emails(token: str, search_string: str) -> dict: #TODO: can search_string be optional?
    """
    Get a list of emails using the Gmail API.

    Args:
        token (str): The OAuth2 token for authentication.
        search_string (str): The search string to filter emails.

    Returns:
        dict: The list of emails from the Gmail API.
    """
    try:
        response = requests.get(
            f'https://gmail.googleapis.com/gmail/v1/users/me/messages?q={search_string}',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get emails: {e}")

def get_email_details(token: str, email_id: str) -> dict:
    """
    Get the details of an email using the Gmail API.

    Args:
        token (str): The OAuth2 token for authentication.
        email_id (str): The ID of the email to retrieve.

    Returns:
        dict: The details of the email from the Gmail API.
    """
    try:
        response = requests.get(
            f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{email_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get email details: {e}")