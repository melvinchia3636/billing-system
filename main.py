from ttkbootstrap import Style
import tkinter.ttk as ttk
from tkinter import *
import datetime
import sqlite3
from win32api import GetSystemMetrics
import sys
import ctypes

def enumerate(xs, start=0, step=1):
    for x in xs:
        yield (start, x)
        start += step

class Window(Style):
    def __init__(self, theme='yeti'):
        super().__init__(theme=theme)

        self.configure("Treeview.Heading", font=(None, 11, 'bold'))
        self.configure("TButton", font=(None, 12, 'bold'))
        self.configure("Outline.TButton", font=(None, 13, 'bold'))
        self.configure('checkout.primary.TButton', font=(None, 15, 'bold'))
        self.configure("GrandTotal.TEntry", font=(None, 20, 'bold'))
        self.configure('navbar.primary.TButton', font=(None, 15, 'bold'))
        self.map(
            "TEntry",
            foreground=[("disabled", "#808080")]
        )

        self.master.title('Billing System')
        self.master.attributes('-fullscreen', True)
        self.master.resizable(False, False)

        self.tabs = ttk.Notebook(self.master, name='main')
        self.billing_frame = ttk.Frame(self.tabs, name='billing_frame')
        self.database_frame = Frame(self.tabs, name='database_frame')
        self.statistic_frame = Frame(self.tabs, name='statistic_frame')
        self.account_frame = Frame(self.tabs, name='account_frame')
        self.barcode_frame = Frame(self.tabs, name='barcode_frame')
        self.theme_frame = Frame(self.tabs, name='theme_frame')
        self.receipt_frame = Frame(self.tabs, name='receipt_frame')

        self.billing_container = BillingFrame(self.billing_frame, name='billing_container')

        self.billing_container.pack(padx=20, pady=20)

        self.tabs.add(self.billing_frame, text='Billing')
        self.tabs.add(self.database_frame, text='Database')
        self.tabs.add(self.statistic_frame, text='Statistic')
        self.tabs.add(self.account_frame, text='Account')
        self.tabs.add(self.barcode_frame, text='Barcode')
        self.tabs.add(self.theme_frame, text='Theme')
        self.tabs.add(self.receipt_frame, text='Receipt')
        self.tabs.pack(pady=(20, 0), padx=(10, 0))

        self.master.update()

