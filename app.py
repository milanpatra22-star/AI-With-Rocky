from flask import (
    Flask,
    render_template,
    session,
    redirect,
    url_for,
    request
)

from werkzeug.utils import secure_filename

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import os

from database import (
    create_database,
    create_user,
    get_user_by_email,
    save_order,
    get_all_orders,
    get_orders_by_email,
    get_order,
    update_order_status,
    get_dashboard_stats,
    get_recent_orders,
    get_all_products,
    search_products,
    get_categories,
    get_product,
    add_product,
    update_product,
    decrease_stock,
    delete_product,
    add_review,
    get_reviews,
    get_rating_summary,
    get_user_review,
    get_rating_breakdown,
    get_all_reviews,
    delete_review,
    add_to_wishlist,
    remove_from_wishlist,
    get_user_wishlist,
    is_product_in_wishlist
)


app = Flask(__name__)

app.secret_key = "my_secret_key"


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"


UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}


ORDER_STATUSES = [
    "Pending",
    "Confirmed",
    "Shipped",
    "Delivered",
    "Cancelled"
]


def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    products = get_all_products()

    categories = get_categories()

    featured_products = products[:6]


    return render_template(
        "home.html",
        featured_products=featured_products,
        categories=categories
    )


# ==================================================
# REGISTER
# ==================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form[
            "name"
        ].strip()

        email = request.form[
            "email"
        ].strip().lower()

        password = request.form[
            "password"
        ]

        confirm_password = request.form[
            "confirm_password"
        ]


        if password != confirm_password:

            return render_template(
                "register.html",
                error="Passwords do not match"
            )


        if len(password) < 6:

            return render_template(
                "register.html",
                error="Password must be at least 6 characters"
            )


        existing_user = get_user_by_email(
            email
        )


        if existing_user:

            return render_template(
                "register.html",
                error="Email already registered"
            )


        hashed_password = generate_password_hash(
            password
        )


        user_id = create_user(
            name,
            email,
            hashed_password
        )


        if user_id is None:

            return render_template(
                "register.html",
                error="Email already registered"
            )


        session["customer_id"] = user_id
        session["customer_name"] = name
        session["customer_email"] = email


        return redirect(
            url_for("product_page")
        )


    return render_template(
        "register.html"
    )


# ==================================================
# LOGIN
# ==================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def customer_login():

    if request.method == "POST":

        email = request.form[
            "email"
        ].strip().lower()

        password = request.form[
            "password"
        ]


        user = get_user_by_email(
            email
        )


        if user is None:

            return render_template(
                "login.html",
                error="Invalid email or password"
            )


        if not check_password_hash(
            user[3],
            password
        ):

            return render_template(
                "login.html",
                error="Invalid email or password"
            )


        session["customer_id"] = user[0]
        session["customer_name"] = user[1]
        session["customer_email"] = user[2]


        return redirect(
            url_for("product_page")
        )


    return render_template(
        "login.html"
    )


# ==================================================
# CUSTOMER LOGOUT
# ==================================================

@app.route("/logout")
def customer_logout():

    session.pop(
        "customer_id",
        None
    )

    session.pop(
        "customer_name",
        None
    )

    session.pop(
        "customer_email",
        None
    )

    session.pop(
        "order",
        None
    )


    return redirect(
        url_for("home")
    )


# ==================================================
# PRODUCTS
# ==================================================

@app.route("/products")
def product_page():

    search = request.args.get(
        "search",
        ""
    ).strip()


    category = request.args.get(
        "category",
        ""
    ).strip()


    products = search_products(
        search,
        category
    )


    categories = get_categories()


    return render_template(
        "products.html",
        products=products,
        categories=categories,
        search=search,
        selected_category=category
    )


# ==================================================
# PRODUCT DETAILS
# ==================================================

@app.route(
    "/product/<int:product_id>"
)
def product_details(product_id):

    product = get_product(
        product_id
    )


    if product is None:

        return "Product not found", 404


    reviews = get_reviews(
        product_id
    )


    rating_summary = get_rating_summary(
        product_id
    )


    rating_breakdown = get_rating_breakdown(
        product_id
    )


    user_review = None

    in_wishlist = False


    if session.get(
        "customer_id"
    ):

        user_id = session[
            "customer_id"
        ]


        user_review = get_user_review(
            product_id,
            user_id
        )


        in_wishlist = is_product_in_wishlist(
            product_id,
            user_id
        )


    return render_template(
        "product_details.html",
        product=product,
        reviews=reviews,
        rating_summary=rating_summary,
        rating_breakdown=rating_breakdown,
        user_review=user_review,
        in_wishlist=in_wishlist
    )


