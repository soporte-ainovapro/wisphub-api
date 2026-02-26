import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Clients from './pages/Clients'
import Plans from './pages/Plans'
import Tickets from './pages/Tickets'
import Network from './pages/Network'
import { Zap } from 'lucide-react'

const PAGES = {
  clients: Clients,
  plans: Plans,
  tickets: Tickets,
  network: Network,
}

export default function App() {
  const [page, setPage] = useState('clients')
  const PageComponent = PAGES[page]

  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0e1a]">
      <Sidebar activePage={page} onNavigate={setPage} />
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center gap-3 px-6 py-4 border-b border-[#1f2d47] bg-[#111827]">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/30">
              <Zap size={16} className="text-blue-400" />
            </div>
            <span className="font-semibold text-[#f1f5f9]">WispHub API Explorer</span>
          </div>
          <span className="text-[#475569] text-sm ml-1">/ v1</span>
          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-[#475569] font-mono">localhost:8000</span>
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="API conectada (proxy)"></div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          <PageComponent />
        </main>
      </div>
    </div>
  )
}
