import React, { useState, useRef } from 'react';
import { useNavigate } from "react-router-dom";




const UploadResumePage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  // Handle file selection
  const handleFileSelect = (file) => {
    if (file && file.type === 'application/pdf') {
      if (file.size <= 10 * 1024 * 1024) { // 10MB limit
        setSelectedFile(file);
      } else {
        alert('File size must be less than 10MB');
      }
    } else {
      alert('Please upload a PDF file');
    }
  };

  // Handle file input change
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  // Handle drag and drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  // Handle browse button click
  const handleBrowseClick = () => {
    fileInputRef.current.click();
  };

  // Handle form submission
  const handleSubmit = async () => {
    if (!selectedFile) {
      alert("Please upload your resume");
      return;
    }
      // 🚀 instantly show loading screen
    navigate("/loading", {
      state: { fileName: selectedFile.name, jobDescription: jobDescription }});
      
    await new Promise(resolve => setTimeout(resolve, 5000));
  
    try {
      const formData = new FormData();
      formData.append("resume", selectedFile);
      formData.append("job_description", jobDescription);
  
      const response = await fetch(
        "http://127.0.0.1:8000/api/analyse_resume",
        {
          method: "POST",
          body: formData,
        }
      );
  
      if (!response.ok) {
        throw new Error("Failed to analyze resume");
      }
  
      const data = await response.json();
      
    //   console.log("Analysis result:", data);
  
    //   alert("Resume analyzed successfully!");
    //   // later: navigate("/results", { state: data });
  
    // } catch (error) {
    //   console.error(error);
    //   alert("Something went wrong. Check backend logs.");
    // }

    navigate("/results", { state: data });
    } catch (error) {
      if (error.message === "Failed to analyze resume") {
        navigate("/error", { state: { error: error.message } });
      }
    }
  };
  // Remove selected file
  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-3">
            {/* Back Button */}
            <button 
              onClick={() => window.history.back()}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            {/* Logo */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span className="text-lg font-bold text-gray-900">ResumeGrow</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Title Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3">
            Upload Your Resume
          </h1>
          <p className="text-lg text-gray-600">
            Get instant ATS analysis and actionable insights
          </p>
        </div>

        {/* Upload Area */}
        <div className="bg-white rounded-2xl shadow-sm border-2 border-gray-200 p-8 mb-8">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all ${
              isDragging 
                ? 'border-black bg-gray-50' 
                : selectedFile 
                  ? 'border-green-500 bg-green-50' 
                  : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />

            {!selectedFile ? (
              <>
                {/* Upload Icon */}
                <div className="mb-4">
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto">
                    <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                </div>

                {/* Text */}
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Drop your resume here
                </h3>
                <p className="text-gray-600 mb-6">
                  or click to browse your files. Supports PDF files up to 10MB.
                </p>

                {/* Browse Button */}
                <button
                  onClick={handleBrowseClick}
                  className="bg-black text-white px-6 py-3 rounded-lg hover:bg-gray-800 transition-colors font-medium"
                >
                  Browse Files
                </button>
              </>
            ) : (
              <>
                {/* File Selected View */}
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div className="text-left">
                    <p className="font-semibold text-gray-900">{selectedFile.name}</p>
                    <p className="text-sm text-gray-600">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                
                {/* Change/Remove Buttons */}
                <div className="flex justify-center space-x-3">
                  <button
                    onClick={handleBrowseClick}
                    className="bg-white border-2 border-gray-300 text-gray-900 px-5 py-2 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                  >
                    Change File
                  </button>
                  <button
                    onClick={handleRemoveFile}
                    className="bg-white border-2 border-red-300 text-red-600 px-5 py-2 rounded-lg hover:bg-red-50 transition-colors font-medium"
                  >
                    Remove
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Job Description Section */}
        <div className="bg-white rounded-2xl shadow-sm border-2 border-gray-200 p-8 mb-8">
          <div className="flex items-start space-x-3 mb-4">
            <div className="w-10 h-10 bg-gray-200 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
              <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-1">
                Job Description (Optional)
              </h3>
              <p className="text-gray-600 text-sm">
                Paste the job posting to get tailored keyword matching
              </p>
            </div>
          </div>

          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the complete job description here to get more accurate ATS matching and keyword recommendations...

Example: We are looking for a Senior Software Engineer with 5+ years of experience in React, TypeScript, and Node.js..."
            className="w-full h-48 p-4 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-black transition-colors resize-none text-gray-700 placeholder:text-gray-400"
          />
        </div>

        {/* Submit Button */}
        <div className="text-center">
          <button
            onClick={handleSubmit}
            disabled={!selectedFile}
            
            className={`px-8 py-4 rounded-lg font-medium text-lg transition-all inline-flex items-center space-x-2 ${
              selectedFile
                ? 'bg-black text-white hover:bg-gray-800 cursor-pointer'
                : 'bg-gray-400 text-white cursor-not-allowed'
            }`}
          >
            <span>Upload Resume to Continue</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
          {!selectedFile && (
            <p className="text-sm text-gray-500 mt-3">
              Please upload your resume to continue
            </p>
          )}
        </div>
      </main>
    </div>
  );
};

export default UploadResumePage;
