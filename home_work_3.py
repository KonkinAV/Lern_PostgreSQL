from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
import json

# Определение базового класса для моделей
Base = declarative_base()

# Модель Издателя (Автора)
class Publisher(Base):
    __tablename__ = 'publisher'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    books = relationship("Book", back_populates="publisher")

# Модель Книги
class Book(Base):
    __tablename__ = 'book'

    id = Column(Integer, primary_key=True)
    title = Column(String(150), nullable=False)
    id_publisher = Column(Integer, ForeignKey('publisher.id'))

    publisher = relationship("Publisher", back_populates="books")
    # Связь с таблицей Stock (наличие)
    stocks = relationship("Stock", back_populates="book")


# Модель Магазина
class Shop(Base):
    __tablename__ = 'shop'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    # Связь с таблицей Stock (наличие)
    stocks = relationship("Stock", back_populates="shop")


# Модель Наличия (Склада) - связывает Book и Shop и хранит количество
class Stock(Base):
    __tablename__ = 'stock'

    id = Column(Integer, primary_key=True)
    id_book = Column(Integer, ForeignKey('book.id'))
    id_shop = Column(Integer, ForeignKey('shop.id'))
    count = Column(Integer, nullable=False) # Количество книг в наличии

    # Связи с таблицами Book и Shop
    book = relationship("Book", back_populates="stocks")
    shop = relationship("Shop", back_populates="stocks")
    # Связь с таблицей Sale (обратная ссылка)
    sales = relationship("Sale", back_populates="stock_item")


# Модель Продажи (фиксирует факт продажи конкретной позиции из Stock)
class Sale(Base):
    __tablename__ = 'sale'

    id = Column(Integer, primary_key=True)
    price = Column(Integer, nullable=False)
    date_sale = Column(DateTime, default=datetime.utcnow)
    # is_stock в схеме, вероятно, опечатка, так как нам нужен id_stock для связи.
    # Используем id_stock как внешний ключ.
    id_stock = Column(Integer, ForeignKey('stock.id'))
    count = Column(Integer, nullable=False) # Количество проданных единиц в этой транзакции

    # Связь с таблицей Stock
    stock_item = relationship("Stock", back_populates="sales")


def get_sales_by_publisher(publisher_name):
    """
    Выполняет запрос к БД и выводит информацию о продажах книг заданного издателя.
    """

    # Объединяем все необходимые таблицы:
    # Sale -> Stock -> Book -> Publisher
    # Sale -> Stock -> Shop
    query = session.query(
        Book.title,
        Shop.name,
        Sale.price,
        Sale.date_sale
    ).join(Stock, Sale.stock_item).join(Book, Stock.book).join(Publisher,
                                                               Book.publisher).join(
        Shop, Stock.shop)

    # Фильтруем по имени издателя, используя LIKE для гибкости поиска
    query = query.filter(Publisher.name.ilike(f'%{publisher_name}%'))

    # Выполняем запрос и получаем результаты
    results = query.all()

    if not results:
        print(f"\nПродажи для издателя '{publisher_name}' не найдены.")
        return

    # Вывод результатов в требуемом формате
    print(f"\nРезультаты для издателя '{publisher_name}':")
    print("-" * 60)
    print(
        f"{'Название книги':<30} | {'Магазин':<15} | {'Цена':<7} | {'Дата покупки':<10}")
    print("-" * 60)
    for book_title, shop_name, price, date_sale in results:
        # Форматируем дату для красивого вывода
        formatted_date = date_sale.strftime('%d-%m-%Y')
        print(
            f"{book_title:<30} | {shop_name:<15} | {price!s:<7} | {formatted_date:<10}")
    print("-" * 60)

if __name__ == '__main__':
    DSN = 'postgresql://postgres:postgres@localhost:5432/books'
    engine = create_engine(DSN)
    Base.metadata.create_all(engine)
    print("Таблицы успешно созданы.")

    Session = sessionmaker(bind=engine)
    session = Session()

    with open('tests_data.json') as f:
        data_to_load = json.load(f)

    models_map = {
        'publisher': Publisher,
        'book': Book,
        'shop': Shop,
        'stock': Stock,
        'sale': Sale
    }
    ordered_models = ['publisher', 'shop', 'book', 'stock', 'sale']

    for model_name in ordered_models:
        model_class = models_map[model_name]
        # Фильтруем данные из списка, относящиеся к текущей модели
        items_to_load = [item for item in data_to_load if item['model'] ==
                         model_name]

        print(f"Загрузка данных для модели '{model_name}' ({len(items_to_load)} записей)...")
        for item in items_to_load:
            fields = item['fields']
            primary_key_value = item['pk']

            # Специальная обработка для поля даты в модели Sale
            if model_name == 'sale' and 'date_sale' in fields:
                # Преобразование строки ISO 8601 в объект datetime
                fields['date_sale'] = datetime.fromisoformat(
                    fields['date_sale'].replace('Z', '+00:00'))

            # Добавляем первичный ключ явно, если он указан в данных JSON
            fields['id'] = primary_key_value

            # Создаем объект модели и добавляем в сессию
            obj = model_class(**fields)
            session.add(obj)

        try:
            # Коммитим каждую таблицу отдельно, чтобы обеспечить доступность PK для следующих таблиц
            session.commit()
            print(f"Успешно загружены данные для {model_name}.")
        except Exception as e:
            session.rollback()
            print(f"Ошибка при загрузке данных для {model_name}: {e}")

    print("Доступные издатели в БД: O’Reilly, Pearson, Microsoft Press, No starch press")
    user_input = input("Введите имя или часть имени издателя (например, O'Reilly): ")

    if user_input:
        get_sales_by_publisher(user_input)
    else:
        print("Имя издателя не было введено.")

    session.close()