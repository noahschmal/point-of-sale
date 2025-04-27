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
    discount_percent: float = 0.0
    discounted_price: float = None

    def __post_init__(self):
        """Format monetary values after initialization."""
        self.unit_price = round(self.unit_price, 2)
        self.total_price = round(self.total_price, 2)
        if self.discount_percent > 0:
            self.discounted_price = round(self.total_price * (1 - self.discount_percent), 2)

@dataclass
class TransactionDetails:
    transaction_id: int
    date: str
    total_price: float
    employee: str
    store: str
    parts_sold: List[PartSold]
    subtotal: float = 0.0
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    discount_id: int = None
    discount_name: str = None

    def __post_init__(self):
        """Format monetary values after initialization."""
        self.total_price = round(self.total_price, 2)
        self.subtotal = round(self.subtotal, 2)
        self.discount_amount = round(self.discount_amount, 2)
        self.tax_amount = round(self.tax_amount, 2)

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
            price DECIMAL(10,2) NOT NULL,
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
            balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            tax_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00
        );
        """
    
        # Create transactions table (ensure discount_id column exists)
        create_transactions_table_query = """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            total_price DECIMAL(10,2) NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            discount_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
            FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
            FOREIGN KEY (discount_id) REFERENCES discounts(discount_id) ON DELETE SET NULL
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
        # Create returns table to track returns separately
        create_returns_table_query = """
        CREATE TABLE IF NOT EXISTS returns (
            return_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            original_transaction_id INTEGER,
            return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_refund DECIMAL(10,2) NOT NULL,
            store_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
            FOREIGN KEY (original_transaction_id) REFERENCES transactions(transaction_id) ON DELETE SET NULL,
            FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
        );
        """
        
        # Create discounts table
        create_discounts_table_query = """
        CREATE TABLE IF NOT EXISTS discounts (
            discount_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            discount_type TEXT NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
            value DECIMAL(10,2) NOT NULL,
            start_date DATE,
            end_date DATE,
            store_id INTEGER,
            active BOOLEAN DEFAULT 1,
            FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
        );
        """
        
        # Create part_discounts table for linking parts to discounts
        create_part_discounts_table_query = """
        CREATE TABLE IF NOT EXISTS part_discounts (
            part_discount_id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL,
            discount_id INTEGER NOT NULL,
            FOREIGN KEY (part_id) REFERENCES parts(pno) ON DELETE CASCADE,
            FOREIGN KEY (discount_id) REFERENCES discounts(discount_id) ON DELETE CASCADE
        );
        """
        try:
            # Execute all table creation queries
            self.cursor.execute(create_stores_table_query)  
            self.cursor.execute(create_employee_table_query)
            self.cursor.execute(create_parts_table_query)
            self.cursor.execute(create_transactions_table_query)
            self.cursor.execute(create_transaction_details_table_query)
            self.cursor.execute(create_trigger_update_total_price)
            self.cursor.execute(create_returns_table_query)  # Add this line
            self.cursor.execute(create_discounts_table_query)
            self.cursor.execute(create_part_discounts_table_query)
            self.conn.commit()
            print("Tables are ready.")
            # --- Ensure discount_id column exists in transactions table ---
            self.ensure_discount_id_column()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def ensure_discount_id_column(self):
        """Ensure the discount_id column exists in the transactions table (for upgrades)."""
        self.cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if "discount_id" not in columns:
            try:
                self.cursor.execute("ALTER TABLE transactions ADD COLUMN discount_id INTEGER;")
                self.conn.commit()
                print("Added discount_id column to transactions table.")
            except Exception as e:
                print(f"Error adding discount_id column: {e}")

    # Closes the connection to the database
    def close_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print(f"Connection to {self.db_name} closed.")

    def format_decimal(self, value: float) -> float:
        """Format a value to 2 decimal places."""
        return round(value, 2)

    # Add a new store
    def add_store(self, store_name, balance=0.0, tax_rate=0.0):
        """
        Add a new store with balance and tax rate.
        
        Args:
            store_name (str): Name of the store
            balance (float): Initial balance, defaults to 0.0
            tax_rate (float): Tax rate as decimal (e.g., 0.08 for 8%), defaults to 0.0
        """
        try:
            formatted_balance = self.format_decimal(balance)
            formatted_tax_rate = self.format_decimal(tax_rate)
            query = "INSERT INTO stores (store_name, balance, tax_rate) VALUES (?, ?, ?)"
            self.cursor.execute(query, (store_name, formatted_balance, formatted_tax_rate))
            self.conn.commit()
            print(f"Store '{store_name}' added successfully with {formatted_tax_rate*100:.2f}% tax rate.")
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
            formatted_price = self.format_decimal(price)
            self.cursor.execute("SELECT store_id FROM stores WHERE store_id = ?", (store_id,))
            if not self.cursor.fetchone():
                print(f"Error: Store ID {store_id} does not exist.")
                return None

            query = "INSERT INTO parts (name, price, store_id, quantity) VALUES (?, ?, ?, ?)"
            self.cursor.execute(query, (name, formatted_price, store_id, quantity))
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
    def return_part(self, name, store_id, quantity, employee_id: int):
        """Return parts with admin check."""
        if not self.check_admin_access(employee_id):
            raise Exception("Admin access required for returns")
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
    def return_part_by_pno(self, pno, store_id, quantity, employee_id: int):
        """Return part by pno with admin check."""
        if not self.check_admin_access(employee_id):
            raise Exception("Admin access required for returns")
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


    def create_purchase(self, parts: List[PartSold], store_id: int, employee_id: int = 1, discount_id: int = None) -> int:
        """Create a purchase transaction for multiple parts with discount support."""
        try:
            tax_rate = self.get_store_tax_rate(store_id)
            subtotal = 0.0
            discounted_total = 0.0
            transaction_id = None
            discount_amount = 0.0

            # Calculate subtotal and discount
            for part in parts:
                part_subtotal = part.unit_price * part.quantity
                subtotal += part_subtotal
            if discount_id:
                # Get discount info
                self.cursor.execute("SELECT discount_type, value FROM discounts WHERE discount_id = ?", (discount_id,))
                row = self.cursor.fetchone()
                if row:
                    dtype, dval = row
                    if dtype == "percentage":
                        discount_amount = round(subtotal * (float(dval) / 100), 2)
                    elif dtype == "fixed":
                        discount_amount = min(round(float(dval), 2), subtotal)
            discounted_total = max(subtotal - discount_amount, 0)

            # Create initial transaction (store discount_id)
            self.cursor.execute(
                "INSERT INTO transactions (employee_id, store_id, total_price, discount_id) VALUES (?, ?, ?, ?)",
                (employee_id, store_id, 0.0, discount_id)
            )
            transaction_id = self.cursor.lastrowid

            # Process each part
            for part in parts:
                self.cursor.execute(
                    "SELECT pno, quantity FROM parts WHERE name = ? AND store_id = ?", 
                    (part.name, store_id)
                )
                result = self.cursor.fetchone()
                if result and result[1] >= part.quantity:
                    pno, current_quantity = result
                    new_quantity = current_quantity - part.quantity
                    self.cursor.execute(
                        "UPDATE parts SET quantity = ? WHERE pno = ?",
                        (new_quantity, pno)
                    )
                    self.cursor.execute(
                        "INSERT INTO transaction_details (transaction_id, part_id, quantity) VALUES (?, ?, ?)",
                        (transaction_id, pno, part.quantity)
                    )
                else:
                    raise Exception(f"Insufficient quantity for {part.name}")

            # Calculate final amounts
            tax_amount = discounted_total * tax_rate
            final_total = discounted_total + tax_amount

            # Update transaction total
            self.cursor.execute(
                "UPDATE transactions SET total_price = ? WHERE transaction_id = ?",
                (final_total, transaction_id)
            )

            # Update store balance
            self.update_store_balance(store_id, final_total, is_addition=True)

            self.conn.commit()
            print(f"Purchase completed - Subtotal: {subtotal:.2f}, Discounted: {discounted_total:.2f}, Tax: {tax_amount:.2f}, Total: {final_total:.2f}")
            return transaction_id

        except Exception as e:
            print(f"Error in create_purchase: {e}")
            self.conn.rollback()
            return None

    def create_return(self, parts: List[PartSold], store_id: int, employee_id: int) -> int:
        """Create a return transaction with admin check."""
        if not self.check_admin_access(employee_id):
            raise Exception("Admin access required for returns")
        try:
            total_refund = 0.0
            # Create a transaction
            self.cursor.execute(
                "INSERT INTO transactions (employee_id, store_id, total_price) VALUES (?, ?, ?)",
                (employee_id, store_id, 0.0)
            )
            transaction_id = self.cursor.lastrowid

            # Process parts and update quantities
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

            # Log the return in returns table
            self.cursor.execute(
                """INSERT INTO returns 
                   (transaction_id, original_transaction_id, total_refund, store_id, employee_id)
                   VALUES (?, NULL, ?, ?, ?)""",
                (transaction_id, total_refund, store_id, employee_id)
            )

            self.conn.commit()
            return transaction_id

        except sqlite3.Error as e:
            print(f"Error creating return: {e}")
            self.conn.rollback()
            return None

    def return_by_transaction_id(self, transaction_id: int, employee_id: int) -> int:
        """Process a return based on transaction ID with admin check."""
        if not self.check_admin_access(employee_id):
            raise Exception("Admin access required for returns")
        try:
            # Get original transaction details
            store_id = self.cursor.execute(
                "SELECT store_id FROM transactions WHERE transaction_id = ?", 
                (transaction_id,)
            ).fetchone()[0]
            
            self.cursor.execute("SELECT tax_rate FROM stores WHERE store_id = ?", (store_id,))
            tax_rate = self.cursor.fetchone()[0]

            # Fetch the original transaction details
            transaction_details = self.get_transaction_details(transaction_id)

            if not transaction_details:
                raise Exception(f"Transaction with ID {transaction_id} not found.")

            total_refund = 0.0

            # Create a new return transaction
            self.cursor.execute(
                "INSERT INTO transactions (employee_id, store_id, total_price) VALUES (?, ?, ?)",
                (employee_id, store_id, 0.0)  # Replace `1` with the actual employee ID
            )
            return_transaction_id = self.cursor.lastrowid

            # Process each part in the original transaction
            for part in transaction_details.parts_sold:
                # Fetch the current quantity of the part
                self.cursor.execute(
                    "SELECT quantity FROM parts WHERE name = ? AND store_id = ?", (part.name, store_id)
                )
                current_quantity = self.cursor.fetchone()[0]

                # Update the quantity of the part in the store
                new_quantity = current_quantity + abs(part.quantity)  # Add the returned quantity
                self.cursor.execute(
                    "UPDATE parts SET quantity = ? WHERE name = ? AND store_id = ?",
                    (new_quantity, part.name, store_id)
                )

                # Calculate the refund for this part
                part_refund = abs(part.quantity) * part.unit_price
                total_refund += part_refund
                part.part_id = self.get_part_by_name(part.name, store_id).part_id  # Get the part ID
                # Add transaction details for the return
                self.cursor.execute(
                    "INSERT INTO transaction_details (transaction_id, part_id, quantity) VALUES (?, ?, ?)",
                    (return_transaction_id, part.part_id, -abs(part.quantity))  # Negative quantity for returns
                )

            # Calculate tax
            tax_amount = total_refund * tax_rate
            total_with_tax = self.format_decimal(total_refund + tax_amount)

            # Update the total refund in the return transaction
            self.cursor.execute(
                "UPDATE transactions SET total_price = ? WHERE transaction_id = ?",
                (-total_with_tax, return_transaction_id)
            )

            # Log the return in returns table
            self.cursor.execute(
                """INSERT INTO returns 
                   (transaction_id, original_transaction_id, total_refund, store_id, employee_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (return_transaction_id, transaction_id, total_with_tax, store_id, employee_id)
            )

            # Update the store's balance
            self.update_store_balance(store_id, total_with_tax, is_addition=False)

            self.conn.commit()
            print(f"Return transaction {return_transaction_id} completed. Subtotal: {total_refund}, Tax: {tax_amount}, Total: {total_with_tax}")
            return return_transaction_id

        except sqlite3.Error as e:
            print(f"Error processing return for transaction ID {transaction_id}: {e}")
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
        # Fetch transaction details (include discount_id)
        transaction_query = """
        SELECT t.transaction_id, t.transaction_date, t.total_price, 
               e.first_name || ' ' || e.last_name AS employee_name, 
               s.store_name, t.discount_id
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
        # Fetch discount info if present
        discount_id = transaction[5]
        discount_name = None
        discount_amount = 0.0
        subtotal = sum(p.total_price for p in parts_sold)
        if discount_id:
            self.cursor.execute("SELECT name, discount_type, value FROM discounts WHERE discount_id = ?", (discount_id,))
            drow = self.cursor.fetchone()
            if drow:
                discount_name = drow[0]
                dtype, dval = drow[1], float(drow[2])
                if dtype == "percentage":
                    discount_amount = round(subtotal * (dval / 100), 2)
                elif dtype == "fixed":
                    discount_amount = min(round(dval, 2), subtotal)
        # Return the structured TransactionDetails object
        return TransactionDetails(
            transaction_id=transaction[0],
            date=transaction[1],
            total_price=transaction[2],
            employee=transaction[3],
            store=transaction[4],
            parts_sold=parts_sold,
            subtotal=subtotal,
            discount_amount=discount_amount,
            discount_id=discount_id,
            discount_name=discount_name
        )

    def SalesReport(self, store_id: int):
        """
        Fetches and returns all transaction details for a specific store.
        """
        try:
            # Query to fetch transactions for the given store (include discount_id)
            transactions_query = """
            SELECT t.transaction_id, t.transaction_date, t.total_price, 
                   e.first_name || ' ' || e.last_name AS employee_name,
                   t.discount_id
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
                transaction_id, transaction_date, total_price, employee_name, discount_id = transaction
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
                # Fetch discount info if present
                discount_name = None
                discount_amount = 0.0
                subtotal = sum(p.total_price for p in parts_sold)
                if discount_id:
                    self.cursor.execute("SELECT name, discount_type, value FROM discounts WHERE discount_id = ?", (discount_id,))
                    drow = self.cursor.fetchone()
                    if drow:
                        discount_name = drow[0]
                        dtype, dval = drow[1], float(drow[2])
                        if dtype == "percentage":
                            discount_amount = round(subtotal * (dval / 100), 2)
                        elif dtype == "fixed":
                            discount_amount = min(round(dval, 2), subtotal)
                # Add transaction details to the report
                sales_report.append(TransactionDetails(
                    transaction_id=transaction_id,
                    date=transaction_date,
                    total_price=total_price,
                    employee=employee_name,
                    store=f"Store ID {store_id}",
                    parts_sold=parts_sold,
                    subtotal=subtotal,
                    discount_amount=discount_amount,
                    discount_id=discount_id,
                    discount_name=discount_name
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

    def get_part_by_name(self, name: str, store_id: int) -> Part:
        """
        Fetches and returns part details based on part name and store ID.

        Args:
            name (str): The name of the part to find.
            store_id (int): The ID of the store where the part is located.

        Returns:
            Part: A Part object containing the part details.

        Raises:
            Exception: If the part is not found in the specified store.
        """
        try:
            query = """
            SELECT pno, name, price, store_id, quantity
            FROM parts
            WHERE name = ? AND store_id = ?;
            """
            self.cursor.execute(query, (name, store_id))
            part = self.cursor.fetchone()
            if not part:
                raise Exception(f"Part '{name}' not found in store {store_id}")
                
            # Return a structured Part object
            return Part(
                part_id=part[0],
                name=part[1],
                price=part[2],
                store_id=part[3],
                quantity=part[4]
            )
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise Exception(f"Error fetching part '{name}' from store {store_id}")

    def get_part_by_id(self, part_id: int):
        """Fetches and returns part details as a structured object."""
        query = """
        SELECT pno, name, price, store_id, quantity
        FROM parts
        WHERE pno = ?;
        """
        self.cursor.execute(query, (part_id,))
        part = self.cursor.fetchone()
        if not part:
            return None
        return Part(
            part_id=part[0],
            name=part[1],
            price=part[2],
            store_id=part[3],
            quantity=part[4]
        )

    def update_store_balance(self, store_id: int, amount: float, is_addition: bool = True) -> bool:
        """
        Update store balance with proper decimal formatting.
        
        Args:
            store_id (int): The ID of the store to update
            amount (float): The amount to add or subtract
            is_addition (bool): True to add amount, False to subtract
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            formatted_amount = self.format_decimal(amount)
            
            # Get current balance
            self.cursor.execute("SELECT balance FROM stores WHERE store_id = ?", (store_id,))
            current_balance = self.cursor.fetchone()[0]
            
            # Calculate new balance
            new_balance = self.format_decimal(
                current_balance + formatted_amount if is_addition 
                else current_balance - formatted_amount
            )
            
            # Update store balance
            self.cursor.execute(
                "UPDATE stores SET balance = ? WHERE store_id = ?",
                (new_balance, store_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating store balance: {e}")
            return False

    def get_store_tax_rate(self, store_id):
        """Fetch the tax rate for a given store."""
        self.cursor.execute("SELECT tax_rate FROM stores WHERE store_id = ?", (store_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0.0

    def get_transaction_log(self, store_id: int = None, start_date: str = None, end_date: str = None):
        """
        Get a log of all transactions including return information.
        
        Args:
            store_id (int, optional): Filter by store ID
            start_date (str, optional): Filter by start date (YYYY-MM-DD)
            end_date (str, optional): Filter by end date (YYYY-MM-DD)
        """
        try:
            query = """
                SELECT 
                    t.transaction_id,
                    t.transaction_date,
                    t.total_price,
                    e.first_name || ' ' || e.last_name AS employee_name,
                    s.store_name,
                    CASE 
                        WHEN r.return_id IS NOT NULL THEN 'Return'
                        ELSE 'Purchase'
                    END as transaction_type,
                    r.original_transaction_id
                FROM transactions t
                JOIN employees e ON t.employee_id = e.id
                JOIN stores s ON t.store_id = s.store_id
                LEFT JOIN returns r ON t.transaction_id = r.transaction_id
                WHERE 1=1
            """
            params = []

            if store_id:
                query += " AND t.store_id = ?"
                params.append(store_id)
            
            if start_date:
                query += " AND date(t.transaction_date) >= date(?)"
                params.append(start_date)
                
            if end_date:
                query += " AND date(t.transaction_date) <= date(?)"
                params.append(end_date)

            query += " ORDER BY t.transaction_date DESC"

            self.cursor.execute(query, params)
            transactions = self.cursor.fetchall()

            # Format the results as a list of dictionaries
            transaction_log = []
            for t in transactions:
                transaction_log.append({
                    'transaction_id': t[0],
                    'date': t[1],
                    'total_price': t[2],
                    'employee': t[3],
                    'store': t[4],
                    'type': t[5],
                    'original_transaction_id': t[6]
                })

            return transaction_log

        except sqlite3.Error as e:
            print(f"Error getting transaction log: {e}")
            return []

    def check_admin_access(self, employee_id: int) -> bool:
        """Check if employee has admin role."""
        try:
            self.cursor.execute("SELECT role FROM employees WHERE id = ?", (employee_id,))
            result = self.cursor.fetchone()
            return result and result[0].lower() == 'admin'
        except sqlite3.Error:
            return False

    def add_discount(self, name: str, discount_type: str, value: float, 
                    description: str = None, start_date: str = None, 
                    end_date: str = None, store_id: int = None) -> int:
        """
        Add a new discount.
        
        Args:
            name: Name of the discount
            discount_type: Either 'percentage' or 'fixed'
            value: Discount value (percentage or fixed amount)
            description: Optional description
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            store_id: Optional store ID for store-specific discounts
        
        Returns:
            int: The ID of the created discount
        """
        try:
            query = """
            INSERT INTO discounts (name, description, discount_type, value, 
                                 start_date, end_date, store_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (name, description, discount_type, value,
                                      start_date, end_date, store_id))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating discount: {e}")
            return None

    def apply_discount_to_part(self, part_id: int, discount_id: int):
        """Apply a discount to a specific part."""
        try:
            query = """
            INSERT INTO part_discounts (part_id, discount_id)
            VALUES (?, ?)
            """
            self.cursor.execute(query, (part_id, discount_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error applying discount to part: {e}")

    def get_active_discounts(self, store_id: int = None) -> list:
        """Get all active discounts for a store."""
        try:
            query = """
            SELECT discount_id, name, description, discount_type, value
            FROM discounts
            WHERE active = 1
            AND (store_id IS NULL OR store_id = ?)
            AND (end_date IS NULL OR date(end_date) >= date('now'))
            AND (start_date IS NULL OR date(start_date) <= date('now'))
            """
            self.cursor.execute(query, (store_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching active discounts: {e}")
            return []

    def calculate_discount(self, original_price: float, discount_type: str, 
                          discount_value: float) -> float:
        """Calculate discounted price."""
        if discount_type == 'percentage':
            discount_amount = original_price * (discount_value / 100)
        else:  # fixed amount
            discount_amount = discount_value
        
        # Ensure discount doesn't make price negative
        discount_amount = min(discount_amount, original_price)
        return self.format_decimal(original_price - discount_amount)

    def get_part_price_with_discount(self, part_id: int, store_id: int) -> tuple:
        """
        Get part price including any applicable discounts.
        
        Returns:
            tuple: (final_price, original_price, discount_applied)
        """
        try:
            # Get original price
            self.cursor.execute(
                "SELECT price FROM parts WHERE pno = ? AND store_id = ?", 
                (part_id, store_id)
            )
            original_price = self.cursor.fetchone()[0]
            
            # Check for applicable discounts
            query = """
            SELECT d.discount_type, d.value
            FROM discounts d
            JOIN part_discounts pd ON d.discount_id = pd.discount_id
            WHERE pd.part_id = ? AND d.active = 1
            AND (d.store_id IS NULL OR d.store_id = ?)
            AND (d.end_date IS NULL OR date(d.end_date) >= date('now'))
            AND (d.start_date IS NULL OR date(d.start_date) <= date('now'))
            ORDER BY d.value DESC
            LIMIT 1
            """
            self.cursor.execute(query, (part_id, store_id))
            discount = self.cursor.fetchone()
            
            if discount:
                final_price = self.calculate_discount(
                    original_price, discount[0], discount[1]
                )
                return (final_price, original_price, True)
            
            return (original_price, original_price, False)
        except sqlite3.Error as e:
            print(f"Error calculating discounted price: {e}")
            return (original_price, original_price, False)