# ==================================================
# SUBMIT REVIEW
# ==================================================

@app.route(
    "/product/<int:product_id>/review",
    methods=["POST"]
)
def submit_review(product_id):

    if not session.get(
        "customer_id"
    ):

        return redirect(
            url_for("customer_login")
        )


    product = get_product(
        product_id
    )


    if product is None:

        return "Product not found", 404


    rating_value = request.form.get(
        "rating",
        ""
    ).strip()


    review_text = request.form.get(
        "review",
        ""
    ).strip()


    try:

        rating = int(
            rating_value
        )

    except ValueError:

        return "Invalid rating", 400


    if rating < 1 or rating > 5:

        return (
            "Rating must be between 1 and 5",
            400
        )


    if not review_text:

        return (
            "Review cannot be empty",
            400
        )


    if len(review_text) > 500:

        return (
            "Review must be 500 characters or less",
            400
        )


    existing_review = get_user_review(
        product_id,
        session["customer_id"]
    )


    if existing_review:

        return (
            "You have already reviewed this product",
            400
        )


    review_id = add_review(
        product_id,
        session["customer_id"],
        rating,
        review_text
    )


    if review_id is None:

        return (
            "You have already reviewed this product",
            400
        )


    return redirect(
        url_for(
            "product_details",
            product_id=product_id
        )
    )


# ==================================================
# ADD TO WISHLIST
# ==================================================

@app.route(
    "/wishlist/add/<int:product_id>"
)
def wishlist_add(product_id):

    if not session.get(
        "customer_id"
    ):

        return redirect(
            url_for("customer_login")
        )


    product = get_product(
        product_id
    )


    if product is None:

        return "Product not found", 404


    add_to_wishlist(
        product_id,
        session["customer_id"]
    )


    return redirect(
        url_for(
            "product_details",
            product_id=product_id
        )
    )


# ==================================================
# REMOVE FROM WISHLIST
# ==================================================

@app.route(
    "/wishlist/remove/<int:product_id>"
)
def wishlist_remove(product_id):

    if not session.get(
        "customer_id"
    ):

        return redirect(
            url_for("customer_login")
        )


    remove_from_wishlist(
        product_id,
        session["customer_id"]
    )


    return redirect(
        url_for("wishlist")
    )


# ==================================================
# MY WISHLIST
# ==================================================

@app.route("/wishlist")
def wishlist():

    if not session.get(
        "customer_id"
    ):

        return redirect(
            url_for("customer_login")
        )


    products = get_user_wishlist(
        session["customer_id"]
    )


    return render_template(
        "wishlist.html",
        products=products
    )


# ==================================================
# ADD TO CART
# ==================================================

@app.route(
    "/add-to-cart/<int:product_id>"
)
def add_to_cart(product_id):

    product = get_product(
        product_id
    )


    if product is None:

        return "Product not found", 404


    cart = session.get(
        "cart",
        {}
    )


    if not isinstance(
        cart,
        dict
    ):

        cart = {}


    product_id_string = str(
        product_id
    )


    current_quantity = cart.get(
        product_id_string,
        0
    )


    if current_quantity >= product[6]:

        return (
            "Not enough stock available",
            400
        )


    cart[
        product_id_string
    ] = current_quantity + 1


    session["cart"] = cart


    return redirect(
        url_for("cart")
    )


# ==================================================
# INCREASE CART
# ==================================================

@app.route(
    "/increase/<int:product_id>"
)
def increase(product_id):

    product = get_product(
        product_id
    )


    if product is None:

        return "Product not found", 404


    cart = session.get(
        "cart",
        {}
    )


    if not isinstance(
        cart,
        dict
    ):

        cart = {}


    product_id_string = str(
        product_id
    )


    if product_id_string in cart:

        current_quantity = cart[
            product_id_string
        ]


        if current_quantity >= product[6]:

            return (
                "Not enough stock available",
                400
            )


        cart[
            product_id_string
        ] += 1


    session["cart"] = cart


    return redirect(
        url_for("cart")
    )


# ==================================================
# DECREASE CART
# ==================================================

@app.route(
    "/decrease/<int:product_id>"
)
def decrease(product_id):

    cart = session.get(
        "cart",
        {}
    )


    if not isinstance(
        cart,
        dict
    ):

        cart = {}


    product_id_string = str(
        product_id
    )


    if product_id_string in cart:

        cart[
            product_id_string
        ] -= 1


        if cart[
            product_id_string
        ] <= 0:

            del cart[
                product_id_string
            ]


    session["cart"] = cart


    return redirect(
        url_for("cart")
    )


