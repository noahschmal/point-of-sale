import sqlite3

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
        try:
            conn = sqlite3.connect(self.db_name)

            # Enabling foreign key support (SQLite foreign key constraints are disabled by default)
            conn.execute('PRAGMA foreign_keys = ON')
            print(f"Successfully connected to the database: {self.db_name}")
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return None

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
            FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE SET NULL
        );
        """
        
        # Create parts table with store_id and quantity
        create_parts_table_query = """
        CREATE TABLE IF NOT EXISTS parts (
            pno INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
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
        
        try:
            # Execute all table creation queries
            self.cursor.execute(create_stores_table_query)  
            self.cursor.execute(create_employee_table_query)
            self.cursor.execute(create_parts_table_query)
            self.conn.commit()
            print("Tables are ready.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

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

    # Add an employee with store assignment
    def add_employee(self, first_name, last_name, role, store_id):
        try:
            self.cursor.execute("SELECT store_id FROM stores WHERE store_id = ?", (store_id,))
            if not self.cursor.fetchone():
                print(f"Error: Store ID {store_id} does not exist.")
                return
            query = "INSERT INTO employees (first_name, last_name, role, store_id) VALUES (?, ?, ?, ?)"
            self.cursor.execute(query, (first_name, last_name, role, store_id))
            self.conn.commit()
            print(f"Employee {first_name} {last_name} added to store {store_id}.")
        except sqlite3.Error as e:
            print(f"Error adding employee: {e}")

    # Add a part to a store with a specified quantity and return the generated pno
    def add_part_to_store(self, name, price, store_id, quantity):
        try:
            self.cursor.execute("SELECT store_id FROM stores WHERE store_id = ?", (store_id,))
            if not self.cursor.fetchone():
                print(f"Error: Store ID {store_id} does not exist.")
                return
            query = "INSERT INTO parts (name, price, store_id, quantity) VALUES (?, ?, ?, ?)"
            self.cursor.execute(query, (name, price, store_id, quantity))
            self.conn.commit()
            # Return the generated pno (part number)
            pno = self.cursor.lastrowid
            print(f"Part '{name}' added to store {store_id} with quantity {quantity}. Generated pno: {pno}")
            return pno
        except sqlite3.Error as e:
            print(f"Error adding part: {e}")
            return None

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