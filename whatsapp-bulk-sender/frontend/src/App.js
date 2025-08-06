import React, { useState, useEffect } from 'react';
import { Upload, Send, Settings, BarChart3, CheckCircle, Clock, XCircle, AlertCircle, MessageSquare, Shield } from 'lucide-react';
import RepliesTab from './RepliesTab';
import ComplianceTab from './ComplianceTab';
import Footer from './Footer';
import './App.css';

const WhatsAppBulkSender = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [file, setFile] = useState(null);
  const [messageTemplate, setMessageTemplate] = useState('');
  const [campaignName, setCampaignName] = useState('');
  const [rateLimit, setRateLimit] = useState(2); // seconds between messages
  const [campaigns, setCampaigns] = useState([]);
  const [campaignSearchQuery, setCampaignSearchQuery] = useState('');
  const [campaignCurrentPage, setCampaignCurrentPage] = useState(1);
  const [apiKey, setApiKey] = useState('');

  // Paginate campaigns based on search query
  const paginatedCampaigns = React.useMemo(() => {
    let filtered = campaigns;
    
    if (campaignSearchQuery.trim()) {
      filtered = campaigns.filter(campaign =>
        campaign.name.toLowerCase().includes(campaignSearchQuery.toLowerCase())
      );
    }
    
    const startIndex = (campaignCurrentPage - 1) * 20;
    const endIndex = startIndex + 20;
    return filtered.slice(startIndex, endIndex);
  }, [campaigns, campaignSearchQuery, campaignCurrentPage]);

  const campaignTotalPages = React.useMemo(() => {
    let filtered = campaigns;
    
    if (campaignSearchQuery.trim()) {
      filtered = campaigns.filter(campaign =>
        campaign.name.toLowerCase().includes(campaignSearchQuery.toLowerCase())
      );
    }
    
    return Math.ceil(filtered.length / 20);
  }, [campaigns, campaignSearchQuery]);

  // Reset campaign page when search changes
  React.useEffect(() => {
    setCampaignCurrentPage(1);
  }, [campaignSearchQuery]);

  const handleFileUpload = (event) => {
    const uploadedFile = event.target.files[0];
    if (uploadedFile && (uploadedFile.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || uploadedFile.name.endsWith('.xlsx'))) {
      setFile(uploadedFile);
    } else {
      alert('Please upload an Excel (.xlsx) file');
    }
  };

  const startCampaign = async () => {
    if (!file || !messageTemplate || !campaignName || !apiKey) {
      alert('Please fill all required fields');
      return;
    }

    // Automatically add compliance footer to every message
    const complianceFooter = "\n\nReply STOP to opt out | Mwihaki Intimates";
    let finalMessageTemplate = messageTemplate;
    
    // Check if the compliance footer is already present
    if (!messageTemplate.toLowerCase().includes('reply stop to opt out')) {
      finalMessageTemplate = messageTemplate + complianceFooter;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('message_template', finalMessageTemplate);
    formData.append('campaign_name', campaignName);
    formData.append('rate_limit', rateLimit);
    formData.append('api_key', apiKey);

    try {
      const response = await fetch('/api/start-campaign', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Campaign started! Campaign ID: ${result.campaign_id}`);
        setActiveTab('monitor');
        // Reset form
        setFile(null);
        setMessageTemplate('');
        setCampaignName('');
        // Fetch updated campaigns
        fetchCampaigns();
      } else {
        const error = await response.json();
        alert('Failed to start campaign: ' + (error.error || 'Unknown error'));
      }
    } catch (error) {
      alert('Error starting campaign: ' + error.message);
    }
  };

  const fetchCampaigns = async () => {
    try {
      const response = await fetch('/api/campaigns');
      if (response.ok) {
        const data = await response.json();
        setCampaigns(data.campaigns || []);
      }
    } catch (error) {
      console.error('Error fetching campaigns:', error);
    }
  };

  // Fetch campaigns on component mount and when switching to monitor tab
  useEffect(() => {
    if (activeTab === 'monitor') {
      fetchCampaigns();
      // Set up polling for real-time updates
      const interval = setInterval(fetchCampaigns, 5000);
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  const TabButton = ({ id, label, icon: Icon }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all ${
        activeTab === id
          ? 'bg-green-600 text-white shadow-lg'
          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
      }`}
    >
      <Icon size={20} />
      <span>{label}</span>
    </button>
  );

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className={`bg-white p-6 rounded-xl shadow-md border-l-4 ${color}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <Icon size={32} className="text-gray-400" />
      </div>
    </div>
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const calculateProgress = (campaign) => {
    const total = campaign.total_messages || campaign.total_contacts || 0;
    const sent = campaign.sent_messages || 0;
    return total > 0 ? Math.round((sent / total) * 100) : 0;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">WhatsApp Bulk Sender</h1>
          <p className="text-gray-600">Send personalized WhatsApp messages to thousands of contacts</p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-4 mb-8">
          <TabButton id="upload" label="Upload & Configure" icon={Upload} />
          <TabButton id="monitor" label="Monitor Campaigns" icon={BarChart3} />
          <TabButton id="replies" label="View Replies" icon={MessageSquare} />
          <TabButton id="compliance" label="Compliance Center" icon={Shield} />
          <TabButton id="settings" label="Settings" icon={Settings} />
        </div>

        {/* Upload & Configure Tab */}
        {activeTab === 'upload' && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">Create New Campaign</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Campaign Name *
                  </label>
                  <input
                    type="text"
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="e.g., Holiday Sale 2024"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    WhatsApp Business API Key *
                  </label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Your WhatsApp Business API key"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload Excel File *
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-green-500 transition-colors">
                    <input
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <Upload size={48} className="mx-auto text-gray-400 mb-4" />
                      <p className="text-gray-600">
                        {file ? file.name : 'Click to upload Excel file'}
                      </p>
                      <p className="text-sm text-gray-400 mt-2">
                        Should contain: phone, name, and any custom fields
                      </p>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rate Limit (seconds between messages)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={rateLimit}
                    onChange={(e) => setRateLimit(parseInt(e.target.value))}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Start with 2 seconds to avoid being blocked
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Message Template *
                </label>
                <textarea
                  value={messageTemplate}
                  onChange={(e) => setMessageTemplate(e.target.value)}
                  rows={12}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Hi {name}! 👋

Welcome to Mwihaki Intimates - your trusted partner for elegant, comfortable intimate wear designed with you in mind.

🌟 Exclusive offers for new customers
📍 Visit our store for personalized fitting
📞 Expert advice from our team

We respect your privacy and will only send valuable updates.

Reply STOP to opt out | Mwihaki Intimates"
                />
                <p className="text-sm text-gray-500 mt-2">
                  ✅ AUTOMATIC COMPLIANCE: "Reply STOP to opt out | Mwihaki Intimates" will be automatically added to the end of your message if not already present.
                  <br />
                  Use {'{name}'}, {'{last_product}'}, etc. for personalization
                </p>
              </div>
            </div>

            <div className="mt-8 flex justify-end">
              <button
                onClick={startCampaign}
                className="bg-green-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center space-x-2"
              >
                <Send size={20} />
                <span>Start Campaign</span>
              </button>
            </div>
          </div>
        )}

        {/* Monitor Tab */}
        {activeTab === 'monitor' && (
          <div className="space-y-8">
            {/* Campaign List */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold mb-6">Recent Campaigns</h2>
              
              {/* Search Bar for Campaigns */}
              <div className="mb-6">
                <input
                  type="text"
                  placeholder="Search campaigns by name..."
                  value={campaignSearchQuery}
                  onChange={(e) => setCampaignSearchQuery(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              
              {paginatedCampaigns.length === 0 ? (
                campaignSearchQuery.trim() ? (
                  <p className="text-gray-500 text-center py-8">No campaigns match your search.</p>
                ) : (
                  <p className="text-gray-500 text-center py-8">No campaigns found. Create your first campaign!</p>
                )
              ) : (
                <div className="space-y-4">
                  {paginatedCampaigns.map((campaign) => (
                    <div key={campaign.id} className="border border-gray-200 rounded-lg p-6">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold">{campaign.name}</h3>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(campaign.status)}`}>
                          {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div className="text-center">
                          <p className="text-2xl font-bold text-blue-600">{campaign.total_messages || campaign.total_contacts}</p>
                          <p className="text-sm text-gray-600">Total</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-yellow-600">{campaign.sent_messages || 0}</p>
                          <p className="text-sm text-gray-600">Sent</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-green-600">{campaign.delivered_messages || 0}</p>
                          <p className="text-sm text-gray-600">Delivered</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-red-600">{campaign.failed_messages || 0}</p>
                          <p className="text-sm text-gray-600">Failed</p>
                        </div>
                      </div>
                      <div className="mb-4">
                        <div className="flex justify-between text-sm text-gray-600 mb-2">
                          <span>{campaign.sent_messages || 0}/{campaign.total_messages || campaign.total_contacts} messages sent</span>
                          <span>{calculateProgress(campaign)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${calculateProgress(campaign)}%` }}
                          ></div>
                        </div>
                      </div>
                      <p className="text-sm text-gray-500">
                        Created: {new Date(campaign.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Campaign Pagination */}
              {campaignTotalPages > 1 && (
                <div className="mt-6 px-4 py-3 border-t border-gray-200 flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Page {campaignCurrentPage} of {campaignTotalPages}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setCampaignCurrentPage(Math.max(1, campaignCurrentPage - 1))}
                      disabled={campaignCurrentPage === 1}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCampaignCurrentPage(Math.min(campaignTotalPages, campaignCurrentPage + 1))}
                      disabled={campaignCurrentPage === campaignTotalPages}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Replies Tab */}
        {activeTab === 'replies' && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">WhatsApp Replies & Analytics</h2>
            <RepliesTab />
          </div>
        )}

        {/* Compliance Tab */}
        {activeTab === 'compliance' && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">WhatsApp Business Compliance</h2>
            <ComplianceTab />
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">Settings</h2>
            <div className="space-y-6">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="text-yellow-600" size={20} />
                  <h3 className="font-medium text-yellow-800">WhatsApp Compliance</h3>
                </div>
                <ul className="mt-2 text-sm text-yellow-700 space-y-1">
                  <li>• Always include opt-out instructions (Reply STOP)</li>
                  <li>• Only message customers who have opted in</li>
                  <li>• Respect rate limits to avoid being blocked</li>
                  <li>• Monitor delivery rates and adjust accordingly</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-4">Default Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Default Rate Limit (seconds)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      defaultValue="2"
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Retry Failed Messages
                    </label>
                    <select className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                      <option>Yes, with exponential backoff</option>
                      <option>Yes, fixed interval</option>
                      <option>No</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-800 mb-2">WhatsApp Business API Setup</h3>
                <ol className="text-sm text-blue-700 space-y-1">
                  <li>1. Go to business.facebook.com and verify your business</li>
                  <li>2. Apply for WhatsApp Business API access</li>
                  <li>3. Get your Phone Number ID and Access Token</li>
                  <li>4. Replace YOUR_PHONE_NUMBER_ID in the backend code</li>
                  <li>5. Use the Access Token as your API key in campaigns</li>
                </ol>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Footer */}
      <Footer />
    </div>
  );
};

export default WhatsAppBulkSender;