# ==================================================
# REMOVE FROM CART
# ==================================================

@app.route(
    "/remove/<int:product_id>"
)
def remove(product_id):

    cart = session.get(
        "cart",
        {}
    )


    if not isinstance(
        cart,
        dict
    ):

        cart = {}


    product_id_string = str(
        product_id
    )


    if product_id_string in cart:

        del cart[
            product_id_string
        ]


    session["cart"] = cart


    return redirect(
        url_for("cart")
    )


# ==================================================
# CART
# ==================================================

@app.route("/cart")
def cart():

    cart = session.get(
        "cart",
        {}
    )


    if not isinstance(
        cart,
        dict
    ):

        cart = {}

        session["cart"] = cart


    cart_products = []

    total = 0

    cart_count = 0


    for product_id, quantity in cart.items():

        product = get_product(
            int(product_id)
        )


        if product is None:

            continue


        product_data = {

            "id": product[0],

            "name": product[1],

            "price": product[2],

            "description": product[3],

            "image": product[4],

            "category": product[5],

            "stock": product[6],

            "quantity": quantity,

            "subtotal": (
                product[2] * quantity
            )

        }


        cart_products.append(
            product_data
        )


        total += product_data[
            "subtotal"
        ]


        cart_count += quantity


    return render_template(
        "cart.html",
        cart_products=cart_products,
        total=total,
        cart_count=cart_count
    )


# ==================================================
# CHECKOUT
# ==================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():

    cart = session.get(
        "cart",
        {}
    )


    if not isinstance(
        cart,
        dict
    ):

        cart = {}


    if not cart:

        return redirect(
            url_for("cart")
        )


    cart_products = []

    total = 0


    for product_id, quantity in cart.items():

        product = get_product(
            int(product_id)
        )


        if product is None:

            continue


        if quantity > product[6]:

            return (
                f"Only {product[6]} items available for {product[1]}",
                400
            )


        subtotal = (
            product[2] * quantity
        )


        cart_products.append({

            "name": product[1],

            "price": product[2],

            "quantity": quantity,

            "subtotal": subtotal

        })


        total += subtotal


    if not cart_products:

        session["cart"] = {}

        return redirect(
            url_for("cart")
        )


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        address = request.form.get(
            "address",
            ""
        ).strip()

        if not name:
            return "Name is required", 400

        if not phone:
            return "Phone number is required", 400

        if not address:
            return "Delivery address is required", 400

        if not email and session.get("customer_email"):
            email = session["customer_email"]

        for product_id, quantity in cart.items():

            success = decrease_stock(
                int(product_id),
                quantity
            )


            if success == 0:

                return (
                    "Stock changed. Please try again.",
                    400
                )


        order_id = save_order(
            name,
            phone,
            email,
            address,
            total
        )


        order = {

            "id": order_id,

            "name": name,

            "phone": phone,

            "email": email,

            "address": address,

            "products": cart_products,

            "total": total,

            "status": "Pending"

        }


        session["order"] = order

        session["cart"] = {}


        return redirect(
            url_for("order_success")
        )


    return render_template(
        "checkout.html",
        cart_products=cart_products,
        total=total
    )


# ==================================================
# ORDER SUCCESS
# ==================================================

@app.route("/order-success")
def order_success():

    order = session.get(
        "order"
    )


    if not order:

        return redirect(
            url_for("home")
        )


    return render_template(
        "order_success.html",
        order=order
    )


# ==================================================
# MY ORDERS
# ==================================================

@app.route("/my-orders")
def my_orders():

    if not session.get(
        "customer_id"
    ):

        return redirect(
            url_for("customer_login")
        )


    customer_email = session[
        "customer_email"
    ]


    orders = get_orders_by_email(
        customer_email
    )


    return render_template(
        "my_orders.html",
        orders=orders,
        email=customer_email
    )


# ==================================================
# ADMIN LOGIN
# ==================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form[
            "username"
        ]

        password = request.form[
            "password"
        ]


        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session[
                "admin_logged_in"
            ] = True


            return redirect(
                url_for("admin_dashboard")
            )


        return render_template(
            "admin_login.html",
            error="Invalid username or password"
        )


    return render_template(
        "admin_login.html"
    )


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route(
    "/admin/dashboard"
)
def admin_dashboard():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    stats = get_dashboard_stats()

    recent_orders = get_recent_orders(
        5
    )


    return render_template(
        "admin_dashboard.html",
        stats=stats,
        recent_orders=recent_orders
    )


