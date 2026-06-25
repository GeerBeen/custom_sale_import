{
    "name": "Sale Imports",
    "summary": "Sale Imports",
    "version": "19.0.0.0.1",
    "license":"OEEL-1",
    "depends": ["base", "sale"],
    "author": "GeerBeen",
    "category": "Sales",
    "description": """
    Adds custom import from excel to sale.order model.
    """,
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Wizard
        "wizard/sale_order_wizard_views.xml",
    ],
    "demo":[
        
        ],
    "application": False,
}