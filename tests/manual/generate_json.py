import json

from email_integration import get_emails, get_email_details

email_json_filename = "email.json"
email_details_json_filename = "email_details.json"
auth_token = None


def wrapper(func: callable):
    def wrapped():
        global auth_token
        if auth_token is None:
            auth_token = input("go to http://localhost:8000/ click login and after that on log token and paste the token here: ")
        return func(auth_token)
    return wrapped


@wrapper
def generate_email_json(auth_token: str):
    result = get_emails(auth_token, "new openai model")
    json_result = json.dumps(result)
    with open(email_json_filename, "w") as f:
        f.write(json_result)
    print(f"Successfully wrote {email_json_filename}")


@wrapper
def generate_email_details_json(auth_token: str):
    with open(email_json_filename, "r") as f:
        emails = json.load(f)
    email_ids = [email['id'] for email in emails['messages']]
    emails = []
    for email_id in email_ids:
        email_details = get_email_details(auth_token, email_id)
        emails.append(email_details)
    with open(email_details_json_filename, "w") as f:
        f.write(json.dumps(emails))


if __name__ == "__main__":
    #generate_email_json()
    generate_email_details_json()