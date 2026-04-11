-- Tabela de rotas monitoradas
CREATE TABLE monitored_routes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    departure_date DATE,
    return_date DATE,
    max_price DECIMAL(10,2),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de histórico de preços
CREATE TABLE price_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    route_id UUID REFERENCES monitored_routes(id),
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'BRL',
    airline VARCHAR(100),
    found_at TIMESTAMP DEFAULT NOW(),
    url TEXT
);

-- Tabela de alertas enviados
CREATE TABLE alerts_sent (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    route_id UUID REFERENCES monitored_routes(id),
    price DECIMAL(10,2),
    sent_at TIMESTAMP DEFAULT NOW(),
    telegram_message_id INTEGER
);

-- Index para performance
CREATE INDEX idx_price_history_route ON price_history(route_id);
CREATE INDEX idx_monitored_routes_active ON monitored_routes(active) WHERE active = true;
