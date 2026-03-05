import pytest
from unittest.mock import MagicMock, patch
from backend.workers.email_worker import EmailWorker
import json

@pytest.fixture
def mock_service():
    service = MagicMock()
    service.get_task.return_value = MagicMock(workspace_id=1)
    return service

@pytest.fixture
def mock_db():
    return MagicMock()

@patch('backend.workers.email_worker.MailboxTools')
def test_email_worker_search(mock_mailbox_cls, mock_service, mock_db):
    # Setup
    mailbox = mock_mailbox_cls.return_value
    mailbox.search_emails.return_value = json.dumps([
        {"id": "1", "subject": "Test", "from": "sender@test.com", "date": "2023-01-01", "snippet": "Hello"}
    ])
    
    input_data = {"action": "search", "query": "Test"}
    
    # Execute
    result = EmailWorker.execute("task_1", input_data, mock_service, mock_db)
    
    # Verify
    assert result["processed_count"] == 1
    assert result["emails_found"][0]["subject"] == "Test"
    mailbox.search_emails.assert_called_with("Test", limit=10)

@patch('backend.workers.email_worker.MailboxTools')
def test_email_worker_summarize(mock_mailbox_cls, mock_service, mock_db):
    # Setup
    mailbox = mock_mailbox_cls.return_value
    # Initial list
    mailbox.list_emails.return_value = json.dumps([
        {"id": "1", "subject": "Meeting", "from": "boss@co.com", "date": "Today", "snippet": "Urgent"}
    ])
    # Detail read
    mailbox.read_email.return_value = json.dumps({"body": "Full body content"})
    
    input_data = {"action": "summarize", "scope": "today"}
    
    # Execute
    result = EmailWorker.execute("task_1", input_data, mock_service, mock_db)
    
    # Verify
    assert "Meeting" in result["summary"]
    assert "boss@co.com" in result["summary"]
    mailbox.list_emails.assert_called()

@patch('backend.workers.email_worker.MailboxTools')
def test_email_worker_reply_draft(mock_mailbox_cls, mock_service, mock_db):
    # Setup
    mailbox = mock_mailbox_cls.return_value
    mailbox.search_emails.return_value = json.dumps([
        {"id": "1", "subject": "Question", "from": "client@test.com", "date": "Today", "snippet": "Help?"}
    ])
    
    input_data = {"action": "reply", "query": "Question"}
    
    # Execute
    result = EmailWorker.execute("task_1", input_data, mock_service, mock_db)
    
    # Verify
    assert "Proposed Replies" in result["summary"]
    assert "To client@test.com" in result["summary"]
    # Should NOT send email
    mailbox.send_email.assert_not_called()
