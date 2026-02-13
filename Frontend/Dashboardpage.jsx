import React from 'react';
import { FileText, Download, Share2, Calendar, CheckCircle, AlertTriangle, Wand2 } from 'lucide-react';

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="bg-blue-600 rounded p-1">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-gray-900">ResumeAnalyzer Pro</span>
            </div>
            
            <div className="flex items-center gap-6">
              <a href="#" className="text-gray-700 hover:text-gray-900 font-medium">Dashboard</a>
              <a href="#" className="text-gray-700 hover:text-gray-900 font-medium">My Resumes</a>
              <a href="#" className="text-gray-700 hover:text-gray-900 font-medium">Job Matches</a>
              <button className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors">
                Improve My Resume
              </button>
              <div className="w-9 h-9 bg-yellow-100 rounded-full"></div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">ATS Score Result Dashboard</h1>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-gray-600">
              <Calendar className="w-4 h-4" />
              <span>Analyzed on October 24, 2023 for '<span className="text-blue-600 font-medium">Senior Product Designer</span>' role</span>
            </div>
            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Download className="w-4 h-4" />
                <span className="font-medium">Export PDF</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Share2 className="w-4 h-4" />
                <span className="font-medium">Share</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar */}
          <div className="col-span-3 space-y-6">
            {/* Match Probability Card */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <h3 className="text-lg font-bold text-gray-900 mb-6">Match Probability</h3>
              
              {/* Circular Progress */}
              <div className="relative w-40 h-40 mx-auto mb-4">
                <svg className="w-40 h-40 transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#E5E7EB"
                    strokeWidth="12"
                    fill="none"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#2563EB"
                    strokeWidth="12"
                    fill="none"
                    strokeDasharray={`${(85 / 100) * 439.6} 439.6`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-5xl font-bold text-gray-900">85</div>
                  <div className="text-sm text-gray-500">Out of 100</div>
                </div>
              </div>

              <div className="text-center mb-4">
                <span className="inline-block bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-semibold">
                  GOOD MATCH
                </span>
              </div>
              
              <p className="text-sm text-gray-600 text-center">
                You're in the top 15% of candidates for this role.
              </p>
            </div>

            {/* Keywords Found */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-bold text-gray-900">KEYWORDS FOUND</h3>
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-1">12/18</div>
              <p className="text-sm text-green-600">+5% above average</p>
            </div>

            {/* Format Errors */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-bold text-gray-900">FORMAT ERRORS</h3>
                <AlertTriangle className="w-5 h-5 text-red-500" />
              </div>
              <div className="text-3xl font-bold text-gray-900 mb-1">2</div>
              <p className="text-sm text-gray-600">-1 fixed since last scan</p>
            </div>
          </div>

          {/* Center Content */}
          <div className="col-span-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              {/* Tabs */}
              <div className="border-b border-gray-200">
                <div className="flex gap-8 px-6">
                  <button className="py-4 text-blue-600 border-b-2 border-blue-600 font-semibold">
                    Resume Preview
                  </button>
                  <button className="py-4 text-gray-600 hover:text-gray-900">
                    Parsed Text
                  </button>
                  <button className="py-4 text-gray-600 hover:text-gray-900">
                    Job Comparison
                  </button>
                </div>
              </div>

              {/* Resume Content */}
              <div className="p-8">
                <div className="max-w-2xl mx-auto">
                  {/* Header */}
                  <div className="text-center mb-8">
                    <h2 className="text-3xl font-bold text-gray-900 mb-2">ALEX RIVERA</h2>
                    <p className="text-gray-600 mb-1">Senior Product Designer • San Francisco, CA</p>
                    <p className="text-sm">
                      <a href="mailto:alex.rivera@design.com" className="text-blue-600 hover:underline">alex.rivera@design.com</a>
                      <span className="mx-2">•</span>
                      <a href="tel:+15550123456" className="text-blue-600 hover:underline">+1 (555) 012-3456</a>
                    </p>
                  </div>

                  {/* Summary */}
                  <div className="mb-8">
                    <h3 className="text-lg font-bold text-gray-900 mb-3">SUMMARY</h3>
                    <p className="text-gray-700 leading-relaxed">
                      Results-oriented <span className="bg-green-100 text-green-800 px-1">Senior Product Designer</span> with over 8 years of experience building scalable design systems and user-centric applications. Proven track record in <span className="bg-green-100 text-green-800 px-1">UI/UX design</span>, cross-functional leadership, and data-driven iteration.
                    </p>
                  </div>

                  {/* Experience */}
                  <div className="mb-8">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">EXPERIENCE</h3>
                    
                    <div className="mb-6">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-bold text-gray-900">Lead Product Designer | TechFlow Inc.</h4>
                        </div>
                        <span className="text-gray-600 text-sm">2020 – Present</span>
                      </div>
                      <ul className="space-y-2 ml-5 list-disc text-gray-700">
                        <li>Orchestrated the redesign of the core dashboard, resulting in a 25% increase in <span className="bg-green-100 text-green-800 px-1">user engagement</span> metrics.</li>
                        <li>Developed a multi-platform <span className="bg-green-100 text-green-800 px-1">design system</span> adopted by 15 internal product teams.</li>
                        <li>Mentored a team of 4 junior designers, providing <span className="bg-yellow-100 text-yellow-800 px-1">strategic direction</span> and feedback.</li>
                      </ul>
                    </div>

                    <div className="mb-6">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-bold text-gray-900">UX Designer | Creative Labs</h4>
                        </div>
                        <span className="text-gray-600 text-sm">2016 – 2020</span>
                      </div>
                      <ul className="space-y-2 ml-5 list-disc text-gray-700">
                        <li>Conducted extensive <span className="bg-green-100 text-green-800 px-1">user research</span> and usability testing for mobile apps.</li>
                        <li>Collaborated with engineering to ensure high-fidelity implementation of <span className="bg-green-100 text-green-800 px-1">prototypes</span>.</li>
                      </ul>
                    </div>
                  </div>

                  {/* Skills */}
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-3">SKILLS</h3>
                    <div className="space-y-2">
                      <div>
                        <span className="font-semibold text-gray-900">Tools:</span>
                        <span className="text-gray-700"> Figma, Sketch, Adobe Creative Suite, Jira</span>
                      </div>
                      <div>
                        <span className="font-semibold text-gray-900">Technical:</span>
                        <span className="text-gray-700"> HTML/CSS, React (Basics), <span className="bg-green-100 text-green-800 px-1">Accessibility</span></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Metrics */}
            <div className="grid grid-cols-3 gap-6 mt-6">
              {/* Visual Hierarchy */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-base font-bold text-gray-900">Visual Hierarchy</h3>
                  <span className="text-blue-600 font-bold text-lg">92%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mb-3">
                  <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: '92%' }}></div>
                </div>
                <p className="text-sm text-gray-600">Your resume has excellent use of white space and headings.</p>
              </div>

              {/* Quantifiable Impact */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-base font-bold text-gray-900">Quantifiable Impact</h3>
                  <span className="text-orange-500 font-bold text-lg">64%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mb-3">
                  <div className="bg-orange-500 h-1.5 rounded-full" style={{ width: '64%' }}></div>
                </div>
                <p className="text-sm text-gray-600">Try to add more metrics (%, $, numbers) to your achievements.</p>
              </div>

              {/* Contact Formatting */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-base font-bold text-gray-900">Contact Formatting</h3>
                  <span className="text-green-600 font-bold text-lg">100%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mb-3">
                  <div className="bg-green-600 h-1.5 rounded-full" style={{ width: '100%' }}></div>
                </div>
                <p className="text-sm text-gray-600">Contact details are clear and formatted for all ATS types.</p>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="col-span-3 space-y-6">
            {/* Critical Fixes */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center gap-2 mb-4">
                <div className="bg-red-100 rounded-full p-1">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                </div>
                <h3 className="font-bold text-gray-900">CRITICAL FIXES (2)</h3>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">Missing Portfolio Link</h4>
                  <p className="text-sm text-gray-600">ATS systems look for portfolio links in the header for Designer roles.</p>
                </div>

                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">Unrecognized Font Type</h4>
                  <p className="text-sm text-gray-600">The current body font may not be parsed correctly by older systems.</p>
                </div>
              </div>
            </div>

            {/* Missing Keywords */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-gray-900">MISSING KEYWORDS</h3>
                <span className="text-blue-600 text-sm font-semibold">MATCH 12/18</span>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                <span className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full text-sm">+ Agile</span>
                <span className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full text-sm">+ Stakeholder</span>
                <span className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full text-sm">+ A/B Testing</span>
                <span className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full text-sm">+ Data Viz</span>
                <span className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full text-sm">+ SaaS</span>
              </div>

              <p className="text-sm text-gray-600 mb-1">
                <span className="italic">Adding these keywords could increase your score to </span>
                <span className="text-blue-600 font-semibold">94/100</span>
              </p>
            </div>

            {/* Automated Optimization */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 shadow-sm border border-blue-200">
              <div className="bg-white rounded-full p-3 w-12 h-12 flex items-center justify-center mx-auto mb-4">
                <Wand2 className="w-6 h-6 text-blue-600" />
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 text-center mb-2">
                Automated Optimization
              </h3>
              
              <p className="text-sm text-gray-600 text-center mb-6">
                Let our AI rewrite your experience section to naturally incorporate missing keywords.
              </p>

              <button className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                Improve Experience
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-center text-gray-600 text-sm">
            © 2023 ResumeAnalyzer Pro. All rights reserved. Helping you land your dream job faster.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;