import psycopg2
from psycopg2 import sql
import psycopg2.extras

DB_CONFIG = {
    'database': 'clients_db',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}


def get_db_connection():
    """Устанавливает соединение с базой данных."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Не удалось подключиться к базе данных: {e}")
        exit()


def create_db(conn):
    """
    Функция, создающая структуру БД (таблицы clients и phones).
    """
    with conn.cursor() as cursor:
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    client_id SERIAL PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE
                );
            ''')
            # UNIQUE constraint на email гарантирует уникальность

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phones (
                    phone_id SERIAL PRIMARY KEY,
                    client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                    phone_number VARCHAR(20) NOT NULL
                );
            ''')
            conn.commit()
            print("Структура БД успешно создана.")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Ошибка при создании БД: {e}")


def add_client(conn, first_name, last_name, email, phones=None):
    """
    Функция, позволяющая добавить нового клиента.
    Возвращает ID нового клиента или None в случае ошибки.
    """
    with conn.cursor() as cursor:
        try:
            cursor.execute('''
                INSERT INTO clients (first_name, last_name, email)
                VALUES (%s, %s, %s)
                RETURNING client_id;
            ''', (first_name, last_name, email))

            client_id = cursor.fetchone()[0]

            if phones:
                # Используем execute_values для эффективной вставки множества телефонов
                phones_data = [(client_id, phone) for phone in phones]
                psycopg2.extras.execute_values(
                    cursor,
                    "INSERT INTO phones (client_id, phone_number) VALUES %s",
                    phones_data
                )

            conn.commit()
            print(f"Клиент {first_name} {last_name} добавлен с ID: {client_id}")
            return client_id

        except psycopg2.Error as e:
            conn.rollback()
            print(f"Ошибка при добавлении клиента: {e}")
            return None


def add_phone(conn, client_id, phone):
    """
    Функция, позволяющая добавить телефон для существующего клиента.
    """
    with conn.cursor() as cursor:
        try:
            cursor.execute('''
                INSERT INTO phones (client_id, phone_number)
                VALUES (%s, %s);
            ''', (client_id, phone))
            conn.commit()
            print(f"Телефон {phone} добавлен для клиента ID {client_id}.")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Ошибка при добавлении телефона: {e}")


def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    """
    Функция, позволяющая изменить данные о клиенте (имя, фамилию, email).
    Телефоны (phones) в этой функции не обрабатываются, для них есть отдельные функции.
    """
    updates = []
    params = []

    if first_name:
        updates.append("first_name = %s")
        params.append(first_name)
    if last_name:
        updates.append("last_name = %s")
        params.append(last_name)
    if email:
        updates.append("email = %s")
        params.append(email)

    if not updates:
        print("Нечего обновлять. Укажите хотя бы одно поле (имя, фамилию или email).")
        return

    # Добавляем ID клиента в конец списка параметров для WHERE
    params.append(client_id)

    query = sql.SQL("UPDATE clients SET {} WHERE client_id = %s").format(
        sql.SQL(', ').join(map(sql.SQL, updates))
    )

    with conn.cursor() as cursor:
        try:
            cursor.execute(query, params)
            conn.commit()
            if cursor.rowcount > 0:
                print(f"Данные клиента ID {client_id} обновлены.")
            else:
                print(f"Клиент с ID {client_id} не найден.")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Ошибка при обновлении данных клиента: {e}")


def delete_phone(conn, client_id, phone):
    """
    Функция, позволяющая удалить телефон для существующего клиента.
    """
    with conn.cursor() as cursor:
        try:
            cursor.execute('''
                DELETE FROM phones
                WHERE client_id = %s AND phone_number = %s;
            ''', (client_id, phone))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"Телефон {phone} удален для клиента ID {client_id}.")
            else:
                print("Телефон или клиент не найдены.")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Ошибка при удалении телефона: {e}")


def delete_client(conn, client_id):
    """
    Функция, позволяющая удалить существующего клиента.
    Благодаря ON DELETE CASCADE в таблице phones, все связанные телефоны удаляются автоматически.
    """
    with conn.cursor() as cursor:
        try:
            cursor.execute('''
                DELETE FROM clients
                WHERE client_id = %s;
            ''', (client_id,))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"Клиент с ID {client_id} и все его телефоны удалены.")
            else:
                print(f"Клиент с ID {client_id} не найден.")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Ошибка при удалении клиента: {e}")


def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    """
    Функция, позволяющая найти клиента по его данным: имени, фамилии, email или телефону.
    """
    query = """
        SELECT DISTINCT c.client_id, c.first_name, c.last_name, c.email
        FROM clients c
        LEFT JOIN phones p ON c.client_id = p.client_id
        WHERE 1=1 
    """
    params = []

    if first_name:
        query += " AND c.first_name ILIKE %s"  # ILIKE для поиска без учета регистра
        params.append(f"%{first_name}%")
    if last_name:
        query += " AND c.last_name ILIKE %s"
        params.append(f"%{last_name}%")
    if email:
        query += " AND c.email ILIKE %s"
        params.append(f"%{email}%")
    if phone:
        query += " AND p.phone_number ILIKE %s"
        params.append(f"%{phone}%")

    if not params:
        print("Укажите хотя бы один параметр для поиска.")
        return []

    with conn.cursor() as cursor:
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()

            if results:
                print(f"\nНайдено клиентов: {len(results)}")
                # Можно добавить функцию для получения телефонов найденных клиентов
                return results
            else:
                print("Клиенты по заданным критериям не найдены.")
                return []

        except psycopg2.Error as e:
            print(f"Ошибка при поиске клиента: {e}")
            return []


def list_all_clients_detailed(conn):
    """
    Дополнительная функция для вывода всех клиентов с их телефонами.
    """
    query = """
        SELECT c.client_id, c.first_name, c.last_name, c.email, p.phone_number
        FROM clients c
        LEFT JOIN phones p ON c.client_id = p.client_id
        ORDER BY c.client_id;
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

        clients_data = {}
        for row in results:
            client_id, first_name, last_name, email, phone_number = row
            if client_id not in clients_data:
                clients_data[client_id] = {
                    'id': client_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phones': []
                }
            if phone_number and phone_number not in clients_data[client_id]['phones']:
                clients_data[client_id]['phones'].append(phone_number)

        print("\n--- Список всех клиентов ---")
        for client in clients_data.values():
            print(client)
        print("---------------------------\n")


