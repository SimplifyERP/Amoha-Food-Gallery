from frappe.desk.doctype.todo.todo import ToDo
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder
import frappe
from frappe.utils import today,getdate

from frappe.model.naming import make_autoname

from erpnext.stock.utils import get_stock_balance, get_stock_value_on

class CustomPurchaseOrder(PurchaseOrder):

    def on_submit(self):
        self.my_custom_code()
        super().on_submit()

    def my_custom_code(self):
        pass


@frappe.whitelist()
def customstockbalance(item_code,warehouse,company):
    dd = frappe.db.sql(f"""

                    SELECT    a.item_code   AS "Item",
                              a.item_name   AS "Item Name",
                              a.item_group  AS "Item Group",
                              a.brand       AS "Brand",
                              a.description AS "Description",
                              b.warehouse   AS "Warehouse",
                              b.actual_qty  AS "balance_qty",
                              c.company     AS "company"
                              
                    FROM      `tabItem` a
                    
                    LEFT JOIN `tabBin` b
                    ON        a.item_code = b.item_code
                    
                    LEFT JOIN `tabItem Default` c
                    ON        a.item_code = c.parent
                    
                    WHERE     a.item_code = '{item_code}'
                    AND       b.warehouse = "{warehouse}"
                    AND       c.company = '{company}'


                    """,as_dict=1)
    if len(dd) !=0  :
        return dd[0]
    



@frappe.whitelist()
def customstockbalanceWarehouse(item_code,warehouse,company):
    dd = frappe.db.sql(f"""
                    SELECT    a.item_code   AS "Item",
                              a.item_name   AS "Item Name",
                              a.item_group  AS "Item Group",
                              a.brand       AS "Brand",
                              a.description AS "Description",
                              b.warehouse   AS "Warehouse",
                              b.actual_qty  AS "balance_qty",
                              c.company     AS "company"
                              
                    FROM      `tabItem` a
                    
                    LEFT JOIN `tabBin` b
                    ON        a.item_code = b.item_code
                    
                    LEFT JOIN `tabItem Default` c
                    ON        a.item_code = c.parent
                    
                    WHERE     a.item_code = '{item_code}'
                    AND       b.warehouse = "{warehouse}"
                    AND       c.company = '{company}'




                    """,as_dict=1)
    if len(dd) !=0  :
        return dd[0]






@frappe.whitelist()
def todayPO(item_code,company):
    dd = frappe.db.sql(f"""  select 
                            poi.item_code,
                            sum(poi.qty) as qty ,
                            po.name
                          from `tabPurchase Order Item` as poi
                          left join `tabPurchase Order` as po
                          on poi.parent = po.name
                          where po.docstatus =1 and po.submitted_on = '{today()}' and poi.item_code = '{item_code}' and po.company = '{company}';
                          """,as_dict=1)
    return dd[0]


@frappe.whitelist()
def todaySI(item_code,company):
    dd = frappe.db.sql(f"""  select 
                            sii.item_code,
                            sum(sii.qty) as qty ,
                            si.name
                          from `tabSales Order Item` as sii
                          left join `tabSales Order` as si
                          on sii.parent = si.name
                          where si.docstatus =1 and si.submitted_on = '{today()}' and sii.item_code = '{item_code}' and si.company = '{company}';
                          """,as_dict=1)
    return dd[0]