class BillingFrame(ttk.Frame):
    purchased_data_order = [
        'product_sno_input', 
        'product_code_input', 
        'product_name_input', 
        'quantity_input', 
        'unit_name_input',
        'unit_price_input',
        'tax_rate_input',
        'tax_amount_input',
        'total_price_input'
    ]

    customer_details = [
        ('bill_no', 'Bill No.', 20),
        ('bill_date', 'Bill Date', 20),
        ('customer_name', 'Customer Name', 30),
        ('customer_contact', 'Customer Contact', 20),
        ('personal_officer', 'PO No.', 10)
    ]

    connection = sqlite3.connect('bill_store.db')
    cursor = connection.cursor()

    def __init__(self, master, *args, **kwargs):
        super(BillingFrame, self).__init__(master, *args, **kwargs)

        self.define_widget()
        self.place_widget()
        self.config_treeview()
        self.bind_event()
        self.initialize_entry()

    def define_widget(self):
        functions = [
            ('Save', 'primary.Outline.TButton', None),
            ('Edit', 'primary.Outline.TButton', self.edit),
            ('Delete', 'primary.Outline.TButton', self.delete_purchased),
            ('Print', 'primary.Outline.TButton', None),
            ('Find Product', 'info.Outline.TButton', None),
            ('Bill Record', 'info.Outline.TButton', None),
            ('Clear', 'warning.Outline.TButton', self.clear),
            ('Reset', 'danger.Outline.TButton', self.reset),
            ('Logout', 'danger.Outline.TButton', None),
            ('Exit', 'danger.Outline.TButton', self.exit),
        ]

        self.add_remove = [
            ('product_sno', 'SNO', 10, (self.master.register(lambda P: self.find_product_by_sno(P, self.add_remove_frame)), '%P'), NORMAL, 'xterm'),
            ('product_code', 'Product Code', 15, (self.master.register(lambda P: self.find_product_by_code(P, self.add_remove_frame)), '%P'), NORMAL, 'xterm'),
            ('product_name', 'Product Name', 40, lambda: True, DISABLED, 'arrow'),
            ('quantity', 'Qty', 5, (self.master.register(self.update_amount), '%P'), NORMAL, 'xterm', lambda: self.update_amount(self.quantity_input.get())),
            ('unit_name', 'Unit', 15, lambda: True, DISABLED, 'arrow'),
            ('unit_price', 'Unit Price', 14, lambda: True, DISABLED, 'arrow'),
            ('tax_rate', 'Tax Rate',10, lambda: True, DISABLED, 'arrow'),
            ('tax_amount', 'Tax Amount', 14, lambda: True, DISABLED, 'arrow'),  
            ('total_price', 'Total Price', 14, lambda: True, DISABLED, 'arrow')
        ]

        self.billing_details_frame = ttk.LabelFrame(self, text=' Customer Details ', name='billing_details_frame')
        self.billing_details_container = ttk.Frame(self.billing_details_frame)

        self.customer_details_label = {i+'_label': ttk.Label(self.billing_details_container, text=j, name=i+'_label') for i, j, _ in self.customer_details}
        self.customer_details_input = {i+'_input': ttk.Entry(self.billing_details_container, text=j, name=i+'_input', width=k) for i, j, k in self.customer_details}
        self.__dict__.update({**self.customer_details_label, **self.customer_details_input})

        self.product_list_frame = ttk.LabelFrame(self, text=' Available Products ', name='product_list_frame')
        self.product_list_container = ttk.Frame(self.product_list_frame, name='product_list_container')
        self.product_list = ttk.Treeview(self.product_list_container, selectmode='browse', height=12, name='product_list')
        self.product_list_scrollbar = ttk.Scrollbar(self.product_list_container, orient ="vertical", command = self.product_list.yview)

        self.add_remove_frame = ttk.Frame(self, name='add_remove_frame')
        self.add_button = ttk.Button(self.add_remove_frame, text='Add', width=10, cursor='hand2', command=self.add_item_to_purchase)
        add_remove_label = {i+'_label': ttk.Label(self.add_remove_frame, text=j, name=i+'_label') for i, j, *_ in self.add_remove}
        add_remove_input = {i+'_input': (ttk.Entry if i!='quantity' else ttk.Spinbox)(self.add_remove_frame, **(dict(width=k, name=i+'_input', validate='key', validatecommand=l, state=m, cursor=n, command=o[0] if o else None)|({'from_': 1, 'to': 9999} if i=='quantity' else {}))) for i, _, k, l, m, n, *o in self.add_remove}
        self.__dict__.update({**add_remove_label, **add_remove_input})

        self.purchased_list_frame = ttk.LabelFrame(self, text=' Purchased Products ')
        self.purchased_list_container = ttk.Frame(self.purchased_list_frame)
        self.purchased_list = ttk.Treeview(self.purchased_list_container, selectmode='browse')
        self.purchased_list_scrollbar = ttk.Scrollbar(self.purchased_list_container, orient ="vertical", command = self.purchased_list.yview)

        self.receipt_view_frame = ttk.LabelFrame(self, text=' Receipt Preview ')
        self.receipt_view_container = ttk.Frame(self.receipt_view_frame)
        self.receipt_view = Canvas(self.receipt_view_container, width=380, height=460)

        self.summarize_frame = ttk.Frame(self)
        self.total_label = ttk.Label(self.summarize_frame, text='Total')
        self.tax_label = ttk.Label(self.summarize_frame, text='Tax')
        self.grand_total_label = ttk.Label(self.summarize_frame, text='Grand Total')
        self.total_input = ttk.Entry(self.summarize_frame, font=(None, 20, 'bold'), width=11)
        self.tax_input = ttk.Entry(self.summarize_frame, font=(None, 20, 'bold'), width=11)
        self.grand_total_input = ttk.Entry(self.summarize_frame, font=(None, 30, 'bold'), width=15, justify=CENTER)
        self.checkout_button = ttk.Button(self.summarize_frame, style='checkout.primary.TButton', text='Check Out', cursor='hand2')

        self.functions_frame = ttk.LabelFrame(self, text=' Functions ')
        self.functions_container = ttk.Frame(self.functions_frame)
        self.function_buttons = [ttk.Button(self.functions_container, text=i, name=i.replace(' ', '_').lower(), width=15, style=j, cursor='hand2', command=c) for i, j, c in functions]

    def place_widget(self):
        self.billing_details_frame.grid(row=0, column=0)
        self.billing_details_container.pack(padx=52, pady=20)
        [self.billing_details_container.nametowidget(v[0]+'_label').grid(row=0, column=i, padx=(0, 10)) for i, v in enumerate(self.customer_details, step=2)]
        [self.billing_details_container.nametowidget(v[0]+'_input').grid(row=0, column=i, padx=(0, 30) if (i+1)/2 != 5 else 0) for i, v in enumerate(self.customer_details, start=1, step=2)]

        self.product_list_frame.grid(row=1, column=0, pady=(20, 0), sticky=NS)
        self.product_list_container.pack(padx=20, pady=20)
        self.product_list.grid(row=1, column=0)
        self.product_list_scrollbar.grid(row=1, column=1, sticky='SN')
        self.product_list.configure(yscrollcommand = self.product_list_scrollbar.set)

        [self.add_remove_frame.nametowidget(v[0]+'_label').grid(row=0, column=i, sticky=W, pady=(0, 5), padx=(20, 0) if i else 0) for i, v in enumerate(self.add_remove)]
        [self.add_remove_frame.nametowidget(v[0]+'_input').grid(row=1, column=i, padx=(20, 0) if i else 0) for i, v in enumerate(self.add_remove)]
        self.add_button.grid(row=1, column=9, padx=(20, 0))
        self.add_remove_frame.grid(row=2, column=0, pady=(20, 0))

        self.purchased_list_frame.grid(row=3, column=0, pady=(20, 0), sticky=EW)
        self.purchased_list_container.pack(padx=20, pady=20)
        self.purchased_list.grid(row=0, column=0)
        self.purchased_list_scrollbar.grid(row=0, column=1, sticky='SN')
        self.purchased_list.configure(yscrollcommand = self.purchased_list_scrollbar.set)

        self.receipt_view_frame.grid(row=0, column=1, rowspan=3, padx=(20, 0))
        self.receipt_view_container.pack(padx=20, pady=20)
        self.receipt_view.pack()

        self.summarize_frame.grid(row=3, column=1, pady=(20, 0), padx=(20,0))
        self.total_label.grid(row=0, column=0, sticky=W, pady=(0, 5), padx=(0, 50))
        self.tax_label.grid(row=0, column=1, sticky=W, pady=(0, 5))
        self.total_input.grid(row=1, column=0, padx=(0, 50))
        self.tax_input.grid(row=1, column=1)
        self.grand_total_label.grid(row=2, column=0, columnspan=2, sticky=W, pady=(20, 5))
        self.grand_total_input.grid(row=3, column=0, columnspan=2, sticky='NESW')
        self.checkout_button.grid(row=4, column=0, columnspan=2, pady=(45, 0), sticky='NESW', ipady=18)

        self.functions_frame.grid(row=4, column=0, pady=(20, 0), columnspan=2, sticky=EW)
        self.functions_container.pack(padx=20, pady=20)
        [v.grid(row=0, column=i, padx=10, ipady=10, sticky=EW) for i, v in enumerate(self.function_buttons)]

    def config_treeview(self):
        self.product_list['columns'] = ('SN', 'PC', 'C', 'PN', 'U', 'UP', 'TR', 'AL')
        size = (100, 70, 150, 200, 380, 120, 100, 100, 120)
        text = ('SNO', 'Product Code', 'Category', 'Product Name', 'Unit', 'Unit Price', 'Tax Rate', 'Amount Left',)
        [self.product_list.column(i, anchor=W, minwidth=j, width=j, stretch=NO) for i, j in zip(('#0',)+self.product_list['columns'], size)]
        [self.product_list.heading(i, text=j, anchor=W) for i, j in zip(self.product_list['columns'], text)]
        self.show_product_list()

        self.purchased_list['columns'] = ('SN', 'PC', 'PN', 'A', 'U', 'UP', 'TR', 'TT', 'TA')
        size = (0, 70, 150, 535, 50, 120, 100, 100, 100, 120)
        text = ('SNO', 'Product Code', 'Product Name', 'Qty', 'Unit', 'Unit Price', 'Tax Rate', 'Tax Amt', 'Total Price')
        [self.purchased_list.column(i, anchor=W, minwidth=j, width=j, stretch=NO) for i, j in zip(('#0',)+self.purchased_list['columns'], size)]
        [self.purchased_list.heading(i, text=j, anchor=W) for i, j in zip(self.purchased_list['columns'], text)]

    def bind_event(self):
        self.product_list.bind('<<TreeviewSelect>>', self.product_list_select_callback)
        self.quantity_input.bind('<FocusIn>', self.select_all)
        self.product_sno_input.bind('<FocusIn>', self.select_all)
        self.quantity_input.bind('<FocusOut>', lambda e: e.widget.select_clear())
        self.product_sno_input.bind('<FocusOut>', lambda e: e.widget.select_clear())

    def initialize_entry(self):
        self.bill_no_input.insert(0, 'RC210000001')
        self.bill_date_input.insert(0, datetime.datetime.now().strftime('%d / %m / %Y'))

        self.total_input.insert(0, '0.00')
        self.tax_input.insert(0, '0.00')
        self.grand_total_input.insert(0, '0.00')

    def show_product_list(self):
        categories = self.cursor.execute('SELECT DISTINCT category FROM products').fetchall()
        for i, v in enumerate(categories):
            self.product_list.insert('', 'end', v[0], text=v[0])
            products = self.cursor.execute('SELECT * FROM products WHERE category="{}"'.format(v[0])).fetchall()
            for v in products:
                self.product_list.insert(v[2], 'end', values=v)

    def clear_add_remove_value(self, master):
        self.change_add_remove_state(NORMAL)
        [master.nametowidget(i).delete(0, 'end') if 'quantity' not in i else master.nametowidget(i).set('') for i in self.purchased_data_order]

    def insert_add_remove_value(self, master, selection, include_category=True, insert_procuct_code=True):
        self.clear_add_remove_value(master)

        self.product_sno_input.insert(0, selection[0])
        if insert_procuct_code: self.product_code_input.insert(0, selection[1])
        self.product_name_input.insert(0, selection[3 if include_category else 2])
        self.unit_name_input.insert(0, selection[4])
        self.unit_price_input.insert(0, selection[5])
        self.tax_rate_input.insert(0, selection[6])
        self.tax_amount_input.insert(0, round(float(selection[6])*float(selection[5])/100, 2))
        self.total_price_input.insert(0, round(float(selection[5])+float(self.tax_amount_input.get()), 2))
        self.quantity_input.set(1)

        self.change_add_remove_state(DISABLED)

    def change_add_remove_state(self, state):
        self.product_name_input.config(state=state)
        self.unit_name_input.config(state=state)
        self.unit_price_input.config(state=state)
        self.tax_rate_input.config(state=state)
        self.tax_amount_input.config(state=state)
        self.total_price_input.config(state=state)
        
    def product_list_select_callback(self, e):
        selection = self.product_list.item(self.product_list.selection()[0])['values']
        if len(selection) == 8:
            self.product_sno_input.delete(0, 'end')
            self.product_sno_input.insert(0, selection[0])

    def select_all(self, e):
        e.widget.select_range(0, 'end')
        e.widget.icursor('end')

    def add_item_to_purchase(self):
        if all(self.add_remove_frame.nametowidget(i).get() for i in self.purchased_data_order):
            self.purchased_list.insert(parent='', index='end', values=[self.add_remove_frame.nametowidget(i).get() for i in self.purchased_data_order])
            self.update_summary()
            self.change_add_remove_state(NORMAL)
            [[self.add_remove_frame.nametowidget(i).delete(0, 'end')] for i in self.purchased_data_order]
            self.change_add_remove_state(DISABLED)

    def update_summary(self):
        total, tax = list(map(
            lambda i: round(sum(i), 2), 
            zip(*[
                (round(float(j[0])*float(j[2]), 2), 
                round(float(j[4]), 2)) 
                for i in self.purchased_list.get_children() 
                if (j:=self.purchased_list.item(i)['values'][3:])
            ])
        ))
        self.total_input.delete(0, 'end')
        self.tax_input.delete(0, 'end')
        self.grand_total_input.delete(0, 'end')
        self.total_input.insert(0, total)
        self.tax_input.insert(0, tax)
        self.grand_total_input.insert(0, round(float(self.total_input.get())+float(self.tax_input.get()), 2))

    def update_amount(self, P):
        if P=='': return True
        if not (P.count('.') <= 1 and P.replace('.', '').isdigit() and float(P)):
            return False
        self.change_add_remove_state(NORMAL)
        try:
            self.tax_amount_input.delete(0, 'end')
            self.total_price_input.delete(0, 'end')
            self.tax_amount_input.insert(0, round(float(P)*float(self.tax_rate_input.get())*float(self.unit_price_input.get())/100, 2))
            self.total_price_input.insert(0, round(float(self.unit_price_input.get())*float(P)+float(self.tax_amount_input.get()), 2))
        except: pass
        self.change_add_remove_state(DISABLED)
        return True

    def delete_summary(self, total, tax):
        ctotal = float(self.total_input.get())
        ctax = float(self.tax_input.get())
        self.total_input.delete(0, 'end')
        self.total_input.insert(0, abs(round(ctotal-total, 2)))
        self.tax_input.delete(0, 'end')
        self.tax_input.insert(0, abs(round(ctax-tax, 2)))
        self.grand_total_input.delete(0, 'end')
        self.grand_total_input.insert(0, abs(round(float(self.total_input.get())+float(self.tax_input.get()), 2)))

    def delete_purchased(self):
        if self.purchased_list.selection():
            selection = self.purchased_list.item(self.purchased_list.selection()[0])['values']
            self.purchased_list.delete(self.purchased_list.selection()[0])
            self.delete_summary(float(selection[3])*float(selection[5]), float(selection[7]))

    def find_product_by_code(self, P, master=None):
        try: 
            selection = self.cursor.execute(f'SELECT * FROM products WHERE product_code="{P}"').fetchone()
            if selection: self.insert_add_remove_value(master, selection, insert_procuct_code=False)
        except: pass
        return True

    def find_product_by_sno(self, P, master=None):
        try: 
            selection = self.cursor.execute(f'SELECT * FROM products WHERE id={P}').fetchone()
            if selection: self.insert_add_remove_value(master, selection)
        except: pass
        return True

    def clear(self):
        for i in self.purchased_list.get_children():
            self.purchased_list.delete(i)
        self.total_input.delete(0, 'end')
        self.tax_input.delete(0, 'end')
        self.grand_total_input.delete(0, 'end')
        self.total_input.insert(0, '0.00')
        self.tax_input.insert(0, '0.00')
        self.grand_total_input.insert(0, '0.00')
        
    def reset(self):
        self.clear()
        self.customer_name_input.delete(0, 'end')
        self.customer_contact_input.delete(0, 'end')
        self.personal_officer_input.delete(0, 'end')

    def exit(self):
        self.master.destroy()
        sys.exit()

    def edit(self):
        if self.purchased_list.selection():
            selection_id = self.purchased_list.selection()[0]
            selection_content = self.purchased_list.item(selection_id)['values']
            self.editwindow = EditWindow(self, selection_content[0], selection_id)
            self.editwindow.mainloop()

