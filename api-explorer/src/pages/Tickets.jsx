import { TicketCheck } from 'lucide-react'
import EndpointCard from '../components/EndpointCard'

export default function Tickets() {
    return (
        <div className="max-w-4xl mx-auto space-y-4">
            <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/20">
                    <TicketCheck size={18} className="text-amber-400" />
                </div>
                <div>
                    <h1 className="text-lg font-semibold text-[#f1f5f9]">Tickets de Soporte</h1>
                    <p className="text-xs text-[#475569]">/api/v1/tickets — creación y consulta de tickets técnicos</p>
                </div>
            </div>

            <EndpointCard
                method="POST"
                path="/api/v1/tickets/"
                description="Crea un nuevo ticket técnico en WispHub"
                fields={[
                    { name: 'service_id', label: 'Service ID', placeholder: '100', required: true, type: 'number' },
                    { name: 'subject', label: 'Asunto', placeholder: 'Sin acceso a internet', required: true },
                    { name: 'description', label: 'Descripción', placeholder: 'El cliente reporta luz roja en el router.', required: true, type: 'textarea' },
                    { name: 'technician_id', label: 'Técnico ID', placeholder: '5', type: 'number' },
                    { name: 'zone_id', label: 'Zone ID', placeholder: '1', required: true, type: 'number' },
                ]}
                buildRequest={({ service_id, subject, description, technician_id, zone_id }) => ({
                    url: '/api/v1/tickets/',
                    body: {
                        service_id: parseInt(service_id),
                        subject,
                        description,
                        technician_id: technician_id ? parseInt(technician_id) : null,
                        zone_id: parseInt(zone_id),
                    },
                })}
            />

            <EndpointCard
                method="GET"
                path="/api/v1/tickets/zone-blocked/{zone_id}"
                description="Verifica si una zona tiene tickets bloqueados activos"
                fields={[{ name: 'zone_id', label: 'Zone ID', placeholder: '1', required: true }]}
                buildRequest={({ zone_id }) => ({ url: `/api/v1/tickets/zone-blocked/${zone_id}`, body: null })}
            />

            <EndpointCard
                method="GET"
                path="/api/v1/tickets/{ticket_id}"
                description="Obtiene detalle de un ticket por su ID"
                fields={[{ name: 'ticket_id', label: 'Ticket ID', placeholder: '500', required: true }]}
                buildRequest={({ ticket_id }) => ({ url: `/api/v1/tickets/${ticket_id}`, body: null })}
            />
        </div>
    )
}
