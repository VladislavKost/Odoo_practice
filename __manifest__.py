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
        'views/progress_report.xml',
        'views/work_list.xml',
        'views/work_name.xml',
        'views/work_category.xml',
        ],
}