import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from DataBase.Database import Database, Part, PartSold, TransactionDetails

class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Point of Sale System")
        self.root.geometry("800x500")
        
        self.db = Database("pos_system.db")
        self.cart = {}
        self.store_id = 1  # Default store ID; adjust as needed
        self.selected_store_id = tk.IntVar(value=self.store_id)  # Variable to track selected store
        self.selected_employee_id = tk.IntVar()  # Variable to track selected employee
        self.transactions = []  # Store transactions for the selected store
        
        self.create_store_selector()  # Add store selector dropdown
        self.create_employee_selector()  # Add employee selector dropdown
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
        if stores:
            self.selected_store_id.set(stores[0][0])  # Default to the first store

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
        # Add logic to refresh other tabs (e.g., transactions) when implemented
    
    def create_employee_selector(self):
        """Create a dropdown to select the employee."""
        employee_selector_frame = ttk.Frame(self.root)
        employee_selector_frame.pack(fill=tk.X, pady=5)

        employee_label = ttk.Label(employee_selector_frame, text="Select Employee:")
        employee_label.pack(side=tk.LEFT, padx=5)

        self.employee_combobox = ttk.Combobox(employee_selector_frame, textvariable=self.selected_employee_id, state="readonly")
        self.employee_combobox.pack(side=tk.LEFT, padx=5)

        self.load_employee_combobox()  # Populate the employee dropdown

    def load_employee_combobox(self):
        """Load employees into the employee selection combobox."""
        employees = self.db.get_employees()
        employee_options = {employee[0]: f"{employee[1]} {employee[2]} ({employee[3]})" for employee in employees}  # {id: "First Last (Role)"}
        self.employee_combobox["values"] = [f"{emp_id}: {emp_name}" for emp_id, emp_name in employee_options.items()]
        if employees:
            self.selected_employee_id.set(employees[0][0])  # Default to the first employee

    def create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        
        self.sales_frame = ttk.Frame(self.notebook)
        self.inventory_frame = ttk.Frame(self.notebook)
        self.store_frame = ttk.Frame(self.notebook)
        self.transactions_frame = ttk.Frame(self.notebook)
        self.employees_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.sales_frame, text="Sales")
        self.notebook.add(self.inventory_frame, text="Inventory")
        self.notebook.add(self.store_frame, text="Stores")
        self.notebook.add(self.transactions_frame, text="Transactions")
        self.notebook.add(self.employees_frame, text="Employees")
        
        self.notebook.pack(expand=True, fill="both")
        
        self.create_sales_tab()
        self.create_inventory_tab()
        self.create_store_tab()
        self.create_transactions_tab()
        self.create_employees_tab()
    
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
        
        self.add_button = ttk.Button(self.sales_frame, text="Add to Cart", command=self.add_to_cart)
        self.add_button.pack(pady=5)
        
        self.cart_listbox = tk.Listbox(self.sales_frame)
        self.cart_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.cart_listbox.bind("<Button-3>", self.show_cart_context_menu)  # Bind right-click event

        self.total_label = ttk.Label(self.sales_frame, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=5)  # Add a label to display the total
        
        self.checkout_button = ttk.Button(self.sales_frame, text="Checkout", command=self.checkout)
        self.checkout_button.pack(pady=5)
    
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
        
        self.add_store_button = ttk.Button(self.store_frame, text="Add Store", command=self.add_store)
        self.add_store_button.pack(pady=5)
        
        self.store_listbox = tk.Listbox(self.store_frame)
        self.store_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        
        self.generate_report_button = ttk.Button(self.store_frame, text="Generate Sales Report", command=self.generate_sales_report)
        self.generate_report_button.pack(pady=5)
        
        self.load_stores()
    
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
            details = f"Transaction ID: {transaction.transaction_id}\nDate: {transaction.date}\nTotal: ${transaction.total_price:.2f}\nEmployee: {transaction.employee}\nStore: {transaction.store}\n\nParts Sold:\n"
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
            return_transaction_id = self.db.return_by_transaction_id(transaction_id)
            if return_transaction_id:
                messagebox.showinfo("Success", f"Return processed successfully. Return Transaction ID: {return_transaction_id}")
                self.load_transactions()  # Refresh transactions
                self.load_inventory_list()  # Refresh inventory
                self.load_stores()  # Refresh store balances
            else:
                messagebox.showerror("Error", "Failed to process return.")
        except Exception as e:
            print(f"Error processing return: {e}")

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

    def load_items(self):
        """Load items from the database and populate the combobox."""
        parts = self.db.get_parts_by_store(self.store_id)
        self.items = {part.name: (part.price, part.quantity) for part in parts}  # {name: (price, quantity)}
        self.item_combobox["values"] = list(self.items.keys())
    
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
            inventory_value = self.calculate_inventory_value(store_id)  # Calculate inventory value
            self.store_listbox.insert(tk.END, f"{store[1]} - Inventory Value: ${inventory_value:.2f}")

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
            part = self.db.get_part_struct(item_id)
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
        """Update the cart listbox and total label."""
        self.cart_listbox.delete(0, tk.END)
        total = 0
        for item, quantity in self.cart.items():
            total_price = self.items[item][0] * quantity
            total += total_price
            self.cart_listbox.insert(tk.END, f"{item} x{quantity} - ${total_price:.2f}")
        self.total_label.config(text=f"Total: ${total:.2f}")  # Update the total label

    def show_cart_context_menu(self, event):
        """Show a context menu to manage items in the cart."""
        try:
            selected_index = self.cart_listbox.nearest(event.y)  # Get the index of the clicked item
            self.cart_listbox.selection_clear(0, tk.END)
            self.cart_listbox.selection_set(selected_index)  # Highlight the selected item
            selected_item = self.cart_listbox.get(selected_index)  # Get the item text
            item_name = selected_item.split(" x")[0]  # Extract the item name

            self.cart_context_menu = tk.Menu(self.cart_listbox, tearoff=0)
            self.cart_context_menu.add_command(label="Remove Item", command=lambda: self.remove_from_cart(item_name))
            self.cart_context_menu.add_command(label="Change Quantity", command=lambda: self.change_cart_quantity(item_name))
            self.cart_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing cart context menu: {e}")

    def show_inventory_context_menu(self, event):
        """Show a context menu to manage items in the inventory."""
        try:
            selected_index = self.inventory_listbox.nearest(event.y)  # Get the index of the clicked item
            self.inventory_listbox.selection_clear(0, tk.END)
            self.inventory_listbox.selection_set(selected_index)  # Highlight the selected item
            selected_item = self.inventory_listbox.get(selected_index)  # Get the item text
            item_name = selected_item.split(" - ")[0]  # Extract the item name

            self.inventory_context_menu = tk.Menu(self.inventory_listbox, tearoff=0)
            self.inventory_context_menu.add_command(label="Remove Item", command=lambda: self.remove_inventory_item(item_name))
            self.inventory_context_menu.add_command(label="Update Price", command=lambda: self.update_inventory_price(item_name))
            self.inventory_context_menu.add_command(label="Update Stock", command=lambda: self.update_inventory_stock(item_name))
            self.inventory_context_menu.add_command(label="Change Name", command=lambda: self.change_inventory_name(item_name))
            self.inventory_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing inventory context menu: {e}")

    def remove_from_cart(self, item_name):
        """Remove the specified item from the cart."""
        try:
            if item_name in self.cart:
                del self.cart[item_name]  # Remove the item from the cart
                self.update_cart_display()  # Refresh the cart display
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
                        self.update_cart_display()  # Refresh the cart display
                        messagebox.showinfo("Success", f"Updated quantity of '{item_name}' to {new_quantity}.")
                elif new_quantity is not None:
                    messagebox.showerror("Error", "Quantity must be greater than 0.")
        except Exception as e:
            print(f"Error changing item quantity: {e}")

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

    def populate_item_id(self, event):
        """Populate the item ID entry box based on the selected item in the dropdown."""
        selected_item = self.item_var.get()
        if selected_item in self.items:
            part = next((p for p in self.db.get_parts_by_store(self.store_id) if p.name == selected_item), None)
            if part:
                self.item_id_entry.delete(0, tk.END)
                self.item_id_entry.insert(0, part.part_id)

    def checkout(self):
        """Process the checkout and update the database."""
        try:
            # Extract the employee ID from the dropdown value
            employee_id_str = self.employee_combobox.get().split(":")[0].strip()
            employee_id = int(employee_id_str)
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Please select a valid employee.")
            return

        parts_sold = []
        for item, quantity in self.cart.items():
            price = self.items[item][0]
            parts_sold.append(PartSold(name=item, quantity=quantity, unit_price=price, total_price=price * quantity))
        
        # Pass the employee_id to create_purchase
        transaction_id = self.db.create_purchase(parts_sold, self.store_id, employee_id)
        if transaction_id:
            subtotal = sum(part.total_price for part in parts_sold)
            tax_rate = self.db.get_store_tax_rate(self.store_id) or 0.0  # Fetch tax rate for the store, default to 0.0
            tax_amount = round(subtotal * tax_rate, 2)
            total = round(subtotal + tax_amount, 2)
            messagebox.showinfo("Total", f"Subtotal: ${subtotal:.2f}\nTax: ${tax_amount:.2f}\nTotal: ${total:.2f}")
            self.cart.clear()
            self.update_cart_display()
            self.load_items()  # Refresh items after purchase
            self.load_inventory_list()  # Update inventory tab after checkout
            self.load_transactions()  # Update transactions tab after checkout
            self.load_stores()  # Update store tab after checkout
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

if __name__ == "__main__":
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()
