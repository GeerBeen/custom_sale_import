import openpyxl
import base64
import io
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrderImportWizard(models.TransientModel):
    _name = "sale.order.import.wizard"
    _description = "Wizard for custom importing Sales from excel."

    excel_file = fields.Binary(string="Excel File", required=True)
    file_name = fields.Char(string="File Name")
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)

    start_row = fields.Integer("Start Row", required=True, default=2)
    product_col = fields.Integer("Product Column", required=True, default=1)
    quantity_col = fields.Integer("Product's Quantity Column", required=True, default=2)
    price_col = fields.Integer("Product's Price Column", required=True, default=3)

    @api.constrains("start_row", "product_col", "quantity_col", "price_col")
    def _check_excel_values(self):
        for record in self:
            if record.start_row < 1 or record.product_col < 1 or record.quantity_col < 1 or record.price_col < 1:
                raise ValidationError(_("Rows and Columns numbers must be bigger than 0!"))
        
    def sale_order_import_action(self):
        self.ensure_one()
        # кодований рядок до байтів
        file_bytes = base64.b64decode(self.excel_file)
        # байти до потоку
        file_input = io.BytesIO(file_bytes)
        # поток до об'єкта журналу
        workbook = openpyxl.load_workbook(file_input,data_only=True)
        # перший лист журналу
        sheet = workbook.active

        # створюємо sale_order об'єкт
        sale_order = self.env['sale.order'].create({
            "partner_id": self.partner_id.id,
        })

        # ітеруємось до першого пустого рядка
        skipped_missing_data_rows = []
        created_products_names = []
        current_row = self.start_row
        while True:
            # отримуємо поточні значення
            current_product = sheet.cell(row=current_row, column=self.product_col).value
            current_quantity = sheet.cell(row=current_row, column=self.quantity_col).value
            current_price = sheet.cell(row=current_row, column=self.price_col).value

            # якщо жодного значення нема - виходимо
            if not current_product and not current_quantity and not current_price:
                break
            
            # опрацьовуємо поточні значення
            # якщо всі три значення є, то додаємо рядок в сейл ордер
            if current_product and current_quantity and current_price:
                product = self.env["product.product"].search([("name","=",current_product)], limit=1)

                if not product:
                    product = self.env["product.product"].create({
                        "name":current_product,
                        "type":"consu"
                    })
                    created_products_names.append(current_product)
                
                self.env["sale.order.line"].create({
                    "order_id":sale_order.id,
                    "product_id":product.id,
                    "product_uom_qty": float(current_quantity),
                    "price_unit": float(current_price)
                })
            # якщо чогось нема, то пишемо про це в нотатки
            else:
                skipped_missing_data_rows.append(str(current_row))
            current_row += 1
        
        notes_text = ""
        if skipped_missing_data_rows:
            notes_text += _("Rows that were skipped due to missing data: %s.\n") % ', '.join(skipped_missing_data_rows)
        if created_products_names:
            notes_text += _("Created products: %s.\n") % ', '.join(created_products_names)
        if notes_text:
            sale_order.write({'note': notes_text})

        return {
            "name":_("Order"),
            "type":"ir.actions.act_window",
            "res_model":"sale.order",
            "view_mode":"form",
            "res_id":sale_order.id,
            "target":"current",
        }
    