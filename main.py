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
    def __init__(self, theme='navy_blue'):
        super().__init__(theme=theme, themes_file='themes.json')

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
        self.theme_settings(theme, {"TNotebook.Tab": {"configure": {"padding": [40, 10]}}})

        self.master.title('Billing System')
        self.master.geometry('1920x1080')
        self.master.attributes('-fullscreen', True)
        self.master.resizable(False, False)

        self.tabs = ttk.Notebook(self.master, name='main')
        self.billing_frm = Frame(self.tabs, name='billing_frm')
        self.database_frm = Frame(self.tabs, name='database_frm')
        self.statistic_frm = Frame(self.tabs, name='statistic_frm')
        self.account_frm = Frame(self.tabs, name='account_frm')
        self.barcode_frm = Frame(self.tabs, name='barcode_frm')
        self.theme_frm = Frame(self.tabs, name='theme_frm')
        self.receipt_frm = Frame(self.tabs, name='receipt_frm')

        self.billing_container = BillingFrame(self.billing_frm, name='billing_container')
        self.database_container = DatabaseFrame(self.database_frm, name='database_container')

        self.billing_container.pack(padx=20, pady=20, fill=BOTH, expand=True)
        self.database_container.pack(padx=20, pady=20, fill=BOTH, expand=True)

        self.tabs.add(self.billing_frm, text='Billing')
        self.tabs.add(self.database_frm, text='Database')
        self.tabs.add(self.statistic_frm, text='Statistic')
        self.tabs.add(self.account_frm, text='Account')
        self.tabs.add(self.barcode_frm, text='Barcode')
        self.tabs.add(self.theme_frm, text='Theme')
        self.tabs.add(self.receipt_frm, text='Receipt')
        self.tabs.pack(pady=10, padx=10, fill=BOTH, expand=True)

        self.master.update()
        global width, height
        width, height = self.master.winfo_width(), self.master.winfo_height()

        self.billing_container.execute()
        self.database_container.execute()

