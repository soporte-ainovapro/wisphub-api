import { Users } from 'lucide-react'
import EndpointCard from '../components/EndpointCard'

export default function Clients() {
    return (
        <div className="max-w-4xl mx-auto space-y-4">
            <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-blue-500/15 border border-blue-500/20">
                    <Users size={18} className="text-blue-400" />
                </div>
                <div>
                    <h1 className="text-lg font-semibold text-[#f1f5f9]">Clientes</h1>
                    <p className="text-xs text-[#475569]">/api/v1/clients — búsqueda, actualización y verificación</p>
                </div>
            </div>

            <EndpointCard
                method="GET"
                path="/api/v1/clients/"
                description="Retorna el pool de clientes en caché"
                fields={[]}
                buildRequest={() => ({ url: '/api/v1/clients/', body: null })}
            />

            <EndpointCard
                method="GET"
                path="/api/v1/clients/by-document/{document_id}"
                description="Búsqueda exacta por cédula / documento"
                fields={[{ name: 'document_id', label: 'Documento', placeholder: '123456789', required: true }]}
                buildRequest={({ document_id }) => ({ url: `/api/v1/clients/by-document/${document_id}`, body: null })}
            />

            <EndpointCard
                method="GET"
                path="/api/v1/clients/by-phone/{phone}"
                description="Búsqueda exacta por número de teléfono"
                fields={[{ name: 'phone', label: 'Teléfono', placeholder: '3000000000', required: true }]}
                buildRequest={({ phone }) => ({ url: `/api/v1/clients/by-phone/${phone}`, body: null })}
            />

            <EndpointCard
                method="GET"
                path="/api/v1/clients/by-service-id/{service_id}"
                description="Búsqueda por Service ID de WispHub"
                fields={[{ name: 'service_id', label: 'Service ID', placeholder: '100', required: true }]}
                buildRequest={({ service_id }) => ({ url: `/api/v1/clients/by-service-id/${service_id}`, body: null })}
            />

            <EndpointCard
                method="GET"
                path="/api/v1/clients/search?q={query}"
                description="Búsqueda flexible por nombre o dirección"
                fields={[{ name: 'q', label: 'Query (nombre / dirección)', placeholder: 'Juan Perez', required: true }]}
                buildRequest={({ q }) => ({ url: `/api/v1/clients/search?q=${encodeURIComponent(q)}`, body: null })}
            />

            <EndpointCard
                method="PUT"
                path="/api/v1/clients/{service_id}"
                description="Actualiza cédula y/o teléfono del perfil"
                fields={[
                    { name: 'service_id', label: 'Service ID', placeholder: '100', required: true },
                    { name: 'document', label: 'Documento', placeholder: '100100100' },
                    { name: 'phone', label: 'Teléfono', placeholder: '3000000000' },
                ]}
                buildRequest={({ service_id, document, phone }) => ({
                    url: `/api/v1/clients/${service_id}`,
                    body: {
                        ...(document && { document }),
                        ...(phone && { phone }),
                    },
                })}
            />

            <EndpointCard
                method="POST"
                path="/api/v1/clients/{service_id}/verify"
                description="Verifica identidad comparando datos de factura"
                fields={[
                    { name: 'service_id', label: 'Service ID', placeholder: '100', required: true },
                    { name: 'name', label: 'Nombre del cliente', placeholder: 'Esperanza Benitez Urbano' },
                    { name: 'address', label: 'Dirección', placeholder: 'Bellavista' },
                    { name: 'internet_plan_name', label: 'Plan', placeholder: '7MB PLUS' },
                    { name: 'internet_plan_price', label: 'Precio del plan', placeholder: '40000', type: 'number' },
                ]}
                buildRequest={({ service_id, name, address, internet_plan_name, internet_plan_price }) => ({
                    url: `/api/v1/clients/${service_id}/verify`,
                    body: {
                        ...(name && { name }),
                        ...(address && { address }),
                        ...(internet_plan_name && { internet_plan_name }),
                        ...(internet_plan_price && { internet_plan_price: parseFloat(internet_plan_price) }),
                    },
                })}
            />

            {/* ── Resolve: flujo sin cédula ni teléfono ── */}
            <div className="flex items-center gap-3 pt-4 pb-1">
                <div className="h-px flex-1 bg-[#1f2d47]" />
                <span className="text-xs text-[#475569] font-medium px-2">Sin cédula ni teléfono</span>
                <div className="h-px flex-1 bg-[#1f2d47]" />
            </div>

            <EndpointCard
                method="POST"
                path="/api/v1/clients/resolve"
                description="Identifica y verifica al cliente en una sola llamada (≥3 campos requeridos)"
                fields={[
                    { name: 'name', label: 'Nombre completo', placeholder: 'Esperanza Benitez Urbano' },
                    { name: 'address', label: 'Dirección', placeholder: 'Bellavista' },
                    { name: 'internet_plan_name', label: 'Plan de internet', placeholder: 'PLAN INTERNET 10MB PLUS' },
                    { name: 'internet_plan_price', label: 'Precio mensual', placeholder: '40000', type: 'number' },
                ]}
                buildRequest={({ name, address, internet_plan_name, internet_plan_price }) => ({
                    url: '/api/v1/clients/resolve',
                    body: {
                        ...(name && { name }),
                        ...(address && { address }),
                        ...(internet_plan_name && { internet_plan_name }),
                        ...(internet_plan_price && { internet_plan_price: parseFloat(internet_plan_price) }),
                    },
                })}
            />
        </div>
    )
}

