{
    'name': "Construction",
    'summary': "Make reports easily",
    'description': "Модуль реализует функционал для заполнения отчетности по проделанной работе",
    'author': "Kostrov Vladislav",
    'category': 'Services',
    'application': 'True',
    'version': '16.0.1',
    'depends': ['base', 'mail',],
    'data': [
        'security/ir.model.access.csv',
        'views/progress_report_views.xml',
        'views/work_list_views.xml',
        'views/work_name_views.xml',
        'views/work_category_views.xml',
        'views/work_statistics_views.xml'
        ],
}