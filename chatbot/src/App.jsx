import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiX, FiSend, FiChevronRight, FiClock, FiMessageSquare, FiUpload, FiFile } from 'react-icons/fi';
import { BsGraphUp, BsClipboardCheck, BsBuilding, BsRobot } from 'react-icons/bs';
import { RiLightbulbFlashLine } from 'react-icons/ri';
import { AppSettings } from './config';
export default function App() {
  const [activeBot, setActiveBot] = useState(null);
  const [messages, setMessages] = useState({
    corporate: [],
    compliance: [],
    performance: []
  });
  const [inputValues, setInputValues] = useState({
    corporate: '',
    compliance: '',
    performance: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfPreview, setPdfPreview] = useState(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const bots = [
    {
      id: 'corporate',
      title: 'StockSage Bot',
      icon: <BsBuilding className="text-blue-400" size={20} />,
      color: 'from-blue-900 to-blue-950',
      bgColor: 'bg-gradient-to-br from-blue-900/30 to-blue-950/30',
      description: 'Unlock stock performance and corporate actions!'
    },
    {
      id: 'compliance',
      title: 'Compliance Regulations Bot',
      icon: <BsClipboardCheck className="text-indigo-400" size={20} />,
      color: 'from-indigo-900 to-indigo-950',
      bgColor: 'bg-gradient-to-br from-indigo-900/30 to-indigo-950/30',
      description: 'Navigate complex regulatory requirements'
    },
    {
      id: 'performance',
      title: 'GenAI MarketView',
      icon: <BsGraphUp className="text-purple-400" size={20} />,
      color: 'from-purple-900 to-purple-950',
      bgColor: 'bg-gradient-to-br from-purple-900/30 to-purple-950/30',
      description: 'Dive into performance, valuation, and news.'
    }
  ];

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeBot]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPdfFile(file);
      // Create preview URL
      setPdfPreview(URL.createObjectURL(file));
    }
  };

  const removeFile = () => {
    setPdfFile(null);
    setPdfPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSendMessage = async (botId) => {
    const messageText = inputValues[botId].trim();
    if (!messageText && !pdfFile) return;

    // Add user message to UI immediately
    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
      file: pdfFile ? { name: pdfFile.name, preview: pdfPreview } : null
    };

    setMessages(prev => ({
      ...prev,
      [botId]: [...prev[botId], userMessage]
    }));

    setInputValues(prev => ({
      ...prev,
      [botId]: ''
    }));

    setIsLoading(true);

    try {
      // Prepare form data to send to Streamlit backend
      const formData = new FormData();
      formData.append('question', messageText);
      formData.append('bot_type', botId);
      if (pdfFile) {
        formData.append('pdf_file', pdfFile);
      }

      // Send to Streamlit backend
      const response = await fetch('http://localhost:8501/chat-with-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();

      // Add bot response to UI
      const botMessage = {
        id: Date.now() + 1,
        text: data.response,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => ({
        ...prev,
        [botId]: [...prev[botId], botMessage]
      }));
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Show error message
      const errorMessage = {
        id: Date.now() + 1,
        text: "Sorry, I'm having trouble connecting to the service. Please try again later.",
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => ({
        ...prev,
        [botId]: [...prev[botId], errorMessage]
      }));
    } finally {
      setIsLoading(false);
      // Clear file after successful send
      removeFile();
    }
  };

  // Empty State Component with PDF Upload Option
  const EmptyState = () => (
    <motion.section
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="mb-12 p-8 rounded-2xl bg-gray-800/30 border border-dashed border-gray-700/50 text-center"
    >
      <div className="max-w-md mx-auto">
        <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-blue-900/20 flex items-center justify-center border border-blue-700/30">
          <RiLightbulbFlashLine className="text-blue-400" size={40} />
        </div>
        <h3 className="text-xl font-medium text-gray-100 mb-4">Start a Conversation</h3>
        <p className="text-gray-400 mb-6">
          Select a specialist bot to begin your analysis or upload a PDF document.
        </p>
        
        {/* PDF Upload Section */}
        <div className="mb-6">
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-700/50 border-dashed rounded-lg cursor-pointer bg-gray-800/50 hover:bg-gray-700/50 transition-colors">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <FiUpload className="text-gray-400 mb-2" size={24} />
              <p className="text-sm text-gray-400">Upload PDF (optional)</p>
              <p className="text-xs text-gray-500 mt-1">Max 10MB</p>
            </div>
            <input 
              ref={fileInputRef}
              type="file" 
              className="hidden" 
              accept=".pdf" 
              onChange={handleFileChange}
            />
          </label>
          {pdfPreview && (
            <div className="mt-2 flex items-center justify-between bg-gray-800/50 rounded-lg p-2">
              <div className="flex items-center">
                <FiFile className="text-blue-400 mr-2" />
                <span className="text-sm text-blue-400 truncate max-w-xs">{pdfFile.name}</span>
              </div>
              <button 
                onClick={removeFile}
                className="text-gray-400 hover:text-gray-200"
              >
                <FiX size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </motion.section>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-950 text-gray-100 p-4 md:p-8">
      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-10">
          <div className="flex items-center justify-between">
            <div>
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="flex items-center"
              >
                <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
                  Insight Nexus
                </h1>
              </motion.div>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="text-sm text-gray-400 mt-1"
              >
                S&P Global • DTCC AI Hackathon
              </motion.p>
            </div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="hidden md:flex items-center px-4 py-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium border border-blue-500/30"
            >
              <RiLightbulbFlashLine className="mr-2" />
              AI Financial Assistants
            </motion.div>
          </div>
        </header>

        {/* Main Content */}
        <main>
          {/* Welcome Section */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mb-12 p-6 rounded-2xl bg-gray-800/50 shadow-lg border border-gray-700/50 backdrop-blur-sm"
          >
            <div className="flex flex-col md:flex-row items-center">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-100 mb-2">
                  <span className="inline-block mr-2">👋</span> Welcome to your DTCC AI Hub!
                </h2>
                <p className="text-gray-400 mb-4">
                  Our specialized assistants are ready to help with corporate actions, compliance, and performance analysis.
                  Start by choosing a specialist below or upload a document for analysis.
                </p>
                <div className="flex flex-wrap gap-2">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-3 py-1.5 text-xs rounded-full bg-gradient-to-r from-indigo-800/50 to-purple-800/50 text-indigo-100 border border-indigo-700/50"
                  >
                    Show me recent dividend announcements
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-3 py-1.5 text-xs rounded-full bg-gradient-to-r from-indigo-800/50 to-purple-800/50 text-indigo-100 border border-indigo-700/50"
                  >
                    What's new in SEC reporting requirements?
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-3 py-1.5 text-xs rounded-full bg-gradient-to-r from-indigo-800/50 to-purple-800/50 text-indigo-100 border border-indigo-700/50"
                  >
                    How might this merger affect stock prices?
                  </motion.button>
                </div>
              </div>
              <div className="mt-6 md:mt-0 md:ml-6">
                <div className="relative">
                  <div className="w-48 h-48 rounded-2xl bg-gradient-to-br from-amber-900/30 to-orange-900/30 flex items-center justify-center border border-amber-800/30">
                    <BsRobot className="text-amber-400/80" size={80} />
                  </div>
                  <div className="absolute -top-4 -right-4 bg-gray-800 p-2 rounded-full shadow-md border border-amber-600/30" style={{ transform: 'rotate(-5.39149deg)' }}>
                    <RiLightbulbFlashLine className="text-amber-400" size={24} />
                  </div>
                </div>
              </div>
            </div>
          </motion.section>

          {/* Bot Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {bots.map((bot) => (
              <motion.div
                key={bot.id}
                whileHover={{ y: -5, scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`${bot.bgColor} rounded-2xl shadow-lg overflow-hidden cursor-pointer border border-gray-700/30 backdrop-blur-sm`}
                onClick={() => {
                  if (bot.id === 'compliance') {
                    window.open( `${AppSettings.COMPLIANCE_REGULATIONS_BOT}`,'_blank');
                  } 
                  else if(bot.id==='performance'){
                    window.open( `${AppSettings.INSTRUMENT_SUMMARY_BOT}`,'_blank');
                  }
                  else if(bot.id==='corporate'){
                    window.open( `${AppSettings.CORPORATE_ACTIONS_BOT}`,'_blank');
                  }
                  else {
                    setActiveBot(bot.id);
                  }
                }}                
              >
                <div className={`h-2 bg-gradient-to-r ${bot.color}`}></div>
                <div className="p-6">
                  <div className="flex items-center mb-4">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center bg-gradient-to-r ${bot.color} mr-4`}>
                      {bot.icon}
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-gray-100">
                        {bot.title}
                      </h2>
                      <p className="text-sm text-gray-400">
                        {bot.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex justify-between items-center text-sm text-gray-500">
                    <span className="inline-flex items-center">
                      <FiClock className="mr-1" /> Ready to assist
                    </span>
                    <div className="flex items-center text-blue-400 font-medium">
                      Chat now <FiChevronRight className="ml-1" />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}