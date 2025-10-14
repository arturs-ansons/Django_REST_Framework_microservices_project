from django.test import TestCase
from django.db import connection

class DatabaseConnectionTest(TestCase):
    """Simple test to verify SQLite DB connection."""

    def test_sqlite_connection(self):
        # Use Django's connection object to execute a simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        self.assertEqual(result[0], 1)
