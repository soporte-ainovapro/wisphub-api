import { Clock, CheckCircle, AlertCircle, XCircle } from 'lucide-react'

function syntaxHighlight(json) {
    if (typeof json !== 'string') {
        json = JSON.stringify(json, null, 2)
    }
    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(\.\d+)?([eE][+-]?\d+)?)/g,
        (match) => {
            let cls = 'json-number'
            if (/^"/.test(match)) {
                cls = /:$/.test(match) ? 'json-key' : 'json-string'
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean'
            } else if (/null/.test(match)) {
                cls = 'json-null'
            }
            return `<span class="${cls}">${match}</span>`
        }
    )
}

function StatusBadge({ status }) {
    if (!status) return null
    let color, Icon, label
    if (status >= 200 && status < 300) {
        color = 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'
        Icon = CheckCircle
        label = 'OK'
    } else if (status >= 400 && status < 500) {
        color = 'text-amber-400 bg-amber-400/10 border-amber-400/20'
        Icon = AlertCircle
        label = 'Error'
    } else if (status >= 500) {
        color = 'text-red-400 bg-red-400/10 border-red-400/20'
        Icon = XCircle
        label = 'Server Error'
    } else {
        color = 'text-blue-400 bg-blue-400/10 border-blue-400/20'
        Icon = CheckCircle
        label = 'Info'
    }
    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-semibold font-mono ${color}`}>
            <Icon size={12} />
            {status} {label}
        </span>
    )
}

export default function ResponseViewer({ result, loading }) {
    if (loading) {
        return (
            <div className="mt-4 rounded-xl border border-[#1f2d47] bg-[#0f1829] p-6 flex items-center justify-center gap-3 text-[#94a3b8]">
                <span className="w-4 h-4 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
                <span className="text-sm font-mono">Enviando solicitud...</span>
            </div>
        )
    }

    if (!result) return null

    const { status, data, elapsed } = result

    return (
        <div className="mt-4 rounded-xl border border-[#1f2d47] bg-[#0f1829] overflow-hidden">
            {/* Header bar */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-[#1f2d47]">
                <StatusBadge status={status} />
                <div className="flex items-center gap-1.5 ml-auto text-[#475569] text-xs font-mono">
                    <Clock size={11} />
                    <span>{elapsed}ms</span>
                </div>
            </div>

            {/* JSON body */}
            <pre
                className="text-xs font-mono leading-relaxed p-4 overflow-x-auto max-h-96 text-[#94a3b8]"
                dangerouslySetInnerHTML={{
                    __html: data !== null
                        ? syntaxHighlight(data)
                        : '<span class="json-null">null (sin cuerpo de respuesta)</span>',
                }}
            />
        </div>
    )
}