# ==================================================
# ADMIN PRODUCTS
# ==================================================

@app.route(
    "/admin/products"
)
def admin_products():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    products = get_all_products()


    return render_template(
        "admin_products.html",
        products=products
    )


# ==================================================
# ADD PRODUCT
# ==================================================

@app.route(
    "/admin/products/add",
    methods=["GET", "POST"]
)
def admin_add_product():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    if request.method == "POST":

        name = request.form[
            "name"
        ]

        price = float(
            request.form["price"]
        )

        description = request.form[
            "description"
        ]

        category = request.form[
            "category"
        ]

        stock = int(
            request.form["stock"]
        )


        image = request.files.get(
            "image"
        )


        image_filename = None


        if image and image.filename:

            if allowed_file(
                image.filename
            ):

                image_filename = secure_filename(
                    image.filename
                )


                image.save(
                    os.path.join(
                        app.config[
                            "UPLOAD_FOLDER"
                        ],
                        image_filename
                    )
                )

            else:

                return (
                    "Invalid image format",
                    400
                )


        add_product(
            name,
            price,
            description,
            image_filename,
            category,
            stock
        )


        return redirect(
            url_for("admin_products")
        )


    return render_template(
        "add_product.html"
    )


# ==================================================
# EDIT PRODUCT
# ==================================================

@app.route(
    "/admin/products/edit/<int:product_id>",
    methods=["GET", "POST"]
)
def admin_edit_product(product_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    product = get_product(
        product_id
    )


    if product is None:

        return "Product not found", 404


    if request.method == "POST":

        name = request.form[
            "name"
        ]

        price = float(
            request.form["price"]
        )

        description = request.form[
            "description"
        ]

        category = request.form[
            "category"
        ]

        stock = int(
            request.form["stock"]
        )


        image = request.files.get(
            "image"
        )


        image_filename = product[4]


        if image and image.filename:

            if allowed_file(
                image.filename
            ):

                image_filename = secure_filename(
                    image.filename
                )


                image.save(
                    os.path.join(
                        app.config[
                            "UPLOAD_FOLDER"
                        ],
                        image_filename
                    )
                )

            else:

                return (
                    "Invalid image format",
                    400
                )


        update_product(
            product_id,
            name,
            price,
            description,
            image_filename,
            category,
            stock
        )


        return redirect(
            url_for("admin_products")
        )


    return render_template(
        "edit_product.html",
        product=product
    )


# ==================================================
# DELETE PRODUCT
# ==================================================

@app.route(
    "/admin/products/delete/<int:product_id>"
)
def admin_delete_product(product_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    delete_product(
        product_id
    )


    return redirect(
        url_for("admin_products")
    )


# ==================================================
# ADMIN ORDERS
# ==================================================

@app.route(
    "/admin/orders"
)
def admin_orders():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    orders = get_all_orders()


    return render_template(
        "admin_orders.html",
        orders=orders
    )


# ==================================================
# UPDATE ORDER STATUS
# ==================================================

@app.route(
    "/admin/orders/status/<int:order_id>",
    methods=["POST"]
)
def admin_update_order_status(order_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    status = request.form[
        "status"
    ]


    if status not in ORDER_STATUSES:

        return (
            "Invalid order status",
            400
        )


    order = get_order(
        order_id
    )


    if order is None:

        return (
            "Order not found",
            404
        )


    update_order_status(
        order_id,
        status
    )


    return redirect(
        url_for("admin_orders")
    )


# ==================================================
# ADMIN REVIEWS
# ==================================================

@app.route(
    "/admin/reviews"
)
def admin_reviews():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    reviews = get_all_reviews()


    return render_template(
        "admin_reviews.html",
        reviews=reviews
    )


# ==================================================
# DELETE REVIEW
# ==================================================

@app.route(
    "/admin/reviews/delete/<int:review_id>"
)
def admin_delete_review(review_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    delete_review(
        review_id
    )


    return redirect(
        url_for("admin_reviews")
    )


# ==================================================
# ADMIN LOGOUT
# ==================================================

@app.route(
    "/admin/logout"
)
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )


    return redirect(
        url_for("admin_login")
    )


# ==================================================
# ABOUT
# ==================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ==================================================
# CONTACT
# ==================================================

@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# ==================================================
# DATABASE
# ==================================================

create_database()


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )