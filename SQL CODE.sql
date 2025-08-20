CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    purchase_date DATE NOT NULL,
    shares NUMERIC(10, 4) NOT NULL,
    cost_basis NUMERIC(15, 2) NOT NULL,
    asset_class VARCHAR(50) NOT NULL
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    notes TEXT,
    FOREIGN KEY (ticker) REFERENCES assets(ticker) ON DELETE CASCADE
);
INSERT INTO assets (ticker, purchase_date, shares, cost_basis, asset_class) VALUES
('GOOG', '2023-01-15', 10.5, 15000.00, 'Equities'),
('AAPL', '2022-09-20', 25.0, 4250.00, 'Equities'),
('BTC', '2024-03-10', 0.5, 35000.00, 'Crypto'),
('AMZN', '2023-05-01', 5.0, 6500.00, 'Equities'),
('TSLA', '2023-11-22', 12.0, 2400.00, 'Equities');