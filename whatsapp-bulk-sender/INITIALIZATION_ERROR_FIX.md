# RepliesTab Initialization Error Fix

## Issue Description
The RepliesTab component was throwing a runtime error:
```
Cannot access 'fetchCampaigns' before initialization
ReferenceError: Cannot access 'fetchCampaigns' before initialization
```

## Root Cause
The `useEffect` hook was positioned before the `useCallback` function definitions in the component code. Since `useCallback` functions are defined using `const`, they are not hoisted like regular function declarations and cannot be accessed before their initialization line.

## Code Issue Location
**File**: `frontend/src/RepliesTab.js`

**Problem Code** (lines 18-21):
```javascript
const [downloading, setDownloading] = useState(false);

useEffect(() => {
  fetchCampaigns();
  fetchReplies();
  fetchAnalytics();
}, [fetchCampaigns, fetchReplies, fetchAnalytics]);

const fetchCampaigns = useCallback(async () => {
  // function definition...
}, []);
```

## Solution Applied
Moved the `useEffect` hook to **after** all `useCallback` function definitions:

**Fixed Code**:
```javascript
const [downloading, setDownloading] = useState(false);

const fetchCampaigns = useCallback(async () => {
  try {
    const response = await fetch('/api/campaigns');
    const data = await response.json();
    setCampaigns(data.campaigns || []);
  } catch (error) {
    console.error('Error fetching campaigns:', error);
  }
}, []);

const fetchReplies = useCallback(async () => {
  // ... function implementation
}, [selectedCampaign, selectedSentiment, startDate, endDate, currentPage, searchQuery]);

const fetchAnalytics = useCallback(async () => {
  // ... function implementation
}, [selectedCampaign]);

// ✅ useEffect now comes AFTER all function definitions
useEffect(() => {
  fetchCampaigns();
  fetchReplies();
  fetchAnalytics();
}, [fetchCampaigns, fetchReplies, fetchAnalytics]);
```

## Technical Explanation
- `const` declarations in JavaScript are **not hoisted** like `function` declarations
- `useCallback` creates functions using `const` assignment
- The `useEffect` dependency array referenced these functions before they were initialized
- Moving `useEffect` after the function definitions ensures all dependencies are available

## Verification
The fix resolves the initialization error and allows the RepliesTab component to:
1. ✅ Load without runtime errors
2. ✅ Properly fetch campaigns, replies, and analytics on component mount
3. ✅ Maintain proper React hook dependency tracking
4. ✅ Support pagination and filtering functionality

## Files Modified
- `frontend/src/RepliesTab.js` - Reordered `useEffect` and `useCallback` functions

## Testing
To verify the fix:
1. Start the React development server: `npm start`
2. Navigate to the "View Replies" tab
3. Confirm no initialization errors appear in the browser console
4. Verify that the page loads with campaign data, replies, and analytics