class BillingFrame(Frame):
    purchased_data_order = [
        'product_sno', 
        'product_code', 
        'product_name', 
        'quantity', 
        'unit_name',
        'unit_price',
        'tax_rate',
        'tax_amount',
        'total_price'
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

    def execute(self):
        self.define_widget()
        self.config_treeview()
        self.place_widget()
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
            ('product_sno', 'SNO', 1, (self.master.register(lambda P: self.find_product_by_sno(P, self.add_remove_container)), '%P'), NORMAL, 'xterm'),
            ('product_code', 'Product Code', 1, (self.master.register(lambda P: self.find_product_by_code(P, self.add_remove_container)), '%P'), NORMAL, 'xterm'),
            ('product_name', 'Product Name', 1, lambda: True, DISABLED, 'arrow'),
            ('quantity', 'Qty', 1, (self.master.register(self.update_amount), '%P'), NORMAL, 'xterm', lambda: self.update_amount(self.quantity_input.get())),
            ('unit_name', 'Unit', 1, lambda: True, DISABLED, 'arrow'),
            ('unit_price', 'Unit Price', 1, lambda: True, DISABLED, 'arrow'),
            ('tax_rate', 'Tax Rate',1, lambda: True, DISABLED, 'arrow'),
            ('tax_amount', 'Tax Amount', 1, lambda: True, DISABLED, 'arrow'),  
            ('total_price', 'Total Price', 1, lambda: True, DISABLED, 'arrow')
        ]

        self.top_frm = Frame(self)
        self.left_frm = Frame(self.top_frm)
        self.right_frm = Frame(self.top_frm)

        self.billing_details_frm = ttk.Labelframe(self.left_frm, text=' Customer Details ', name='billing_details_frm')
        self.billing_details_container = Frame(self.billing_details_frm)
        self.billing_details_input_container = [Frame(self.billing_details_container, name=i+'_container') for i, *_ in self.customer_details]

        self.customer_details_lb = {i+'_lb': ttk.Label(self.billing_details_input_container[c], text=j, name=i+'_lb') for c, *v in enumerate(self.customer_details) for i, j, k in v}
        self.customer_details_input = {i+'_input': ttk.Entry(self.billing_details_input_container[c], text=j, name=i+'_input', width=k) for c, *v in enumerate(self.customer_details) for i, j, k in v}
        self.__dict__.update({**self.customer_details_lb, **self.customer_details_input})

        self.product_lst_frm = ttk.Labelframe(self.left_frm, text=' Available Products ', name='product_lst_frm')
        self.product_lst_container = Frame(self.product_lst_frm, name='product_lst_container')
        self.product_lst = ttk.Treeview(self.product_lst_container, selectmode='browse', name='product_lst')
        self.product_lst_scrollbar = ttk.Scrollbar(self.product_lst_container, orient ="vertical", command = self.product_lst.yview)

        self.add_remove_frm = Frame(self.left_frm, name='add_remove_frm')
        self.add_remove_container = Frame(self.add_remove_frm, name='add_remove_container')
        self.add_remove_widget_container = [Frame(self.add_remove_container, name=i+'_container') for i, *_ in self.add_remove+['add_btn']]

        self.add_btn_top_dummy = ttk.Label(self.add_remove_widget_container[-1], text=' ')
        self.add_btn = ttk.Button(self.add_remove_widget_container[-1], text='Add', width=10, cursor='hand2', command=self.add_item_to_purchase)
        add_remove_lb = {i+'_lb': ttk.Label(self.add_remove_widget_container[c], text=j, name=i+'_lb') for c, *v in enumerate(self.add_remove) for i, j, *_ in v}
        add_remove_input = {i+'_input': (ttk.Entry if i!='quantity' else ttk.Spinbox)(self.add_remove_widget_container[c], **(dict(width=k, name=i+'_input', validate='key', validatecommand=l, state=m, cursor=n, command=o[0] if o else None)|({'from_': 1, 'to': 9999} if i=='quantity' else {}))) for c, *v in enumerate(self.add_remove) for i, _, k, l, m, n, *o in v}
        self.__dict__.update({**add_remove_lb, **add_remove_input})

        self.purchased_lst_frm = ttk.Labelframe(self.left_frm, text=' Purchased Products ')
        self.purchased_lst_container = Frame(self.purchased_lst_frm)
        self.purchased_lst = ttk.Treeview(self.purchased_lst_container, selectmode='browse')
        self.purchased_lst_scrollbar = ttk.Scrollbar(self.purchased_lst_container, orient ="vertical", command = self.purchased_lst.yview)

        self.receipt_view_frm = ttk.Labelframe(self.right_frm, text=' Receipt Preview ')
        self.receipt_view_container = Frame(self.receipt_view_frm)
        self.receipt_view = Canvas(self.receipt_view_container)

        self.summarize_frm_container = Frame(self.right_frm)
        self.summarize_frm = Frame(self.summarize_frm_container)
        self.summarize_top_frm = Frame(self.summarize_frm)

        self.total_frm = Frame(self.summarize_top_frm)
        self.total_lb = ttk.Label(self.total_frm, text='Total')
        self.total_input = ttk.Entry(self.total_frm, font=(None, 20, 'bold'), width=0)

        self.tax_frm = Frame(self.summarize_top_frm)
        self.tax_lb = ttk.Label(self.tax_frm, text='Tax')
        self.tax_input = ttk.Entry(self.tax_frm, font=(None, 20, 'bold'), width=0)
        
        self.grand_total_lb = ttk.Label(self.summarize_frm, text='Grand Total')
        self.grand_total_input = ttk.Entry(self.summarize_frm, font=(None, 30, 'bold'), justify=CENTER)
        self.checkout_btn = ttk.Button(self.summarize_frm, style='checkout.primary.TButton', text='Check Out', cursor='hand2')

        self.functions_frm = ttk.Labelframe(self, text=' Functions ')
        self.functions_container = Frame(self.functions_frm)
        self.function_btns = [ttk.Button(self.functions_container, text=i, name=i.replace(' ', '_').lower(), style=j, cursor='hand2', command=c, padding=(0, 0)) for i, j, c in functions]

    def place_widget(self):
        [i.pack(side=LEFT, expand=True, fill=X, padx=10) for i in self.billing_details_input_container]
        [self.billing_details_container.nametowidget('{0}_container.{0}_lb'.format(i)).pack(side=TOP, expand=True, fill=X, pady=(0, 5)) for i, j, k in self.customer_details]
        [self.billing_details_container.nametowidget('{0}_container.{0}_input'.format(i)).pack(side=TOP, expand=True, fill=X) for i, j, k in self.customer_details]
        self.billing_details_container.pack(padx=20, pady=(10, 20), expand=True, fill=X)

        self.product_lst.grid(row=1, column=0)
        self.product_lst_scrollbar.grid(row=1, column=1, sticky='SN')
        self.product_lst_container.pack(padx=20, pady=20)

        [i.pack(side=LEFT, expand=True, fill=BOTH, padx=10) for i in self.add_remove_widget_container]
        [self.add_remove_container.nametowidget('{0}_container.{0}_lb'.format(v[0])).pack(side=TOP, expand=True, fill=X, pady=(0, 5)) for i, v in enumerate(self.add_remove)]
        [self.add_remove_container.nametowidget('{0}_container.{0}_input'.format(v[0])).pack(side=TOP, expand=True, fill=X) for i, v in enumerate(self.add_remove)]
        self.add_btn_top_dummy.pack(side=TOP, fill=BOTH, pady=(0, 5))
        self.add_btn.pack(side=BOTTOM, fill=BOTH)
        self.add_remove_container.pack(expand=True, fill=X)

        self.purchased_lst.grid(row=0, column=0)
        self.purchased_lst_scrollbar.grid(row=0, column=1, sticky='SN')
        self.purchased_lst_container.pack(padx=20, pady=20)

        self.receipt_view.pack(fill=Y, expand=True)
        self.receipt_view_container.pack(padx=20, pady=20, fill=BOTH, expand=True)

        self.summarize_top_frm.pack(fill=BOTH, expand=True)
        self.total_frm.pack(fill=BOTH, expand=True, side=LEFT)
        self.total_lb.pack(expand=True, fill=X)
        self.total_input.pack(expand=True, fill=BOTH)
        self.tax_frm.pack(fill=BOTH, expand=True, side=LEFT, padx=(20, 0))
        self.tax_lb.pack(expand=True, fill=X)
        self.tax_input.pack(expand=True, fill=BOTH)
        self.grand_total_lb.pack(expand=True, fill=X)
        self.grand_total_input.pack(expand=True, fill=BOTH, pady=(0, 20))
        self.checkout_btn.pack(expand=True, fill=BOTH)

        [v.pack(fill=BOTH, expand=True, side=LEFT, padx=10) for i, v in enumerate(self.function_btns)]
        self.functions_container.pack(padx=20, pady=20, fill=BOTH, expand=True)

        self.top_frm.pack(fill=BOTH, expand=True, side=TOP)
        self.left_frm.pack(fill=BOTH, expand=True, side=LEFT)
        self.right_frm.pack(fill=BOTH, expand=True, side=RIGHT, padx=(20, 0))
        self.billing_details_frm.pack(fill=BOTH, expand=True, side=TOP)
        self.receipt_view_frm.pack(fill=BOTH, expand=True)
        self.summarize_frm_container.pack(fill=BOTH, expand=True, pady=(20, 0))
        self.summarize_frm.pack(expand=True, fill=Y)
        self.product_lst_frm.pack(fill=BOTH, expand=True, side=TOP, pady=(20, 0))
        self.add_remove_frm.pack(fill=BOTH, expand=True, side=TOP, pady=(20, 0))
        self.purchased_lst_frm.pack(fill=BOTH, expand=True, side=TOP, pady=(20, 0))
        self.functions_frm.pack(fill=BOTH, expand=True, side=BOTTOM, pady=(20, 0))

    def config_treeview(self):
        self.product_lst['columns'] = ('SN', 'PC', 'C', 'PN', 'U', 'UP', 'TR', 'AL')
        size = tuple(map(lambda i: int(i/1920*width), (100, 70, 150, 200, 380, 120, 100, 100, 120)))
        text = ('SNO', 'Product Code', 'Category', 'Product Name', 'Unit', 'Unit Price', 'Tax Rate', 'Amount Left',)
        [self.product_lst.column(i, anchor=W, minwidth=10, width=j, stretch=NO) for i, j in zip(('#0',)+self.product_lst['columns'], size)]
        [self.product_lst.heading(i, text=j, anchor=W) for i, j in zip(self.product_lst['columns'], text)]
        self.show_product_lst()

        self.purchased_lst['columns'] = ('SN', 'PC', 'PN', 'A', 'U', 'UP', 'TR', 'TT', 'TA')
        size = tuple(map(lambda i: int(i/1920*width), (0, 70, 150, 535, 50, 120, 100, 100, 100, 120)))
        text = ('SNO', 'Product Code', 'Product Name', 'Qty', 'Unit', 'Unit Price', 'Tax Rate', 'Tax Amt', 'Total Price')
        [self.purchased_lst.column(i, anchor=W, minwidth=10, width=j, stretch=NO) for i, j in zip(('#0',)+self.purchased_lst['columns'], size)]
        [self.purchased_lst.heading(i, text=j, anchor=W) for i, j in zip(self.purchased_lst['columns'], text)]

    def bind_event(self):
        self.product_lst.bind('<<TreeviewSelect>>', self.product_lst_select_callback)
        self.quantity_input.bind('<FocusIn>', self.select_all)
        self.product_sno_input.bind('<FocusIn>', self.select_all)
        self.quantity_input.bind('<FocusOut>', lambda e: e.widget.select_clear())
        self.product_sno_input.bind('<FocusOut>', lambda e: e.widget.select_clear())

        self.product_lst.configure(yscrollcommand=self.product_lst_scrollbar.set)
        self.purchased_lst.configure(yscrollcommand=self.purchased_lst_scrollbar.set)

    def initialize_entry(self):
        self.bill_no_input.insert(0, 'RC210000001')
        self.bill_date_input.insert(0, datetime.datetime.now().strftime('%d / %m / %Y'))

        self.total_input.insert(0, '0.00')
        self.tax_input.insert(0, '0.00')
        self.grand_total_input.insert(0, '0.00')

    def show_product_lst(self):
        categories = self.cursor.execute('SELECT DISTINCT category FROM products').fetchall()
        for i, v in enumerate(categories):
            self.product_lst.insert('', 'end', v[0], text=v[0])
            products = self.cursor.execute('SELECT * FROM products WHERE category="{}"'.format(v[0])).fetchall()
            for v in products:
                self.product_lst.insert(v[2], 'end', values=v)

    def clear_add_remove_value(self, master, edit=False):
        self.change_add_remove_state(NORMAL)
        [master.nametowidget('{0}_container.{0}_input'.format(i) if not edit else i+'_input').delete(0, 'end') if 'quantity' not in i else master.nametowidget('{0}_container.{0}_input'.format(i) if not edit else i+'_input').set('') for i in self.purchased_data_order]

    def insert_add_remove_value(self, master, selection, include_category=True, insert_procuct_code=True, edit=False):
        self.clear_add_remove_value(master, edit)

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
        
    def product_lst_select_callback(self, e):
        selection = self.product_lst.item(self.product_lst.selection()[0])['values']
        if len(selection) == 8:
            self.product_sno_input.delete(0, 'end')
            self.product_sno_input.insert(0, selection[0])

    def select_all(self, e):
        e.widget.select_range(0, 'end')
        e.widget.icursor('end')

    def add_item_to_purchase(self):
        if all(self.add_remove_container.nametowidget('{0}_container.{0}_input'.format(i)).get() for i in self.purchased_data_order):
            self.purchased_lst.insert(parent='', index='end', values=[self.add_remove_container.nametowidget('{0}_container.{0}_input'.format(i)).get() for i in self.purchased_data_order])
            self.update_summary()
            self.change_add_remove_state(NORMAL)
            [[self.add_remove_container.nametowidget('{0}_container.{0}_input'.format(i)).delete(0, 'end')] for i in self.purchased_data_order]
            self.change_add_remove_state(DISABLED)

    def update_summary(self):
        total, tax = list(map(
            lambda i: round(sum(i), 2), 
            zip(*[
                (round(float(j[0])*float(j[2]), 2), 
                round(float(j[4]), 2)) 
                for i in self.purchased_lst.get_children() 
                if (j:=self.purchased_lst.item(i)['values'][3:])
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
        if self.purchased_lst.selection():
            selection = self.purchased_lst.item(self.purchased_lst.selection()[0])['values']
            self.purchased_lst.delete(self.purchased_lst.selection()[0])
            self.delete_summary(float(selection[3])*float(selection[5]), float(selection[7]))

    def find_product_by_code(self, P, master=None, edit=False):
        try: 
            selection = self.cursor.execute(f'SELECT * FROM products WHERE product_code="{P}"').fetchone()
            if selection: self.insert_add_remove_value(master, selection, insert_procuct_code=False, edit=edit)
        except: pass
        return True

    def find_product_by_sno(self, P, master=None, edit=False):
        try: 
            selection = self.cursor.execute(f'SELECT * FROM products WHERE id={P}').fetchone()
            if selection: self.insert_add_remove_value(master, selection, edit=edit)
        except: pass
        return True

    def clear(self):
        for i in self.purchased_lst.get_children():
            self.purchased_lst.delete(i)
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
        if self.purchased_lst.selection():
            selection_id = self.purchased_lst.selection()[0]
            selection_content = self.purchased_lst.item(selection_id)['values']
            self.editwindow = EditWindow(self, selection_content[0], selection_id)
            self.editwindow.mainloop()

class DatabaseFrame(Frame):
    connection = sqlite3.connect('bill_store.db')
    cursor = connection.cursor()

    product_table_proportion = (1, 3, 4, 10, 2, 3, 3, 3)

    type_proportion = {
        'INTEGER': 100,
        'REAL': 100,
        'TEXT': 250,
        'NUMERIC': 100
    }

    def __init__(self, master, *args, **kwargs):
        super(DatabaseFrame, self).__init__(master, *args, **kwargs)

    def execute(self):
        self.define_widget()
        self.place_widget()
        self.update()
        self.database_table.update()
        self.config_treeview()

    def define_widget(self):
        self.left_container = Frame(self)
        self.right_container = Frame(self, width=600)
        self.top_container = Frame(self.left_container)

        self.table_name_input_container = Frame(self.top_container)
        self.table_name_input_lb = ttk.Label(self.table_name_input_container, text='Table Name')
        self.table_name_input_input = ttk.Combobox(self.table_name_input_container)
        
        self.table_name_input_input['values'] = [i[0].replace('_', ' ').title() for i in self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        self.table_name_input_input['state'] = 'readonly'
        self.table_name_input_input.set('Products')
        self.table_name_input_input.bind('<<ComboboxSelected>>', self.table_name_change_callback)

        self.search_input_container = Frame(self.top_container)
        self.search_input_lb = ttk.Label(self.search_input_container, text="Search Item")
        self.search_input_input = ttk.Entry(self.search_input_container)
        
        self.database_table = ttk.Treeview(self.left_container)
        self.database_table_x_scrollbar = ttk.Scrollbar(self.left_container, command=self.database_table.xview, orient='horizontal')
        self.database_table_y_scrollbar = ttk.Scrollbar(self.left_container, command=self.database_table.yview, orient='vertical')

    def place_widget(self):
        self.left_container.grid(row=0, column=0, sticky=NSEW)
        self.right_container.grid(row=0, column=1, sticky=NS, padx=(20, 0))
        self.top_container.pack(fill=X, pady=(0, 20))
        
        self.table_name_input_container.grid(row=0, column=0, sticky=NSEW, padx=(0, 20))
        self.table_name_input_lb.pack(fill=BOTH, pady=(0, 5))
        self.table_name_input_input.pack(fill=BOTH)

        self.search_input_container.grid(row=0, column=1, sticky=NSEW)
        self.search_input_lb.pack(fill=BOTH, pady=(0, 5))
        self.search_input_input.pack(fill=BOTH)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.top_container.grid_columnconfigure(0, weight=1)
        self.top_container.grid_columnconfigure(1, weight=5)
        self.database_table_y_scrollbar.pack(fill=Y, side=RIGHT)
        self.database_table_x_scrollbar.pack(fill=X, side=BOTTOM)
        self.database_table.configure(yscrollcommand=self.database_table_y_scrollbar.set)
        self.database_table.configure(xscrollcommand=self.database_table_x_scrollbar.set)

    def config_treeview(self):
        table_name = self.table_name_input_input.get().replace(' ', '_').lower()
        column_names_raw = self.cursor.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        column_names, column_type = zip(*(i[1:3] for i in column_names_raw))
        column_width = [100]+[i*50 for i in self.product_table_proportion]
        column_names = [i.replace('_', ' ').title() for i in column_names]

        self.database_table.pack_forget()
        self.database_table['columns'] = column_names
        [self.database_table.column(i, anchor=W, minwidth=j, width=j, stretch=NO) for i, j in zip(('#0',)+self.database_table['columns'], column_width)]
        [self.database_table.heading(i, text=j, anchor=W) for i, j in zip(self.database_table['columns'], column_names)]
        self.database_table.pack(fill=BOTH, side=LEFT)

        self.show_database(table_name)

    def table_name_change_callback(self, e):
        self.table_name_input_input.selection_clear()
        self.config_treeview()

    def show_database(self, table_name):
        for i in self.database_table.get_children():
            self.database_table.delete(i)

        if table_name == 'products':
            categories = self.cursor.execute('SELECT DISTINCT category FROM '+table_name).fetchall()
            for i, v in enumerate(categories):
                self.database_table.insert('', 'end', v[0], text=v[0])
                products = self.cursor.execute('SELECT * FROM {} WHERE category="{}"'.format(table_name, v[0])).fetchall()
                for v in products:
                    self.database_table.insert(v[2], 'end', values=v)
        else:
            products = self.cursor.execute('SELECT * FROM {}'.format(table_name)).fetchall()
            for v in products:
                self.database_table.insert('', 'end', values=v)

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
        self.widget_container_frm = Frame(self)
        self.widget_container = Frame(self.widget_container_frm)
        self.btn_container = Frame(self.widget_container)

        edit = [
            ('product_sno', 'SNO', 10, (self.register(lambda P: self.find_product_by_sno(P, self.widget_container, edit=True)), '%P'), NORMAL, 'xterm'),
            ('product_code', 'Product Code', 15, (self.master.register(lambda P: self.find_product_by_code(P, self.widget_container, edit=True)), '%P'), NORMAL, 'xterm'),
            ('product_name', 'Product Name', 40, lambda: True, DISABLED, 'arrow'),
            ('quantity', 'Qty', 5, (self.register(self.update_amount), '%P'), NORMAL, 'xterm', lambda: self.update_amount(self.quantity_input.get())),
            ('unit_name', 'Unit', 15, lambda: True, DISABLED, 'arrow'),
            ('unit_price', 'Unit Price', 14, lambda: True, DISABLED, 'arrow'),
            ('tax_rate', 'Tax Rate',10, lambda: True, DISABLED, 'arrow'),
            ('tax_amount', 'Tax Amount', 14, lambda: True, DISABLED, 'arrow'),  
            ('total_price', 'Total Price', 14, lambda: True, DISABLED, 'arrow')
        ]

        edit_lb = {i+'_lb': ttk.Label(self.widget_container, text=j, name=i+'_lb') for i, j, *_ in edit}
        edit_input = {i+'_input': (ttk.Entry if i!='quantity' else ttk.Spinbox)(self.widget_container, **(dict(width=k, name=i+'_input', validate='key', validatecommand=l, state=m, cursor=n, command=o[0] if o else None)|({'from_': 1, 'to': 9999} if i=='quantity' else {}))) for i, _, k, l, m, n, *o in edit}
        self.__dict__.update({**edit_lb, **edit_input})

        self.reset_btn = ttk.Button(self.widget_container, text='Reset', style='danger.Outline.TButton', width=10, command=lambda: self.insert_add_remove_value(self.widget_container, self.original_data))
        self.cancel_btn = ttk.Button(self.btn_container, text='Cancel', style='primary.Outline.TButton', width=10, command=self.destroy)
        self.save_btn = ttk.Button(self.btn_container, text='Save', style='primary.TButton', width=10, command=self.save_and_close)

    def place_widget(self):
        self.widget_container_frm.pack()
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

        [self.widget_container.nametowidget(v+'_lb').grid(row=i, column=0, sticky=W, pady=(0, 15)) for i, v, in enumerate(order)]
        [self.widget_container.nametowidget(v+'_input').grid(row=i, column=1, padx=(20, 0), pady=(0, 15), sticky=W) for i, v, in enumerate(order)]

        self.btn_container.grid(row=9, column=1, sticky=E, pady=(20, 0))
        self.reset_btn.grid(row=9, column=0, sticky=W, pady=(20, 0))
        self.cancel_btn.grid(row=0, column=1, sticky=E)
        self.save_btn.grid(row=0, column=2, sticky=E, padx=(10, 0))

    def save_and_close(self):
        if all(self.widget_container.nametowidget(i+'_input').get() for i in self.purchased_data_order):
            self.main_window.purchased_lst.delete(self.treeview_id)
            self.main_window.purchased_lst.insert(parent='', index=int(self.treeview_id[1:]), values=[self.widget_container.nametowidget(i+'_input').get() for i in self.main_window.purchased_data_order])
            self.main_window.update_summary()
            self.destroy()

if __name__ == '__main__':
    root = Window()
    root.master.mainloop()