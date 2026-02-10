import React, { useState, useEffect } from 'react';

const LoadingScreen = ({ fileName = "Resume.pdf" }) => {
  const [progress, setProgress] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [steps, setSteps] = useState([
    { id: '1', label: 'Parsing document structure', status: 'pending' },
    { id: '2', label: 'Identifying industry keywords', status: 'pending' },
    { id: '3', label: 'Comparing against job descriptions', status: 'pending' },
    { id: '4', label: 'Generating final ATS report', status: 'pending' },
  ]);

  useEffect(() => {
    const totalDuration = 5000;
    const stepDuration = totalDuration / steps.length;
    const progressInterval = 50;
    const progressIncrement = (100 / totalDuration) * progressInterval;

    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        const newProgress = Math.min(prev + progressIncrement, 100);
        return newProgress;
      });
    }, progressInterval);

    const stepTimer = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < steps.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, stepDuration);

    return () => {
      clearInterval(progressTimer);
      clearInterval(stepTimer);
    };
  }, [steps.length]);

  useEffect(() => {
    setSteps((prevSteps) =>
      prevSteps.map((step, index) => {
        if (index < currentStepIndex) {
          return { ...step, status: 'completed' };
        } else if (index === currentStepIndex) {
          return { ...step, status: 'in-progress' };
        }
        return step;
      })
    );
  }, [currentStepIndex]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100/10 to-gray-50 flex items-center justify-center px-6">
      <div className="max-w-2xl w-full">
        <div className="animate-fadeIn">
          {/* Logo/Icon */}
          <div className="flex justify-center mb-8">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center animate-spin-slow">
              <svg className="w-10 h-10 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          </div>

          {/* Title */}
          <div className="text-center mb-4">
            <h1 className="text-3xl md:text-4xl font-bold mb-2 text-gray-900">
              Analyzing Your Resume
            </h1>
            <p className="text-gray-600">
              Our AI is extracting key insights to optimize your ATS score
              <br />
              and matching you with relevant industry benchmarks.
            </p>
          </div>

          {/* Progress Card */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 mt-8">
            {/* Progress Bar */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-900">Overall Progress</span>
                <span className="text-sm font-bold text-gray-900">
                  {Math.round(progress)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-black h-2 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Current Step Info */}
            <div className="mb-6 pb-6 border-b border-gray-200">
              <p className="text-sm text-gray-600 mb-1">
                Step {currentStepIndex + 1} of {steps.length}: {steps[currentStepIndex]?.label}
              </p>
              <p className="text-xs text-gray-500">
                Estimated time: {Math.max(5 - currentStepIndex, 1)}s
              </p>
            </div>

            {/* Steps List */}
            <div className="space-y-4">
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  className="flex items-start gap-3"
                  style={{
                    animation: `slideIn 0.3s ease-out ${index * 0.1}s both`
                  }}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {step.status === 'completed' ? (
                      <div className="w-6 h-6 bg-black rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    ) : step.status === 'in-progress' ? (
                      <div className="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center">
                        <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                      </div>
                    ) : (
                      <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-gray-400 rounded-full" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm ${
                      step.status === 'completed' 
                        ? 'text-gray-900' 
                        : step.status === 'in-progress'
                        ? 'text-gray-900 font-medium'
                        : 'text-gray-500'
                    }`}>
                      {step.label}
                    </p>
                    {step.status === 'in-progress' && (
                      <p className="text-xs text-gray-500 mt-1">
                        In progress...
                      </p>
                    )}
                    {step.status === 'completed' && (
                      <p className="text-xs text-gray-900 mt-1">
                        Completed
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* File Info */}
          <div className="mt-6 flex items-center justify-center gap-3 text-sm text-gray-600">
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="font-medium">{fileName}</span>
              <span className="text-xs">• Processing...</span>
            </div>
          </div>

          {/* Info Message */}
          <p className="mt-6 text-center text-sm text-gray-600 flex items-center justify-center gap-2">
            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
              <circle cx="8" cy="8" r="8" className="text-gray-200" />
              <path
                d="M8 4a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 018 4zm0 8a1 1 0 100-2 1 1 0 000 2z"
                className="text-gray-900"
              />
            </svg>
            Don't close this window. Your analysis will be ready shortly.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;
