import tkinter as tk
from tkinter import ttk, messagebox
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
        
        self.quantity_label = ttk.Label(self.sales_frame, text="Quantity:")
        self.quantity_label.pack(pady=5)
        
        self.quantity_entry = ttk.Entry(self.sales_frame)
        self.quantity_entry.pack(pady=5)
        
        self.add_button = ttk.Button(self.sales_frame, text="Add to Cart", command=self.add_to_cart)
        self.add_button.pack(pady=5)
        
        self.cart_listbox = tk.Listbox(self.sales_frame)
        self.cart_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        
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
        quantity = self.quantity_entry.get()
        
        if selected_item and quantity.isdigit():
            quantity = int(quantity)
            available_quantity = self.items[selected_item][1]
            
            if quantity > available_quantity:
                messagebox.showerror("Error", "Not enough stock available.")
                return
            
            if selected_item in self.cart:
                self.cart[selected_item] += quantity
            else:
                self.cart[selected_item] = quantity
            
            self.update_cart_display()
        else:
            messagebox.showerror("Error", "Please select an item and enter a valid quantity.")

    def update_cart_display(self):
        self.cart_listbox.delete(0, tk.END)
        for item, quantity in self.cart.items():
            total_price = self.items[item][0] * quantity
            self.cart_listbox.insert(tk.END, f"{item} x{quantity} - ${total_price:.2f}")


    def checkout(self):
        total = sum(self.items[item][0] * quantity for item, quantity in self.cart.items())
        
        for item, quantity in self.cart.items():
            self.db.purchase_part(item, 1, quantity)  # Assuming store_id is 1
        
        messagebox.showinfo("Total", f"Total Amount: ${total:.2f}")
        self.cart.clear()
        self.update_cart_display()
        self.load_items()  # Refresh items after purchase




if __name__ == "__main__":
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()
