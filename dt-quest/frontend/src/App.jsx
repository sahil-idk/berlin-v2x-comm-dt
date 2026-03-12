import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import UploadStep from './components/UploadStep';
import RangeCheck from './components/RangeCheck';
import ConsistencyCheck from './components/ConsistencyCheck';
import ConstantCheck from './components/ConstantCheck';
import CompletenessCheck from './components/CompletenessCheck';
import UnitCheck from './components/UnitCheck';
import CleanExport from './components/CleanExport';
import PathLossPlot from './components/PathLossPlot';
import CustomEquations from './components/CustomEquations';
import { getReadinessScore, getDomains } from './utils/api';

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [sessionId, setSessionId] = useState(null);
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [mapping, setMapping] = useState({});
  const [pipelineResults, setPipelineResults] = useState({});
  const [readinessScore, setReadinessScore] = useState(null);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [showPathLoss, setShowPathLoss] = useState(false);
  const [showEquations, setShowEquations] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState('its-v2x');
  const [domainList, setDomainList] = useState([]);

  // Fetch domain list on mount for metadata
  useEffect(() => {
    getDomains().then(setDomainList).catch(console.error);
  }, []);

  // Derived domain info
  const currentDomainInfo = domainList.find(d => d.id === selectedDomain) || {};
  const domainName = currentDomainInfo.name || 'Domain';
  const hasReferenceModels = currentDomainInfo.has_reference_models || false;

  const updateReadinessScore = async () => {
    if (sessionId) {
      try {
        const score = await getReadinessScore(sessionId);
        setReadinessScore(score);
      } catch (err) {
        console.error('Failed to get readiness score:', err);
      }
    }
  };

  useEffect(() => {
    if (Object.keys(pipelineResults).length > 0) {
      updateReadinessScore();
    }
  }, [pipelineResults]);

  const handleStepComplete = (stepNum, results) => {
    setPipelineResults(prev => ({ ...prev, [`step${stepNum}`]: results }));
    setCompletedSteps(prev => [...new Set([...prev, stepNum])]);
  };

  const canAccessStep = (stepNum) => {
    if (stepNum === 0) return true;
    if (stepNum === 1) return sessionId && Object.keys(mapping).length > 0;
    return completedSteps.includes(stepNum - 1);
  };

  const renderStep = () => {
    if (showEquations && sessionId) {
      return <CustomEquations sessionId={sessionId} mapping={mapping} onBack={() => setShowEquations(false)} />;
    }

    if (showPathLoss && sessionId) {
      return <PathLossPlot sessionId={sessionId} onBack={() => setShowPathLoss(false)} />;
    }

    switch (currentStep) {
      case 0:
        return (
          <UploadStep
            sessionId={sessionId}
            setSessionId={setSessionId}
            datasetInfo={datasetInfo}
            setDatasetInfo={setDatasetInfo}
            mapping={mapping}
            setMapping={setMapping}
            selectedDomain={selectedDomain}
            setSelectedDomain={setSelectedDomain}
            onComplete={() => {
              handleStepComplete(0, { uploaded: true, mapped: true });
              setCurrentStep(1);
            }}
          />
        );
      case 1:
        return (
          <RangeCheck
            sessionId={sessionId}
            results={pipelineResults.step1}
            domainName={domainName}
            onComplete={(results) => {
              handleStepComplete(1, results);
              setCurrentStep(2);
            }}
          />
        );
      case 2:
        return (
          <ConsistencyCheck
            sessionId={sessionId}
            results={pipelineResults.step2}
            domainName={domainName}
            onComplete={(results) => {
              handleStepComplete(2, results);
              setCurrentStep(3);
            }}
          />
        );
      case 3:
        return (
          <ConstantCheck
            sessionId={sessionId}
            results={pipelineResults.step3}
            onComplete={(results) => {
              handleStepComplete(3, results);
              setCurrentStep(4);
            }}
          />
        );
      case 4:
        return (
          <CompletenessCheck
            sessionId={sessionId}
            results={pipelineResults.step4}
            onComplete={(results) => {
              handleStepComplete(4, results);
              setCurrentStep(5);
            }}
          />
        );
      case 5:
        return (
          <UnitCheck
            sessionId={sessionId}
            results={pipelineResults.step5}
            domainName={domainName}
            onComplete={(results) => {
              handleStepComplete(5, results);
              setCurrentStep(6);
            }}
          />
        );
      case 6:
        return (
          <CleanExport
            sessionId={sessionId}
            pipelineResults={pipelineResults}
            readinessScore={readinessScore}
            domainName={domainName}
            onComplete={(results) => {
              handleStepComplete(6, results);
            }}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex min-h-screen bg-dt-dark">
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 h-16 bg-dt-card border-b border-gray-800 z-50 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg gradient-accent flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">DT-QUEST</h1>
            <p className="text-xs text-gray-400">Digital Twin QUality Evaluation for Simulation-ready Transport</p>
          </div>
        </div>
        <button
          onClick={() => {
            setCurrentStep(0);
            setSessionId(null);
            setDatasetInfo(null);
            setMapping({});
            setPipelineResults({});
            setReadinessScore(null);
            setCompletedSteps([]);
            setShowPathLoss(false);
            setShowEquations(false);
            setSelectedDomain('its-v2x');
          }}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors"
        >
          Upload New
        </button>
      </div>

      {/* Sidebar */}
      <Sidebar
        currentStep={currentStep}
        setCurrentStep={setCurrentStep}
        completedSteps={completedSteps}
        canAccessStep={canAccessStep}
        readinessScore={readinessScore}
        sessionId={sessionId}
        onShowPathLoss={() => { setShowPathLoss(true); setShowEquations(false); }}
        showPathLoss={showPathLoss}
        onShowEquations={() => { setShowEquations(true); setShowPathLoss(false); }}
        showEquations={showEquations}
        hasReferenceModels={hasReferenceModels}
        domainInfo={currentDomainInfo}
      />

      {/* Main Content */}
      <div className="flex-1 ml-64 mt-16 p-8">
        <div className="max-w-7xl mx-auto animate-fade-in">
          {renderStep()}
        </div>
      </div>
    </div>
  );
}

export default App;
