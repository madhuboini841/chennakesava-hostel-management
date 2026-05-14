import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, Plus, Clock, CheckCircle } from 'lucide-react';

const ComplaintsStudent = () => {
    const [complaints, setComplaints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showForm, setShowForm] = useState(false);
    
    // Form state
    const [subject, setSubject] = useState('');
    const [description, setDescription] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const fetchComplaints = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`http://${window.location.hostname}:5000/api/student/complaints`, { withCredentials: true });
            setComplaints(res.data);
            setError('');
        } catch (err) {
            console.error("Complaints fetch error", err);
            setError('Failed to load complaints.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchComplaints();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await axios.post(`http://${window.location.hostname}:5000/api/student/complaints`, 
                { subject, description },
                { withCredentials: true }
            );
            setSubject('');
            setDescription('');
            setShowForm(false);
            fetchComplaints();
        } catch (err) {
            alert('Failed to submit complaint. ' + (err.response?.data?.error || ''));
        } finally {
            setSubmitting(false);
        }
    };

    if (loading && complaints.length === 0) return <div className="flex items-center justify-center p-8 text-indigo-600 font-bold">Loading Complaints...</div>;

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            
            <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                <div className="flex items-center gap-2 text-indigo-600 font-bold">
                    <MessageSquare size={24} />
                    <span>My Complaints</span>
                </div>
                <button 
                    onClick={() => setShowForm(!showForm)}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors"
                >
                    <Plus size={18} /> {showForm ? 'Cancel' : 'New Complaint'}
                </button>
            </div>

            {error && <div className="bg-red-50 text-red-600 p-4 rounded shadow">{error}</div>}

            {showForm && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-bold text-gray-800 mb-4">Submit a New Complaint</h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
                            <input 
                                type="text" 
                                required
                                value={subject}
                                onChange={e => setSubject(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder="E.g., Broken fan in room"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                            <textarea 
                                required
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                rows="4"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder="Please provide details..."
                            ></textarea>
                        </div>
                        <div className="flex justify-end">
                            <button 
                                type="submit" 
                                disabled={submitting}
                                className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-2 rounded-lg font-bold disabled:opacity-50"
                            >
                                {submitting ? 'Submitting...' : 'Submit Complaint'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="space-y-4">
                {complaints.length === 0 ? (
                    <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center text-gray-500">
                        You haven't submitted any complaints yet.
                    </div>
                ) : (
                    complaints.map(c => (
                        <div key={c.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col sm:flex-row gap-4 justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <h4 className="font-bold text-lg text-gray-800">{c.subject}</h4>
                                    <span className={`px-2 py-1 rounded-full text-xs font-bold flex items-center gap-1
                                        ${c.status === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}
                                    >
                                        {c.status === 'resolved' ? <CheckCircle size={12}/> : <Clock size={12}/>}
                                        {c.status.toUpperCase()}
                                    </span>
                                </div>
                                <p className="text-gray-600 mb-3">{c.description}</p>
                                <div className="text-sm text-gray-400 flex items-center gap-4">
                                    <span>Submitted: {c.submitted_at}</span>
                                    {c.status === 'resolved' && c.resolved_at && (
                                        <span className="text-green-600">Resolved: {c.resolved_at}</span>
                                    )}
                                </div>
                            </div>
                            {c.admin_response && (
                                <div className="sm:w-1/3 bg-gray-50 p-4 rounded-lg border border-gray-200">
                                    <div className="text-xs font-bold text-gray-500 mb-1 uppercase tracking-wider">Admin Response</div>
                                    <p className="text-sm text-gray-800">{c.admin_response}</p>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>

        </div>
    );
};

export default ComplaintsStudent;
