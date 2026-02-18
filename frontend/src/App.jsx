import { useState, useEffect } from 'react';
import UrlInput from './components/UrlInput';
import ProcessingStatus from './components/ProcessingStatus';
import VideoPreview from './components/VideoPreview';
import ActionButtons from './components/ActionButtons';
import { generateVideo } from './api/client';
import { useJobPolling } from './hooks/useJobPolling';

function App() {
  const [jobId, setJobId] = useState(null);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false);

  const { status: jobStatus, error: pollingError } = useJobPolling(jobId);

  useEffect(() => {
    if (pollingError) setError(pollingError);
  }, [pollingError]);

  useEffect(() => {
    if (jobStatus?.status === 'failed') {
      setError(jobStatus.message || 'Video generation failed');
    }
  }, [jobStatus]);

  const handleSubmit = async (url) => {
    setError(null);
    setJobId(null);

    try {
      const result = await generateVideo(url);
      setJobId(result.job_id);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleGenerate = () => {
    const form = document.querySelector('form');
    if (form) form.requestSubmit();
  };

  const handleReset = () => {
    setJobId(null);
    setError(null);
  };

  const isProcessing = jobStatus && !['completed', 'failed'].includes(jobStatus.status) && !error;
  const isComplete = jobStatus?.status === 'completed';
  const videoPath = jobStatus?.video_path;
  const stage = jobStatus?.stage;
  const stageDetail = jobStatus?.stage_detail;

  // Derive overall status string for ProcessingStatus
  let displayStatus = 'idle';
  if (error) displayStatus = 'failed';
  else if (isComplete) displayStatus = 'completed';
  else if (isProcessing) displayStatus = 'processing';

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="bg-slate-100 dark:bg-slate-900 min-h-screen flex flex-col items-center justify-center p-4 sm:p-8 transition-colors">
        {/* Dark mode toggle */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="fixed top-4 right-4 p-2 rounded-lg bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
        >
          {darkMode ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>

        <main className="w-full max-w-[1000px] bg-white dark:bg-slate-800 rounded-2xl shadow-xl dark:shadow-none border border-slate-200 dark:border-slate-700 overflow-hidden flex flex-col md:flex-row min-h-[700px]">
          {/* Left Panel */}
          <div className="flex-1 p-8 sm:p-10 flex flex-col gap-10 border-b md:border-b-0 md:border-r border-slate-100 dark:border-slate-700">
            {/* Header */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className="text-blue-600 text-3xl">🚀</span>
                <h1 className="text-slate-900 dark:text-white text-2xl font-black tracking-tight">
                  Website <span className="text-slate-400 font-medium mx-1">&rarr;</span> Ad
                </h1>
              </div>
              <p className="text-slate-500 dark:text-slate-400 text-sm font-medium leading-relaxed">
                Turn any website into a promo video with multi-agent AI.
              </p>
            </div>

            {/* URL Input & Status */}
            <div className="flex flex-col gap-8 flex-1">
              <UrlInput onSubmit={handleSubmit} isDisabled={isProcessing} />

              {error && (
                <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm">
                  <strong>Error:</strong> {error}
                  <button
                    onClick={handleReset}
                    className="ml-3 underline text-red-500 hover:text-red-700"
                  >
                    Try again
                  </button>
                </div>
              )}

              <ProcessingStatus
                jobStatus={displayStatus}
                stage={stage}
                stageDetail={stageDetail}
              />
            </div>
          </div>

          {/* Right Panel */}
          <div className="flex-1 bg-slate-50 dark:bg-slate-900/50 p-8 flex flex-col justify-between gap-8">
            <VideoPreview
              videoPath={videoPath}
              isLoading={isProcessing && (stage === 'rendering' || stage === 'generating')}
              stage={stage}
              stageDetail={stageDetail}
            />

            <ActionButtons
              onGenerate={handleGenerate}
              isGenerating={isProcessing}
              canDownload={isComplete && !!videoPath}
              videoPath={videoPath}
            />
          </div>
        </main>

        {/* Footer */}
        <p className="mt-6 text-slate-400 text-xs">
          Powered by AI &bull; Built with Remotion
        </p>
      </div>
    </div>
  );
}

export default App;
