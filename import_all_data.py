"""
Полный импорт всех данных
"""
from migrations.import_excel import import_users_from_excel, import_products_from_excel, import_orders_from_excel

print("=== Импорт данных ===")
print("\n1. Импорт пользователей...")
import_users_from_excel('pril/user_import.xlsx')

print("\n2. Импорт товаров...")
import_products_from_excel('pril/Tovar.xlsx')

print("\n3. Импорт заказов...")
import_orders_from_excel('pril/Заказ_import.xlsx')

print("\n=== Импорт завершен! ===")

