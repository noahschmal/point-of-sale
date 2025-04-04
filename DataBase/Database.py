import sqlite3
import bcrypt
from dataclasses import dataclass
from typing import List

# all data structs used in the database
@dataclass
class PartSold:
    name: str
    quantity: int
    unit_price: float
    total_price: float


@dataclass
class TransactionDetails:
    transaction_id: int
    date: str
    total_price: float
    employee: str
    store: str
    parts_sold: List[PartSold]


@dataclass
class Part:
    part_id: int
    name: str
    price: float
    store_id: int
    quantity: int


class Database:
    def __init__(self, db_name):
        """
        Initializes the SQLite database and connects to it.
        If the database does not exist, it will be created.
        Also creates required tables if they do not exist.
        """
        self.db_name = db_name
        self.conn = self.connect()
        self.cursor = self.conn.cursor()
        self.create_tables()

    def connect(self):
        """Create a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_name)

        # Enabling foreign key support (SQLite foreign key constraints are disabled by default)
        conn.execute('PRAGMA foreign_keys = ON')
        print(f"Successfully connected to the database: {self.db_name}")
        return conn

    def create_tables(self):
        """Create tables if they don't already exist."""
        
        # Create employees table with store_id
        create_employee_table_query = """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL,
            store_id INTEGER,
            password_hash TEXT NOT NULL,
            FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE SET NULL
        );
        """
        
        # Create parts table with store_id and quantity
        create_parts_table_query = """
        CREATE TABLE IF NOT EXISTS parts (
            pno INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,  -- Enforce unique part names
            price REAL NOT NULL,
            store_id INTEGER,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE SET NULL
        );
        """
        
        # Create stores table
        create_stores_table_query = """
        CREATE TABLE IF NOT EXISTS stores (
            store_id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0.0
        );
        """
    
        # Create transactions table
        create_transactions_table_query = """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            total_price REAL NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
            FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
        );
        """
    
        # Create transaction_details table to store sold parts
        create_transaction_details_table_query = """
        CREATE TABLE IF NOT EXISTS transaction_details (
            transaction_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            part_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
            FOREIGN KEY (part_id) REFERENCES parts(pno) ON DELETE CASCADE
        );
        """
        # Trigger to update total_price in transactions table when a new transaction detail is added
        create_trigger_update_total_price = """
        CREATE TRIGGER IF NOT EXISTS update_total_price
        AFTER INSERT ON transaction_details
        FOR EACH ROW
        BEGIN
            UPDATE transactions
            SET total_price = (
                SELECT COALESCE(SUM(td.quantity * p.price), 0)
                FROM transaction_details td
                JOIN parts p ON td.part_id = p.pno
                WHERE td.transaction_id = NEW.transaction_id
            )
            WHERE transaction_id = NEW.transaction_id;
        END;
        """        
        try:
            # Execute all table creation queries
            self.cursor.execute(create_stores_table_query)  
            self.cursor.execute(create_employee_table_query)
            self.cursor.execute(create_parts_table_query)
            self.cursor.execute(create_transactions_table_query)
            self.cursor.execute(create_transaction_details_table_query)
            self.cursor.execute(create_trigger_update_total_price)
            self.conn.commit()
            print("Tables are ready.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    # Closes the connection to the database
    def close_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print(f"Connection to {self.db_name} closed.")


    # Add a new store
    def add_store(self, store_name, balance=0.0):
        try:
            query = "INSERT INTO stores (store_name, balance) VALUES (?, ?)"
            self.cursor.execute(query, (store_name, balance))
            self.conn.commit()
            print(f"Store '{store_name}' added successfully.")
        except sqlite3.Error as e:
            print(f"Error adding store: {e}")

    # Add a new employee
    def add_employee(self, first_name, last_name, role, store_id, password):
        """Create a new employee with a hashed password."""
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        query = """
        INSERT INTO employees (first_name, last_name, role, store_id, password_hash)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.cursor.execute(query, (first_name, last_name, role, store_id, hashed_pw))
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise Exception("Error creating employee. Possible duplicate or invalid data.")

    # Add a part to a store with a specified quantity and return the generated pno
    def add_part_to_store(self, name, price, store_id, quantity):
        """
        Add a part to a store with a specified quantity.

        Args:
            name (str): The name of the part.
            price (float): The price of the part.
            store_id (int): The ID of the store.
            quantity (int): The quantity of the part.

        Returns:
            int: The generated part number (pno) if successful, None otherwise.
        """
        try:
            self.cursor.execute("SELECT store_id FROM stores WHERE store_id = ?", (store_id,))
            if not self.cursor.fetchone():
                print(f"Error: Store ID {store_id} does not exist.")
                return None

            query = "INSERT INTO parts (name, price, store_id, quantity) VALUES (?, ?, ?, ?)"
            self.cursor.execute(query, (name, price, store_id, quantity))
            self.conn.commit()

            # Return the generated pno (part number)
            pno = self.cursor.lastrowid
            print(f"Part '{name}' added to store {store_id} with quantity {quantity}. Generated pno: {pno}")
            return pno
        except sqlite3.IntegrityError:
            print(f"Error: Part '{name}' already exists in store {store_id}.")
            return None
        except sqlite3.Error as e:
            print(f"Error adding part: {e}")
            return None

    # Resets the employee password 
    def set_employee_password(self, employee_id, password):
        """Hash and store the employee's password."""
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        query = "UPDATE employees SET password_hash = ? WHERE id = ?"
        self.cursor.execute(query, (hashed_pw, employee_id))
        self.conn.commit()

    # logs in for an employee and returns there role and id
    def employee_login(self, first_name, last_name, password) -> tuple[str, str]:
        """Verify employee login and return their role if successful."""
        query = "SELECT id, password_hash, role FROM employees WHERE first_name = ? AND last_name = ?"
        self.cursor.execute(query, (first_name, last_name))
        result = self.cursor.fetchone()

        if not result:
            raise Exception("Employee not found.")

        emp_id, hashed_pw, role = result

        if not bcrypt.checkpw(password.encode(), hashed_pw):
            raise Exception("Incorrect password.")

        return (role, emp_id)

    # Purchase parts: Decrease quantity of part in store and increase store's balance
    def purchase_part(self, name, store_id, quantity):
        try:
            # Check the current quantity of the part in the store by part name
            self.cursor.execute("SELECT pno, quantity, price FROM parts WHERE name = ? AND store_id = ?", (name, store_id))
            result = self.cursor.fetchone()
            
            if result:
                pno, current_quantity, part_price = result
                
                if current_quantity >= quantity:
                    new_quantity = current_quantity - quantity
                    total_price = part_price * quantity
                    
                    # Update the quantity of the part in the store
                    self.cursor.execute("UPDATE parts SET quantity = ? WHERE pno = ? AND store_id = ?", (new_quantity, pno, store_id))
                    
                    # Update the store's balance (increase by total price)
                    self.cursor.execute("UPDATE stores SET balance = balance + ? WHERE store_id = ?", (total_price, store_id))
                    
                    self.conn.commit()
                    print(f"Sold {quantity} of part '{name}' (pno: {pno}) for store {store_id}. Total amount: {total_price}. New quantity: {new_quantity}.")
                else:
                    print(f"Insufficient quantity of part '{name}' in store {store_id}. Available quantity: {current_quantity}.")
            else:
                print(f"Part '{name}' not found in store {store_id}.")
        except sqlite3.Error as e:
            print(f"Error purchasing part: {e}")

    # Return parts: Increase quantity of part in store and decrease store's balance
    def return_part(self, name, store_id, quantity):
        try:
            # Check the current quantity of the part in the store by part name
            self.cursor.execute("SELECT pno, quantity, price FROM parts WHERE name = ? AND store_id = ?", (name, store_id))
            result = self.cursor.fetchone()
            
            if result:
                pno, current_quantity, part_price = result
                
                # Increase the quantity of the part in the store
                new_quantity = current_quantity + quantity
                total_refund = part_price * quantity
                
                # Update the quantity of the part in the store
                self.cursor.execute("UPDATE parts SET quantity = ? WHERE pno = ? AND store_id = ?", (new_quantity, pno, store_id))
                
                # Update the store's balance (decrease by total refund amount)
                self.cursor.execute("UPDATE stores SET balance = balance - ? WHERE store_id = ?", (total_refund, store_id))
                
                self.conn.commit()
                print(f"Returned {quantity} of part '{name}' (pno: {pno}) for store {store_id}. Total refund: {total_refund}. New quantity: {new_quantity}.")
            else:
                print(f"Part '{name}' not found in store {store_id}.")
        except sqlite3.Error as e:
            print(f"Error returning part: {e}")

    # Purchase part by pno: Decrease quantity of part in store and increase store's balance
    def purchase_part_by_pno(self, pno, store_id, quantity):
        try:
            # Check the current quantity of the part in the store by pno
            self.cursor.execute("SELECT quantity, price FROM parts WHERE pno = ? AND store_id = ?", (pno, store_id))
            result = self.cursor.fetchone()
            
            if result:
                current_quantity, part_price = result
                
                if current_quantity >= quantity:
                    new_quantity = current_quantity - quantity
                    total_price = part_price * quantity
                    
                    # Create a transaction
                    self.cursor.execute(
                        "INSERT INTO transactions (employee_id, store_id, total_price) VALUES (?, ?, ?)",
                        (1, store_id, total_price)  # Replace `1` with the actual employee ID
                    )
                    transaction_id = self.cursor.lastrowid

                    # Add transaction details
                    self.cursor.execute(
                        "INSERT INTO transaction_details (transaction_id, part_id, quantity) VALUES (?, ?, ?)",
                        (transaction_id, pno, quantity)
                    )

                    # Update the quantity of the part in the store
                    self.cursor.execute("UPDATE parts SET quantity = ? WHERE pno = ? AND store_id = ?", (new_quantity, pno, store_id))
                    
                    # Update the store's balance (increase by total price)
                    self.cursor.execute("UPDATE stores SET balance = balance + ? WHERE store_id = ?", (total_price, store_id))
                    
                    self.conn.commit()
                    print(f"Sold {quantity} of part with pno {pno} for store {store_id}. Total amount: {total_price}. New quantity: {new_quantity}.")
                else:
                    print(f"Insufficient quantity of part with pno {pno} in store {store_id}. Available quantity: {current_quantity}.")
            else:
                print(f"Part with pno {pno} not found in store {store_id}.")
        except sqlite3.Error as e:
            print(f"Error purchasing part: {e}")

    # Return part by pno: Increase quantity of part in store and decrease store's balance
    def return_part_by_pno(self, pno, store_id, quantity):
        try:
            # Check the current quantity of the part in the store by pno
            self.cursor.execute("SELECT quantity, price FROM parts WHERE pno = ? AND store_id = ?", (pno, store_id))
            result = self.cursor.fetchone()
            
            if result:
                current_quantity, part_price = result
                
                # Increase the quantity of the part in the store
                new_quantity = current_quantity + quantity
                total_refund = part_price * quantity
                
                # Create a transaction
                self.cursor.execute(
                    "INSERT INTO transactions (employee_id, store_id, total_price) VALUES (?, ?, ?)",
                    (1, store_id, -total_refund)  # Replace `1` with the actual employee ID
                )
                transaction_id = self.cursor.lastrowid

                # Add transaction details
                self.cursor.execute(
                    "INSERT INTO transaction_details (transaction_id, part_id, quantity) VALUES (?, ?, ?)",
                    (transaction_id, pno, -quantity)  # Negative quantity for returns
                )

                # Update the quantity of the part in the store
                self.cursor.execute("UPDATE parts SET quantity = ? WHERE pno = ? AND store_id = ?", (new_quantity, pno, store_id))
                
                # Update the store's balance (decrease by total refund amount)
                self.cursor.execute("UPDATE stores SET balance = balance - ? WHERE store_id = ?", (total_refund, store_id))
                
                self.conn.commit()
                print(f"Returned {quantity} of part with pno {pno} for store {store_id}. Total refund: {total_refund}. New quantity: {new_quantity}.")
            else:
                print(f"Part with pno {pno} not found in store {store_id}.")
        except sqlite3.Error as e:
            print(f"Error returning part: {e}")

    def purchase_part_by_pno(self, parts, store_id):
        """
        Purchase multiple parts in a single transaction.
        
        Args:
            parts (list of dict): A list of dictionaries, where each dictionary contains:
                                  - 'pno': Part number (int)
                                  - 'quantity': Quantity to purchase (int)
            store_id (int): The ID of the store where the purchase is made.
        """
        try:
            total_price = 0.0
            transaction_id = None

            # Create a transaction
            self.cursor.execute(
                "INSERT INTO transactions (employee_id, store_id, total_price) VALUES (?, ?, ?)",
                (1, store_id, 0.0)  # Replace `1` with the actual employee ID
            )
            transaction_id = self.cursor.lastrowid

            for part in parts:
                pno = part['pno']
                quantity = part['quantity']

                # Check the current quantity and price of the part
                self.cursor.execute("SELECT quantity, price FROM parts WHERE pno = ? AND store_id = ?", (pno, store_id))
                result = self.cursor.fetchone()

                if result:
                    current_quantity, part_price = result

                    if current_quantity >= quantity:
                        new_quantity = current_quantity - quantity
                        part_total_price = part_price * quantity
                        total_price += part_total_price

                        # Add transaction details
                        self.cursor.execute(
                            "INSERT INTO transaction_details (transaction_id, part_id, quantity) VALUES (?, ?, ?)",
                            (transaction_id, pno, quantity)
                        )

                        # Update the quantity of the part in the store
                        self.cursor.execute(
                            "UPDATE parts SET quantity = ? WHERE pno = ? AND store_id = ?",
                            (new_quantity, pno, store_id)
                        )
                    else:
                        print(f"Insufficient quantity for part with pno {pno}. Available: {current_quantity}, Requested: {quantity}.")
                else:
                    print(f"Part with pno {pno} not found in store {store_id}.")

            # Update the total price of the transaction
            self.cursor.execute(
                "UPDATE transactions SET total_price = ? WHERE transaction_id = ?",
                (total_price, transaction_id)
            )

            # Update the store's balance
            self.cursor.execute(
                "UPDATE stores SET balance = balance + ? WHERE store_id = ?",
                (total_price, store_id)
            )

            self.conn.commit()
            print(f"Transaction {transaction_id} completed. Total price: {total_price}.")
            return transaction_id

        except sqlite3.Error as e:
            print(f"Error purchasing parts: {e}")
            self.conn.rollback()
            return None

    def create_purchase(self, parts: List[PartSold], store_id: int) -> int:
        """
        Create a purchase transaction for multiple parts.

        Args:
            parts (List[PartSold]): A list of `PartSold` objects, where each object contains:
                                    - name: Part name (str)
                                    - quantity: Quantity to purchase (int)
                                    - unit_price: Unit price of the part (float)
            store_id (int): The ID of the store where the purchase is made.

        Returns:
            int: The transaction ID of the created purchase.
        """
        try:
            total_price = 0.0
            transaction_id = None

            # Create a transaction
            self.cursor.execute(
                "INSERT INTO transactions (employee_id, store_id, total_price) VALUES (?, ?, ?)",
                (1, store_id, 0.0)  # Replace `1` with the actual employee ID
            )
            transaction_id = self.cursor.lastrowid

            for part in parts:
                # Fetch pno if not provided
                self.cursor.execute("SELECT pno, quantity FROM parts WHERE name = ? AND store_id = ?", (part.name, store_id))
                result = self.cursor.fetchone()

                if result:
                    pno, current_quantity = result

                    if current_quantity >= part.quantity:
                        new_quantity = current_quantity - part.quantity
                        part_total_price = part.unit_price * part.quantity
                        total_price += part_total_price

                        # Add transaction details
                        self.cursor.execute(
                            "INSERT INTO transaction_details (transaction_id, part_id, quantity) VALUES (?, ?, ?)",
                            (transaction_id, pno, part.quantity)
                        )

                        # Update the quantity of the part in the store
                        self.cursor.execute(
                            "UPDATE parts SET quantity = ? WHERE pno = ? AND store_id = ?",
                            (new_quantity, pno, store_id)
                        )
                    else:
                        print(f"Insufficient quantity for part '{part.name}'. Available: {current_quantity}, Requested: {part.quantity}.")
                else:
                    print(f"Part '{part.name}' not found in store {store_id}.")

            # Update the total price of the transaction
            self.cursor.execute(
                "UPDATE transactions SET total_price = ? WHERE transaction_id = ?",
                (total_price, transaction_id)
            )

            # Update the store's balance
            self.cursor.execute(
                "UPDATE stores SET balance = balance + ? WHERE store_id = ?",
                (total_price, store_id)
            )

            self.conn.commit()
            print(f"Purchase transaction {transaction_id} completed. Total price: {total_price}.")
            return transaction_id

        except sqlite3.Error as e:
            print(f"Error creating purchase: {e}")
            self.conn.rollback()
            return None

    def create_return(self, parts: List[PartSold], store_id: int) -> int:
        """
        Create a return transaction for multiple parts.

        Args:
            parts (List[PartSold]): A list of `PartSold` objects, where each object contains:
                                    - name: Part name (str)
                                    - quantity: Quantity to return (int)
                                    - unit_price: Unit price of the part (float)
                                    - total_price: Total price of the returned part (float)
            store_id (int): The ID of the store where the return is made.

        Returns:
            int: The transaction ID of the created return.
        """
        try:
            total_refund = 0.0
            transaction_id = None

            # Create a transaction
            self.cursor.execute(
                "INSERT INTO transactions (employee_id, store_id, total_price) VALUES (?, ?, ?)",
                (1, store_id, 0.0)  # Replace `1` with the actual employee ID
            )
            transaction_id = self.cursor.lastrowid
            print(f"Created return transaction with ID: {transaction_id}")

            for part in parts:
                # Fetch part details by name
                self.cursor.execute("SELECT pno, quantity, price FROM parts WHERE name = ? AND store_id = ?", (part.name, store_id))
                result = self.cursor.fetchone()

                if result:
                    pno, current_quantity, part_price = result

                    # Increase the quantity of the part in the store
                    new_quantity = current_quantity + part.quantity
                    part_total_refund = part_price * part.quantity
                    total_refund += part_total_refund

                    # Add transaction details
                    self.cursor.execute(
                        "INSERT INTO transaction_details (transaction_id, part_id, quantity) VALUES (?, ?, ?)",
                        (transaction_id, pno, -part.quantity)  # Negative quantity for returns
                    )

                    # Update the quantity of the part in the store
                    self.cursor.execute(
                        "UPDATE parts SET quantity = ? WHERE pno = ? AND store_id = ?",
                        (new_quantity, pno, store_id)
                    )
                    print(f"Updated part '{part.name}' (pno: {pno}) quantity to {new_quantity}.")
                else:
                    print(f"Part '{part.name}' not found in store {store_id}.")

            # Update the total refund of the transaction
            self.cursor.execute(
                "UPDATE transactions SET total_price = ? WHERE transaction_id = ?",
                (-total_refund, transaction_id)  # Negative total price for returns
            )
            print(f"Updated transaction {transaction_id} with total refund: {-total_refund}")

            # Update the store's balance
            self.cursor.execute(
                "UPDATE stores SET balance = balance - ? WHERE store_id = ?",
                (total_refund, store_id)
            )
            print(f"Updated store {store_id} balance by deducting refund: {total_refund}")

            self.conn.commit()
            print(f"Return transaction {transaction_id} completed successfully.")
            return transaction_id

        except sqlite3.Error as e:
            print(f"Error creating return: {e}")
            self.conn.rollback()
            return None

    def reset_db(self):
        """Reset the database by dropping all tables."""
        try:
            # Drop all tables
            self.cursor.execute("PRAGMA foreign_keys=OFF;")  # Disable foreign key checks temporarily
            self.cursor.execute("DROP TABLE IF EXISTS stores;")
            self.cursor.execute("DROP TABLE IF EXISTS employees;")
            self.cursor.execute("DROP TABLE IF EXISTS parts;")
            self.cursor.execute("PRAGMA foreign_keys=ON;")  # Re-enable foreign key checks
            self.conn.commit()
            print("All tables have been dropped and the database has been reset.")
        except Exception as e:
            print(f"Error resetting database: {e}")
            self.conn.rollback()

    # Get all stores
    def get_stores(self):
        try:
            self.cursor.execute("SELECT * FROM stores")
            stores = self.cursor.fetchall()
            return stores
        except sqlite3.Error as e:
            print(f"Error fetching stores: {e}")
            return []

    # Get all employees
    def get_employees(self):
        try:
            self.cursor.execute("SELECT * FROM employees")
            employees = self.cursor.fetchall()
            return employees
        except sqlite3.Error as e:
            print(f"Error fetching employees: {e}")
            return []

    # Get all parts
    def get_parts(self):
        try:
            self.cursor.execute("SELECT * FROM parts")
            parts = self.cursor.fetchall()
            return parts
        except sqlite3.Error as e:
            print(f"Error fetching parts: {e}")
            return []

    def get_transaction_details(self, transaction_id) -> TransactionDetails:
        """Fetches and returns all details of a specific transaction as a structured object."""
        # Fetch transaction details
        transaction_query = """
        SELECT t.transaction_id, t.transaction_date, t.total_price, 
               e.first_name || ' ' || e.last_name AS employee_name, 
               s.store_name
        FROM transactions t
        JOIN employees e ON t.employee_id = e.id
        JOIN stores s ON t.store_id = s.store_id
        WHERE t.transaction_id = ?;
        """
        self.cursor.execute(transaction_query, (transaction_id,))
        transaction = self.cursor.fetchone()
    
        if not transaction:
            raise Exception("No trasaction found")
    
        # Fetch all parts involved in the transaction
        parts_query = """
        SELECT p.name, td.quantity, p.price, (td.quantity * p.price) AS total_part_price
        FROM transaction_details td
        JOIN parts p ON td.part_id = p.pno
        WHERE td.transaction_id = ?;
        """
        self.cursor.execute(parts_query, (transaction_id,))
        parts = self.cursor.fetchall()
    
        # Create a list of PartSold objects
        parts_sold = [PartSold(name=p[0], quantity=p[1], unit_price=p[2], total_price=p[3]) for p in parts]
    
        # Return the structured TransactionDetails object
        return TransactionDetails(
            transaction_id=transaction[0],
            date=transaction[1],
            total_price=transaction[2],
            employee=transaction[3],
            store=transaction[4],
            parts_sold=parts_sold
        )
        
    def get_part_struct(self, part_id: int) -> Part:
        """Fetches and returns part details as a structured object."""
        query = """
        SELECT pno, name, price, store_id, quantity
        FROM parts
        WHERE pno = ?;
        """
        self.cursor.execute(query, (part_id,))
        part = self.cursor.fetchone()
        if not part:
            raise Exception("Part not found")
        # Return a structured Part object
        return Part(
            part_id=part[0],
            name=part[1],
            price=part[2],
            store_id=part[3],
            quantity=part[4]
        )

    def SalesReport(self, store_id: int):
        """
        Fetches and returns all transaction details for a specific store.
        """
        try:
            # Query to fetch transactions for the given store
            transactions_query = """
            SELECT t.transaction_id, t.transaction_date, t.total_price, 
                   e.first_name || ' ' || e.last_name AS employee_name
            FROM transactions t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.store_id = ?
            ORDER BY t.transaction_date DESC;
            """
            self.cursor.execute(transactions_query, (store_id,))
            transactions = self.cursor.fetchall()
    
            if not transactions:
                print(f"No transactions found for store ID {store_id}.")
                return []
    
            # Fetch details for each transaction
            sales_report = []
            for transaction in transactions:
                transaction_id, transaction_date, total_price, employee_name = transaction
    
                # Fetch parts sold in this transaction
                parts_query = """
                SELECT p.name, td.quantity, p.price, (td.quantity * p.price) AS total_part_price
                FROM transaction_details td
                JOIN parts p ON td.part_id = p.pno
                WHERE td.transaction_id = ?;
                """
                self.cursor.execute(parts_query, (transaction_id,))
                parts = self.cursor.fetchall()
    
                # Create a list of PartSold objects
                parts_sold = [PartSold(name=p[0], quantity=p[1], unit_price=p[2], total_price=p[3]) for p in parts]
    
                # Add transaction details to the report
                sales_report.append(TransactionDetails(
                    transaction_id=transaction_id,
                    date=transaction_date,
                    total_price=total_price,
                    employee=employee_name,
                    store=f"Store ID {store_id}",
                    parts_sold=parts_sold
                ))
    
            return sales_report
    
        except sqlite3.Error as e:
            print(f"Error fetching sales report for store ID {store_id}: {e}")
            return []

    def get_parts_by_store(self, store_id: int) -> List[Part]:
        """
        Fetches and returns all parts for a specific store.

        Args:
            store_id (int): The ID of the store.

        Returns:
            List[Part]: A list of Part objects representing the parts in the store.
        """
        try:
            query = """
            SELECT pno, name, price, store_id, quantity
            FROM parts
            WHERE store_id = ?;
            """
            self.cursor.execute(query, (store_id,))
            parts = self.cursor.fetchall()

            # Convert the results into a list of Part objects
            return [Part(part_id=p[0], name=p[1], price=p[2], store_id=p[3], quantity=p[4]) for p in parts]
        except sqlite3.Error as e:
            print(f"Error fetching parts for store ID {store_id}: {e}")
            return []