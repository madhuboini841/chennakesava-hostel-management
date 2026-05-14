import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bell, Calendar, ChevronRight } from 'lucide-react';

const NoticesStudent = () => {
    const [notices, setNotices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchNotices = async () => {
            try {
                const res = await axios.get(`http://${window.location.hostname}:5000/api/student/notices`, { withCredentials: true });
                setNotices(res.data);
            } catch (err) {
                console.error("Notices fetch error", err);
                setError('Failed to load notices.');
            } finally {
                setLoading(false);
            }
        };
        fetchNotices();
    }, []);

    if (loading) return <div className="flex items-center justify-center p-8 text-indigo-600 font-bold">Loading Notices...</div>;
    if (error) return <div className="bg-red-50 text-red-600 p-4 rounded shadow">{error}</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            
            <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl shadow-lg p-6 text-white flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2 mb-1">
                        <Bell /> Notice Board
                    </h2>
                    <p className="text-orange-100">Important updates and announcements from the admin.</p>
                </div>
            </div>

            <div className="space-y-4">
                {notices.length === 0 ? (
                    <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center text-gray-500">
                        No recent notices.
                    </div>
                ) : (
                    notices.map(notice => (
                        <div key={notice.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
                            <div className="p-6">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-lg font-bold text-gray-800">{notice.title}</h3>
                                    <span className="text-sm font-medium text-gray-500 flex items-center gap-1 bg-gray-100 px-3 py-1 rounded-full">
                                        <Calendar size={14} /> {notice.created_at.split(' ')[0]}
                                    </span>
                                </div>
                                <p className="text-gray-600 whitespace-pre-wrap">{notice.content}</p>
                            </div>
                        </div>
                    ))
                )}
            </div>

        </div>
    );
};

export default NoticesStudent;
