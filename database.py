import sqlite3


DATABASE_NAME = "website.db"


# ==================================================
# CREATE DATABASE
# ==================================================

def create_database():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    # ---------------- USERS ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)


    # ---------------- ORDERS ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)


    # ---------------- PRODUCTS ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT NOT NULL,
            image TEXT,
            category TEXT,
            stock INTEGER DEFAULT 0
        )
    """)


    # ---------------- REVIEWS ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            review TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(product_id, user_id)
        )
    """)


    # ---------------- WISHLIST ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(product_id, user_id)
        )
    """)


    # ---------------- PRODUCT COLUMNS ----------------

    cursor.execute(
        "PRAGMA table_info(products)"
    )

    product_columns = cursor.fetchall()

    product_column_names = [
        column[1]
        for column in product_columns
    ]


    if "image" not in product_column_names:

        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN image TEXT
        """)


    if "category" not in product_column_names:

        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN category TEXT
        """)


    if "stock" not in product_column_names:

        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN stock INTEGER DEFAULT 0
        """)


    # ---------------- ORDER COLUMNS ----------------

    cursor.execute(
        "PRAGMA table_info(orders)"
    )

    order_columns = cursor.fetchall()

    order_column_names = [
        column[1]
        for column in order_columns
    ]


    if "status" not in order_column_names:

        cursor.execute("""
            ALTER TABLE orders
            ADD COLUMN status TEXT DEFAULT 'Pending'
        """)


    # ---------------- INITIAL PRODUCTS ----------------

    cursor.execute(
        "SELECT COUNT(*) FROM products"
    )

    product_count = cursor.fetchone()[0]


    if product_count == 0:

        initial_products = [

            (
                "Product 1",
                499,
                "This is our first product.",
                None,
                "Other",
                10
            ),

            (
                "Product 2",
                799,
                "This is our second product.",
                None,
                "Other",
                10
            ),

            (
                "Product 3",
                999,
                "This is our third product.",
                None,
                "Other",
                10
            )

        ]


        cursor.executemany("""
            INSERT INTO products
            (name, price, description, image, category, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        """, initial_products)


    connection.commit()
    connection.close()


# ==================================================
# DASHBOARD
# ==================================================

def get_dashboard_stats():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT COUNT(*)
        FROM products
    """)

    total_products = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    total_customers = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
    """)

    total_orders = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM orders
        WHERE status != 'Cancelled'
    """)

    total_sales = cursor.fetchone()[0]


    connection.close()


    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "total_sales": total_sales
    }


def get_recent_orders(limit=5):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            email,
            total,
            status
        FROM orders
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))


    orders = cursor.fetchall()

    connection.close()


    return orders


# ==================================================
# USERS
# ==================================================

def create_user(name, email, password):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    try:

        cursor.execute("""
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
        """, (
            name,
            email,
            password
        ))


        user_id = cursor.lastrowid

        connection.commit()
        connection.close()


        return user_id


    except sqlite3.IntegrityError:

        connection.close()

        return None


def get_user_by_email(email):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            email,
            password
        FROM users
        WHERE email = ?
    """, (email,))


    user = cursor.fetchone()

    connection.close()


    return user


# ==================================================
# ORDERS
# ==================================================

def save_order(name, email, address, total):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO orders
        (name, email, address, total, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        email,
        address,
        total,
        "Pending"
    ))


    order_id = cursor.lastrowid

    connection.commit()
    connection.close()


    return order_id


def get_all_orders():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            email,
            address,
            total,
            status
        FROM orders
        ORDER BY id DESC
    """)


    orders = cursor.fetchall()

    connection.close()


    return orders


def get_orders_by_email(email):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            email,
            address,
            total,
            status
        FROM orders
        WHERE email = ?
        ORDER BY id DESC
    """, (email,))


    orders = cursor.fetchall()

    connection.close()


    return orders


def get_order(order_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            email,
            address,
            total,
            status
        FROM orders
        WHERE id = ?
    """, (order_id,))


    order = cursor.fetchone()

    connection.close()


    return order


def update_order_status(order_id, status):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        UPDATE orders
        SET status = ?
        WHERE id = ?
    """, (
        status,
        order_id
    ))


    connection.commit()
    connection.close()


# ==================================================
# PRODUCTS
# ==================================================

def get_all_products():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            price,
            description,
            image,
            category,
            stock
        FROM products
        ORDER BY id DESC
    """)


    products = cursor.fetchall()

    connection.close()


    return products


def search_products(search, category):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    query = """
        SELECT
            id,
            name,
            price,
            description,
            image,
            category,
            stock
        FROM products
        WHERE 1=1
    """


    parameters = []


    if search:

        query += """
            AND (
                name LIKE ?
                OR description LIKE ?
            )
        """


        search_value = f"%{search}%"

        parameters.append(search_value)
        parameters.append(search_value)


    if category:

        query += """
            AND category = ?
        """

        parameters.append(category)


    query += """
        ORDER BY id DESC
    """


    cursor.execute(
        query,
        parameters
    )


    products = cursor.fetchall()

    connection.close()


    return products


def get_categories():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL
        AND category != ''
        ORDER BY category
    """)


    categories = cursor.fetchall()

    connection.close()


    return [
        category[0]
        for category in categories
    ]


