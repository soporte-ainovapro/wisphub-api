import { Network } from 'lucide-react'
import EndpointCard from '../components/EndpointCard'

export default function NetworkPage() {
    return (
        <div className="max-w-4xl mx-auto space-y-4">
            <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-violet-500/15 border border-violet-500/20">
                    <Network size={18} className="text-violet-400" />
                </div>
                <div>
                    <h1 className="text-lg font-semibold text-[#f1f5f9]">Red y Diagnósticos</h1>
                    <p className="text-xs text-[#475569]">/api/v1/ping — herramientas de diagnóstico asíncrono</p>
                </div>
            </div>

            <EndpointCard
                method="POST"
                path="/api/v1/{service_id}/ping/"
                description="Inicia un ping asíncrono al equipo del cliente"
                fields={[
                    { name: 'service_id', label: 'Service ID', placeholder: '100', required: true },
                    { name: 'pings', label: 'Número de pings', placeholder: '4', type: 'number', default: '4' },
                ]}
                buildRequest={({ service_id, pings }) => ({
                    url: `/api/v1/${service_id}/ping/`,
                    body: { pings: parseInt(pings) || 4 },
                })}
            />

            <EndpointCard
                method="GET"
                path="/api/v1/ping/{task_id}/"
                description="Consulta el resultado de un ping por Task ID"
                fields={[{ name: 'task_id', label: 'Task ID', placeholder: '123-abc-...', required: true }]}
                buildRequest={({ task_id }) => ({ url: `/api/v1/ping/${task_id}/`, body: null })}
            />
        </div>
    )
}
