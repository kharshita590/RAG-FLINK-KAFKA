"use client"
import React, { useState } from 'react';
import { Plus, Globe, BarChart3, ArrowUp } from 'lucide-react';

interface Message {
  user_id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export default function Page() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sleep = (ms: number) => new Promise(res => setTimeout(res, ms));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userId = Date.now().toString();

    const userMessage: Message = {
      user_id: userId,
      text: input,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const postRes = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, query_text: input }),
      });

      if (!postRes.ok) {
        throw new Error(`POST /query failed: ${postRes.status}`);
      }

      const pollInterval = 1000; 
      const maxAttempts = 30;
      let attempts = 0;
      let gotResult = false;

      while (attempts < maxAttempts && !gotResult) {
        attempts += 1;
        const res = await fetch(`http://127.0.0.1:8000/results/${encodeURIComponent(userId)}`);
        if (res.ok) {
          const json = await res.json();
          if (json.status && json.status === 'no-result') {
          } else {
            const aiText = json.ai_response;
            const aiMessage: Message = {
              user_id: (Date.now() + 1).toString(),
              text: aiText,
              isUser: false,
              timestamp: new Date(),
            };
            setMessages(prev => [...prev, aiMessage]);
            gotResult = true;
            break;
          }
        } else {
          console.warn('Polling /results returned non-OK:', res.status);
        }
        await sleep(pollInterval);
      }

      if (!gotResult) {
        setMessages(prev => [...prev, {
          user_id: (Date.now() + 1).toString(),
          text: "No response yet — the backend didn't produce a result in time.",
          isUser: false,
          timestamp: new Date(),
        }]);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        user_id: (Date.now() + 1).toString(),
        text: "Sorry, I'm having trouble connecting right now. Please try again later.",
        isUser: false,
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
      setInput('');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-orange-500 flex flex-col items-center justify-center p-4">
      <div className="text-center mb-8 max-w-4xl mx-auto">
        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-4 tracking-tight">
          <span className="inline-flex items-center">
            <span className="text-blue-400">flink</span>
            {' '}Rag
          </span>
        </h1>
        <p className="text-xl md:text-2xl text-slate-300 font-medium">Your Production Ready RAG: powered by Apache FLINK and Apache KAFKA</p>
      </div>

      {messages.length > 0 && (
        <div className="w-full max-w-4xl mx-auto mb-6 max-h-96 overflow-y-auto space-y-4 px-4">
          {messages.map((message) => (
  <div key={message.user_id} className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}>
    <div className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-3 rounded-2xl ${message.isUser ? 'bg-white/9 backdrop-blur-sm text-white ml-auto border border-white/20' : 'bg-white/10 backdrop-blur-sm text-white border border-white/20'}`}>
      
      {message.text.split('\n').map((line, index) => (
        <div key={index} className="text-sm md:text-base leading-relaxed mb-2">
          {line.startsWith('•') ? (
            <div className="flex items-start space-x-2">
              <span className="text-green-500">•</span>
              <p>{line.slice(1).trim()}</p>
            </div>
          ) : (
            <p>
              {line.split(/\s+/).map((word, idx) => (
                <span key={idx} className={word.match(/^\$\d[\d,.]*$/) ? 'font-semibold text-blue-300' : ''}>
                  {word}{' '}
                </span>
              ))}
            </p>
          )}
        </div>
      ))}

      <p className="text-xs opacity-70 mt-1 text-right">
        {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </p>
    </div>
  </div>
))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white/10 backdrop-blur-sm text-white border border-white/20 max-w-xs px-4 py-3 rounded-2xl">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="w-full max-w-4xl mx-auto px-4">
        <form onSubmit={handleSubmit} className="relative">
          <div className="bg-slate-800/80 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-4 shadow-2xl">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
              </div>

              <div className="flex-1">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask flinkRag for expert insights and the latest news on stocks"
                  className="w-full bg-transparent text-slate-200 placeholder-slate-500 text-lg focus:outline-none"
                  disabled={isLoading}
                />
              </div>

              <div className="flex items-center space-x-2">
                <button type="button" className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors duration-200">
                  <BarChart3 className="w-5 h-5 text-slate-400" />
                </button>
                <button type="submit" disabled={!input.trim() || isLoading} className="p-2 bg-slate-600 hover:bg-slate-500 disabled:bg-slate-700/50 disabled:cursor-not-allowed rounded-lg transition-all duration-200 group">
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <ArrowUp className="w-5 h-5 text-slate-200 group-hover:text-white group-disabled:text-slate-500" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>

      {messages.length === 0 && (
        <p className="text-slate-400 text-sm mt-6 text-center max-w-md">
            Enter your finance query above and press Enter or click the arrow to get insights powered by Kafka and real-time processing.

        </p>
      )}
    </div>
  );
}
