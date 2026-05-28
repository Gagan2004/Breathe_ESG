import React, { useState, useEffect } from 'react';

const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8080';
const API_URL = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;


// ---------------------------------------------------------
// Inline SVG Icons
// ---------------------------------------------------------
const ShieldIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
);
const DatabaseIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" /></svg>
);
const TableIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="9" y1="3" x2="9" y2="21" /><line x1="15" y1="3" x2="15" y2="21" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="3" y1="15" x2="21" y2="15" /></svg>
);
const UploadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
);
const AlertIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
);
const LockIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
);
const EditIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" /></svg>
);
const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
);

export default function App() {
  // ---------------------------------------------------------
  // State variables
  // ---------------------------------------------------------
  const [token, setToken] = useState<string | null>(localStorage.getItem('esg_token'));
  const [user, setUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<string>('ledger');

  // Auth Form State
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // Ingestion State
  const [selectedSource, setSelectedSource] = useState('SAP');
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [jobs, setJobs] = useState<any[]>([]);

  // Activities State
  const [activities, setActivities] = useState<any[]>([]);
  const [selectedActivity, setSelectedActivity] = useState<any>(null);
  const [filterState, setFilterState] = useState('');
  const [filterScope, setFilterScope] = useState('');

  // Edit Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editQty, setEditQty] = useState('');
  const [editDate, setEditDate] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [editReason, setEditReason] = useState('');
  const [editError, setEditError] = useState('');

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Loading States for Smooth Transitions
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isActivitiesLoading, setIsActivitiesLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);


  // ---------------------------------------------------------
  // Effects
  // ---------------------------------------------------------
  useEffect(() => {
    if (token) {
      fetchUser();
      fetchJobs();
      fetchActivities();
      fetchAuditLogs();
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchActivities();
    }
  }, [filterState, filterScope]);

  // ---------------------------------------------------------
  // API Calls
  // ---------------------------------------------------------
  const fetchUser = async () => {
    try {
      const res = await fetch(`${API_URL}/api/auth/me/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        handleLogout();
      }
    } catch {
      handleLogout();
    }
  };

  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_URL}/api/jobs/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchActivities = async () => {
    setIsActivitiesLoading(true);
    const start = Date.now();
    try {
      let url = `${API_URL}/api/activities/`;
      const params = new URLSearchParams();
      if (filterState) params.append('review_state', filterState);
      if (filterScope) params.append('emissions_scope', filterScope);
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const res = await fetch(url, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const duration = Date.now() - start;
        if (duration < 600) {
          await new Promise(resolve => setTimeout(resolve, 600 - duration));
        }
        setActivities(data);
        // Sync selected activity if open
        if (selectedActivity) {
          const updated = data.find((a: any) => a.id === selectedActivity.id);
          if (updated) setSelectedActivity(updated);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsActivitiesLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch(`${API_URL}/api/audit-trail/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setIsLoggingIn(true);
    const start = Date.now();
    try {
      const res = await fetch(`${API_URL}/api/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const duration = Date.now() - start;
      if (duration < 800) {
        await new Promise(resolve => setTimeout(resolve, 800 - duration));
      }
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('esg_token', data.token);
        setToken(data.token);
      } else {
        const errData = await res.json();
        setLoginError(errData.non_field_errors?.[0] || 'Invalid username or password.');
      }
    } catch {
      setLoginError('Server connection failed. Make sure backend is running.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('esg_token');
    setToken(null);
    setUser(null);
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileToUpload) return;
    setUploadStatus('Uploading and normalizing...');
    setIsUploading(true);
    const start = Date.now();

    const formData = new FormData();
    formData.append('source_type', selectedSource);
    formData.append('file', fileToUpload);

    try {
      const res = await fetch(`${API_URL}/api/jobs/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`
        },
        body: formData
      });

      const duration = Date.now() - start;
      if (duration < 1000) {
        await new Promise(resolve => setTimeout(resolve, 1000 - duration));
      }

      if (res.ok) {
        setUploadStatus('Ingested and auto-normalized successfully!');
        setFileToUpload(null);
        // Clear input element
        const fileInput = document.getElementById('file-input') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
        fetchJobs();
        fetchActivities();
        fetchAuditLogs();
      } else {
        const errData = await res.json();
        setUploadStatus(errData.error || 'Upload failed.');
        fetchJobs();
      }
    } catch {
      setUploadStatus('Network error during file upload.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/api/activities/${id}/approve/`, {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        fetchActivities();
        fetchAuditLogs();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (id: string, reason: string) => {
    try {
      const res = await fetch(`${API_URL}/api/activities/${id}/reject/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason })
      });
      if (res.ok) {
        fetchActivities();
        fetchAuditLogs();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLock = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/api/activities/${id}/lock/`, {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        fetchActivities();
        fetchAuditLogs();
      } else {
        const err = await res.json();
        alert(err.error || 'Lock failed.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleBulkLock = async () => {
    if (!confirm('Are you sure you want to lock all APPROVED records? This action is permanent and makes them immutable for audit readiness.')) return;
    try {
      const res = await fetch(`${API_URL}/api/activities/bulk_lock/`, {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        fetchActivities();
        fetchAuditLogs();
        alert('All approved records have been locked successfully.');
      } else {
        const err = await res.json();
        alert(err.error || 'Bulk lock failed.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const openEditModal = (activity: any) => {
    setEditQty(activity.normalized_quantity);
    setEditDate(activity.activity_date);
    setEditCategory(activity.activity_category);
    setEditReason('');
    setEditError('');
    setIsEditModalOpen(true);
  };

  const handleEditSave = async () => {
    if (!selectedActivity) return;
    if (editReason.trim() === '') {
      setEditError('An audit justification reason is required.');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/activities/${selectedActivity.id}/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          normalized_quantity: editQty,
          activity_date: editDate,
          activity_category: editCategory,
          edit_reason: editReason
        })
      });

      if (res.ok) {
        setIsEditModalOpen(false);
        fetchActivities();
        fetchAuditLogs();
      } else {
        const err = await res.json();
        setEditError(err.error || 'Save failed. Verify inputs.');
      }
    } catch {
      setEditError('Connection error.');
    }
  };

  // ---------------------------------------------------------
  // Analytics Calculations
  // ---------------------------------------------------------
  const getScopeEmissions = (scope: string) => {
    return activities
      .filter(a => a.emissions_scope === scope && a.review_state !== 'FLAGGED')
      .reduce((sum, a) => sum + parseFloat(a.normalized_quantity), 0);
  };

  const getLockRatio = () => {
    if (activities.length === 0) return '0%';
    const locked = activities.filter(a => a.review_state === 'LOCKED').length;
    return `${Math.round((locked / activities.length) * 100)}%`;
  };

  // Render Login page if no token
  if (!token) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card glass-panel">
          <div className="auth-header">

            <p>Enterprise ESG Data Ingestion & Audit Ledger</p>
          </div>
          <form onSubmit={handleLogin}>
            {loginError && <div style={{ color: 'var(--accent-rose)', marginBottom: 16, fontSize: 14 }}>{loginError}</div>}
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                className="form-input"
                placeholder="analyst, manager, or admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary" style={{ marginTop: 8 }} disabled={isLoggingIn}>
              {isLoggingIn ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                  <span className="spinner-mini"></span>
                  <span>Verifying Credentials...</span>
                </div>
              ) : (
                "Access Platform"
              )}
            </button>
            <div style={{ marginTop: 20, fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>
              Credentials: <code>analyst</code> / <code>analyst123</code>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header bar */}
      <header className="header-bar glass-panel">
        <div className="brand">
          <ShieldIcon />
          <span>CHI-CHA</span>
        </div>
        <nav className="nav-tabs">
          <button
            className={`tab-btn ${activeTab === 'ledger' ? 'active' : ''}`}
            onClick={() => setActiveTab('ledger')}
          >
            <TableIcon />
            <span style={{ marginLeft: 8 }}>Review Ledger</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'ingest' ? 'active' : ''}`}
            onClick={() => setActiveTab('ingest')}
          >
            <DatabaseIcon />
            <span style={{ marginLeft: 8 }}>Data Ingestion</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <ShieldIcon />
            <span style={{ marginLeft: 8 }}>Audit & Analytics</span>
          </button>
        </nav>
        <div className="user-profile">
          <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
            Signed in as <strong>{user?.username}</strong> ({user?.organization_name})
          </span>
          <button className="btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      {/* KPI Cards */}
      {activeTab !== 'ingest' && (
        <section className="kpi-container">
          <div className="kpi-card glass-panel">
            <div className="kpi-title">Scope 1 Direct</div>
            <div className="kpi-value" style={{ color: 'var(--accent-rose)' }}>
              {getScopeEmissions('SCOPE_1').toLocaleString(undefined, { maximumFractionDigits: 1 })}
              <span style={{ fontSize: 14, color: 'var(--text-secondary)', marginLeft: 6 }}>L/kg</span>
            </div>
          </div>
          <div className="kpi-card glass-panel">
            <div className="kpi-title">Scope 2 Indirect</div>
            <div className="kpi-value" style={{ color: 'var(--accent-amber)' }}>
              {getScopeEmissions('SCOPE_2').toLocaleString(undefined, { maximumFractionDigits: 1 })}
              <span style={{ fontSize: 14, color: 'var(--text-secondary)', marginLeft: 6 }}>kWh</span>
            </div>
          </div>
          <div className="kpi-card glass-panel">
            <div className="kpi-title">Scope 3 Value Chain</div>
            <div className="kpi-value" style={{ color: 'var(--accent-blue)' }}>
              {getScopeEmissions('SCOPE_3').toLocaleString(undefined, { maximumFractionDigits: 1 })}
              <span style={{ fontSize: 14, color: 'var(--text-secondary)', marginLeft: 6 }}>p-km</span>
            </div>
          </div>
          <div className="kpi-card glass-panel">
            <div className="kpi-title">Audit Sealed Ratio</div>
            <div className="kpi-value" style={{ color: 'var(--accent-purple)' }}>
              {getLockRatio()}
            </div>
          </div>
        </section>
      )}

      {/* Tab Contents */}
      <main>
        {activeTab === 'ingest' && (
          <div className="grid-2col">
            {/* Left side: Upload card */}
            <div className="glass-panel" style={{ padding: 32 }}>
              <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: 24, fontSize: 22 }}>
                Upload Corporate Data Source
              </h2>
              <form onSubmit={handleFileUpload}>
                <div className="form-group">
                  <label>Data Origin / System</label>
                  <select
                    className="form-input"
                    value={selectedSource}
                    onChange={(e) => setSelectedSource(e.target.value)}
                    style={{ background: 'var(--bg-tertiary)' }}
                  >
                    <option value="SAP">SAP Fuel & Procurement (CSV)</option>
                    <option value="UTILITY">Utility Electricity Portal (CSV)</option>
                    <option value="TRAVEL">Corporate Travel APIs (JSON)</option>
                  </select>
                </div>

                <div className="form-group" style={{ marginTop: 24 }}>
                  <label>Data File</label>
                  <div className="upload-zone">
                    <UploadIcon />
                    <p style={{ marginTop: 12, fontWeight: 500 }}>
                      {fileToUpload ? fileToUpload.name : 'Select or drop source export file'}
                    </p>
                    <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 4 }}>
                      Accepts .csv for SAP/Utility, .json for Concur/Navan
                    </p>
                    <input
                      id="file-input"
                      type="file"
                      accept=".csv,.json"
                      onChange={(e) => setFileToUpload(e.target.files?.[0] || null)}
                      required
                    />
                  </div>
                </div>

                {uploadStatus && (
                  <div style={{ margin: '16px 0', fontSize: 14, color: uploadStatus.includes('successfully') ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                    {uploadStatus}
                  </div>
                )}

                <button
                  type="submit"
                  className="btn-primary"
                  style={{ marginTop: 8 }}
                  disabled={!fileToUpload || isUploading}
                >
                  {isUploading ? (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                      <span className="spinner-mini"></span>
                      <span>Processing & Normalizing...</span>
                    </div>
                  ) : (
                    "Process and Auto-Normalize"
                  )}
                </button>
              </form>
            </div>

            {/* Right side: Ingestion Job Logs */}
            <div className="glass-panel" style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 20 }}>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22 }}>Ingestion Jobs History</h2>
              <div style={{ overflowY: 'auto', maxHeight: '450px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {jobs.map((job) => (
                  <div key={job.id} className="glass-card" style={{ padding: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                      <strong style={{ fontSize: 15 }}>{job.filename}</strong>
                      <span className={`badge ${job.status === 'COMPLETED' ? 'badge-approved' : job.status === 'FAILED' ? 'badge-flagged' : 'badge-ingested'}`}>
                        {job.status}
                      </span>
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <div>Source: {job.source_type}</div>
                      <div>Uploaded by: {job.uploaded_by_username}</div>
                      <div>Rows parsed: {job.records_count}</div>
                      <div>Date: {new Date(job.created_at).toLocaleString()}</div>
                      {job.error_log && (
                        <div style={{
                          color: 'var(--accent-rose)',
                          background: 'rgba(239, 68, 68, 0.05)',
                          padding: 8,
                          borderRadius: 4,
                          marginTop: 8,
                          fontFamily: 'monospace',
                          fontSize: 11
                        }}>
                          Error: {job.error_log}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'ledger' && (
          <div className="inspector-layout">
            {/* Table side */}
            <div className="glass-panel" style={{ padding: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22 }}>Sustainability Ledger</h2>
                <div style={{ display: 'flex', gap: 12 }}>
                  <select
                    className="form-input"
                    value={filterScope}
                    onChange={(e) => setFilterScope(e.target.value)}
                    style={{ padding: '8px 12px', fontSize: 13, background: 'var(--bg-tertiary)' }}
                  >
                    <option value="">All Scopes</option>
                    <option value="SCOPE_1">Scope 1 (Direct)</option>
                    <option value="SCOPE_2">Scope 2 (Electricity)</option>
                    <option value="SCOPE_3">Scope 3 (Travel & Procurement)</option>
                  </select>
                  <select
                    className="form-input"
                    value={filterState}
                    onChange={(e) => setFilterState(e.target.value)}
                    style={{ padding: '8px 12px', fontSize: 13, background: 'var(--bg-tertiary)' }}
                  >
                    <option value="">All States</option>
                    <option value="INGESTED">Ingested</option>
                    <option value="FLAGGED">Flagged</option>
                    <option value="APPROVED">Approved</option>
                    <option value="LOCKED">Locked</option>
                  </select>
                  <button className="btn-primary" onClick={handleBulkLock} style={{ padding: '8px 16px', fontSize: 13, width: 'auto' }}>
                    Bulk Lock Approved
                  </button>
                </div>
              </div>
              <div className="table-container-relative">
                {isActivitiesLoading && (
                  <div className="table-loading-overlay">
                    <span className="spinner-large"></span>
                    <span style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: 14 }}>
                      Syncing ledger records...
                    </span>
                  </div>
                )}
                <div className="activity-table-wrapper">
                  <table className="activity-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Category</th>
                        <th>Scope</th>
                        <th>Raw Quantity</th>
                        <th>Normalized Quantity</th>
                        <th>Audit Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activities.map((a) => (
                        <tr
                          key={a.id}
                          className={selectedActivity?.id === a.id ? 'selected' : ''}
                          onClick={() => setSelectedActivity(a)}
                        >
                          <td>{a.activity_date}</td>
                          <td>
                            <div style={{ fontWeight: 600 }}>{a.activity_category}</div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.job_filename}</div>
                          </td>
                          <td>
                            <span className={`badge ${a.emissions_scope === 'SCOPE_1' ? 'badge-scope1' : a.emissions_scope === 'SCOPE_2' ? 'badge-scope2' : a.emissions_scope === 'SCOPE_3' ? 'badge-scope3' : 'badge-scope3'}`}>
                              {a.emissions_scope.replace('_', ' ')}
                            </span>
                          </td>
                          <td>{parseFloat(a.raw_quantity).toLocaleString()} {a.raw_unit}</td>
                          <td>
                            <strong>{parseFloat(a.normalized_quantity).toLocaleString()}</strong> {a.normalized_unit}
                          </td>
                          <td>
                            <span className={`badge ${a.review_state === 'LOCKED' ? 'badge-locked' : a.review_state === 'APPROVED' ? 'badge-approved' : a.review_state === 'FLAGGED' ? 'badge-flagged' : a.review_state === 'INGESTED' ? 'badge-ingested' : 'badge-ingested'}`}>
                              {a.review_state}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Trace inspector panel */}
            <div className="glass-panel inspector-panel">
              <h3 className="trace-title">Data Trace Inspector</h3>
              {selectedActivity ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Activity ID</label>
                    <div style={{ fontSize: 13, wordBreak: 'break-all', fontFamily: 'monospace' }}>{selectedActivity.id}</div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div>
                      <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Status</label>
                      <div>
                        <span className={`badge ${selectedActivity.review_state === 'LOCKED' ? 'badge-locked' : selectedActivity.review_state === 'APPROVED' ? 'badge-approved' : selectedActivity.review_state === 'FLAGGED' ? 'badge-flagged' : 'badge-ingested'}`}>
                          {selectedActivity.review_state}
                        </span>
                      </div>
                    </div>
                    <div>
                      <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Date</label>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{selectedActivity.activity_date}</div>
                    </div>
                  </div>

                  {selectedActivity.activity_start_date && (
                    <div>
                      <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Billing Period</label>
                      <div style={{ fontSize: 13 }}>
                        {selectedActivity.activity_start_date} to {selectedActivity.activity_end_date}
                      </div>
                    </div>
                  )}

                  {selectedActivity.flags && selectedActivity.flags.length > 0 && (
                    <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: 8, padding: 12 }}>
                      <strong style={{ color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, marginBottom: 6 }}>
                        <AlertIcon /> Anomaly Flags Detected:
                      </strong>
                      <ul style={{ paddingLeft: 16, fontSize: 12, color: 'var(--text-primary)' }}>
                        {selectedActivity.flags.map((flag: string, idx: number) => (
                          <li key={idx} style={{ marginBottom: 4 }}>{flag}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Raw Data Trace */}
                  <div>
                    <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Raw Input Source Data</label>
                    <div className="raw-json-block">
                      {JSON.stringify(selectedActivity.raw_record_data, null, 2)}
                    </div>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      Traceability link: Row #{selectedActivity.raw_record_data?.row_index || 'N/A'} in {selectedActivity.job_filename}
                    </span>
                  </div>

                  {/* Actions for analysts */}
                  {selectedActivity.review_state !== 'LOCKED' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          className="btn-primary"
                          onClick={() => handleApprove(selectedActivity.id)}
                          style={{ flex: 1, background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)', border: '1px solid rgba(16, 185, 129, 0.25)' }}
                        >
                          <CheckIcon /> <span style={{ marginLeft: 6 }}>Approve</span>
                        </button>
                        <button
                          className="btn-primary"
                          onClick={() => {
                            const reason = prompt('Enter flagging/rejection reason:');
                            if (reason) handleReject(selectedActivity.id, reason);
                          }}
                          style={{ flex: 1, background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', border: '1px solid rgba(245, 158, 11, 0.25)' }}
                        >
                          <AlertIcon /> <span style={{ marginLeft: 6 }}>Flag / Warn</span>
                        </button>
                      </div>

                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          className="btn-primary"
                          onClick={() => openEditModal(selectedActivity)}
                          style={{ flex: 1, background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-blue)', border: '1px solid rgba(59, 130, 246, 0.25)' }}
                        >
                          <EditIcon /> <span style={{ marginLeft: 6 }}>Edit Record</span>
                        </button>

                        {selectedActivity.review_state === 'APPROVED' && (
                          <button
                            className="btn-primary"
                            onClick={() => handleLock(selectedActivity.id)}
                            style={{ flex: 1, background: 'linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%)' }}
                          >
                            <LockIcon /> <span style={{ marginLeft: 6 }}>Lock for Audit</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div style={{ background: 'rgba(139, 92, 246, 0.08)', border: '1px solid rgba(139, 92, 246, 0.2)', borderRadius: 8, padding: 12, textAlign: 'center', marginTop: 12 }}>
                      <strong style={{ color: 'var(--accent-purple)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 14 }}>
                        <LockIcon /> Sealed & Locked
                      </strong>
                      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                        Approved by {selectedActivity.reviewer_username} on {new Date(selectedActivity.reviewed_at).toLocaleDateString()}. Immutable audit hash established.
                      </p>
                    </div>
                  )}

                  {/* Audit History Log */}
                  <div style={{ marginTop: 16 }}>
                    <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-secondary)', display: 'block', marginBottom: 8 }}>Record Edit History</label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {selectedActivity.audit_history?.map((log: any) => (
                        <div key={log.id} style={{ fontSize: 12, background: 'rgba(255, 255, 255, 0.02)', padding: 10, borderRadius: 6, border: '1px solid var(--border-glass)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', marginBottom: 4 }}>
                            <strong>{log.action}</strong>
                            <span>{new Date(log.timestamp).toLocaleDateString()}</span>
                          </div>
                          <div>By: {log.user_username}</div>
                          {log.notes && <div style={{ fontStyle: 'italic', color: 'var(--text-secondary)', marginTop: 2 }}>"{log.notes}"</div>}
                          {log.changes && Object.keys(log.changes).length > 0 && (
                            <div style={{ fontSize: 11, color: 'var(--accent-blue)', marginTop: 4, fontFamily: 'monospace' }}>
                              Changes: {JSON.stringify(log.changes)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px 0' }}>
                  Select a row in the ledger table to view its raw data trace and trigger approval actions.
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="grid-2col">
            {/* Emissions charts */}
            <div className="glass-panel" style={{ padding: 32 }}>
              <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: 24, fontSize: 22 }}>
                Emissions Breakdown by Scope
              </h2>
              <div className="svg-chart-container">
                <div className="chart-bar-wrapper">
                  <div
                    className="chart-bar chart-bar-scope1"
                    style={{ height: `${Math.min(100, Math.max(10, getScopeEmissions('SCOPE_1') / 100))}%` }}
                    data-val={`${getScopeEmissions('SCOPE_1').toFixed(0)} L/kg`}
                  />
                  <div className="chart-label">Scope 1</div>
                </div>
                <div className="chart-bar-wrapper">
                  <div
                    className="chart-bar chart-bar-scope2"
                    style={{ height: `${Math.min(100, Math.max(10, getScopeEmissions('SCOPE_2') / 500))}%` }}
                    data-val={`${getScopeEmissions('SCOPE_2').toFixed(0)} kWh`}
                  />
                  <div className="chart-label">Scope 2</div>
                </div>
                <div className="chart-bar-wrapper">
                  <div
                    className="chart-bar chart-bar-scope3"
                    style={{ height: `${Math.min(100, Math.max(10, getScopeEmissions('SCOPE_3') / 200))}%` }}
                    data-val={`${getScopeEmissions('SCOPE_3').toFixed(0)} p-km`}
                  />
                  <div className="chart-label">Scope 3</div>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                  <span>Scope 1 (Direct Fuel Combustion):</span>
                  <strong>{getScopeEmissions('SCOPE_1').toLocaleString()} L/kg</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                  <span>Scope 2 (Electricity Usage):</span>
                  <strong>{getScopeEmissions('SCOPE_2').toLocaleString()} kWh</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                  <span>Scope 3 (Travel & Procurement):</span>
                  <strong>{getScopeEmissions('SCOPE_3').toLocaleString()} p-km</strong>
                </div>
              </div>
            </div>

            {/* Audit log list */}
            <div className="glass-panel" style={{ padding: 32 }}>
              <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: 24, fontSize: 22 }}>
                Global System Audit Log
              </h2>
              <div style={{ overflowY: 'auto', maxHeight: '400px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {auditLogs.map((log) => (
                  <div key={log.id} style={{ display: 'flex', flexDirection: 'column', gap: 4, padding: 12, background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-glass)', borderRadius: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <strong>{log.action} Activity</strong>
                      <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      Performed by user: <strong>{log.user_username}</strong>
                    </div>
                    {log.notes && <div style={{ fontSize: 12, fontStyle: 'italic', marginTop: 2 }}>"{log.notes}"</div>}
                    {log.changes && Object.keys(log.changes).length > 0 && (
                      <div style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--accent-blue)', marginTop: 4 }}>
                        Changes: {JSON.stringify(log.changes)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Edit Record Modal */}
      {isEditModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel">
            <div className="modal-header">
              <span>Adjust Sustainability Record</span>
              <button className="modal-close" onClick={() => setIsEditModalOpen(false)}>×</button>
            </div>

            {editError && <div style={{ color: 'var(--accent-rose)', fontSize: 14 }}>{editError}</div>}

            <div className="form-group">
              <label>Normalized Quantity</label>
              <input
                type="number"
                className="form-input"
                value={editQty}
                onChange={(e) => setEditQty(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Activity Date</label>
              <input
                type="date"
                className="form-input"
                value={editDate}
                onChange={(e) => setEditDate(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Category Type</label>
              <input
                type="text"
                className="form-input"
                value={editCategory}
                onChange={(e) => setEditCategory(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Audit Justification Reason</label>
              <textarea
                className="form-input"
                style={{ height: '80px', resize: 'vertical' }}
                placeholder="Explain the correction (e.g. Adjusted wrong unit multiplier)"
                value={editReason}
                onChange={(e) => setEditReason(e.target.value)}
                required
              />
            </div>

            <button className="btn-primary" onClick={handleEditSave} style={{ marginTop: 8 }}>
              Apply Changes and Log Audit Trail
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
