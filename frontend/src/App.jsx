import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [processedVideoUrl, setProcessedVideoUrl] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('doubles'); // 'singles' or 'doubles'
  const [shotType, setShotType] = useState('rally'); // 'serve' or 'rally'

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setProcessedVideoUrl(null);
      setResults([]);
      setError(null);
      setStatus('');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setStatus('Uploading video...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Upload
      const uploadResponse = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const filename = uploadResponse.data.filename;
      setStatus('Processing video (this may take a while)...');

      // 2. Process
      const processResponse = await axios.post(`http://localhost:8000/process/${filename}?mode=${mode}&shot_type=${shotType}`);

      // Assuming the backend returns the full path, we need to convert it to a URL
      // Since we mounted /outputs, we can construct the URL
      // The backend returns "output_video": "outputs\\processed_filename.mp4"
      const outputFilename = processResponse.data.output_video.split(/[\\/]/).pop();
      setProcessedVideoUrl(`http://localhost:8000/outputs/${outputFilename}`);
      setResults(processResponse.data.results_summary);
      setStatus('Processing complete!');

    } catch (err) {
      console.error(err);
      setError('Failed to process video. Ensure backend is running.');
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <header className="mb-10 text-center">
        <h1 className="text-5xl font-bold text-shuttle mb-2">ALiCaS-B</h1>
        <p className="text-gray-400 text-lg">Automated Line Call System for Badminton</p>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Panel: Upload & Preview */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-xl backdrop-blur-sm bg-opacity-50">
            <div className="border-2 border-dashed border-gray-600 rounded-xl p-8 text-center hover:border-shuttle transition-colors cursor-pointer relative"
              onClick={() => document.getElementById('fileInput').click()}>
              <input
                type="file"
                id="fileInput"
                className="hidden"
                accept="video/*"
                onChange={handleFileChange}
              />
              <p className="text-xl font-medium">Click to upload video or drag and drop</p>
              <p className="text-sm text-gray-500 mt-2">MP4, AVI supported</p>
            </div>
            {file && <p className="mt-4 text-center text-shuttle font-medium">{file.name}</p>}
          </div>

          {preview && !processedVideoUrl && (
            <div className="relative bg-gray-800 rounded-2xl overflow-hidden shadow-2xl border border-gray-700 flex justify-center bg-black">
              <h3 className="absolute top-0 left-0 w-full text-xl font-bold p-4 bg-gradient-to-b from-gray-900/80 to-transparent z-10">Original Video</h3>
              <video
                src={preview}
                controls
                className="w-full max-h-[60vh] object-contain block"
              />
            </div>
          )}

          {processedVideoUrl && (
            <div className="relative bg-gray-800 rounded-2xl overflow-hidden shadow-2xl border border-gray-700 flex justify-center bg-black">
              <h3 className="absolute top-0 left-0 w-full text-xl font-bold p-4 bg-gradient-to-b from-gray-900/80 to-transparent text-shuttle z-10">Processed Video</h3>
              <video
                src={processedVideoUrl}
                controls
                className="w-full max-h-[60vh] object-contain block"
              />
            </div>
          )}
        </div>

        {/* Right Panel: Controls & Results */}
        <div className="space-y-6">
          <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-xl">

            {/* Mode Selection */}
            <div className="mb-4 flex bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setMode('singles')}
                className={`flex-1 py-2 rounded-md font-bold transition-all ${mode === 'singles' ? 'bg-shuttle text-gray-900 shadow' : 'text-gray-400 hover:text-white'}`}
              >
                Singles
              </button>
              <button
                onClick={() => setMode('doubles')}
                className={`flex-1 py-2 rounded-md font-bold transition-all ${mode === 'doubles' ? 'bg-shuttle text-gray-900 shadow' : 'text-gray-400 hover:text-white'}`}
              >
                Doubles
              </button>
            </div>

            {/* Shot Type Selection */}
            <div className="mb-6 flex bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setShotType('serve')}
                className={`flex-1 py-2 rounded-md font-bold transition-all ${shotType === 'serve' ? 'bg-blue-500 text-white shadow' : 'text-gray-400 hover:text-white'}`}
              >
                Serve
              </button>
              <button
                onClick={() => setShotType('rally')}
                className={`flex-1 py-2 rounded-md font-bold transition-all ${shotType === 'rally' ? 'bg-blue-500 text-white shadow' : 'text-gray-400 hover:text-white'}`}
              >
                Rally
              </button>
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className={`w-full py-4 rounded-xl font-bold text-xl transition-all transform hover:scale-105 ${!file || loading
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-shuttle text-court-light hover:bg-yellow-400 shadow-lg shadow-yellow-900/20'
                }`}
            >
              {loading ? 'Processing...' : 'Analyze Match'}
            </button>

            {status && (
              <div className="mt-4 text-center font-medium text-blue-300 animate-pulse">
                {status}
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-900/50 border border-red-500 rounded-xl text-red-200">
                {error}
              </div>
            )}
          </div>

          {results.length > 0 && (
            <div className="bg-gray-800 p-8 rounded-2xl border border-gray-700 shadow-xl text-center">
              <h3 className="text-2xl font-bold mb-6 text-shuttle">Final Decision</h3>

              <div className={`text-8xl font-black py-12 rounded-2xl shadow-inner ${results[results.length - 1].decision === 'IN' ? 'bg-green-600 text-white shadow-green-900/50' : 'bg-red-600 text-white shadow-red-900/50'}`}>
                {results[results.length - 1].decision}
              </div>

              <p className="mt-6 text-gray-400 text-lg">
                Impact detected at Frame {results[results.length - 1].frame}
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
