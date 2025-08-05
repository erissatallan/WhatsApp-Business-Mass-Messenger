import React, { useState, useEffect } from 'react';

const RepliesTab = () => {
  const [replies, setReplies] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedCampaign, setSelectedCampaign] = useState('');
  const [selectedSentiment, setSelectedSentiment] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [campaigns, setCampaigns] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    fetchCampaigns();
    fetchReplies();
    fetchAnalytics();
  }, [selectedCampaign, selectedSentiment, startDate, endDate, currentPage]);

  const fetchCampaigns = async () => {
    try {
      const response = await fetch('/api/campaigns');
      const data = await response.json();
      setCampaigns(data.campaigns || []);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
    }
  };

  const fetchReplies = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage,
        per_page: 20
      });
      
      if (selectedCampaign) params.append('campaign_id', selectedCampaign);
      if (selectedSentiment) params.append('sentiment', selectedSentiment);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const response = await fetch(`/api/replies?${params}`);
      const data = await response.json();
      
      setReplies(data.replies || []);
      setTotalPages(data.total_pages || 1);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching replies:', error);
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const params = selectedCampaign ? `?campaign_id=${selectedCampaign}` : '';
      const response = await fetch(`/api/replies/analytics${params}`);
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const getSentimentEmoji = (sentiment) => {
    switch (sentiment) {
      case 'interested': return '😊';
      case 'positive_feedback': return '🌟';
      case 'complaint': return '😞';
      case 'question': return '❓';
      case 'desired_opt_out': return '🚫';
      case 'urgent': return '🚨';
      case 'neutral': return '😐';
      default: return '😐';
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'interested': return 'text-green-600 bg-green-50';
      case 'positive_feedback': return 'text-emerald-600 bg-emerald-50';
      case 'complaint': return 'text-red-600 bg-red-50';
      case 'question': return 'text-blue-600 bg-blue-50';
      case 'desired_opt_out': return 'text-red-800 bg-red-100 border border-red-200';
      case 'urgent': return 'text-orange-600 bg-orange-50';
      case 'neutral': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const downloadExcel = async () => {
    try {
      setDownloading(true);
      
      // Build download parameters
      const params = new URLSearchParams();
      if (selectedCampaign) params.append('campaign_id', selectedCampaign);
      if (selectedSentiment) params.append('sentiment', selectedSentiment);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const response = await fetch(`/api/replies/download?${params}`);
      
      if (!response.ok) {
        const error = await response.json();
        alert(`Error: ${error.error}`);
        return;
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Get filename from response header or create default
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'whatsapp_replies.xlsx';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match) {
          filename = match[1].replace(/['"]/g, '');
        }
      }
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (error) {
      console.error('Error downloading Excel:', error);
      alert('Failed to download Excel file');
    } finally {
      setDownloading(false);
    }
  };

  const clearAllFilters = () => {
    setSelectedCampaign('');
    setSelectedSentiment('');
    setStartDate('');
    setEndDate('');
    setCurrentPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Analytics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-blue-600">Reply Rate</h3>
          <p className="text-2xl font-bold text-blue-900">{analytics.reply_rate || 0}%</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-green-600">Positive Replies</h3>
          <p className="text-2xl font-bold text-green-900">
            {analytics.sentiment_breakdown?.positive || 0}
          </p>
        </div>
        <div className="bg-red-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-red-600">Opt-outs</h3>
          <p className="text-2xl font-bold text-red-900">{analytics.total_opt_outs || 0}</p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-purple-600">Recent (24h)</h3>
          <p className="text-2xl font-bold text-purple-900">{analytics.recent_replies_24h || 0}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Campaign
            </label>
            <select
              value={selectedCampaign}
              onChange={(e) => {
                setSelectedCampaign(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">All Campaigns</option>
              {campaigns.map((campaign) => (
                <option key={campaign.id} value={campaign.id}>
                  {campaign.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sentiment
            </label>
            <select
              value={selectedSentiment}
              onChange={(e) => {
                setSelectedSentiment(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">All Sentiments</option>
              <option value="interested">😊 Interested</option>
              <option value="positive_feedback">🌟 Positive Feedback</option>
              <option value="question">❓ Questions</option>
              <option value="complaint">😞 Complaints</option>
              <option value="desired_opt_out">🚫 Opt-out Requests</option>
              <option value="urgent">🚨 Urgent</option>
              <option value="neutral">😐 Neutral</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={clearAllFilters}
              className="w-full px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Download Section */}
        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            {replies.length > 0 && (
              <span>
                Showing {replies.length} replies
                {(selectedCampaign || selectedSentiment || startDate || endDate) && ' (filtered)'}
              </span>
            )}
          </div>
          <button
            onClick={downloadExcel}
            disabled={downloading || replies.length === 0}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {downloading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Downloading...
              </>
            ) : (
              <>
                <svg className="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download Excel
              </>
            )}
          </button>
        </div>
      </div>

      {/* Replies List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">WhatsApp Replies</h3>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading replies...</p>
          </div>
        ) : replies.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No replies found for the selected filters.</p>
            <p className="text-sm mt-2">
              Make sure your webhook is configured and people are replying to your campaigns!
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {replies.map((reply) => (
              <div key={reply.id} className={`p-4 hover:bg-gray-50 ${reply.requires_attention ? 'border-l-4 border-orange-400 bg-orange-50' : ''}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2 flex-wrap">
                      <span className="font-medium text-gray-900">
                        {reply.sender_name || 'Unknown'}
                      </span>
                      <span className="text-sm text-gray-500">
                        {reply.phone_number}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(reply.sentiment)}`}
                      >
                        {getSentimentEmoji(reply.sentiment)} {reply.sentiment}
                      </span>
                      
                      {reply.requires_attention && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-orange-600 bg-orange-100">
                          ⚠️ Needs Attention
                        </span>
                      )}
                      
                      {reply.is_opt_out && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-red-600 bg-red-100">
                          🚫 Opt-out
                        </span>
                      )}
                      
                      {reply.confidence_score && (
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          reply.confidence_score > 0.8 ? 'text-green-600 bg-green-100' : 
                          reply.confidence_score > 0.6 ? 'text-yellow-600 bg-yellow-100' : 
                          'text-gray-600 bg-gray-100'
                        }`}>
                          🎯 {Math.round(reply.confidence_score * 100)}%
                        </span>
                      )}
                    </div>
                    
                    <p className="text-gray-700 mb-2">{reply.message_content}</p>
                    
                    {reply.media_url && (
                      <div className="mb-2">
                        {reply.media_type?.startsWith('image/') ? (
                          <img
                            src={reply.media_url}
                            alt="Reply media"
                            className="max-w-xs rounded-lg border"
                          />
                        ) : (
                          <a
                            href={reply.media_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 underline"
                          >
                            📎 View Media ({reply.media_type})
                          </a>
                        )}
                      </div>
                    )}
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>📅 {formatDateTime(reply.received_at)}</span>
                      {reply.campaign_name && (
                        <span>📢 Campaign: {reply.campaign_name}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RepliesTab;
