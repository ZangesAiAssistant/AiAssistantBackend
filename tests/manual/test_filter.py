import json

import search


def load_email_json():
    with open("email_details.json", "r") as f:
        return json.load(f)


def test_filter_emails():
    emails = load_email_json()
    preprocessing_result = search.preprocess_emails(emails)
    # print(preprocessing_result)
    # with open("email_details_preprocessed.json", "w") as f:
    #     json.dump(preprocessing_result, f)
    filtered_emails = search.search(preprocessing_result, "new openai model")
    assert len(filtered_emails) == 5
    print(f"Filtered emails: {filtered_emails}")


if __name__ == "__main__":
    test_filter_emails()