class EditWindow(Toplevel, BillingFrame):
    def __init__(self, main_window, selection_id, treeview_id):
        super().__init__()

        self.title('Edit Item')

        self.main_window = main_window
        self.data_id = selection_id
        self.treeview_id = treeview_id
        
        self.define_widget()
        self.place_widget()
        self.product_sno_input.delete(0, 'end')
        self.product_sno_input.insert(0, self.data_id)
        self.setActive()
        self.update()
        
        x_left = int(self.winfo_screenwidth()/2 - self.winfo_width()/2)
        y_top = int(self.winfo_screenheight()/2 - self.winfo_height()/2)
        self.geometry(f'+{x_left}+{y_top}')

    def setActive(self):
        self.lift()
        self.focus_force()
        self.grab_set()
        self.grab_release()

    def define_widget(self):
        self.widget_container_frame = Frame(self)
        self.widget_container = Frame(self.widget_container_frame)
        self.button_container = Frame(self.widget_container)

        edit = [
            ('product_sno', 'SNO', 10, (self.register(lambda P: self.find_product_by_sno(P, self.widget_container)), '%P'), NORMAL, 'xterm'),
            ('product_code', 'Product Code', 15, (self.master.register(lambda P: self.find_product_by_code(P, self.widget_container)), '%P'), NORMAL, 'xterm'),
            ('product_name', 'Product Name', 40, lambda: True, DISABLED, 'arrow'),
            ('quantity', 'Qty', 5, (self.register(self.update_amount), '%P'), NORMAL, 'xterm', lambda: self.update_amount(self.quantity_input.get())),
            ('unit_name', 'Unit', 15, lambda: True, DISABLED, 'arrow'),
            ('unit_price', 'Unit Price', 14, lambda: True, DISABLED, 'arrow'),
            ('tax_rate', 'Tax Rate',10, lambda: True, DISABLED, 'arrow'),
            ('tax_amount', 'Tax Amount', 14, lambda: True, DISABLED, 'arrow'),  
            ('total_price', 'Total Price', 14, lambda: True, DISABLED, 'arrow')
        ]

        edit_label = {i+'_label': ttk.Label(self.widget_container, text=j, name=i+'_label') for i, j, *_ in edit}
        edit_input = {i+'_input': (ttk.Entry if i!='quantity' else ttk.Spinbox)(self.widget_container, **(dict(width=k, name=i+'_input', validate='key', validatecommand=l, state=m, cursor=n, command=o[0] if o else None)|({'from_': 1, 'to': 9999} if i=='quantity' else {}))) for i, _, k, l, m, n, *o in edit}
        self.__dict__.update({**edit_label, **edit_input})

        self.reset_button = ttk.Button(self.widget_container, text='Reset', style='danger.Outline.TButton', width=10, command=lambda: self.insert_add_remove_value(self.widget_container, self.original_data))
        self.cancel_button = ttk.Button(self.button_container, text='Cancel', style='primary.Outline.TButton', width=10, command=self.destroy)
        self.save_button = ttk.Button(self.button_container, text='Save', style='primary.TButton', width=10, command=self.save_and_close)

    def place_widget(self):
        self.widget_container_frame.pack()
        self.widget_container.pack(padx=20, pady=20)

        order = (
            'product_sno', 
            'product_code',
            'product_name',
            'quantity',
            'unit_name',
            'unit_price',
            'tax_rate',
            'tax_amount',
            'total_price'
        )

        [self.widget_container.nametowidget(v+'_label').grid(row=i, column=0, sticky=W, pady=(0, 15)) for i, v, in enumerate(order)]
        [self.widget_container.nametowidget(v+'_input').grid(row=i, column=1, padx=(20, 0), pady=(0, 15), sticky=W) for i, v, in enumerate(order)]

        self.button_container.grid(row=9, column=1, sticky=E, pady=(20, 0))
        self.reset_button.grid(row=9, column=0, sticky=W, pady=(20, 0))
        self.cancel_button.grid(row=0, column=1, sticky=E)
        self.save_button.grid(row=0, column=2, sticky=E, padx=(10, 0))

    def save_and_close(self):
        if all(self.widget_container.nametowidget(i).get() for i in self.purchased_data_order):
            self.main_window.purchased_list.delete(self.treeview_id)
            self.main_window.purchased_list.insert(parent='', index=int(self.treeview_id[1:]), values=[self.widget_container.nametowidget(i).get() for i in self.main_window.purchased_data_order])
            self.main_window.update_summary()
            self.destroy()

if __name__ == '__main__':
    width, height = GetSystemMetrics(0), GetSystemMetrics(1)
    if width < 1920 and height < 1080:
        ctypes.windll.user32.MessageBoxW(0, "This program required screen resolution not less than 1920x1080 to run properly", "Higher Resolution Required", 0x10)
        sys.exit()
    root = Window()
    root.master.mainloop()