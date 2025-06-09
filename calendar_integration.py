import json
import urllib.parse
from datetime import datetime

import logfire
import requests


def fetch_google_calendar_events(token: str, parameters: dict):
    """
        Fetch all events from all calendars of the user with the given token and at least one of the given parameters.

        Parameters:
            token: The user's Google API token.
            parameters: A dictionary of parameters with the following keys:
                search_string: A string to filter events by.
                minimum_end_time: A datetime object representing the minimum end time of events to fetch.
                maximum_start_time: A datetime object representing the maximum start time of events to fetch.
    """
    search_string = parameters.get('search_string', '')
    minimum_end_time = parameters.get('minimum_end_time', None)
    maximum_start_time = parameters.get('maximum_start_time', None)

    with logfire.span("Fetching Google Calendar events", parameters={search_string, minimum_end_time, maximum_start_time}):
        if minimum_end_time is None and maximum_start_time is None and not search_string:
            raise ValueError("At least one of minimum_end_time, maximum_start_time, or query must be provided.")
        if minimum_end_time is not None:
            if type(minimum_end_time) is not datetime:
                raise ValueError("minimum_end_time must be a datetime object.")
            if minimum_end_time.tzinfo is None:
                raise ValueError("minimum_end_time must be timezone-aware datetime object.")
        if maximum_start_time is not None:
            if type(maximum_start_time) is not datetime:
                raise ValueError("maximum_start_time must be a datetime object.")
            if maximum_start_time.tzinfo is None:
                raise ValueError("maximum_start_time must be timezone-aware datetime object.")
        params: dict[str, str | bool] = {'singleEvents': True}
        if search_string:
            params['q'] = search_string
        if minimum_end_time:
            params['timeMin'] = maximum_start_time.isoformat()
        if maximum_start_time:
            params['timeMax'] = minimum_end_time.isoformat()
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
        calendar_ids.append("primary")  # Include primary calendar

        events = []
        with logfire.span("Fetching events from all calendars"):
            for calendar_id in calendar_ids:
                try:
                    events_response = requests.get(
                        f'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events',
                        headers=headers,
                        params=params,
                    )
                    events_response.raise_for_status()
                    logfire.info(f"Fetched events from calendar {calendar_id}")
                    items = events_response.json()
                    logfire.info(f"Got {items}")
                    logfire.info(f"Got items data: {items}")
                    events.extend(items.get('items', []))
                except Exception as error:
                    # TODO: Handle specific exceptions, ?maybe wrap in logfire.span logfire.instrument?
                    logfire.exception(f"Failed to fetch events from calendar {calendar_id}: {error}")
        logfire.info(f"Fetched {len(events)} events from all calendars.")

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
        with logfire.span(f"Returning {len(return_events)} events."):
            for event in return_events:
                logfire.info(f"Event ID: {event['id']}, Summary: {event['summary']}, Start: {event['start']}, End: {event['end']}")

        return return_events


# events_response = requests.get(
#                 f'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?timeMin={datetime.now().isoformat()}Z',
#                 headers=headers,
#             )


def _get_managed_calendar(token: str):
    """ Internal method to get the managed calendar """
    headers = {
        'Authorization': f'Bearer {token}',
    }

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
    return ai_managed_calendar


def create_google_calendar_event(token: str, event_name: str, start_time: str, end_time: str, recurrence: list = None, description: str = None, location: str = None):
    """ Create a Google Calendar event with the given parameters and return the created event data. """
    headers = {
        'Authorization': f'Bearer {token}',
    }

    try:
        ai_managed_calendar = _get_managed_calendar(token)

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
                'dateTime': start_time
            },
            'end': {
                'dateTime': end_time
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


def delete_google_calendar_event(token: str, event_id: str):
    """ Delete a Google Calendar event. """
    headers = {
        'Authorization': f'Bearer {token}'
    }
    delete_response = requests.delete(
        f'https://www.googleapis.com/calendar/v3/calendars/{_get_managed_calendar(token)["id"]}/events/{event_id}',
        headers=headers,
    )
    delete_response.raise_for_status()
    return delete_response.json()