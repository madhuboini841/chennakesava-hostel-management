import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { User, MapPin, Phone, Mail, BookOpen, Clock, Activity, Calendar } from 'lucide-react';

const StudentProfile = () => {
    const [profileData, setProfileData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    const [passwordData, setPasswordData] = useState({ currentPassword: '', newPassword: '', confirmPassword: '' });
    const [passwordMsg, setPasswordMsg] = useState('');
    const [passwordErr, setPasswordErr] = useState('');
    const [changingPassword, setChangingPassword] = useState(false);

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        setPasswordMsg('');
        setPasswordErr('');
        
        if (passwordData.newPassword !== passwordData.confirmPassword) {
            return setPasswordErr('New passwords do not match');
        }
        if (passwordData.newPassword.length < 6) {
            return setPasswordErr('Password must be at least 6 characters');
        }

        setChangingPassword(true);
        try {
            const res = await axios.post(`/api/auth/change-password`, {
                currentPassword: passwordData.currentPassword,
                newPassword: passwordData.newPassword
            }, { withCredentials: true, headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
            
            setPasswordMsg(res.data.message || 'Password updated successfully');
            setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
        } catch (err) {
            setPasswordErr(err.response?.data?.error || 'Failed to change password');
        } finally {
            setChangingPassword(false);
        }
    };

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                // Ensure auth token is sent (axios config in AuthContext already sets defaults)
                const res = await axios.get(`http://${window.location.hostname}:5000/api/student/profile`, { withCredentials: true });
                setProfileData(res.data);
            } catch (err) {
                console.error("Profile fetch error", err);
                setError('Failed to load profile data.');
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, []);

    if (loading) return <div className="flex items-center justify-center p-8 text-indigo-600 font-bold">Loading Profile...</div>;
    if (error) return <div className="bg-red-50 text-red-600 p-4 rounded shadow">{error}</div>;
    if (!profileData) return null;

    const { student, roommates } = profileData;

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            
            {/* Welcome Banner */}
            <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 rounded-xl shadow-lg p-6 sm:p-8 text-white flex flex-col sm:flex-row justify-between items-center gap-6">
                <div>
                    <h2 className="text-3xl font-bold mb-2">Hello, {student?.name}! 👋</h2>
                    <p className="text-indigo-100 flex items-center gap-2">
                        <MapPin size={18} />
                        {student?.room_number ? `Room ${student.room_number}` : 'No room assigned yet.'} 
                        {student?.course && ` | ${student.course} Year ${student.year_of_study || ''}`}
                    </p>
                </div>
                <div className="bg-white/20 px-4 py-2 rounded-lg backdrop-blur-sm flex items-center gap-2 font-bold text-lg">
                    <BookOpen size={20} />
                    {student?.roll_number || 'N/A'}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Personal Info Card */}
                <div className="md:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center gap-2">
                        <User className="text-indigo-500" size={20} />
                        <h3 className="font-bold text-gray-800">Personal Information</h3>
                    </div>
                    <div className="p-6">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            <div>
                                <div className="text-sm text-gray-500 mb-1 flex items-center gap-2"><Mail size={14}/> Email Address</div>
                                <div className="font-semibold text-gray-800">{student?.email}</div>
                            </div>
                            <div>
                                <div className="text-sm text-gray-500 mb-1 flex items-center gap-2"><Phone size={14}/> Mobile Number</div>
                                <div className="font-semibold text-gray-800">{student?.mobile_number || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-sm text-gray-500 mb-1 flex items-center gap-2"><BookOpen size={14}/> Course</div>
                                <div className="font-semibold text-gray-800">{student?.course || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-sm text-gray-500 mb-1 flex items-center gap-2"><Calendar size={14}/> Year of Study</div>
                                <div className="font-semibold text-gray-800">{student?.year_of_study || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-sm text-gray-500 mb-1 flex items-center gap-2"><Activity size={14}/> Account Status</div>
                                <div className="font-semibold">
                                    <span className={`px-2 py-1 rounded text-xs uppercase ${student?.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                        {student?.status || 'Unknown'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Room Details Card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center gap-2">
                        <MapPin className="text-indigo-500" size={20} />
                        <h3 className="font-bold text-gray-800">Room Details</h3>
                    </div>
                    <div className="p-6">
                        {student?.room_number ? (
                            <div className="space-y-4">
                                <div className="flex justify-between border-b pb-2">
                                    <span className="text-gray-500">Room No.</span>
                                    <span className="font-bold text-gray-800">{student.room_number}</span>
                                </div>
                                <div className="flex justify-between border-b pb-2">
                                    <span className="text-gray-500">Floor</span>
                                    <span className="font-bold text-gray-800">{student.floor || 'N/A'}</span>
                                </div>
                                <div className="flex justify-between border-b pb-2">
                                    <span className="text-gray-500">Type</span>
                                    <span className="font-bold text-gray-800">{student.room_type || 'N/A'}</span>
                                </div>
                                <div className="flex justify-between pb-2">
                                    <span className="text-gray-500">Monthly Fee</span>
                                    <span className="font-bold text-green-600">₹{student.monthly_fee || 'N/A'}</span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-gray-500 text-sm text-center py-4">You have not been assigned a room yet.</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Roommates Card */}
            {student?.room_number && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center gap-2">
                        <User className="text-indigo-500" size={20} />
                        <h3 className="font-bold text-gray-800">Roommates</h3>
                    </div>
                    <div className="p-0">
                        {(!roommates || roommates.length === 0) ? (
                            <p className="p-6 text-gray-500 text-sm text-center">You currently have no roommates.</p>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-gray-50 border-b text-gray-500 text-sm">
                                            <th className="p-4 font-semibold">Name</th>
                                            <th className="p-4 font-semibold">Course</th>
                                            <th className="p-4 font-semibold">Contact</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {roommates.map((r, idx) => (
                                            <tr key={idx} className="border-b hover:bg-gray-50">
                                                <td className="p-4 font-medium text-gray-800">{r.name}</td>
                                                <td className="p-4 text-sm text-gray-600">{r.course} (Yr {r.year_of_study})</td>
                                                <td className="p-4 text-sm text-gray-600">
                                                    <div>{r.mobile_number}</div>
                                                    <div className="text-xs text-gray-400">{r.email}</div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            )}
            {/* Change Password Card */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center gap-2">
                    <User className="text-indigo-500" size={20} />
                    <h3 className="font-bold text-gray-800">Change Password</h3>
                </div>
                <div className="p-6">
                    {passwordMsg && <div className="bg-green-100 text-green-700 p-2 mb-4 rounded text-sm text-center">{passwordMsg}</div>}
                    {passwordErr && <div className="bg-red-100 text-red-700 p-2 mb-4 rounded text-sm text-center">{passwordErr}</div>}
                    
                    <form onSubmit={handlePasswordChange} className="space-y-4 max-w-sm">
                        <div>
                            <label className="block text-sm text-gray-600 mb-1">Current Password</label>
                            <input type="password" required className="w-full border rounded p-2 text-sm outline-none focus:ring-1 focus:ring-indigo-500" value={passwordData.currentPassword} onChange={e => setPasswordData({...passwordData, currentPassword: e.target.value})} />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-600 mb-1">New Password</label>
                            <input type="password" required className="w-full border rounded p-2 text-sm outline-none focus:ring-1 focus:ring-indigo-500" value={passwordData.newPassword} onChange={e => setPasswordData({...passwordData, newPassword: e.target.value})} />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-600 mb-1">Confirm New Password</label>
                            <input type="password" required className="w-full border rounded p-2 text-sm outline-none focus:ring-1 focus:ring-indigo-500" value={passwordData.confirmPassword} onChange={e => setPasswordData({...passwordData, confirmPassword: e.target.value})} />
                        </div>
                        <button type="submit" disabled={changingPassword} className="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold hover:bg-indigo-700 disabled:bg-indigo-400">
                            {changingPassword ? 'Updating...' : 'Update Password'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default StudentProfile;
