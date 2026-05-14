import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { Utensils, User, Info, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const StudentDashboard = () => {
  const { user, logout } = useContext(AuthContext);
  const [menus, setMenus] = useState([]);
  const [optOut, setOptOut] = useState({ breakfast: false, lunch: false, dinner: false, reason: '' });
  const [notifs, setNotifs] = useState([]);
  const [msg, setMsg] = useState('');
  const navigate = useNavigate();
  
  const today = new Date().toISOString().split('T')[0];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [menuRes, optRes, notifRes] = await Promise.all([
        axios.get(`/api/student/menu`),
        axios.get(`/api/student/optout/today`),
        axios.get(`/api/student/notifications`)
      ]);
      setMenus(menuRes.data);
      setOptOut({
        breakfast: !!optRes.data.breakfast,
        lunch: !!optRes.data.lunch,
        dinner: !!optRes.data.dinner,
        reason: optRes.data.reason || ''
      });
      setNotifs(notifRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleOptOutSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/student/optout`, {
        date: today,
        ...optOut
      });
      setMsg('Opt-out preferences saved!');
      setTimeout(() => setMsg(''), 3000);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to save');
    }
  };

  // Filter menus to find today's
  const todaysMenu = (Array.isArray(menus) ? menus : []).filter(m => m.date === today);

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg p-6 text-white flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2 mb-1">
                        <Utensils /> Food & Meals
                    </h2>
                    <p className="text-blue-100">Check today's menu and update your meal attendance.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Today's Opt-Out Form */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center gap-2">
                        <User className="text-indigo-500" size={20} />
                        <h3 className="font-bold text-gray-800">Meal Attendance (Today: {today})</h3>
                    </div>
                    <div className="p-6">
                        <div className="bg-blue-50 text-blue-800 p-4 rounded-lg text-sm mb-6 flex items-start gap-2">
                            <Info size={16} className="mt-0.5 shrink-0" />
                            <p>You are counted as <strong>EATING</strong> by default. Only check these boxes if you wish to <strong>SKIP</strong> a meal today. (Breakfast cutoff: 7 AM, Lunch/Dinner cutoff: 10 AM)</p>
                        </div>
                        
                        {msg && (
                            <div className="mb-6 p-3 bg-green-50 text-green-700 rounded-lg text-sm font-bold flex items-center gap-2">
                                <CheckCircle size={16} /> {msg}
                            </div>
                        )}
                        
                        <form onSubmit={handleOptOutSubmit} className="space-y-4">
                            <div className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                                <label htmlFor="b" className="font-medium text-gray-700 cursor-pointer select-none">Skip Breakfast</label>
                                <input type="checkbox" id="b" checked={optOut.breakfast} onChange={e => setOptOut({...optOut, breakfast: e.target.checked})} className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"/>
                            </div>
                            <div className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                                <label htmlFor="l" className="font-medium text-gray-700 cursor-pointer select-none">Skip Lunch</label>
                                <input type="checkbox" id="l" checked={optOut.lunch} onChange={e => setOptOut({...optOut, lunch: e.target.checked})} className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"/>
                            </div>
                            <div className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                                <label htmlFor="d" className="font-medium text-gray-700 cursor-pointer select-none">Skip Dinner</label>
                                <input type="checkbox" id="d" checked={optOut.dinner} onChange={e => setOptOut({...optOut, dinner: e.target.checked})} className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"/>
                            </div>
                            <div className="pt-2">
                                <label className="block text-sm font-medium text-gray-700 mb-2">Reason (Optional)</label>
                                <select value={optOut.reason} onChange={e => setOptOut({...optOut, reason: e.target.value})} className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                                    <option value="">None</option>
                                    <option value="Going Home">Going Home</option>
                                    <option value="Outing">Outing</option>
                                    <option value="Fasting">Fasting</option>
                                </select>
                            </div>
                            <button type="submit" className="w-full bg-indigo-600 text-white py-3 rounded-lg font-bold hover:bg-indigo-700 transition-colors mt-2">
                                Save Preferences
                            </button>
                        </form>
                    </div>
                </div>

                {/* Today's Menu */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center gap-2">
                        <Utensils className="text-indigo-500" size={20} />
                        <h3 className="font-bold text-gray-800">Today's Menu ({user?.meal_preference})</h3>
                    </div>
                    <div className="p-6 space-y-4">
                        {['breakfast', 'lunch', 'dinner'].map(slot => {
                            const item = todaysMenu.find(m => m.meal_slot === slot && m.meal_type === user?.meal_preference);
                            return (
                                <div key={slot} className="border border-gray-100 bg-gray-50/50 p-4 rounded-lg relative overflow-hidden">
                                    {item?.is_locked && (
                                        <div className="absolute top-0 right-0 bg-red-100 text-red-600 text-[10px] font-bold px-2 py-1 rounded-bl-lg">
                                            LOCKED
                                        </div>
                                    )}
                                    <h4 className="font-bold capitalize text-indigo-800 mb-1">{slot}</h4>
                                    <p className="text-gray-700">{item ? item.items : 'Not posted yet.'}</p>
                                </div>
                            )
                        })}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default StudentDashboard;
