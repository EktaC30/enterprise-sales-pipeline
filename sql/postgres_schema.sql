-- Create database if not exists
CREATE DATABASE salesdb;

\c salesdb;

-- Create operational sales table
CREATE TABLE IF NOT EXISTS sales_table (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT NOT NULL,
    product_category VARCHAR(100),
    amount NUMERIC(12, 2),
    transaction_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);