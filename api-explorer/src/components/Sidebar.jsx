import { Users, Wifi, TicketCheck, Network } from 'lucide-react'

const NAV_ITEMS = [
    { id: 'clients', label: 'Clientes', icon: Users },
    { id: 'plans', label: 'Planes', icon: Wifi },
    { id: 'tickets', label: 'Tickets', icon: TicketCheck },
    { id: 'network', label: 'Red', icon: Network },
]

export default function Sidebar({ activePage, onNavigate }) {
    return (
        <aside className="w-16 md:w-56 flex flex-col shrink-0 border-r border-[#1f2d47] bg-[#111827] py-4 transition-all duration-300">
            {/* Logo mark */}
            <div className="flex items-center justify-center md:justify-start gap-3 px-4 mb-8">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shrink-0 shadow-lg">
                    <span className="text-white font-bold text-sm">W</span>
                </div>
                <span className="hidden md:block text-sm font-semibold text-[#f1f5f9] tracking-wide">WispHub</span>
            </div>

            {/* Navigation */}
            <nav className="flex flex-col gap-1 px-2">
                {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
                    const isActive = activePage === id
                    return (
                        <button
                            key={id}
                            onClick={() => onNavigate(id)}
                            title={label}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg w-full text-left transition-all duration-200 group
                ${isActive
                                    ? 'bg-blue-500/15 text-blue-400 border border-blue-500/20'
                                    : 'text-[#94a3b8] hover:text-[#f1f5f9] hover:bg-[#1a2235] border border-transparent'
                                }`}
                        >
                            <Icon size={18} className={`shrink-0 transition-colors ${isActive ? 'text-blue-400' : 'text-[#94a3b8] group-hover:text-[#f1f5f9]'}`} />
                            <span className="hidden md:block text-sm font-medium">{label}</span>
                            {isActive && <div className="hidden md:block ml-auto w-1.5 h-1.5 rounded-full bg-blue-400" />}
                        </button>
                    )
                })}
            </nav>

            {/* Footer */}
            <div className="mt-auto px-4 hidden md:block">
                <p className="text-[10px] text-[#475569] font-mono">FastAPI · v1 · HTTPX</p>
            </div>
        </aside>
    )
}
