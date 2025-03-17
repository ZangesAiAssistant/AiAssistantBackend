from datetime import datetime

import logfire
import requests


def fetch_google_calendar_events(token: str):
    """ Fetch all events from all calendars of the user with the given token. """
    headers = {
        'Authorization': f'Bearer {token}',
    }
    calendars_response = requests.get(
        'https://www.googleapis.com/calendar/v3/users/me/calendarList',
        headers=headers,
    )
    calendars_response.raise_for_status()
    calendars = calendars_response.json()['items']
    calendar_ids = [calendar['id'] for calendar in calendars]
    events = []
    for calendar_id in calendar_ids:
        try:
            events_response = requests.get(
                f'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?timeMin={datetime.now().isoformat()}Z',
                headers=headers,
            )
            events_response.raise_for_status()
            events.extend(events_response.json()['items'])
        except Exception as error:
            # TODO: Handle specific exceptions, ?maybe wrap in logfire.span logfire.instrument?
            logfire.exception(f"Failed to fetch events from calendar {calendar_id}: {error}")
    return_events = []
    for event in events:
        return_events.append({
            'id': event.get('id'),
            'summary': event.get('summary'),
            'description': event.get('description'),
            'start': event.get('start'),
            'end': event.get('end'),
            'attendees': event.get('attendees'),
            'location': event.get('location'),
            'recurrence': event.get('recurrence'),
        })
    return return_events


def create_google_calendar_event(token: str, event_name: str, start_time: datetime, end_time: datetime, recurrence: list = None, description: str = None, location: str = None):
    """ Create a Google Calendar event with the given parameters and return the created event data. """
    headers = {
        'Authorization': f'Bearer {token}',
    }

    try:
        # Get list of calendars
        calendars_response = requests.get(
            'https://www.googleapis.com/calendar/v3/users/me/calendarList',
            headers=headers,
        )
        calendars_response.raise_for_status()
        calendars = calendars_response.json()['items']

        # Find or create AI Managed Calendar
        try:
            ai_managed_calendar = next(filter(lambda calendar: calendar['summary'] == 'AI Managed Calendar', calendars))
        except StopIteration:
            ai_managed_calendar = None

        if ai_managed_calendar is None:
            calendar_create_response = requests.post(
                'https://www.googleapis.com/calendar/v3/calendars',
                headers=headers,
                json={
                    'summary': 'AI Managed Calendar',
                },
            )
            calendar_create_response.raise_for_status()
            ai_managed_calendar = calendar_create_response.json()

        # Prepare event data
        event_data = {
            'summary': event_name,
            'start': {
                'dateTime': start_time.isoformat() + 'Z',  # Adding 'Z' for UTC time
            },
            'end': {
                'dateTime': end_time.isoformat() + 'Z',  # Adding 'Z' for UTC time
            },
        }
        if description:
            event_data['description'] = description
        if location:
            event_data['location'] = location
        if recurrence:
            event_data['recurrence'] = recurrence if isinstance(recurrence, list) else [recurrence]

        # Create event
        event_response = requests.post(
            f'https://www.googleapis.com/calendar/v3/calendars/{ai_managed_calendar["id"]}/events',
            headers=headers,
            json=event_data,
        )
        event_response.raise_for_status()
        return event_response.json()

    except requests.exceptions.HTTPError as e:
        logfire.exception(f"HTTP error occurred: {e}. Response content: {e.response.content}")
        raise
    except Exception as e:
        logfire.exception(f"Error creating calendar event: {e}")
        raise