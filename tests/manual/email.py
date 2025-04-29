import email_integration


token = 'ya29.a0AZYkNZiMohbwMvdsdP0wvc_L-mAiXVd4RSpDFhujjXcUVZNDwmu4u8hdEuh4hfudhia4bEwQ4HW8J8g5PsDwKqrSbBM1zFIvHQq56NEhF2qyx5mZy__HVEv9FET-TxTbcifrvmm46mynfqzEoNH4jbqNGDwPE4Vur3WMF6fEaCgYKAUQSARESFQHGX2MiqsZVPLV-vFqXFXMiu-FFbg0175'

def test_sending_email():
    receiver = 'zanges93@gmail.com'
    subject = 'Test Email'
    body = 'This is a test email.'

    draft_response = email_integration.draft_email(token, receiver, subject, body)
    assert draft_response is not None, "Failed to draft email"
    print('Draft response:')
    print(draft_response)
    draft_id = draft_response.get('id')
    assert draft_id is not None, "Draft ID is missing in the response"
    print(f"Draft ID: {draft_id}")

    sent_response = email_integration.send_draft(token, draft_id)
    assert sent_response is not None, "Failed to send email"
    print('Sent response:')
    print(sent_response)


def test_get_emails():
    search_string = 'Test Email'
    emails_response = email_integration.get_emails(token, search_string)
    assert emails_response is not None, "Failed to get emails"
    print('Emails response:')
    print(emails_response)
    assert isinstance(emails_response, dict), "Emails response is not a dictionary"
    assert 'messages' in emails_response, "Messages key is missing in the response"
    assert isinstance(emails_response['messages'], list), "Messages is not a list"
    assert len(emails_response['messages']) > 0, "No messages found in the response"
    i = 0
    for message in emails_response['messages']:
        if i > 5:
            break
        i += 1
        assert isinstance(message, dict), "Message is not a dictionary"
        assert 'id' in message, "Message ID is missing"
        assert 'threadId' in message, "Thread ID is missing"
        print(f"Message ID: {message['id']}, Thread ID: {message['threadId']}")
        # Get the specific email details
        email_details_response = email_integration.get_email_details(token, message['id'])
        assert email_details_response is not None, "Failed to get email details"
        print('Email details response:')
        print(email_details_response)


def main():
    # test_sending_email()
    test_get_emails()

    print("Test completed successfully.")


if __name__ == "__main__":
    main()