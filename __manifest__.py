{
    'name': "Construction",
    'summary': "Make reports easily",
    'description': "Модуль реализует функционал для заполнения отчетности по проделанной работе",
    'author': "Kostrov Vladislav",
    'category': 'Services',
    'application': 'True',
    'version': '16.0.1',
    'depends': ['base', 'mail', 'product', 'stock', 'fleet'],
    'data': [
        'security/ir.model.access.csv',
        
        'views/progress_report_views.xml',
        'views/work_list_views.xml',
        'views/work_name_views.xml',
        'views/work_category_views.xml',
        'views/work_statistics_views.xml',
        'views/construction_objects_views.xml',
        'views/stock_picking_views.xml',

        'data/stock_location_data.xml',

        'reports/progress_reports_template.xml',
        'reports/progress_reports_report.xml',
        ],
}