if __name__ == '__main__':
    with get_db_connection() as conn:
        create_db(conn)

        # Добавление клиентов
        client1_id = add_client(conn, "Иван", "Петров", "ivan.p@example.com", ["+79001234567", "+74951234567"])
        client2_id = add_client(conn, "Мария", "Сидорова", "maria.s@example.com", ["+79267654321"])
        client3_id = add_client(conn, "Алексей", "Козлов", "alexey.k@example.com")  # Клиент без телефона

        list_all_clients_detailed(conn)

        # Добавляем телефон клиенту 3
        if client3_id:
            add_phone(conn, client3_id, "+79998887766")

        # Изменяем данные клиента 1
        if client1_id:
            change_client(conn, client1_id, email="ivan_new@example.com")

        # Удаляем телефон у клиента 1
        if client1_id:
            delete_phone(conn, client1_id, "+74951234567")

        list_all_clients_detailed(conn)

        # Поиск клиента по фамилии
        print("Поиск клиента по фамилии 'Петров':")
        found_clients = find_client(conn, last_name="Петров")
        print(found_clients)

        # Поиск клиента по телефону
        print("Поиск клиента по телефону '+79267654321':")
        found_clients_phone = find_client(conn, phone="+79267654321")
        print(found_clients_phone)

        # Удаляем клиента 2
        if client2_id:
            delete_client(conn, client2_id)

        list_all_clients_detailed(conn)

    print("Соединение с БД закрыто.")

