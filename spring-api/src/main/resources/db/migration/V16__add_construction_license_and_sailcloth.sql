INSERT INTO warehouse_resources (name, sort_order, is_active, created_at, updated_at) VALUES
    ('Construction License', 535, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Sailcloth', 540, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;
