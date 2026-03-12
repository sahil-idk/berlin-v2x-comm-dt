import { useState } from 'react';
import ReadinessGauge from './ReadinessGauge';

const steps = [
  { id: 0, name: 'Upload', icon: '📁' },
  { id: 1, name: 'Range', icon: '📊' },
  { id: 2, name: 'Consistency', icon: '🔗' },
  { id: 3, name: 'Constants', icon: '🔍' },
  { id: 4, name: 'Completeness', icon: '📋' },
  { id: 5, name: 'Units', icon: '⚖️' },
  { id: 6, name: 'Clean & Export', icon: '✨' },
];

function Sidebar({ 
  currentStep, 
  setCurrentStep, 
  completedSteps, 
  canAccessStep, 
  readinessScore,
  sessionId,
  onShowPathLoss,
  showPathLoss,
  onShowEquations,
  showEquations,
  hasReferenceModels,
  domainInfo
}) {
  const [showDomainPanel, setShowDomainPanel] = useState(false);

  return (
    <div className="fixed left-0 top-16 bottom-0 w-64 bg-dt-card border-r border-gray-800 flex flex-col">
      {/* Domain Badge */}
      {domainInfo?.id && (
        <div className="p-3 border-b border-gray-800">
          <button
            onClick={() => setShowDomainPanel(!showDomainPanel)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-gray-800/60 hover:bg-gray-800 border border-gray-700 transition-all duration-200 group"
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-lg flex-shrink-0">{domainInfo.icon}</span>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white truncate">{domainInfo.name}</p>
                <p className="text-[10px] text-gray-500">v{domainInfo.version || '1.0'}</p>
              </div>
            </div>
            <svg
              className={`w-4 h-4 text-gray-500 transition-transform duration-200 flex-shrink-0 ${showDomainPanel ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Expandable Info Panel */}
          <div className={`overflow-hidden transition-all duration-300 ease-in-out ${showDomainPanel ? 'max-h-64 opacity-100 mt-2' : 'max-h-0 opacity-0'}`}>
            <div className="bg-gray-800/40 rounded-lg p-3 space-y-2 border border-gray-700/50">
              <p className="text-xs text-gray-400 leading-relaxed">{domainInfo.description}</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-900/50 rounded-md px-2 py-1.5 text-center">
                  <p className="text-lg font-bold text-dt-accent">{domainInfo.parameter_count}</p>
                  <p className="text-[10px] text-gray-500 uppercase tracking-wide">Params</p>
                </div>
                <div className="bg-gray-900/50 rounded-md px-2 py-1.5 text-center">
                  <p className="text-lg font-bold text-dt-accent">{domainInfo.preset_count}</p>
                  <p className="text-[10px] text-gray-500 uppercase tracking-wide">Presets</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {domainInfo.has_reference_models && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">
                    📈 Ref Models
                  </span>
                )}
                {domainInfo.has_consistency_rules && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    🔗 Rules
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Steps */}
      <div className="flex-1 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
          Pipeline
        </h3>
        <div className="space-y-2">
          {steps.map((step, index) => {
            const isCompleted = completedSteps.includes(step.id);
            const isCurrent = currentStep === step.id && !showPathLoss && !showEquations;
            const isAccessible = canAccessStep(step.id);

            return (
              <button
                key={step.id}
                onClick={() => isAccessible && setCurrentStep(step.id)}
                disabled={!isAccessible}
                className={`
                  w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                  ${isCurrent ? 'bg-dt-accent/20 text-white border border-dt-accent/50' : ''}
                  ${isCompleted && !isCurrent ? 'bg-dt-success/10 text-dt-success' : ''}
                  ${!isAccessible ? 'opacity-40 cursor-not-allowed' : 'hover:bg-gray-800'}
                  ${!isCurrent && !isCompleted && isAccessible ? 'text-gray-400' : ''}
                `}
              >
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm
                  ${isCompleted ? 'bg-dt-success text-white' : ''}
                  ${isCurrent ? 'gradient-accent text-white animate-pulse-glow' : ''}
                  ${!isCurrent && !isCompleted ? 'bg-gray-700' : ''}
                `}>
                  {isCompleted ? '✓' : step.icon}
                </div>
                <span className="text-sm font-medium">{step.name}</span>
              </button>
            );
          })}
        </div>

        {/* Path Loss Bonus Tab — only for domains with reference models */}
        {sessionId && hasReferenceModels && (
          <div className="mt-6 pt-6 border-t border-gray-700">
            <button
              onClick={onShowPathLoss}
              className={`
                w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                ${showPathLoss ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50' : 'text-gray-400 hover:bg-gray-800'}
              `}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${showPathLoss ? 'bg-purple-500 text-white' : 'bg-gray-700'}`}>
                📈
              </div>
              <span className="text-sm font-medium">Path Loss</span>
            </button>
          </div>
        )}

        {/* Custom Equations Tab — always visible when session active */}
        {sessionId && (
          <div className={`${!hasReferenceModels ? 'mt-6 pt-6 border-t border-gray-700' : 'mt-2'}`}>
            <button
              onClick={onShowEquations}
              className={`
                w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                ${showEquations ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50' : 'text-gray-400 hover:bg-gray-800'}
              `}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${showEquations ? 'bg-purple-500 text-white' : 'bg-gray-700'}`}>
                <span style={{fontFamily: 'serif', fontStyle: 'italic'}}>fx</span>
              </div>
              <span className="text-sm font-medium">Equations</span>
            </button>
          </div>
        )}
      </div>

      {/* Readiness Score */}
      <div className="p-4 border-t border-gray-800">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
          DT-Readiness
        </h3>
        <ReadinessGauge score={readinessScore} />
      </div>
    </div>
  );
}

export default Sidebar;
