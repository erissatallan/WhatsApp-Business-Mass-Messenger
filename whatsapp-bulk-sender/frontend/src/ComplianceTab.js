import React, { useState, useEffect } from 'react';

const ComplianceTab = () => {
  const [analytics, setAnalytics] = useState({});
  const [optOutQueue, setOptOutQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendingConfirmations, setSendingConfirmations] = useState(false);
  const [templates, setTemplates] = useState('');

  useEffect(() => {
    fetchAnalytics();
    fetchOptOutQueue();
    fetchTemplates();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('/api/opt-out/analytics');
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching opt-out analytics:', error);
    }
  };

  const fetchOptOutQueue = async () => {
    try {
      const response = await fetch('/api/opt-out/queue');
      const data = await response.json();
      setOptOutQueue(data.queue || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching opt-out queue:', error);
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/templates/compliant');
      const data = await response.json();
      setTemplates(data.templates || '');
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const sendPendingConfirmations = async () => {
    try {
      setSendingConfirmations(true);
      const response = await fetch('/api/opt-out/send-pending', {
        method: 'POST',
      });
      const data = await response.json();
      
      alert(`Sent ${data.sent_count} out of ${data.total_confirmations} opt-out confirmations`);
      
      if (data.errors && data.errors.length > 0) {
        console.error('Errors sending confirmations:', data.errors);
      }
      
      // Refresh the queue
      fetchOptOutQueue();
      fetchAnalytics();
    } catch (error) {
      console.error('Error sending confirmations:', error);
      alert('Failed to send confirmations');
    } finally {
      setSendingConfirmations(false);
    }
  };

  const cleanOptOutsFromCampaign = async (campaignId) => {
    try {
      const response = await fetch(`/api/campaigns/${campaignId}/clean-opt-outs`, {
        method: 'POST',
      });
      const data = await response.json();
      
      alert(data.message);
      fetchAnalytics();
    } catch (error) {
      console.error('Error cleaning opt-outs:', error);
      alert('Failed to clean opt-outs from campaign');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h2 className="text-xl font-bold text-blue-900 mb-2">WhatsApp Business Compliance Center</h2>
        <p className="text-blue-700 text-sm">
          Manage opt-outs, monitor compliance metrics, and ensure your campaigns follow WhatsApp Business guidelines.
        </p>
      </div>

      {/* Compliance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <h3 className="text-sm font-medium text-red-600">Total Opt-outs</h3>
          <p className="text-2xl font-bold text-red-900">{analytics.total_opt_outs || 0}</p>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
          <h3 className="text-sm font-medium text-orange-600">Recent (24h)</h3>
          <p className="text-2xl font-bold text-orange-900">{analytics.recent_opt_outs_24h || 0}</p>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <h3 className="text-sm font-medium text-yellow-600">Pending Confirmations</h3>
          <p className="text-2xl font-bold text-yellow-900">{analytics.pending_confirmations || 0}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <h3 className="text-sm font-medium text-green-600">Compliance Status</h3>
          <p className="text-sm font-bold text-green-900">
            {analytics.total_opt_outs > 0 ? 'Active' : 'Monitoring'}
          </p>
        </div>
      </div>

      {/* Opt-out Confirmation Queue */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900">Opt-out Confirmation Queue</h3>
          <button
            onClick={sendPendingConfirmations}
            disabled={sendingConfirmations || analytics.pending_confirmations === 0}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {sendingConfirmations ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Sending...
              </>
            ) : (
              <>
                <svg className="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Send Pending ({analytics.pending_confirmations || 0})
              </>
            )}
          </button>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading queue...</p>
          </div>
        ) : optOutQueue.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No opt-out confirmations in queue.</p>
            <p className="text-sm mt-2">
              Confirmations are automatically scheduled when customers opt out.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {optOutQueue.slice(0, 10).map((item) => (
              <div key={item.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-gray-900">
                        {item.sender_name || 'Unknown'}
                      </span>
                      <span className="text-sm text-gray-500">
                        {item.phone_number}
                      </span>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        item.sent ? 'text-green-600 bg-green-100' : 'text-orange-600 bg-orange-100'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      Scheduled: {new Date(item.scheduled_time).toLocaleString()}
                      {item.sent && item.sent_at && (
                        <span className="ml-4">
                          Sent: {new Date(item.sent_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Campaign Opt-out Rates */}
      {analytics.campaign_opt_out_rates && analytics.campaign_opt_out_rates.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-4 py-3 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Campaign Opt-out Rates</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {analytics.campaign_opt_out_rates.map((campaign, index) => (
              <div key={index} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{campaign.campaign}</div>
                    <div className="text-sm text-gray-500">
                      {campaign.opt_outs} opt-outs out of {campaign.total_contacts} contacts
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`text-lg font-bold ${
                      campaign.opt_out_rate > 5 ? 'text-red-600' : 
                      campaign.opt_out_rate > 2 ? 'text-orange-600' : 'text-green-600'
                    }`}>
                      {campaign.opt_out_rate}%
                    </span>
                    <button
                      onClick={() => cleanOptOutsFromCampaign(campaign.campaign_id)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Clean Opt-outs
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compliance Guidelines */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Compliance Guidelines</h3>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">✅ Requirements Met</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Opt-out mechanism in all messages</li>
                <li>• Business identification included</li>
                <li>• Automatic opt-out processing</li>
                <li>• Immediate confirmation messages</li>
                <li>• Phone number normalization</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">⚠️ Best Practices</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Monitor opt-out rates (keep under 5%)</li>
                <li>• Send confirmations within 1 hour</li>
                <li>• Clean contact lists regularly</li>
                <li>• Respect quiet hours (9PM-8AM)</li>
                <li>• Maintain consent records</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Compliant Templates Preview */}
      {templates && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-4 py-3 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Compliant Message Templates</h3>
          </div>
          <div className="p-4">
            <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                {templates}
              </pre>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              All templates include mandatory "Reply STOP to opt out" and business identification.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplianceTab;
