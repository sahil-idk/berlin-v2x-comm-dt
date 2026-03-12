export function SummaryCard({ label, value, color = 'text-white', icon }) {
  return (
    <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
      <p className="text-sm text-gray-400 flex items-center gap-1">
        {icon && <span>{icon}</span>}
        {label}
      </p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

export function StepHeader({ step, title, description }) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">
        {step !== undefined && `Step ${step}: `}{title}
      </h2>
      {description && <p className="text-gray-400">{description}</p>}
    </div>
  );
}

export function ChartCard({ title, subtitle, children, className = '' }) {
  return (
    <div className={`bg-dt-card rounded-xl border border-gray-800 overflow-hidden ${className}`}>
      {(title || subtitle) && (
        <div className="px-4 py-3 border-b border-gray-800">
          {title && <h3 className="font-semibold text-white">{title}</h3>}
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
      )}
      <div className="p-4">
        {children}
      </div>
    </div>
  );
}

export function DataTable({ columns, rows, highlightColumns = [], maxColumns = 10 }) {
  const visibleCols = columns.slice(0, maxColumns);
  return (
    <div className="overflow-x-auto">
      {columns.length > maxColumns && (
        <div className="text-xs text-gray-500 px-4 py-2 border-b border-gray-800">
          Showing {visibleCols.length} of {columns.length} columns
        </div>
      )}
      <table className="w-full text-sm">
        <thead className="bg-gray-800/50">
          <tr>
            {visibleCols.map((col) => (
              <th
                key={col}
                className={`px-3 py-2 text-left text-gray-400 font-medium whitespace-nowrap ${
                  highlightColumns.includes(col) ? 'bg-yellow-500/10 text-yellow-400' : ''
                }`}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-gray-800/50 hover:bg-gray-800/30">
              {visibleCols.map((col) => (
                <td
                  key={col}
                  className={`px-3 py-1.5 text-gray-300 whitespace-nowrap font-mono text-xs ${
                    highlightColumns.includes(col) ? 'bg-yellow-500/5' : ''
                  }`}
                >
                  {row[col] !== null && row[col] !== undefined
                    ? typeof row[col] === 'number'
                      ? row[col].toFixed ? row[col].toFixed(4) : row[col]
                      : String(row[col]).slice(0, 20)
                    : '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <svg className="w-12 h-12 text-dt-accent animate-spin mx-auto mb-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p className="text-gray-400">{message}</p>
      </div>
    </div>
  );
}

export function ErrorAlert({ message, onRetry }) {
  return (
    <div className="bg-dt-error/10 border border-dt-error/50 rounded-lg p-4 text-dt-error">
      {message}
      {onRetry && <button onClick={onRetry} className="ml-4 underline">Retry</button>}
    </div>
  );
}

export function NextButton({ onClick, disabled, loading, text = 'Next Step →' }) {
  return (
    <div className="flex justify-end">
      <button
        onClick={onClick}
        disabled={disabled || loading}
        className="px-6 py-3 rounded-lg font-semibold gradient-accent text-white hover:opacity-90 transition-all disabled:opacity-50"
      >
        {loading ? 'Processing...' : text}
      </button>
    </div>
  );
}
