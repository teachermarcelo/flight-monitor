// ⚠️ IMPORTANTE: Substitua pelos seus dados do Supabase
// Vá em Supabase > Project Settings > API
const SUPABASE_URL = 'https://rvgcniaowzmsudzliozf.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_N_xCS0lbbTvG7qWTpAw0ag_vlg1lbHb';

// Headers para requisições
const headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
    'Content-Type': 'application/json'
};

// Função para buscar dados do Supabase
async function fetchFromSupabase(table, options = {}) {
    const url = new URL(`${SUPABASE_URL}/rest/v1/${table}`);
    
    if (options.select) {
        url.searchParams.append('select', options.select);
    }
    if (options.eq) {
        Object.entries(options.eq).forEach(([key, value]) => {
            url.searchParams.append(key, `eq.${value}`);
        });
    }
    if (options.order) {
        url.searchParams.append('order', `${options.order.column}.${options.order.descending ? 'desc' : 'asc'}`);
    }
    if (options.limit) {
        url.searchParams.append('limit', options.limit);
    }
    
    const response = await fetch(url, { headers });
    return response.json();
}

// Atualiza estatísticas
async function updateStats() {
    try {
        const routes = await fetchFromSupabase('monitored_routes');
        const prices = await fetchFromSupabase('price_history');
        const alerts = await fetchFromSupabase('alerts_sent');
        
        // Filtra rotas ativas
        const activeRoutes = routes.filter(r => r.active);
        
        document.getElementById('total-routes').textContent = activeRoutes.length;
        document.getElementById('total-prices').textContent = prices.length;
        document.getElementById('total-alerts').textContent = alerts.length;
        
        // Atualiza data
        document.getElementById('last-update').textContent = 
            `Última atualização: ${new Date().toLocaleString('pt-BR')}`;
    } catch (error) {
        console.error('Erro ao buscar estatísticas:', error);
    }
}

// Atualiza tabela de rotas
async function updateRoutesTable() {
    try {
        const routes = await fetchFromSupabase('monitored_routes', {
            eq: { active: true }
        });
        
        const tbody = document.getElementById('routes-table');
        tbody.innerHTML = '';
        
        for (const route of routes) {
            // Busca último preço
            const prices = await fetchFromSupabase('price_history', {
                eq: { route_id: route.id },
                order: { column: 'found_at', descending: true },
                limit: 1
            });
            
            const currentPrice = prices[0];
            
            // Determina status
            let status = '<span class="badge badge-warning">Monitorando</span>';
            if (currentPrice && route.max_price && currentPrice.price <= route.max_price) {
                status = '<span class="badge badge-success">🔥 Oferta!</span>';
            }
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${route.origin} → ${route.destination}</strong></td>
                <td>${currentPrice ? `R$ ${currentPrice.price.toLocaleString('pt-BR', {minimumFractionDigits: 2})}` : 'N/A'}</td>
                <td>${route.max_price ? `R$ ${route.max_price.toLocaleString('pt-BR', {minimumFractionDigits: 2})}` : 'N/A'}</td>
                <td>${currentPrice?.airline || 'N/A'}</td>
                <td>${status}</td>
            `;
            
            tbody.appendChild(row);
        }
        
        if (routes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">Nenhuma rota monitorada</td></tr>';
        }
    } catch (error) {
        console.error('Erro ao buscar rotas:', error);
        document.getElementById('routes-table').innerHTML = 
            '<tr><td colspan="5" class="loading">Erro ao carregar dados</td></tr>';
    }
}

// Inicializa dashboard
async function initDashboard() {
    await updateStats();
    await updateRoutesTable();
    
    // Atualiza a cada 5 minutos
    setInterval(() => {
        updateStats();
        updateRoutesTable();
    }, 5 * 60 * 1000);
}

// Inicia quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', initDashboard);
