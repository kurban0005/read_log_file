import pytest
import json
from collections import defaultdict
from datetime import datetime
from main import parse_logs, AverageResponseTimeReport, UserAgentReport


@pytest.fixture
def test_log_data(tmp_path):
    """Создает временные файлы с тестовыми логами."""
    log_data = [
        {"@timestamp": "2025-06-22T12:00:00", "url": "/api/v1/resource", "response_time": 200,
         "http_user_agent": "Mozilla/5.0"},
        {"@timestamp": "2025-06-22T12:05:00", "url": "/api/v1/resource", "response_time": 300,
         "http_user_agent": "Mozilla/5.0"},
    ]

    log_file = tmp_path / "test_logs.json"
    with open(log_file, 'w') as f:
        for entry in log_data:
            f.write(json.dumps(entry) + "\n")
    return log_file


def test_parse_logs(test_log_data):
    """Тестирование функции parse_logs без фильтрации по дате."""
    expected_stats = defaultdict(lambda: {'count': 0, 'total_response_time': 0})
    expected_stats["/api/v1/resource"]['count'] = 2
    expected_stats["/api/v1/resource"]['total_response_time'] = 500  # 200 + 300

    actual_stats, _ = parse_logs([str(test_log_data)])
    assert dict(actual_stats) == dict(expected_stats)


def test_parse_logs_with_date_filter(test_log_data):
    """Тестирование функции parse_logs с фильтрацией по дате."""
    expected_stats = defaultdict(lambda: {'count': 0, 'total_response_time': 0})
    expected_stats["/api/v1/resource"]['count'] = 2
    expected_stats["/api/v1/resource"]['total_response_time'] = 500  # 200 + 300 (only from 2025-06-22)

    report_date = datetime.strptime('2025-06-22', '%Y-%m-%d').date()
    actual_stats, _ = parse_logs([str(test_log_data)], report_date)
    assert dict(actual_stats) == dict(expected_stats)


def test_average_response_time_report():
    """Тестирование класса AverageResponseTimeReport."""
    endpoint_stats = {
        "/api/v1/resource": {'count': 2, 'total_response_time': 500},
        "/api/v1/another_resource": {'count': 1, 'total_response_time': 400},
    }

    report = AverageResponseTimeReport(title="Average Response Time Report")
    report_data, title = report.generate(endpoint_stats)

    expected_report_data = [
        ("/api/v1/resource", 2, 250.0),  # 500 / 2
        ("/api/v1/another_resource", 1, 400.0),  # 400 / 1
    ]
    assert report_data == expected_report_data
    assert title == "Average Response Time Report"  # Проверка заголовка


def test_user_agent_report():
    """Тестирование класса UserAgentReport."""
    logs = [
        {"@timestamp": "2025-06-22T12:00:00", "url": "/api/v1/resource", "response_time": 200,
         "http_user_agent": "Mozilla/5.0"},
        {"@timestamp": "2025-06-22T12:05:00", "url": "/api/v1/resource", "response_time": 300,
         "http_user_agent": "Mozilla/5.0"},
        {"@timestamp": "2025-06-22T12:10:00", "url": "/api/v1/another_resource", "response_time": 400,
         "http_user_agent": "Chrome/91.0"},
        {"@timestamp": "2025-06-23T12:15:00", "url": "/api/v1/resource", "response_time": 250,
         "http_user_agent": "Firefox/89.0"},
    ]

    report = UserAgentReport(title="User Agent Report")
    report_data, title = report.generate(logs)

    expected_report_data = [
        ("Mozilla/5.0", 2),
        ("Chrome/91.0", 1),
        ("Firefox/89.0", 1),
    ]
    assert sorted(report_data) == sorted(expected_report_data)  # Сравнение без учета порядка
    assert title == "User Agent Report"  # Проверка заголовка


if __name__ == '__main__':
    pytest.main()
