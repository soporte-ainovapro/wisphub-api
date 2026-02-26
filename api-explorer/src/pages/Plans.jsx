import { Wifi } from 'lucide-react'
import EndpointCard from '../components/EndpointCard'

export default function Plans() {
    return (
        <div className="max-w-4xl mx-auto space-y-4">
            <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-emerald-500/15 border border-emerald-500/20">
                    <Wifi size={18} className="text-emerald-400" />
                </div>
                <div>
                    <h1 className="text-lg font-semibold text-[#f1f5f9]">Planes de Internet</h1>
                    <p className="text-xs text-[#475569]">/api/v1/internet-plans — dataset sincronizado en caché</p>
                </div>
            </div>

            <EndpointCard
                method="GET"
                path="/api/v1/internet-plans/"
                description="Lista todos los planes disponibles del proveedor"
                fields={[]}
                buildRequest={() => ({ url: '/api/v1/internet-plans/', body: null })}
            />

            <EndpointCard
                method="GET"
                path="/api/v1/internet-plans/{plan_id}"
                description="Obtiene atributos detallados de un plan específico"
                fields={[{ name: 'plan_id', label: 'Plan ID', placeholder: '10', required: true }]}
                buildRequest={({ plan_id }) => ({ url: `/api/v1/internet-plans/${plan_id}`, body: null })}
            />
        </div>
    )
}
