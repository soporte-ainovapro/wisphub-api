import { useState } from 'react'
import { Send, ChevronDown, ChevronUp } from 'lucide-react'
import { apiRequest, METHOD_COLORS } from '../config'
import ResponseViewer from './ResponseViewer'

export default function EndpointCard({ method, path, description, fields = [], buildRequest }) {
    const [values, setValues] = useState(() =>
        Object.fromEntries(fields.map((f) => [f.name, f.default ?? '']))
    )
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [expanded, setExpanded] = useState(false)

    const methodColor = METHOD_COLORS[method] ?? 'text-gray-400'

    const handleChange = (name, value) => {
        setValues((prev) => ({ ...prev, [name]: value }))
    }

    const handleSend = async () => {
        setLoading(true)
        setResult(null)
        setExpanded(true)
        try {
            const { url, body } = buildRequest(values)
            const res = await apiRequest(method, url, body)
            setResult(res)
        } catch (err) {
            setResult({ status: 0, data: { error: err.message }, elapsed: 0 })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="rounded-xl border border-[#1f2d47] bg-[#111827] hover:border-[#2d4060] transition-colors duration-200 overflow-hidden">
            {/* Card header */}
            <button
                onClick={() => setExpanded((v) => !v)}
                className="flex items-center gap-3 w-full px-5 py-4 text-left hover:bg-[#1a2235]/60 transition-colors duration-150"
            >
                <span className={`text-xs font-bold font-mono shrink-0 w-12 ${methodColor}`}>{method}</span>
                <code className="text-sm text-[#93c5fd] font-mono flex-1 min-w-0 truncate">{path}</code>
                <p className="hidden md:block text-xs text-[#475569] shrink-0 max-w-xs truncate">{description}</p>
                {expanded ? <ChevronUp size={15} className="text-[#475569] shrink-0" /> : <ChevronDown size={15} className="text-[#475569] shrink-0" />}
            </button>

            {/* Expandable body */}
            {expanded && (
                <div className="px-5 pb-5 border-t border-[#1f2d47]">
                    {fields.length > 0 && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 mt-4">
                            {fields.map((field) => (
                                <div key={field.name} className="flex flex-col gap-1">
                                    <label className="text-xs font-medium text-[#94a3b8]">
                                        {field.label}
                                        {field.required && <span className="text-red-400 ml-1">*</span>}
                                    </label>
                                    {field.type === 'textarea' ? (
                                        <textarea
                                            rows={3}
                                            value={values[field.name]}
                                            onChange={(e) => handleChange(field.name, e.target.value)}
                                            placeholder={field.placeholder ?? ''}
                                            className="bg-[#0f1829] border border-[#1f2d47] rounded-lg px-3 py-2 text-sm text-[#f1f5f9] font-mono placeholder-[#475569] focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 resize-none transition-colors"
                                        />
                                    ) : (
                                        <input
                                            type={field.type ?? 'text'}
                                            value={values[field.name]}
                                            onChange={(e) => handleChange(field.name, e.target.value)}
                                            placeholder={field.placeholder ?? ''}
                                            className="bg-[#0f1829] border border-[#1f2d47] rounded-lg px-3 py-2 text-sm text-[#f1f5f9] font-mono placeholder-[#475569] focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-colors"
                                        />
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    <button
                        onClick={handleSend}
                        disabled={loading}
                        className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors duration-150"
                    >
                        {loading ? (
                            <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                        ) : (
                            <Send size={14} />
                        )}
                        Enviar
                    </button>

                    <ResponseViewer result={result} loading={loading} />
                </div>
            )}
        </div>
    )
}
