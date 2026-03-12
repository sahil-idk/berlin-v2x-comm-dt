function ReadinessGauge({ score }) {
  if (!score) {
    return (
      <div className="flex flex-col items-center">
        <div className="relative w-24 h-24">
          <svg className="w-24 h-24 transform -rotate-90">
            <circle
              cx="48"
              cy="48"
              r="40"
              stroke="rgb(55 65 81)"
              strokeWidth="8"
              fill="none"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-gray-500">--</span>
          </div>
        </div>
        <span className="text-xs text-gray-500 mt-2">Not calculated</span>
      </div>
    );
  }

  const totalScore = Math.round(score.total_score);
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (totalScore / 100) * circumference;

  const getColor = () => {
    if (totalScore >= 70) return '#10b981'; // green
    if (totalScore >= 40) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const getStatus = () => {
    if (totalScore >= 70) return 'DT-Ready';
    if (totalScore >= 40) return 'Needs Correction';
    return 'Not Ready';
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 transform -rotate-90">
          {/* Background circle */}
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="rgb(55 65 81)"
            strokeWidth="8"
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke={getColor()}
            strokeWidth="8"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-1000 ease-out"
            style={{
              filter: `drop-shadow(0 0 10px ${getColor()}40)`
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color: getColor() }}>
            {totalScore}
          </span>
          <span className="text-xs text-gray-400">/100</span>
        </div>
      </div>
      <span 
        className="text-xs font-medium mt-2"
        style={{ color: getColor() }}
      >
        {getStatus()}
      </span>
    </div>
  );
}

export default ReadinessGauge;
