import { useState, useEffect } from 'react';
import { Loader, Upload, BookOpen, PlusCircle, ChevronRight, Check, X, Eye, EyeOff, Trash2, Download, Search, ArrowLeft } from 'lucide-react';

export default function LectureQuestionBank() {
  const API_BASE_URL =  'http://127.0.0.1:5000';
  const userId = '12'; // Temporary hardcoded user ID

  // State management
  
  const [units, setUnits] = useState([]);
  const [newUnitTitle, setNewUnitTitle] = useState('');
  const [currentUnit, setCurrentUnit] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [topic, setTopic] = useState('');
  const [questionType, setQuestionType] = useState('multiple-choice');
  const [generatedQuestions, setGeneratedQuestions] = useState(null);
  const [previousSets, setPreviousSets] = useState([]);
  const [showAnswers, setShowAnswers] = useState({});
  const [userAnswers, setUserAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Load units from backend on mount (simulated)
  useEffect(() => {
    const fetchUnits = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/units?user_id=${userId}`);
        const data = await response.json();
        setUnits(data);
      } catch (error) {
        console.error("Error fetching units:", error);
      }
    };
    
    fetchUnits();
  }, [userId]);

  // Handler functions
  const handleCreateUnit = async () => {
    if (newUnitTitle.trim()) {
      try {
        const response = await fetch('${API_BASE_URL}/units', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            title: newUnitTitle.trim()
          })
        });
        
        const newUnit = await response.json();
        setUnits([...units, newUnit]);
        setNewUnitTitle('');
      } catch (error) {
        console.error("Error creating unit:", error);
      }
    }
  };

  const handleSelectUnit = (unit) => {
    setCurrentUnit(unit);
    setGeneratedQuestions(null);
  };

  const handleUploadPDF = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setUploading(true);
    setUploadProgress(0);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    formData.append('unit_id', currentUnit.id);
    
    try {
      // You'll need to implement progress tracking
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      });
      
      xhr.addEventListener('load', () => {
        setUploading(false);
        // Show success notification
      });
      
      xhr.open('POST', '/upload');
      xhr.send(formData);
    } catch (error) {
      setUploading(false);
      console.error("Error uploading PDF:", error);
    }
  };

  const handleGenerateQuestions = async () => {
    if (!topic.trim()) return;
    
    setIsLoading(true);
    
    try {
      const response = await fetch('${API_BASE_URL}/generate_questions_by_topic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic,
          style: questionType,
          user_id: userId,
          unit_id: currentUnit.id
        })
      });
      
      const data = await response.json();
      setGeneratedQuestions(data);
      loadPreviousQuestionSets(); // Refresh the list
      setIsLoading(false);
      setTopic('');
    } catch (error) {
      setIsLoading(false);
      console.error("Error generating questions:", error);
    }
  };

  const loadPreviousQuestionSets = async () => {
    if (!currentUnit) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/question_sets?user_id=${userId}&unit_id=${currentUnit.id}`);
      const data = await response.json();
      setPreviousSets(data);
    } catch (error) {
      console.error("Error fetching question sets:", error);
    }
  };
  
  // Use this in useEffect
  useEffect(() => {
    if (currentUnit) {
      loadPreviousQuestionSets();
    }
  }, [currentUnit]);


  const toggleAnswer = (questionId) => {
    setShowAnswers({
      ...showAnswers,
      [questionId]: !showAnswers[questionId]
    });
  };

  const handleAnswerSelect = (questionId, answer) => {
    setUserAnswers({
      ...userAnswers,
      [questionId]: answer
    });
  };

  const handleDeleteSet = (setId) => {
    setPreviousSets(previousSets.filter(set => set.id !== setId));
    if (generatedQuestions && generatedQuestions.id === setId) {
      setGeneratedQuestions(null);
    }
  };

  const handleSearch = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/search_questions_by_topic?user_id=${userId}&unit_id=${currentUnit.id}&topic=${searchTerm}`);
      const data = await response.json();
      setPreviousSets(data);
    } catch (error) {
      console.error("Error searching question sets:", error);
    }
  };

  const handleExportSet = (set) => {
    alert(`Exporting ${set.topic} question set (would download in a real app)`);
  };

  const filteredSets = previousSets.filter(set => 
    set.topic.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const goBackToUnits = () => {
    setCurrentUnit(null);
    setGeneratedQuestions(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-indigo-600 text-white p-4 shadow-md">
        <div className="container mx-auto flex items-center">
          <BookOpen className="mr-2" />
          <h1 className="text-xl font-bold">Lecture Question Bank</h1>
        </div>
      </header>

      <main className="container mx-auto p-4">
        {!currentUnit ? (
          // HOMEPAGE (DASHBOARD)
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Your Units</h2>
            
            {/* Create new unit form */}
            <div className="bg-white p-4 rounded-lg shadow-md">
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={newUnitTitle}
                  onChange={(e) => setNewUnitTitle(e.target.value)}
                  placeholder="Enter unit title..."
                  className="flex-1 p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={handleCreateUnit}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 flex items-center"
                >
                  <PlusCircle className="mr-1 h-5 w-5" />
                  Create Unit
                </button>
              </div>
            </div>
            
            {/* Units list */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <ul className="divide-y divide-gray-200">
                {units.length === 0 ? (
                  <li className="p-4 text-gray-500 text-center">No units created yet</li>
                ) : (
                  units.map(unit => (
                    <li key={unit.id} className="p-0 hover:bg-gray-50">
                      <button
                        onClick={() => handleSelectUnit(unit)}
                        className="w-full p-4 text-left flex items-center justify-between"
                      >
                        <span className="font-medium text-gray-800">{unit.title}</span>
                        <ChevronRight className="h-5 w-5 text-gray-400" />
                      </button>
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
        ) : (
          // UNIT MENU PAGE
          <div className="space-y-6">
            <div className="flex items-center">
              <button
                onClick={goBackToUnits}
                className="mr-4 flex items-center text-indigo-600 hover:text-indigo-800"
              >
                <ArrowLeft className="h-5 w-5 mr-1" />
                Back to Units
              </button>
              <h2 className="text-2xl font-bold text-gray-800">{currentUnit.title}</h2>
            </div>
            
            {/* PDF Upload */}
            <section className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold mb-4">Upload Lecture Notes</h3>
              {uploading ? (
                <div className="space-y-2">
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 rounded-full"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-600">Uploading... {uploadProgress}%</p>
                </div>
              ) : (
                <button
                  onClick={handleUploadPDF}
                  className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  <Upload className="mr-2 h-5 w-5" />
                  Upload PDF
                </button>
              )}
            </section>
            
            {/* Question Generation Form */}
            <section className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold mb-4">Generate Questions</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Topic or keyword
                  </label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., Photosynthesis"
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Question Type
                  </label>
                  <select
                    value={questionType}
                    onChange={(e) => setQuestionType(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="multiple-choice">Multiple Choice</option>
                    <option value="true-false">True or False</option>
                    <option value="open-ended">Open-Ended</option>
                  </select>
                </div>
                
                <button
                  onClick={handleGenerateQuestions}
                  disabled={isLoading || !topic.trim()}
                  className={`w-full p-2 rounded-md flex items-center justify-center ${
                    isLoading || !topic.trim() ? 'bg-gray-300 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'
                  } text-white`}
                >
                  {isLoading ? (
                    <>
                      <Loader className="mr-2 h-5 w-5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    'Generate Questions'
                  )}
                </button>
              </div>
            </section>
            
            {/* Generated Questions Display */}
            {generatedQuestions && (
              <section className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">{generatedQuestions.topic} Questions</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleExportSet(generatedQuestions)}
                      className="p-2 text-gray-600 hover:text-indigo-600"
                      title="Export"
                    >
                      <Download className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteSet(generatedQuestions.id)}
                      className="p-2 text-gray-600 hover:text-red-600"
                      title="Delete"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
                
                <ul className="space-y-4">
                  {generatedQuestions.questions.map((q) => (
                    <li key={q.id} className="border border-gray-200 rounded-md p-4">
                      <p className="font-medium mb-2">{q.question}</p>
                      
                      {generatedQuestions.type === 'multiple-choice' && (
                        <div className="space-y-2 pl-4">
                          {q.options.map((option) => (
                            <button
                              key={option}
                              onClick={() => handleAnswerSelect(q.id, option)}
                              className={`w-full text-left p-2 rounded-md flex items-center ${
                                userAnswers[q.id] === option
                                  ? option === q.correctAnswer
                                    ? 'bg-green-100 border-green-300'
                                    : 'bg-red-100 border-red-300'
                                  : 'bg-gray-50 hover:bg-gray-100 border-gray-200'
                              } border`}
                            >
                              {userAnswers[q.id] === option ? (
                                option === q.correctAnswer ? (
                                  <Check className="h-5 w-5 text-green-600 mr-2" />
                                ) : (
                                  <X className="h-5 w-5 text-red-600 mr-2" />
                                )
                              ) : (
                                <div className="h-5 w-5 mr-2" />
                              )}
                              {option}
                              {userAnswers[q.id] && option === q.correctAnswer && userAnswers[q.id] !== option && (
                                <span className="ml-2 text-green-600 text-sm">(Correct answer)</span>
                              )}
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {generatedQuestions.type === 'true-false' && (
                        <div className="space-y-2 pl-4">
                          {[true, false].map((option) => (
                            <button
                              key={option.toString()}
                              onClick={() => handleAnswerSelect(q.id, option)}
                              className={`w-full text-left p-2 rounded-md flex items-center ${
                                userAnswers[q.id] === option
                                  ? option === q.correctAnswer
                                    ? 'bg-green-100 border-green-300'
                                    : 'bg-red-100 border-red-300'
                                  : 'bg-gray-50 hover:bg-gray-100 border-gray-200'
                              } border`}
                            >
                              {userAnswers[q.id] === option ? (
                                option === q.correctAnswer ? (
                                  <Check className="h-5 w-5 text-green-600 mr-2" />
                                ) : (
                                  <X className="h-5 w-5 text-red-600 mr-2" />
                                )
                              ) : (
                                <div className="h-5 w-5 mr-2" />
                              )}
                              {option ? 'True' : 'False'}
                              {userAnswers[q.id] !== undefined && option === q.correctAnswer && userAnswers[q.id] !== option && (
                                <span className="ml-2 text-green-600 text-sm">(Correct answer)</span>
                              )}
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {generatedQuestions.type === 'open-ended' && (
                        <div className="mt-2">
                          <button
                            onClick={() => toggleAnswer(q.id)}
                            className="flex items-center text-indigo-600 hover:text-indigo-800"
                          >
                            {showAnswers[q.id] ? (
                              <>
                                <EyeOff className="h-4 w-4 mr-1" />
                                Hide Answer
                              </>
                            ) : (
                              <>
                                <Eye className="h-4 w-4 mr-1" />
                                Show Answer
                              </>
                            )}
                          </button>
                          
                          {showAnswers[q.id] && (
                            <div className="mt-2 p-3 bg-gray-50 rounded-md">
                              <p className="text-gray-700">{q.answer}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            )}
            
            {/* Previous Question Sets */}
            <section className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold mb-4">Previous Question Sets</h3>
              
              <div className="mb-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search by topic..."
                    className="pl-10 w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
              
              {filteredSets.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No question sets yet</p>
              ) : (
                <ul className="divide-y divide-gray-200">
                  {filteredSets.map((set) => (
                    <li key={set.id} className="py-3">
                      <div className="flex justify-between items-center">
                        <div>
                          <h4 className="font-medium">{set.topic}</h4>
                          <p className="text-sm text-gray-500">
                            {set.type === 'multiple-choice' ? 'Multiple Choice' : 
                             set.type === 'true-false' ? 'True/False' : 'Open-Ended'} 
                            · {set.questions.length} questions
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => setGeneratedQuestions(set)}
                            className="p-2 text-gray-600 hover:text-indigo-600"
                            title="View"
                          >
                            <Eye className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleExportSet(set)}
                            className="p-2 text-gray-600 hover:text-indigo-600"
                            title="Export"
                          >
                            <Download className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleDeleteSet(set.id)}
                            className="p-2 text-gray-600 hover:text-red-600"
                            title="Delete"
                          >
                            <Trash2 className="h-5 w-5" />
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}