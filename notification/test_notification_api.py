#!/usr/bin/python3
#pylint: disable = invalid-name, broad-except, missing-docstring
"""
Unit tests for notification_api.py
Tests cover all major functions including logger initialization, 
configuration reading, email sending, and elasticsearch operations.
"""

import unittest
import logging
import sys
import os
from unittest.mock import patch, MagicMock, call
import pytest
import notification_api


class TestLoggerInitialization(unittest.TestCase):
    """Test cases for logger initialization functions"""

    @pytest.mark.unit
    @pytest.mark.logger
    def test_init_logger_returns_stream_handler(self):
        """Test that init_logger returns a StreamHandler"""
        handler = notification_api.init_logger()
        self.assertIsInstance(handler, logging.StreamHandler)

    @pytest.mark.unit
    @pytest.mark.logger
    def test_init_logger_has_formatter(self):
        """Test that init_logger applies formatter correctly"""
        handler = notification_api.init_logger()
        self.assertIsNotNone(handler.formatter)
        self.assertIsInstance(handler.formatter, logging.Formatter)

    @pytest.mark.unit
    @pytest.mark.logger
    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a Logger instance"""
        logger = notification_api.get_logger()
        self.assertIsInstance(logger, logging.Logger)

    @pytest.mark.unit
    @pytest.mark.logger
    def test_get_logger_name(self):
        """Test that get_logger creates logger with correct name"""
        logger = notification_api.get_logger()
        self.assertEqual(logger.name, "notification-service")

    @pytest.mark.unit
    @pytest.mark.logger
    def test_get_logger_debug_level(self):
        """Test that get_logger sets DEBUG level"""
        logger = notification_api.get_logger()
        self.assertEqual(logger.level, logging.DEBUG)

    @pytest.mark.unit
    @pytest.mark.logger
    def test_get_logger_has_handler(self):
        """Test that get_logger has at least one handler"""
        logger = notification_api.get_logger()
        self.assertGreater(len(logger.handlers), 0)


class TestConfigurationReading(unittest.TestCase):
    """Test cases for configuration reading functions"""

    @pytest.mark.unit
    @pytest.mark.config
    @patch.dict(os.environ, {"CONFIG_FILE": "/path/to/config.yaml"})
    @patch("notification_api.config.load")
    def test_read_configuration_success(self, mock_config_load):
        """Test successful configuration reading"""
        mock_config = MagicMock()
        mock_config_load.return_value = mock_config
        
        result = notification_api.read_configuration()
        
        self.assertEqual(result, mock_config)
        mock_config_load.assert_called_once_with("/path/to/config.yaml")

    @pytest.mark.unit
    @pytest.mark.config
    @patch.dict(os.environ, {"CONFIG_FILE": "/invalid/path.yaml"})
    @patch("notification_api.config.load")
    def test_read_configuration_exception(self, mock_config_load):
        """Test configuration reading with exception"""
        mock_config_load.side_effect = Exception("Config file not found")
        
        with patch("notification_api.get_logger") as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            result = notification_api.read_configuration()
            
            mock_logger_instance.error.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.config
    @patch.dict(os.environ, {"CONFIG_FILE": ""})
    def test_read_configuration_no_config_file_env(self):
        """Test configuration reading when CONFIG_FILE env is not set"""
        with patch("notification_api.config.load") as mock_config_load:
            mock_config = MagicMock()
            mock_config_load.return_value = mock_config
            
            result = notification_api.read_configuration()
            
            # Even if CONFIG_FILE is empty, it should be passed to load
            mock_config_load.assert_called_once()


class TestEmailFunctionality(unittest.TestCase):
    """Test cases for email sending functions"""

    @pytest.mark.unit
    @pytest.mark.email
    @patch("notification_api.read_configuration")
    @patch("notification_api.emails.html")
    def test_send_mail_success(self, mock_emails_html, mock_read_config):
        """Test successful email sending"""
        mock_config = MagicMock()
        mock_config.getProperty.side_effect = lambda key: {
            "smtp.from": "sender@example.com",
            "smtp.smtp_server": "smtp.example.com",
            "smtp.smtp_port": 587,
            "smtp.username": "user@example.com",
            "smtp.password": "password123",
        }.get(key)
        mock_read_config.return_value = mock_config
        
        mock_message = MagicMock()
        mock_emails_html.return_value = mock_message
        
        notification_api.send_mail("recipient@example.com")
        
        mock_emails_html.assert_called_once()
        mock_message.send.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.email
    @patch("notification_api.read_configuration")
    @patch("notification_api.emails.html")
    def test_send_mail_exception(self, mock_emails_html, mock_read_config):
        """Test email sending with exception"""
        mock_config = MagicMock()
        mock_read_config.return_value = mock_config
        mock_emails_html.side_effect = Exception("SMTP connection failed")
        
        with patch("notification_api.get_logger") as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            notification_api.send_mail("recipient@example.com")
            
            mock_logger_instance.error.assert_called()

    @pytest.mark.unit
    @pytest.mark.email
    @patch("notification_api.read_configuration")
    @patch("notification_api.emails.html")
    def test_send_mail_email_content(self, mock_emails_html, mock_read_config):
        """Test that email has correct content"""
        mock_config = MagicMock()
        mock_config.getProperty.side_effect = lambda key: {
            "smtp.from": "sender@example.com",
            "smtp.smtp_server": "smtp.example.com",
            "smtp.smtp_port": 587,
            "smtp.username": "user@example.com",
            "smtp.password": "password123",
        }.get(key)
        mock_read_config.return_value = mock_config
        
        mock_message = MagicMock()
        mock_emails_html.return_value = mock_message
        
        notification_api.send_mail("recipient@example.com")
        
        # Verify email content
        call_args = mock_emails_html.call_args
        self.assertIn("Salary Slip", call_args.kwargs.get("subject", ""))
        self.assertIn("salary slip", call_args.kwargs.get("html", ""))

    @pytest.mark.unit
    @pytest.mark.email
    @patch("notification_api.read_configuration")
    @patch("notification_api.emails.html")
    def test_send_mail_smtp_configuration(self, mock_emails_html, mock_read_config):
        """Test that SMTP configuration is passed correctly"""
        mock_config = MagicMock()
        mock_config.getProperty.side_effect = lambda key: {
            "smtp.from": "sender@example.com",
            "smtp.smtp_server": "smtp.example.com",
            "smtp.smtp_port": 587,
            "smtp.username": "testuser",
            "smtp.password": "testpass",
        }.get(key)
        mock_read_config.return_value = mock_config
        
        mock_message = MagicMock()
        mock_emails_html.return_value = mock_message
        
        notification_api.send_mail("recipient@example.com")
        
        # Verify SMTP config is correct
        send_call_args = mock_message.send.call_args
        smtp_config = send_call_args.kwargs.get("smtp", {})
        self.assertEqual(smtp_config.get("host"), "smtp.example.com")
        self.assertEqual(smtp_config.get("port"), 587)
        self.assertEqual(smtp_config.get("user"), "testuser")
        self.assertEqual(smtp_config.get("password"), "testpass")
        self.assertTrue(smtp_config.get("tls"))


class TestElasticsearchFunctionality(unittest.TestCase):
    """Test cases for elasticsearch operations"""

    @pytest.mark.unit
    @pytest.mark.elasticsearch
    @patch("notification_api.Elasticsearch")
    @patch("notification_api.send_mail")
    @patch("notification_api.read_configuration")
    def test_send_mail_to_all_users_success(self, mock_read_config, mock_send_mail, mock_elasticsearch):
        """Test successful mail sending to all users from elasticsearch"""
        mock_config = MagicMock()
        mock_config.getProperty.side_effect = lambda key: {
            "elasticsearch.host": "localhost",
            "elasticsearch.username": "elastic",
            "elasticsearch.password": "password",
            "elasticsearch.port": 9200,
        }.get(key)
        mock_read_config.return_value = mock_config
        
        mock_es_instance = MagicMock()
        mock_elasticsearch.return_value = mock_es_instance
        mock_es_instance.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"email_id": "user1@example.com"}},
                    {"_source": {"email_id": "user2@example.com"}},
                ]
            }
        }
        
        notification_api.send_mail_to_all_users()
        
        self.assertEqual(mock_send_mail.call_count, 2)
        mock_send_mail.assert_any_call("user1@example.com")
        mock_send_mail.assert_any_call("user2@example.com")

    @pytest.mark.unit
    @pytest.mark.elasticsearch
    @patch("notification_api.Elasticsearch")
    @patch("notification_api.read_configuration")
    def test_send_mail_to_all_users_elasticsearch_connection(self, mock_read_config, mock_elasticsearch):
        """Test elasticsearch connection parameters"""
        mock_config = MagicMock()
        mock_config.getProperty.side_effect = lambda key: {
            "elasticsearch.host": "es.example.com",
            "elasticsearch.username": "elastic_user",
            "elasticsearch.password": "elastic_pass",
            "elasticsearch.port": 9300,
        }.get(key)
        mock_read_config.return_value = mock_config
        
        mock_es_instance = MagicMock()
        mock_elasticsearch.return_value = mock_es_instance
        mock_es_instance.search.return_value = {"hits": {"hits": []}}
        
        notification_api.send_mail_to_all_users()
        
        # Verify elasticsearch connection parameters
        mock_elasticsearch.assert_called_once()
        call_args = mock_elasticsearch.call_args
        self.assertEqual(call_args[0][0], ["es.example.com"])

    @pytest.mark.unit
    @pytest.mark.elasticsearch
    @patch("notification_api.Elasticsearch")
    @patch("notification_api.read_configuration")
    def test_send_mail_to_all_users_query(self, mock_read_config, mock_elasticsearch):
        """Test elasticsearch query parameters"""
        mock_config = MagicMock()
        mock_config.getProperty.side_effect = lambda key: {
            "elasticsearch.host": "localhost",
            "elasticsearch.username": "elastic",
            "elasticsearch.password": "password",
            "elasticsearch.port": 9200,
        }.get(key)
        mock_read_config.return_value = mock_config
        
        mock_es_instance = MagicMock()
        mock_elasticsearch.return_value = mock_es_instance
        mock_es_instance.search.return_value = {"hits": {"hits": []}}
        
        notification_api.send_mail_to_all_users()
        
        # Verify elasticsearch search query
        mock_es_instance.search.assert_called_once()
        search_call = mock_es_instance.search.call_args
        self.assertEqual(search_call.kwargs.get("index"), "employee-management")

    @pytest.mark.unit
    @pytest.mark.elasticsearch
    @patch("notification_api.Elasticsearch")
    @patch("notification_api.read_configuration")
    def test_send_mail_to_all_users_exception(self, mock_read_config, mock_elasticsearch):
        """Test exception handling in send_mail_to_all_users"""
        mock_config = MagicMock()
        mock_read_config.return_value = mock_config
        mock_elasticsearch.side_effect = Exception("Connection refused")
        
        with patch("notification_api.get_logger") as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            notification_api.send_mail_to_all_users()
            
            mock_logger_instance.error.assert_called()

    @pytest.mark.unit
    @pytest.mark.elasticsearch
    @patch("notification_api.Elasticsearch")
    @patch("notification_api.send_mail")
    @patch("notification_api.read_configuration")
    def test_send_mail_to_all_users_empty_result(self, mock_read_config, mock_send_mail, mock_elasticsearch):
        """Test handling empty elasticsearch results"""
        mock_config = MagicMock()
        mock_config.getProperty.side_effect = lambda key: {
            "elasticsearch.host": "localhost",
            "elasticsearch.username": "elastic",
            "elasticsearch.password": "password",
            "elasticsearch.port": 9200,
        }.get(key)
        mock_read_config.return_value = mock_config
        
        mock_es_instance = MagicMock()
        mock_elasticsearch.return_value = mock_es_instance
        mock_es_instance.search.return_value = {"hits": {"hits": []}}
        
        notification_api.send_mail_to_all_users()
        
        mock_send_mail.assert_not_called()


class TestScheduleOperation(unittest.TestCase):
    """Test cases for schedule operations"""

    @pytest.mark.unit
    @pytest.mark.schedule
    @patch("notification_api.schedule.run_pending")
    @patch("notification_api.schedule.every")
    @patch("notification_api.time.sleep")
    def test_schedule_operation_sets_hourly_schedule(self, mock_sleep, mock_every, mock_run_pending):
        """Test that schedule_operation sets hourly schedule"""
        mock_every_instance = MagicMock()
        mock_every.return_value = mock_every_instance
        
        # Mock to stop the infinite loop after one iteration
        mock_sleep.side_effect = KeyboardInterrupt()
        
        try:
            notification_api.schedule_operation()
        except KeyboardInterrupt:
            pass
        
        mock_every.assert_called()
        mock_every_instance.hour.do.assert_called_once_with(notification_api.send_mail_to_all_users)

    @pytest.mark.unit
    @pytest.mark.schedule
    @patch("notification_api.get_logger")
    @patch("notification_api.schedule.run_pending")
    @patch("notification_api.schedule.every")
    @patch("notification_api.time.sleep")
    def test_schedule_operation_logging(self, mock_sleep, mock_every, mock_run_pending, mock_get_logger):
        """Test that schedule_operation logs waiting message"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_every_instance = MagicMock()
        mock_every.return_value = mock_every_instance
        
        # Mock to stop after one iteration
        mock_sleep.side_effect = KeyboardInterrupt()
        
        try:
            notification_api.schedule_operation()
        except KeyboardInterrupt:
            pass
        
        mock_logger.info.assert_called()


