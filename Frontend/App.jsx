import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from './HomePage';
import UploadResumePage from './UploadResumePage';
import LoadingScreen from './LoadingScreen';


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path = '/' element= {<HomePage />} />
        <Route path = '/uploadyourresume' element = {<UploadResumePage />} />
        <Route path = '/loading' element = {<LoadingScreen />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
