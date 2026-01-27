# Проект 'custom_auth_system'

Backend-приложение - Система аутентификации и авторизации

### Установка
1. Подготовка базы данных (`PostgreSQL`):
Перед запуском проекта создайте БД:
```
sudo -u postgres psql 
```
Создайте базу данных
```
CREATE DATABASE your_db_name;
```
Создайте пользователя (опционально, но рекомендуется)
```
CREATE USER your_user WITH PASSWORD 'your_password';
```
Дайте права пользователю на базу данных
```
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_user;
```
Выйти из psql
```
\q
```
2. Клонировать репозиторий:
```
git clone git@github.com:Nefertitu/custom_auth_system
cd custom_auth_system
```
3. Настройка окружения:

Создайте файл .env на основе шаблона (`.env.sample`):
```
cp .env.sample .env
```
Отредактируйте .env (укажите свои секретные ключи, настройки БД и т.д.)

4. Установка зависимостей:
```
poetry install
poetry shell
venv\Scripts\activate
```
5. Миграции базы данных:
```
python manage.py makemigrations
python manage.py migrate
```
6. Создание суперпользователя (для доступа в админ-панель):
```
python manage.py csu
```

7. Загрузка тестовых данных:
```
python manage.py create_test_data
```
Создает:
- Менеджер продуктов (может менять цены, удалять продукты)
- Менеджер пользователей (может просматривать/удалять пользователей)
- Обычные пользователи (владельцы продуктов)
- Тестовые продукты (активные/неактивные)

8. Запуск сервера:
```
python manage.py runserver
```

## Обзор

Система реализует гибкую модель управления правами доступа на основе 
Django Permissions Framework с кастомными правами, JWT-аутентификацией и 
ролевой моделью.

## Архитектура

### Модели данных

# authentication/models.py
```
class User(AbstractUser):
    """Кастомная модель пользователя с email как username"""
    permissions = [
        ("can_view_all_users", "Может видеть всех пользователей"),
        ("can_delete_user", "Может удалять пользователей"),
    ]
```
# products/models.py  
```
class Product(models.Model):
    """Модель продукта с правами доступа"""
    permissions = [
        ("can_change_price", "Может изменять цену"),
        ("can_delete_product", "Может удалять продукты"),
        ("can_view_all_products", "Может просматривать все продукты"),
    ]
```

##  Уровни доступа

1. Анонимные пользователи
✅ Регистрация (/api/auth/register/)
✅ Вход в систему (/api/auth/login/)
✅ Просмотр активных продуктов
❌ Управление пользователями/продуктами

2. Обычные пользователи
✅ Просмотр/редактирование своего профиля
✅ Создание продуктов (становятся владельцем)
✅ Просмотр активных продуктов
❌ Удаление пользователей/продуктов
❌ Изменение цен

3. Менеджер продуктов (is_staff=True + права)
✅ Все права обычного пользователя
✅ Изменение цен любых продуктов (can_change_price)
✅ Удаление продуктов (can_delete_product)
✅ Просмотр всех продуктов (can_view_all_products)

4. Менеджер пользователей (is_staff=True + права)
✅ Просмотр всех пользователей (can_view_all_users)
✅ Удаление пользователей (can_delete_user)
❌ Управление продуктами

5. Администратор (is_superuser=True)
✅ Полный доступ ко всем операциям
✅ Управление правами через API (/api/permissions/)

## API Эндпоинты 

✅ Аутентификация:
  POST   /api/auth/login/           # вход
  POST   /api/auth/register/        # регистрация  
  POST   /api/auth/logout/          # выход
  POST   /api/auth/token/refresh/   # обновление токена
  
✅ Управление пользователями:
  GET    /api/auth/                 # список пользователей
  POST   /api/auth/                 # создать пользователя
  GET    /api/auth/{id}/            # получить пользователя
  PUT    /api/auth/{id}/            # обновить пользователя
  DELETE /api/auth/{id}/            # удалить пользователя
  
✅ Продукты:
  GET    /api/products/             # список продуктов
  POST   /api/products/             # создать продукт
  GET    /api/products/{id}/        # получить продукт
  PUT    /api/products/{id}/        # обновить продукт
  DELETE /api/products/{id}/        # удалить продукт
  
✅ Права:
  GET    /api/permissions/                              # доступные методы
  GET    /api/permissions/user_permissions/?user_id=4   # права конкретного пользователя
  GET    /api/permissions/available_permissions/        # все доступные права
  POST   /api/permissions/grant_permission/             # назначить право пользователю 
  POST   /api/permissions/revoke_permission/            # отозвать право у пользователя

## Классы разрешений

### Для пользователей

IsSelfOnly()           # Доступ только к своему профилю
CanViewAllUsers()      # Просмотр всех пользователей
CanDeleteUser()        # Удаление пользователей

### Для продуктов

IsOwnerOrReadOnly()    # Владелец может редактировать
CanChangePrice()       # Изменение цены (менеджеры)
CanDeleteProduct()     # Удаление продуктов
CanViewAllProducts()   # Просмотр всех продуктов

## Технические особенности
- JWT аутентификация с refresh токенами
- Blacklist токенов при выходе из системы
- Динамические permissions в ViewSets
- Идемпотентные команды создания данных
- Полная REST API для управления правами

## Обработка ошибок
- 401 Unauthorized - не аутентифицирован
- 403 Forbidden - нет прав доступа
- 404 Not Found - ресурс не существует
- 400 Bad Request - неверные данные

## Принципы работы
- Принцип наименьших привилегий - пользователи получают только необходимые права
- Владелец ресурса может управлять своим контентом
- Менеджеры имеют расширенные права в своей области
- Администраторы имеют полный контроль через API
 
## Технологии 
- Django 6.x, 
- Django REST Framework, 
- JWT, 
- PostgreSQL

## Лицензия: MIT

## Статус: 
Готово к использованию 🚀