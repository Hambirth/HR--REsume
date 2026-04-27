import { useState, useEffect } from 'react'
import axios from 'axios'
import { Upload, Briefcase, Search, CheckCircle, XCircle, FileText, Users, Loader2, X, Award, GraduationCap, Clock, Brain, ChevronDown, ChevronUp, Trash2 } from 'lucide-react'

const API_URL = '/api/v1'

function App() {
  const [activeTab, setActiveTab] = useState('upload')
  const [candidates, setCandidates] = useState([])
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [apiConnected, setApiConnected] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState(null)

  useEffect(() => {
    checkApi()
    fetchCandidates()
    fetchJobs()
  }, [])

  const checkApi = async () => {
    try {
      await axios.get(`${API_URL}/health`)
      setApiConnected(true)
    } catch {
      setApiConnected(false)
    }
  }

  const fetchCandidates = async () => {
    try {
      const res = await axios.get(`${API_URL}/candidates`)
      setCandidates(res.data)
    } catch (err) {
      console.error('Error fetching candidates:', err)
    }
  }

  const fetchJobs = async () => {
    try {
      const res = await axios.get(`${API_URL}/jobs`)
      setJobs(res.data)
    } catch (err) {
      console.error('Error fetching jobs:', err)
    }
  }

  const deleteCandidate = async (candidateId) => {
    try {
      await axios.delete(`${API_URL}/candidates/${candidateId}`)
      fetchCandidates()
    } catch (err) {
      console.error('Error deleting candidate:', err)
      alert('Failed to delete candidate')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">HR Resume Screening</h1>
            </div>
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${apiConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {apiConnected ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
              {apiConnected ? 'API Connected' : 'API Disconnected'}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        <div className="flex gap-2 border-b">
          <TabButton active={activeTab === 'upload'} onClick={() => setActiveTab('upload')} icon={<Upload className="w-4 h-4" />} label="Upload Resumes" />
          <TabButton active={activeTab === 'jobs'} onClick={() => setActiveTab('jobs')} icon={<Briefcase className="w-4 h-4" />} label="Manage Jobs" />
          <TabButton active={activeTab === 'match'} onClick={() => setActiveTab('match')} icon={<Search className="w-4 h-4" />} label="Find Matches" />
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'upload' && <UploadTab candidates={candidates} onUpload={fetchCandidates} onSelectCandidate={setSelectedCandidate} onDelete={deleteCandidate} />}
        {activeTab === 'jobs' && <JobsTab jobs={jobs} onJobCreated={fetchJobs} />}
        {activeTab === 'match' && <MatchTab jobs={jobs} />}
      </main>

      {/* Candidate Profile Modal */}
      {selectedCandidate && (
        <CandidateProfileModal candidate={selectedCandidate} onClose={() => setSelectedCandidate(null)} />
      )}
    </div>
  )
}

function TabButton({ active, onClick, icon, label }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors ${active ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
    >
      {icon}
      {label}
    </button>
  )
}

function UploadTab({ candidates, onUpload, onSelectCandidate, onDelete }) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState([])

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files))
    setResults([])
  }

  const handleUpload = async () => {
    if (files.length === 0) return
    setUploading(true)
    
    try {
      // Use bulk upload endpoint for multiple files
      if (files.length > 1) {
        const formData = new FormData()
        files.forEach(file => formData.append('files', file))
        
        const res = await axios.post(`${API_URL}/candidates/upload/bulk`, formData)
        
        const newResults = res.data.candidates.map(c => ({
          success: true,
          name: c.name || 'Unknown',
          skills: c.skills?.length || 0
        }))
        
        const errorResults = res.data.errors.map(e => ({
          success: false,
          name: e.file
        }))
        
        setResults([...newResults, ...errorResults])
      } else {
        // Single file upload
        const formData = new FormData()
        formData.append('file', files[0])
        
        try {
          const res = await axios.post(`${API_URL}/candidates/upload`, formData)
          setResults([{ success: true, name: res.data.name || files[0].name, skills: res.data.skills?.length || 0 }])
        } catch {
          setResults([{ success: false, name: files[0].name }])
        }
      }
    } catch (error) {
      console.error('Upload error:', error)
      setResults(files.map(f => ({ success: false, name: f.name })))
    }

    setFiles([])
    setUploading(false)
    onUpload()
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Upload Section */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-blue-600" />
          Upload Resumes
        </h2>
        <p className="text-gray-500 text-sm mb-4">Hold Ctrl/Cmd to select multiple files</p>
        
        <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
          <input
            type="file"
            multiple
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 font-medium">Click to select files</p>
            <p className="text-gray-400 text-sm">PDF or DOCX</p>
          </label>
        </div>

        {files.length > 0 && (
          <div className="mt-4">
            <p className="font-medium text-gray-700">{files.length} file(s) selected</p>
            <ul className="text-sm text-gray-500 mt-2">
              {files.map((f, i) => <li key={i}>• {f.name}</li>)}
            </ul>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300 flex items-center justify-center gap-2"
            >
              {uploading ? <><Loader2 className="w-4 h-4 animate-spin" /> Uploading...</> : `Upload ${files.length} Resume(s)`}
            </button>
          </div>
        )}

        {results.length > 0 && (
          <div className="mt-4 space-y-2">
            {results.map((r, i) => (
              <div key={i} className={`p-3 rounded-lg text-sm ${r.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                {r.success ? `✓ ${r.name} - ${r.skills} skills found` : `✗ ${r.name} failed`}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Candidates List */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Users className="w-5 h-5 text-blue-600" />
          Uploaded Candidates ({candidates.length})
        </h2>
        
        {candidates.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No candidates yet. Upload some resumes!</p>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {candidates.map((c) => (
              <div 
                key={c.id} 
                className="p-4 bg-gray-50 rounded-lg hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 cursor-pointer" onClick={() => onSelectCandidate(c)}>
                    <p className="font-medium text-gray-900">{c.name || 'Unknown'}</p>
                    <p className="text-sm text-gray-500">{c.email}</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="text-right">
                      <p className="text-sm font-medium text-blue-600">{c.total_experience_years || 0} yrs</p>
                      <p className="text-xs text-gray-400">{c.education_summary || 'N/A'}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm(`Delete ${c.name || 'this candidate'}?`)) {
                          onDelete(c.id)
                        }
                      }}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete candidate"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {(c.skills || []).slice(0, 5).map((skill, i) => (
                    <span key={i} className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">{skill}</span>
                  ))}
                  {(c.skills || []).length > 5 && (
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full">+{c.skills.length - 5} more</span>
                  )}
                </div>
                <p className="text-xs text-blue-500 mt-2">Click to view full profile →</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function JobsTab({ jobs, onJobCreated }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [skills, setSkills] = useState('')
  const [experience, setExperience] = useState(2)
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!title || !description) return
    setCreating(true)
    try {
      await axios.post(`${API_URL}/jobs`, {
        title,
        description,
        required_skills: skills.split(',').map(s => s.trim()).filter(Boolean),
        preferred_skills: [],
        min_experience_years: experience
      })
      setTitle('')
      setDescription('')
      setSkills('')
      setExperience(2)
      onJobCreated()
    } catch (err) {
      console.error('Error creating job:', err)
    }
    setCreating(false)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Create Job */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-blue-600" />
          Create New Job
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Senior Software Engineer"
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the role and responsibilities..."
              rows={3}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Required Skills (comma separated)</label>
            <input
              type="text"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="Python, AWS, Docker"
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Experience (years)</label>
            <input
              type="number"
              value={experience}
              onChange={(e) => setExperience(parseInt(e.target.value) || 0)}
              min={0}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <button
            onClick={handleCreate}
            disabled={creating || !title || !description}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300"
          >
            {creating ? 'Creating...' : 'Create Job'}
          </button>
        </div>
      </div>

      {/* Jobs List */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4">Your Jobs ({jobs.length})</h2>
        
        {jobs.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No jobs yet. Create one!</p>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {jobs.map((job) => (
              <div key={job.id} className="p-4 bg-gray-50 rounded-lg">
                <p className="font-medium text-gray-900">{job.title}</p>
                <p className="text-sm text-gray-500 line-clamp-2">{job.description}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {(job.required_skills || []).slice(0, 4).map((skill, i) => (
                    <span key={i} className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">{skill}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function MatchTab({ jobs }) {
  const [selectedJob, setSelectedJob] = useState('')
  const [rankings, setRankings] = useState([])
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [expandedCandidate, setExpandedCandidate] = useState(null)

  const handleFindMatches = async () => {
    if (!selectedJob) return
    setLoading(true)
    try {
      const res = await axios.get(`${API_URL}/rankings/${selectedJob}?top_k=10`)
      setRankings(res.data.rankings || [])
      setSummary(res.data.summary || '')
    } catch (err) {
      console.error('Error getting rankings:', err)
      // Handle rate limiting
      if (err.response?.status === 429) {
        alert('⚠️ System Busy\n\nThe system is currently processing other ranking requests (max 3 concurrent).\n\nPlease wait 30 seconds and try again.')
      } else {
        alert('Error ranking candidates. Please try again.')
      }
    }
    setLoading(false)
  }

  const toggleExpand = (candidateId) => {
    setExpandedCandidate(expandedCandidate === candidateId ? null : candidateId)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Search className="w-5 h-5 text-blue-600" />
        Find Best Candidates
      </h2>

      {jobs.length === 0 ? (
        <p className="text-gray-400 text-center py-8">Create a job first in the "Manage Jobs" tab</p>
      ) : (
        <>
          <div className="flex gap-4 mb-6">
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a job...</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>{job.title}</option>
              ))}
            </select>
            <button
              onClick={handleFindMatches}
              disabled={!selectedJob || loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-blue-300 flex items-center gap-2"
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</> : 'Find Matches'}
            </button>
          </div>

          {/* AI Summary */}
          {summary && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
                <Brain className="w-4 h-4" />
                AI Analysis Summary
              </h3>
              <p className="text-sm text-blue-700">{summary}</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
              <p className="text-gray-600 font-medium">Analyzing candidates...</p>
              <p className="text-gray-400 text-sm mt-2">Computing semantic similarity and generating insights</p>
            </div>
          )}

          {!loading && rankings.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium text-gray-700">Top Candidates (click for detailed reasoning)</h3>
              {rankings.map((r) => {
                const score = r.overall_score || 0
                const color = score >= 70 ? 'green' : score >= 50 ? 'yellow' : 'red'
                const isExpanded = expandedCandidate === r.candidate_id
                return (
                  <div key={r.candidate_id} className="bg-gray-50 rounded-lg overflow-hidden">
                    {/* Main Card */}
                    <div 
                      className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => toggleExpand(r.candidate_id)}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${color === 'green' ? 'bg-green-500' : color === 'yellow' ? 'bg-yellow-500' : 'bg-red-500'}`}>
                          #{r.rank}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{r.candidate_name || 'Unknown'}</p>
                          <p className={`text-sm font-medium ${r.recommendation === 'highly_recommended' ? 'text-green-600' : r.recommendation === 'recommended' ? 'text-blue-600' : r.recommendation === 'consider' ? 'text-yellow-600' : 'text-red-600'}`}>
                            {(r.recommendation || '').replace(/_/g, ' ').toUpperCase()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className={`text-2xl font-bold ${color === 'green' ? 'text-green-600' : color === 'yellow' ? 'text-yellow-600' : 'text-red-600'}`}>
                            {score.toFixed(1)}
                          </p>
                          <p className="text-xs text-gray-400">overall score</p>
                        </div>
                        {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                      </div>
                    </div>

                    {/* Expanded Reasoning Section */}
                    {isExpanded && (
                      <div className="px-4 pb-4 border-t border-gray-200">
                        <h4 className="font-medium text-gray-700 mt-3 mb-3">Score Breakdown & Reasoning</h4>
                        
                        {/* Score Bars */}
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <ScoreBar 
                            label="Skills Match" 
                            score={r.skill_score || 0} 
                            icon={<Award className="w-4 h-4" />}
                            color="blue"
                          />
                          <ScoreBar 
                            label="Experience" 
                            score={r.experience_score || 0} 
                            icon={<Clock className="w-4 h-4" />}
                            color="purple"
                          />
                          <ScoreBar 
                            label="Education" 
                            score={r.education_score || 0} 
                            icon={<GraduationCap className="w-4 h-4" />}
                            color="indigo"
                          />
                          <ScoreBar 
                            label="Semantic Fit" 
                            score={(r.semantic_similarity || 0) * 100} 
                            icon={<Brain className="w-4 h-4" />}
                            color="green"
                          />
                        </div>

                        {/* Reasoning Text */}
                        <div className="bg-white p-3 rounded-lg border">
                          <p className="text-sm text-gray-600">
                            <strong>Why this ranking:</strong> This candidate scores {score.toFixed(1)}/100 overall. 
                            {r.skill_score >= 70 ? ' Strong skills match with job requirements.' : r.skill_score >= 50 ? ' Partial skills match - some required skills present.' : ' Limited skills overlap with requirements.'}
                            {r.experience_score >= 80 ? ' Experience level exceeds requirements.' : r.experience_score >= 60 ? ' Experience meets basic requirements.' : ' May need more experience.'}
                            {r.education_score >= 80 ? ' Education qualifications are excellent.' : ' Education level is acceptable.'}
                            {(r.semantic_similarity || 0) >= 0.6 ? ' Profile content shows strong semantic alignment with job description.' : ' Profile shows moderate alignment with job description.'}
                          </p>
                        </div>

                        {/* Strengths & Concerns */}
                        {((r.key_strengths && r.key_strengths.length > 0) || (r.key_concerns && r.key_concerns.length > 0)) && (
                          <div className="grid grid-cols-2 gap-4 mt-3">
                            {r.key_strengths && r.key_strengths.length > 0 && (
                              <div className="bg-green-50 p-3 rounded-lg">
                                <p className="text-sm font-medium text-green-700 mb-1">✓ Key Strengths</p>
                                <ul className="text-sm text-green-600">
                                  {r.key_strengths.map((s, i) => <li key={i}>• {s}</li>)}
                                </ul>
                              </div>
                            )}
                            {r.key_concerns && r.key_concerns.length > 0 && (
                              <div className="bg-red-50 p-3 rounded-lg">
                                <p className="text-sm font-medium text-red-700 mb-1">⚠ Key Concerns</p>
                                <ul className="text-sm text-red-600">
                                  {r.key_concerns.map((c, i) => <li key={i}>• {c}</li>)}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function ScoreBar({ label, score, icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    indigo: 'bg-indigo-500',
    green: 'bg-green-500'
  }
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-gray-600 flex items-center gap-1">{icon} {label}</span>
        <span className="text-sm font-medium text-gray-900">{score.toFixed(0)}/100</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${colorClasses[color]} rounded-full transition-all`} style={{ width: `${Math.min(100, score)}%` }} />
      </div>
    </div>
  )
}

function CandidateProfileModal({ candidate, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Candidate Profile</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Basic Info */}
          <div className="flex items-start gap-4 mb-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <Users className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-900">{candidate.name || 'Unknown'}</h3>
              <p className="text-gray-500">{candidate.email || 'No email'}</p>
              <p className="text-gray-500">{candidate.phone || 'No phone'}</p>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <Clock className="w-4 h-4" />
                <span className="text-sm font-medium">Experience</span>
              </div>
              <p className="text-2xl font-bold text-blue-700">{candidate.total_experience_years || 0} years</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-purple-600 mb-1">
                <GraduationCap className="w-4 h-4" />
                <span className="text-sm font-medium">Education</span>
              </div>
              <p className="text-lg font-bold text-purple-700">{candidate.education_summary || 'Not specified'}</p>
            </div>
          </div>

          {/* Skills */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Award className="w-4 h-4 text-blue-600" />
              Skills ({(candidate.skills || []).length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {(candidate.skills || []).map((skill, i) => (
                <span key={i} className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">
                  {skill}
                </span>
              ))}
              {(!candidate.skills || candidate.skills.length === 0) && (
                <p className="text-gray-400">No skills extracted</p>
              )}
            </div>
          </div>

          {/* Timeline */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3">Candidate Timeline</h4>
            <div className="border-l-2 border-gray-200 pl-4 space-y-3">
              <div className="relative">
                <div className="absolute -left-[21px] w-3 h-3 bg-blue-500 rounded-full border-2 border-white" />
                <p className="text-sm text-gray-500">Uploaded on</p>
                <p className="font-medium">{new Date(candidate.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
              </div>
            </div>
          </div>

          {/* ID */}
          <div className="text-xs text-gray-400 border-t pt-4">
            Candidate ID: {candidate.id}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
