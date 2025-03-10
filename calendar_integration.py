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
    for calendar in calendars:
        print('Calendar:')
        for key, value in calendar.items():
            print(f'{key}: {value}')
        print('=' * 20)
        print('\n')
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
            'status': event.get('status'),
            'summary': event.get('summary'),
            'description': event.get('description'),
            'start': event.get('start'),
            'end': event.get('end'),
        })
    return return_events