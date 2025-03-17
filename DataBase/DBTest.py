import unittest
import sqlite3
from Database import Database  # Assuming Database.py is in the same directory

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Set up a temporary database for testing."""
        self.db = Database(':memory:')  # Use in-memory database for testing
    
    def tearDown(self):
        """Close database connection after each test."""
        self.db.close_connection()

    def test_create_tables(self):
        """Ensure that tables are created successfully."""
        tables = ['stores', 'employees', 'parts']
        for table in tables:
            self.db.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            self.assertIsNotNone(self.db.cursor.fetchone())
    
    def test_add_store(self):
        """Test adding a store to the database."""
        self.db.add_store('Test Store', 100.0)
        self.db.cursor.execute("SELECT * FROM stores WHERE store_name = ?", ('Test Store',))
        store = self.db.cursor.fetchone()
        self.assertIsNotNone(store)
        self.assertEqual(store[1], 'Test Store')  # store_name
        self.assertEqual(store[2], 100.0)  # balance
    
    def test_add_employee(self):
        """Test adding an employee."""
        self.db.add_store('Test Store')
        self.db.cursor.execute("SELECT store_id FROM stores WHERE store_name = ?", ('Test Store',))
        store_id = self.db.cursor.fetchone()[0]
        
        self.db.add_employee('John', 'Doe', 'Manager', store_id)
        self.db.cursor.execute("SELECT * FROM employees WHERE first_name = ?", ('John',))
        employee = self.db.cursor.fetchone()
        self.assertIsNotNone(employee)
        self.assertEqual(employee[1], 'John')
        self.assertEqual(employee[2], 'Doe')
        self.assertEqual(employee[3], 'Manager')
        self.assertEqual(employee[4], store_id)
    
    def test_add_part_to_store(self):
        """Test adding a part to a store."""
        self.db.add_store('Test Store')
        self.db.cursor.execute("SELECT store_id FROM stores WHERE store_name = ?", ('Test Store',))
        store_id = self.db.cursor.fetchone()[0]
        
        pno = self.db.add_part_to_store('Widget', 10.5, store_id, 50)
        self.db.cursor.execute("SELECT * FROM parts WHERE pno = ?", (pno,))
        part = self.db.cursor.fetchone()
        self.assertIsNotNone(part)
        self.assertEqual(part[1], 'Widget')  # name
        self.assertEqual(part[2], 10.5)  # price
        self.assertEqual(part[3], store_id)  # store_id
        self.assertEqual(part[4], 50)  # quantity
    
    def test_purchase_part(self):
        """Test purchasing a part and updating store balance."""
        self.db.add_store('Test Store', 200.0)
        self.db.cursor.execute("SELECT store_id FROM stores WHERE store_name = ?", ('Test Store',))
        store_id = self.db.cursor.fetchone()[0]
        
        self.db.add_part_to_store('Widget', 10.0, store_id, 10)
        self.db.purchase_part('Widget', store_id, 5)
        
        self.db.cursor.execute("SELECT quantity FROM parts WHERE name = ? AND store_id = ?", ('Widget', store_id))
        new_quantity = self.db.cursor.fetchone()[0]
        self.assertEqual(new_quantity, 5)
        
        self.db.cursor.execute("SELECT balance FROM stores WHERE store_id = ?", (store_id,))
        new_balance = self.db.cursor.fetchone()[0]
        self.assertEqual(new_balance, 250.0)  # 200 + (5 * 10)
    
    def test_return_part(self):
        """Test returning a part and updating store balance."""
        self.db.add_store('Test Store', 500.0)
        self.db.cursor.execute("SELECT store_id FROM stores WHERE store_name = ?", ('Test Store',))
        store_id = self.db.cursor.fetchone()[0]
        
        self.db.add_part_to_store('Widget', 20.0, store_id, 5)
        self.db.return_part('Widget', store_id, 2)
        
        self.db.cursor.execute("SELECT quantity FROM parts WHERE name = ? AND store_id = ?", ('Widget', store_id))
        new_quantity = self.db.cursor.fetchone()[0]
        self.assertEqual(new_quantity, 7)
        
        self.db.cursor.execute("SELECT balance FROM stores WHERE store_id = ?", (store_id,))
        new_balance = self.db.cursor.fetchone()[0]
        self.assertEqual(new_balance, 460.0)  # 500 - (2 * 20)
    
    def test_get_stores(self):
        """Test retrieving all stores."""
        self.db.add_store('Store 1')
        self.db.add_store('Store 2')
        stores = self.db.get_stores()
        self.assertEqual(len(stores), 2)
        self.assertEqual(stores[0][1], 'Store 1')
        self.assertEqual(stores[1][1], 'Store 2')
    
    def test_get_employees(self):
        """Test retrieving all employees."""
        self.db.add_store('Test Store')
        self.db.cursor.execute("SELECT store_id FROM stores WHERE store_name = ?", ('Test Store',))
        store_id = self.db.cursor.fetchone()[0]
        
        self.db.add_employee('Alice', 'Smith', 'Clerk', store_id)
        self.db.add_employee('Bob', 'Johnson', 'Technician', store_id)
        employees = self.db.get_employees()
        self.assertEqual(len(employees), 2)
        self.assertEqual(employees[0][1], 'Alice')
        self.assertEqual(employees[1][1], 'Bob')
    
if __name__ == '__main__':
    unittest.main()
