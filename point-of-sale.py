import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from DataBase.Database import Database

class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Point of Sale System")
        self.root.geometry("800x500")
        
        self.db = Database("pos_system.db")
        self.cart = {}
        
        self.create_tabs()
        self.load_items()
    
    def create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        
        self.sales_frame = ttk.Frame(self.notebook)
        self.inventory_frame = ttk.Frame(self.notebook)
        self.store_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.sales_frame, text="Sales")
        self.notebook.add(self.inventory_frame, text="Inventory")
        self.notebook.add(self.store_frame, text="Stores")
        
        self.notebook.pack(expand=True, fill="both")
        
        self.create_sales_tab()
        self.create_inventory_tab()
        self.create_store_tab()
    
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
        
        self.load_stores()
    
    def load_items(self):
        parts = self.db.get_parts()
        self.items = {part[1]: (part[2], part[4]) for part in parts}  # {name: (price, quantity)}
        self.item_combobox["values"] = list(self.items.keys())
    
    def load_inventory_list(self):
        self.inventory_listbox.delete(0, tk.END)
        parts = self.db.get_parts()
        for part in parts:
            self.inventory_listbox.insert(tk.END, f"{part[1]} - ${part[2]:.2f} - {part[4]} in stock")
    
    def add_inventory_item(self):
        name = self.item_name_entry.get()
        price = self.item_price_entry.get()
        quantity = self.item_quantity_entry.get()
        
        if name and price.replace('.', '', 1).isdigit() and quantity.isdigit():
            price = float(price)
            quantity = int(quantity)
            self.db.add_part_to_store(name, price, 1, quantity)  # Assuming store_id is 1
            messagebox.showinfo("Success", "Item added successfully!")
            self.load_inventory_list()
        else:
            messagebox.showerror("Error", "Please enter valid item details.")
    
    def add_store(self):
        store_name = self.store_name_entry.get()
        if store_name:
            self.db.add_store(store_name)
            messagebox.showinfo("Success", "Store added successfully!")
            self.load_stores()
        else:
            messagebox.showerror("Error", "Please enter a store name.")
    
    def load_stores(self):
        self.store_listbox.delete(0, tk.END)
        stores = self.db.get_stores()
        for store in stores:
            self.store_listbox.insert(tk.END, f"{store[1]} - Balance: ${store[2]:.2f}")

    def add_inventory_item(self):
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
        
        store_id = 1  # Assuming store ID 1 for now; adjust logic as necessary
        pno = self.db.add_part_to_store(name, price, store_id, quantity)
        
        if pno:
            messagebox.showinfo("Success", f"Item '{name}' added with quantity {quantity} at ${price:.2f}.")
            self.load_inventory_list()
            self.load_items()  # Update sales items list
            self.item_name_entry.delete(0, tk.END)
            self.item_price_entry.delete(0, tk.END)
            self.item_quantity_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Failed to add item to inventory.")

    def add_to_cart(self):
        selected_item = self.item_var.get()
        item_id = self.item_id_entry.get()
        quantity = self.quantity_entry.get()
        
        if not quantity.isdigit():
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return
        
        quantity = int(quantity)
        
        if selected_item:
            # Add item using dropdown selection
            available_quantity = self.items[selected_item][1]
            if quantity > available_quantity:
                messagebox.showerror("Error", "Not enough stock available.")
                return
            if selected_item in self.cart:
                self.cart[selected_item] += quantity
            else:
                self.cart[selected_item] = quantity
        elif item_id.isdigit():
            # Add item using item ID
            item_id = int(item_id)
            parts = self.db.get_parts()
            item = next((part for part in parts if part[0] == item_id), None)
            if not item:
                messagebox.showerror("Error", "Item ID not found.")
                return
            item_name, price, available_quantity = item[1], item[2], item[4]
            if quantity > available_quantity:
                messagebox.showerror("Error", "Not enough stock available.")
                return
            if item_name in self.cart:
                self.cart[item_name] += quantity
            else:
                self.cart[item_name] = quantity
            self.items[item_name] = (price, available_quantity)  # Ensure item is in the items dictionary
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
            self.cart_context_menu = tk.Menu(self.cart_listbox, tearoff=0)
            self.cart_context_menu.add_command(label="Remove Item", command=lambda: self.remove_from_cart(event))
            self.cart_context_menu.add_command(label="Change Quantity", command=lambda: self.change_cart_quantity(event))
            self.cart_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing context menu: {e}")

    def change_cart_quantity(self, event):
        """Change the quantity of the selected item in the cart."""
        try:
            selected_index = self.cart_listbox.nearest(event.y)  # Get the index of the clicked item
            selected_item = self.cart_listbox.get(selected_index)  # Get the item text
            item_name = selected_item.split(" x")[0]  # Extract the item name
            
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

    def remove_from_cart(self, event):
        """Remove the selected item from the cart."""
        try:
            selected_index = self.cart_listbox.nearest(event.y)  # Get the index of the clicked item
            selected_item = self.cart_listbox.get(selected_index)  # Get the item text
            item_name = selected_item.split(" x")[0]  # Extract the item name
            if item_name in self.cart:
                del self.cart[item_name]  # Remove the item from the cart
                self.update_cart_display()  # Refresh the cart display
                messagebox.showinfo("Success", f"Removed '{item_name}' from the cart.")
        except Exception as e:
            print(f"Error removing item from cart: {e}")

    def checkout(self):
        total = sum(self.items[item][0] * quantity for item, quantity in self.cart.items())
        
        for item, quantity in self.cart.items():
            self.db.purchase_part(item, 1, quantity)  # Assuming store_id is 1
        
        messagebox.showinfo("Total", f"Total Amount: ${total:.2f}")
        self.cart.clear()
        self.update_cart_display()
        self.load_items()  # Refresh items after purchase
        self.load_inventory_list()  # Update inventory tab after checkout

    def show_inventory_context_menu(self, event):
        """Show a context menu to manage items in the inventory."""
        try:
            self.inventory_context_menu = tk.Menu(self.inventory_listbox, tearoff=0)
            self.inventory_context_menu.add_command(label="Remove Item", command=lambda: self.remove_inventory_item(event))
            self.inventory_context_menu.add_command(label="Update Price", command=lambda: self.update_inventory_price(event))
            self.inventory_context_menu.add_command(label="Update Stock", command=lambda: self.update_inventory_stock(event))
            self.inventory_context_menu.add_command(label="Change Name", command=lambda: self.change_inventory_name(event))
            self.inventory_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing inventory context menu: {e}")

    def remove_inventory_item(self, event):
        """Remove the selected item from the inventory."""
        try:
            selected_index = self.inventory_listbox.nearest(event.y)
            selected_item = self.inventory_listbox.get(selected_index)
            item_name = selected_item.split(" - ")[0]  # Extract the item name
            self.db.cursor.execute("DELETE FROM parts WHERE name = ?", (item_name,))
            self.db.conn.commit()
            self.load_inventory_list()
            messagebox.showinfo("Success", f"Removed '{item_name}' from inventory.")
        except Exception as e:
            print(f"Error removing inventory item: {e}")

    def update_inventory_price(self, event):
        """Update the price of the selected item in the inventory."""
        try:
            selected_index = self.inventory_listbox.nearest(event.y)
            selected_item = self.inventory_listbox.get(selected_index)
            item_name = selected_item.split(" - ")[0]  # Extract the item name
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

    def update_inventory_stock(self, event):
        """Update the stock of the selected item in the inventory."""
        try:
            selected_index = self.inventory_listbox.nearest(event.y)
            selected_item = self.inventory_listbox.get(selected_index)
            item_name = selected_item.split(" - ")[0]  # Extract the item name
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

    def change_inventory_name(self, event):
        """Change the name of the selected item in the inventory."""
        try:
            selected_index = self.inventory_listbox.nearest(event.y)
            selected_item = self.inventory_listbox.get(selected_index)
            item_name = selected_item.split(" - ")[0]  # Extract the item name
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
            # Assuming `get_parts` returns a list of tuples (pno, name, price, store_id, quantity)
            parts = self.db.get_parts()
            for part in parts:
                if part[1] == selected_item:  # Match by item name
                    self.item_id_entry.delete(0, tk.END)
                    self.item_id_entry.insert(0, part[0])  # Populate with item ID (pno)
                    break

if __name__ == "__main__":
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()
