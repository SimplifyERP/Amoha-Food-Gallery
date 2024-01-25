from frappe.desk.doctype.todo.todo import ToDo
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder
import frappe
from frappe.utils import today,getdate


from erpnext.stock.utils import get_stock_balance, get_stock_value_on


from erpnext.accounts.doctype.sales_invoice.sales_invoice  import *

# for auto creations



class CustomSalesInvoice(SalesInvoice):

    def on_submit(self):
        make_inter_company_transaction2(self.doctype,self.name)
        super().on_submit()

    def my_custom_code(self):
        pass




def make_inter_company_transaction2(doctype, source_name, target_doc=None):
	if doctype in ["Sales Invoice", "Sales Order"]:
		source_doc = frappe.get_doc(doctype, source_name)
		target_doctype = "Purchase Invoice" if doctype == "Sales Invoice" else "Purchase Order"
		target_detail_field = "sales_invoice_item" if doctype == "Sales Invoice" else "sales_order_item"
		source_document_warehouse_field = "target_warehouse"
		target_document_warehouse_field = "from_warehouse"
		received_items = get_received_items(source_name, target_doctype, target_detail_field)
	else:
		source_doc = frappe.get_doc(doctype, source_name)
		target_doctype = "Sales Invoice" if doctype == "Purchase Invoice" else "Sales Order"
		source_document_warehouse_field = "from_warehouse"
		target_document_warehouse_field = "target_warehouse"
		received_items = {}

	validate_inter_company_transaction(source_doc, doctype)
	details = get_inter_company_details(source_doc, doctype)

	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		set_purchase_references(target)

	def update_details(source_doc, target_doc, source_parent):
		target_doc.inter_company_invoice_reference = source_doc.name
		if target_doc.doctype in ["Purchase Invoice", "Purchase Order"]:
			currency = frappe.db.get_value("Supplier", details.get("party"), "default_currency")
			target_doc.company = details.get("company")
			target_doc.supplier = details.get("party")
			target_doc.is_internal_supplier = 1
			target_doc.ignore_pricing_rule = 1
			target_doc.buying_price_list = source_doc.selling_price_list

			# Invert Addresses
			update_address(target_doc, "supplier_address", "address_display", source_doc.company_address)
			update_address(
				target_doc, "shipping_address", "shipping_address_display", source_doc.customer_address
			)

			if currency:
				target_doc.currency = currency

			update_taxes(
				target_doc,
				party=target_doc.supplier,
				party_type="Supplier",
				company=target_doc.company,
				doctype=target_doc.doctype,
				party_address=target_doc.supplier_address,
				company_address=target_doc.shipping_address,
			)

		else:
			currency = frappe.db.get_value("Customer", details.get("party"), "default_currency")
			target_doc.company = details.get("company")
			target_doc.customer = details.get("party")
			target_doc.selling_price_list = source_doc.buying_price_list

			update_address(
				target_doc, "company_address", "company_address_display", source_doc.supplier_address
			)
			update_address(
				target_doc, "shipping_address_name", "shipping_address", source_doc.shipping_address
			)
			update_address(target_doc, "customer_address", "address_display", source_doc.shipping_address)

			if currency:
				target_doc.currency = currency

			update_taxes(
				target_doc,
				party=target_doc.customer,
				party_type="Customer",
				company=target_doc.company,
				doctype=target_doc.doctype,
				party_address=target_doc.customer_address,
				company_address=target_doc.company_address,
				shipping_address_name=target_doc.shipping_address_name,
			)

	def update_item(source, target, source_parent):
		target.qty = flt(source.qty) - received_items.get(source.name, 0.0)

	item_field_map = {
		"doctype": target_doctype + " Item",
		"field_no_map": ["income_account", "expense_account", "cost_center", "warehouse"],
		"field_map": {
			"rate": "rate",
		},
		"postprocess": update_item,
		"condition": lambda doc: doc.qty > 0,
	}

	if doctype in ["Sales Invoice", "Sales Order"]:
		item_field_map["field_map"].update(
			{
				"name": target_detail_field,
			}
		)

	if source_doc.get("update_stock"):
		item_field_map["field_map"].update(
			{
				source_document_warehouse_field: target_document_warehouse_field,
				"batch_no": "batch_no",
				"serial_no": "serial_no",
			}
		)

	doclist = get_mapped_doc(
		doctype,
		source_name,
		{
			doctype: {
				"doctype": target_doctype,
				"postprocess": update_details,
				"set_target_warehouse": "set_from_warehouse",
				"field_no_map": ["taxes_and_charges", "set_warehouse", "shipping_address"],
			},
			doctype + " Item": item_field_map,
		},
		target_doc,
		set_missing_values,
	)
	doclist.save()
	return doclist








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
def getStockBalance(item_code, warehouse,company):
	balance_qty = frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`
		where item_code=%s and warehouse=%s and company=%s and is_cancelled='No'
		order by posting_date desc, posting_time desc, name desc
		limit 1""",(item_code,warehouse,company))
	return balance_qty[0][0] if balance_qty else 0.0

@frappe.whitelist()
def company_balance(item_code,company):
    dd = frappe.db.sql(f""" 
                    select 
                        default_warehouse 
                    from 
                        `tabItem Default` 
                    where 
                      parent = '{item_code}' 
                      and company = '{company}'
            """,as_dict=1)

    if len(dd) >= 1:
        return getStockBalance(item_code, dd[0]['default_warehouse'],company)
    else:
         return 0.0

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