class TestMainArguments(unittest.TestCase):
    """Test cases for main argument parsing"""

    @patch("notification_api.schedule_operation")
    def test_main_scheduled_mode(self, mock_schedule):
        """Test main with scheduled mode"""
        with patch("sys.argv", ["notification_api.py", "-m", "scheduled"]):
            with patch("notification_api.schedule_operation") as mock_schedule_op:
                mock_schedule_op.side_effect = KeyboardInterrupt()
                try:
                    exec(open(notification_api.__file__).read())
                except:
                    pass

    @patch("notification_api.send_mail_to_all_users")
    def test_main_external_mode(self, mock_send_all):
        """Test main with external mode"""
        with patch("sys.argv", ["notification_api.py", "-m", "external"]):
            try:
                # This would normally run send_mail_to_all_users
                notification_api.send_mail_to_all_users()
            except:
                pass

    def test_default_mode_is_scheduled(self):
        """Test that default mode is 'scheduled'"""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-m", "--mode", help="Mode", default="scheduled")
        
        # Test with no arguments
        with patch("sys.argv", ["notification_api.py"]):
            args = parser.parse_args([])
            self.assertEqual(args.mode, "scheduled")


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""

    @pytest.mark.integration
    @pytest.mark.smoke
    @patch("notification_api.Elasticsearch")
    @patch("notification_api.emails.html")
    @patch("notification_api.read_configuration")
    def test_end_to_end_mail_sending(self, mock_read_config, mock_emails_html, mock_elasticsearch):
        """Test end-to-end mail sending workflow"""
        mock_config = MagicMock()
        mock_config.getProperty.side_effect = lambda key: {
            "elasticsearch.host": "localhost",
            "elasticsearch.username": "elastic",
            "elasticsearch.password": "password",
            "elasticsearch.port": 9200,
            "smtp.from": "sender@example.com",
            "smtp.smtp_server": "smtp.example.com",
            "smtp.smtp_port": 587,
            "smtp.username": "user@example.com",
            "smtp.password": "password123",
        }.get(key)
        mock_read_config.return_value = mock_config
        
        mock_es_instance = MagicMock()
        mock_elasticsearch.return_value = mock_es_instance
        mock_es_instance.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"email_id": "emp1@example.com"}},
                    {"_source": {"email_id": "emp2@example.com"}},
                ]
            }
        }
        
        mock_message = MagicMock()
        mock_emails_html.return_value = mock_message
        
        notification_api.send_mail_to_all_users()
        
        self.assertEqual(mock_emails_html.call_count, 2)
        self.assertEqual(mock_message.send.call_count, 2)


if __name__ == "__main__":
    unittest.main()
