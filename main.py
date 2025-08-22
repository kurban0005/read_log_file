import argparse
import json
from collections import defaultdict
from datetime import datetime
from tabulate import tabulate


class Report:
    """Базовый класс для отчетов."""

    def __init__(self, title):
        """
        Инициализация отчета с заданным заголовком.

        :param title: Заголовок отчета.
        """
        self.title = title

    def generate(self, endpoint_stats):
        """
        Метод, который должен быть реализован в подклассах для генерации отчета.

        :param endpoint_stats: Статистика конечных точек, на основе которых будет сформирован отчет.
        :raises NotImplementedError: Если метод не переопределен в подклассе.
        """
        raise NotImplementedError("Subclasses should implement this!")


class AverageResponseTimeReport(Report):
    """Класс для генерации отчета о среднем времени ответа по конечным точкам API."""

    def generate(self, endpoint_stats):
        """
        Генерация отчета о среднем времени ответа.

        :param endpoint_stats: Статистика конечных точек (количество запросов и общее время ответа).
        :return: Данные отчета и заголовок.
        """
        report_data = []  # список с отчетами
        for endpoint, stats in endpoint_stats.items():
            average_response_time = stats['total_response_time'] / stats['count'] if stats['count'] > 0 else 0
            report_data.append((endpoint, stats['count'], average_response_time))
        return report_data, self.title


class UserAgentReport(Report):
    """Класс для генерации отчета о статистике User-Agent."""

    def generate(self, logs):
        """
        Генерация отчета по User-Agent.

        :param logs: Логи запросов, содержащие информацию о User-Agent.
        :return: Данные отчета и заголовок.
        """
        user_agent_stats = defaultdict(int)

        for log_entry in logs:
            user_agent = log_entry.get('http_user_agent', 'Unknown')
            user_agent_stats[user_agent] += 1

        report_data = [(ua, count) for ua, count in user_agent_stats.items()]
        return report_data, self.title


def parse_logs(file_paths, report_date=None):
    """
    Парсинг логов из указанных файлов.

    :param file_paths: Список путей к файлам логов.
    :param report_date: Дата для фильтрации логов (опционально).
    :return: Статистика конечных точек и список записей логов.
    """
    logs = []  # Список для хранения записей логов
    endpoint_stats = defaultdict(lambda: {'count': 0, 'total_response_time': 0})

    for file_path in file_paths:
        with open(file_path, 'r') as f:
            for line in f:
                log_entry = json.loads(line)  # Загружаем запись лога из JSON
                logs.append(log_entry)  # Сохраняем запись для дальнейшего использования

                # Предполагаем, что в записи лога есть поле '@timestamp'
                log_date = datetime.fromisoformat(log_entry['@timestamp']).date() if '@timestamp' in log_entry else None

                # Если указана дата, включаем только логи с этой датой
                if report_date and log_date != report_date:
                    continue

                endpoint = log_entry.get('url')
                response_time = log_entry.get('response_time')

                # Если есть конечная точка и время ответа, обновляем статистику
                if endpoint and response_time is not None:
                    endpoint_stats[endpoint]['count'] += 1
                    endpoint_stats[endpoint]['total_response_time'] += response_time

    return endpoint_stats, logs


def main():
    """Главная функция для обработки аргументов командной строки и генерации отчета."""
    parser = argparse.ArgumentParser(description="Process log files and generate report.")
    parser.add_argument('--files', type=str, nargs='+', required=True, help='Paths to the log files')
    parser.add_argument('--report', type=str, required=True, help='Type of report to generate')
    parser.add_argument('--date', type=str, required=False, help='Date to filter logs (YYYY-MM-DD)')

    # Парсим аргументы командной строки
    args = parser.parse_args()
    # Преобразуем аргумент даты, если он указан
    report_date = datetime.strptime(args.date, '%Y-%m-%d').date() if args.date else None
    # Парсим логи и собираем статистику
    endpoint_stats, logs = parse_logs(args.files, report_date)

    # Определяем тип отчета
    if args.report == 'average':
        report = AverageResponseTimeReport(title="Average Response Time Report")
    elif args.report == 'user-agent':
        report = UserAgentReport(title="User Agent Report")
    else:
        print("Currently, only 'average' and 'user-agent' report types are supported.")
        return

    # Генерируем данные отчета и заголовок
    report_data, title = report.generate(endpoint_stats if isinstance(report, AverageResponseTimeReport) else logs)

    # Выводим заголовок отчета
    print(title)
    print("=" * len(title))

    # Форматируем и выводим отчет
    if isinstance(report, AverageResponseTimeReport):

        print(tabulate(report_data, headers=['Endpoint', 'Request Count', 'Average Response Time'], tablefmt='pretty'))
    else:
        print(tabulate(report_data, headers=['User-Agent', 'Count'], tablefmt='pretty'))


if __name__ == '__main__':
    main()
