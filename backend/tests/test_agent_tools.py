import pytest
from unittest.mock import MagicMock, patch
import json
from backend.tools.mailbox_tools import MailboxTools
from backend.tools.drive_tools import DriveTools

# Mock Database Session
@pytest.fixture
def mock_db_session():
    return MagicMock()

# --- MailboxTools Tests ---

@patch('backend.tools.mailbox_tools.SessionLocal')
@patch('backend.tools.mailbox_tools.GmailService')
@patch('backend.tools.mailbox_tools.OutlookService')
@patch('backend.tools.mailbox_tools.ICloudService')
def test_mailbox_list_emails_gmail(mock_icloud, mock_outlook, mock_gmail, mock_session_local, mock_db_session):
    mock_session_local.return_value = mock_db_session
    
    # Setup Mock Service
    gmail_instance = mock_gmail.return_value
    gmail_instance.list_emails.return_value = [{"id": "1", "subject": "Test", "provider": "gmail"}]
    
    # Test
    tools = MailboxTools(workspace_id=1)
    result = tools.list_emails(provider="gmail_mailbox")
    
    # Verify
    assert "Test" in result
    assert "gmail" in result
    gmail_instance.list_emails.assert_called_once_with(1, 10)
    mock_outlook.assert_not_called()

@patch('backend.tools.mailbox_tools.SessionLocal')
@patch('backend.tools.mailbox_tools.GmailService')
@patch('backend.tools.mailbox_tools.OutlookService')
def test_mailbox_list_emails_all_providers(mock_outlook, mock_gmail, mock_session_local, mock_db_session):
    mock_session_local.return_value = mock_db_session
    
    # Setup Mocks
    gmail_instance = mock_gmail.return_value
    gmail_instance.list_emails.return_value = [{"id": "1", "subject": "Gmail Msg"}]
    
    outlook_instance = mock_outlook.return_value
    outlook_instance.list_emails.return_value = [{"id": "2", "subject": "Outlook Msg"}]
    
    # Test (No provider specified -> should check all)
    tools = MailboxTools(workspace_id=1)
    result = tools.list_emails()
    
    # Verify
    assert "Gmail Msg" in result
    assert "Outlook Msg" in result
    gmail_instance.list_emails.assert_called()
    outlook_instance.list_emails.assert_called()

@patch('backend.tools.mailbox_tools.SessionLocal')
@patch('backend.tools.mailbox_tools.GmailService')
def test_mailbox_send_email(mock_gmail, mock_session_local, mock_db_session):
    mock_session_local.return_value = mock_db_session
    
    # Setup Mock
    gmail_instance = mock_gmail.return_value
    # Mock detection: _get_integration returns specific object
    gmail_instance._get_integration.return_value = MagicMock() 
    gmail_instance.send_email.return_value = True
    
    # Test
    tools = MailboxTools(workspace_id=1)
    result = tools.send_email("test@example.com", "Subject", "Body")
    
    # Verify
    assert "successfully" in result
    gmail_instance.send_email.assert_called_with(1, "test@example.com", "Subject", "Body")

# --- DriveTools Tests ---

@patch('backend.tools.drive_tools.SessionLocal')
@patch('backend.tools.drive_tools.GoogleDriveService')
def test_drive_list_files(mock_drive, mock_session_local, mock_db_session):
    mock_session_local.return_value = mock_db_session
    
    # Setup Mock
    drive_instance = mock_drive.return_value
    drive_instance.list_files.return_value = [{"id": "abc", "name": "Report.pdf"}]
    
    # Test
    tools = DriveTools(workspace_id=1)
    result = tools.list_files()
    
    # Verify
    assert "Report.pdf" in result
    drive_instance.list_files.assert_called_with(1, None, 10)

@patch('backend.tools.drive_tools.SessionLocal')
@patch('backend.tools.drive_tools.GoogleDriveService')
def test_drive_upload_file(mock_drive, mock_session_local, mock_db_session):
    mock_session_local.return_value = mock_db_session
    
    # Setup Mock
    drive_instance = mock_drive.return_value
    drive_instance.upload_file.return_value = {"id": "new_id", "link": "http://drive..."}
    
    # Test
    tools = DriveTools(workspace_id=1)
    result = tools.upload_file("NewDoc.txt", "Content")
    
    # Verify
    assert "new_id" in result
    drive_instance.upload_file.assert_called_with(1, "NewDoc.txt", "Content")
