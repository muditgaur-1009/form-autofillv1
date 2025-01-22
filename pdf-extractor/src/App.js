// src/App.js
import React from 'react';
import PDFExtractor from './components/PDFExtractor';
import './App.css';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">
          PDF Data Extractor
        </h1>
        <PDFExtractor />
      </div>
    </div>
  );
}

export default App;