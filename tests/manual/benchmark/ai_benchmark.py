import logfire
import requests


auth_token = None

BASE_URL = "http://localhost:8000"
AI_ENDPOINT = "/chat"


def wrapper(func: callable):
    def wrapped():
        global auth_token
        if auth_token is None:
            auth_token = input("go to http://localhost:8000/ click login and after that on log token and paste the token here: ")
        return func(auth_token)
    return wrapped


@wrapper
def simple_question(auth_token: str):
    response = requests.post(
        BASE_URL + AI_ENDPOINT,
        json={"message": "Who was the first president of the United States?"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()


@wrapper
def calender_question(auth_token: str):
    response = requests.post(
        BASE_URL + AI_ENDPOINT,
        json={"message": "When is my AI test event happening?"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()


@wrapper
def hard_calender_question(auth_token: str):
    response = requests.post(
        BASE_URL + AI_ENDPOINT,
        json={"message": "When is my next event at the Microsoft Headquarters happening?"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()


@wrapper
def create_event(auth_token: str):
    response = requests.post(
        BASE_URL + AI_ENDPOINT,
        json={"message": "Create a calendar entry for next Tuesday for showcase at 10am."},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()


@wrapper
def create_event_with_location(auth_token: str):
    response = requests.post(
        BASE_URL + AI_ENDPOINT,
        json={"message": "Create a calendar entry for next Tuesday for Microsoft Showcase at 10am at the Microsoft Headquarters."},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()


@wrapper
def create_complex_event(auth_token: str):
    response = requests.post(
        BASE_URL + AI_ENDPOINT,
        json={"message": "Monday in two weeks, I have a flight from Cologne airport to Berlin at 7 in the morning. add a calendar entry for this."},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()


def main():
    simple_question_result = simple_question()
    calender_question_result = calender_question()
    hard_calender_question_result = hard_calender_question()
    create_event_result = create_event()
    create_event_with_location_result = create_event_with_location()
    create_complex_event_result = create_complex_event()
    print(create_complex_event_result)


if __name__ == "__main__":
    main()