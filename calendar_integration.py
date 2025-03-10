from datetime import datetime

import requests


def fetch_google_calendar_events(token: str):
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
            print(f'Error fetching events for calendar {calendar_id}: {error}')
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


def create_google_calendar_event(token: str, event_name: str, start_time: datetime, end_time: datetime, recurrence: str = None, description: str = None, location: str = None):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    calendars_response = requests.get(
        'https://www.googleapis.com/calendar/v3/users/me/calendarList',
        headers=headers,
    )
    calendars_response.raise_for_status()
    calendars = calendars_response.json()['items']
    try:
        ai_managed_calendar = filter(lambda calendar: calendar['summary'] == 'AI Managed Calendar', calendars).__next__()
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
    event_response = requests.post(
        f'https://www.googleapis.com/calendar/v3/calendars/{ai_managed_calendar["id"]}/events',
        headers=headers,
        json={
            'summary': event_name,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
            },
            'end': {
                'dateTime': end_time.isoformat(),
            },
            'location': location,
            'recurrence': recurrence,
        },
    )
    event_response.raise_for_status()
    return event_response.json()