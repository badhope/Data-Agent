CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT,
    price REAL,
    stock_quantity INTEGER,
    created_date DATE
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    city TEXT
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    total_amount REAL,
    status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 示例数据
INSERT INTO products (product_name, category, price, stock_quantity, created_date) VALUES
('笔记本电脑 Pro', '电子设备', 8999.00, 150, '2024-01-01'),
('无线鼠标', '配件', 199.00, 500, '2024-01-05'),
('机械键盘', '配件', 599.00, 300, '2024-01-10'),
('显示器 27寸', '电子设备', 2499.00, 80, '2024-01-15'),
('USB-C 扩展坞', '配件', 399.00, 250, '2024-01-20');

INSERT INTO customers (customer_name, email, phone, city) VALUES
('张三', 'zhangsan@example.com', '13800138001', '北京'),
('李四', 'lisi@example.com', '13800138002', '上海'),
('王五', 'wangwu@example.com', '13800138003', '广州'),
('赵六', 'zhaoliu@example.com', '13800138004', '深圳'),
('孙七', 'sunqi@example.com', '13800138005', '杭州');

INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
(1, '2024-01-15', 9598.00, '已完成'),
(2, '2024-01-20', 199.00, '已发货'),
(3, '2024-01-25', 2499.00, '待处理'),
(1, '2024-02-01', 998.00, '已完成'),
(4, '2024-02-05', 8999.00, '已发货');

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 8999.00),
(1, 2, 3, 199.00),
(2, 2, 1, 199.00),
(3, 4, 1, 2499.00),
(4, 3, 1, 599.00),
(4, 2, 2, 199.00),
(5, 1, 1, 8999.00);
