import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from DataBase.Database import Database, Part, PartSold, TransactionDetails

class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Point of Sale System")
        self.root.geometry("800x650")
        
        self.db = Database("pos_system.db")
        self.cart = {}
        self.store_id = None  # No store selected initially
        self.selected_store_id = tk.StringVar(value="")  # Default to an empty string (no store displayed)
        self.selected_employee_id = tk.StringVar(value="")  # Default to an empty string (no employee displayed)
        self.logged_in_employee_name = tk.StringVar(value="")  # Track logged-in employee name
        self.transactions = []  # Store transactions for the selected store
        
        self.create_store_selector()
        self.create_employee_selector()
        # --- Add label for logged-in employee ---
        self.employee_name_label = ttk.Label(self.root, textvariable=self.logged_in_employee_name, font=("Arial", 10, "italic"))
        self.employee_name_label.pack(anchor="ne", padx=10, pady=2)
        self.create_tabs()
        self.load_items()
    
    def create_store_selector(self):
        """Create a dropdown to select the store."""
        store_selector_frame = ttk.Frame(self.root)
        store_selector_frame.pack(fill=tk.X, pady=5)

        store_label = ttk.Label(store_selector_frame, text="Select Store:")
        store_label.pack(side=tk.LEFT, padx=5)

        self.store_combobox = ttk.Combobox(store_selector_frame, textvariable=self.selected_store_id, state="readonly")
        self.store_combobox.pack(side=tk.LEFT, padx=5)
        self.store_combobox.bind("<<ComboboxSelected>>", self.on_store_change)  # Bind store change event

        self.load_store_combobox()  # Populate the store dropdown

    def load_store_combobox(self):
        """Load stores into the store selection combobox."""
        stores = self.db.get_stores()
        store_options = {store[0]: store[1] for store in stores}  # {store_id: store_name}
        self.store_combobox["values"] = [f"{store_id}: {store_name}" for store_id, store_name in store_options.items()]
        self.selected_store_id.set("")  # No store displayed initially

    def on_store_change(self, event):
        """Handle store selection change."""
        try:
            # Extract the store ID from the dropdown value
            store_id_str = self.store_combobox.get().split(":")[0].strip()
            self.store_id = int(store_id_str)
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Please select a valid store.")
            return

        self.load_items()  # Reload items for the selected store
        self.load_inventory_list()  # Reload inventory for the selected store
        self.load_transactions()  # Reload transactions for the selected store
        self.load_employees()  # Reload employees for the selected store
        self.load_employee_combobox()  # Refresh the employee dropdown
        # --- Refresh discounts for sales tab ---
        self.load_sales_discounts()
        self.update_cart_display()
        # Add logic to refresh other tabs (e.g., transactions) when implemented
    
    def create_employee_selector(self):
        """Create a dropdown to select the employee."""
        employee_selector_frame = ttk.Frame(self.root)
        employee_selector_frame.pack(fill=tk.X, pady=5)

        employee_label = ttk.Label(employee_selector_frame, text="Select Employee:")
        employee_label.pack(side=tk.LEFT, padx=5)

        self.employee_combobox = ttk.Combobox(employee_selector_frame, textvariable=self.selected_employee_id, state="readonly")
        self.employee_combobox.pack(side=tk.LEFT, padx=5)
        self.employee_combobox.bind("<<ComboboxSelected>>", self.authenticate_employee)  # Bind selection event

        self.logout_button = ttk.Button(employee_selector_frame, text="Logout", command=self.logout_employee)
        self.logout_button.pack(side=tk.LEFT, padx=5)  # Add the logout button next to the combobox

        self.load_employee_combobox()  # Populate the employee dropdown

    def load_employee_combobox(self):
        """Load employees into the employee selection combobox."""
        employees = self.db.get_employees()
        employee_options = {employee[0]: f"{employee[1]} {employee[2]}" for employee in employees if employee[4] == self.store_id}
        # Show "Name (ID: X)" in dropdown for clarity
        self.employee_combobox["values"] = [f"{emp_name} (ID: {emp_id})" for emp_id, emp_name in employee_options.items()]
        self.selected_employee_id.set("")  # No employee displayed initially

    def authenticate_employee(self, event):
        """Prompt for a password when an employee is selected."""
        try:
            # Extract the employee name and ID from the dropdown value
            combo_val = self.employee_combobox.get()
            if "(ID:" in combo_val:
                name_part, id_part = combo_val.rsplit(" (ID:", 1)
                employee_name = name_part.strip()
                employee_id = int(id_part.replace(")", "").strip())
            else:
                # fallback for old format
                employee_data = combo_val.split(":")
                employee_id = int(employee_data[0].strip())
                employee_name = employee_data[1].strip()

            # Prompt for the password
            password = simpledialog.askstring("Authentication", f"Enter password for {employee_name}:", show="*")
            if not password:
                messagebox.showerror("Error", "Password is required.")
                self.employee_combobox.set("")  # Clear the selection
                return

            # Verify the password
            first, last = employee_name.split(" ", 1)
            role, emp_id = self.db.employee_login(first, last, password)
            if emp_id == employee_id:
                # Set the combobox display to the name (not just the ID)
                self.selected_employee_id.set(str(employee_id))  # Only set to the ID as string
                self.employee_combobox.set(f"{employee_name} (ID: {employee_id})")
                self.logged_in_employee_name.set(f"Logged in as: {employee_name}")
                messagebox.showinfo("Success", f"Welcome, {employee_name}!")
            else:
                raise Exception("Authentication failed.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.employee_combobox.set("")  # Clear the selection
            self.logged_in_employee_name.set("")

    def logout_employee(self):
        """Logout the currently selected employee."""
        self.selected_employee_id.set("")  # Clear the selected employee
        self.employee_combobox.set("")  # Clear the combobox display
        self.logged_in_employee_name.set("")
        messagebox.showinfo("Logout", "Employee has been logged out.")

    def create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        
        self.sales_frame = ttk.Frame(self.notebook)
        self.inventory_frame = ttk.Frame(self.notebook)
        self.store_frame = ttk.Frame(self.notebook)
        self.transactions_frame = ttk.Frame(self.notebook)
        self.employees_frame = ttk.Frame(self.notebook)
        self.discounts_frame = ttk.Frame(self.notebook)  # Add discounts tab
        
        self.notebook.add(self.sales_frame, text="Sales")
        self.notebook.add(self.inventory_frame, text="Inventory")
        self.notebook.add(self.store_frame, text="Stores")
        self.notebook.add(self.transactions_frame, text="Transactions")
        self.notebook.add(self.employees_frame, text="Employees")
        self.notebook.add(self.discounts_frame, text="Discounts")  # Add discounts tab to notebook
        
        self.notebook.pack(expand=True, fill="both")
        
        self.create_sales_tab()
        self.create_inventory_tab()
        self.create_store_tab()
        self.create_transactions_tab()
        self.create_employees_tab()
        self.create_discounts_tab()  # Initialize discounts tab
    
    def create_sales_tab(self):
        self.label = ttk.Label(self.sales_frame, text="Select Item:")
        self.label.pack(pady=5)
        
        self.item_var = tk.StringVar()
        self.item_combobox = ttk.Combobox(self.sales_frame, textvariable=self.item_var)
        self.item_combobox.pack(pady=5)
        self.item_combobox.bind("<<ComboboxSelected>>", self.populate_item_id)  # Bind selection event
        
        self.item_id_label = ttk.Label(self.sales_frame, text="Or Enter Item ID:")
        self.item_id_label.pack(pady=5)
        
        self.item_id_entry = ttk.Entry(self.sales_frame)
        self.item_id_entry.pack(pady=5)
        
        self.quantity_label = ttk.Label(self.sales_frame, text="Quantity:")
        self.quantity_label.pack(pady=5)
        
        self.quantity_entry = ttk.Entry(self.sales_frame)
        self.quantity_entry.pack(pady=5)

        # --- Discount Selector ---
        self.discount_var = tk.StringVar()
        self.discount_label = ttk.Label(self.sales_frame, text="Apply Discount:")
        self.discount_label.pack(pady=5)
        self.discount_combobox = ttk.Combobox(self.sales_frame, textvariable=self.discount_var, state="readonly")
        self.discount_combobox.pack(pady=5)
        self.discount_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_cart_display())
        # -------------------------

        self.add_button = ttk.Button(self.sales_frame, text="Add to Cart", command=self.add_to_cart)
        self.add_button.pack(pady=5)
        
        self.cart_listbox = tk.Listbox(self.sales_frame)
        self.cart_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.cart_listbox.bind("<Button-3>", self.show_cart_context_menu)  # Bind right-click event

        self.total_label = ttk.Label(self.sales_frame, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=5)  # Add a label to display the total
        
        self.checkout_button = ttk.Button(self.sales_frame, text="Checkout", command=self.checkout)
        self.checkout_button.pack(pady=5)
        # Show totals on app launch
        self.update_cart_display()

    def load_items(self):
        """Load items from the database and populate the combobox."""
        parts = self.db.get_parts_by_store(self.store_id)
        self.items = {part.name: (part.price, part.quantity) for part in parts}  # {name: (price, quantity)}
        self.item_combobox["values"] = list(self.items.keys())
        # --- Load discounts for the sales tab ---
        self.load_sales_discounts()
    
    def load_sales_discounts(self):
        """Load active discounts for the selected store into the sales tab discount combobox."""
        discounts = self.db.get_active_discounts(self.store_id)
        self.sales_discounts = {}  # {display: discount_tuple}
        discount_display_list = []
        for discount in discounts:
            # discount: (id, name, description, type, value, ...)
            display = f"{discount[1]} ({discount[3]}: {discount[4]})"
            self.sales_discounts[display] = discount
            discount_display_list.append(display)
        self.discount_combobox["values"] = ["No Discount"] + discount_display_list
        self.discount_var.set("No Discount")

    def create_inventory_tab(self):
        self.item_name_label = ttk.Label(self.inventory_frame, text="Item Name:")
        self.item_name_label.pack(pady=5)
        
        self.item_name_entry = ttk.Entry(self.inventory_frame)
        self.item_name_entry.pack(pady=5)
        
        self.item_price_label = ttk.Label(self.inventory_frame, text="Price:")
        self.item_price_label.pack(pady=5)
        
        self.item_price_entry = ttk.Entry(self.inventory_frame)
        self.item_price_entry.pack(pady=5)
        
        self.item_quantity_label = ttk.Label(self.inventory_frame, text="Quantity:")
        self.item_quantity_label.pack(pady=5)
        
        self.item_quantity_entry = ttk.Entry(self.inventory_frame)
        self.item_quantity_entry.pack(pady=5)
        
        self.add_inventory_button = ttk.Button(self.inventory_frame, text="Add Item", command=self.add_inventory_item)
        self.add_inventory_button.pack(pady=5)
        
        self.inventory_listbox = tk.Listbox(self.inventory_frame)
        self.inventory_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.inventory_listbox.bind("<Button-3>", self.show_inventory_context_menu)  # Bind right-click event
        
        self.load_inventory_list()
    
    def create_store_tab(self):
        self.store_name_label = ttk.Label(self.store_frame, text="Store Name:")
        self.store_name_label.pack(pady=5)
        
        self.store_name_entry = ttk.Entry(self.store_frame)
        self.store_name_entry.pack(pady=5)

        # --- Remove Tax Rate Display ---
        # self.tax_rate_var = tk.StringVar(value="Tax Rate: N/A")
        # self.tax_rate_label = ttk.Label(self.store_frame, textvariable=self.tax_rate_var, font=("Arial", 10, "bold"))
        # self.tax_rate_label.pack(pady=2)
        # -------------------------------

        self.add_store_button = ttk.Button(self.store_frame, text="Add Store", command=self.add_store)
        self.add_store_button.pack(pady=5)
        
        self.store_listbox = tk.Listbox(self.store_frame)
        self.store_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.store_listbox.bind("<Button-3>", self.show_store_context_menu)  # Add right-click context menu
        
        self.generate_report_button = ttk.Button(self.store_frame, text="Generate Sales Report", command=self.generate_sales_report)
        self.generate_report_button.pack(pady=5)

        self.load_stores()

    def show_store_context_menu(self, event):
        """Show a context menu for stores to set tax rate."""
        try:
            selected_index = self.store_listbox.nearest(event.y)
            self.store_listbox.selection_clear(0, tk.END)
            self.store_listbox.selection_set(selected_index)
            selected_store_text = self.store_listbox.get(selected_index)
            store_name = selected_store_text.split(" - ")[0]
            stores = self.db.get_stores()
            store_id = None
            for store in stores:
                if store[1] == store_name:
                    store_id = store[0]
                    break
            if store_id is None:
                return

            self.store_context_menu = tk.Menu(self.store_listbox, tearoff=0)
            self.store_context_menu.add_command(label="Set Tax Rate", command=lambda: self.set_store_tax_rate(store_id, store_name))
            self.store_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing store context menu: {e}")

    def set_store_tax_rate(self, store_id, store_name):
        """Prompt user to set a new tax rate for the store."""
        try:
            new_tax = simpledialog.askfloat("Set Tax Rate", f"Enter new tax rate for '{store_name}' (as a percentage, e.g., 8.5 for 8.5%):")
            if new_tax is not None and new_tax >= 0:
                # Convert percentage to decimal for storage
                self.db.cursor.execute("UPDATE stores SET tax_rate = ? WHERE store_id = ?", (round(new_tax / 100, 4), store_id))
                self.db.conn.commit()
                self.load_stores()
                messagebox.showinfo("Success", f"Tax rate for '{store_name}' set to {new_tax:.2f}%.")
            elif new_tax is not None:
                messagebox.showerror("Error", "Tax rate must be 0 or greater.")
        except Exception as e:
            print(f"Error setting store tax rate: {e}")

    def create_transactions_tab(self):
        """Create the Transactions tab."""
        self.transactions_listbox = tk.Listbox(self.transactions_frame)
        self.transactions_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.transactions_listbox.bind("<Double-1>", self.view_transaction_details)  # Bind double-click to view details
        self.transactions_listbox.bind("<Button-3>", self.show_transaction_context_menu)  # Bind right-click for context menu
        self.load_transactions()

    def view_transaction_details(self, event):
        """View details of the selected transaction."""
        try:
            selected_index = self.transactions_listbox.curselection()
            if not selected_index:
                return
            transaction = self.transactions[selected_index[0]]
            details = f"Transaction ID: {transaction.transaction_id}\nDate: {transaction.date}\nTotal: ${transaction.total_price:.2f}\nEmployee: {transaction.employee}\nStore: {transaction.store}\n"
            if getattr(transaction, "discount_name", None):
                details += f"Discount: {transaction.discount_name} (-${transaction.discount_amount:.2f})\n"
            details += "\nParts Sold:\n"
            for part in transaction.parts_sold:
                details += f"- {part.name}: {part.quantity} @ ${part.unit_price:.2f} each (Total: ${part.total_price:.2f})\n"
            messagebox.showinfo("Transaction Details", details)
        except Exception as e:
            print(f"Error viewing transaction details: {e}")

    def show_transaction_context_menu(self, event):
        """Show a context menu for transactions."""
        try:
            selected_index = self.transactions_listbox.nearest(event.y)
            self.transactions_listbox.selection_clear(0, tk.END)
            self.transactions_listbox.selection_set(selected_index)
            transaction = self.transactions[selected_index]

            self.transaction_context_menu = tk.Menu(self.transactions_listbox, tearoff=0)
            self.transaction_context_menu.add_command(label="View Details", command=lambda: self.view_transaction_details(None))
            self.transaction_context_menu.add_command(label="Process Return", command=lambda: self.process_return(transaction.transaction_id))
            self.transaction_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing transaction context menu: {e}")

    def process_return(self, transaction_id):
        """Process a return for the selected transaction."""
        try:
            # Use the same employee ID extraction logic as checkout
            combo_val = self.employee_combobox.get()
            if "(ID:" in combo_val:
                _, id_part = combo_val.rsplit(" (ID:", 1)
                employee_id = int(id_part.replace(")", "").strip())
            else:
                employee_id = self.selected_employee_id.get()
                if not employee_id.isdigit():
                    messagebox.showerror("Error", "Please select a valid employee.")
                    return
                employee_id = int(employee_id)

            return_transaction_id = self.db.return_by_transaction_id(transaction_id, employee_id)
            if return_transaction_id:
                messagebox.showinfo("Success", f"Return processed successfully. Return Transaction ID: {return_transaction_id}")
                self.load_transactions()  # Refresh transactions
                self.load_inventory_list()  # Refresh inventory
                self.load_stores()  # Refresh store balances
            else:
                messagebox.showerror("Error", "Failed to process return.")
        except Exception as e:
            print(f"Error processing return: {e}")
            messagebox.showerror("Error", "Failed to process return. Please ensure you are logged in.")

    def create_employees_tab(self):
        """Create the Employees tab."""
        self.employee_first_name_label = ttk.Label(self.employees_frame, text="First Name:")
        self.employee_first_name_label.pack(pady=5)
        
        self.employee_first_name_entry = ttk.Entry(self.employees_frame)
        self.employee_first_name_entry.pack(pady=5)
        
        self.employee_last_name_label = ttk.Label(self.employees_frame, text="Last Name:")
        self.employee_last_name_label.pack(pady=5)
        
        self.employee_last_name_entry = ttk.Entry(self.employees_frame)
        self.employee_last_name_entry.pack(pady=5)
        
        self.employee_role_label = ttk.Label(self.employees_frame, text="Role:")
        self.employee_role_label.pack(pady=5)
        
        self.employee_role_entry = ttk.Entry(self.employees_frame)
        self.employee_role_entry.pack(pady=5)
        
        self.employee_password_label = ttk.Label(self.employees_frame, text="Password:")
        self.employee_password_label.pack(pady=5)
        
        self.employee_password_entry = ttk.Entry(self.employees_frame, show="*")
        self.employee_password_entry.pack(pady=5)
        
        self.add_employee_button = ttk.Button(self.employees_frame, text="Add Employee", command=self.add_employee)
        self.add_employee_button.pack(pady=5)
        
        self.employees_listbox = tk.Listbox(self.employees_frame)
        self.employees_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.load_employees()

    def load_employees(self):
        """Load employees for the selected store."""
        self.employees_listbox.delete(0, tk.END)
        employees = self.db.get_employees()
        for employee in employees:
            if employee[4] == self.store_id:  # Filter by store_id
                self.employees_listbox.insert(
                    tk.END,
                    f"ID: {employee[0]}, Name: {employee[1]} {employee[2]}, Role: {employee[3]}"
                )

    def add_employee(self):
        """Add a new employee to the selected store and update the employee dropdown."""
        first_name = self.employee_first_name_entry.get()
        last_name = self.employee_last_name_entry.get()
        role = self.employee_role_entry.get()
        password = self.employee_password_entry.get()
        
        if not first_name or not last_name or not role or not password:
            messagebox.showerror("Error", "All fields must be filled.")
            return
        
        try:
            self.db.add_employee(first_name, last_name, role, self.store_id, password)
            messagebox.showinfo("Success", f"Employee '{first_name} {last_name}' added successfully.")
            self.load_employees()
            self.load_employee_combobox()  # Refresh the employee dropdown
            employees = self.db.get_employees()
            self.selected_employee_id.set(employees[-1][0])  # Select the newly added employee
            self.employee_first_name_entry.delete(0, tk.END)
            self.employee_last_name_entry.delete(0, tk.END)
            self.employee_role_entry.delete(0, tk.END)
            self.employee_password_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_inventory_list(self):
        """Load inventory items and display them in the listbox."""
        self.inventory_listbox.delete(0, tk.END)
        parts = self.db.get_parts_by_store(self.store_id)
        for part in parts:
            self.inventory_listbox.insert(tk.END, f"{part.name} - ${part.price:.2f} - {part.quantity} in stock")
    
    def add_inventory_item(self):
        """Add a new item to the inventory."""
        name = self.item_name_entry.get()
        price = self.item_price_entry.get()
        quantity = self.item_quantity_entry.get()
        
        if not name or not price or not quantity:
            messagebox.showerror("Error", "All fields must be filled.")
            return
        
        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            messagebox.showerror("Error", "Price must be a number and quantity must be an integer.")
            return
        
        pno = self.db.add_part_to_store(name, price, self.store_id, quantity)
        if pno:
            messagebox.showinfo("Success", f"Item '{name}' added with quantity {quantity} at ${price:.2f}.")
            self.load_inventory_list()
            self.load_items()  # Update sales items list
            self.load_stores()  # Refresh store inventory total
            self.item_name_entry.delete(0, tk.END)
            self.item_price_entry.delete(0, tk.END)
            self.item_quantity_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Failed to add item to inventory.")

    def add_store(self):
        """Add a new store and update the store dropdown."""
        store_name = self.store_name_entry.get()
        if store_name:
            self.db.add_store(store_name)
            messagebox.showinfo("Success", "Store added successfully!")
            self.load_stores()
            self.load_store_combobox()  # Refresh the store dropdown
            stores = self.db.get_stores()
            self.selected_store_id.set(stores[-1][0])  # Select the newly added store
        else:
            messagebox.showerror("Error", "Please enter a store name.")
    
    def load_stores(self):
        """Load stores and update the store listbox."""
        self.store_listbox.delete(0, tk.END)
        stores = self.db.get_stores()
        for store in stores:
            store_id = store[0]
            inventory_value = self.calculate_inventory_value(store_id)
            # --- Inline tax rate display ---
            tax_rate = self.db.get_store_tax_rate(store_id)
            self.store_listbox.insert(
                tk.END,
                f"{store[1]} - Inventory Value: ${inventory_value:.2f} - Tax Rate: {tax_rate*100:.2f}%"
            )
        # --- Remove tax rate label update ---
        # if self.store_id:
        #     tax_rate = self.db.get_store_tax_rate(self.store_id)
        #     self.tax_rate_var.set(f"Tax Rate: {tax_rate*100:.2f}%")
        # else:
        #     self.tax_rate_var.set("Tax Rate: N/A")

    def calculate_inventory_value(self, store_id):
        """Calculate the total value of the inventory for a given store."""
        parts = self.db.get_parts_by_store(store_id)
        return sum(part.price * part.quantity for part in parts)

    def add_to_cart(self):
        """Add an item to the cart."""
        selected_item = self.item_var.get()
        item_id = self.item_id_entry.get()
        quantity = self.quantity_entry.get()
        
        if not quantity.isdigit():
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return
        
        quantity = int(quantity)
        
        if item_id.isdigit():
            # Add item using manually entered item ID
            item_id = int(item_id)
            # Use get_part_by_id instead of get_part_struct
            part = self.db.get_part_by_id(item_id)
            if not part:
                messagebox.showerror("Error", "Item ID not found.")
                return
            if quantity > part.quantity:
                messagebox.showerror("Error", "Not enough stock available.")
                return
            if part.name in self.cart:
                self.cart[part.name] += quantity
            else:
                self.cart[part.name] = quantity
            self.items[part.name] = (part.price, part.quantity)  # Ensure item is in the items dictionary
        elif selected_item:
            # Add item using dropdown selection
            available_quantity = self.items[selected_item][1]
            if quantity > available_quantity:
                messagebox.showerror("Error", "Not enough stock available.")
                return
            if selected_item in self.cart:
                self.cart[selected_item] += quantity
            else:
                self.cart[selected_item] = quantity
        else:
            messagebox.showerror("Error", "Please select an item or enter a valid item ID.")
            return
        
        self.update_cart_display()

    def update_cart_display(self):
        """Update the cart listbox and subtotal/total labels."""
        self.cart_listbox.delete(0, tk.END)
        subtotal = 0
        for item, quantity in self.cart.items():
            total_price = self.items[item][0] * quantity
            subtotal += total_price
            self.cart_listbox.insert(tk.END, f"{item} x{quantity} - ${total_price:.2f}")
        # --- Apply discount if selected ---
        discount_display = self.discount_var.get()
        discount_amount = 0
        if hasattr(self, "sales_discounts") and discount_display and discount_display != "No Discount":
            discount = self.sales_discounts.get(discount_display)
            if discount:
                dtype = discount[3]
                dval = float(discount[4])
                if dtype.lower() == "percentage":
                    discount_amount = round(subtotal * (dval / 100), 2)
                elif dtype.lower() == "fixed":
                    discount_amount = min(round(dval, 2), subtotal)
        discounted_subtotal = max(subtotal - discount_amount, 0)
        tax_rate = self.db.get_store_tax_rate(self.store_id) or 0.0
        tax_amount = round(discounted_subtotal * tax_rate, 2)
        total = round(discounted_subtotal + tax_amount, 2)
        # Show both subtotal and total, and discount if applied
        if discount_amount > 0:
            self.total_label.config(
                text=f"Subtotal: ${subtotal:.2f}   Discount: -${discount_amount:.2f}   Tax: ${tax_amount:.2f}   Total: ${total:.2f}"
            )
        else:
            self.total_label.config(
                text=f"Subtotal: ${subtotal:.2f}   Tax: ${tax_amount:.2f}   Total: ${total:.2f}"
            )

    def checkout(self):
        """Process the checkout and update the database."""
        try:
            # Try to get the logged-in employee ID from combobox
            combo_val = self.employee_combobox.get()
            if "(ID:" in combo_val:
                _, id_part = combo_val.rsplit(" (ID:", 1)
                employee_id = int(id_part.replace(")", "").strip())
            else:
                employee_id = self.selected_employee_id.get()
                if not employee_id.isdigit():
                    messagebox.showerror("Error", "Please select a valid employee.")
                    return
                employee_id = int(employee_id)

            if not employee_id:
                messagebox.showerror("Error", "Please select a valid employee.")
                return

        except Exception as e:
            print("DEBUG Exception in checkout employee_id:", e)
            messagebox.showerror("Error", "Please select a valid employee.")
            return

        parts_sold = []
        for item, quantity in self.cart.items():
            price = self.items[item][0]
            parts_sold.append(PartSold(name=item, quantity=quantity, unit_price=price, total_price=price * quantity))
        
        # --- Calculate discount ---
        subtotal = sum(part.total_price for part in parts_sold)
        discount_display = self.discount_var.get()
        discount_amount = 0
        discount_id = None
        if hasattr(self, "sales_discounts") and discount_display and discount_display != "No Discount":
            discount = self.sales_discounts.get(discount_display)
            if discount:
                discount_id = discount[0]
                dtype = discount[3]
                dval = float(discount[4])
                if dtype.lower() == "percentage":
                    discount_amount = round(subtotal * (dval / 100), 2)
                elif dtype.lower() == "fixed":
                    discount_amount = min(round(dval, 2), subtotal)
        discounted_subtotal = max(subtotal - discount_amount, 0)
        tax_rate = self.db.get_store_tax_rate(self.store_id) or 0.0  # Fetch tax rate for the store, default to 0.0
        tax_amount = round(discounted_subtotal * tax_rate, 2)
        total = round(discounted_subtotal + tax_amount, 2)

        # --- Pass discount_id to create_purchase ---
        transaction_id = self.db.create_purchase(parts_sold, self.store_id, employee_id=employee_id, discount_id=discount_id)
        if transaction_id:
            receipt = f"Subtotal: ${subtotal:.2f}\n"
            if discount_amount > 0:
                receipt += f"Discount: -${discount_amount:.2f}\n"
            receipt += f"Tax: ${tax_amount:.2f}\nTotal: ${total:.2f}"
            messagebox.showinfo("Total", receipt)
            self.cart.clear()
            self.update_cart_display()
            self.load_items()  # Refresh items after purchase
            self.load_inventory_list()  # Update inventory tab after checkout
            self.load_transactions()  # Update transactions tab after checkout
            self.load_stores()  # Update store tab after checkout
            # Reset discount selection after checkout
            self.discount_var.set("No Discount")
        else:
            messagebox.showerror("Error", "Checkout failed.")

    def generate_sales_report(self):
        """Generate a sales report for the selected store."""
        try:
            sales_report = self.db.SalesReport(self.store_id)
            if not sales_report:
                messagebox.showinfo("Sales Report", "No transactions found for this store.")
                return

            report = f"Sales Report for Store ID {self.store_id}\n\n"
            for transaction in sales_report:
                report += f"Transaction ID: {transaction.transaction_id}, Date: {transaction.date}, Total: ${transaction.total_price:.2f}, Employee: {transaction.employee}\n"
                if getattr(transaction, "discount_name", None):
                    report += f"  Discount: {transaction.discount_name} (-${transaction.discount_amount:.2f})\n"
                for part in transaction.parts_sold:
                    report += f"  - {part.name}: {part.quantity} @ ${part.unit_price:.2f} each (Total: ${part.total_price:.2f})\n"
                report += "\n"

            # Display the report in a new window
            report_window = tk.Toplevel(self.root)
            report_window.title("Sales Report")
            report_text = tk.Text(report_window, wrap=tk.WORD)
            report_text.insert(tk.END, report)
            report_text.pack(expand=True, fill=tk.BOTH)
            report_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error generating sales report: {e}")

    def load_transactions(self):
        """Load transactions for the selected store."""
        self.transactions_listbox.delete(0, tk.END)
        self.transactions = self.db.SalesReport(self.store_id)
        for transaction in self.transactions:
            self.transactions_listbox.insert(
                tk.END,
                f"ID: {transaction.transaction_id}, Date: {transaction.date}, Total: ${transaction.total_price:.2f}, Employee: {transaction.employee}"
            )

    def create_discounts_tab(self):
        """Create the Discounts tab."""
        self.discount_name_label = ttk.Label(self.discounts_frame, text="Discount Name:")
        self.discount_name_label.pack(pady=5)

        self.discount_name_entry = ttk.Entry(self.discounts_frame)
        self.discount_name_entry.pack(pady=5)

        self.discount_type_label = ttk.Label(self.discounts_frame, text="Discount Type:")
        self.discount_type_label.pack(pady=5)

        # --- Use radio buttons for discount type selection ---
        self.discount_type_var = tk.StringVar(value="percentage")
        discount_type_frame = ttk.Frame(self.discounts_frame)
        discount_type_frame.pack(pady=5)
        self.discount_percentage_radio = ttk.Radiobutton(
            discount_type_frame, text="Percentage", variable=self.discount_type_var, value="percentage"
        )
        self.discount_percentage_radio.pack(side=tk.LEFT, padx=5)
        self.discount_fixed_radio = ttk.Radiobutton(
            discount_type_frame, text="Fixed", variable=self.discount_type_var, value="fixed"
        )
        self.discount_fixed_radio.pack(side=tk.LEFT, padx=5)
        # -----------------------------------------------------

        self.discount_value_label = ttk.Label(self.discounts_frame, text="Discount Value:")
        self.discount_value_label.pack(pady=5)

        self.discount_value_entry = ttk.Entry(self.discounts_frame)
        self.discount_value_entry.pack(pady=5)

        self.discount_start_label = ttk.Label(self.discounts_frame, text="Start Date (YYYY-MM-DD, optional):")
        self.discount_start_label.pack(pady=5)
        self.discount_start_entry = ttk.Entry(self.discounts_frame)
        self.discount_start_entry.pack(pady=5)

        self.discount_end_label = ttk.Label(self.discounts_frame, text="End Date (YYYY-MM-DD, optional):")
        self.discount_end_label.pack(pady=5)
        self.discount_end_entry = ttk.Entry(self.discounts_frame)
        self.discount_end_entry.pack(pady=5)

        self.discount_desc_label = ttk.Label(self.discounts_frame, text="Description (optional):")
        self.discount_desc_label.pack(pady=5)
        self.discount_desc_entry = ttk.Entry(self.discounts_frame)
        self.discount_desc_entry.pack(pady=5)

        self.add_discount_button = ttk.Button(self.discounts_frame, text="Add Discount", command=self.add_discount)
        self.add_discount_button.pack(pady=5)

        self.discounts_listbox = tk.Listbox(self.discounts_frame)
        self.discounts_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        # --- Add right-click context menu binding ---
        self.discounts_listbox.bind("<Button-3>", self.show_discount_context_menu)
        self.load_discounts()

    def add_discount(self):
        """Add a new discount using the backend Database.py system."""
        name = self.discount_name_entry.get()
        # Use the radio button value for discount type
        discount_type = self.discount_type_var.get()
        value = self.discount_value_entry.get()
        start_date = self.discount_start_entry.get().strip() or None
        end_date = self.discount_end_entry.get().strip() or None
        description = self.discount_desc_entry.get().strip() or None

        if not name or not discount_type or not value:
            messagebox.showerror("Error", "Name, type, and value are required.")
            return

        try:
            value = float(value)
        except ValueError:
            messagebox.showerror("Error", "Discount value must be a number.")
            return

        discount_id = self.db.add_discount(
            name=name,
            discount_type=discount_type,
            value=value,
            description=description,
            start_date=start_date,
            end_date=end_date,
            store_id=self.store_id
        )
        if discount_id:
            messagebox.showinfo("Success", f"Discount '{name}' added successfully.")
            self.load_discounts()
            self.load_sales_discounts()  # Add this line to refresh sales tab discounts
            self.discount_name_entry.delete(0, tk.END)
            # Reset radio button to default
            self.discount_type_var.set("percentage")
            self.discount_value_entry.delete(0, tk.END)
            self.discount_start_entry.delete(0, tk.END)
            self.discount_end_entry.delete(0, tk.END)
            self.discount_desc_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Failed to add discount.")

    def load_discounts(self):
        """Load discounts into the listbox."""
        self.discounts_listbox.delete(0, tk.END)
        discounts = self.db.get_active_discounts(self.store_id)
        for discount in discounts:
            self.discounts_listbox.insert(
                tk.END,
                f"{discount[1]} - {discount[3]}: {discount[4]} | {discount[2] or ''}"
            )

    def populate_item_id(self, event):
        """Populate the item ID entry box based on the selected item in the dropdown."""
        selected_item = self.item_var.get()
        if selected_item in self.items:
            # Find the part by name and store
            parts = self.db.get_parts_by_store(self.store_id)
            for part in parts:
                if part.name == selected_item:
                    self.item_id_entry.delete(0, tk.END)
                    self.item_id_entry.insert(0, part.part_id)
                    break

    def show_cart_context_menu(self, event):
        """Show a context menu to manage items in the cart."""
        try:
            selected_index = self.cart_listbox.nearest(event.y)
            self.cart_listbox.selection_clear(0, tk.END)
            self.cart_listbox.selection_set(selected_index)
            selected_item = self.cart_listbox.get(selected_index)
            item_name = selected_item.split(" x")[0]

            self.cart_context_menu = tk.Menu(self.cart_listbox, tearoff=0)
            self.cart_context_menu.add_command(label="Remove Item", command=lambda: self.remove_from_cart(item_name))
            self.cart_context_menu.add_command(label="Change Quantity", command=lambda: self.change_cart_quantity(item_name))
            self.cart_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing cart context menu: {e}")

    def remove_from_cart(self, item_name):
        """Remove the specified item from the cart."""
        try:
            if item_name in self.cart:
                del self.cart[item_name]
                self.update_cart_display()
                messagebox.showinfo("Success", f"Removed '{item_name}' from the cart.")
        except Exception as e:
            print(f"Error removing item from cart: {e}")

    def change_cart_quantity(self, item_name):
        """Change the quantity of the specified item in the cart."""
        try:
            if item_name in self.cart:
                new_quantity = tk.simpledialog.askinteger("Change Quantity", f"Enter new quantity for '{item_name}':")
                if new_quantity is not None and new_quantity > 0:
                    available_quantity = self.items[item_name][1]
                    if new_quantity > available_quantity:
                        messagebox.showerror("Error", f"Not enough stock available. Max available: {available_quantity}.")
                    else:
                        self.cart[item_name] = new_quantity
                        self.update_cart_display()
                        messagebox.showinfo("Success", f"Updated quantity of '{item_name}' to {new_quantity}.")
                elif new_quantity is not None:
                    messagebox.showerror("Error", "Quantity must be greater than 0.")
        except Exception as e:
            print(f"Error changing item quantity: {e}")

    def show_inventory_context_menu(self, event):
        """Show a context menu to manage items in the inventory."""
        try:
            selected_index = self.inventory_listbox.nearest(event.y)
            self.inventory_listbox.selection_clear(0, tk.END)
            self.inventory_listbox.selection_set(selected_index)
            selected_item = self.inventory_listbox.get(selected_index)
            item_name = selected_item.split(" - ")[0]

            self.inventory_context_menu = tk.Menu(self.inventory_listbox, tearoff=0)
            self.inventory_context_menu.add_command(label="Remove Item", command=lambda: self.remove_inventory_item(item_name))
            self.inventory_context_menu.add_command(label="Update Price", command=lambda: self.update_inventory_price(item_name))
            self.inventory_context_menu.add_command(label="Update Stock", command=lambda: self.update_inventory_stock(item_name))
            self.inventory_context_menu.add_command(label="Change Name", command=lambda: self.change_inventory_name(item_name))
            self.inventory_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing inventory context menu: {e}")

    def remove_inventory_item(self, item_name):
        """Remove the specified item from the inventory."""
        try:
            part = next((p for p in self.db.get_parts_by_store(self.store_id) if p.name == item_name), None)
            if part:
                self.db.cursor.execute("DELETE FROM parts WHERE pno = ?", (part.part_id,))
                self.db.conn.commit()
                self.load_inventory_list()
                messagebox.showinfo("Success", f"Removed '{item_name}' from inventory.")
        except Exception as e:
            print(f"Error removing inventory item: {e}")

    def update_inventory_price(self, item_name):
        """Update the price of the specified item in the inventory."""
        try:
            new_price = simpledialog.askfloat("Update Price", f"Enter new price for '{item_name}':")
            if new_price is not None and new_price > 0:
                self.db.cursor.execute("UPDATE parts SET price = ? WHERE name = ?", (new_price, item_name))
                self.db.conn.commit()
                self.load_inventory_list()
                messagebox.showinfo("Success", f"Updated price of '{item_name}' to ${new_price:.2f}.")
            elif new_price is not None:
                messagebox.showerror("Error", "Price must be greater than 0.")
        except Exception as e:
            print(f"Error updating inventory price: {e}")

    def update_inventory_stock(self, item_name):
        """Update the stock of the specified item in the inventory."""
        try:
            new_stock = simpledialog.askinteger("Update Stock", f"Enter new stock quantity for '{item_name}':")
            if new_stock is not None and new_stock >= 0:
                self.db.cursor.execute("UPDATE parts SET quantity = ? WHERE name = ?", (new_stock, item_name))
                self.db.conn.commit()
                self.load_inventory_list()
                messagebox.showinfo("Success", f"Updated stock of '{item_name}' to {new_stock}.")
            elif new_stock is not None:
                messagebox.showerror("Error", "Stock must be 0 or greater.")
        except Exception as e:
            print(f"Error updating inventory stock: {e}")

    def change_inventory_name(self, item_name):
        """Change the name of the specified item in the inventory."""
        try:
            new_name = simpledialog.askstring("Change Name", f"Enter new name for '{item_name}':")
            if new_name:
                self.db.cursor.execute("UPDATE parts SET name = ? WHERE name = ?", (new_name, item_name))
                self.db.conn.commit()
                self.load_inventory_list()
                messagebox.showinfo("Success", f"Changed name of '{item_name}' to '{new_name}'.")
        except Exception as e:
            print(f"Error changing inventory name: {e}")

    def show_discount_context_menu(self, event):
        """Show a context menu for discounts to allow deletion."""
        try:
            selected_index = self.discounts_listbox.nearest(event.y)
            self.discounts_listbox.selection_clear(0, tk.END)
            self.discounts_listbox.selection_set(selected_index)
            selected_discount = self.discounts_listbox.get(selected_index)
            # Find the discount id by matching the name and type/value
            discount_name = selected_discount.split(" - ")[0].strip()
            discounts = self.db.get_active_discounts(self.store_id)
            discount_id = None
            for discount in discounts:
                if discount[1] == discount_name:
                    discount_id = discount[0]
                    break
            if discount_id is None:
                return
            self.discount_context_menu = tk.Menu(self.discounts_listbox, tearoff=0)
            self.discount_context_menu.add_command(
                label="Delete Discount",
                command=lambda: self.delete_discount(discount_id, discount_name)
            )
            self.discount_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing discount context menu: {e}")

    def delete_discount(self, discount_id, discount_name):
        """Delete the specified discount from the database."""
        try:
            if messagebox.askyesno("Delete Discount", f"Are you sure you want to delete '{discount_name}'?"):
                self.db.cursor.execute("DELETE FROM discounts WHERE discount_id = ?", (discount_id,))
                self.db.conn.commit()
                self.load_discounts()
                messagebox.showinfo("Success", f"Discount '{discount_name}' deleted.")
        except Exception as e:
            print(f"Error deleting discount: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()