def get_product(product_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            price,
            description,
            image,
            category,
            stock
        FROM products
        WHERE id = ?
    """, (product_id,))


    product = cursor.fetchone()

    connection.close()


    return product


def add_product(
    name,
    price,
    description,
    image,
    category,
    stock
):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO products
        (name, price, description, image, category, stock)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        price,
        description,
        image,
        category,
        stock
    ))


    product_id = cursor.lastrowid

    connection.commit()
    connection.close()


    return product_id


def update_product(
    product_id,
    name,
    price,
    description,
    image,
    category,
    stock
):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        UPDATE products
        SET
            name = ?,
            price = ?,
            description = ?,
            image = ?,
            category = ?,
            stock = ?
        WHERE id = ?
    """, (
        name,
        price,
        description,
        image,
        category,
        stock,
        product_id
    ))


    connection.commit()
    connection.close()


def decrease_stock(product_id, quantity):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        UPDATE products
        SET stock = stock - ?
        WHERE id = ?
        AND stock >= ?
    """, (
        quantity,
        product_id,
        quantity
    ))


    connection.commit()

    affected_rows = cursor.rowcount

    connection.close()


    return affected_rows


def delete_product(product_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        DELETE FROM products
        WHERE id = ?
    """, (product_id,))


    connection.commit()
    connection.close()


# ==================================================
# REVIEWS
# ==================================================

def add_review(
    product_id,
    user_id,
    rating,
    review
):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    try:

        cursor.execute("""
            INSERT INTO reviews
            (
                product_id,
                user_id,
                rating,
                review
            )
            VALUES (?, ?, ?, ?)
        """, (
            product_id,
            user_id,
            rating,
            review
        ))


        review_id = cursor.lastrowid

        connection.commit()
        connection.close()


        return review_id


    except sqlite3.IntegrityError:

        connection.close()

        return None


def get_reviews(product_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            reviews.id,
            users.name,
            reviews.rating,
            reviews.review
        FROM reviews
        JOIN users
        ON reviews.user_id = users.id
        WHERE reviews.product_id = ?
        ORDER BY reviews.id DESC
    """, (product_id,))


    reviews = cursor.fetchall()

    connection.close()


    return reviews


def get_rating_summary(product_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(AVG(rating), 0)
        FROM reviews
        WHERE product_id = ?
    """, (product_id,))


    result = cursor.fetchone()

    connection.close()


    return {
        "count": result[0],
        "average": round(result[1], 1)
    }


def get_user_review(product_id, user_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            rating,
            review
        FROM reviews
        WHERE product_id = ?
        AND user_id = ?
    """, (
        product_id,
        user_id
    ))


    review = cursor.fetchone()

    connection.close()


    return review


def get_rating_breakdown(product_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            rating,
            COUNT(*)
        FROM reviews
        WHERE product_id = ?
        GROUP BY rating
        ORDER BY rating DESC
    """, (product_id,))


    results = cursor.fetchall()

    connection.close()


    breakdown = {
        5: 0,
        4: 0,
        3: 0,
        2: 0,
        1: 0
    }


    for rating, count in results:

        breakdown[rating] = count


    return breakdown


# ==================================================
# ADMIN REVIEW MANAGEMENT
# ==================================================

def get_all_reviews():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            reviews.id,
            products.name,
            users.name,
            users.email,
            reviews.rating,
            reviews.review
        FROM reviews

        JOIN products
        ON reviews.product_id = products.id

        JOIN users
        ON reviews.user_id = users.id

        ORDER BY reviews.id DESC
    """)


    reviews = cursor.fetchall()

    connection.close()


    return reviews


def delete_review(review_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        DELETE FROM reviews
        WHERE id = ?
    """, (review_id,))


    connection.commit()
    connection.close()


# ==================================================
# WISHLIST
# ==================================================

def add_to_wishlist(
    product_id,
    user_id
):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    try:

        cursor.execute("""
            INSERT INTO wishlist
            (
                product_id,
                user_id
            )
            VALUES (?, ?)
        """, (
            product_id,
            user_id
        ))


        wishlist_id = cursor.lastrowid

        connection.commit()
        connection.close()


        return wishlist_id


    except sqlite3.IntegrityError:

        connection.close()

        return None


def remove_from_wishlist(
    product_id,
    user_id
):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        DELETE FROM wishlist
        WHERE product_id = ?
        AND user_id = ?
    """, (
        product_id,
        user_id
    ))


    connection.commit()
    connection.close()


def get_user_wishlist(user_id):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            products.id,
            products.name,
            products.price,
            products.description,
            products.image,
            products.category,
            products.stock
        FROM wishlist

        JOIN products
        ON wishlist.product_id = products.id

        WHERE wishlist.user_id = ?

        ORDER BY wishlist.id DESC
    """, (user_id,))


    wishlist = cursor.fetchall()

    connection.close()


    return wishlist


def is_product_in_wishlist(
    product_id,
    user_id
):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()


    cursor.execute("""
        SELECT id
        FROM wishlist
        WHERE product_id = ?
        AND user_id = ?
    """, (
        product_id,
        user_id
    ))


    result = cursor.fetchone()

    connection.close()


    return result is not None