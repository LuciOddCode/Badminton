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
      const processResponse = await axios.post(`http://localhost:8000/process/${filename}`);

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
            <div className="relative bg-gray-800 rounded-2xl overflow-hidden shadow-2xl border border-gray-700">
              <h3 className="text-xl font-bold p-4 bg-gray-700/50">Original Video</h3>
              <video
                src={preview}
                controls
                className="w-full h-auto block"
              />
            </div>
          )}

          {processedVideoUrl && (
            <div className="relative bg-gray-800 rounded-2xl overflow-hidden shadow-2xl border border-gray-700">
              <h3 className="text-xl font-bold p-4 bg-gray-700/50 text-shuttle">Processed Video</h3>
              <video
                src={processedVideoUrl}
                controls
                className="w-full h-auto block"
              />
            </div>
          )}
        </div>

        {/* Right Panel: Controls & Results */}
        <div className="space-y-6">
          <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-xl">
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
            <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-xl max-h-[600px] overflow-y-auto">
              <h3 className="text-2xl font-bold mb-4 text-shuttle sticky top-0 bg-gray-800 pb-2">Match Decisions</h3>
              <div className="space-y-3">
                {results.map((res, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg border border-gray-600">
                    <span className="font-medium text-white">Frame {res.frame}</span>
                    <span className={`font-bold px-3 py-1 rounded ${res.decision === 'IN' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                      {res.decision}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
