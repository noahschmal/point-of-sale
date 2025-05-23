import unittest
from Database import Database, TransactionDetails, PartSold  # Assuming Database.py is in the same directory

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Set up a temporary database for testing."""
        self.db = Database(':memory:')  # Use in-memory database for testing
        self.db.create_tables()  # Ensure tables are created for each test
    
    def tearDown(self):
        """Close database connection after each test."""
        self.db.close_connection()

    def test_create_tables(self):
        """Ensure that tables are created successfully."""
        tables = ['stores', 'employees', 'parts', 'transactions', 'transaction_details']
        missing_tables = []

        for table in tables:
            # Check if the table exists in the database
            self.db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not self.db.cursor.fetchone():
                missing_tables.append(table)

        # If any tables are missing, fail the test and print the missing tables
        if missing_tables:
            self.fail(f"The following tables were not created: {', '.join(missing_tables)}")

    def test_add_store(self):
        """Test adding a store to the database."""
        self.db.add_store('Test Store', 100.0)
        stores = self.db.get_stores()
        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0][1], 'Test Store')  # store_name
        self.assertEqual(stores[0][2], 100.0)  # balance

    def test_add_employee(self):
        """Test adding an employee."""
        self.db.add_store('Test Store')
        store_id = self.db.get_stores()[0][0]
        
        self.db.add_employee('John', 'Doe', 'Manager', store_id, "password")
        employees = self.db.get_employees()
        self.assertEqual(len(employees), 1)
        self.assertEqual(employees[0][1], 'John')
        self.assertEqual(employees[0][2], 'Doe')
        self.assertEqual(employees[0][3], 'Manager')
        self.assertEqual(employees[0][4], store_id)

    def test_add_part_to_store(self):
        """Test adding a part to a store."""
        self.db.add_store('Test Store')
        store_id = self.db.get_stores()[0][0]
        
        pno = self.db.add_part_to_store('Widget', 10.5, store_id, 50)
        parts = self.db.get_parts_by_store(store_id)  # Use get_parts_by_store
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0].name, 'Widget')  # name
        self.assertEqual(parts[0].price, 10.5)  # price
        self.assertEqual(parts[0].store_id, store_id)  # store_id
        self.assertEqual(parts[0].quantity, 50)  # quantity

    def test_purchase_part(self):
        """Test purchasing a part and updating store balance."""
        self.db.add_store('Test Store', 200.0)
        store_id = self.db.get_stores()[0][0]
        
        self.db.add_part_to_store('Widget', 10.0, store_id, 10)
        self.db.purchase_part('Widget', store_id, 5)
        
        parts = self.db.get_parts_by_store(store_id)  # Use get_parts_by_store
        self.assertEqual(parts[0].quantity, 5)  # New quantity
        
        stores = self.db.get_stores()
        self.assertEqual(stores[0][2], 250.0)  # New balance

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
        store_id = self.db.get_stores()[0][0]
        
        self.db.add_employee('Alice', 'Smith', 'Clerk', store_id, "password")
        self.db.add_employee('Bob', 'Johnson', 'Technician', store_id, "password")
        employees = self.db.get_employees()
        self.assertEqual(len(employees), 2)
        self.assertEqual(employees[0][1], 'Alice')
        self.assertEqual(employees[1][1], 'Bob')

    def test_get_parts(self):
        """Test retrieving all parts for a specific store."""
        self.db.add_store('Test Store')
        store_id = self.db.get_stores()[0][0]
        
        self.db.add_part_to_store('Widget', 10.0, store_id, 10)
        self.db.add_part_to_store('Gadget', 15.0, store_id, 5)
        parts = self.db.get_parts_by_store(store_id)  # Use get_parts_by_store
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0].name, 'Widget')
        self.assertEqual(parts[1].name, 'Gadget')

    def test_sales_report(self):
        """Test generating a sales report for a store."""
        self.db.add_store('Test Store')
        store_id = self.db.get_stores()[0][0]

        self.db.add_employee('Alice', 'Smith', 'Clerk', store_id, "password")
        employee_id = self.db.get_employees()[0][0]

        part1_id = self.db.add_part_to_store('Widget', 10.0, store_id, 10)
        part2_id = self.db.add_part_to_store('Gadget', 15.0, store_id, 5)

        # Create a purchase transaction
        parts_to_purchase = [
            PartSold(name='Widget', quantity=3, unit_price=10.0, total_price=30.0),
            PartSold(name='Gadget', quantity=2, unit_price=15.0, total_price=30.0)
        ]
        transaction_id = self.db.create_purchase(parts_to_purchase, store_id)

        # Generate the sales report
        report = self.db.SalesReport(store_id)

        # Assertions
        self.assertEqual(len(report), 1)  # Only one transaction
        self.assertEqual(report[0].total_price, 60.0)  # Total price of the transaction
        self.assertEqual(len(report[0].parts_sold), 2)

        # Verify transaction details
        self.assertEqual(report[0].parts_sold[0].name, 'Widget')
        self.assertEqual(report[0].parts_sold[0].quantity, 3)
        self.assertEqual(report[0].parts_sold[0].unit_price, 10.0)
        self.assertEqual(report[0].parts_sold[0].total_price, 30.0)

        self.assertEqual(report[0].parts_sold[1].name, 'Gadget')
        self.assertEqual(report[0].parts_sold[1].quantity, 2)
        self.assertEqual(report[0].parts_sold[1].unit_price, 15.0)
        self.assertEqual(report[0].parts_sold[1].total_price, 30.0)

    def test_employee_login(self):
        """Test employee login functionality."""
        self.db.add_store('Test Store')
        store_id = self.db.get_stores()[0][0]

        self.db.add_employee('Alice', 'Smith', 'Clerk', store_id, "securepassword")

        # Successful login
        role, emp_id = self.db.employee_login('Alice', 'Smith', 'securepassword')
        self.assertEqual(role, 'Clerk')
        self.assertIsNotNone(emp_id)

        # Incorrect password
        with self.assertRaises(Exception) as context:
            self.db.employee_login('Alice', 'Smith', 'wrongpassword')
        self.assertEqual(str(context.exception), "Incorrect password.")

        # Non-existent employee
        with self.assertRaises(Exception) as context:
            self.db.employee_login('NonExistent', 'User', 'password')
        self.assertEqual(str(context.exception), "Employee not found.")

    def test_get_transaction_details(self):
        """Test retrieving all details of a specific transaction."""
        # Add a store
        self.db.add_store('Test Store')
        store_id = self.db.get_stores()[0][0]

        # Add an employee
        self.db.add_employee('Alice', 'Smith', 'Clerk', store_id, "password")
        employee_id = self.db.get_employees()[0][0]

        # Add parts to the store
        part1_id = self.db.add_part_to_store('Widget', 10.0, store_id, 10)
        part2_id = self.db.add_part_to_store('Gadget', 15.0, store_id, 5)

        # Create a purchase transaction
        parts_to_purchase = [
            PartSold(name='Widget', quantity=3, unit_price=10.0, total_price=30.0),
            PartSold(name='Gadget', quantity=2, unit_price=15.0, total_price=30.0)
        ]
        transaction_id = self.db.create_purchase(parts_to_purchase, store_id)

        # Retrieve transaction details
        transaction_details = self.db.get_transaction_details(transaction_id)

        # Debug: Print transaction details
        print("Transaction Details:", transaction_details)

        # Assertions
        expected_total_price = (3 * 10.0) + (2 * 15.0)  # Widget: 3 * 10, Gadget: 2 * 15
        self.assertEqual(transaction_details.total_price, expected_total_price)
        self.assertEqual(len(transaction_details.parts_sold), 2)

        # Check part details
        self.assertEqual(transaction_details.parts_sold[0].name, 'Widget')
        self.assertEqual(transaction_details.parts_sold[0].quantity, 3)
        self.assertEqual(transaction_details.parts_sold[0].unit_price, 10.0)
        self.assertEqual(transaction_details.parts_sold[0].total_price, 30.0)

        self.assertEqual(transaction_details.parts_sold[1].name, 'Gadget')
        self.assertEqual(transaction_details.parts_sold[1].quantity, 2)
        self.assertEqual(transaction_details.parts_sold[1].unit_price, 15.0)
        self.assertEqual(transaction_details.parts_sold[1].total_price, 30.0)

    def test_return_part(self):
        """Test returning parts and updating store balance."""
        # Step 1: Add a store and admin employee
        self.db.add_store('Test Store', 500.0)
        store_id = self.db.get_stores()[0][0]
        self.db.add_employee('Test', 'Admin', 'Admin', store_id, 'password')
        admin_id = self.db.get_employees()[0][0]

        # Step 2: Add parts to the store
        self.db.add_part_to_store('Widget', 20.0, store_id, 5)
        self.db.add_part_to_store('Gadget', 15.0, store_id, 5)

        # Step 3: Return parts
        self.db.return_part('Widget', store_id, 2, admin_id)  # Return 2 units of Widget
        self.db.return_part('Gadget', store_id, 1, admin_id)  # Return 1 unit of Gadget

        # Step 4: Verify updated quantities in the `parts` table
        parts = self.db.get_parts_by_store(store_id)  # Use get_parts_by_store
        self.assertEqual(len(parts), 2)  # Ensure two parts exist
        self.assertEqual(parts[0].name, 'Widget')  # Part name
        self.assertEqual(parts[0].quantity, 7)  # Widget: Original 5 + Returned 2
        self.assertEqual(parts[1].name, 'Gadget')  # Part name
        self.assertEqual(parts[1].quantity, 6)  # Gadget: Original 5 + Returned 1

        # Step 5: Verify updated store balance
        stores = self.db.get_stores()
        self.assertEqual(len(stores), 1)  # Ensure one store exists
        self.assertEqual(stores[0][2], 445.0)  # Original 500 - Refund (40 + 15)

        print("test_return_part passed successfully.")

    def test_return_from_transaction(self):
        """Test returning items from a specific transaction."""
        # Step 1: Add a store and employees
        self.db.add_store('Test Store', 500.0)
        store_id = self.db.get_stores()[0][0]
        self.db.add_employee('Test', 'Admin', 'Admin', store_id, 'password')
        admin_id = self.db.get_employees()[0][0]

        # Step 2: Add parts to the store
        part1_id = self.db.add_part_to_store('Widget', 20.0, store_id, 10)
        part2_id = self.db.add_part_to_store('Gadget', 15.0, store_id, 8)

        # Step 3: Create a purchase transaction
        parts_to_purchase = [
            PartSold(name='Widget', quantity=3, unit_price=20.0, total_price=60.0),
            PartSold(name='Gadget', quantity=2, unit_price=15.0, total_price=30.0)
        ]
        transaction_id = self.db.create_purchase(parts_to_purchase, store_id)

        # Step 4: Verify initial state after purchase
        parts = self.db.get_parts_by_store(store_id)
        self.assertEqual(parts[0].quantity, 7)  # Widget: 10 - 3
        self.assertEqual(parts[1].quantity, 6)  # Gadget: 8 - 2
        stores = self.db.get_stores()
        self.assertEqual(stores[0][2], 590.0)  # Initial 500 + Purchase (60 + 30)

        # Step 5: Process return by transaction ID
        return_transaction_id = self.db.return_by_transaction_id(transaction_id, admin_id)
        self.assertIsNotNone(return_transaction_id)

        # Step 6: Verify final state after return
        parts = self.db.get_parts_by_store(store_id)
        self.assertEqual(parts[0].quantity, 10)  # Widget: 7 + 3
        self.assertEqual(parts[1].quantity, 8)   # Gadget: 6 + 2

        stores = self.db.get_stores()
        self.assertEqual(stores[0][2], 500.0)  # Back to initial balance

        # Step 7: Verify return transaction details
        return_details = self.db.get_transaction_details(return_transaction_id)
        self.assertEqual(return_details.total_price, -90.0)  # Negative total for return
        self.assertEqual(len(return_details.parts_sold), 2)

        # Verify Widget return details
        self.assertEqual(return_details.parts_sold[0].name, 'Widget')
        self.assertEqual(return_details.parts_sold[0].quantity, -3)  # Negative quantity for returns
        self.assertEqual(return_details.parts_sold[0].unit_price, 20.0)
        self.assertEqual(return_details.parts_sold[0].total_price, -60.0)

        # Verify Gadget return details
        self.assertEqual(return_details.parts_sold[1].name, 'Gadget')
        self.assertEqual(return_details.parts_sold[1].quantity, -2)  # Negative quantity for returns
        self.assertEqual(return_details.parts_sold[1].unit_price, 15.0)
        self.assertEqual(return_details.parts_sold[1].total_price, -30.0)

        print("test_return_from_transaction passed successfully.")

    def test_store_tax_rate(self):
        """Test tax rate calculations for store transactions."""
        # Step 1: Add a store with 8% tax rate and admin employee
        self.db.add_store('Test Store', 500.0, tax_rate=0.08)
        store_id = self.db.get_stores()[0][0]
        self.db.add_employee('Test', 'Admin', 'Admin', store_id, 'password')
        admin_id = self.db.get_employees()[0][0]

        # Step 2: Add parts to the store
        part1_id = self.db.add_part_to_store('Widget', 20.0, store_id, 10)
        part2_id = self.db.add_part_to_store('Gadget', 15.0, store_id, 8)

        # Step 3: Create a purchase transaction
        parts_to_purchase = [
            PartSold(name='Widget', quantity=3, unit_price=20.0, total_price=60.0),
            PartSold(name='Gadget', quantity=2, unit_price=15.0, total_price=30.0)
        ]
        transaction_id = self.db.create_purchase(parts_to_purchase, store_id)

        # Step 4: Verify purchase transaction with tax
        purchase_details = self.db.get_transaction_details(transaction_id)
        subtotal = 90.0  # (3 * 20.0) + (2 * 15.0)
        expected_tax = subtotal * 0.08
        expected_total = subtotal + expected_tax
        self.assertEqual(purchase_details.total_price, expected_total)

        # Step 5: Verify store balance after purchase with tax
        stores = self.db.get_stores()
        self.assertEqual(stores[0][2], 500.0 + expected_total)

        # Step 6: Process return by transaction ID
        return_transaction_id = self.db.return_by_transaction_id(transaction_id, admin_id)

        # Step 7: Verify return transaction with tax
        return_details = self.db.get_transaction_details(return_transaction_id)
        expected_return_total = -expected_total  # Negative total for returns
        self.assertEqual(return_details.total_price, expected_return_total)

        # Step 8: Verify store balance after return with tax
        stores = self.db.get_stores()
        self.assertEqual(stores[0][2], 500.0)  # Back to initial balance

        # Step 9: Verify part quantities after complete cycle
        parts = self.db.get_parts_by_store(store_id)
        self.assertEqual(parts[0].quantity, 10)  # Widget: Original quantity restored
        self.assertEqual(parts[1].quantity, 8)   # Gadget: Original quantity restored

        print("test_store_tax_rate passed successfully.")

    def test_transaction_with_discount(self):
        """Test applying discounts to transactions."""
        # Setup store and employee
        self.db.add_store('Test Store', 500.0, tax_rate=0.08)  # 8% tax rate
        store_id = self.db.get_stores()[0][0]
        self.db.add_employee('Test', 'Admin', 'Admin', store_id, 'password')
        admin_id = self.db.get_employees()[0][0]

        # Add parts to store
        self.db.add_part_to_store('Widget', 100.0, store_id, 10)  # $100 item
        self.db.add_part_to_store('Gadget', 50.0, store_id, 8)    # $50 item

        # Create purchase with 20% discount
        widget_price = 100.0 * 0.8  # Widget price after 20% discount
        gadget_price = 50.0 * 0.8   # Gadget price after 20% discount
        
        parts_to_purchase = [
            PartSold(name='Widget', quantity=1, unit_price=100.0, total_price=widget_price, discount_percent=0.20),
            PartSold(name='Gadget', quantity=2, unit_price=50.0, total_price=gadget_price * 2, discount_percent=0.20)
        ]
        transaction_id = self.db.create_purchase(parts_to_purchase, store_id, admin_id)

        # Verify transaction details
        transaction_details = self.db.get_transaction_details(transaction_id)
        
        # Calculate expected values
        subtotal = widget_price + (gadget_price * 2)  # Total after discounts
        tax_amount = subtotal * 0.08                  # Tax on discounted amount
        expected_total = subtotal + tax_amount        # Final total
        
        # Verify calculations
        self.assertEqual(transaction_details.total_price, expected_total)

        # Verify store balance
        stores = self.db.get_stores()
        self.assertEqual(stores[0][2], 500.0 + expected_total)

        # Verify inventory was updated
        parts = self.db.get_parts_by_store(store_id)
        self.assertEqual(parts[0].quantity, 9)   # Widget: 10 - 1
        self.assertEqual(parts[1].quantity, 6)   # Gadget: 8 - 2

    def test_return_logging(self):
        """Test that returns are properly logged in the returns table."""
        # Setup store and admin employee
        self.db.add_store('Test Store', 500.0, 0.08)  # 8% tax rate
        store_id = self.db.get_stores()[0][0]
        self.db.add_employee('Test', 'Admin', 'Admin', store_id, 'password')  # Changed to Admin
        admin_id = self.db.get_employees()[0][0]

        # Add parts to store
        self.db.add_part_to_store('Widget', 20.0, store_id, 10)
        self.db.add_part_to_store('Gadget', 15.0, store_id, 8)

        # Create initial purchase
        purchase_parts = [
            PartSold(name='Widget', quantity=3, unit_price=20.0, total_price=60.0),
            PartSold(name='Gadget', quantity=2, unit_price=15.0, total_price=30.0)
        ]
        transaction_id = self.db.create_purchase(purchase_parts, store_id, admin_id)

        # Process return by transaction ID with admin
        return_transaction_id = self.db.return_by_transaction_id(transaction_id, admin_id)

        # Get transaction log and verify return was recorded
        transactions = self.db.get_transaction_log(store_id)
        
        # Find the return transaction
        return_transaction = next(
            (t for t in transactions if t['transaction_id'] == return_transaction_id), 
            None
        )

        # Assert return transaction exists and has correct values
        self.assertIsNotNone(return_transaction, "Return transaction should exist in log")
        self.assertEqual(return_transaction['type'], 'Return')
        self.assertEqual(return_transaction['original_transaction_id'], transaction_id)
        
        # Verify refund amount includes tax (negative amount for returns)
        expected_refund = -(90.0 * 1.08)  # Original total with 8% tax
        self.assertAlmostEqual(return_transaction['total_price'], expected_refund, places=2)

        print("test_return_logging passed successfully.")

    def test_return_part_admin_only(self):
        """Test that only admin users can process returns."""
        # Setup store and employees
        self.db.add_store('Test Store', 500.0)
        store_id = self.db.get_stores()[0][0]
        
        # Create admin and regular employee
        self.db.add_employee('Admin', 'User', 'Admin', store_id, 'password')
        self.db.add_employee('Regular', 'User', 'Clerk', store_id, 'password')
        admin_id = self.db.get_employees()[0][0]
        clerk_id = self.db.get_employees()[1][0]

        # Add test part
        self.db.add_part_to_store('Widget', 20.0, store_id, 5)

        # Test admin can return parts
        try:
            self.db.return_part('Widget', store_id, 2, admin_id)
        except Exception as e:
            self.fail("Admin should be able to process returns")

        # Test clerk cannot return parts
        with self.assertRaises(Exception) as context:
            self.db.return_part('Widget', store_id, 1, clerk_id)
        self.assertEqual(str(context.exception), "Admin access required for returns")

    def test_return_by_transaction_admin_only(self):
        """Test that only admin users can process transaction returns."""
        # Setup store and employees
        self.db.add_store('Test Store', 500.0)
        store_id = self.db.get_stores()[0][0]
        
        # Create admin and regular employee
        self.db.add_employee('Admin', 'User', 'Admin', store_id, 'password')
        self.db.add_employee('Regular', 'User', 'Clerk', store_id, 'password')
        admin_id = self.db.get_employees()[0][0]
        clerk_id = self.db.get_employees()[1][0]

        # Add parts and create purchase
        self.db.add_part_to_store('Widget', 20.0, store_id, 10)
        parts_to_purchase = [
            PartSold(name='Widget', quantity=3, unit_price=20.0, total_price=60.0)
        ]
        transaction_id = self.db.create_purchase(parts_to_purchase, store_id)

        # Test admin can process return
        try:
            return_id = self.db.return_by_transaction_id(transaction_id, admin_id)
            self.assertIsNotNone(return_id)
        except Exception as e:
            self.fail("Admin should be able to process transaction returns")

        # Test clerk cannot process return
        with self.assertRaises(Exception) as context:
            self.db.return_by_transaction_id(transaction_id, clerk_id)
        self.assertEqual(str(context.exception), "Admin access required for returns")

if __name__ == '__main__':
    unittest.main()